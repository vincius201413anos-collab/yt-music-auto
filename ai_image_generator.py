"""
ai_image_generator.py — DJ DARK MARK v37 TREND WAIFU OPENING-FRAME
=============================================================

OBJETIVO v37:
- Parar de pensar só em "thumbnail estática"
- Gerar VISUAL DE ABERTURA para Shorts: o primeiro frame precisa prender atenção
- Seguir tendência de anime/waifu sem copiar nomes oficiais de personagens famosos
- Criar personagens com vibe reconhecível: shonen, dark fantasy, cyberpunk, idol, battle girl,
  demon girl, yandere leve, gamer girl, gothic waifu, street waifu
- Adult only: nada de loli, nada de underage, nada de personagem infantil
- Visual limpo, rosto forte, olhos hipnóticos, cabelo em movimento, partículas e luz viva

IMPORTANTE:
Este arquivo NÃO usa nomes de personagens famosos.
Ele usa arquétipos "inspirados em tendências" para evitar depender de IP/copyright
e para deixar o canal com identidade própria.
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
# CONFIG
# ══════════════════════════════════════════════════════════════════════

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")

REPLICATE_MODELS = [
    "cjwbw/animagine-xl-3.1",
    "lucataco/anything-v5-better-vae",
    "black-forest-labs/flux-dev",
]

FLUX_PARAMS = {
    "width": int(os.getenv("FLUX_WIDTH", "768")),
    "height": int(os.getenv("FLUX_HEIGHT", "1024")),
    "num_inference_steps": int(os.getenv("FLUX_STEPS", "38")),
    "guidance_scale": float(os.getenv("FLUX_GUIDANCE", "8.0")),
    "num_outputs": 1,
    "output_format": "png",
    "output_quality": 100,
    "disable_safety_checker": True,
}


# ══════════════════════════════════════════════════════════════════════
# IDENTIDADE v37
# ══════════════════════════════════════════════════════════════════════

CHANNEL_IDENTITY = (
    "DJ Dark Mark viral anime music visual identity, "
    "adult waifu character, anime trend aesthetic, "
    "dark trap phonk electronic music opening frame, "
    "scroll-stopping first 2 seconds, high CTR, high retention, "
    "premium YouTube Shorts anime visual universe"
)

CORE_CHARACTER = (
    "one adult anime woman, clearly adult, mature proportions, "
    "beautiful waifu character, expressive face, hypnotic eyes, "
    "magnetic emotional presence, strong visual identity, "
    "alone, single character, no other people, no text"
)

COMPOSITION_LOCK = (
    "vertical 9:16 mobile-first composition, "
    "face and upper body dominant, eyes in upper third, "
    "character large in frame, readable at tiny phone size, "
    "clean background, strong silhouette, clear focal point, "
    "opening frame for YouTube Shorts, designed to stop scrolling immediately"
)

STYLE_LOCK = (
    "premium anime key visual, clean sharp lineart, "
    "high-end 2D anime illustration, polished cel shading, "
    "cinematic lighting, glossy eyes, detailed hair, "
    "rich colors, high contrast, professional music cover art, "
    "not photorealistic, not 3d render"
)

MOTION_LOCK = (
    "alive frame, subtle sense of motion, hair moving in wind, "
    "floating particles, cinematic depth, glowing dust, "
    "energy in the air, dynamic but not cluttered"
)

VIRAL_HOOK_LOCK = (
    "one strong visual hook: glowing tear OR intense eye reflection OR dramatic face light "
    "OR hair blown by neon wind OR small aura around character, "
    "instantly recognizable visual moment, memorable frame"
)

QUALITY_LOCK = (
    "masterpiece, best quality, ultra detailed, crisp lineart, "
    "beautiful face, detailed shining eyes, clean anatomy, "
    "professional channel branding, high resolution, premium finish"
)


# ══════════════════════════════════════════════════════════════════════
# PALETAS v37 — TREND + CTR
# ══════════════════════════════════════════════════════════════════════

PALETTE_WARM = (
    "dominant warm golden amber palette, sunset orange light, "
    "golden rim light on hair, warm cinematic shadows, "
    "high contrast amber glow, emotional golden-hour anime look"
)

PALETTE_TEAL = (
    "dominant teal blue cyber palette, deep navy shadows, "
    "teal neon reflections, cool cinematic atmosphere, "
    "blue-green glow around character, futuristic night mood"
)

PALETTE_CRIMSON = (
    "dominant crimson red and black palette, dark dramatic shadows, "
    "blood-red accent light, intense phonk energy, "
    "dangerous but beautiful dark anime mood"
)

PALETTE_PURPLE = (
    "dominant violet purple and indigo palette, magical dark aura, "
    "purple rim light, dreamy anime atmosphere, "
    "deep shadow with bright violet highlights"
)

PALETTE_PINK = (
    "dominant hot pink and black palette, rose neon glow, "
    "cute but dangerous dark pop mood, pink bokeh, "
    "high contrast pink highlights"
)

PALETTES = [
    ("warm", PALETTE_WARM, 30),
    ("teal", PALETTE_TEAL, 28),
    ("crimson", PALETTE_CRIMSON, 18),
    ("purple", PALETTE_PURPLE, 14),
    ("pink", PALETTE_PINK, 10),
]


# ══════════════════════════════════════════════════════════════════════
# ARQUÉTIPOS TREND — SEM NOMES DE PERSONAGENS FAMOSOS
# ══════════════════════════════════════════════════════════════════════

TREND_WAIFU_ARCHETYPES = [
    (
        "dark fantasy battle waifu",
        "adult dark fantasy anime heroine, black battle outfit, dramatic cloak movement, "
        "confident dangerous aura, sword-like silhouette implied but not weapon-focused"
    ),
    (
        "cyberpunk street waifu",
        "adult cyberpunk anime girl, futuristic streetwear, neon city attitude, "
        "tech accessories, glowing earrings, confident urban energy"
    ),
    (
        "gothic vampire waifu",
        "adult gothic anime woman, elegant dark outfit, crimson eyes, "
        "romantic dangerous beauty, night atmosphere"
    ),
    (
        "idol pop waifu",
        "adult anime idol-inspired performer, stylish stage outfit, headphones, "
        "sparkling emotional eyes, music video energy"
    ),
    (
        "yandere soft waifu",
        "adult anime woman with controlled chaotic expression, sweet but intense gaze, "
        "subtle dangerous smile, emotional overload, not horror"
    ),
    (
        "demon aura waifu",
        "adult anime demon-girl inspired character, small subtle horns or aura, "
        "glowing eyes, dark magical energy, elegant not monstrous"
    ),
    (
        "gamer hacker waifu",
        "adult anime gamer hacker girl, headset, neon monitor glow, "
        "teal cyber atmosphere, smart intense stare"
    ),
    (
        "street trap waifu",
        "adult anime streetwear waifu, dark oversized jacket, chain accessories, "
        "trap/phonk energy, confident pose, urban night background"
    ),
    (
        "angel fallen waifu",
        "adult fallen angel anime woman, dark wings implied by shadow shape, "
        "golden or violet rim light, melancholic divine energy"
    ),
    (
        "samurai neon waifu",
        "adult neon samurai-inspired anime woman, sleek dark outfit, "
        "windy hair, cinematic discipline, intense eyes"
    ),
]


FACE_HOOKS = [
    "hypnotic direct eye contact, viewer feels watched",
    "one glowing tear on cheek catching neon light",
    "eyes reflecting city lights and music waveform",
    "slight dangerous smile with soft emotional eyes",
    "wide emotional eyes, lips slightly parted, instant curiosity",
    "half-lidded confident gaze, magnetic and calm",
    "vulnerable melancholic stare, beautiful sadness",
    "subtle crazy eyes but still beautiful and controlled",
    "dreamy distant gaze as if hearing the song inside her head",
    "sharp confident stare, dark queen energy"
]

HAIR_VARIATIONS = [
    "long black hair with glowing teal highlights, wind-blown",
    "dark purple hair with violet rim light, flowing dramatically",
    "silver white hair with blue shadows, cinematic and clean",
    "warm brown hair catching golden sunset, soft and emotional",
    "black hair with crimson reflections, dangerous phonk mood",
    "pink-black ombre hair glowing under neon, cute but dark",
    "deep navy hair with electric blue edges, cyber mood",
    "auburn hair with amber firelight, warm dramatic energy",
    "messy short black hair with strong anime silhouette",
    "long twin-tail inspired hair, clearly adult styling, dynamic motion"
]

OUTFIT_VARIATIONS = [
    "dark futuristic jacket, stylish but tasteful, premium anime design",
    "black streetwear outfit with small chains and choker, clean silhouette",
    "gothic elegant dark outfit, lace details subtle, not revealing",
    "cyberpunk cropped jacket over dark top, tasteful adult fashion",
    "stage performer outfit with headphones, stylish music identity",
    "dark battle-inspired outfit, sleek and cinematic, no armor clutter",
    "oversized hoodie with neon trim, trap aesthetic, clean design",
    "black dress with modern anime styling, elegant dark pop mood",
    "techwear outfit, straps and reflective details, futuristic vibe",
    "rock-inspired dark outfit, leather texture, subtle metal accessories"
]

BACKGROUND_VARIATIONS = [
    "rainy neon city street, wet reflections, teal and pink bokeh",
    "golden sunset skyline, cinematic clouds, warm emotional mood",
    "dark abstract stage with smoke and rim lights",
    "cyberpunk alley with blurred neon signs, clean depth",
    "night rooftop with city lights far behind, dramatic wind",
    "purple fog atmosphere with floating particles",
    "warm indoor studio with glowing music equipment blurred behind",
    "dark concert light beams, cinematic smoke, music performance feeling",
    "black void with one strong colored rim light and particle depth",
    "anime city sunset with soft bokeh, emotional ending scene"
]

MUSIC_ELEMENTS = [
    "sleek headphones around neck",
    "one earbud visible, immersed in the song",
    "small glowing waveform behind character, very subtle",
    "microphone silhouette blurred in background",
    "music visualizer particles around her, not cluttered",
    "no music prop, emotion carries the music",
    "no music prop, pure cinematic anime portrait",
]

GENRE_MAP = {
    "phonk": "phonk",
    "trap": "trap",
    "dark": "dark",
    "darkpop": "darkpop",
    "dark pop": "darkpop",
    "electronic": "electronic",
    "edm": "electronic",
    "dubstep": "electronic",
    "funk": "trap",
    "rock": "rock",
    "metal": "dark",
    "cinematic": "darkpop",
    "lofi": "darkpop",
    "indie": "darkpop",
    "pop": "darkpop",
}

GENRE_BOOSTS = {
    "phonk": (
        "phonk atmosphere, heavy 808 bass feeling, dark street energy, "
        "crimson or teal contrast, aggressive but clean"
    ),
    "trap": (
        "trap music atmosphere, urban night energy, stylish confidence, "
        "warm or rose neon lighting, premium street aesthetic"
    ),
    "electronic": (
        "electronic music atmosphere, futuristic energy, teal blue neon, "
        "clean digital glow, cyber rhythm visual"
    ),
    "darkpop": (
        "dark pop emotional atmosphere, romantic sadness, cinematic beauty, "
        "warm golden or rose-violet color story"
    ),
    "dark": (
        "dark music atmosphere, dramatic shadows, intense emotional presence, "
        "single strong accent color against darkness"
    ),
    "rock": (
        "rock energy atmosphere, warm firelight, concert smoke, "
        "raw emotional power, dramatic rim lighting"
    ),
    "default": (
        "dark music atmosphere, emotional anime beauty, cinematic contrast, "
        "premium viral Shorts visual"
    ),
}


# ══════════════════════════════════════════════════════════════════════
# NEGATIVE PROMPT
# ══════════════════════════════════════════════════════════════════════

NEGATIVE_PROMPT = (
    "ugly, bad anatomy, bad face, distorted face, asymmetrical eyes, "
    "bad hands, extra fingers, missing fingers, fused limbs, broken body, "
    "long neck, disfigured, mutated, melted face, uncanny valley, "
    "blurry, low quality, jpeg artifacts, heavy noise, flat boring image, "
    "photorealistic, real person, 3d render, CGI, doll, plastic skin, "
    "western cartoon, simple cartoon, childish style, "
    "child, underage, loli, young girl, schoolgirl, baby face, "
    "nude, explicit nudity, nipples, genitalia, sexual act, pornographic, "
    "multiple people, crowd, two girls, duplicate character, "
    "text, words, logo, watermark, signature, letters, numbers, "
    "famous anime character, exact character copy, cosplay of existing character, "
    "too dark to see face, face too small, full body tiny, "
    "cluttered background, excessive effects, neon overload, "
    "overexposed bloom, muddy colors, washed out, desaturated, "
    "messy composition, no focal point, bad eyes, dead eyes"
)


GENERATION_SUFFIX = (
    ", beautiful expressive adult anime face, eyes readable at small size, "
    "first frame optimized for Shorts feed, high contrast, clear silhouette, "
    "alive cinematic frame, motion feeling, polished anime art, "
    "no text, no logo, no watermark, no extra people"
)


# ══════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════

def _compact(text: str, max_len: int = 3000) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace(" ,", ",").replace(",,", ",")
    return text[:max_len].rstrip(" ,")


def _clean_song_name(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(r"\[[^\]]*\]|\{[^\}]*\}|\([^\)]*\)", "", name)
    name = re.sub(r"[_\-]+", " ", name)
    return re.sub(r"\s+", " ", name).strip() or "dark phonk"


def _seed(style: str, filename: str, short_num: int) -> int:
    key = f"{style}|{filename}|{short_num}|darkmark_v37_trend_waifu_opening_frame"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % (10**9)


def _rng(style: str, filename: str, short_num: int) -> random.Random:
    return random.Random(_seed(style, filename, short_num))


def _weighted_palette(rng: random.Random) -> tuple[str, str]:
    total = sum(weight for _, _, weight in PALETTES)
    r = rng.random() * total
    acc = 0
    for name, palette, weight in PALETTES:
        acc += weight
        if r <= acc:
            return name, palette
    return PALETTES[0][0], PALETTES[0][1]


def _song_mood_boost(song_name: str) -> str:
    clean = song_name.lower()

    if any(w in clean for w in ["dark", "shadow", "ghost", "night", "madrugada", "noite"]):
        return "haunted night emotion, lonely but powerful, eyes carrying darkness"
    if any(w in clean for w in ["fire", "burn", "rage", "fury", "angry"]):
        return "intense fire emotion, contained rage, powerful passionate stare"
    if any(w in clean for w in ["love", "heart", "amor", "coraçao", "coracao", "rose", "cherry"]):
        return "dark romantic emotion, longing eyes, beautiful bittersweet mood"
    if any(w in clean for w in ["lost", "alone", "lonely", "sozinho", "perdido"]):
        return "deep lonely emotion, quiet sadness, isolated cinematic feeling"
    if any(w in clean for w in ["drive", "speed", "run", "race", "corrida"]):
        return "fast motion energy, focused eyes, wind and speed feeling"
    if any(w in clean for w in ["queen", "king", "boss", "power", "rule"]):
        return "dominant confident aura, dark queen energy, commanding stare"
    if any(w in clean for w in ["dream", "sonho", "sleep", "cloud"]):
        return "dreamy floating emotion, soft surreal atmosphere, ethereal eyes"

    return "emotion matching the music, magnetic presence, cinematic feeling"


# ══════════════════════════════════════════════════════════════════════
# PROMPT PRINCIPAL v37
# ══════════════════════════════════════════════════════════════════════

def build_ai_prompt(
    style: str,
    filename: str,
    styles: list | None = None,
    short_num: int = 1,
    force_warm: bool = False,
    force_teal: bool = False,
    force_crimson: bool = False,
) -> str:
    styles = styles or []
    mapped = GENRE_MAP.get((style or "default").lower().strip(), "default")
    rng = _rng(mapped, filename, short_num)
    song_name = _clean_song_name(filename)

    archetype_name, archetype_prompt = rng.choice(TREND_WAIFU_ARCHETYPES)
    face_hook = rng.choice(FACE_HOOKS)
    hair = rng.choice(HAIR_VARIATIONS)
    outfit = rng.choice(OUTFIT_VARIATIONS)
    background = rng.choice(BACKGROUND_VARIATIONS)
    music_element = rng.choice(MUSIC_ELEMENTS)
    song_mood = _song_mood_boost(song_name)

    if force_warm:
        palette_name, palette = "warm", PALETTE_WARM
    elif force_teal:
        palette_name, palette = "teal", PALETTE_TEAL
    elif force_crimson:
        palette_name, palette = "crimson", PALETTE_CRIMSON
    else:
        palette_name, palette = _weighted_palette(rng)

    genre_text = ", ".join([style] + [s for s in styles if s and s != style])
    genre_boost = GENRE_BOOSTS.get(mapped, GENRE_BOOSTS["default"])

    prompt = (
        f"{CHANNEL_IDENTITY}, "
        f"{CORE_CHARACTER}, "

        # Trending archetype primeiro para direcionar o modelo
        f"trend archetype: {archetype_name}, {archetype_prompt}, "

        # Hook visual
        f"face hook: {face_hook}, "
        f"{VIRAL_HOOK_LOCK}, "

        # Detalhes principais
        f"hair: {hair}, "
        f"outfit: {outfit}, "
        f"music element: {music_element}, "

        # Composição e movimento
        f"{COMPOSITION_LOCK}, "
        f"{MOTION_LOCK}, "

        # Fundo e paleta
        f"background: {background}, "
        f"dominant palette: {palette_name}, {palette}, "

        # Música
        f"genre atmosphere: {genre_boost}, "
        f"genre: {genre_text}, "
        f"song title mood: {song_name}, "
        f"song emotion: {song_mood}, "

        # Qualidade
        f"{STYLE_LOCK}, "
        f"{QUALITY_LOCK}, "

        # Reforço final
        "opening frame for viral music Short, "
        "viewer must understand the mood instantly, "
        "beautiful adult anime waifu, emotional, trendy, memorable, "
        "no text, no watermark, no logo"
    )

    return _compact(prompt, max_len=3000)


def build_prompt(style: str = "phonk", seed_variant: int = 0) -> tuple[str, str]:
    fake_filename = f"{style}_variant_{seed_variant}.mp3"
    prompt = build_ai_prompt(
        style=style,
        filename=fake_filename,
        styles=[style],
        short_num=seed_variant + 1,
    )
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

    full_prompt = _compact(prompt + GENERATION_SUFFIX, max_len=3300)

    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }

    last_error: Optional[Exception] = None

    for model in REPLICATE_MODELS:
        for attempt in range(1, 4):
            try:
                logger.info(f"[Replicate] Tentativa {attempt}/3 — {model}")

                model_input = {
                    "prompt": full_prompt,
                    "negative_prompt": NEGATIVE_PROMPT,
                    "width": FLUX_PARAMS["width"],
                    "height": FLUX_PARAMS["height"],
                    "num_inference_steps": FLUX_PARAMS["num_inference_steps"],
                    "guidance_scale": FLUX_PARAMS["guidance_scale"],
                    "seed": random.randint(1000, 999_999),
                }

                if "flux" in model:
                    model_input.update({
                        "num_outputs": FLUX_PARAMS["num_outputs"],
                        "output_format": FLUX_PARAMS["output_format"],
                        "output_quality": FLUX_PARAMS["output_quality"],
                        "disable_safety_checker": FLUX_PARAMS["disable_safety_checker"],
                    })

                payload = {"input": model_input}

                create_url = f"https://api.replicate.com/v1/models/{model}/predictions"
                resp = requests.post(create_url, headers=headers, json=payload, timeout=45)
                resp.raise_for_status()
                pred = resp.json()

                poll_url = (
                    pred.get("urls", {}).get("get")
                    or f"https://api.replicate.com/v1/predictions/{pred['id']}"
                )

                for _ in range(120):
                    time.sleep(2)
                    sr = requests.get(poll_url, headers=headers, timeout=30)
                    sr.raise_for_status()
                    data = sr.json()
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

                raise TimeoutError("Replicate demorou demais.")

            except Exception as e:
                last_error = e
                logger.warning(f"[Replicate] Falhou tentativa {attempt}: {e}")
                time.sleep(3 * attempt)

    logger.error(f"[Replicate] Todas as tentativas falharam: {last_error}")
    return None


# ══════════════════════════════════════════════════════════════════════
# FUNÇÕES DE CONVENIÊNCIA
# ══════════════════════════════════════════════════════════════════════

def generate_background_image(
    style: str = "phonk",
    output_path: str = "assets/background.png",
    seed_variant: int = 0,
    max_retries: int = 3,
    force_warm: bool = False,
    force_teal: bool = False,
    force_crimson: bool = False,
) -> Optional[str]:
    prompt = build_ai_prompt(
        style=style,
        filename=f"{style}_variant_{seed_variant}.mp3",
        styles=[style],
        short_num=seed_variant + 1,
        force_warm=force_warm,
        force_teal=force_teal,
        force_crimson=force_crimson,
    )

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
    return generate_background_image(
        style=style,
        output_path=output_path,
        seed_variant=variant,
    )


def generate_background_batch(
    styles: list[str],
    output_dir: str = "assets/backgrounds",
    variants_per_style: int = 3,
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

            path = generate_background_image(
                style=style,
                output_path=output_path,
                seed_variant=v,
            )
            if path:
                results[style].append(path)

    return results


# ══════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="AI Image Generator — DJ DARK MARK v37 Trend Waifu Opening Frame"
    )
    parser.add_argument("--style", default="phonk",
                        help="Gênero musical: phonk, trap, electronic, dark, darkpop, rock")
    parser.add_argument("--filename", default="dark phonk.mp3",
                        help="Nome da música para adaptar mood")
    parser.add_argument("--short-num", type=int, default=1,
                        help="Número do short, muda seed")
    parser.add_argument("--output", default="assets/background.png")
    parser.add_argument("--force-warm", action="store_true",
                        help="Força paleta warm golden")
    parser.add_argument("--force-teal", action="store_true",
                        help="Força paleta teal blue")
    parser.add_argument("--force-crimson", action="store_true",
                        help="Força paleta crimson dark phonk")
    parser.add_argument("--prompt-only", action="store_true",
                        help="Só imprime prompt, não gera imagem")
    args = parser.parse_args()

    prompt = build_ai_prompt(
        style=args.style,
        filename=args.filename,
        styles=[args.style],
        short_num=args.short_num,
        force_warm=args.force_warm,
        force_teal=args.force_teal,
        force_crimson=args.force_crimson,
    )

    if args.prompt_only:
        print("=== PROMPT v37 ===")
        print(prompt)
        print("\n=== NEGATIVE PROMPT ===")
        print(NEGATIVE_PROMPT)
        print("\n=== GENERATION SUFFIX ===")
        print(GENERATION_SUFFIX)
    else:
        path = generate_image(prompt, args.output)
        print(f"✅ Salvo: {path}" if path else "✗ Falha na geração.")
