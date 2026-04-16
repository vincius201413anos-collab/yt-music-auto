"""
ai_image_generator.py — Gerador de imagens IA premium.
Focado em:
- garotas bonitas/fofas
- sempre fazendo algo
- cenas naturais e dinâmicas
- estilo consistente tipo lofi/anime aesthetic
- qualidade alta com Flux Dev primeiro
"""

from __future__ import annotations

import os
import random
import re
import time
from pathlib import Path
from typing import Any

import anthropic
import replicate
import requests

SAVE_DIR = Path("temp")
MAX_TRIES = 3

_ANTHROPIC_CLIENT: anthropic.Anthropic | None = None


# ══════════════════════════════════════════════════════════════════════
# CLIENT / CONFIG
# ══════════════════════════════════════════════════════════════════════

def get_anthropic_model() -> str:
    return os.getenv("ANTHROPIC_MODEL", "claude-opus-4-7")


def get_anthropic_client() -> anthropic.Anthropic | None:
    global _ANTHROPIC_CLIENT
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    if _ANTHROPIC_CLIENT is None:
        _ANTHROPIC_CLIENT = anthropic.Anthropic(api_key=api_key)
    return _ANTHROPIC_CLIENT


# ══════════════════════════════════════════════════════════════════════
# BASE VISUAL
# ══════════════════════════════════════════════════════════════════════

BASE_GIRL_STYLE = (
    "one beautiful anime-style young woman, cute face, delicate features, expressive eyes, "
    "soft glossy hair, natural pose, candid moment, not looking at camera, "
    "tasteful and non-sexualized, premium anime illustration"
)

QUALITY_SUFFIX = (
    "masterpiece, best quality, ultra-detailed, highly detailed face, polished shading, "
    "cinematic lighting, depth of field, vivid colors, anime aesthetic, 9:16 vertical format, "
    "single subject, detailed environment, no text, no watermark"
)

NEGATIVE_PROMPT = (
    "text, watermark, signature, logo, border, frame, split image, collage, multiple people, "
    "duplicate person, extra arms, extra fingers, deformed hands, bad anatomy, ugly face, "
    "asymmetrical eyes, poorly drawn eyes, messy hair, low detail face, blurry, muddy colors, "
    "dull lighting, flat background, empty scene, stock photo, realistic photo, child, elderly, "
    "sexualized pose, bikini, cleavage focus, staring at camera"
)

STYLE_VISUAL_GUIDE: dict[str, str] = {
    "lofi": (
        "cozy bedroom at night, moonlight through the window, warm desk lamp, city lights outside, "
        "dreamy calm atmosphere, soft blue and orange tones"
    ),
    "indie": (
        "cozy room, warm cinematic light, window glow, soft dreamy atmosphere, emotional late-night mood"
    ),
    "pop": (
        "clean polished room, bright soft neon, dreamy pastel glow, cute premium atmosphere"
    ),
    "electronic": (
        "futuristic room, neon blue and purple glow, holographic lighting, night city ambiance"
    ),
    "phonk": (
        "dark neon room or city-night background, purple-red glow, moody urban aesthetic"
    ),
    "trap": (
        "stylish urban night environment, teal and gold glow, premium modern mood"
    ),
    "rock": (
        "dramatic warm lights, rebellious cozy atmosphere, intense cinematic contrast"
    ),
    "metal": (
        "dark dramatic environment, red-black cinematic glow, intense elegant mood"
    ),
    "dark": (
        "mysterious moonlit room, purple shadow glow, gothic elegant atmosphere"
    ),
    "cinematic": (
        "grand emotional lighting, dramatic foggy glow, blockbuster mood, elegant scene depth"
    ),
    "funk": (
        "retro warm lights, playful color accents, stylish vibrant room atmosphere"
    ),
    "default": (
        "cozy night room, cinematic light, beautiful window glow, dreamy anime atmosphere"
    ),
}

