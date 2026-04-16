"""
ai_image_generator.py — Gerador de imagens IA de alta qualidade.
Sempre prioriza uma personagem feminina estilizada, bonita e fofa,
adaptada ao gênero da música, para visuais mais fortes em Shorts.
"""

import os
import re
import time
import random
import requests
from pathlib import Path

import replicate
import anthropic

# ══════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════

SAVE_DIR = Path("temp")
MAX_TRIES = 3


def get_anthropic_model() -> str:
    return os.getenv("ANTHROPIC_MODEL", "claude-opus-4-7")


# ══════════════════════════════════════════════════════════════════════
# GUIA VISUAL BASE POR ESTILO
# ══════════════════════════════════════════════════════════════════════

STYLE_VISUAL_GUIDE = {
    "electronic": (
        "futuristic neon environment, electric blue and purple glow, holographic particles, "
        "night city lights, dynamic synthwave atmosphere, vivid luminous energy"
    ),
    "phonk": (
        "dark neon street at night, red and magenta glow, sports car reflections, smoke, "
        "street energy, moody city background, intense contrast"
    ),
    "trap": (
        "luxury urban night setting, vivid teal and gold lighting, stylish city skyline, "
        "premium street fashion mood, dramatic spotlight, modern high-energy atmosphere"
    ),
    "rock": (
        "dramatic concert lights, orange and blue glow, rebellious energy, wind in the hair, "
        "stage-like cinematic atmosphere, raw electric intensity"
    ),
    "metal": (
        "dark epic fantasy sky, red-black lighting, chains, storm energy, dramatic embers, "
        "powerful aura, intense cinematic darkness with vivid highlights"
    ),
    "pop": (
        "bright pastel neon glow, dreamy sparkles, soft pink and purple lights, joyful premium mood, "
        "cute vibrant atmosphere, polished pop-art shine"
    ),
    "indie": (
        "golden-hour cinematic window light, soft dreamy haze, warm amber and rose tones, "
        "emotional cozy atmosphere, filmic softness, intimate urban mood"
    ),
    "lofi": (
        "cozy bedroom at night, headphones, moonlight through the window, warm desk lamp, "
        "rainy city ambiance, calm emotional stillness, soft blue and purple tones"
    ),
    "funk": (
        "retro-futuristic disco lighting, vibrant warm colors, glowing lights, rhythmic energy, "
        "playful stylish atmosphere, saturated disco mood"
    ),
    "cinematic": (
        "epic cinematic lighting, god rays, dramatic fog, widescreen blockbuster atmosphere, "
        "high-end teal-orange color grade, emotional visual scale"
    ),
    "dark": (
        "mysterious moonlit atmosphere, vivid purple and teal mist, elegant shadows, "
        "gothic energy, dramatic dark fantasy mood, glowing accents"
    ),
    "default": (
        "dramatic music-inspired atmosphere, vivid neon lighting, polished cinematic mood, "
        "high contrast, premium visual impact"
    ),
}

# Guia da personagem feminina por estilo
GIRL_STYLE_GUIDE = {
    "electronic": (
        "one beautiful anime-style young woman, cute and elegant face, glowing headphones, "
        "futuristic outfit, luminous eyes, stylish hair, centered composition"
    ),
    "phonk": (
        "one beautiful anime-style young woman, edgy streetwear, confident expression, "
        "dark stylish vibe, long flowing hair, centered composition"
    ),
    "trap": (
        "one beautiful anime-style young woman, fashionable urban look, luxury street style, "
        "clean makeup, confident pose, centered composition"
    ),
    "rock": (
        "one beautiful anime-style young woman, rebellious aesthetic, expressive eyes, "
        "cool attitude, dynamic hair, centered composition"
    ),
    "metal": (
        "one beautiful gothic anime-style young woman, elegant dark outfit, red eyes glow, "
        "dramatic presence, centered composition"
    ),
    "pop": (
        "one beautiful anime-style young woman, cute charming face, soft smile, polished idol-like vibe, "
        "bright stylish outfit, centered composition"
    ),
    "indie": (
        "one beautiful anime-style young woman, soft emotional expression, cozy sweater, "
        "dreamy natural beauty, centered composition"
    ),
    "lofi": (
        "one beautiful anime-style young woman, cute calm expression, oversized hoodie, "
        "headphones, peaceful night-listening vibe, centered composition"
    ),
    "funk": (
        "one beautiful anime-style young woman, playful stylish expression, colorful retro fashion, "
        "fun vibrant energy, centered composition"
    ),
    "cinematic": (
        "one beautiful anime-style young woman, elegant dramatic presence, emotional face, "
        "premium cinematic styling, centered composition"
    ),
    "dark": (
        "one beautiful gothic anime-style young woman, mysterious elegant expression, dark fashion, "
        "subtle glow accents, centered composition"
    ),
    "default": (
        "one beautiful anime-style young woman, cute and stylish, expressive eyes, "
        "premium polished look, centered composition"
    ),
}

