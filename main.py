import os
import json
from pathlib import Path
from datetime import datetime

from drive_service import (
    get_drive_service,
    find_folder_id,
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

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


# ===== MAIN =====

def main():
    log("BOT INICIANDO...")

    if not DRIVE_FOLDER_ID:
        raise ValueError("DRIVE_FOLDER_ID não configurado.")

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

    # evita index quebrado
    state["index"] = state["index"] % len(state["tracks"])

    # pega próxima música
    track = state["tracks"][state["index"]]

    name = track["name"]
    short_num = track["done"] + 1

    log(f"Processando: {name} (Short {short_num})")

    os.makedirs("temp", exist_ok=True)

    # mantém extensão original do arquivo
    audio_path = f"temp/{name}"
    video_path = f"temp/video_{short_num}.mp4"

    try:
        # download
        log("Baixando áudio do Drive...")
        download_drive_file(service, track["id"], audio_path)
        log("Download concluído.")

        # gera vídeo
        log("Gerando vídeo...")
        create_short(audio_path, None, video_path, "default")
        log(f"Vídeo gerado: {video_path}")

        title = clean_title(name)
        description = f"{title} 🔥\n\n#shorts #viral #music"

        # ===== YOUTUBE =====
        try:
            log("Postando no YouTube...")
            res = upload_video(video_path, title, description, [], "public")
            video_id = res.get("id") if isinstance(res, dict) else None
            log(f"YouTube OK: {video_id}")
        except Exception as e:
            log(f"Erro YouTube: {e}")

        # ===== FACEBOOK =====
        try:
            log("Postando no Facebook...")
            fb_res = upload_facebook_reel(video_path, title)
            log(f"Facebook OK: {fb_res}")
        except Exception as e:
            log(f"Erro Facebook: {e}")

        # ===== BACKUP DRIVE =====
        try:
            backup_folder_id = find_folder_id(service, DRIVE_FOLDER_ID, "backups")
            if backup_folder_id:
                log("Salvando backup no Drive...")
                upload_file_to_drive(service, backup_folder_id, video_path)
                log("Backup salvo no Drive")
            else:
                log("Pasta 'backups' não encontrada. Backup ignorado.")
        except Exception as e:
            log(f"Erro backup: {e}")

        # ===== ATUALIZA STATE =====
        track["done"] += 1
        if track["done"] >= SHORTS_PER_TRACK:
            track["done"] = 0
            state["index"] = (state["index"] + 1) % len(state["tracks"])

        save_state(state)
        log("STATE salvo.")
        log("FINALIZADO")

    finally:
        # ===== LIMPEZA =====
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
                log("Áudio temporário apagado")
        except Exception as e:
            log(f"Erro ao apagar áudio: {e}")

        try:
            if os.path.exists(video_path):
                os.remove(video_path)
                log("Vídeo temporário apagado")
        except Exception as e:
            log(f"Erro ao apagar vídeo: {e}")


# ===== RUN =====

if __name__ == "__main__":
    main()
