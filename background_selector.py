import os
import random

BASE_PATH = "assets/backgrounds"

SUPPORTED_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".mp4",
    ".mov",
    ".webm"
)


def get_all_backgrounds():
    backgrounds = []

    if not os.path.exists(BASE_PATH):
        print(f"Pasta não encontrada: {BASE_PATH}. Usando fundo automático.")
        return backgrounds

    for root, dirs, files in os.walk(BASE_PATH):
        for file in files:
            if file.lower().endswith(SUPPORTED_EXTENSIONS):
                backgrounds.append(os.path.join(root, file))

    return backgrounds


def detect_style(filename):
    name = filename.lower()

    if "phonk" in name:
        return "phonk"
    if "trap" in name:
        return "trap"
    if "lofi" in name or "lo-fi" in name:
        return "lofi"
    if "dark" in name:
        return "dark"
    if "electronic" in name or "edm" in name:
        return "electronic"
    if "metal" in name or "metalcore" in name:
        return "metal"
    if "rock" in name:
        return "rock"
    if "indie" in name:
        return "indie"
    if "cinematic" in name or "hanszimmer" in name or "hans_zimmer" in name or "orchestral" in name:
        return "cinematic"
    if "pop" in name:
        return "pop"

    return "default"


def get_random_background(style, filename=None):
    backgrounds = get_all_backgrounds()

    if not backgrounds:
        raise ValueError("Nenhum background encontrado em assets/backgrounds")

    chosen = random.choice(backgrounds)

    print(f"Background escolhido: {chosen}")

    return chosen