# CENAS SEMPRE COM AÇÃO
SCENE_LIBRARY: dict[str, list[str]] = {
    "lofi": [
        "sitting by the window at night wearing headphones, watching the moon and listening to music",
        "writing in a notebook at a desk with headphones on, soft lamp light and calm focus",
        "leaning on the desk while listening to music, warm mug nearby, dreamy expression",
        "sitting on the bed with headphones, looking outside the window, cozy night vibe",
        "typing on a laptop at night while listening to music, peaceful late-night work mood",
    ],
    "indie": [
        "sitting by the window during sunset with headphones, soft emotional expression",
        "holding a notebook while listening to music, warm room light, thoughtful mood",
        "resting on the bed with headphones on, city lights outside, calm dreamy feeling",
        "sitting on the floor near the window with headphones, fairy lights glowing softly",
    ],
    "pop": [
        "sitting near a glowing window with headphones, playful dreamy expression",
        "dancing lightly in a cozy room with headphones on, soft neon glow",
        "holding a cup and listening to music near the window, cute polished vibe",
    ],
    "electronic": [
        "sitting at a futuristic desk with glowing headphones, looking out the neon-lit window",
        "leaning near a holographic window while listening to music, electric glow everywhere",
        "watching the night skyline with headphones, digital particles floating softly",
    ],
    "phonk": [
        "sitting by a neon-lit window at night with headphones, moody expression, urban glow",
        "leaning on the desk while listening to music, purple-red city lights outside",
        "resting by the window with headphones, dark stylish atmosphere and neon reflections",
    ],
    "trap": [
        "sitting in a stylish night room with headphones, looking out the city window confidently",
        "leaning at the desk with headphones, urban lights outside, premium cinematic mood",
        "relaxing on the bed with headphones on, luxury night ambiance and soft glow",
    ],
    "rock": [
        "sitting near the window with headphones, intense thoughtful expression, warm dramatic light",
        "leaning on a desk covered with notes while listening to music, electric emotional vibe",
        "resting by the bed with headphones and messy room lights, rebellious but soft mood",
    ],
    "metal": [
        "standing by a dramatic window with headphones off one ear, intense calm expression",
        "sitting in a dark elegant room with headphones, red-black glow and cinematic mood",
        "leaning by the window at night, listening deeply, storm-like dramatic lighting",
    ],
    "dark": [
        "sitting quietly by the moonlit window with headphones, mysterious elegant expression",
        "resting on the bed in a dark room with headphones, purple glow and emotional silence",
        "leaning near the desk while listening to music, gothic calm atmosphere",
    ],
    "cinematic": [
        "sitting by a large glowing window with headphones, emotional movie-like atmosphere",
        "writing softly at a desk while listening to music, grand warm-and-cool cinematic contrast",
        "watching the distant skyline from the room with headphones, dramatic elegant framing",
    ],
    "funk": [
        "sitting by the window with headphones, playful smile, warm retro lights around",
        "moving lightly to the rhythm in a cozy room, colorful glowing bulbs and fun vibe",
        "leaning at the desk with headphones, groovy warm atmosphere and lively room details",
    ],
    "default": [
        "sitting by the window at night with headphones, dreamy expression and cozy room light",
        "writing at a desk while listening to music, warm lamp light and city lights outside",
        "sitting on the bed with headphones, looking outside quietly, emotional late-night mood",
        "typing on a laptop at night with headphones on, calm focused atmosphere",
    ],
}

MOTION_HINTS = [
    "soft motion feeling, subtle movement, wind in hair",
    "candid storytelling moment, natural captured scene",
    "gentle emotional stillness, lived-in atmosphere",
]


# ══════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════

def _clean_song_name(filename: str) -> str:
    song_name = Path(filename).stem
    song_name = re.sub(r"\[[^\]]*\]|\{[^\}]*\}|\([^\)]*\)", "", song_name)
    song_name = re.sub(r"[_\-]+", " ", song_name).strip().title()
    return song_name or "Untitled Track"


