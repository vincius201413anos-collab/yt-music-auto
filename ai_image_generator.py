"""
ai_image_generator.py — DJ DARK MARK v18 TRAPSTAR BEAUTY LOCK
============================================================
Versão profissional para gastar crédito de imagem com mais chance de valer a pena.

Objetivo visual:
- Anime 2D premium, dark cyberpunk, trap/phonk/electronic.
- Garotas adultas com vibe trapstar/dark queen, SEM escrever "trapstar" na imagem.
- Muitas variações: cabelo colorido, olhos brilhando, piercings, tattoos, roupas e poses.
- Corpo inteiro ou meio-corpo amplo: roupa/silhueta aparecem; evita close genérico.
- Foco em beleza + atitude forte: brava, maluca, dominante, perigosa, muito bonita.
- Sem texto, sem logo, sem watermark; a logo fica melhor como overlay no video_generator.
"""

from __future__ import annotations

import hashlib
import logging
import os
import random
import re
import time
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger("ai_image_generator")


# ══════════════════════════════════════════════════════════════════════
# CONFIG — seguro para GitHub/Replicate
# ══════════════════════════════════════════════════════════════════════

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")

REPLICATE_MODELS = [
    "black-forest-labs/flux-dev",
]

FLUX_PARAMS = {
    "width": int(os.getenv("FLUX_WIDTH", "1080")),
    "height": int(os.getenv("FLUX_HEIGHT", "1920")),
    "num_inference_steps": int(os.getenv("FLUX_STEPS", "42")),
    "guidance_scale": float(os.getenv("FLUX_GUIDANCE", "7.7")),
    "num_outputs": 1,
    "output_format": "png",
    "output_quality": 100,
    "disable_safety_checker": True,
}


# ══════════════════════════════════════════════════════════════════════
# LOCK PRINCIPAL
# ══════════════════════════════════════════════════════════════════════

CHANNEL_IDENTITY = (
    "DJ darkMark visual identity, dark anime edit, viral phonk cover art, "
    "YouTube Shorts music visualizer background, underground trap and electronic music aesthetic"
)

TRAPSTAR_DNA = (
    "one adult anime woman only, beautiful trapstar cyberpunk anime girl, "
    "dark queen energy, rebellious streetwear attitude, intimidating beauty, "
    "very beautiful face, sharp jawline, glossy lips, sharp eyeliner, soft blush, "
    "natural anime skin tone, glowing hypnotic eyes matching the music mood, "
    "angry expression or crazy expression or cold dominant stare, "
    "confident dangerous aura, expensive underground street style, "
    "subtle face tattoos, neck tattoos, arm tattoos, hand tattoos, "
    "nose piercing, eyebrow piercing, lip piercing or ear piercings, "
    "black choker, silver chains, rings, cyber jewelry, "
    "colorful hair, neon dyed hair, black hair with red streaks, blue hair, pink hair, purple hair, "
    "black techwear, gothic streetwear, glossy black jacket, oversized hoodie, cargo pants, skirt with chains, "
    "platform boots or chunky boots visible, full outfit visible, "
    "platform-safe outfit, no nudity, no explicit outfit, alone in frame, no crowd"
)

BODY_LOCK = (
    "medium full body or full body composition, character visible from head to knees or head to feet, "
    "character fills 70 to 85 percent of vertical 9:16 frame, "
    "outfit, tattoos, piercings and silhouette clearly visible, "
    "not a face-only portrait, not a generic close-up, not cropped at neck, not tiny in the background"
)

STYLE_LOCK = (
    "2D anime illustration only, premium anime key visual, sharp manga lineart, polished cel shading, "
    "dark cyberpunk anime edit, viral phonk anime cover, dark trap cover art, "
    "deep black shadows, neon magenta, violet, red, cyan and toxic green rim lights, "
    "high contrast, clean readable face, cinematic lighting, smoky glitch background, "
    "neon rain, dark city bokeh, electric aura, bass shockwave particles, "
    "beautiful vibrant glow but not messy, not overexposed, not realistic, not 3D"
)

RETENTION_LOCK = (
    "scroll stopping first frame, strong centered focal point, phone-screen readable, "
    "eyes and face instantly visible, body pose strong and memorable, "
    "dark background with one dominant neon color, clean composition, no clutter, "
    "space near bottom for waveform and DJ logo overlay"
)

