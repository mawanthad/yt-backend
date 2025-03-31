from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import uuid
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, set to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FILES_DIR = "files"
os.makedirs(FILES_DIR, exist_ok=True)

class ScrapeRequest(BaseModel):
    url: str

@app.get("/")
def read_root():
    return {"message": "YouTube Transcript Scraper Backend is Live"}

@app.post("/scrape")
async def scrape_transcripts(req: ScrapeRequest):
    # Placeholder implementation
    if not req.url.startswith("http"):
        return JSONResponse(status_code=400, content={"status": "error", "message": "Invalid URL"})

    filename = f"transcripts_{uuid.uuid4().hex[:8]}.docx"
    file_path = os.path.join(FILES_DIR, filename)

    # Simulate writing transcript
    with open(file_path, "w") as f:
        f.write(f"Transcripts for {req.url}")

    return {
        "status": "success",
        "file": filename,
        "count": 1,
    }

@app.get("/files/{filename}")
def get_file(filename: str):
    file_path = os.path.join(FILES_DIR, filename)
    if os.path.exists(file_path):
        return JSONResponse(content={"message": "File found"}, status_code=200)
    return JSONResponse(content={"message": "File not found"}, status_code=404)