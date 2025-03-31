from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import os
import uuid
from yt_transcript_api import YouTubeTranscriptApi
from docx import Document

app = FastAPI()

# CORS settings
origins = [
    "http://localhost:3000",
    "https://yt-transcript-app-delta.vercel.app"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

FILES_DIR = "files"
os.makedirs(FILES_DIR, exist_ok=True)

class ScrapeRequest(BaseModel):
    url: str

@app.post("/scrape")
async def scrape_channel(data: ScrapeRequest):
    from yt_scraper import scrape_channel_transcripts  # adjust based on structure

    try:
        video_data = scrape_channel_transcripts(data.url)
        if not video_data:
            return JSONResponse(content={"status": "no_transcripts"})

        doc = Document()
        doc.add_heading("YouTube Transcripts", 0)
        for video in video_data:
            doc.add_heading(video["title"], level=1)
            doc.add_paragraph(f"📅 Uploaded: {video['date']}")
            doc.add_paragraph(f"👁️ Views: {video['views']}")
            doc.add_paragraph(video["transcript"])
            doc.add_page_break()

        filename = f"transcripts_{uuid.uuid4().hex[:8]}.docx"
        path = os.path.join(FILES_DIR, filename)
        doc.save(path)

        return {
            "status": "success",
            "file": filename,
            "count": len(video_data)
        }

    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)})

@app.get("/files/{filename}")
def get_file(filename: str):
    path = os.path.join(FILES_DIR, filename)
    if os.path.exists(path):
        return FileResponse(path, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    return JSONResponse(content={"message": "File not found"}, status_code=404)

@app.get("/")
def read_root():
    return {"message": "Server is live!"}
