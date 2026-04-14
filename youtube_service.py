import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_youtube_service():
    credentials_json = os.getenv("YOUTUBE_CREDENTIALS")
    if not credentials_json:
        raise ValueError("Secret YOUTUBE_CREDENTIALS não encontrado.")

    creds = Credentials.from_authorized_user_info(
        json.loads(credentials_json),
        scopes=YOUTUBE_SCOPES
    )

    service = build("youtube", "v3", credentials=creds)
    return service


def upload_video(video_path, title, description="", tags=None, privacy_status="public"):
    if tags is None:
        tags = []

    youtube = get_youtube_service()

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "10"
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()

    return response
