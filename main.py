from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build
from docx import Document
import uuid
import os

API_KEY = "AIzaSyDqwXBSlJGspFzMFGTvat2gx5X8H-m5Xn8"

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Serve generated .docx files at /files/*
app.mount("/files", StaticFiles(directory=os.getcwd()), name="files")

class ChannelRequest(BaseModel):
    url: str

@app.post("/scrape")
def scrape_transcripts(data: ChannelRequest):
    url = data.url
    try:
        channel_id = resolve_channel_id(url)
        videos = get_videos_from_channel(channel_id, max_results=5)
        results = []

        for video in videos:
            transcript = fetch_transcript(video["video_id"])
            if transcript:
                video["transcript"] = transcript
                results.append(video)

        if results:
            filename = create_doc(results)
            return {
                "status": "success",
                "file": filename,
                "count": len(results)
            }
        else:
            return {"status": "no_transcripts"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def resolve_channel_id(input_url):
    youtube = build("youtube", "v3", developerKey=API_KEY)
    if "/channel/" in input_url:
        return input_url.split("/")[-1]
    identifier = input_url.strip("/").split("/")[-1].replace("@", "")
    request = youtube.search().list(
        part="snippet", q=identifier, type="channel", maxResults=1
    )
    response = request.execute()
    return response["items"][0]["snippet"]["channelId"]

def get_videos_from_channel(channel_id, max_results=10):
    youtube = build("youtube", "v3", developerKey=API_KEY)
    request = youtube.search().list(
        part="snippet",
        channelId=channel_id,
        maxResults=max_results,
        order="date"
    )
    response = request.execute()
    videos = []
    for item in response["items"]:
        if item["id"]["kind"] == "youtube#video":
            vid_id = item["id"]["videoId"]
            stats = youtube.videos().list(part="statistics", id=vid_id).execute()
            views = stats["items"][0]["statistics"].get("viewCount", "0")
            videos.append({
                "video_id": vid_id,
                "title": item["snippet"]["title"],
                "date": item["snippet"]["publishedAt"][:10],
                "views": views
            })
    return videos

def fetch_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return "\n".join([x["text"] for x in transcript])
    except:
        return None

def create_doc(videos):
    doc = Document()
    for video in videos:
        doc.add_heading(video["title"], level=1)
        doc.add_paragraph(f"📅 Uploaded: {video['date']}")
        doc.add_paragraph(f"👁 Views: {video['views']}")
        doc.add_paragraph(video["transcript"])
        doc.add_page_break()
    filename = f"transcripts_{uuid.uuid4().hex[:8]}.docx"
    doc.save(filename)
    return filename

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
