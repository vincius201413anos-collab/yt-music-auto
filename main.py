import os
import json
import re
import shutil
from pathlib import Path

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


def load_state():
    if not STATE_FILE.exists():
        return {"tracks": [], "queue_index": 0}

    with STATE_FILE.open("r", encoding="utf-8") as f:
        state = json.load(f)

    if "tracks" not in state:
        state["tracks"] = []

    if "queue_index" not in state:
        state["queue_index"] = 0

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


def sync_tracks(state, drive_files):
    existing_by_name = {track["name"]: track for track in state["tracks"]}

    for file in drive_files:
        file_name = file["name"]

        if file_name not in existing_by_name:
            print(f"Novo áudio detectado: {file_name}")
            state["tracks"].append({
                "id": file["id"],
                "name": file_name,
                "shorts_done": 0,
                "done": False,
                "is_new": True
            })
        else:
            track = existing_by_name[file_name]
            track["id"] = file["id"]

            if "shorts_done" not in track:
                track["shorts_done"] = 0
            if "done" not in track:
                track["done"] = False
            if "is_new" not in track:
                track["is_new"] = False

    drive_names = {file["name"] for file in drive_files}
    state["tracks"] = [track for track in state["tracks"] if track["name"] in drive_names]

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
            if track.get("shorts_done", 0) >= SHORTS_PER_TRACK:
                track["shorts_done"] = 0
                track["done"] = False

            track["is_new"] = False
            print(f"Prioridade para música nova: {track['name']}")
            return track

    start_index = state.get("queue_index", 0) % len(tracks)
    current_index = start_index

    for _ in range(len(tracks)):
        track = tracks[current_index]

        if track.get("shorts_done", 0) >= SHORTS_PER_TRACK:
            track["shorts_done"] = 0
            track["done"] = False

        if not track.get("done", False):
            state["queue_index"] = (current_index + 1) % len(tracks)
            return track

        current_index = (current_index + 1) % len(tracks)

    return None


