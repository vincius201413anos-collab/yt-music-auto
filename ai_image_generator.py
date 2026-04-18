"""
ai_image_generator.py — Gerador de imagens com máxima variedade visual.
Cada short tem personagem única: etnia, cabelo, roupa, expressão e cena diferentes.
"""

import os
import re
import time
import random
import requests
from pathlib import Path

import replicate
import anthropic

SAVE_DIR = Path("temp")
MAX_TRIES = 3

_anthropic_client: anthropic.Anthropic | None = None

def get_anthropic_client() -> anthropic.Anthropic:
    global _anthropic_client
    if _anthropic_client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY nao configurado.")
        _anthropic_client = anthropic.Anthropic(api_key=api_key)
    return _anthropic_client

def get_anthropic_model() -> str:
    return os.getenv("ANTHROPIC_MODEL", "claude-opus-4-5")


# ══════════════════════════════════════════════════════════════════════
# VARIAÇÕES DE PERSONAGEM — garante diversidade visual máxima
# ══════════════════════════════════════════════════════════════════════

CHARACTER_VARIATIONS = [
    # Variação 1 — Asiática, cabelo preto liso longo
    {
        "hair": "long straight black hair, side-swept bangs",
        "skin": "light porcelain skin tone",
        "eyes": "large dark almond-shaped eyes",
        "vibe": "elegant and mysterious",
    },
    # Variação 2 — Latina, cabelo castanho ondulado
    {
        "hair": "long wavy chestnut brown hair with loose curls",
        "skin": "warm olive skin tone, sun-kissed",
        "eyes": "expressive brown eyes with long lashes",
        "vibe": "passionate and confident",
    },
    # Variação 3 — Europeia, cabelo loiro platinum
    {
        "hair": "platinum blonde hair in a messy bun with loose strands",
        "skin": "fair rosy skin tone with light freckles",
        "eyes": "sharp blue-grey eyes",
        "vibe": "cool and rebellious",
    },
    # Variação 4 — Negra, cabelo afro volumoso
    {
        "hair": "voluminous natural afro hair with gold accessories",
        "skin": "deep rich brown skin tone, glowing",
        "eyes": "large expressive dark eyes",
        "vibe": "powerful and radiant",
    },
    # Variação 5 — Cabelo roxo/fantasia
    {
        "hair": "short edgy purple and black hair with undercut",
        "skin": "pale cool skin tone",
        "eyes": "dramatic violet eyes with bold eyeliner",
        "vibe": "alternative and intense",
    },
    # Variação 6 — Cabelo ruivo
    {
        "hair": "long flowing auburn red hair, slightly wavy",
        "skin": "light freckled skin with warm undertones",
        "eyes": "green or amber eyes, sharp gaze",
        "vibe": "fierce and free-spirited",
    },
    # Variação 7 — Cabelo prata/branco futurista
    {
        "hair": "silver-white straight hair cut at the shoulder",
        "skin": "neutral beige skin tone",
        "eyes": "glowing silver or pale blue eyes",
        "vibe": "futuristic and ethereal",
    },
    # Variação 8 — Cabelo preto com mechas coloridas
    {
        "hair": "black hair with neon blue and pink streaks, half up",
        "skin": "warm tan skin tone",
        "eyes": "dark eyes with colorful eye shadow",
        "vibe": "playful and energetic",
    },
    # Variação 9 — Cabelo castanho escuro, tranças
    {
        "hair": "long dark brown box braids with gold thread",
        "skin": "medium brown skin tone, luminous",
        "eyes": "deep brown eyes, intense gaze",
        "vibe": "strong and graceful",
    },
    # Variação 10 — Cabelo rosa pastel
    {
        "hair": "soft pastel pink wavy hair, flowing",
        "skin": "soft peach skin tone",
        "eyes": "wide innocent rose-pink eyes",
        "vibe": "dreamy and gentle",
    },
]

# ══════════════════════════════════════════════════════════════════════
# PERFIS POR GÊNERO
# ══════════════════════════════════════════════════════════════════════

