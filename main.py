import os
import json
import re
import shutil
import random
import time
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

# delay humano antes de postar
MIN_HUMAN_DELAY_SECONDS = 20
MAX_HUMAN_DELAY_SECONDS = 180

SPOTIFY_LINK = "https://open.spotify.com/intl-pt/artist/1zyM1Pyi4YLAQgrSVRAYEy?si=3fQcRGwSQ8O2vsqq6jOVow"
TIKTOK_LINK = "https://www.tiktok.com/@darkmrkedit?is_from_webapp=1&sender_device=pc"


def load_state():
    if not STATE_FILE.exists():
        return {"tracks": [], "queue_index": 0}

    with STATE_FILE.open("r", encoding="utf-8") as f:
        state = json.load(f)

    state.setdefault("tracks", [])
    state.setdefault("queue_index", 0)

    for track in state["tracks"]:
        track.setdefault("shorts_done", 0)
        track.setdefault("done", False)
        track.setdefault("is_new", False)

    return state


def save_state(state):
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


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
        "Wait For This 😳",
        "This Drop Hits HARD 🔥",
        "Don’t Skip This 😳",
        "This Part Goes CRAZY 🤯",
        "This Feels Illegal 😈",
        "This Is Addictive 🔁",
        "Loop This 🔥",
        "You’ll Replay This 😳",
        "This Gets Better Every Loop 🔁",
    ]
    return f"{random.choice(hooks)} | {base_title}"


def build_output_path(base_title, style, short_number):
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    base_clean = safe_filename(base_title)

    folder = Path("output") / date_str / style
    folder.mkdir(parents=True, exist_ok=True)

    filename = f"{date_str}__{style}__{base_clean}__short_{short_number}.mp4"
    return str(folder / filename)


def build_video_metadata(filename, short_number, style, styles):
    base_title = clean_title(filename)
    title = generate_viral_title(base_title, style)

    description = (
        f"{base_title}\n\n"
        f"Main style: {style}\n"
        f"Detected styles: {', '.join(styles)}\n"
        f"Short version {short_number}/{SHORTS_PER_TRACK}\n\n"
        f"🎧 Spotify oficial:\n{SPOTIFY_LINK}\n\n"
        f"📲 TikTok oficial:\n{TIKTOK_LINK}\n\n"
        f"#music #shorts #youtube #{style} #viral #edit"
    )

    tags = [
        "music",
        "shorts",
        "youtube shorts",
        "viral music",
        style,
        f"{style} music",
        base_title.lower(),
    ]

    for s in styles:
        tags.append(s)
        tags.append(f"{s} music")

    seen = set()
    final_tags = []
    for tag in tags:
        tag_clean = tag.strip().lower()
        if tag_clean and tag_clean not in seen:
            seen.add(tag_clean)
            final_tags.append(tag_clean)

    return title, description, final_tags


def sync_tracks(state, drive_files):
    existing = {t["name"]: t for t in state["tracks"]}

    for file in drive_files:
        if file["name"] not in existing:
            print(f"Nova música detectada: {file['name']}")
            state["tracks"].append({
                "id": file["id"],
                "name": file["name"],
                "shorts_done": 0,
                "done": False,
                "is_new": True
            })
        else:
            track = existing[file["name"]]
            track["id"] = file["id"]
            track.setdefault("shorts_done", 0)
            track.setdefault("done", False)
            track.setdefault("is_new", False)

    drive_names = {f["name"] for f in drive_files}
    state["tracks"] = [t for t in state["tracks"] if t["name"] in drive_names]

    if state["tracks"]:
        state["queue_index"] = state["queue_index"] % len(state["tracks"])
    else:
        state["queue_index"] = 0


def get_next_track(state):
    tracks = state.get("tracks", [])
    if not tracks:
        return None

    for track in tracks:
        if track.get("is_new", False):
            track["is_new"] = False
            return track

    start_index = state.get("queue_index", 0) % len(tracks)
    current_index = start_index

    for _ in range(len(tracks)):
        track = tracks[current_index]

        if track.get("shorts_done", 0) < SHORTS_PER_TRACK:
            state["queue_index"] = (current_index + 1) % len(tracks)
            return track

        current_index = (current_index + 1) % len(tracks)

    for track in tracks:
        track["shorts_done"] = 0
        track["done"] = False

    state["queue_index"] = 1 % len(tracks) if len(tracks) > 1 else 0
    return tracks[0]


