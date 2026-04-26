"""
ai_image_generator.py — DJ DARK MARK v30 PERFECT CYBERPUNK GIRLS
=============================================================
CHANGELOG v30:
- MODELOS TROCADOS: adicionado animagine-xl e anything-v5 (muito melhores para full body anime)
- FLUX_PARAMS: resolução alterada para 768x1344 (ratio 4:7 força mais espaço vertical para corpo)
- PROMPT REORDENADO: pose/composição vem PRIMEIRO antes de qualquer descrição de rosto
- BODY_LOCK v3: linguagem ainda mais direta, frases curtas que os modelos entendem melhor
- GENERATION_SUFFIX reforçado com triggers técnicos: "full body", "wide shot", "from head to toe"
- NEGATIVE PROMPT: adicionado "portrait", "face focus", "upper body" explicitamente
- PALETA: azul/cyan banido em todas as camadas
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
    # Animagine XL — melhor para anime full body, composição vertical
    "cjwbw/animagine-xl-3.1",
    # Fallback: Anything v5 — clássico anime, respeita bem composição de corpo
    "lucataco/anything-v5-better-vae",
    # Último fallback: Flux-dev
    "black-forest-labs/flux-dev",
]

FLUX_PARAMS = {
    # 768x1344 = ratio ~1:1.75 — força mais espaço vertical, menos tendência a focar no rosto
    # Equivale a aprox. 9:16 mas com pixels suficientes para mostrar corpo completo
    "width":               int(os.getenv("FLUX_WIDTH",    "768")),
    "height":              int(os.getenv("FLUX_HEIGHT",   "1344")),
    "num_inference_steps": int(os.getenv("FLUX_STEPS",    "35")),
    "guidance_scale":      float(os.getenv("FLUX_GUIDANCE", "7.5")),
    "num_outputs": 1,
    "output_format": "png",
    "output_quality": 100,
    "disable_safety_checker": True,
}


# ══════════════════════════════════════════════════════════════════════
# IDENTIDADE DO CANAL
# ══════════════════════════════════════════════════════════════════════

CHANNEL_IDENTITY = (
    "DJ darkMark visual identity, dark anime trapstar edit, viral phonk cover art, "
    "YouTube Shorts music visualizer, underground trap phonk cyberpunk aesthetic"
)


# ══════════════════════════════════════════════════════════════════════
# LOCKS PRINCIPAIS — V30 TRAPSTAR CYBERPUNK + ANTI-BLUE NUCLEAR
# ══════════════════════════════════════════════════════════════════════

TRAPSTAR_DNA = (
    "one adult anime woman, "
    "beautiful cyberpunk trapstar girl, underground phonk dark pop visual identity, "
    "cute but dangerous, soft face with chaotic energy, "
    "dark anime girl, extremely attractive, expressive eyes, glossy lips, sharp eyeliner, "
    "sweet and unhinged at the same time, fofa maluca malvada vibe, "
    "confident trap queen energy, mysterious, seductive, intimidating, "
    "not generic, memorable character design, unique silhouette, "
    "wearing: oversized black hoodie OR black leather jacket OR dark techwear jacket OR cropped black hoodie, "
    "chunky chain necklace, black choker, piercings, rings, chain belt, "
    "dark cargo pants OR black mini skirt OR techwear shorts OR thigh-high boots, "
    "platform boots or combat boots, "
    "subtle tattoos, nose ring or lip ring or eyebrow piercing, "
    "alone, no other characters, no crowds"
)

# ══════════════════════════════════════════════════════════════════════
# BODY LOCK V4 — FRASES CURTAS + ORDEM PRIORITÁRIA
# ══════════════════════════════════════════════════════════════════════

BODY_LOCK = (
    "full body, "
    "full length character, "
    "wide shot, "
    "long shot, "
    "head to toe visible, "
    "whole body visible, "
    "legs visible, "
    "boots visible, "
    "feet in frame, "
    "complete outfit visible, "
    "full silhouette visible, "
    "face beautiful but not close-up, "
    "body dominant composition, "
    "vertical poster framing, "
    "centered character, "
    "9:16 aspect ratio"
)

# ══════════════════════════════════════════════════════════════════════
# STYLE LOCK — CYBERPUNK TRAPSTAR ESPECÍFICO
# ══════════════════════════════════════════════════════════════════════

STYLE_LOCK = (
    "premium 2D anime illustration, "
    "dark cyberpunk anime key visual, "
    "sharp clean lineart, polished cel shading, "
    "dramatic shadows, high contrast lighting, "
    "viral phonk cover art aesthetic, "
    "dark pop music visualizer background, "
    "professional anime music thumbnail, "
    "cinematic cyberpunk streetwear fashion, "
    "not realistic, not 3D, not photo"
)

# ══════════════════════════════════════════════════════════════════════
# PALETA — ANTI-AZUL NUCLEAR V30
# ══════════════════════════════════════════════════════════════════════

PALETTE_HARD_LOCK = (
    "magenta dominant color palette, "
    "hot pink neon accents, "
    "deep violet shadows, "
    "dark purple atmosphere, "
    "crimson red highlights, "
    "warm orange secondary rim light, "
    "near-black background, "
    "dark red and violet mood, "
    "no blue, no cyan, no teal, no turquoise, no aqua, "
    "avoid cold blue lighting, avoid icy colors, "
    "warm neon palette only, magenta violet red only"
)

# ══════════════════════════════════════════════════════════════════════
# LIGHTING — QUENTE E DIRECIONAL
# ══════════════════════════════════════════════════════════════════════

LIGHTING_LOCK = (
    "cinematic neon lighting, "
    "hot magenta rim light, "
    "deep violet backlight, "
    "warm red-orange key light from one side, "
    "face beautifully lit, eyes glowing with neon reflection, "
    "dark background, subject clearly separated from background, "
    "soft smoke haze, wet reflective highlights, "
    "no blue light, no cyan light, no cold overexposure"
)

# ══════════════════════════════════════════════════════════════════════
# SKIN — TOM NATURAL ANIME
# ══════════════════════════════════════════════════════════════════════

SKIN_LOCK = (
    "warm pale anime skin, "
    "natural skin tone, "
    "light beige or warm ivory, "
    "soft blush on cheeks, "
    "no blue skin, no cyan skin, no cold skin tone, "
    "not blue-tinted, not cyan-tinted, "
    "warm skin color"
)

RETENTION_LOCK = (
    "scroll-stopping viral YouTube Shorts thumbnail, "
    "strong visual impact in under one second, "
    "character instantly recognizable, "
    "beautiful face, powerful silhouette, "
    "full body centered, "
    "space at bottom for DJ logo and waveform overlay, "
    "dark anime music video energy, "
    "high CTR phonk trap dark pop thumbnail"
)

QUALITY_LOCK = (
    "masterpiece, best quality, ultra detailed anime illustration, "
    "clean anatomy, beautiful face, sharp eyes, detailed outfit, "
    "professional dark cyberpunk anime poster, "
    "high resolution, crisp lineart, polished shading"
)


# ══════════════════════════════════════════════════════════════════════
# NEGATIVE PROMPT V30 — ANTI-AZUL MÁXIMO + COMPOSIÇÃO FORÇADA
# ══════════════════════════════════════════════════════════════════════

NEGATIVE_PROMPT = (
    "blue, cyan, teal, turquoise, aqua, cobalt, azure, cerulean, "
    "blue background, cyan background, teal background, "
    "blue hair, cyan hair, teal hair, blue highlights, cyan highlights, "
    "blue eyes, cyan eyes, teal eyes, blue iris, "
    "blue skin, cyan skin, blue-tinted skin, cold skin, gray skin, "
    "blue light, cyan light, teal light, cold light, ice light, "
    "blue neon, cyan neon, teal neon, blue glow, cyan glow, teal glow, "
    "cold atmosphere, cold color palette, icy tones, "
    "green, yellow, washed out colors, desaturated, flat colors, "
    "ugly, bad anatomy, bad face, distorted face, asymmetrical eyes, lazy eye, "
    "bad hands, extra fingers, missing fingers, fused fingers, fused limbs, "
    "long neck, broken body, disfigured, mutated, "
    "melted face, uncanny valley, blurry, low quality, jpeg artifacts, noise, "
    "photorealistic, realistic, photography, real person, 3D render, CGI, doll, plastic skin, "
    "child, underage, loli, chibi, schoolgirl, baby face, teenager, young girl, "
    "nude, explicit nudity, genitalia, nipples, porn, erotic explicit, "
    "multiple people, crowd, two girls, group, duplicate character, "
    "text, words, logo, watermark, signature, letters, numbers, username, "
    "portrait, headshot, bust shot, close-up, extreme close-up, "
    "face only, face filling frame, upper body only, waist up, shoulders up, "
    "cropped legs, cropped body, missing legs, missing feet, missing lower body, "
    "bad composition, boring pose, generic anime girl, plain outfit, "
    "overexposed, too much glow, bloom overload, color chaos"
)


# ══════════════════════════════════════════════════════════════════════
# VARIAÇÕES — V30 TRAPSTAR CYBERPUNK, SEM AZUL
# ══════════════════════════════════════════════════════════════════════

HAIR_VARIATIONS = [
    "long black hair with glossy magenta rim light, soft messy strands, beautiful anime bangs",
    "short sharp black bob, glossy hair, gothic cyberpunk cut, hot pink edge light",
    "long black hair under oversized dark hood, pink neon catching the hair tips",
    "black hair with deep crimson streaks, wild but beautiful, trapstar energy",
    "messy black twin tails with chain accessories, cute but dangerous",
    "long silver white hair with black roots, magenta glow, dramatic contrast",
    "white platinum hair with hot pink streaks, cyberpunk villain princess vibe",
    "dark burgundy hair, glossy waves, warm red neon reflection",
    "black to deep violet ombre hair, rich dark gradient, sharp anime bangs",
    "messy high ponytail, black hair, loose strands, seductive chaotic energy",
    "black wolfcut hair, punk anime style, hot pink rim light",
    "long black wavy hair flowing in neon wind, dark queen aesthetic",
]

EYE_VARIATIONS = [
    "bright glowing pink eyes, extremely detailed, hypnotic, wet neon reflections",
    "neon violet eyes with sharp reflections, cute but insane stare",
    "glowing magenta eyes with tiny star highlights, unforgettable gaze",
    "deep crimson red eyes, cold villain stare, beautiful and dangerous",
    "soft pink eyes with chaotic shine, innocent but unstable",
    "pink-violet glowing eyes, seductive and dark, intense eye contact",
    "crazy glowing eyes with spark effects inside the iris",
    "half-lidded violet eyes, calm but terrifying energy",
    "wide cute anime eyes with dangerous madness behind them",
    "sharp red eyes with glossy reflections, evil princess vibe",
]

EXPRESSION_VARIATIONS = [
    "cute but dangerous smile, slightly insane eyes, playful but threatening",
    "soft innocent face with crazy glowing eyes, unhinged beauty",
    "adorable smile hiding pure chaos, sweet but evil aura",
    "sweet cute expression with psychotic stare, dual personality",
    "calm relaxed face but eyes full of rage and insanity",
    "gentle soft smile, eyes glowing like a villain",
    "seductive look with unstable chaotic energy, unpredictable girl",
    "innocent anime girl face with dark evil aura, contrast vibe",
    "smiling softly while looking completely insane in the eyes",
    "cold emotionless face with a tiny twitching smile, creepy cute vibe",
    "fofa and malvada expression, cute lips, dangerous eyes",
    "shy little smile but intimidating stare, cyberpunk yandere energy",
    "confident trap queen smirk, superior energy, looking directly at viewer",
    "blank dead stare, beautiful face, terrifying calm energy",
]

POSE_VARIATIONS = [
    "full body standing pose, one hand in hoodie pocket, legs apart, complete figure head to boots",
    "full body walking toward camera, jacket flowing, chains moving, boots visible",
    "full body low angle shot, looking down at viewer, boots visible, powerful silhouette",
    "full body leaning against neon wall, one knee bent, full outfit visible",
    "full body arms crossed, weight on one hip, dominant stance, complete silhouette",
    "full body sitting on concrete ledge, legs visible, boots visible, dark relaxed pose",
    "full body crouched slightly, one hand near face, mischievous crazy smile, boots visible",
    "full body three-quarter turn, looking back over shoulder, complete figure visible",
    "full body hand reaching toward camera, rest of body fully visible behind, dramatic perspective",
    "full body standing in rain, hood up, chains glowing, boots and legs visible",
    "full body dancing subtly to phonk music, smooth confident pose, complete outfit visible",
    "full body holding chain loosely, dark aura around boots, head to toe visible",
]

OUTFIT_VARIATIONS = [
    "oversized black hoodie, dark mini skirt, thigh-high boots, chunky chain necklace, choker",
    "black leather jacket open, dark crop top, cargo pants, combat boots, silver chains",
    "black techwear vest, strapped cargo pants, platform boots, fingerless gloves, chain belt",
    "oversized black puffer jacket, dark shorts, thigh-high black boots, gold Cuban chain",
    "cropped black hoodie, high-waisted black pants, platform boots, choker and layered chains",
    "long black trench coat open, dark fitted outfit underneath, heavy chains, combat boots",
    "dark gothic corset top, black wide-leg pants, platform boots, multiple chain layers",
    "black zip-up tracksuit top half open, dark shorts, thigh-high boots, piercings",
    "oversized black graphic tee, black mini skirt, thigh-high stockings, platform boots, chains",
    "black cyberpunk bodysuit with cargo straps, chunky boots, fingerless gloves, choker",
    "dark hooded jacket with metal zipper details, black skirt, tall boots, magenta accessories",
    "black streetwear set, cropped jacket, baggy pants, heavy sneakers, cyberpunk jewelry",
]

SCENE_VARIATIONS = [
    "dark cyberpunk alley, magenta neon lights flickering, wet reflective ground, heavy fog",
    "underground neon tunnel, hot pink and red lights, glitch distortion, cinematic darkness",
    "dark futuristic street, glowing magenta signs, rainy night, reflections everywhere",
    "pure black void background, only neon lighting the character, ultra focus",
    "dark room with one magenta spotlight, deep shadows, mysterious atmosphere",
    "cyberpunk city background blurred, neon bokeh, character dominant in foreground",
    "abandoned neon-lit building, flickering lights, soft horror vibe, pink smoke",
    "underground parking garage, violet fog, hot magenta tubes, concrete shadows",
    "rooftop at night, blood red moon, violet fog, city lights far below",
    "dark nightclub hallway, magenta lasers, smoke haze, red velvet shadows",
    "rainy asphalt street, warm red taillights, pink reflections under boots",
    "black industrial tunnel, neon violet strips, fog around legs, cinematic depth",
]

AURA_VARIATIONS = [
    "deep magenta electric sparks tracing her silhouette from boots upward",
    "dark red energy smoke rising around her boots and legs",
    "hot pink glitch distortion at the edges of her body",
    "violet shadow tendrils curling around her arms and legs",
    "crimson plasma aura wrapping her lower body, controlled and dark",
    "dark ink bleeding effect at silhouette edges, magenta glow inside",
    "warm orange heat shimmer rising from ground near her boots",
    "pink neon particles orbiting around her body, subtle but alive",
    "magenta cyberpunk halo behind her head, dark queen icon energy",
    "red-violet smoke forming claw shapes behind her, cute but dangerous",
]

ART_STYLE_VARIATIONS = [
    "premium dark 2D anime, ultra sharp lineart, polished high contrast cel shading, phonk cover quality",
    "dark cyberpunk anime illustration, crisp clean lines, deep shadows, professional music cover energy",
    "underground trap anime art, bold silhouette, neon accents, viral thumbnail composition",
    "dark anime key visual style, cinematic lighting, clean anatomy, phonk trapstar aesthetic",
    "high quality dark anime poster art, moody atmosphere, dark queen protagonist energy",
    "music video anime cover art, sharp expressive face, detailed streetwear, dramatic neon",
    "cyberpunk manga cover style, glossy eyes, bold shape language, dark pop energy",
    "high CTR anime thumbnail art, beautiful character, strong silhouette, unforgettable vibe",
]

MOOD_VARIATIONS = [
    "personality mix: 45% cute, 35% dangerous, 20% insane",
    "personality mix: soft pretty face, villain eyes, chaotic aura",
    "personality mix: adorable but unstable, cyberpunk bad girl",
    "personality mix: cold trap queen, sweet smile, crazy stare",
    "personality mix: fofa maluca malvada, beautiful and unpredictable",
]


# ══════════════════════════════════════════════════════════════════════
# MAPEAMENTO DE GÊNERO
# ══════════════════════════════════════════════════════════════════════

GENRE_MAP = {
    "phonk":      "phonk",
    "trap":       "trap",
    "dark":       "dark",
    "darkpop":    "dark",
    "dark pop":   "dark",
    "electronic": "electronic",
    "edm":        "electronic",
    "dubstep":    "electronic",
    "funk":       "trap",
    "rock":       "dark",
    "metal":      "dark",
    "cinematic":  "dark",
    "lofi":       "dark",
    "indie":      "dark",
    "pop":        "default",
}

# PALETAS SEM AZUL/CYAN — V30
GENRE_PALETTES = {
    "phonk": [
        "palette: black background, hot magenta dominant rim light, deep violet shadows, crimson red accents",
        "palette: near-black background, neon pink primary, dark blood red secondary, violet smoke",
        "palette: dark background, magenta glow, warm red sparks, deep purple haze, no blue",
    ],
    "trap": [
        "palette: black background, hot pink neon dominant, violet rim light, gold jewelry warm accent",
        "palette: near-black background, crimson neon primary, magenta glow secondary, warm street reflection",
        "palette: dark background, violet dominant, magenta street glow, warm dark red accent",
    ],
    "electronic": [
        "palette: black background, magenta laser dominant, violet digital atmosphere, no cyan or blue",
        "palette: deep black background, hot pink primary neon, violet glow secondary, red spark accents",
        "palette: dark background, electric purple dominant, magenta accent, warm dark red hint",
    ],
    "dark": [
        "palette: near black background, dark blood red eyes and accents, deep violet aura, minimal glow",
        "palette: black background, gray-black deep shadows, crimson neon accent, magenta edge light",
        "palette: black background, silver hair contrast, magenta-pink glow, dark violet atmosphere",
    ],
    "default": [
        "palette: black background, violet and magenta dominant neon, warm dark red secondary, clean professional palette",
    ],
}


# ══════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════

def _compact(text: str, max_len: int = 3800) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace(" ,", ",").replace(",,", ",")
    return text[:max_len].rstrip(" ,")


def _clean_song_name(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(r"\[[^\]]*\]|\{[^\}]*\}|\([^\)]*\)", "", name)
    name = re.sub(r"[_\-]+", " ", name)
    return re.sub(r"\s+", " ", name).strip() or "dark trap phonk"


def _seed(style: str, filename: str, short_num: int) -> int:
    key = f"{style}|{filename}|{short_num}|darkmark_v30_perfect_cyberpunk_girls"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % (10**9)


def _rng(style: str, filename: str, short_num: int) -> random.Random:
    return random.Random(_seed(style, filename, short_num))


def _song_detail(song_name: str) -> str:
    clean = song_name.lower()
    if any(w in clean for w in ["bass", "808", "drop"]):
        return "visible bass shockwave rings on the wet ground around her feet"
    if any(w in clean for w in ["dark", "shadow", "ghost", "night", "madrugada"]):
        return "midnight shadow aura hugging her silhouette, dark red neon smoke at feet"
    if any(w in clean for w in ["rage", "fire", "burn"]):
        return "crimson neon flame aura outlining her body, aggressive energy"
    if any(w in clean for w in ["drive", "drift", "car", "speed"]):
        return "night drive warm red taillight streaks in background, wet asphalt reflection below"
    if any(w in clean for w in ["red", "blood", "demon", "devil"]):
        return "dark blood red energy aura wrapping her lower body and arms"
    if any(w in clean for w in ["queen", "king", "rule", "boss"]):
        return "dark throne energy, commanding full body stance, powerful presence"
    return "music energy as subtle violet neon aura outlining her full body"


# ══════════════════════════════════════════════════════════════════════
# PROMPT PRINCIPAL — V30
# ══════════════════════════════════════════════════════════════════════

def build_ai_prompt(
    style: str,
    filename: str,
    styles: list | None = None,
    short_num: int = 1,
) -> str:
    styles = styles or []
    mapped = GENRE_MAP.get((style or "default").lower().strip(), "default")
    rng    = _rng(mapped, filename, short_num)
    song_name = _clean_song_name(filename)

    hair        = rng.choice(HAIR_VARIATIONS)
    eyes        = rng.choice(EYE_VARIATIONS)
    expression  = rng.choice(EXPRESSION_VARIATIONS)
    pose        = rng.choice(POSE_VARIATIONS)
    outfit      = rng.choice(OUTFIT_VARIATIONS)
    scene       = rng.choice(SCENE_VARIATIONS)
    aura        = rng.choice(AURA_VARIATIONS)
    art         = rng.choice(ART_STYLE_VARIATIONS)
    mood_mix    = rng.choice(MOOD_VARIATIONS)
    palette     = rng.choice(GENRE_PALETTES.get(mapped, GENRE_PALETTES["default"]))
    detail      = _song_detail(song_name)

    genre_text = ", ".join([style] + [s for s in styles if s and s != style])

    prompt = (
        # ══ COMPOSIÇÃO VEM PRIMEIRO — isso é o que o modelo prioriza ══
        f"{BODY_LOCK}, "

        # PERSONAGEM
        f"{TRAPSTAR_DNA}, "

        # ESTILO VISUAL
        f"{STYLE_LOCK}, "

        # PALETA DE CORES (SEM AZUL)
        f"{PALETTE_HARD_LOCK}, "

        # ILUMINAÇÃO
        f"{LIGHTING_LOCK}, "

        # PELE
        f"{SKIN_LOCK}, "

        # COMPOSIÇÃO PARA ENGAJAMENTO
        f"{RETENTION_LOCK}, "

        # QUALIDADE
        f"{QUALITY_LOCK}, "

        # VARIAÇÕES DINÂMICAS — pose vem antes de hair/eyes
        f"pose: {pose}, "
        f"outfit: {outfit}, "
        f"scene: {scene}, "
        f"hair: {hair}, "
        f"eyes: {eyes}, "
        f"expression: {expression}, "
        f"mood: {mood_mix}, "
        f"aura: {aura}, "
        f"detail: {detail}, "

        # CONTEXTO MUSICAL
        f"{palette}, "
        f"genre mood: {genre_text}, "
        f"song mood: {song_name}, "
        f"{art}, "

        # REGRAS CRÍTICAS FINAIS
        "full body, wide shot, whole body visible from head to toe, "
        "NO BLUE NO CYAN NO TEAL, "
        "no text, no watermark, no logo"
    )

    return _compact(prompt, max_len=3800)


def build_prompt(style: str = "default", seed_variant: int = 0) -> tuple[str, str]:
    """Atalho para gerar prompt sem arquivo real."""
    fake_filename = f"{style}_variant_{seed_variant}.mp3"
    prompt = build_ai_prompt(
        style=style,
        filename=fake_filename,
        styles=[style],
        short_num=seed_variant + 1,
    )
    return prompt, NEGATIVE_PROMPT


# ══════════════════════════════════════════════════════════════════════
# SUFIXO DE REFORÇO — Adicionado na hora da geração
# ══════════════════════════════════════════════════════════════════════

GENERATION_SUFFIX = (
    ", full body, full length, wide shot, long shot, head to toe, "
    "whole body visible, legs visible, boots visible, complete figure, "
    "beautiful cyberpunk anime girl, cute but dangerous, slightly crazy eyes, "
    "dark trapstar streetwear, black outfit, chains, piercings, "
    "premium 2D anime art, sharp lineart, polished cel shading, "
    "dark cyberpunk phonk music cover aesthetic, "
    "magenta dominant, hot pink neon, deep violet shadows, crimson red accents, "
    "NO BLUE, NO CYAN, NO TEAL, warm neon palette only, "
    "dark background, no text, no logo, no watermark"
)


# ══════════════════════════════════════════════════════════════════════
# GERAÇÃO DE IMAGEM (REPLICATE)
# ══════════════════════════════════════════════════════════════════════

def generate_image(prompt: str, output_path: str | None = None) -> str | None:
    if not REPLICATE_API_TOKEN:
        logger.error("REPLICATE_API_TOKEN não configurado.")
        return None

    output_path = output_path or "temp/generated_background.png"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    full_prompt = _compact(prompt + GENERATION_SUFFIX)

    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }

    last_error: Optional[Exception] = None

    for model in REPLICATE_MODELS:
        for attempt in range(1, 4):
            try:
                logger.info(f"[Replicate] Tentativa {attempt}/3 — {model}")

                # Cada modelo tem nomes de parâmetros diferentes.
                # Mantém compatibilidade sem quebrar quando trocar de modelo.
                if "flux" in model:
                    model_input = {
                        **FLUX_PARAMS,
                        "prompt": full_prompt,
                        "negative_prompt": NEGATIVE_PROMPT,
                        "seed": random.randint(1000, 999_999),
                    }
                elif "animagine" in model:
                    model_input = {
                        "prompt": full_prompt,
                        "negative_prompt": NEGATIVE_PROMPT,
                        "width": FLUX_PARAMS["width"],
                        "height": FLUX_PARAMS["height"],
                        "num_inference_steps": FLUX_PARAMS["num_inference_steps"],
                        "guidance_scale": FLUX_PARAMS["guidance_scale"],
                        "seed": random.randint(1000, 999_999),
                    }
                else:
                    model_input = {
                        "prompt": full_prompt,
                        "negative_prompt": NEGATIVE_PROMPT,
                        "width": FLUX_PARAMS["width"],
                        "height": FLUX_PARAMS["height"],
                        "num_inference_steps": FLUX_PARAMS["num_inference_steps"],
                        "guidance_scale": FLUX_PARAMS["guidance_scale"],
                        "seed": random.randint(1000, 999_999),
                    }

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
                    data   = sr.json()
                    status = data.get("status")

                    if status == "succeeded":
                        output    = data.get("output")
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
) -> Optional[str]:
    prompt, _ = build_prompt(style=style, seed_variant=seed_variant)
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

    variant     = random.randint(0, 99)
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

    parser = argparse.ArgumentParser(
        description="AI Image Generator — DJ DARK MARK v30 Perfect Cyberpunk Girls Engine"
    )
    parser.add_argument("--style",       default="phonk",
                        help="Gênero musical (phonk, trap, electronic, dark, etc.)")
    parser.add_argument("--filename",    default="dark phonk.mp3",
                        help="Nome da música (usado para variar o prompt)")
    parser.add_argument("--short-num",   type=int, default=1,
                        help="Número do short (varia seed)")
    parser.add_argument("--output",      default="assets/background.png")
    parser.add_argument("--prompt-only", action="store_true",
                        help="Só imprime o prompt, não gera imagem")
    args = parser.parse_args()

    prompt = build_ai_prompt(
        style=args.style,
        filename=args.filename,
        styles=[args.style],
        short_num=args.short_num,
    )

    if args.prompt_only:
        print("=== PROMPT ===")
        print(prompt)
        print("\n=== NEGATIVE PROMPT ===")
        print(NEGATIVE_PROMPT)
        print("\n=== GENERATION SUFFIX ===")
        print(GENERATION_SUFFIX)
    else:
        path = generate_image(prompt, args.output)
        print(f"✅ Salvo: {path}" if path else "✗ Falha na geração.")
