import os
import random


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


def detect_style(filename: str) -> str:
    name = filename.lower()

    for style, keywords in STYLE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in name:
                return style

    return "default"


def get_random_background(style: str, filename: str | None = None) -> str:
    background_folder = "assets/backgrounds"

    if not os.path.exists(background_folder):
        print(f"Pasta não encontrada: {background_folder}")
        return "__AUTO__"

    valid_exts = (".jpg", ".jpeg", ".png", ".webp")

    style_files = []
    generic_files = []

    for file in os.listdir(background_folder):
        if not file.lower().endswith(valid_exts):
            continue

        full_path = os.path.join(background_folder, file)
        lower_file = file.lower()

        if style in lower_file:
            style_files.append(full_path)
        else:
            generic_files.append(full_path)

    if style_files:
        chosen = random.choice(style_files)
        print(f"Background local por estilo encontrado: {chosen}")
        return chosen

    default_candidates = [
        os.path.join(background_folder, "default.jpg"),
        os.path.join(background_folder, "default.jpeg"),
        os.path.join(background_folder, "default.png"),
        os.path.join(background_folder, "default.webp"),
    ]

    for candidate in default_candidates:
        if os.path.exists(candidate):
            print(f"Usando background default local: {candidate}")
            return candidate

    if generic_files:
        chosen = random.choice(generic_files)
        print(f"Usando background genérico local: {chosen}")
        return chosen

    print("Nenhum background local válido encontrado.")
    return "__AUTO__"
