
import re
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import yt_dlp

app = FastAPI(title="BitChute MP4 Extractor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
    url: HttpUrl

def validate_url(url):
    parsed = urlparse(url)

    if parsed.scheme != "https":
        raise HTTPException(400, "HTTPS required")

    if parsed.hostname not in [
        "bitchute.com",
        "www.bitchute.com"
    ]:
        raise HTTPException(400, "BitChute URLs only")

    if not re.search(r"/(video|embed)/[A-Za-z0-9]+", parsed.path):
        raise HTTPException(400, "Invalid video URL")

    return url

@app.get("/")
def home():
    return {"status": "BitChute Extractor Online"}

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/api/extract")
def extract_video(data: VideoRequest):

    url = validate_url(str(data.url))

    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        "socket_timeout": 20,
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)

    except Exception:
        raise HTTPException(
            502,
            "Video source unavailable or extractor failed."
        )

    formats = []

    for f in info.get("formats", []):

        if not f.get("url"):
            continue

        if f.get("vcodec") == "none":
            continue

        ext = f.get("ext", "")

        if ext not in ["mp4", "m3u8", "webm"]:
            continue

        formats.append({
            "quality": str(f.get("height") or "Unknown") + "p",
            "format": ext,
            "format_id": f.get("format_id"),
            "url": f.get("url")
        })

    return {
        "title": info.get("title"),
        "formats": formats,
        "total_formats": len(formats)
    }
  
