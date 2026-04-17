import os
import json
import random
import time
from pathlib import Path
from datetime import datetime

from drive_service import (
    get_drive_service,
    list_audio_files_in_folder,
    download_drive_file,
    upload_file_to_drive,
)

from video_generator import create_short
from youtube_service import upload_video
from facebook_service import upload_facebook_reel

# CONFIG
STATE_FILE = Path("state.json")
SHORTS_PER_TRACK = 3
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")

# ===== UTILS =====

def log(msg):
    print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] {msg}")

def clean_title(name):
    return Path(name).stem.replace("_", " ").title()

# ===== STATE =====

def load_state():
    if not STATE_FILE.exists():
        return {"tracks": [], "index": 0}

    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

# ===== MAIN =====

def main():
    log("BOT INICIANDO...")

    service = get_drive_service()
    files = list_audio_files_in_folder(service, DRIVE_FOLDER_ID)

    state = load_state()

    if not files:
        log("Nenhum áudio encontrado.")
        return

    # sincroniza
    existing_names = {t["name"] for t in state["tracks"]}
    for f in files:
        if f["name"] not in existing_names:
            state["tracks"].append({
                "id": f["id"],
                "name": f["name"],
                "done": 0
            })

    if not state["tracks"]:
        log("Sem músicas.")
        return

    # pega próxima música
    track = state["tracks"][state["index"] % len(state["tracks"])]

    name = track["name"]
    short_num = track["done"] + 1

    log(f"Processando: {name} (Short {short_num})")

    os.makedirs("temp", exist_ok=True)
    audio_path = f"temp/{name}"

    # download
    download_drive_file(service, track["id"], audio_path)

    # gera vídeo
    video_path = f"temp/video_{short_num}.mp4"

    create_short(audio_path, None, video_path, "default")

    title = clean_title(name)
    description = f"{title} 🔥\n\n#shorts #viral #music"

    # ===== YOUTUBE =====
    try:
        log("Postando no YouTube...")
        res = upload_video(video_path, title, description, [], "public")
        log(f"YouTube OK: {res.get('id')}")
    except Exception as e:
        log(f"Erro YouTube: {e}")

    # ===== FACEBOOK =====
    try:
        log("Postando no Facebook...")
        upload_facebook_reel(video_path, title)
        log("Facebook OK")
    except Exception as e:
        log(f"Erro Facebook: {e}")

    # ===== BACKUP DRIVE =====
    try:
        backup_folder = DRIVE_FOLDER_ID
        upload_file_to_drive(service, backup_folder, video_path)
        log("Backup salvo no Drive")
    except Exception as e:
        log(f"Erro backup: {e}")

    # ===== LIMPEZA =====
    try:
        os.remove(audio_path)
        os.remove(video_path)
        log("Arquivos temporários apagados")
    except:
        pass

    # ===== ATUALIZA STATE =====
    track["done"] += 1
    if track["done"] >= SHORTS_PER_TRACK:
        track["done"] = 0
        state["index"] += 1

    save_state(state)

    log("FINALIZADO")

# ===== RUN =====

if __name__ == "__main__":
    main()