SKIN_LOCK = (
    "natural anime skin tone preserved, pale or warm anime skin, "
    "skin is not blue, face is not fully cyan, neon colors only as rim light and eye glow, "
    "soft blush visible, natural face shading, beautiful readable face"
)

QUALITY_TAGS = (
    "masterpiece, best quality, high-end anime illustration, ultra sharp, clean anatomy, "
    "beautiful anime woman, detailed tattoos, detailed piercings, detailed hair, glossy glowing eyes, "
    "cinematic shadows, high retention music cover, 9:16 vertical, 4k look"
)

NEGATIVE_PROMPT = (
    "photorealistic, realistic, photography, real person, 3d, CGI, doll, plastic skin, "
    "child, teen, underage, loli, chibi, schoolgirl, baby face, mascot, "
    "nsfw, nude, explicit, lingerie, fetish, overly revealing outfit, cleavage focus, "
    "gore, horror monster, ugly, creepy, deformed face, bad anatomy, bad hands, "
    "extra fingers, missing fingers, extra arms, extra legs, fused limbs, long neck, tiny head, "
    "lazy eye, crossed eyes, asymmetrical eyes, distorted mouth, melted face, uncanny, "
    "multiple people, crowd, duplicate character, two girls, text, letters, words, captions, "
    "trapstar text, DJ text, logo, watermark, signature, username, UI, number, "
    "low quality, blurry, low resolution, muddy colors, washed out, flat lighting, "
    "generic AI art, generic purple gradient, boring composition, clutter, bad crop, "
    "yellow dominant, orange sunset dominant, daylight, sunny, photobash, "
    "blue skin, cyan skin, fully blue face, blue body, neon skin, overexposed cyan face, "
    "face only, headshot only, portrait only, cropped body, missing legs, missing torso, "
    "small character, character too far, empty background without character"
)


# ══════════════════════════════════════════════════════════════════════
# VARIAÇÕES ANTI-GENÉRICO
# ══════════════════════════════════════════════════════════════════════

HAIR_VARIATIONS = [
    "long black hair with red neon streaks, wet bangs, glowing red eye reflections",
    "electric blue hair with black underlayer, twin tails, cyan rim light",
    "hot pink hair with purple roots, messy trapstar style, glossy strands",
    "white silver hair with black tips, sharp bangs, magenta glow",
    "black and violet ombre hair, long flowing hair, neon smoke highlights",
    "short black bob with red streaks, dangerous clean silhouette",
    "turquoise and purple split-dye hair, cyberpunk streetwear mood",
    "dark red hair with black roots, wet shine, crimson backlight",
    "lavender hair with black horns, violet eye glow",
    "black hair under oversized hood, colored strands visible",
]

EYE_VARIATIONS = [
    "glowing red eyes, angry hypnotic stare",
    "glowing violet eyes, cold dominant stare",
    "bright magenta eyes, crazy beautiful expression",
    "cyan and pink heterochromia, intense cyberpunk stare",
    "toxic green glowing eyes, dangerous smile",
    "orange red glowing eyes matching hard trap energy",
    "electric blue glowing eyes with purple reflections",
]

EXPRESSION_VARIATIONS = [
    "furious beautiful face, controlled rage, sharp stare",
    "crazy gorgeous smile, unhinged but stylish, glowing eyes",
    "cold dominant expression, boss energy, looking down at viewer",
    "evil confident smirk, trap queen attitude",
    "serious angry stare, no smile, intimidating beauty",
    "playful dangerous fang smile, pretty but threatening",
    "calm psycho stare, elegant and scary",
    "brave rebellious expression, lip slightly parted, intense",
]

PIERCING_TATTOO_VARIATIONS = [
    "subtle forehead tattoo, small cheek tattoo, nose ring, ear piercings",
    "neck tattoo, eyebrow piercing, lip ring, silver earrings",
    "hand tattoos, arm sleeve tattoos, nose piercing, chain earrings",
    "small face tattoos near the eye, septum piercing, black choker",
    "cyber rune tattoos on neck and collarbone, multiple ear piercings",
    "minimal black ink tattoos on cheek and fingers, glossy lip piercing",
    "red glowing tattoo lines on arms, eyebrow piercing, silver rings",
    "gothic floral tattoos on arms, small cross tattoo under eye, nose stud",
]