def resolve_background(style, filename, short_number, styles):
    try:
        bg = get_random_background(style, filename)
        if bg and not str(bg).startswith("__AUTO"):
            print(f"Background encontrado: {bg}")
            return bg
    except Exception as e:
        print(f"Falha ao buscar background local: {e}")

    os.makedirs("temp", exist_ok=True)

    prompt = build_ai_prompt(style, filename, styles)
    print(f"[IA] Gerando imagem para: {prompt[:160]}...")

    img = generate_image(prompt)

    if img and os.path.exists(img):
        cached = f"temp/{Path(filename).stem}_{short_number}.png"
        shutil.copy2(img, cached)
        print(f"[IA] Imagem salva em: {cached}")
        return cached

    fallback = "assets/backgrounds/default.jpg"
    if os.path.exists(fallback):
        print(f"Usando fallback: {fallback}")
        return fallback

    raise FileNotFoundError(
        "Nenhum background encontrado e fallback assets/backgrounds/default.jpg não existe."
    )


def apply_human_delay():
    delay = random.randint(MIN_HUMAN_DELAY_SECONDS, MAX_HUMAN_DELAY_SECONDS)
    print(f"Aguardando {delay}s para simular comportamento humano...")
    time.sleep(delay)


def main():
    print("BOT INICIADO")

    if not DRIVE_FOLDER_ID:
        raise ValueError("DRIVE_FOLDER_ID não encontrado nas variáveis de ambiente.")

    state = load_state()
    service = get_drive_service()

    inbox_id = find_folder_id(service, DRIVE_FOLDER_ID, "inbox")
    if not inbox_id:
        raise ValueError("Pasta 'inbox' não encontrada no Drive.")

    files = list_audio_files_in_folder(service, inbox_id)
    print(f"Áudios encontrados: {[f['name'] for f in files]}")

    sync_tracks(state, files)
    save_state(state)

    track = get_next_track(state)
    if not track:
        print("Nada pra postar")
        save_state(state)
        return

    name = track["name"]
    print(f"Processando: {name}")

    styles = detect_styles(name)
    style = detect_style(name)
    base_title = clean_title(name)

    os.makedirs("temp", exist_ok=True)
    audio_path = f"temp/{name}"

    print("Baixando áudio do Drive...")
    download_drive_file(service, track["id"], audio_path)

    short_number = track.get("shorts_done", 0) + 1
    print(f"Criando short {short_number}/{SHORTS_PER_TRACK}")

    bg = resolve_background(style, name, short_number, styles)
    output_path = build_output_path(base_title, style, short_number)

    print("Gerando vídeo...")
    video_path = create_short(audio_path, bg, output_path, style)
    print(f"Vídeo gerado: {video_path}")

    title, desc, tags = build_video_metadata(name, short_number, style, styles)

    apply_human_delay()

    print("Upload YouTube...")
    response = upload_video(video_path, title, desc, tags, "public")
    if isinstance(response, dict):
        print(f"Upload concluído. Video ID: {response.get('id')}")

    try:
        print("Tentando salvar backup no Drive...")
        backup_folder_id = find_folder_id(service, DRIVE_FOLDER_ID, "backups")
        if backup_folder_id:
            upload_file_to_drive(service, backup_folder_id, video_path)
            print("Backup salvo com sucesso.")
        else:
            print("Pasta 'backups' não encontrada. Pulando backup.")
    except Exception as e:
        print(f"Backup falhou, mas o bot continua normal: {e}")

    track["shorts_done"] = short_number
    track["done"] = track["shorts_done"] >= SHORTS_PER_TRACK
    save_state(state)

    try:
        if os.path.exists(audio_path):
            os.remove(audio_path)
    except Exception:
        pass

    if track["done"]:
        print(f"Música concluída nesta etapa: {name}")

    print("FINALIZADO")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERRO GERAL: {e}")
        import traceback
        traceback.print_exc()
        raise
