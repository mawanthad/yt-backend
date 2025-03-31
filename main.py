from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
from scrape import get_transcripts, create_doc

app = FastAPI()

# ✅ Allow requests from your frontend domain
origins = [
    "https://yt-transcript-app-delta.vercel.app",  # your frontend
    "http://localhost:3000",  # for local dev
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScrapeRequest(BaseModel):
    url: str

@app.post("/scrape")
async def scrape_endpoint(payload: ScrapeRequest):
    url = payload.url
    try:
        videos = get_transcripts(url)
        if not videos:
            return {"status": "no_transcripts"}

        filename = create_doc(videos)
        return {
            "status": "success",
            "file": filename,
            "count": len(videos)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/files/{filename}")
async def download_file(filename: str):
    filepath = os.path.join("files", filename)
    if os.path.exists(filepath):
        return FileResponse(filepath, filename=filename)
    return {"error": "File not found"}