OUTFIT_VARIATIONS = [
    "black techwear jacket, cargo pants with chains, chunky platform boots",
    "glossy black cropped jacket over dark top, chained skirt, thigh-high boots, platform-safe",
    "oversized black hoodie, tactical belt, dark shorts over leggings, chunky boots",
    "gothic streetwear dress with silver chains, leather gloves, platform boots",
    "black cyberpunk vest, cargo pants, fingerless gloves, heavy boots",
    "dark leather jacket, choker, chain belt, black pants, streetwear silhouette",
    "black and purple trap outfit, layered belts, arm sleeves, boots",
    "hooded black coat, neon seams, chains around waist, boots visible",
]

POSE_VARIATIONS = [
    "standing confidently, one hand near face, full outfit visible",
    "walking toward viewer, chains swinging, dominant pose",
    "arms crossed, chin down, angry glowing stare, body centered",
    "one hand in pocket, other hand holding glowing energy, full body pose",
    "leaning against neon wall, legs visible, cold stare",
    "low angle full body pose, looking down at viewer like a boss",
    "sitting on a low speaker, legs visible, leaning forward, crazy smile",
    "standing in rain, hair blowing, hand raised with neon smoke",
    "turning over shoulder, tattoos visible, dangerous expression",
    "dynamic full body stance, boots on wet reflective ground",
]

SCENE_VARIATIONS = [
    "rainy neon alley, wet ground reflections, purple smoke",
    "dark underground club entrance, magenta and red neon lights",
    "cyberpunk city rooftop at midnight, electric aura behind",
    "graffiti wall without readable words, black smoke and neon bokeh",
    "abandoned subway tunnel, violet lights, bass shockwave rings",
    "night drive street, red taillight streaks, wet asphalt",
    "dark studio with laser lights, smoky trap music atmosphere",
    "phonk drift garage, neon reflections, black car silhouette blurred in background",
    "futuristic nightclub, cyan magenta lighting, heavy shadows",
    "dark alley with broken neon signs but no readable text",
]

AURA_VARIATIONS = [
    "purple lightning aura around her silhouette",
    "red neon smoke wrapping around her arms",
    "hot pink glitch particles exploding behind her",
    "cyan and violet electric mist rising from the floor",
    "toxic green eye glow reflected in smoke",
    "black ink shadows with magenta sparks",
    "bass shockwave rings expanding from her boots",
    "crimson flame-like neon aura behind her",
]

ART_STYLE_VARIATIONS = [
    "premium anime key visual, sharp line art, glossy cel shading",
    "dark manga cover energy, halftone shadows, neon glow",
    "viral anime music cover art, polished lighting, dramatic pose",
    "cyberpunk anime poster, clean silhouette, high contrast",
    "phonk anime edit style, beautiful face, detailed streetwear",
]


GENRE_MAP = {
    "phonk": "phonk",
    "trap": "trap",
    "dark": "dark",
    "electronic": "electronic",
    "edm": "electronic",
    "dubstep": "electronic",
    "funk": "trap",
    "rock": "dark",
    "metal": "dark",
    "cinematic": "dark",
    "lofi": "dark",
    "indie": "dark",
    "pop": "default",
}

GENRE_PALETTES = {
    "phonk": [
        "black, red, hot magenta, violet glow",
        "black, toxic green, violet shadows",
        "black, crimson, purple lightning",
    ],
    "trap": [
        "black, pink neon, icy blue rim light",
        "black, red neon, gold jewelry highlights",
        "black, cyan, violet, magenta street glow",
    ],
    "electronic": [
        "black, cyan laser light, magenta glow",
        "deep blue, neon pink, violet digital particles",
        "black, teal, electric purple, club lights",
    ],
    "dark": [
        "near black, red eyes, violet aura",
        "black, gray shadows, blood red neon glow",
        "black, purple smoke, white hair highlights",
    ],
    "default": [
        "black, violet, magenta, cyan, red glow",
    ],
}


# ══════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════

def _compact(text: str, max_len: int = 3900) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace(" ,", ",").replace(",,", ",")
    return text[:max_len].rstrip(" ,")