NEGATIVE_PROMPT = (
    "text, watermark, signature, logo, border, frame, split image, collage, multiple people, "
    "duplicate person, two girls, extra arms, extra fingers, deformed hands, bad anatomy, ugly face, "
    "blurry, muddy, dull, flat lighting, underexposed, overexposed, low contrast, low quality, "
    "stock photo, realistic photo, elderly, child, sexualized pose, revealing outfit, bikini, cleavage focus"
)

MOOD_VARIANTS = {
    "lofi": ["night window", "moonlight room", "city lights", "rainy night", "soft dreamy desk"],
    "indie": ["golden hour", "city rooftop", "window reflection", "warm film mood", "sunset room"],
    "pop": ["sparkle glow", "dreamy neon", "cute idol mood", "bright pastel energy", "soft glam"],
    "trap": ["luxury night", "city neon", "confident spotlight", "teal-gold mood", "street glam"],
    "phonk": ["night drive vibe", "dark neon street", "smoke and red glow", "retro car light", "moody city"],
    "rock": ["stage light energy", "electric atmosphere", "wind and fire glow", "concert intensity", "rebellious mood"],
    "metal": ["embers and chains", "storm sky", "dark red aura", "epic gothic mood", "shadow power"],
    "electronic": ["holographic glow", "futuristic lights", "synthwave city", "laser atmosphere", "digital particles"],
    "cinematic": ["epic god rays", "dramatic fog", "heroic framing", "emotional scale", "grand atmosphere"],
    "dark": ["moonlit mist", "purple shadow glow", "mysterious night", "gothic elegance", "dark fantasy vibe"],
    "funk": ["retro disco shine", "playful color burst", "groovy warm lights", "dancefloor glow", "stylish sparkle"],
    "default": ["premium music mood", "anime aesthetic", "polished light", "dreamy scene", "vivid glow"],
}


# ══════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════

def _clean_song_name(filename: str) -> str:
    song_name = Path(filename).stem
    song_name = re.sub(r"\[[^\]]*\]|\{[^\}]*\}|\([^\)]*\)", "", song_name)
    song_name = re.sub(r"[_\-]+", " ", song_name).strip().title()
    return song_name or "Untitled Track"


def _pick_variant(style: str, short_num: int) -> str:
    pool = MOOD_VARIANTS.get(style, MOOD_VARIANTS["default"])
    if not pool:
        return "premium music mood"
    index = max(0, (short_num - 1) % len(pool))
    return pool[index]


def _compact_prompt(text: str, max_chars: int = 900) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


# ══════════════════════════════════════════════════════════════════════
# PROMPT BUILDING
# ══════════════════════════════════════════════════════════════════════

def build_ai_prompt(style: str, filename: str, styles: list, short_num: int = 1) -> str:
    """
    Sempre gera prompt focado em uma personagem feminina estilizada,
    bonita e fofa, adaptada ao gênero da música.
    """
    song_name = _clean_song_name(filename)
    visual_ref = STYLE_VISUAL_GUIDE.get(style, STYLE_VISUAL_GUIDE["default"])
    girl_ref = GIRL_STYLE_GUIDE.get(style, GIRL_STYLE_GUIDE["default"])
    all_styles = ", ".join(s.title() for s in styles) if styles else style.title()
    mood_variant = _pick_variant(style, short_num)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        try:
            return _opus_prompt(
                song_name=song_name,
                style=style,
                all_styles=all_styles,
                visual_ref=visual_ref,
                girl_ref=girl_ref,
                mood_variant=mood_variant,
                api_key=api_key,
            )
        except Exception as e:
            print(f"  [Claude] Falha ao gerar prompt: {e} — usando fallback")

    return _static_prompt(
        song_name=song_name,
        style=style,
        visual_ref=visual_ref,
        girl_ref=girl_ref,
        mood_variant=mood_variant,
    )