GENRE_PROFILES = {
    "lofi": {
        "outfit": "oversized hoodie or cozy knit sweater, large over-ear headphones",
        "pose": "chin resting on hand, sitting at a desk, peaceful sleepy expression",
        "environment": "cozy bedroom at night, warm desk lamp, rain drops on window, city lights blurred, steaming coffee mug, fairy lights, plants",
        "palette": "warm amber and deep blue, soft candlelight, purple night sky",
        "mood": "calm, nostalgic, studying late at night",
        "fx": "floating musical notes, soft bokeh rain outside, moonlight",
    },
    "indie": {
        "outfit": "vintage band tee or flowy blouse, small gold earrings, light natural makeup",
        "pose": "holding a vinyl record or sitting by a window, wistful expression",
        "environment": "rooftop at golden hour, warm orange sunset, worn brick walls with posters, string lights, polaroid photos",
        "palette": "golden amber, dusty rose, warm film grain, faded vintage tones",
        "mood": "emotional, nostalgic, bittersweet",
        "fx": "film grain texture, sunset lens flare, wind in hair",
    },
    "rock": {
        "outfit": "ripped band tee, leather jacket with patches, fingerless gloves, heavy boots",
        "pose": "holding electric guitar, fierce rebellious expression, confident powerful stance",
        "environment": "dramatic concert stage, intense spotlights, smoke machines, crowd silhouettes, sparks",
        "palette": "deep orange and electric blue stage lights, high contrast shadows",
        "mood": "raw power, rebellion, adrenaline",
        "fx": "guitar sparks, stage smoke, dramatic rim lighting",
    },
    "metal": {
        "outfit": "black corset dress with dark lace, ornate gothic jewelry, chains around wrists",
        "pose": "standing in wind, intense powerful presence, dramatic pose",
        "environment": "dark epic fantasy landscape, storm clouds with red lightning, ancient castle ruins, glowing embers, black ravens",
        "palette": "deep crimson red, pitch black, glowing ember orange, silver highlights",
        "mood": "dark power, gothic elegance, epic",
        "fx": "glowing runes, floating chains, black ravens, ember particles",
    },
    "phonk": {
        "outfit": "oversized hoodie with kanji, cap tilted low, dark streetwear, tattoo on neck",
        "pose": "leaning against a car, hands in pockets, cool intimidating expression",
        "environment": "underground parking lot at 3am, red neon lights on wet concrete, sports car headlights, graffiti walls, city highway",
        "palette": "deep red neon, pitch black, concrete grey, magenta highlights",
        "mood": "aggressive, cool, underground, night drive",
        "fx": "wet concrete reflections, neon signs, smoke wisps",
    },
    "trap": {
        "outfit": "designer streetwear, gold jewelry, high-end sneakers, long styled nails",
        "pose": "confident luxury expression, holding phone, boss energy stance",
        "environment": "penthouse rooftop at night, luxury city skyline, swimming pool with teal light, gold and chrome decor",
        "palette": "teal and gold, deep purple night sky, chrome reflections",
        "mood": "wealth, ambition, luxury, power",
        "fx": "city light reflections on water, gold accents, neon skyline glow",
    },
    "electronic": {
        "outfit": "futuristic outfit with light-up details, LED headphones or holographic visor",
        "pose": "arms raised, dancing, euphoric expression, glowing neon tattoos on skin",
        "environment": "massive festival mainstage at night, laser beams, LED screen visuals, crowd with glowsticks, holographic particles",
        "palette": "electric blue, neon purple, cyan, vivid magenta lasers",
        "mood": "euphoria, energy, futuristic, peak moment",
        "fx": "laser grid patterns, holographic particles, bass-wave distortion",
    },
    "dark": {
        "outfit": "flowing dark cloak or elegant black dress, ethereal dark aesthetic",
        "pose": "half face in shadow, standing alone, melancholic powerful aura",
        "environment": "moonlit abandoned cathedral, broken stained glass, moonbeams through dust, overgrown dark vines, flickering candles, mist",
        "palette": "deep indigo, silver moonlight, cold teal mist, near-black shadows",
        "mood": "mysterious, haunting, ethereal, poetic darkness",
        "fx": "moonlight shafts, dust motes, flickering candles",
    },
    "pop": {
        "outfit": "colorful pastel outfit with accessories, cute hair accessories",
        "pose": "bright radiant smile, heart gesture or peace sign, cheerful stance",
        "environment": "dreamy pastel studio, neon signs, confetti and sakura petals, ring lights, glitter, cloud backdrop",
        "palette": "soft pink, lavender, sky blue, sparkle gold, pastel rainbow",
        "mood": "joyful, energetic, fresh, youthful",
        "fx": "confetti burst, sparkle particles, heart shapes, pastel bokeh",
    },
    "electronic": {
        "outfit": "futuristic outfit with light-up details, LED headphones or holographic visor",
        "pose": "arms raised, dancing, euphoric expression",
        "environment": "massive festival mainstage, laser beams, LED screen visuals, crowd with glowsticks",
        "palette": "electric blue, neon purple, cyan, vivid magenta lasers",
        "mood": "euphoria, energy, futuristic",
        "fx": "laser grid, holographic particles, bass-wave distortion",
    },
    "cinematic": {
        "outfit": "elegant warrior or adventurer attire, flowing cape",
        "pose": "intense determined expression, hair blowing in heroic wind, strong powerful pose",
        "environment": "epic landscape at dramatic sunset, towering mountains, storm clouds, god rays, ancient temple ruins",
        "palette": "teal and orange cinematic grade, dramatic god rays, golden-hour warmth",
        "mood": "epic, emotional, heroic, cinematic scale",
        "fx": "god rays, floating magical particles, epic scale, cinematic lens flare",
    },
    "default": {
        "outfit": "stylish contemporary outfit with headphones",
        "pose": "expressive emotional eyes, captivating presence",
        "environment": "dramatic music-inspired atmosphere, cinematic lighting, premium aesthetic",
        "palette": "vivid dramatic colors, high contrast, cinematic grade",
        "mood": "emotional, captivating, scroll-stopping",
        "fx": "musical atmosphere, premium visual quality",
    },
}

