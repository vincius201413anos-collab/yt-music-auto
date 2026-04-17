import requests
import os

FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")


def upload_facebook_reel(video_path, caption):
    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/video_reels"

    files = {
        "video_file": open(video_path, "rb")
    }

    data = {
        "description": caption,
        "access_token": FB_TOKEN
    }

    response = requests.post(url, files=files, data=data)
    print("FB RESPONSE:", response.text)
    return response.json()