def _pick_scene(style: str, short_num: int) -> str:
    scenes = SCENE_LIBRARY.get(style, SCENE_LIBRARY["default"])
    if not scenes:
        scenes = SCENE_LIBRARY["default"]
    index = max(0, (short_num - 1) % len(scenes))
    return scenes[index]


def _pick_motion_hint(short_num: int) -> str:
    index = max(0, (short_num - 1) % len(MOTION_HINTS))
    return MOTION_HINTS[index]


def _compact_prompt(text: str, max_chars: int = 1200) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


# ══════════════════════════════════════════════════════════════════════
# PROMPT BUILDING
# ══════════════════════════════════════════════════════════════════════

def build_ai_prompt(
    style: str,
    filename: str,
    styles: list[str],
    short_num: int = 1,
) -> str:
    """
    Gera prompt sempre no mesmo estilo:
    - anime cozy aesthetic
    - garota bonita/fofa
    - fazendo algo
    - cena rica, não forçada
    """
    song_name = _clean_song_name(filename)
    visual_ref = STYLE_VISUAL_GUIDE.get(style, STYLE_VISUAL_GUIDE["default"])
    scene = _pick_scene(style, short_num)
    motion_hint = _pick_motion_hint(short_num)
    all_styles = ", ".join(s.title() for s in styles) if styles else style.title()

    client = get_anthropic_client()
    if client is not None:
        try:
            return _opus_prompt(
                client=client,
                song_name=song_name,
                style=style,
                all_styles=all_styles,
                visual_ref=visual_ref,
                scene=scene,
                motion_hint=motion_hint,
            )
        except Exception as e:
            print(f"  [Claude] Falha ao gerar prompt: {e} — usando fallback")

    return _static_prompt(
        song_name=song_name,
        style=style,
        visual_ref=visual_ref,
        scene=scene,
        motion_hint=motion_hint,
    )


