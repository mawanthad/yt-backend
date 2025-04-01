from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import uuid
from docx import Document
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
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

    # If it's not a full link, use ytsearch
    if not input_url.startswith("http"):
        search_url = f"ytsearch10:{input_url}"  # fetch top 10 results
    else:
        search_url = input_url

    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": True,
        "force_generic_extractor": False,
        "dump_single_json": True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_url, download=False)
            videos = info["entries"] if "entries" in info else [info]
    except Exception as e:
        return {"status": "error", "message": str(e)}

    results = []
    for video in videos:
        video_id = video.get("id")
        if not video_id:
            continue
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            results.append({
                "title": video.get("title", "Untitled"),
                "url": f"https://youtu.be/{video_id}",
                "transcript": transcript
            })
        except TranscriptsDisabled:
            continue
        except Exception:
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
    if not os.path.isfile(path):
        return {"message": "File not found"}
    return {"message": "File found"}
