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
    # força IA sempre
    print("Forçando uso de IA.")
    return "__AUTO__"
