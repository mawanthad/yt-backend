from fastapi import FastAPI, Request
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
    allow_origins=["*"],  # Change to your frontend domain for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FILES_DIR = "files"
os.makedirs(FILES_DIR, exist_ok=True)

class ScrapeRequest(BaseModel):
    url: str

def get_video_urls_from_channel(channel_url: str, max_videos: int = 5):
    ydl_opts = {
        'extract_flat': True,
        'force_generic_extractor': True,
        'quiet': True,
    }

    video_urls = []

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(channel_url, download=False)
        entries = info.get('entries', [])
        for entry in entries[:max_videos]:
            video_urls.append(f"https://www.youtube.com/watch?v={entry['id']}")
    
    return video_urls

@app.post("/scrape")
async def scrape_transcripts(data: ScrapeRequest):
    channel_url = data.url.strip()

    try:
        video_urls = get_video_urls_from_channel(channel_url)
    except Exception as e:
        return {"status": "error", "message": f"Failed to fetch videos: {e}"}

    transcripts = []
    success_count = 0

    for url in video_urls:
        video_id = url.split("v=")[-1]
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            transcripts.append({
                "url": url,
                "transcript": transcript
            })
            success_count += 1
        except:
            continue  # Skip if transcript isn't available

    if not transcripts:
        return {"status": "no_transcripts"}

    # Create DOCX
    doc = Document()
    doc.add_heading("YouTube Channel Transcripts", level=1)

    for video in transcripts:
        doc.add_heading(f"Video: {video['url']}", level=2)
        for item in video['transcript']:
            doc.add_paragraph(f"{item['start']:.2f}s: {item['text']}")
        doc.add_page_break()

    filename = f"transcripts_{uuid.uuid4().hex[:8]}.docx"
    path = os.path.join(FILES_DIR, filename)
    doc.save(path)

    return {
        "status": "success",
        "file": filename,
        "count": success_count
    }

@app.get("/files/{filename}")
def serve_file(filename: str):
    path = os.path.join(FILES_DIR, filename)
    if not os.path.isfile(path):
        return {"message": "File not found"}
    return {"message": "File found"}
