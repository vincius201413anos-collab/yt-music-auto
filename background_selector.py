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

    for file in os.listdir(background_folder):
        if not file.lower().endswith(valid_exts):
            continue

        full_path = os.path.join(background_folder, file)
        lower_file = file.lower()

        # 🚫 IGNORA default (pra não bloquear IA)
        if lower_file.startswith("default"):
            continue

        # 🎯 pega só imagens do estilo
        if style in lower_file:
            style_files.append(full_path)

    # ✅ usa imagem específica do estilo
    if style_files:
        chosen = random.choice(style_files)
        print(f"Background local por estilo encontrado: {chosen}")
        return chosen

    # 🤖 não encontrou → IA entra em ação
    print("Nenhum background por estilo encontrado. Usando IA.")
    return "__AUTO__"