def _opus_prompt(
    song_name: str,
    style: str,
    all_styles: str,
    visual_ref: str,
    girl_ref: str,
    mood_variant: str,
    api_key: str,
) -> str:
    client = anthropic.Anthropic(api_key=api_key)

    system = (
        "You are a professional creative director for a YouTube music Shorts channel. "
        "You create image prompts for Flux that are scroll-stopping, premium, vivid and beautiful. "
        "The image must always feature exactly one beautiful anime-style young woman as the central subject. "
        "She must feel tasteful, charming, visually striking, stylish and emotionally expressive. "
        "Avoid realism. Avoid stock-photo vibes. Avoid generic backgrounds. "
        "Output ONLY the final image prompt, in English, comma-separated, no explanation."
    )

    user = f"""
Create a Flux prompt for a vertical YouTube music Short.

Song name: "{song_name}"
Main music style: {style}
All detected styles: {all_styles}
Scene mood variation: {mood_variant}

Character direction:
{girl_ref}

Visual environment:
{visual_ref}

Rules:
- exactly one female subject
- anime-style young woman
- beautiful, cute, polished, premium aesthetic
- tasteful and non-sexualized
- strong face appeal and expressive eyes
- centered subject for 9:16 vertical composition
- music-themed atmosphere matching the genre
- vivid colors, dramatic lighting, scroll-stopping look
- no text, no watermark, no extra people, no collage
- 60 to 100 words max
- comma-separated visual elements only
"""

    resp = client.messages.create(
        model=get_anthropic_model(),
        max_tokens=220,
        system=system,
        messages=[{"role": "user", "content": user}],
    )

    prompt = resp.content[0].text.strip().strip('"').strip("'")
    prompt = _compact_prompt(prompt)
    print(f"  [Claude] Prompt gerado ({len(prompt)} chars)")
    return prompt


def _static_prompt(
    song_name: str,
    style: str,
    visual_ref: str,
    girl_ref: str,
    mood_variant: str,
) -> str:
    templates = [
        (
            f"{girl_ref}, {visual_ref}, {mood_variant}, inspired by the feeling of '{song_name}', "
            f"beautiful anime aesthetic, vivid lighting, premium music visual, elegant pose, "
            f"cute expressive face, detailed hair, sharp focus, high contrast, 9:16 vertical, masterpiece"
        ),
        (
            f"music artwork for '{song_name}', {girl_ref}, {visual_ref}, {mood_variant}, "
            f"cute and beautiful anime-style young woman, scroll-stopping composition, "
            f"cinematic glow, polished colors, detailed eyes, centered subject, premium Shorts visual"
        ),
        (
            f"viral YouTube Shorts anime music visual, {girl_ref}, {visual_ref}, {mood_variant}, "
            f"stylish feminine character, premium aesthetic, dramatic light, vivid colors, "
            f"high detail, clean composition, centered framing, elegant emotional atmosphere"
        ),
    ]
    return _compact_prompt(random.choice(templates))


# ══════════════════════════════════════════════════════════════════════
# REPLICATE — GERAÇÃO DE IMAGEM
# ══════════════════════════════════════════════════════════════════════

REPLICATE_MODELS = [
    "black-forest-labs/flux-schnell",
    "black-forest-labs/flux-dev",
]

MODEL_PARAMS = {
    "black-forest-labs/flux-schnell": {
        "num_inference_steps": 4,
        "aspect_ratio": "9:16",
        "output_format": "png",
        "output_quality": 95,
        "go_fast": True,
        "disable_safety_checker": True,
    },
    "black-forest-labs/flux-dev": {
        "num_inference_steps": 28,
        "aspect_ratio": "9:16",
        "guidance": 3.5,
        "output_format": "png",
        "output_quality": 95,
        "disable_safety_checker": True,
    },
}


def generate_image(prompt: str, output_path: str = None) -> str | None:
    token = os.getenv("REPLICATE_API_TOKEN")
    if not token:
        print("  [Replicate] REPLICATE_API_TOKEN não configurado.")
        return None

    os.environ["REPLICATE_API_TOKEN"] = token
    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    full_prompt = _compact_prompt(
        prompt
        + ", anime-style, one female character, beautiful face, cute charm, premium composition, "
          "vivid colors, cinematic lighting, detailed eyes, high contrast, sharp focus, masterpiece, best quality"
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


def _extract_url(output) -> str | None:
    if isinstance(output, str) and output.startswith("http"):
        return output

    if isinstance(output, list) and output:
        first = output[0]
        if hasattr(first, "url"):
            return str(first.url)
        if isinstance(first, str) and first.startswith("http"):
            return first

    try:
        for item in output:
            if hasattr(item, "url"):
                return str(item.url)
            if isinstance(item, str) and item.startswith("http"):
                return item
    except Exception:
        pass

    return None


def _download_image(url: str, output_path: str = None) -> str | None:
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
