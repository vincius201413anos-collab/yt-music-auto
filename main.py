import os
import json
import re
import shutil
import random
from pathlib import Path
from datetime import datetime

from drive_service import (
    get_drive_service,
    find_folder_id,
    list_audio_files_in_folder,
    download_drive_file,
    upload_file_to_drive,
)
from background_selector import detect_style, detect_styles, get_random_background
from video_generator import create_short
from youtube_service import upload_video
from ai_image_generator import generate_image, build_ai_prompt

STATE_FILE = Path("state.json")
SHORTS_PER_TRACK = 3
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")

SPOTIFY_LINK = "https://open.spotify.com/intl-pt/artist/1zyM1Pyi4YLAQgrSVRAYEy?si=3fQcRGwSQ8O2vsqq6jOVow"
TIKTOK_LINK = "https://www.tiktok.com/@darkmrkedit?is_from_webapp=1&sender_device=pc"


# =========================
# STATE
# =========================

def load_state():
    if not STATE_FILE.exists():
        return {"tracks": [], "queue_index": 0}

    with STATE_FILE.open("r", encoding="utf-8") as f:
        state = json.load(f)

    state.setdefault("tracks", [])
    state.setdefault("queue_index", 0)

    return state


def save_state(state):
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# =========================
# UTIL
# =========================

def clean_title(filename):
    name = Path(filename).stem
    name = re.sub(r"\[[^\]]+\]", "", name)
    name = re.sub(r"[_\-]+", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name.title()


def safe_filename(text):
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "_", text)
    return text[:60]


def generate_viral_title(base_title, style):
    hooks = [
        "Wait For This 😳", "This Drop Hits HARD 🔥", "Don’t Skip This 😳",
        "This Part Goes CRAZY 🤯", "This Feels Illegal 😈",
        "This Is Addictive 🔁", "Loop This 🔥",
        "You’ll Replay This 😳", "This Gets Better Every Loop 🔁"
    ]

    return f"{random.choice(hooks)} | {base_title}"


def build_output_path(base_title, style, short_number):
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    base_clean = safe_filename(base_title)

    folder = Path("output") / date_str / style
    folder.mkdir(parents=True, exist_ok=True)

    filename = f"{date_str}__{style}__{base_clean}__short_{short_number}.mp4"

    return str(folder / filename)


# =========================
# TRACK CONTROL
# =========================

def sync_tracks(state, drive_files):
    existing = {t["name"]: t for t in state["tracks"]}

    for file in drive_files:
        if file["name"] not in existing:
            state["tracks"].append({
                "id": file["id"],
                "name": file["name"],
                "shorts_done": 0,
                "done": False,
                "is_new": True
            })
        else:
            existing[file["name"]]["id"] = file["id"]

    drive_names = {f["name"] for f in drive_files}
    state["tracks"] = [t for t in state["tracks"] if t["name"] in drive_names]


def get_next_track(state):
    for t in state["tracks"]:
        if t.get("is_new"):
            t["is_new"] = False
            return t

    for t in state["tracks"]:
        if t["shorts_done"] < SHORTS_PER_TRACK:
            return t

    for t in state["tracks"]:
        t["shorts_done"] = 0
        t["done"] = False

    return state["tracks"][0] if state["tracks"] else None


# =========================
# BACKGROUND
# =========================

def resolve_background(style, filename, short_number, styles):
    try:
        bg = get_random_background(style, filename)
        if bg and not str(bg).startswith("__AUTO"):
            return bg
    except:
        pass

    os.makedirs("temp", exist_ok=True)

    prompt = build_ai_prompt(style, filename, styles)
    img = generate_image(prompt)

    if img and os.path.exists(img):
        cached = f"temp/{Path(filename).stem}_{short_number}.png"
        shutil.copy2(img, cached)
        return cached

    return "assets/backgrounds/default.jpg"


# =========================
# MAIN
# =========================

def main():
    print("BOT INICIADO")

    state = load_state()
    service = get_drive_service()

    inbox_id = find_folder_id(service, DRIVE_FOLDER_ID, "inbox")
    files = list_audio_files_in_folder(service, inbox_id)

    sync_tracks(state, files)

    track = get_next_track(state)
    if not track:
        print("Nada pra postar")
        return

    name = track["name"]
    print(f"Processando: {name}")

    styles = detect_styles(name)
    style = detect_style(name)

    base_title = clean_title(name)

    os.makedirs("temp", exist_ok=True)
    audio_path = f"temp/{name}"

    download_drive_file(service, track["id"], audio_path)

    short_number = track["shorts_done"] + 1

    bg = resolve_background(style, name, short_number, styles)

    output_path = build_output_path(base_title, style, short_number)

    print("Gerando vídeo...")
    video_path = create_short(audio_path, bg, output_path, style)

    title = generate_viral_title(base_title, style)

    desc = f"{base_title}\n\n🎧 Spotify:\n{SPOTIFY_LINK}\n\n📲 TikTok:\n{TIKTOK_LINK}"

    tags = ["music", "shorts", style]

    print("Upload YouTube...")
    upload_video(video_path, title, desc, tags, "public")

    track["shorts_done"] = short_number
    save_state(state)

    print("FINALIZADO")


if __name__ == "__main__":
    main()
