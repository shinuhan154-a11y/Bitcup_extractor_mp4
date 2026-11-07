
import re
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import yt_dlp

app = FastAPI(title="BitChute Video Extractor")

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
    return {
        "status": "BitChute Extractor Online"
    }


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
            "Video extraction failed or source unavailable."
        )

    formats = []
    seen = set()

    for f in info.get("formats", []):

        video_url = f.get("url")

        if not video_url:
            continue

        if f.get("vcodec") in [None, "none"]:
            continue

        ext = f.get("ext", "")

        if ext not in ["mp4", "webm", "m3u8"]:
            continue

        format_id = f.get("format_id")
        height = f.get("height")
        width = f.get("width")
        fps = f.get("fps")

        audio = f.get("acodec") not in [
            None, "none"
        ]

        quality = (
            f"{height}p"
            if height
            else f.get("format_note") or "Unknown"
        )

        unique_key = (
            format_id,
            height,
            ext,
            f.get("acodec"),
            f.get("vcodec")
        )

        if unique_key in seen:
            continue

        seen.add(unique_key)

        formats.append({
            "quality": quality,
            "height": height,
            "width": width,
            "fps": fps,
            "format": ext,
            "format_id": format_id,
            "has_audio": audio,
            "video_codec": f.get("vcodec"),
            "audio_codec": f.get("acodec"),
            "filesize": (
                f.get("filesize")
                or f.get("filesize_approx")
            ),
            "url": video_url
        })

    formats.sort(
        key=lambda x: (
            x["height"] or 0,
            x["fps"] or 0,
            x["format"] == "mp4",
            x["has_audio"]
        ),
        reverse=True
    )

    mp4_formats = [
        f for f in formats
        if f["format"] == "mp4"
    ]

    qualities = sorted(
        set(
            f["quality"]
            for f in formats
            if f["height"]
        ),
        key=lambda q: int(q.replace("p", "")),
        reverse=True
    )

    return {
        "title": info.get("title"),
        "thumbnail": info.get("thumbnail"),
        "duration": info.get("duration"),
        "formats": formats,
        "mp4_formats": mp4_formats,
        "available_qualities": qualities,
        "total_formats": len(formats),
        "total_mp4_formats": len(mp4_formats)
    }
