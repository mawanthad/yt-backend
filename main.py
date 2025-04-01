from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import uuid
from docx import Document
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    input_url = data.url.strip()

    # Use ytsearch for handle or channel
    if not input_url.startswith("http"):
        input_url = f"ytsearch10:{input_url}"

    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True,
        "force_generic_extractor": False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(input_url, download=False)
            videos = info.get("entries", [])
    except Exception as e:
        return {"status": "error", "message": f"Failed to get videos: {str(e)}"}

    if not videos:
        return {"status": "error", "message": "No videos found from this input."}

    results = []
    for video in videos:
        video_id = video.get("id")
        if not video_id:
            continue

        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            results.append({
                "title": video.get("title", "Untitled Video"),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "transcript": transcript
            })
        except (TranscriptsDisabled, NoTranscriptFound):
            continue
        except Exception as e:
            print(f"Failed for {video_id}: {e}")
            continue

    if not results:
        return {"status": "no_transcripts"}

    doc = Document()
    doc.add_heading("YouTube Transcript", level=1)

    for video in results:
        doc.add_heading(video["title"], level=2)
        doc.add_paragraph(video["url"])
        for entry in video["transcript"]:
            doc.add_paragraph(f"{entry['start']:.1f}s: {entry['text']}")
        doc.add_page_break()

    filename = f"transcripts_{uuid.uuid4().hex[:8]}.docx"
    path = os.path.join(FILES_DIR, filename)
    doc.save(path)

    return {
        "status": "success",
        "file": filename,
        "count": len(results)
    }

@app.get("/files/{filename}")
def serve_file(filename: str):
    path = os.path.join(FILES_DIR, filename)
    if not os.path.exists(path):
        return {"message": "File not found"}
    return {"message": "File found"}
