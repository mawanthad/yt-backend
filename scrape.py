from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, VideoUnavailable, NoTranscriptAvailable

def get_transcript(video_id: str):
    """
    Fetches the transcript for a given YouTube video ID.
    """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return transcript
    except VideoUnavailable:
        raise Exception("The video is unavailable.")
    except TranscriptsDisabled:
        raise Exception("Transcripts are disabled for this video.")
    except NoTranscriptAvailable:
        raise Exception("No transcript available for this video.")
    except Exception as e:
        raise Exception(f"An error occurred: {str(e)}")
