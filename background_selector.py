import os
import random
import re
from pathlib import Path


STYLE_KEYWORDS = {
    "phonk": ["phonk", "drift", "cowbell"],
    "trap": ["trap", "808", "rage"],
    "lofi": ["lofi", "chill", "sad", "study"],
    "cinematic": ["cinematic", "epic", "ambient", "orchestral"],
    "rock": ["rock", "guitar", "grunge", "alternative"],
    "metal": ["metal", "metalcore", "deathcore", "hardcore"],
    "indie": ["indie", "dream", "shoegaze"],
    "pop": ["pop", "commercial", "mainstream"],
    "funk": ["funk", "mandela", "bruxaria"],
    "electronic": ["edm", "electronic", "house", "techno"],
    "dark": ["dark"]
}

STYLE_PRIORITY = [
    "metal",
    "rock",
    "phonk",
    "trap",
    "electronic",
    "cinematic",
    "dark",
    "indie",
    "lofi",
    "pop",
    "funk",
]


def detect_styles(filename: str) -> list[str]:
    name = filename.lower()
    found = []

    for style, keywords in STYLE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in name:
                found.append(style)
                break

    if not found:
        return ["default"]

    # remove duplicados preservando ordem
    unique = []
    for style in found:
        if style not in unique:
            unique.append(style)

    return unique


def detect_style(filename: str) -> str:
    styles = detect_styles(filename)

    if styles == ["default"]:
        return "default"

    # escolhe o mais forte pela prioridade
    for priority_style in STYLE_PRIORITY:
        if priority_style in styles:
            return priority_style

    return styles[0]


def normalize_media_name(name: str) -> str:
    stem = Path(name).stem.lower()
    stem = re.sub(r"\[[^\]]+\]", "", stem)
    stem = re.sub(r"\s+", " ", stem).strip()
    return stem


def _find_matching_media_by_name(filename: str, folder: str, exts: tuple[str, ...]):
    if not os.path.exists(folder):
        return None

    stem = normalize_media_name(filename)

    exact_matches = []
    variant_matches = []

    for file in os.listdir(folder):
        lower_file = file.lower()
        full_path = os.path.join(folder, file)

        if not lower_file.endswith(exts):
            continue

        file_stem = normalize_media_name(file)

        if file_stem == stem:
            exact_matches.append(full_path)
        elif file_stem.startswith(stem + "__"):
            variant_matches.append(full_path)

    if exact_matches:
        return random.choice(exact_matches)

    if variant_matches:
        return random.choice(variant_matches)

    return None


def get_random_background(style: str, filename: str | None = None) -> str:
    specific_video_folder = "assets/source_videos"
    background_folder = "assets/backgrounds"

    video_exts = (".mp4", ".mov", ".mkv", ".webm", ".gif")
    image_exts = (".jpg", ".jpeg", ".png", ".webp")

    # 1) prioridade total: vídeo específico da música
    if filename:
        specific_video = _find_matching_media_by_name(filename, specific_video_folder, video_exts)
        if specific_video:
            print(f"Vídeo específico encontrado para a música: {specific_video}")
            return specific_video

    # 2) imagem específica da música
    if filename:
        specific_image = _find_matching_media_by_name(filename, background_folder, image_exts)
        if specific_image:
            print(f"Imagem específica encontrada para a música: {specific_image}")
            return specific_image

    # 3) imagens por estilo
    if os.path.exists(background_folder):
        style_files = []

        for file in os.listdir(background_folder):
            lower_file = file.lower()
            full_path = os.path.join(background_folder, file)

            if not lower_file.endswith(image_exts):
                continue

            if lower_file.startswith("default"):
                continue

            if style in lower_file:
                style_files.append(full_path)

        if style_files:
            chosen = random.choice(style_files)
            print(f"Background local por estilo encontrado: {chosen}")
            return chosen

    # 4) se não achou nada → IA
    print("Nenhum background local encontrado. Usando IA.")
    return "__AUTO__"