def _clean_song_name(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(r"\[[^\]]*\]|\{[^\}]*\}|\([^\)]*\)", "", name)
    name = re.sub(r"[_\-]+", " ", name)
    return re.sub(r"\s+", " ", name).strip() or "dark trap phonk"


def _seed(style: str, filename: str, short_num: int) -> int:
    key = f"{style}|{filename}|{short_num}|darkmark_v18_trapstar_beauty_lock"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % (10**9)


def _rng(style: str, filename: str, short_num: int) -> random.Random:
    return random.Random(_seed(style, filename, short_num))


def _song_detail(song_name: str) -> str:
    clean = song_name.lower()
    if any(w in clean for w in ["bass", "808", "drop"]):
        return "visible bass shockwave rings on the wet floor"
    if any(w in clean for w in ["dark", "shadow", "ghost", "madrugada", "night"]):
        return "midnight shadow aura and red neon smoke"
    if any(w in clean for w in ["rage", "fire", "burn"]):
        return "crimson neon flame aura and aggressive energy"
    if any(w in clean for w in ["drive", "drift", "car"]):
        return "night drive reflections and blurred car lights"
    if any(w in clean for w in ["blue", "cyber", "electric"]):
        return "cyan electronic glow and digital particles"
    return "music energy visualized as neon aura around the character"


# ══════════════════════════════════════════════════════════════════════
# PROMPT PRINCIPAL — COMPATÍVEL COM SEU BOT
# ══════════════════════════════════════════════════════════════════════

def build_ai_prompt(style: str, filename: str, styles: list | None = None, short_num: int = 1) -> str:
    styles = styles or []
    mapped = GENRE_MAP.get((style or "default").lower().strip(), "default")
    rng = _rng(mapped, filename, short_num)
    song_name = _clean_song_name(filename)

    hair = rng.choice(HAIR_VARIATIONS)
    eyes = rng.choice(EYE_VARIATIONS)
    expression = rng.choice(EXPRESSION_VARIATIONS)
    piercing_tattoo = rng.choice(PIERCING_TATTOO_VARIATIONS)
    outfit = rng.choice(OUTFIT_VARIATIONS)
    pose = rng.choice(POSE_VARIATIONS)
    scene = rng.choice(SCENE_VARIATIONS)
    aura = rng.choice(AURA_VARIATIONS)
    art = rng.choice(ART_STYLE_VARIATIONS)
    palette = rng.choice(GENRE_PALETTES.get(mapped, GENRE_PALETTES["default"]))
    detail = _song_detail(song_name)

    genre_text = ", ".join([style] + [s for s in styles if s and s != style])

    prompt = (
        f"{TRAPSTAR_DNA}, {BODY_LOCK}, {STYLE_LOCK}, {RETENTION_LOCK}, {SKIN_LOCK}, {QUALITY_TAGS}, "
        f"{hair}, {eyes}, {expression}, {piercing_tattoo}, {outfit}, {pose}, "
        f"scene: {scene}, aura: {aura}, {detail}, "
        f"palette: {palette}, genre mood: {genre_text}, song mood: {song_name}, "
        f"{art}, "
        "CRITICAL: no written text anywhere in the image, no readable words on hat or wall or clothes, "
        "no logo, no watermark, no letters, no numbers, "
        "must look expensive, professional, high-retention YouTube Shorts visual, "
        "not generic, not boring, not realistic, not 3D"
    )

    return _compact(prompt, max_len=3600)


def build_prompt(style: str = "default", seed_variant: int = 0) -> tuple[str, str]:
    fake_filename = f"{style}_variant_{seed_variant}.mp3"
    prompt = build_ai_prompt(style=style, filename=fake_filename, styles=[style], short_num=seed_variant + 1)
    return prompt, NEGATIVE_PROMPT


# ══════════════════════════════════════════════════════════════════════
# GERAÇÃO DE IMAGEM
# ══════════════════════════════════════════════════════════════════════

def generate_image(prompt: str, output_path: str | None = None) -> str | None:
    if not REPLICATE_API_TOKEN:
        logger.error("REPLICATE_API_TOKEN não configurado.")
        return None

    output_path = output_path or "temp/generated_background.png"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    full_prompt = _compact(
        prompt
        + ", 2D anime only, professional dark trapstar anime girl, full body or medium full body, "
        + "beautiful face, tattoos, piercings, colorful hair, glowing eyes, dark cyberpunk streetwear, "
        + "premium anime illustration, viral phonk trap electronic cover art, sharp lineart, clean anatomy, "
        + "natural anime skin tone, neon only as rim light and eye glow, no text, no logo, no watermark"
    )

    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }

    last_error: Optional[Exception] = None

    for model in REPLICATE_MODELS:
        for attempt in range(1, 4):
            try:
                logger.info(f"[Replicate] Tentativa {attempt}/3 — {model}")

                payload = {
                    "input": {
                        **FLUX_PARAMS,
                        "prompt": full_prompt,
                        "negative_prompt": NEGATIVE_PROMPT,
                        "seed": random.randint(1000, 999999),
                    }
                }

                create_url = f"https://api.replicate.com/v1/models/{model}/predictions"
                resp = requests.post(create_url, headers=headers, json=payload, timeout=45)
                resp.raise_for_status()
                pred = resp.json()

                poll_url = pred.get("urls", {}).get("get") or f"https://api.replicate.com/v1/predictions/{pred['id']}"

                for _ in range(120):
                    time.sleep(2)
                    status_resp = requests.get(poll_url, headers=headers, timeout=30)
                    status_resp.raise_for_status()
                    data = status_resp.json()
                    status = data.get("status")

                    if status == "succeeded":
                        output = data.get("output")
                        image_url = output[0] if isinstance(output, list) else output
                        if not image_url:
                            raise RuntimeError("Replicate retornou output vazio.")

                        img = requests.get(image_url, timeout=90)
                        img.raise_for_status()
                        Path(output_path).write_bytes(img.content)

                        logger.info(f"[Replicate] Salvo: {output_path}")
                        return output_path

                    if status == "failed":
                        raise RuntimeError(data.get("error") or "Replicate falhou.")

                raise TimeoutError("Replicate demorou demais para gerar imagem.")

            except Exception as e:
                last_error = e
                logger.warning(f"[Replicate] Falhou tentativa {attempt}: {e}")
                time.sleep(3 * attempt)

    logger.error(f"[Replicate] Todas as tentativas falharam: {last_error}")
    return None