QUALITY_SUFFIX = (
    "masterpiece, best quality, ultra-detailed, sharp focus, "
    "anime illustration style, 9:16 vertical composition, centered subject, "
    "beautiful detailed eyes, cinematic lighting, vivid saturated colors, "
    "high contrast, professional digital art, "
    "no text, no watermark, no extra people, single subject only"
)

NEGATIVE_PROMPT = (
    "text, watermark, signature, logo, border, frame, "
    "split image, collage, multiple people, duplicate person, two girls, "
    "extra arms, extra fingers, deformed hands, bad anatomy, "
    "ugly face, blurry, muddy, dull, flat lighting, "
    "underexposed, overexposed, low quality, stock photo, "
    "realistic photo, elderly, child, "
    "sexualized pose, revealing outfit, bikini, cleavage focus, "
    "generic background, boring composition"
)

SCENE_VARIANTS = {
    "lofi":       ["late night studying", "rainy window mood", "3am city lights", "soft lamplight corner", "pre-dawn quiet"],
    "indie":      ["golden hour rooftop", "film photo moment", "sunset window", "vintage afternoon", "bittersweet memory"],
    "rock":       ["concert climax", "backstage intensity", "solo guitar moment", "crowd energy peak", "electric storm"],
    "metal":      ["dark storm ritual", "ember and chain chaos", "gothic throne scene", "ravens in red sky", "power awakening"],
    "phonk":      ["3am parking lot", "night highway drift", "red neon alley", "underground scene", "cold concrete night"],
    "trap":       ["penthouse night view", "luxury poolside", "midnight city hustle", "gold and chrome moment", "skyline boss"],
    "electronic": ["festival drop moment", "laser rave peak", "holographic future", "neon crowd wave", "mainstage euphoria"],
    "dark":       ["moonlit cathedral", "abandoned church fog", "midnight forest", "silver moonbeam", "solitary darkness"],
    "pop":        ["sparkle confetti burst", "idol stage debut", "pastel dream world", "glitter rain moment", "kawaii peak"],
    "cinematic":  ["epic cliff reveal", "heroic wind moment", "god rays emergence", "emotional skyline", "legendary stance"],
    "default":    ["premium music mood", "dramatic light scene", "vivid cinematic", "emotional atmosphere", "scroll-stopping visual"],
}


# ══════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════