def build_video_metadata(filename, short_number, style, styles):
    base_title = clean_title(filename)

    secondary = styles[1] if len(styles) > 1 else None
    hybrid = f"{style} x {secondary}" if secondary else style

    title_variants = {
        "metal": [
            f"{base_title} | Infernal {hybrid.title()} Energy 🔥",
            f"{base_title} | Heavy {hybrid.title()} Demon Vibes",
            f"{base_title} | Brutal {hybrid.title()} Music Edit",
        ],
        "rock": [
            f"{base_title} | {hybrid.title()} Music That Hits Hard 🔥",
            f"{base_title} | Dark {hybrid.title()} Short Edit",
            f"{base_title} | This {hybrid.title()} Vibe Is Different",
        ],
        "phonk": [
            f"{base_title} | {hybrid.title()} Night Drive Edit 🚗",
            f"{base_title} | Dark {hybrid.title()} Vibes",
            f"{base_title} | Aggressive {hybrid.title()} Short",
        ],
        "trap": [
            f"{base_title} | {hybrid.title()} Luxury Dark Edit",
            f"{base_title} | Hard {hybrid.title()} Vibes",
            f"{base_title} | {hybrid.title()} Energy Short Edit",
        ],
        "indie": [
            f"{base_title} | Emotional {hybrid.title()} Atmosphere",
            f"{base_title} | Dreamy {hybrid.title()} Short Edit",
            f"{base_title} | {hybrid.title()} Mood Music",
        ],
        "lofi": [
            f"{base_title} | Calm {hybrid.title()} Vibes",
            f"{base_title} | Late Night {hybrid.title()} Mood",
            f"{base_title} | Soft {hybrid.title()} Music Edit",
        ],
        "electronic": [
            f"{base_title} | Futuristic {hybrid.title()} Energy",
            f"{base_title} | Neon {hybrid.title()} Music",
            f"{base_title} | Cyber {hybrid.title()} Short Edit",
        ],
        "cinematic": [
            f"{base_title} | Epic {hybrid.title()} Atmosphere",
            f"{base_title} | Cinematic {hybrid.title()} Music",
            f"{base_title} | Dark {hybrid.title()} Soundtrack",
        ],
        "pop": [
            f"{base_title} | Stylish {hybrid.title()} Music",
            f"{base_title} | Dreamy {hybrid.title()} Short",
            f"{base_title} | Modern {hybrid.title()} Vibes",
        ],
        "dark": [
            f"{base_title} | Dark {hybrid.title()} Atmosphere",
            f"{base_title} | Sinister {hybrid.title()} Mood",
            f"{base_title} | Shadowy {hybrid.title()} Edit",
        ],
        "funk": [
            f"{base_title} | Energetic {hybrid.title()} Vibes",
            f"{base_title} | Party {hybrid.title()} Music",
            f"{base_title} | Loud {hybrid.title()} Short",
        ],
        "default": [
            f"{base_title} | {hybrid.title()} Music Short Edit",
            f"{base_title} | {hybrid.title()} Vibes",
            f"{base_title} | Cinematic {hybrid.title()} Edit",
        ],
    }

    variants = title_variants.get(style, title_variants["default"])
    title = variants[(short_number - 1) % len(variants)]

    description = (
        f"{base_title}\n\n"
        f"Main style: {style}\n"
        f"Detected styles: {', '.join(styles)}\n"
        f"Short version {short_number}\n\n"
        f"🎧 Spotify oficial:\n{SPOTIFY_LINK}\n\n"
        f"📲 TikTok oficial:\n{TIKTOK_LINK}\n\n"
        f"#music #shorts #youtube #{style} #viral #edit"
    )

    tags = [
        base_title.lower(),
        f"{base_title.lower()} music",
        "music",
        "shorts",
        "youtube shorts",
        "viral music",
        style,
        f"{style} music",
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


def resolve_background(style, filename, short_number, styles):
    try:
        background = get_random_background(style, filename)
        if background and not str(background).startswith("__AUTO"):
            print(f"Background encontrado: {background}")
            return background
    except Exception as e:
        print(f"Falha ao buscar background local/vídeo: {e}")

    print("Gerando imagem IA...")

    os.makedirs("temp", exist_ok=True)
    safe_name = Path(filename).stem.replace(" ", "_")
    cached_path = os.path.join("temp", f"{safe_name}_{short_number}.png")

    prompt = build_ai_prompt(style, filename, styles)
    print(f"Prompt IA: {prompt[:200]}...")

    image_result = generate_image(prompt)

    if image_result and os.path.exists(image_result):
        shutil.copy2(image_result, cached_path)
        print(f"Imagem IA salva em: {cached_path}")
        return cached_path

    fallback_list = [
        "assets/backgrounds/default.jpg",
        "assets/backgrounds/default.jpeg",
        "assets/backgrounds/default.png",
        "assets/backgrounds/default.webp",
    ]

    for fallback in fallback_list:
        if os.path.exists(fallback):
            print(f"Usando fallback final: {fallback}")
            return fallback

    raise RuntimeError("Falha IA e nenhum fallback local encontrado.")


def main():
    print("Bot iniciado")

    if not DRIVE_FOLDER_ID:
        raise ValueError("DRIVE_FOLDER_ID não encontrado nas variáveis de ambiente.")

    state = load_state()
    service = get_drive_service()

    inbox_id = find_folder_id(service, DRIVE_FOLDER_ID, "inbox")
    if not inbox_id:
        raise ValueError("Pasta 'inbox' não encontrada no Drive.")

    files = list_audio_files_in_folder(service, inbox_id)
    print(f"Áudios encontrados no inbox: {[f['name'] for f in files]}")

    sync_tracks(state, files)

    track = get_next_track(state)

    if not track:
        print("Nada pra postar")
        save_state(state)
        return

    name = track["name"]

    styles = detect_styles(name)
    style = detect_style(name)

    print(f"Estilos detectados: {styles}")
    print(f"Estilo principal: {style}")

    os.makedirs("temp", exist_ok=True)
    audio_path = os.path.join("temp", name)

    print("Baixando áudio do Drive...")
    download_drive_file(service, track["id"], audio_path)

    short_number = track.get("shorts_done", 0) + 1
    print(f"Criando short {short_number}/{SHORTS_PER_TRACK}")

    bg = resolve_background(style, name, short_number, styles)

    output_name = f"{Path(name).stem}_short_{short_number}.mp4"

    print("Gerando vídeo...")
    video_path = create_short(audio_path, bg, output_name, style)
    print(f"Vídeo gerado: {video_path}")

    title, desc, tags = build_video_metadata(name, short_number, style, styles)

    print("Enviando para o YouTube...")
    response = upload_video(video_path, title, desc, tags, "public")
    print(f"Upload concluído. Video ID: {response.get('id')}")

    # BACKUP SEGURO E NÃO CRÍTICO
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
    if track["shorts_done"] >= SHORTS_PER_TRACK:
        track["done"] = True
        print(f"Áudio completou {SHORTS_PER_TRACK} shorts nesta volta: {name}")

    save_state(state)
    print("Execução finalizada")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERRO GERAL: {e}")
        import traceback
        traceback.print_exc()
        raise
