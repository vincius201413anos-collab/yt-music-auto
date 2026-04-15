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

SPOTIFY_LINK = "https://open.spotify.com/intl-pt/artist/1zyM1Pyi4YLAQgrSVRAYEy?si=3fQcRGwSQ8O2vsqq6jOVow"
TIKTOK_LINK = "https://www.tiktok.com/@darkmrkedit?is_from_webapp=1&sender_device=pc"


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
    name = re.sub(r"\[[^\]]+\]", "", name)
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
                "done": False,
                "is_new": True
            })
        else:
            track = existing_by_name[file_name]
            if "id" not in track:
                track["id"] = file["id"]
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


def build_video_metadata(filename, short_number, style):
    base_title = clean_title(filename)

    title_variants = {
        "rock": [
            f"{base_title} Rock Music | This Drop Hits Different 🔥",
            f"{base_title} Heavy Rock Vibes | Dark Short Edit",
            f"{base_title} Rock Energy | Cinematic Music Short",
        ],
        "metal": [
            f"{base_title} Metal Music | Dark Demon Vibes 🔥",
            f"{base_title} Heavy Metal Energy | Infernal Short Edit",
            f"{base_title} Metal Soundtrack | Brutal Cinematic Edit",
        ],
        "phonk": [
            f"{base_title} Phonk Music | Drift Night Edit 🚗",
            f"{base_title} Dark Phonk Vibes | Street Racing Short",
            f"{base_title} Aggressive Phonk | Neon Car Edit",
        ],
        "trap": [
            f"{base_title} Trap Music | Dark Luxury Edit",
            f"{base_title} Hard Trap Vibes | Night Mood Short",
            f"{base_title} Trap Energy | Cinematic Short Edit",
        ],
        "lofi": [
            f"{base_title} Lofi Music | Chill Aesthetic Short",
            f"{base_title} Calm Lofi Vibes | Rainy Mood Edit",
            f"{base_title} Lofi Atmosphere | Soft Music Short",
        ],
        "indie": [
            f"{base_title} Indie Music | Emotional Short Edit",
            f"{base_title} Dreamy Indie Vibes | Cinematic Mood",
            f"{base_title} Indie Atmosphere | Soft Aesthetic Short",
        ],
        "pop": [
            f"{base_title} Pop Music | Stylish Short Edit",
            f"{base_title} Pop Vibes | Cinematic Music Short",
            f"{base_title} Modern Pop Energy | Aesthetic Edit",
        ],
        "electronic": [
            f"{base_title} Electronic Music | Futuristic Short",
            f"{base_title} Cyber Electronic Vibes | Music Edit",
            f"{base_title} Electronic Energy | Neon Short Edit",
        ],
        "cinematic": [
            f"{base_title} Cinematic Music | Epic Short Edit",
            f"{base_title} Epic Soundtrack Vibes | Dark Short",
            f"{base_title} Cinematic Atmosphere | Music Edit",
        ],
        "funk": [
            f"{base_title} Funk Music | Party Short Edit",
            f"{base_title} Brazilian Funk Vibes | Music Short",
            f"{base_title} Funk Energy | Night Edit",
        ],
        "dark": [
            f"{base_title} Dark Music | Cinematic Short Edit",
            f"{base_title} Dark Atmosphere | Music Short",
            f"{base_title} Moody Soundtrack | Aesthetic Edit",
        ],
        "default": [
            f"{base_title} Music | Cinematic Short Edit",
            f"{base_title} Vibes | Music Short",
            f"{base_title} Soundtrack | Aesthetic Edit",
        ],
    }

    variants = title_variants.get(style, title_variants["default"])
    title = variants[(short_number - 1) % len(variants)]

    description = (
        f"{base_title}\n\n"
        f"Style: {style}\n"
        f"Short version {short_number}\n\n"
        f"🎧 Spotify oficial:\n{SPOTIFY_LINK}\n\n"
        f"📲 TikTok oficial:\n{TIKTOK_LINK}\n\n"
        f"#music #shorts #youtube #{style} #viral #edit"
    )

    tags = [
        base_title.lower(),
        f"{base_title.lower()} music",
        style,
        f"{style} music",
        "music",
        "shorts",
        "youtube shorts",
        "viral music",
        "aesthetic edit",
        "cinematic edit",
        "dark vibes",
    ]

    if style == "rock":
        tags += ["rock music", "heavy rock", "dark rock"]
    elif style == "metal":
        tags += ["metal music", "heavy metal", "dark metal"]
    elif style == "phonk":
        tags += ["phonk", "drift phonk", "night drive"]
    elif style == "trap":
        tags += ["trap music", "dark trap", "luxury trap"]
    elif style == "lofi":
        tags += ["lofi", "chill music", "sad lofi"]
    elif style == "electronic":
        tags += ["electronic music", "edm", "cinematic electronic"]

    seen = set()
    final_tags = []
    for tag in tags:
        tag_clean = tag.strip().lower()
        if tag_clean and tag_clean not in seen:
            seen.add(tag_clean)
            final_tags.append(tag_clean)

    return title, description, final_tags


