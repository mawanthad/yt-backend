from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
import uuid
import os
from docx import Document

app = FastAPI()

# Allow CORS for any origin (or restrict to Vercel domain if needed)
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
    url = data.url.strip()

    if "watch?v=" not in url:
        return {"status": "error", "message": "Please provide a valid YouTube video URL"}

    video_id = url.split("watch?v=")[-1].split("&")[0]

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
    except Exception as e:
        return {"status": "error", "message": str(e)}

    doc = Document()
    doc.add_heading("YouTube Transcript", level=1)
    for entry in transcript:
        doc.add_paragraph(f"{entry['start']:.2f}s: {entry['text']}")

    filename = f"transcript_{uuid.uuid4().hex[:8]}.docx"
    filepath = os.path.join(FILES_DIR, filename)
    doc.save(filepath)

    return {
        "status": "success",
        "file": filename,
        "count": len(transcript)
    }

@app.get("/files/{filename}")
def serve_file(filename: str):
    path = os.path.join(FILES_DIR, filename)
    if os.path.exists(path):
        return {"message": "File found"}
    return {"message": "File not found"}
