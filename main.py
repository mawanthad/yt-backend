from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
import uuid
import os
from docx import Document

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict to your frontend domain
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
    channel_url = data.url.strip()

    # Simplified: expects full YouTube video URL
    if "watch?v=" not in channel_url:
        return {"status": "error", "message": "Please provide a valid video URL."}

    video_id = channel_url.split("watch?v=")[-1]
    
    try:
        transcripts = YouTubeTranscriptApi.get_transcript(video_id)
    except Exception as e:
        return {"status": "error", "message": str(e)}

    # Create DOCX
    doc = Document()
    doc.add_heading("YouTube Transcript", level=1)
    for item in transcripts:
        doc.add_paragraph(f"{item['start']:.2f}s: {item['text']}")

    filename = f"transcript_{uuid.uuid4().hex[:8]}.docx"
    path = os.path.join(FILES_DIR, filename)
    doc.save(path)

    return {
        "status": "success",
        "file": filename,
        "count": len(transcripts)
    }

@app.get("/files/{filename}")
def serve_file(filename: str):
    path = os.path.join(FILES_DIR, filename)
    if not os.path.isfile(path):
        return {"message": "File not found"}
    return {"message": "File found"}
