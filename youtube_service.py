"""
youtube_service.py — Upload para YouTube com retry robusto.
"""

import os
import json
import time
import random
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

MAX_RETRIES    = 5
RETRY_STATUS   = {500, 502, 503, 504}


def get_youtube_service():
    raw = os.getenv("YOUTUBE_CREDENTIALS")
    if not raw:
        raise ValueError("Secret YOUTUBE_CREDENTIALS não encontrado.")
    creds = Credentials.from_authorized_user_info(
        json.loads(raw), scopes=YOUTUBE_SCOPES
    )
    return build("youtube", "v3", credentials=creds)


def upload_video(
    video_path: str,
    title: str,
    description: str = "",
    tags: list = None,
    privacy_status: str = "public",
) -> dict:
    if tags is None:
        tags = []

    youtube = get_youtube_service()

    body = {
        "snippet": {
            "title":       title[:100],
            "description": description[:5000],
            "tags":        tags[:500],
            "categoryId":  "10",   # Music
        },
        "status": {
            "privacyStatus":           privacy_status,
            "selfDeclaredMadeForKids": False,
            "madeForKids":             False,
        },
    }

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        chunksize=8 * 1024 * 1024,   # 8 MB chunks
        resumable=True,
    )

    request  = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response   = None
    retry      = 0
    error_msg  = None

    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                print(f"  Upload: {pct}%")
        except HttpError as e:
            if e.resp.status in RETRY_STATUS and retry < MAX_RETRIES:
                wait = (2 ** retry) + random.random()
                print(f"  Erro {e.resp.status}, tentando novamente em {wait:.1f}s…")
                time.sleep(wait)
                retry += 1
            else:
                raise
        except Exception as e:
            if retry < MAX_RETRIES:
                wait = (2 ** retry) + random.random()
                print(f"  Erro inesperado: {e}. Retry em {wait:.1f}s…")
                time.sleep(wait)
                retry += 1
            else:
                raise

    print(f"  Upload concluído! Video ID: {response.get('id')}")
    return response
