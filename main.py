import os
import json
import re
import shutil
from pathlib import Path

import requests

from drive_service import (
    get_drive_service,
    find_folder_id,
    list_audio_files_in_folder,
    download_drive_file,
)

# 🔥 IMPORT NOVO
from background_selector import detect_style, detect_styles, get_random_background

from video_generator import create_short
from youtube_service import upload_video
from ai_image_generator import generate_image

STATE_FILE = Path("state.json")
SHORTS_PER_TRACK = 3
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")

SPOTIFY_LINK = "https://open.spotify.com/intl-pt/artist/1zyM1Pyi4YLAQgrSVRAYEy?si=3fQcRGwSQ8O2vsqq6jOVow"
TIKTOK_LINK = "https://www.tiktok.com/@darkmrkedit?is_from_webapp=1&sender_device=pc"


def load_state():
    if not STATE_FILE.exists():
        return {"tracks": [], "queue_index": 0}

    with STATE_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def clean_title(filename):
    name = Path(filename).stem
    name = re.sub(r"\[[^\]]+\]", "", name)
    name = re.sub(r"[_\-]+", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name.title()


# 🔥 NOVO: METADATA INTELIGENTE
def build_video_metadata(filename, short_number, style, styles):
    base_title = clean_title(filename)

    secondary = styles[1] if len(styles) > 1 else None
    hybrid = f"{style} x {secondary}" if secondary else style

    title = f"{base_title} | {hybrid.title()} Music 🔥"

    description = (
        f"{base_title}\n\n"
        f"Main style: {style}\n"
        f"Detected: {', '.join(styles)}\n\n"
        f"🎧 Spotify:\n{SPOTIFY_LINK}\n\n"
        f"📲 TikTok:\n{TIKTOK_LINK}\n\n"
        f"#music #shorts #{style} #viral"
    )

    tags = [base_title.lower(), style]
    for s in styles:
        tags.append(s)
        tags.append(f"{s} music")

    return title, description, tags


# 🔥 NOVO: PROMPT HÍBRIDO
def build_ai_prompt(style, filename, styles):
    hybrid = " and ".join(styles)

    return f"""
    cinematic scene, {hybrid} atmosphere,
    dark, dramatic, intense lighting,
    ultra detailed, emotional, not generic,
    no text, no watermark, vertical 9:16
    """


def resolve_background(style, filename, short_number, styles):
    try:
        background = get_random_background(style, filename)
        if background and not str(background).startswith("__AUTO"):
            return background
    except:
        pass

    print("Gerando imagem IA...")

    safe_name = Path(filename).stem.replace(" ", "_")
    cached_path = os.path.join("temp", f"{safe_name}_{short_number}.png")

    prompt = build_ai_prompt(style, filename, styles)

    image_result = generate_image(prompt)

    if os.path.exists(image_result):
        shutil.copy2(image_result, cached_path)
        return cached_path

    raise RuntimeError("Falha IA")


def main():
    print("Bot iniciado")

    state = load_state()
    service = get_drive_service()

    inbox_id = find_folder_id(service, DRIVE_FOLDER_ID, "inbox")
    files = list_audio_files_in_folder(service, inbox_id)

    sync = {f["name"]: f for f in files}

    # adiciona novos
    for name, file in sync.items():
        if not any(t["name"] == name for t in state["tracks"]):
            state["tracks"].append({
                "id": file["id"],
                "name": name,
                "shorts_done": 0,
                "done": False,
                "is_new": True
            })

    # pega próximo
    track = next((t for t in state["tracks"] if not t["done"]), None)

    if not track:
        print("Nada pra postar")
        return

    name = track["name"]

    # 🔥 DETECÇÃO INTELIGENTE
    styles = detect_styles(name)
    style = detect_style(name)

    print("Estilos:", styles)
    print("Principal:", style)

    audio_path = f"temp/{name}"
    download_drive_file(service, track["id"], audio_path)

    short_number = track["shorts_done"] + 1

    bg = resolve_background(style, name, short_number, styles)

    video_path = create_short(audio_path, bg, f"{name}.mp4", style)

    title, desc, tags = build_video_metadata(name, short_number, style, styles)

    upload_video(video_path, title, desc, tags, "public")

    track["shorts_done"] += 1
    if track["shorts_done"] >= SHORTS_PER_TRACK:
        track["done"] = True

    save_state(state)


if __name__ == "__main__":
    main()