# ══════════════════════════════════════════════════════════════════════
# FUNÇÕES EXTRAS — compatibilidade com partes antigas do bot
# ══════════════════════════════════════════════════════════════════════

def generate_background_image(
    style: str = "phonk",
    output_path: str = "assets/background.png",
    seed_variant: int = 0,
    max_retries: int = 3,
) -> Optional[str]:
    prompt, _negative = build_prompt(style=style, seed_variant=seed_variant)
    for attempt in range(1, max_retries + 1):
        result = generate_image(prompt, output_path)
        if result:
            return result
        logger.warning(f"Tentativa background {attempt}/{max_retries} falhou.")
        time.sleep(3 * attempt)
    return None


def get_or_generate_background(
    style: str = "phonk",
    output_dir: str = "assets/backgrounds",
    force_new: bool = False,
) -> Optional[str]:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    existing = list(Path(output_dir).glob(f"{style}_bg_*.png"))

    if existing and not force_new:
        chosen = random.choice(existing)
        logger.info(f"Background reutilizado: {chosen}")
        return str(chosen)

    variant = random.randint(0, 99)
    output_path = str(Path(output_dir) / f"{style}_bg_{variant:02d}.png")
    return generate_background_image(style=style, output_path=output_path, seed_variant=variant)


def generate_background_batch(
    styles: list[str],
    output_dir: str = "assets/backgrounds",
    variants_per_style: int = 2,
) -> dict[str, list[str]]:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    results: dict[str, list[str]] = {}

    for style in styles:
        results[style] = []
        for v in range(variants_per_style):
            output_path = str(Path(output_dir) / f"{style}_bg_{v:02d}.png")
            if os.path.exists(output_path):
                results[style].append(output_path)
                continue

            path = generate_background_image(style=style, output_path=output_path, seed_variant=v)
            if path:
                results[style].append(path)

    return results


# ══════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="AI Image Generator — DJ DARK MARK v18 Trapstar Beauty Lock")
    parser.add_argument("--style", default="phonk")
    parser.add_argument("--filename", default="dark phonk.mp3")
    parser.add_argument("--short-num", type=int, default=1)
    parser.add_argument("--output", default="assets/background.png")
    parser.add_argument("--prompt-only", action="store_true")
    args = parser.parse_args()

    prompt = build_ai_prompt(
        style=args.style,
        filename=args.filename,
        styles=[args.style],
        short_num=args.short_num,
    )

    if args.prompt_only:
        print(prompt)
    else:
        path = generate_image(prompt, args.output)
        if path:
            print(f"✅ Salvo: {path}")
        else:
            print("✗ Falha na geração.")