def _opus_prompt(
    client: anthropic.Anthropic,
    song_name: str,
    style: str,
    all_styles: str,
    visual_ref: str,
    scene: str,
    motion_hint: str,
) -> str:
    system = (
        "You are a professional creative director for a YouTube music Shorts channel. "
        "Create image prompts for Flux in a consistent premium anime cozy aesthetic. "
        "The image must always feature exactly one beautiful anime-style young woman doing something natural in a lived-in environment. "
        "Never make her pose stiffly or stare at the camera. "
        "The scene should feel like a candid moment from an anime. "
        "Output only the final prompt in English, comma-separated."
    )

    user = f"""
Create a Flux prompt for a vertical YouTube music Short.

Song name: "{song_name}"
Main music style: {style}
All detected styles: {all_styles}

Character style:
{BASE_GIRL_STYLE}

Scene action:
{scene}

Environment style:
{visual_ref}

Mood direction:
{motion_hint}

Rules:
- exactly one female subject
- beautiful, cute, natural, premium anime aesthetic
- must be doing something natural, not just standing still
- not looking at camera
- cozy or cinematic environment with depth
- strong face appeal but not close-up only
- no empty background
- 70 to 110 words max
- comma-separated visual elements only
"""

    resp = client.messages.create(
        model=get_anthropic_model(),
        max_tokens=260,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    prompt = resp.content[0].text.strip().strip('"').strip("'")
    return _compact_prompt(f"{prompt}, {QUALITY_SUFFIX}")


def _static_prompt(
    song_name: str,
    style: str,
    visual_ref: str,
    scene: str,
    motion_hint: str,
) -> str:
    templates = [
        (
            f"{BASE_GIRL_STYLE}, {scene}, {visual_ref}, inspired by the feeling of '{song_name}', "
            f"{motion_hint}, beautiful anime illustration, cozy cinematic atmosphere, {QUALITY_SUFFIX}"
        ),
        (
            f"anime music artwork for '{song_name}', {BASE_GIRL_STYLE}, {scene}, {visual_ref}, "
            f"{motion_hint}, natural storytelling scene, dreamy room aesthetic, {QUALITY_SUFFIX}"
        ),
        (
            f"viral YouTube Shorts anime visual, {BASE_GIRL_STYLE}, {scene}, {visual_ref}, "
            f"{motion_hint}, rich environment, emotional late-night mood, {QUALITY_SUFFIX}"
        ),
    ]
    return _compact_prompt(random.choice(templates))


# ══════════════════════════════════════════════════════════════════════
# REPLICATE
# ══════════════════════════════════════════════════════════════════════

REPLICATE_MODELS = [
    "black-forest-labs/flux-dev",
    "black-forest-labs/flux-schnell",
]

MODEL_PARAMS: dict[str, dict[str, Any]] = {
    "black-forest-labs/flux-dev": {
        "num_inference_steps": 28,
        "aspect_ratio": "9:16",
        "guidance": 3.5,
        "output_format": "png",
        "output_quality": 95,
        "disable_safety_checker": True,
    },
    "black-forest-labs/flux-schnell": {
        "num_inference_steps": 4,
        "aspect_ratio": "9:16",
        "output_format": "png",
        "output_quality": 95,
        "go_fast": True,
        "disable_safety_checker": True,
    },
}


def generate_image(prompt: str, output_path: str | None = None) -> str | None:
    token = os.getenv("REPLICATE_API_TOKEN")
    if not token:
        print("  [Replicate] REPLICATE_API_TOKEN não configurado.")
        return None

    os.environ["REPLICATE_API_TOKEN"] = token
    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    full_prompt = _compact_prompt(
        f"{prompt}, detailed scene, natural action, cozy storytelling composition, "
        f"beautiful anime girl, expressive eyes, soft glossy hair, premium lighting"
    )

    for model in REPLICATE_MODELS:
        params = {**MODEL_PARAMS.get(model, {}), "prompt": full_prompt}

        if "flux-dev" in model:
            params["negative_prompt"] = NEGATIVE_PROMPT

        for attempt in range(1, MAX_TRIES + 1):
            try:
                print(f"  [Replicate] Tentativa {attempt} — {model.split('/')[-1]}")
                output = replicate.run(model, input=params)

                url = _extract_url(output)
                if not url:
                    print("  [Replicate] URL não encontrada na resposta.")
                    continue

                saved = _download_image(url, output_path)
                if saved:
                    print(f"  [Replicate] Imagem salva: {saved}")
                    return saved

            except Exception as e:
                wait = 2 ** attempt
                print(f"  [Replicate] Erro ({e}). Aguardando {wait}s…")
                time.sleep(wait)

    print("  [Replicate] Todas as tentativas falharam.")
    return None


def _extract_url(output: object) -> str | None:
    if isinstance(output, str) and output.startswith("http"):
        return output

    if isinstance(output, list) and output:
        first = output[0]
        if hasattr(first, "url"):
            return str(first.url)
        if isinstance(first, str) and first.startswith("http"):
            return first

    try:
        for item in output:  # type: ignore
            if hasattr(item, "url"):
                return str(item.url)
            if isinstance(item, str) and item.startswith("http"):
                return item
    except Exception:
        pass

    return None


def _download_image(url: str, output_path: str | None = None) -> str | None:
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()

        if not output_path:
            ts = int(time.time())
            output_path = str(SAVE_DIR / f"ai_bg_{ts}.png")

        with open(output_path, "wb") as f:
            f.write(resp.content)

        size = os.path.getsize(output_path)
        if size < 50_000:
            print(f"  [Replicate] Imagem suspeita: {size} bytes — descartando.")
            os.remove(output_path)
            return None

        return output_path

    except Exception as e:
        print(f"  [Replicate] Download falhou: {e}")
        return None