def build_ai_prompt(style, filename, variant_index=1):
    camera_angles = [
        "low angle cinematic shot",
        "close-up dramatic framing",
        "wide cinematic composition",
        "off-center artistic framing",
        "top view perspective"
    ]

    lighting_styles = [
        "harsh red lighting",
        "neon glow lighting",
        "soft cinematic shadows",
        "high contrast dramatic light",
        "dark ambient lighting"
    ]

    textures = [
        "smoke and fog everywhere",
        "rain particles and wet reflections",
        "fire sparks and ash in the air",
        "dust and cinematic grain",
        "glitch distortion atmosphere"
    ]

    angle = camera_angles[variant_index % len(camera_angles)]
    lighting = lighting_styles[variant_index % len(lighting_styles)]
    texture = textures[variant_index % len(textures)]

    prompts = {
        "metal": f"""
        dark demonic ritual scene, massive horned demon emerging from shadows,
        gothic cathedral destroyed, burning altar, fire and ash everywhere,
        terrifying presence, red and black color palette,
        {angle}, {lighting}, {texture},
        ultra detailed, cinematic composition, album cover quality,
        emotionally intense, not generic, no text, no watermark, vertical 9:16
        """,

        "rock": f"""
        dark rock concert scene, silhouette guitarist in red light,
        heavy smoke, fire sparks, underground stage energy,
        rebellious atmosphere, dramatic shadows,
        {angle}, {lighting}, {texture},
        cinematic, ultra detailed, album cover style,
        strong emotional impact, no text, no watermark, vertical 9:16
        """,

        "phonk": f"""
        japanese street at night, neon lights reflecting on wet asphalt,
        drift car sliding with smoke, cyberpunk vibe,
        purple and blue tones, underground street racing energy,
        {angle}, neon glow lighting, rain reflections,
        ultra detailed, cinematic, album cover quality,
        aggressive mood, no text, no watermark, vertical 9:16
        """,

        "trap": f"""
        dark luxury trap aesthetic, expensive cars, chains, shadows,
        urban night scene, mysterious figure, rich villain vibe,
        moody lighting, deep contrast,
        {angle}, {lighting}, {texture},
        cinematic, ultra detailed, album cover style,
        powerful and stylish, no text, no watermark, vertical 9:16
        """,

        "lofi": f"""
        lonely room at night, rain on window, warm lamp light,
        nostalgic atmosphere, soft shadows, emotional silence,
        calm and melancholic vibe,
        {angle}, soft cinematic lighting, dust particles,
        ultra detailed, cinematic composition,
        peaceful but sad, no text, no watermark, vertical 9:16
        """,

        "indie": f"""
        dreamy nostalgic scene, empty street at dusk,
        soft light, emotional atmosphere, memory-like feeling,
        cinematic storytelling composition,
        {angle}, soft shadows, film grain,
        ultra detailed, indie aesthetic,
        unique emotional vibe, no text, no watermark, vertical 9:16
        """,

        "electronic": f"""
        futuristic cyber world, glowing lights, digital structures,
        neon energy flowing, sci-fi environment,
        immersive electronic atmosphere,
        {angle}, neon lighting, glitch effects,
        ultra detailed, cinematic, album cover quality,
        modern and intense, no text, no watermark, vertical 9:16
        """,

        "cinematic": f"""
        epic cinematic scene, massive landscape, glowing sky,
        dramatic lighting, emotional scale, film-like composition,
        powerful atmosphere,
        {angle}, {lighting}, {texture},
        ultra detailed, cinematic masterpiece,
        high impact visual, no text, no watermark, vertical 9:16
        """,

        "funk": f"""
        brazilian funk nightlife, urban favela aesthetic,
        vibrant colors, party lights, energetic scene,
        bold contrast and movement,
        {angle}, {lighting}, {texture},
        ultra detailed, cinematic, album cover style,
        high energy vibe, no text, no watermark, vertical 9:16
        """,

        "dark": f"""
        shadowy mysterious figure, fog, dark red tones,
        sinister cinematic atmosphere,
        ominous presence, horror-inspired visual,
        {angle}, {lighting}, {texture},
        ultra detailed, dramatic composition,
        emotionally intense, no text, no watermark, vertical 9:16
        """,

        "default": f"""
        cinematic aesthetic scene, strong atmosphere,
        dramatic lighting, emotional composition,
        visually striking image,
        {angle}, {lighting}, {texture},
        ultra detailed, album cover quality,
        not generic, no text, no watermark, vertical 9:16
        """
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
        privacy_status="public"
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
