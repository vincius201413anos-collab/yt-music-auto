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
        f"#music #shorts #youtube #{style} #viral #edit"
    )
    tags = [
        "music",
        "shorts",
        "youtube",
        style,
        base_title.lower().replace(" ", ""),
        "viral",
        "edit"
    ]
    return title, description, tags


def build_ai_prompt(style, filename):
    base_title = clean_title(filename)

    prompts = {
        "phonk": (
            f"{base_title}, dark street racing, neon japanese city, drift cars, smoke, night, "
            f"cyberpunk, aggressive atmosphere, purple lighting, cinematic, ultra detailed, vertical 9:16"
        ),
        "trap": (
            f"{base_title}, luxury dark aesthetic, money, sports cars, urban night, neon lights, "
            f"cinematic shadows, aggressive trap mood, ultra detailed, vertical 9:16"
        ),
        "lofi": (
            f"{base_title}, cozy anime room, rainy window, warm lights, calm mood, soft colors, "
            f"lofi aesthetic, cinematic, ultra detailed, vertical 9:16"
        ),
        "dark": (
            f"{base_title}, dark cinematic atmosphere, fog, moody lighting, dramatic shadows, "
            f"intense mood, ultra detailed, vertical 9:16"
        ),
        "electronic": (
            f"{base_title}, futuristic neon lights, cyber world, glowing patterns, electronic vibe, "
            f"digital energy, ultra detailed, vertical 9:16"
        ),
        "metal": (
            f"{base_title}, heavy metal atmosphere, red lights, smoke, chaos, fire mood, "
            f"aggressive energy, cinematic, ultra detailed, vertical 9:16"
        ),
        "rock": (
            f"{base_title}, rock concert stage, dramatic lights, smoke, guitar energy, "
            f"cinematic performance vibe, ultra detailed, vertical 9:16"
        ),
        "indie": (
            f"{base_title}, dreamy nostalgic aesthetic, soft lights, emotional atmosphere, "
            f"film look, artistic composition, ultra detailed, vertical 9:16"
        ),
        "pop": (
            f"{base_title}, colorful lights, glossy modern pop aesthetic, vibrant and stylish mood, "
            f"clean cinematic visual, ultra detailed, vertical 9:16"
        ),
        "cinematic": (
            f"{base_title}, epic cinematic scene, dramatic lighting, movie look, emotional atmosphere, "
            f"grand composition, ultra detailed, vertical 9:16"
        ),
        "funk": (
            f"{base_title}, brazilian funk visual, nightlife, party lights, urban energy, bold contrast, "
            f"cinematic mood, ultra detailed, vertical 9:16"
        ),
        "default": (
            f"{base_title}, dark cinematic visual, neon atmosphere, moody lights, stylish music background, "
            f"ultra detailed, vertical 9:16"
        )
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
    # 1. tenta background local
    try:
        background = get_random_background(style, filename)

        if background and not str(background).startswith("__AUTO"):
            print(f"Background encontrado: {background}")
            return background

    except Exception as e:
        print(f"Falha ao buscar background local: {e}")

    print("Nenhum background local válido encontrado. Gerando imagem com IA...")

    # 2. cache local pra não gerar a mesma imagem toda vez
    safe_name = Path(filename).stem.replace(" ", "_")
    cached_path = os.path.join("temp", f"{safe_name}_{style}_ai_background.png")

    if os.path.exists(cached_path):
        print(f"Usando imagem em cache: {cached_path}")
        return cached_path

    # 3. gera prompt por estilo
    prompt = build_ai_prompt(style, filename)
    print(f"Prompt IA: {prompt}")

    try:
        image_result = generate_image(prompt)
        print(f"Resultado da IA: {image_result}")

        # CASO 1: IA retornou arquivo local
        if isinstance(image_result, str) and os.path.exists(image_result):
            os.makedirs(os.path.dirname(cached_path), exist_ok=True)
            shutil.copy2(image_result, cached_path)
            print(f"Imagem local copiada para: {cached_path}")
            return cached_path

        # CASO 2: IA retornou URL
        if isinstance(image_result, str) and image_result.startswith(("http://", "https://")):
            download_image_from_url(image_result, cached_path)
            print(f"Imagem baixada em: {cached_path}")
            return cached_path

        raise RuntimeError(f"Retorno inesperado da IA: {image_result}")

    except Exception as e:
        print(f"⚠️ Erro ao gerar imagem com IA: {e}")

        # 4. fallback final
        fallback_list = [
            "assets/backgrounds/default.jpg",
            "assets/backgrounds/default.jpeg",
            "assets/backgrounds/default.png",
            "assets/backgrounds/default.webp",
            "assets/default.jpg",
            "assets/default.png",
        ]

        for fallback in fallback_list:
            if os.path.exists(fallback):
                print(f"Usando fallback final: {fallback}")
                return fallback

        raise RuntimeError(
            "Nenhum background local encontrado, a IA falhou e nenhum fallback padrão existe."
        )


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
    try:
        main()
    except Exception as e:
        print(f"ERRO GERAL: {e}")
        import traceback
        traceback.print_exc()
        raise