def _clean_song_name(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(r"\[[^\]]*\]|\{[^\}]*\}|\([^\)]*\)", "", name)
    name = re.sub(r"[_\-]+", " ", name).strip().title()
    return name or "Untitled Track"

def _pick_variant(style: str, short_num: int) -> str:
    pool = SCENE_VARIANTS.get(style, SCENE_VARIANTS["default"])
    return pool[(short_num - 1) % len(pool)]

def _pick_character(style: str, short_num: int) -> dict:
    """
    Seleciona variação de personagem de forma determinística por short_num
    mas com offset por estilo para garantir diversidade entre estilos diferentes.
    """
    style_offsets = {
        "lofi": 0, "indie": 2, "rock": 4, "metal": 6, "phonk": 1,
        "trap": 3, "electronic": 5, "dark": 7, "pop": 9, "cinematic": 8, "default": 0,
    }
    offset = style_offsets.get(style, 0)
    idx = (short_num - 1 + offset) % len(CHARACTER_VARIATIONS)
    return CHARACTER_VARIATIONS[idx]

def _compact_prompt(text: str, max_chars: int = 950) -> str:
    return re.sub(r"\s+", " ", text).strip()[:max_chars]


# ══════════════════════════════════════════════════════════════════════
# PROMPT BUILDING
# ══════════════════════════════════════════════════════════════════════

def build_ai_prompt(style: str, filename: str, styles: list, short_num: int = 1) -> str:
    song_name = _clean_song_name(filename)
    profile = GENRE_PROFILES.get(style, GENRE_PROFILES["default"])
    character = _pick_character(style, short_num)
    scene_variant = _pick_variant(style, short_num)
    all_styles = ", ".join(s.title() for s in styles) if styles else style.title()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            return _claude_prompt(song_name, style, all_styles, profile, character, scene_variant)
        except Exception as e:
            print(f"  [Claude] Falha no prompt: {e} — usando fallback")

    return _static_prompt(profile, character, scene_variant)


def _claude_prompt(
    song_name: str, style: str, all_styles: str,
    profile: dict, character: dict, scene_variant: str,
) -> str:
    client = get_anthropic_client()

    system = (
        "You are a master visual director for a premium YouTube music Shorts channel. "
        "You create breathtaking Flux image prompts that are cinematic, scroll-stopping, and emotionally powerful. "
        "Each prompt must feature exactly ONE beautiful anime-style girl as the central subject. "
        "Use the exact character description provided — do not change her appearance. "
        "Output ONLY the prompt in English — comma-separated visual elements, no explanation, no quotes."
    )

    user = f"""Create a cinematic Flux prompt for a vertical YouTube music Short.

Song: "{song_name}"
Genre: {style} ({all_styles})
Scene: {scene_variant}

CHARACTER (use exactly as described):
- Hair: {character['hair']}
- Skin: {character['skin']}
- Eyes: {character['eyes']}
- Vibe: {character['vibe']}
- Outfit: {profile['outfit']}
- Pose: {profile['pose']}

Environment: {profile['environment']}
Color palette: {profile['palette']}
Mood: {profile['mood']}
Special FX: {profile['fx']}

Rules:
- Exactly ONE female subject with the character details above
- 9:16 vertical composition, subject centered
- Dramatic intentional lighting — not flat
- Make someone STOP scrolling
- 60–100 words, comma-separated
- No text, no watermark, no extra people"""

    resp = client.messages.create(
        model=get_anthropic_model(),
        max_tokens=250,
        system=system,
        messages=[{"role": "user", "content": user}],
    )

    prompt = resp.content[0].text.strip().strip('"').strip("'")
    full = f"{prompt}, {QUALITY_SUFFIX}"
    print(f"  [Claude] Prompt gerado ({len(full)} chars)")
    return _compact_prompt(full)


def _static_prompt(profile: dict, character: dict, scene_variant: str) -> str:
    prompt = (
        f"one beautiful anime girl, {character['hair']}, {character['skin']}, "
        f"{character['eyes']}, {character['vibe']} expression, "
        f"{profile['outfit']}, {profile['pose']}, "
        f"{profile['environment']}, {scene_variant}, "
        f"{profile['palette']}, {profile['mood']}, {profile['fx']}, "
        f"{QUALITY_SUFFIX}"
    )
    return _compact_prompt(prompt)


# ══════════════════════════════════════════════════════════════════════
# REPLICATE
# ══════════════════════════════════════════════════════════════════════

REPLICATE_MODELS = [
    "black-forest-labs/flux-dev",
    "black-forest-labs/flux-schnell",
]

MODEL_PARAMS = {
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
    token = os.environ.get("REPLICATE_API_TOKEN")
    if not token:
        print("  [Replicate] REPLICATE_API_TOKEN nao configurado.")
        return None

    os.environ["REPLICATE_API_TOKEN"] = token
    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    quality_reinforcement = (
        ", anime-style, one beautiful female character, "
        "detailed face, premium cinematic composition, "
        "vivid colors, dramatic lighting, sharp focus, masterpiece"
    )
    full_prompt = _compact_prompt(prompt + quality_reinforcement)

    for model in REPLICATE_MODELS:
        params = {**MODEL_PARAMS.get(model, {}), "prompt": full_prompt}
        if "flux-dev" in model:
            params["negative_prompt"] = NEGATIVE_PROMPT

        for attempt in range(1, MAX_TRIES + 1):
            try:
                model_short = model.split("/")[-1]
                print(f"  [Replicate] Tentativa {attempt}/{MAX_TRIES} — {model_short}")
                output = replicate.run(model, input=params)
                url = _extract_url(output)
                if not url:
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


def _download_image(url: str, output_path: str | None = None) -> str | None:
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        if not output_path:
            output_path = str(SAVE_DIR / f"ai_bg_{int(time.time())}.png")
        with open(output_path, "wb") as f:
            f.write(resp.content)
        if os.path.getsize(output_path) < 50_000:
            print(f"  [Replicate] Imagem suspeita — descartando.")
            os.remove(output_path)
            return None
        return output_path
    except Exception as e:
        print(f"  [Replicate] Download falhou: {e}")
        return None
