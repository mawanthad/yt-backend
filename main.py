from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
import uuid
import os
from docx import Document
import yt_dlp

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FILES_DIR = "files"
os.makedirs(FILES_DIR, exist_ok=True)

class ScrapeRequest(BaseModel):
    url: str

@app.post("/scrape")
async def scrape_transcripts(data: ScrapeRequest):
    url = data.url.strip()

    # Try extracting video URL(s) from channel using yt_dlp
    try:
        ydl_opts = {
            'quiet': True,
            'extract_flat': 'in_playlist',
            'dump_single_json': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if "entries" in info and len(info["entries"]) > 0:
                # It's a channel or playlist: use first video
                video_id = info["entries"][0]["id"]
            elif "id" in info:
                # It's a single video
                video_id = info["id"]
            else:
                return {"status": "error", "message": "Could not extract video from URL."}
    except Exception as e:
        return {"status": "error", "message": f"Video extraction failed: {str(e)}"}

    # Get transcript
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
    except Exception as e:
        return {"status": "error", "message": f"Transcript fetch failed: {str(e)}"}

    # Save to DOCX
    doc = Document()
    doc.add_heading("YouTube Transcript", level=1)
    for item in transcript:
        doc.add_paragraph(f"{item['start']:.2f}s: {item['text']}")

    filename = f"transcript_{uuid.uuid4().hex[:8]}.docx"
    path = os.path.join(FILES_DIR, filename)
    doc.save(path)

    return {
        "status": "success",
        "file": filename,
        "count": len(transcript)
    }

@app.get("/files/{filename}")
def serve_file(filename: str):
    path = os.path.join(FILES_DIR, filename)
    if not os.path.isfile(path):
        return {"message": "File not found"}
    return {"message": "File found"}
