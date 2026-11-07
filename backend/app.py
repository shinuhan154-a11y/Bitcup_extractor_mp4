
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
    parsed = urlparse(str(url))

    if parsed.scheme != "https":
        raise HTTPException(400, "HTTPS required")

    if parsed.hostname not in [
        "bitchute.com",
        "www.bitchute.com"
    ]:
        raise HTTPException(400, "BitChute URLs only")

    if not re.search(
        r"/(video|embed)/[A-Za-z0-9]+",
        parsed.path
    ):
        raise HTTPException(400, "Invalid video URL")

    return str(url)


@app.get("/")
def home():
    return {"status": "BitChute Extractor Online"}


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/api/extract")
def extract_video(data: VideoRequest):

    url = validate_url(data.url)

    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        "socket_timeout": 30,
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(
                url,
                download=False
            )

    except Exception as e:
        raise HTTPException(
            502,
            "Video extraction failed: " + str(e)[:300]
        )

    formats = []
    seen_urls = set()

    for f in info.get("formats", []):

        video_url = f.get("url")

        if not video_url or video_url in seen_urls:
            continue

        if f.get("vcodec") == "none":
            continue

        ext = f.get("ext", "")

        if ext not in ["mp4", "webm", "m3u8"]:
            continue

        height = f.get("height")

        audio = f.get("acodec") not in [
            None,
            "none"
        ]

        quality = (
            f"{height}p"
            if height
            else f.get("format_note") or "Unknown"
        )

        formats.append({
            "quality": quality,
            "height": height,
            "width": f.get("width"),
            "fps": f.get("fps"),
            "format": ext,
            "format_id": f.get("format_id"),
            "has_audio": audio,
            "filesize": (
                f.get("filesize")
                or f.get("filesize_approx")
            ),
            "url": video_url
        })

        seen_urls.add(video_url)

    formats.sort(
        key=lambda f: (
            f["height"] or 0,
            f["fps"] or 0,
            f["format"] == "mp4",
            f["has_audio"]
        ),
        reverse=True
    )

    mp4_formats = [
        f for f in formats
        if f["format"] == "mp4"
    ]

    available_qualities = list(
        dict.fromkeys(
            f["quality"] for f in mp4_formats
        )
    )

    return {
        "title": info.get("title"),
        "thumbnail": info.get("thumbnail"),
        "formats": formats,
        "mp4_formats": mp4_formats,
        "available_qualities": available_qualities,
        "total_formats": len(formats),
        "total_mp4_formats": len(mp4_formats)
    }
