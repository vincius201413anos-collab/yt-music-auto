import os
import requests

FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")


def upload_facebook_reel(video_path, caption):
    if not FB_PAGE_ID or not FB_TOKEN:
        raise ValueError("FB_PAGE_ID ou FB_PAGE_ACCESS_TOKEN não configurado.")

    url = f"https://graph.facebook.com/v23.0/{FB_PAGE_ID}/video_reels"

    with open(video_path, "rb") as video_file:
        files = {
            "source": video_file
        }
        data = {
            "description": caption,
            "access_token": FB_TOKEN
        }
        response = requests.post(url, files=files, data=data, timeout=120)

    response.raise_for_status()
    return response.json()
