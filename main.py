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
        return {
            "tracks": [],
            "queue_index": 0
        }

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

    # remove músicas que não existem mais no drive
    drive_names = {file["name"] for file in drive_files}
    state["tracks"] = [track for track in state["tracks"] if track["name"] in drive_names]

    if state["tracks"]:
        state["queue_index"] = state["queue_index"] % len(state["tracks"])
    else:
        state["queue_index"] = 0


def get_next_track(state):
    tracks = state.get("tracks", [])
    if not tracks:
        return None, None

    start_index = state.get("queue_index", 0) % len(tracks)
    current_index = start_index

    for _ in range(len(tracks)):
        track = tracks[current_index]

        # loop infinito: se terminou 3 shorts, zera e reentra na fila
        if track.get("shorts_done", 0) >= SHORTS_PER_TRACK:
            track["shorts_done"] = 0
            track["done"] = False

        if not track.get("done", False):
            next_queue_index = (current_index + 1) % len(tracks)
            state["queue_index"] = next_queue_index
            return track, current_index

        current_index = (current_index + 1) % len(tracks)

    return None, None


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


def build_ai_prompt(style, filename, variant_index=1):
    base_title = clean_title(filename)

    variant_map = {
        1: "main version, powerful central composition, iconic scene, highly cinematic",
        2: "alternate angle, fresh framing, second visual variation, same theme",
        3: "different composition, unique perspective, third visual variation, same theme",
    }

    variant_text = variant_map.get(variant_index, f"unique visual variation {variant_index}")

    prompts = {
        "metal": (
            f"{base_title}, dark infernal ritual, demonic creatures, horns, fire, ash, smoke, "
            f"apocalyptic gothic cathedral, cursed symbols, hellish atmosphere, red and black palette, "
            f"terrifying but cinematic, ultra detailed, masterpiece, dramatic lighting, vertical 9:16, "
            f"{variant_text}, no text, no watermark, no logo, not generic, emotionally intense"
        ),
        "rock": (
            f"{base_title}, dark rock concert from hell, demonic stage energy, burning amplifiers, fire sparks, "
            f"smoke, red lights, black leather, rebellious infernal vibe, epic dramatic composition, "
            f"cinematic, ultra detailed, vertical 9:16, {variant_text}, no text, no watermark, no logo, "
            f"powerful emotional impact"
        ),
        "phonk": (
            f"{base_title}, dark street racing, japanese neon city at night, drift cars, tire smoke, "
            f"aggressive underground vibe, purple and crimson lights, cyberpunk aesthetic, intense composition, "
            f"ultra detailed, vertical 9:16, {variant_text}, no text, no watermark, no logo"
        ),
        "trap": (
            f"{base_title}, luxury dark trap aesthetic, money, chains, sports cars, urban night, "
            f"moody shadows, aggressive rich villain vibe, cinematic composition, bold contrast, "
            f"ultra detailed, vertical 9:16, {variant_text}, no text, no watermark, no logo"
        ),
        "lofi": (
            f"{base_title}, cozy melancholic anime room, warm lamp light, rainy window, soft atmosphere, "
            f"nostalgic emotional vibe, peaceful but sad, dreamy composition, ultra detailed, vertical 9:16, "
            f"{variant_text}, no text, no watermark, no logo"
        ),
        "dark": (
            f"{base_title}, sinister dark cinematic atmosphere, shadowy figure, smoke, fog, moody red and black lighting, "
            f"ominous tone, gothic visual, ultra detailed, vertical 9:16, {variant_text}, no text, no watermark, no logo"
        ),
        "electronic": (
            f"{base_title}, futuristic cyber world, glowing lights, digital energy, neon geometry, "
            f"electronic rave atmosphere, immersive sci-fi composition, ultra detailed, vertical 9:16, "
            f"{variant_text}, no text, no watermark, no logo"
        ),
        "indie": (
            f"{base_title}, dreamy nostalgic indie aesthetic, emotional youth atmosphere, dusk lighting, "
            f"soft film look, artistic composition, bittersweet mood, ultra detailed, vertical 9:16, "
            f"{variant_text}, no text, no watermark, no logo"
        ),
        "pop": (
            f"{base_title}, glossy modern pop visual, vibrant lights, fashion-forward composition, stylish and dramatic, "
            f"clean and cinematic, colorful but elegant, ultra detailed, vertical 9:16, "
            f"{variant_text}, no text, no watermark, no logo"
        ),
        "cinematic": (
            f"{base_title}, epic cinematic masterpiece, dramatic scene, emotional grand scale atmosphere, "
            f"movie poster quality, intense lighting, ultra detailed, vertical 9:16, "
            f"{variant_text}, no text, no watermark, no logo"
        ),
        "funk": (
            f"{base_title}, brazilian funk nightlife, urban energy, bold lights, favela-inspired atmosphere, "
            f"party mood, loud visual style, strong contrast, cinematic, ultra detailed, vertical 9:16, "
            f"{variant_text}, no text, no watermark, no logo"
        ),
        "default": (
            f"{base_title}, dark cinematic visual, emotionally intense atmosphere, stylish dramatic lighting, "
            f"striking composition, ultra detailed, vertical 9:16, {variant_text}, no text, no watermark, no logo"
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


def resolve_background(style, filename, short_number):
    try:
        background = get_random_background(style, filename)

        if background and not str(background).startswith("__AUTO"):
            print(f"Background encontrado: {background}")
            return background

    except Exception as e:
        print(f"Falha ao buscar background local: {e}")

    print("Nenhum background local válido encontrado. Gerando imagem com IA...")

    safe_name = Path(filename).stem.replace(" ", "_")
    cached_path = os.path.join(
        "temp",
        f"{safe_name}_{style}_short_{short_number}_ai_background.png"
    )

    if os.path.exists(cached_path):
        os.remove(cached_path)
        print(f"Cache antigo removido: {cached_path}")

    prompt = build_ai_prompt(style, filename, variant_index=short_number)
    print(f"Prompt IA: {prompt}")

    try:
        image_result = generate_image(prompt)
        print(f"Resultado da IA: {image_result}")

        if isinstance(image_result, str) and os.path.exists(image_result):
            os.makedirs(os.path.dirname(cached_path), exist_ok=True)
            shutil.copy2(image_result, cached_path)
            print(f"Imagem local copiada para: {cached_path}")
            return cached_path

        if isinstance(image_result, str) and image_result.startswith(("http://", "https://")):
            download_image_from_url(image_result, cached_path)
            print(f"Imagem baixada em: {cached_path}")
            return cached_path

        raise RuntimeError(f"Retorno inesperado da IA: {image_result}")

    except Exception as e:
        print(f"⚠️ Erro ao gerar imagem com IA: {e}")

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

    track, track_index = get_next_track(state)

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

    background = resolve_background(style, name, short_number)

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
        print(f"Áudio completou 3 shorts nesta volta: {name}")

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
