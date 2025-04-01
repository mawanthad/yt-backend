from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
import yt_dlp
import uuid
import os
import time
from docx import Document

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict this in production
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

    # Allow @handles or channel links
    if not input_url.startswith("http"):
        input_url = f"ytsearch3:{input_url}"
    elif "watch?v=" in input_url:
        input_url = input_url  # video URL
    else:
        input_url = f"ytsearch3:{input_url}"

    print(f"🔍 Searching via yt_dlp: {input_url}")

    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(input_url, download=False)
            videos = info.get("entries", [])
    except Exception as e:
        return {"status": "error", "message": f"Failed to get videos: {str(e)}"}

    if not videos:
        return {"status": "error", "message": "No videos found."}

    results = []

    for video in videos[:3]:  # limit to 3 for now
        vid = video.get("id")
        title = video.get("title", "Untitled")

        try:
            transcript = YouTubeTranscriptApi.get_transcript(vid)
            results.append({
                "title": title,
                "url": f"https://youtube.com/watch?v={vid}",
                "transcript": transcript
            })
            print(f"✅ Transcript for {vid}")
        except TranscriptsDisabled:
            print(f"⚠️ No transcript for {vid} (disabled)")
        except Exception as e:
            print(f"⚠️ Error for {vid}: {e}")
        time.sleep(2)

    if not results:
        return {"status": "no_transcripts"}

    doc = Document()
    doc.add_heading("YouTube Transcript", level=1)
    for video in results:
        doc.add_heading(video["title"], level=2)
        doc.add_paragraph(video["url"])
        for line in video["transcript"]:
            doc.add_paragraph(f"{line['start']:.2f}s: {line['text']}")
        doc.add_page_break()

    filename = f"transcripts_{uuid.uuid4().hex[:8]}.docx"
    full_path = os.path.join(FILES_DIR, filename)
    doc.save(full_path)

    print(f"📁 Transcript saved as: {filename}")
    return {
        "status": "success",
        "file": filename,
        "count": len(results)
    }

@app.get("/files/{filename}")
def serve_file(filename: str):
    path = os.path.join(FILES_DIR, filename)
    if os.path.exists(path):
        return {"message": "File ready"}
    return {"message": "File not found"}
