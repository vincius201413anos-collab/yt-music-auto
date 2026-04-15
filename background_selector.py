import os
import random
from ai_image_generator import generate_image


STYLE_KEYWORDS = {
    "phonk": ["phonk", "drift", "cowbell"],
    "trap": ["trap", "808", "rage"],
    "lofi": ["lofi", "chill", "sad", "study"],
    "cinematic": ["cinematic", "epic", "ambient", "orchestral"],
    "rock": ["rock", "guitar", "grunge", "alternative"],
    "metal": ["metal", "metalcore", "deathcore", "hardcore"],
    "indie": ["indie", "dream", "shoegaze"],
    "pop": ["pop", "commercial", "mainstream"],
    "funk": ["funk", "brazilian funk", "mandela"],
    "electronic": ["edm", "electronic", "house", "techno"]
}


def detect_style(filename: str) -> str:
    name = filename.lower()

    for style, keywords in STYLE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in name:
                return style

    return "default"


def find_local_background(style: str, background_folder: str) -> str | None:
    if not os.path.exists(background_folder):
        print(f"Pasta não encontrada: {background_folder}")
        return None

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
    return None


def build_prompt(style: str, music_name: str) -> str:
    clean_name = os.path.splitext(os.path.basename(music_name))[0]
    clean_name = clean_name.replace("_", " ").replace("-", " ").strip()

    prompts = {
        "phonk": (
            f"Dark phonk music visual inspired by street racing culture, "
            f"neon japanese city at night, aggressive atmosphere, drifting cars, "
            f"smoke, speed, moody purple lighting, cinematic, ultra detailed, "
            f"vertical 9:16, no text, no watermark. Song vibe: {clean_name}"
        ),
        "trap": (
            f"Dark trap music visual, luxury urban lifestyle, cinematic shadows, "
            f"expensive cars, neon highlights, intense mood, stylish street energy, "
            f"high contrast, ultra detailed, vertical 9:16, no text, no watermark. "
            f"Song vibe: {clean_name}"
        ),
        "lofi": (
            f"Lofi anime aesthetic visual, cozy room, rainy window, soft warm lights, "
            f"calm emotional atmosphere, dreamy mood, peaceful composition, "
            f"cinematic, ultra detailed, vertical 9:16, no text, no watermark. "
            f"Song vibe: {clean_name}"
        ),
        "cinematic": (
            f"Cinematic music visual, epic emotional atmosphere, dramatic lighting, "
            f"wide composition adapted to vertical 9:16, film look, grand scenery, "
            f"moody and powerful, ultra detailed, no text, no watermark. "
            f"Song vibe: {clean_name}"
        ),
        "rock": (
            f"Rock music visual, dark stage lights, grunge atmosphere, electric guitar energy, "
            f"smoky environment, dramatic contrast, rebellious mood, cinematic, "
            f"ultra detailed, vertical 9:16, no text, no watermark. Song vibe: {clean_name}"
        ),
        "metal": (
            f"Heavy metal music visual, intense dark atmosphere, red and black lighting, "
            f"aggressive mood, smoke, chaos, powerful stage energy, cinematic, "
            f"ultra detailed, vertical 9:16, no text, no watermark. Song vibe: {clean_name}"
        ),
        "indie": (
            f"Indie music visual, nostalgic dreamy aesthetic, soft film tones, "
            f"moody youth atmosphere, artistic composition, emotional and stylish, "
            f"cinematic, ultra detailed, vertical 9:16, no text, no watermark. "
            f"Song vibe: {clean_name}"
        ),
        "pop": (
            f"Modern pop music visual, clean stylish aesthetic, glossy lights, "
            f"trendy cinematic composition, vibrant but elegant mood, ultra detailed, "
            f"vertical 9:16, no text, no watermark. Song vibe: {clean_name}"
        ),
        "funk": (
            f"Brazilian funk music visual, nightlife energy, urban favela-inspired lights, "
            f"party mood, bold contrast, powerful atmosphere, cinematic, ultra detailed, "
            f"vertical 9:16, no text, no watermark. Song vibe: {clean_name}"
        ),
        "electronic": (
            f"Electronic music visual, futuristic neon lights, cyber atmosphere, "
            f"digital energy, immersive cinematic lighting, stylish composition, "
            f"ultra detailed, vertical 9:16, no text, no watermark. Song vibe: {clean_name}"
        ),
        "default": (
            f"Dark cinematic music visual, moody neon atmosphere, professional cover art style, "
            f"dramatic lighting, immersive composition, ultra detailed, vertical 9:16, "
            f"no text, no watermark. Song vibe: {clean_name}"
        ),
    }

    return prompts.get(style, prompts["default"])


def resolve_background(style: str, music_name: str) -> str:
    print("Resolvendo background...")

    background_folder = "assets/backgrounds"

    local_background = find_local_background(style, background_folder)
    if local_background:
        return local_background

    prompt = build_prompt(style, music_name)
    print(f"Prompt IA: {prompt}")

    try:
        image_url = generate_image(prompt)
        print(f"Imagem gerada com sucesso: {image_url}")
        return image_url

    except Exception as e:
        print(f"⚠️ Erro ao gerar imagem com IA: {e}")

        final_fallbacks = [
            "assets/backgrounds/default.jpg",
            "assets/backgrounds/default.jpeg",
            "assets/backgrounds/default.png",
            "assets/backgrounds/default.webp",
            "assets/default.jpg",
            "assets/default.png",
        ]

        for fallback_path in final_fallbacks:
            if os.path.exists(fallback_path):
                print(f"Usando fallback final: {fallback_path}")
                return fallback_path

        raise RuntimeError(
            "Nenhum background local encontrado e a geração por IA falhou."
        )
