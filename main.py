from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from scrape import get_transcript

app = FastAPI()

# Configure CORS
origins = [
    "http://localhost:3000",  # Adjust based on your frontend's URL
    "https://your-frontend-domain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/transcript/")
async def fetch_transcript(video_url: str = Query(..., title="YouTube Video URL")):
    """
    Endpoint to fetch the transcript of a YouTube video given its URL.
    """
    # Extract video ID from the URL
    try:
        video_id = video_url.split("v=")[1].split("&")[0]
    except IndexError:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL format.")

    try:
        transcript = get_transcript(video_id)
        return {"transcript": transcript}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
