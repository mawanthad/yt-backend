from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
import uuid
import os
import time
from docx import Document

app = FastAPI()

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this with your frontend URL for better security
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
    print(f"📥 Received URL: {data.url}")
    input_url = data.url.strip()

    # Accept handles like @veritasium directly
    if not input_url.startswith("http"):
        input_url = f"ytsearch2:{input_url}"

    print(f"🔍 Using yt_dlp to fetch videos from: {input_url}")

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
        print(f"❌ yt_dlp error: {str(e)}")
        return {"status": "error", "message": f"yt_dlp error: {str(e)}"}

    print(f"🎥 Found {len(videos)} videos")
    if not videos:
        return {"status": "error", "message": "No videos found."}

    results = []
    for video in videos[:3]:  # Limit to 3 videos for speed
        vid_id = video.get("id")
        title = video.get("title", "Untitled")
        print(f"📝 Attempting transcript for: {title} ({vid_id})")

        try:
            transcript = YouTubeTranscriptApi.get_transcript(vid_id)
            results.append({
                "title": title,
                "url": f"https://youtube.com/watch?v={vid_id}",
                "transcript": transcript
            })
            print(f"✅ Transcript retrieved for {vid_id}")
        except Exception as e:
            print(f"⚠️ Failed to fetch transcript for {vid_id}: {str(e)}")

        time.sleep(2)

    if not results:
        print("⚠️ No transcripts found.")
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
    print(f"📁 File saved at: {full_path}")

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
