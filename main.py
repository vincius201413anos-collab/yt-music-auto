import os
import json
import re
from pathlib import Path

import requests

from drive_service import (
    get_drive_service,
    find_folder_id,
    list_audio_files_in_folder,
    download_drive_file,
)
from background_selector import detect_style, get_random_background
from video_generator import create_short
from youtube_service import upload_video
from ai_image_generator import generate_image

STATE_FILE = Path("state.json")
SHORTS_PER_TRACK = 3
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")


def load_state():
    if not STATE_FILE.exists():
        return {"tracks": []}

    with STATE_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def clean_title(filename):
    name = Path(filename).stem
    name = re.sub(r"[_\-]+", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name.title()


def scan_drive_folder():
    print("Escaneando Google Drive...")

    service = get_drive_service()

    inbox_folder_id = find_folder_id(service, DRIVE_FOLDER_ID, "inbox")
    if not inbox_folder_id:
        raise ValueError("Pasta 'inbox' não encontrada dentro da pasta principal do Drive.")

    audio_files = list_audio_files_in_folder(service, inbox_folder_id)

    print(f"Áudios encontrados no inbox: {[file['name'] for file in audio_files]}")
    return audio_files


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
                "done": False
            })
        else:
            if "id" not in existing_by_name[file_name]:
                existing_by_name[file_name]["id"] = file["id"]


def get_next_track(state):
    for track in state["tracks"]:
        if not track.get("done", False):
            return track
    return None


def build_video_metadata(filename, short_number, style):
    base_title = clean_title(filename)
    title = f"{base_title} | Short {short_number}"
    description = (
        f"{base_title}\n\n"
        f"Style: {style}\n"
        f"#music #shorts #youtube #trap #phonk #lofi #electronic"
    )
    tags = ["music", "shorts", "youtube", style, base_title.lower().replace(" ", "")]
    return title, description, tags


def build_ai_prompt(style, filename):
    base_title = clean_title(filename)

    prompts = {
        "phonk": f"{base_title}, dark neon city at night, cyberpunk, street lights, rain, cinematic, phonk vibe, vertical 9:16, ultra detailed, high contrast",
        "trap": f"{base_title}, luxury dark aesthetic, neon lights, urban night, aggressive trap mood, cinematic, vertical 9:16, ultra detailed",
        "lofi": f"{base_title}, cozy anime room, rainy window, warm lights, chill lo-fi mood, cinematic, vertical 9:16, detailed background",
        "dark": f"{base_title}, dark cinematic atmosphere, moody lighting, fog, dramatic shadows, vertical 9:16, ultra detailed",
        "electronic": f"{base_title}, futuristic abstract lights, electronic music vibe, glowing patterns, cyber aesthetic, vertical 9:16, ultra detailed",
        "metal": f"{base_title}, intense dark metal atmosphere, red lights, smoke, chaotic energy, cinematic, vertical 9:16, ultra detailed",
        "rock": f"{base_title}, dark stage lights, smoke, dramatic rock atmosphere, cinematic, vertical 9:16, ultra detailed",
        "indie": f"{base_title}, dreamy indie aesthetic, nostalgic lights, soft cinematic mood, vertical 9:16, ultra detailed",
        "pop": f"{base_title}, colorful dreamy lights, modern pop aesthetic, cinematic, glossy style, vertical 9:16, ultra detailed",
        "cinematic": f"{base_title}, epic cinematic atmosphere, orchestral mood, dramatic lighting, grand composition, vertical 9:16, ultra detailed",
        "default": f"{base_title}, cinematic music visual, neon atmosphere, moody lights, vertical 9:16, ultra detailed"
    }

    return prompts.get(style, prompts["default"])


def download_image_from_url(image_url, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    response = requests.get(image_url, timeout=120)
    response.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(response.content)

    return output_path


def resolve_background(style, filename):
    try:
        background = get_random_background(style, filename)
        if background and not str(background).startswith("__AUTO"):
            print(f"Background encontrado: {background}")
            return background
    except Exception as e:
        print(f"Falha ao buscar background local: {e}")

    print("Nenhum background local válido encontrado. Gerando imagem com IA...")

    prompt = build_ai_prompt(style, filename)
    print(f"Prompt IA: {prompt}")

    image_url = generate_image(prompt)
    print(f"Imagem gerada: {image_url}")

    safe_name = Path(filename).stem.replace(" ", "_")
    image_path = os.path.join("temp", f"{safe_name}_ai_background.jpg")

    download_image_from_url(image_url, image_path)
    print(f"Imagem baixada em: {image_path}")

    return image_path


def main():
    print("Bot iniciado")

    if not DRIVE_FOLDER_ID:
        raise ValueError("Drive folder ID não encontrado")

    print("Drive folder ID carregado")

    state = load_state()
    drive_files = scan_drive_folder()
    sync_tracks(state, drive_files)

    track = get_next_track(state)

    if not track:
        print("Nenhum áudio pendente")
        save_state(state)
        return

    name = track["name"]

    if "id" not in track:
        matched = next((f for f in drive_files if f["name"] == name), None)
        if not matched:
            raise ValueError(f"Não foi possível encontrar o ID do arquivo no Drive para: {name}")
        track["id"] = matched["id"]

    file_id = track["id"]
    shorts_done = track.get("shorts_done", 0)

    if shorts_done >= SHORTS_PER_TRACK:
        track["done"] = True
        save_state(state)
        print(f"Áudio {name} já estava concluído")
        return

    short_number = shorts_done + 1

    print(f"Processando: {name}")
    print(f"Criando short {short_number}/{SHORTS_PER_TRACK}")

    style = detect_style(name)
    print(f"Estilo detectado: {style}")

    os.makedirs("temp", exist_ok=True)
    audio_path = os.path.join("temp", name)

    print("Baixando áudio do Drive...")
    service = get_drive_service()
    download_drive_file(service, file_id, audio_path)

    background = resolve_background(style, name)

    output_name = f"{Path(name).stem}_short_{short_number}.mp4"

    print("Gerando vídeo...")
    video_path = create_short(audio_path, background, output_name, style)
    print(f"Vídeo gerado: {video_path}")

    title, description, tags = build_video_metadata(name, short_number, style)

    print("Enviando para o YouTube...")
    response = upload_video(
        video_path=video_path,
        title=title,
        description=description,
        tags=tags,
        privacy_status="private"
    )

    print(f"Upload concluído. Video ID: {response.get('id')}")

    track["shorts_done"] = short_number

    if track["shorts_done"] >= SHORTS_PER_TRACK:
        track["done"] = True
        print(f"Áudio finalizado: {name}")

    save_state(state)
    print("Execução finalizada")


if __name__ == "__main__":
    main()
