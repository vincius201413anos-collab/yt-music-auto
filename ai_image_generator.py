"""
ai_image_generator.py — v8.0 HYBRID CYBERPUNK GIRLS EDITION
============================================================
VERSÃO HÍBRIDA APERFEIÇOADA:
- Mantém a inteligência do v6: variação por conceito visual A/B/C/D.
- Mantém a força do v7: anime cyberpunk girl, neon, chuva, cidade, trap/phonk.
- Evita repetição: não é sempre a mesma personagem igual template.
- Mantém identidade: girls cyberpunk sombrias, neon roxo/ciano/vermelho, vibe trap/phonk.
- Prompts mais específicos, menos genéricos, menos “AI slop”.
- Compatível com o pipeline antigo: build_ai_prompt(...) e generate_image(...).
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

REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN", "")

# Mantém compatibilidade com flux-dev usado no seu bot.
REPLICATE_MODELS = [
    "black-forest-labs/flux-dev",
]

# Caso seu main.py use generate_background_image(), esses params entram.
FLUX_PARAMS = {
    "width": 1080,
    "height": 1920,
    "num_inference_steps": 50,
    "guidance_scale": 7.5,
    "num_outputs": 1,
    "output_format": "png",
    "output_quality": 100,
    "disable_safety_checker": True,
}


# ══════════════════════════════════════════════════════════════════════
# IDENTIDADE VISUAL — FIXA, MAS NÃO REPETITIVA
# ══════════════════════════════════════════════════════════════════════

CHANNEL_IDENTITY = (
    "DJ darkMark visual identity, dark anime cyberpunk music visual, "
    "trap and phonk energy, seductive but platform-safe, powerful and mysterious"
)

# A identidade é fixa no ESTILO, não no mesmo rosto sempre.
CHARACTER_DNA = (
    "one cyberpunk anime girl, adult woman, varied appearance, "
    "sharp edgy anime features, cold confident expression, intense gaze, "
    "dark futuristic streetwear or tactical cyberpunk outfit with neon accents, "
    "subtle cybernetic implants glowing cyan or magenta, "
    "glowing neon eyes, high contrast face lighting, alone in frame, "
    "not cute, not childish, not generic waifu"
)

CYBERPUNK_STYLE_DNA = (
    "anime key visual, premium cel shading, sharp clean lineart, "
    "Studio Trigger inspired energy, Cyberpunk Edgerunners inspired color direction, "
    "dynamic composition, cinematic 9:16 vertical portrait, "
    "deep black shadows, ultra vivid neon bloom, rain, fog, wet reflections"
)

BACKGROUND_DNA = (
    "cyberpunk city at night, heavy rain, wet asphalt reflections, "
    "neon signs, holographic billboards, dark alleys, rooftop edges, "
    "underground parking lots, drifting smoke, volumetric fog, "
    "purple cyan magenta and blood red neon lighting, cinematic depth"
)

LIGHTING_DNA = (
    "dramatic rim lighting, neon backlight, cyan side light, magenta highlights, "
    "deep shadows, high contrast chiaroscuro, lens flare, bokeh neon background, "
    "rain droplets catching light, reflective wet surfaces"
)

QUALITY_TAGS = (
    "masterpiece, best quality, ultra-detailed anime illustration, "
    "professional anime key visual, extremely sharp lineart, "
    "premium cel shading, cinematic composition, dynamic pose, "
    "deep rich blacks, luminous neon highlights, atmospheric depth, "
    "volumetric neon lighting, scroll-stopping visual impact, "
    "9:16 vertical format, high retention YouTube Shorts background"
)

NEGATIVE_PROMPT = (
    "photorealistic, hyperrealistic, photography, 3d render, CGI, real human, "
    "child, young teen, childish face, chibi, kawaii, cute mascot, "
    "nsfw, nude, explicit, revealing outfit, fetish, "
    "multiple people, crowd, extra limbs, extra fingers, bad hands, bad anatomy, "
    "deformed face, distorted face, asymmetrical eyes, malformed body, "
    "text, watermark, signature, logo, frame, border, username, "
    "blurry, low quality, muddy colors, washed out colors, pastel colors, "
    "bright daylight, warm cozy aesthetic, cheerful mood, "
    "generic anime waifu, generic purple gradient, empty background, plain studio background, "
    "boring composition, repetitive, forgettable, AI slop, plastic skin, uncanny valley, "
    "green dominant, yellow dominant, brown dominant, orange sunset dominant"
)


# ══════════════════════════════════════════════════════════════════════
# VARIAÇÕES DE PERSONAGEM
# ══════════════════════════════════════════════════════════════════════

HAIR_VARIATIONS = [
    "long black hair with blunt bangs and violet neon rim light",
    "short silver hair with black streaks, messy cyberpunk cut",
    "white silver hair with black underlayer, wind blown in rain",
    "black bob haircut with glowing magenta hair clips",
    "long dark purple hair with shaved side and cybernetic temple implant",
    "silver twin tails with black cyberpunk ribbons, mature serious look",
    "messy black hair covering one eye, red neon reflection across face",
    "white hair with magenta tips, wet strands from heavy rain",
]

EYE_VARIATIONS = [
    "glowing blood red eyes",
    "glowing magenta eyes",
    "glowing cyan eyes",
    "one red eye and one cyan cybernetic eye",
    "violet glowing eyes with tiny circuit pattern in the iris",
]

OUTFIT_VARIATIONS = [
    "black tactical bodysuit with neon purple seams",
    "oversized black cyberpunk jacket over dark combat outfit",
    "dark streetwear techwear outfit with glowing cyan lines",
    "black armored crop jacket over platform-safe futuristic outfit",
    "hooded black tactical jacket with red neon trim",
    "dark biker cyberpunk outfit with reflective wet leather texture",
]

POSE_VARIATIONS = [
    "looking directly at camera with cold intense stare, low angle shot",
    "side profile, face half in shadow and half in neon light",
    "standing in rain, glancing over shoulder at the viewer",
    "walking through fog in slow motion, city lights blurred behind",
    "crouching on wet asphalt, dominant low angle perspective",
    "standing on rooftop edge, neon city below, hair moving in wind",
    "extreme close up on glowing eyes, rain drops on face",
    "full body shot, powerful stance, one hand near cybernetic headset",
    "silhouette with neon outline, face barely visible except glowing eyes",
]

CAMERA_VARIATIONS = [
    "close up portrait, face focus, shallow depth of field",
    "medium shot, chest to crown framing, cinematic portrait",
    "full body shot, dynamic pose, vertical composition",
    "low angle shot, dominant perspective",
    "top view cinematic shot, rain falling toward camera",
    "three quarter view, strong diagonal composition",
    "extreme close up, eyes and neon reflections dominate",
]


# ══════════════════════════════════════════════════════════════════════
# ESTILOS ARTÍSTICOS — rota para não parecer tudo igual
# ══════════════════════════════════════════════════════════════════════

ART_STYLES = [
    (
        "premium cel-shaded anime illustration, sharp shadow boundaries, "
        "clean flat color fills, vivid saturated neon against deep black, "
        "Studio Trigger inspired dark cyberpunk key visual"
    ),
    (
        "dark painterly anime illustration, confident brush strokes, "
        "dramatic chiaroscuro lighting, atmospheric color bleed, "
        "Yoji Shinkawa meets Cyberpunk Edgerunners mood"
    ),
    (
        "manga-inspired dark cyberpunk illustration, heavy ink linework, "
        "high contrast black base with selective neon accents, "
        "sharp cross-hatching in shadows"
    ),
    (
        "digital glitch anime illustration, chromatic aberration edges, "
        "scanline texture, RGB split in shadows, corrupted neon cyberpunk mood"
    ),
]


# ══════════════════════════════════════════════════════════════════════
# CONCEITOS VISUAIS POR GÊNERO
# A/B/C/D = character / scene / cinematic / abstract
# ══════════════════════════════════════════════════════════════════════

VISUAL_CONCEPTS = {
    "phonk": [
        {
            "type": "character",
            "label": "PHONK_CYBER_GIRL",
            "anchor": "drift car headlights cutting through purple fog behind her",
            "scene": (
                "{character}, standing in an abandoned underground parking lot at 3am, "
                "wet concrete reflecting blood red neon, drift car headlights cutting through purple fog behind her, "
                "cassette tape ribbon unraveling around her boots, aggressive phonk night drive energy"
            ),
            "palette": "blood red, neon purple, cyan rim light, absolute black shadows",
        },
        {
            "type": "scene",
            "label": "PHONK_NIGHT_DRIVE",
            "anchor": "empty drift road reflected in cracked rearview mirror",
            "scene": (
                "empty cyberpunk highway at midnight, no dominant character, wet asphalt mirror reflections, "
                "red taillights dissolving into fog, cracked rearview mirror reflecting a neon girl silhouette, "
                "dark city signs flickering in purple rain"
            ),
            "palette": "black asphalt, blood red taillights, violet fog, cyan neon edges",
        },
        {
            "type": "cinematic",
            "label": "PHONK_TUNNEL_GIRL",
            "anchor": "massive red neon circle tunnel behind her",
            "scene": (
                "{character}, walking toward camera inside a massive underground tunnel, "
                "enormous red neon circle portal behind her, water dripping from concrete ceiling, "
                "her shadow stretches toward viewer, cinematic phonk cover art"
            ),
            "palette": "absolute black tunnel, crimson portal, purple haze, cold cyan edge light",
        },
        {
            "type": "abstract",
            "label": "PHONK_BASS_SHOCKWAVE",
            "anchor": "808 bass shockwave cracking the city floor",
            "scene": (
                "808 bass wave made visible as crimson shockwave cracking wet asphalt, "
                "neon anime girl silhouette inside the wave, glass shards floating in slow motion, "
                "vinyl record splitting under bass pressure"
            ),
            "palette": "blood red shockwave, electric violet cracks, black void, cyan sparks",
        },
    ],
    "trap": [
        {
            "type": "character",
            "label": "TRAP_LUXURY_GIRL",
            "anchor": "rain on penthouse glass reflecting neon city grid",
            "scene": (
                "{character}, standing at floor-to-ceiling penthouse window at night, "
                "rain on glass reflecting the entire neon city grid, luxury darkness, "
                "cold confident expression, trap queen cyberpunk energy"
            ),
            "palette": "electric violet city, cyan reflections, black luxury interior, magenta highlights",
        },
        {
            "type": "scene",
            "label": "TRAP_ROOFTOP",
            "anchor": "violet glowing helipad in rain",
            "scene": (
                "luxury cyberpunk rooftop at night, no dominant character, "
                "helipad H marking glowing violet in rain puddle, storm clouds above, neon city below, "
                "two abandoned glasses on ledge catching cyan light"
            ),
            "palette": "violet rain, cyan city lights, black sky, magenta reflections",
        },
        {
            "type": "cinematic",
            "label": "TRAP_CITY_CENTER",
            "anchor": "girl as still center of moving neon city",
            "scene": (
                "{character}, overhead shot on rooftop, looking up at camera, "
                "entire neon city grid spreading around her like a circuit board, "
                "she is the still center of the moving city"
            ),
            "palette": "electric violet grid, cyan streets, black buildings, magenta eye glow",
        },
        {
            "type": "abstract",
            "label": "TRAP_808_ARCHITECTURE",
            "anchor": "808 waveform rendered as neon architecture",
            "scene": (
                "808 waveform rendered as violet neon architecture floating in black void, "
                "gold chain links dissolving into frequency particles, cyberpunk girl silhouette reflected in glass bass waves"
            ),
            "palette": "violet architecture, cyan frequency lines, black void, magenta highlights",
        },
    ],
    "dark": [
        {
            "type": "character",
            "label": "DARK_MIRROR_GIRL",
            "anchor": "mirror shards reflecting different versions of her face",
            "scene": (
                "{character}, surrounded by floating shattered mirror fragments in dark void, "
                "each mirror shard reflecting a different angle of her glowing eyes, "
                "purple fog, sinister calm, beautiful and dangerous"
            ),
            "palette": "near black, crimson eyes, violet mirror edges, cyan rim light",
        },
        {
            "type": "scene",
            "label": "DARK_ABANDONED_DISTRICT",
            "anchor": "abandoned arcade machine still glowing in rain",
            "scene": (
                "abandoned cyberpunk district at night, no dominant character, "
                "one arcade machine still running in the rain, flickering violet screen, "
                "fog at ground level, broken neon signs, dark vines on buildings"
            ),
            "palette": "cold black, violet arcade glow, red neon fragments, rain silver",
        },
        {
            "type": "cinematic",
            "label": "DARK_FLARE_GIRL",
            "anchor": "single red emergency flare lighting flooded underground space",
            "scene": (
                "{character}, tiny figure in vast flooded underground space, "
                "holding a single red emergency flare, water at ankle level reflecting crimson light, "
                "absolute darkness beyond the circle of light"
            ),
            "palette": "single crimson light, black flood water, violet fog, pale skin glow",
        },
        {
            "type": "abstract",
            "label": "DARK_HEARTBEAT",
            "anchor": "heartbeat line erupting into crimson pulse rings",
            "scene": (
                "dark melody visualized as EKG heartbeat line erupting into crimson pulse rings, "
                "black ink spreading through neon water, cyberpunk girl silhouette barely visible inside the pulse"
            ),
            "palette": "black ink, crimson pulse, violet outer rings, cyan static",
        },
    ],
    "electronic": [
        {
            "type": "character",
            "label": "ELECTRONIC_LASER_GIRL",
            "anchor": "horizontal red laser crossing her glowing eyes",
            "scene": (
                "{character}, standing in heavy rain on cyberpunk street, "
                "single horizontal red laser crossing her glowing eyes, holograms behind her, "
                "digital glitch artifacts around her outline"
            ),
            "palette": "red laser, cyan rain, magenta holograms, black street",
        },
        {
            "type": "scene",
            "label": "ELECTRONIC_EMPTY_RAVE",
            "anchor": "empty rave stage running lasers for no audience",
            "scene": (
                "underground rave venue empty before the crowd, no dominant character, "
                "laser grid cutting through smoke, massive subwoofer stacks glowing red, "
                "dust particles visible in UV purple light"
            ),
            "palette": "UV purple, red lasers, cyan haze, black concrete",
        },
        {
            "type": "cinematic",
            "label": "ELECTRONIC_STAGE_GIRL",
            "anchor": "girl silhouette controlling the drop from stage",
            "scene": (
                "{character}, rear silhouette on stage facing enormous dark crowd, "
                "massive LED wall exploding with crimson and violet visuals behind her, "
                "she controls the frequency of thousands"
            ),
            "palette": "crimson LED wall, violet crowd haze, cyan rim light, pure black silhouette",
        },
        {
            "type": "abstract",
            "label": "ELECTRONIC_SUPERNOVA",
            "anchor": "bass drop as neon supernova",
            "scene": (
                "bass drop visualized as neon supernova expanding from center point, "
                "frequency rings bending light, glitch anime girl silhouette in the white-hot core"
            ),
            "palette": "white hot center, cyan rings, magenta explosion, black void",
        },
    ],
    "lofi": [
        {
            "type": "character",
            "label": "LOFI_RAIN_WINDOW",
            "anchor": "she reads by the glow of her own neon eyes",
            "scene": (
                "{character}, seated on windowsill in abandoned library at 3am, "
                "reading by the glow of her own neon eyes, rain on glass beside her, "
                "city fog outside, quiet dark cyberpunk mood"
            ),
            "palette": "warm amber lamp, cyan rain, violet city fog, black room",
        },
        {
            "type": "scene",
            "label": "LOFI_CLOSED_CAFE",
            "anchor": "closed cafe with one lamp still on",
            "scene": (
                "small cyberpunk coffee shop after closing, no dominant character, "
                "one pendant lamp still on, forgotten cup steaming, rain streaming down glass, "
                "neon CLOSED sign half lit"
            ),
            "palette": "amber lamp, blue black outside, magenta sign, rain silver",
        },
        {
            "type": "cinematic",
            "label": "LOFI_TRAIN_GIRL",
            "anchor": "last train leaving while she stays",
            "scene": (
                "{character}, standing on empty subway platform watching the last train leave, "
                "train lights streaking into tunnel darkness, headphone wire visible, "
                "rain dripping from ceiling grate"
            ),
            "palette": "yellow train streak, teal shadows, crimson eye glow, violet platform haze",
        },
        {
            "type": "abstract",
            "label": "LOFI_VINYL",
            "anchor": "vinyl groove glowing softly",
            "scene": (
                "vinyl record spinning in dark room, groove glowing softly as visible melody, "
                "dust particles suspended in amber light, neon girl reflection distorted on record surface"
            ),
            "palette": "black vinyl, amber dust, violet reflection, cyan edge light",
        },
    ],
    "default": [
        {
            "type": "character",
            "label": "DEFAULT_CYBER_GIRL",
            "anchor": "rain falls only inside the neon cone of light around her",
            "scene": (
                "{character}, standing in dark neon alley, rain falling only inside the cone of light around her, "
                "wet pavement reflecting red and violet signs, mysterious precise energy"
            ),
            "palette": "blood red, violet, cyan, absolute black",
        },
        {
            "type": "scene",
            "label": "DEFAULT_CITY_GLASS",
            "anchor": "city seen through shattered windshield",
            "scene": (
                "abandoned car interior, no dominant character, shattered windshield framing cyberpunk city skyline, "
                "each glass shard reflecting neon differently, dashboard radio static glowing"
            ),
            "palette": "midnight blue, red neon shards, violet rain, cyan dashboard static",
        },
        {
            "type": "cinematic",
            "label": "DEFAULT_RAINDROP",
            "anchor": "entire city reflected in one raindrop on her face",
            "scene": (
                "{character}, extreme close shot, single raindrop on cheek reflecting entire neon city skyline, "
                "glowing eye visible behind shallow depth of field"
            ),
            "palette": "crimson eye, violet city reflection, cyan bokeh, pale skin",
        },
        {
            "type": "abstract",
            "label": "DEFAULT_SOUND_ARCHITECTURE",
            "anchor": "song waveform as building you can walk into",
            "scene": (
                "song waveform rendered as cyberpunk architecture, bass frequencies as foundation columns, "
                "melody as glass spire, rhythm as neon archways, girl silhouette at entrance"
            ),
            "palette": "red structure, violet glass, cyan windows, black sky",
        },
    ],
}

GENRE_MAP = {
    "phonk": "phonk",
    "trap": "trap",
    "dark": "dark",
    "electronic": "electronic",
    "dubstep": "electronic",
    "edm": "electronic",
    "lofi": "lofi",
    "indie": "default",
    "rock": "dark",
    "metal": "dark",
    "cinematic": "dark",
    "funk": "trap",
    "pop": "default",
}


# ══════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════

def _compact(text: str, max_len: int = 3900) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace(" ,", ",").replace(",,", ",")
    return text[:max_len].rstrip(" ,")


def _seed(filename: str, short_num: int) -> int:
    key = f"{filename}|{short_num}|v8_hybrid_cyberpunk_girls"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % (10 ** 9)


def _rng(filename: str, short_num: int) -> random.Random:
    return random.Random(_seed(filename, short_num))


def _clean_song_name(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(r"\[[^\]]*\]|\{[^\}]*\}|\([^\)]*\)", "", name)
    name = re.sub(r"[_\-]+", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name or "dark phonk"


def _pick_concept(style: str, filename: str, short_num: int) -> dict:
    mapped = GENRE_MAP.get(style, style)
    concepts = VISUAL_CONCEPTS.get(mapped, VISUAL_CONCEPTS["default"])
    index = (max(1, short_num) - 1) % len(concepts)
    return concepts[index]


def _pick_style_parts(filename: str, short_num: int) -> dict:
    rng = _rng(filename, short_num)
    return {
        "hair": rng.choice(HAIR_VARIATIONS),
        "eyes": rng.choice(EYE_VARIATIONS),
        "outfit": rng.choice(OUTFIT_VARIATIONS),
        "pose": rng.choice(POSE_VARIATIONS),
        "camera": rng.choice(CAMERA_VARIATIONS),
        "art": rng.choice(ART_STYLES),
    }


def _build_character(parts: dict) -> str:
    return (
        f"{CHARACTER_DNA}, {parts['hair']}, {parts['eyes']}, "
        f"{parts['outfit']}, {parts['pose']}, {parts['camera']}"
    )


def _song_micro_detail(song_name: str) -> str:
    clean = song_name.lower()

    if any(w in clean for w in ["car", "drive", "drift", "night", "road"]):
        return "subtle drift car silhouette and road light streaks inspired by the song title"
    if any(w in clean for w in ["ghost", "phantom", "shadow", "dark"]):
        return "ghostly hologram distortion and shadow doubles inspired by the song title"
    if any(w in clean for w in ["rain", "cry", "sad", "alone"]):
        return "rain-heavy mood with lonely neon reflections inspired by the song title"
    if any(w in clean for w in ["fire", "burn", "rage"]):
        return "neon fire sparks and crimson heat haze inspired by the song title"
    if any(w in clean for w in ["bass", "drop", "808"]):
        return "visible bass shockwave rings bending neon light inspired by the song title"

    return "one unforgettable micro-detail connected to the song title"


# ══════════════════════════════════════════════════════════════════════
# PROMPT PRINCIPAL — COMPATÍVEL COM SEU BOT
# ══════════════════════════════════════════════════════════════════════

def build_ai_prompt(style: str, filename: str, styles: list | None = None, short_num: int = 1) -> str:
    styles = styles or []
    song_name = _clean_song_name(filename)

    rng = _rng(filename, short_num)

    poses = [
        "looking at camera",
        "side profile",
        "walking forward in rain",
        "standing still in neon fog",
        "low angle dominant pose"
    ]

    moods = [
        "aggressive",
        "mysterious",
        "dark seductive",
        "emotionless",
        "melancholic"
    ]

    scenes = [
        "cyberpunk city at night with heavy rain",
        "underground parking lot with neon reflections",
        "dark alley with flickering lights",
        "cosmic void with floating particles",
        "rooftop with neon skyline"
    ]

    pose = rng.choice(poses)
    mood = rng.choice(moods)
    scene = rng.choice(scenes)

    prompt = (
        f"{mood} cyberpunk anime girl, {pose}, "
        f"{scene}, glowing neon eyes, black hoodie, "
        f"purple cyan magenta lighting, volumetric fog, rain reflections, "
        f"high contrast, cinematic composition, phonk trap aesthetic, "
        f"ultra detailed, masterpiece, best quality, 8k, 9:16 vertical"
    )

    return _compact(prompt)


# ══════════════════════════════════════════════════════════════════════
# GERAÇÃO DE IMAGEM — COMPATÍVEL COM PIPELINE ANTIGO
# ══════════════════════════════════════════════════════════════════════

def generate_image(prompt: str, output_path: str | None = None) -> str | None:
    """
    Gera imagem via Replicate.
    Compatível com o fluxo antigo do seu main.py.
    """
    if not REPLICATE_API_TOKEN:
        logger.error("REPLICATE_API_TOKEN não configurado.")
        return None

    if output_path is None:
        output_path = "temp/generated_background.png"

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    full_prompt = _compact(
        prompt
        + ", dark anime cyberpunk illustration, NOT photorealistic, NOT 3D render, "
        + "anime key visual, cyberpunk girl, deep black shadows, neon purple cyan magenta red, "
        + "rain, wet reflections, volumetric fog, cinematic high contrast, not generic AI image"
    )

    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }

    last_error: Optional[Exception] = None

    for model in REPLICATE_MODELS:
        for attempt in range(1, 4):
            try:
                logger.info(f"  [Replicate] Tentativa {attempt}/3 — {model}")

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
                        if isinstance(output, list):
                            image_url = output[0]
                        else:
                            image_url = output

                        if not image_url:
                            raise RuntimeError("Replicate retornou output vazio.")

                        img = requests.get(image_url, timeout=90)
                        img.raise_for_status()

                        with open(output_path, "wb") as f:
                            f.write(img.content)

                        logger.info(f"  [Replicate] Salvo: {output_path}")
                        return output_path

                    if status == "failed":
                        raise RuntimeError(data.get("error") or "Replicate falhou.")

                raise TimeoutError("Replicate demorou demais para gerar imagem.")

            except Exception as e:
                last_error = e
                logger.warning(f"  [Replicate] Falhou: {e}")
                time.sleep(3 * attempt)

    logger.error(f"  [Replicate] Todas as tentativas falharam: {last_error}")
    return None


# ══════════════════════════════════════════════════════════════════════
# FUNÇÕES EXTRAS — CASO ALGUMA PARTE DO BOT USE
# ══════════════════════════════════════════════════════════════════════

def build_prompt(style: str = "default", seed_variant: int = 0) -> tuple[str, str]:
    """
    Compatibilidade com versões que chamavam build_prompt().
    """
    fake_filename = f"{style}_variant_{seed_variant}.mp3"
    prompt = build_ai_prompt(style=style, filename=fake_filename, styles=[style], short_num=seed_variant + 1)
    return prompt, NEGATIVE_PROMPT


def generate_background_image(
    style: str = "phonk",
    output_path: str = "assets/background.png",
    seed_variant: int = 0,
    max_retries: int = 3,
) -> Optional[str]:
    """
    Compatibilidade com versões que chamavam generate_background_image().
    """
    prompt, _negative = build_prompt(style=style, seed_variant=seed_variant)

    for attempt in range(1, max_retries + 1):
        result = generate_image(prompt, output_path)
        if result:
            return result
        logger.warning(f"  ⚠ Tentativa background {attempt}/{max_retries} falhou.")
        time.sleep(3 * attempt)

    return None


def get_or_generate_background(
    style: str = "phonk",
    output_dir: str = "assets/backgrounds",
    force_new: bool = False,
) -> Optional[str]:
    """
    Retorna um background existente ou gera um novo.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    existing = list(Path(output_dir).glob(f"{style}_bg_*.png"))

    if existing and not force_new:
        chosen = random.choice(existing)
        logger.info(f"  ► Background reutilizado: {chosen}")
        return str(chosen)

    variant = random.randint(0, 99)
    output_path = str(Path(output_dir) / f"{style}_bg_{variant:02d}.png")
    return generate_background_image(style=style, output_path=output_path, seed_variant=variant)


def generate_background_batch(
    styles: list[str],
    output_dir: str = "assets/backgrounds",
    variants_per_style: int = 2,
) -> dict[str, list[str]]:
    """
    Gera múltiplos backgrounds por estilo.
    """
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

    parser = argparse.ArgumentParser(description="AI Image Generator v8.0 — Hybrid Cyberpunk Girls")
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
