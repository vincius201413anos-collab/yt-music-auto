"""
ai_image_generator.py — DJ DARK MARK v34 CINEMATIC SENSUAL CYBERPUNK
=============================================================
CHANGELOG v34:
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
    "DJ Dark Mark official cinematic cyberpunk visual identity, "
    "adult anime cyberpunk muse, dark phonk trap dark pop music cover art, "
    "magenta violet crimson palette, glowing eyes, sensual streetwear, "
    "premium YouTube Shorts thumbnail universe"
)


# ══════════════════════════════════════════════════════════════════════
# LOCKS PRINCIPAIS — V30 TRAPSTAR CYBERPUNK + ANTI-BLUE NUCLEAR
# ══════════════════════════════════════════════════════════════════════

TRAPSTAR_DNA = (
    "one adult anime woman, clearly adult, "
    "beautiful cyberpunk trapstar muse, sensual but stylish, not explicit, "
    "cute but dangerous, yandere cyberpunk personality, soft face with unstable obsessive eyes, "
    "fofa maluca malvada vibe, sweet smile hiding chaos, "
    "extremely attractive face, glossy lips, sharp cat eyeliner, heavy mascara, "
    "glowing eyes, hypnotic stare, confident dark trap queen energy, "
    "curvy feminine body, rounded waist, attractive proportions, visible waistline, "
    "subtle body definition, soft stomach shading, stylish tattoos visible, "
    "black/pink/violet identity, memorable silhouette, "
    "wearing sensual cyberpunk streetwear: open cropped jacket OR oversized open hoodie OR techwear straps, "
    "black bra top OR strappy crop top OR leather top visible, "
    "chain necklace, black choker, rings, piercings, chain belt, "
    "dark mini skirt OR dark cargo pants OR techwear shorts, thigh-high boots OR platform combat boots, "
    "glowing tattoos, waist tattoos, arm tattoos, thigh tattoo details, "
    "alone, no other characters, no crowds"
)

# ══════════════════════════════════════════════════════════════════════
# BODY LOCK V4 — FRASES CURTAS + ORDEM PRIORITÁRIA
# ══════════════════════════════════════════════════════════════════════

BODY_LOCK = (
    "full body, full length character, wide shot, long shot, head to toe visible, "
    "whole body visible, legs visible, boots visible, feet in frame, "
    "complete outfit visible, full silhouette visible, "
    "face beautiful but not close-up, body dominant composition, "
    "visible waist, stylish sensual pose, vertical poster framing, centered character, 9:16 aspect ratio"
)

# ══════════════════════════════════════════════════════════════════════
# STYLE LOCK — CYBERPUNK TRAPSTAR ESPECÍFICO
# ══════════════════════════════════════════════════════════════════════

STYLE_LOCK = (
    "premium 2D anime illustration, cinematic cyberpunk anime key visual, "
    "sharp clean lineart, polished cel shading, glossy neon highlights, "
    "deep cinematic shadows, high contrast silhouette, dark phonk cover art aesthetic, "
    "dark pop music visualizer background, professional anime music thumbnail, "
    "clean color grading, vibrant colors, not generic, not realistic, not 3D, not photo"
)

# ══════════════════════════════════════════════════════════════════════
# PALETA — ANTI-AZUL NUCLEAR V30
# ══════════════════════════════════════════════════════════════════════

PALETTE_HARD_LOCK = (
    "clean cinematic color grading, vibrant colors, no ugly filter, "
    "magenta dominant color palette, hot pink neon accents, deep violet shadows, "
    "dark purple atmosphere, crimson red highlights, warm orange secondary rim light, "
    "near-black background, dark red and violet mood, "
    "hair may be neon pink, violet, crimson, silver, black with colorful highlights, "
    "eyes must glow pink, magenta, violet, or red, "
    "no blue, no cyan, no teal, no turquoise, no aqua, no cobalt, no azure, "
    "avoid cold blue lighting, avoid icy colors, avoid washed color filter, "
    "warm neon palette only, magenta violet red only"
)

# ══════════════════════════════════════════════════════════════════════
# LIGHTING — QUENTE E DIRECIONAL
# ══════════════════════════════════════════════════════════════════════

LIGHTING_LOCK = (
    "cinematic neon lighting, hot magenta rim light, deep violet backlight, "
    "warm red-orange key light from one side, clean natural anime skin tone, "
    "soft highlight on waist and stomach, subtle body contour lighting, "
    "eyes glowing with neon reflection, glossy lips highlight, "
    "dark background, subject clearly separated from background, "
    "soft smoke haze, wet reflective highlights, high contrast, "
    "no blue light, no cyan light, no cold color filter, no ugly blue overlay"
)

# ══════════════════════════════════════════════════════════════════════
# SKIN — TOM NATURAL ANIME
# ══════════════════════════════════════════════════════════════════════

SKIN_LOCK = (
    "natural warm anime skin tone, warm pale skin, light beige or warm ivory, "
    "soft blush on cheeks, clean skin shading, no color filter on skin, "
    "no blue skin, no cyan skin, no cold skin tone, not blue-tinted, not gray skin"
)

RETENTION_LOCK = (
    "scroll-stopping viral YouTube Shorts thumbnail, strong visual impact in under one second, "
    "recognizable DJ Dark Mark visual identity, character instantly memorable, "
    "beautiful face, glowing eyes, sensual cyberpunk silhouette, "
    "full body centered, clean space near bottom for DJ logo and waveform overlay, "
    "dark anime music video energy, high CTR phonk trap dark pop thumbnail, "
    "not cluttered, readable silhouette even on phone screen"
)

QUALITY_LOCK = (
    "masterpiece, best quality, ultra detailed anime illustration, "
    "clean anatomy, beautiful face, sharp expressive glowing eyes, detailed outfit, "
    "professional dark cyberpunk anime poster, high resolution, crisp lineart, polished shading, "
    "consistent character proportions, premium channel branding quality, cinematic composition"
)


CONSISTENCY_LOCK = (
    "consistent channel branding, same visual universe, "
    "recognizable recurring cyberpunk anime muse, "
    "black outfit, magenta neon identity, deep violet shadows, crimson accents, "
    "clean readable silhouette, premium YouTube channel standard, "
    "not random, not generic, not cluttered"
)

CINEMATIC_COLOR_LOCK = (
    "clean cinematic color grading, no ugly blue filter, no washed filter, "
    "skin remains warm natural anime skin tone, "
    "neon colors are magenta pink violet crimson only, "
    "eyes and hair are colorful and glowing, "
    "high contrast but not overexposed"
)



# ══════════════════════════════════════════════════════════════════════
# NEGATIVE PROMPT V30 — ANTI-AZUL MÁXIMO + COMPOSIÇÃO FORÇADA
# ══════════════════════════════════════════════════════════════════════

NEGATIVE_PROMPT = (
    "blue, cyan, teal, turquoise, aqua, cobalt, azure, cerulean, indigo, navy blue, sky blue, "
    "blue background, cyan background, teal background, blue lighting, cyan lighting, "
    "blue neon, cyan neon, teal neon, blue glow, cyan glow, blue filter, cyan filter, "
    "cold color grading, cold color palette, icy tones, washed color filter, ugly filter, "
    "blue skin, cyan skin, blue-tinted skin, cold skin, gray skin, dead skin, "
    "green, yellow, muddy colors, washed out colors, desaturated, flat colors, "
    "ugly, bad anatomy, bad face, distorted face, asymmetrical eyes, lazy eye, "
    "bad hands, extra fingers, missing fingers, fused fingers, fused limbs, broken body, "
    "long neck, disfigured, mutated, melted face, uncanny valley, blurry, low quality, jpeg artifacts, noise, "
    "photorealistic, realistic, photography, real person, 3D render, CGI, doll, plastic skin, "
    "child, underage, loli, chibi, schoolgirl, baby face, teenager, young girl, "
    "nude, explicit nudity, genitalia, nipples, porn, erotic explicit, transparent clothes, "
    "multiple people, crowd, two girls, group, duplicate character, "
    "text, words, logo, watermark, signature, letters, numbers, username, "
    "portrait, headshot, bust shot, close-up, extreme close-up, face only, face filling frame, "
    "upper body only, waist up, shoulders up, cropped legs, cropped body, missing legs, missing feet, "
    "missing lower body, bad composition, boring pose, generic anime girl, plain outfit, "
    "too much clothing, winter coat covering body, oversized outfit hiding waist, "
    "overexposed, too much glow, bloom overload, color chaos"
)


# ══════════════════════════════════════════════════════════════════════
# VARIAÇÕES — V30 TRAPSTAR CYBERPUNK, SEM AZUL
# ══════════════════════════════════════════════════════════════════════

HAIR_VARIATIONS = [
    "neon pink hair, vibrant and glowing, glossy cyberpunk strands",
    "deep violet hair, glossy, cinematic cyberpunk shine",
    "black hair with neon pink highlights, glowing strands, sharp anime bangs",
    "dark purple hair with hot pink neon reflections, smooth gradient",
    "black hair with crimson red highlights, glossy finish, magenta rim light",
    "white platinum hair with magenta glow, soft and beautiful, black roots",
    "silver hair with magenta rim light, futuristic seductive look",
    "black hair with glowing purple streaks, cyberpunk aesthetic",
    "deep red hair with neon glow, seductive dark pop vibe",
    "dark violet ombre hair, smooth gradient, high detail",
    "black wolfcut hair with pink streaks, punk cyberpunk style",
    "long black wavy hair flowing in neon wind, hot magenta edge light",
]

EYE_VARIATIONS = [
    "bright glowing pink eyes, extremely detailed, strong neon reflections",
    "intense magenta eyes with powerful glow, hypnotic stare",
    "violet glowing eyes with reflections and spark effects",
    "deep red glowing eyes, dark seductive villain vibe",
    "pink neon eyes with light bloom, ultra anime style",
    "glowing purple eyes with soft light aura",
    "magenta eyes with inner glow and sharp highlights",
    "neon pink eyes with electric spark details inside iris",
    "crimson pink eyes, calm but terrifying, direct eye contact",
    "wide glowing violet eyes, cute but unstable yandere energy",
]

EXPRESSION_VARIATIONS = [
    "cute smile but eyes completely insane, unsettling contrast",
    "adorable expression with slightly broken emotional look",
    "soft smile with obsessive stare, uncomfortable but attractive",
    "playful cute smile hiding something dark",
    "emotionless face with slight creepy smile forming",
    "shy smile but intense eye contact, yandere vibe",
    "gentle expression but mentally unstable aura",
    "sweet face with subtle madness behind the eyes",
    "small innocent smile but eyes screaming obsession",
    "calm relaxed face with disturbing undertone",
    "seductive but unstable expression, confident gaze, slight smirk",
    "confident trap queen smirk, beautiful and dangerous",
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
    "full body holding chain loosely, dark aura around boots, head to toe visible",
]

OUTFIT_VARIATIONS = [
    "black cyberpunk bra top, open cropped jacket, exposed waist, glowing tattoos, thigh-high boots",
    "cropped oversized hoodie open, black bra visible, cyberpunk chains, exposed midriff, platform boots",
    "dark strappy top, minimal fabric, techwear belts, visible waist, thigh-high boots",
    "black bikini-style top with techwear straps, open jacket, cargo pants, chains",
    "cropped neon bra top, oversized open hoodie, exposed waist, cyberpunk accessories",
    "tight black top with stylish cutouts, chain belt, thigh-high boots, glowing tattoos",
    "minimal cyberpunk outfit, bra top, dark shorts, exposed legs, platform boots",
    "dark leather bra top, techwear mini skirt, exposed stomach, chains and piercings",
    "black harness top, exposed torso, cyberpunk straps, high boots, arm tattoos",
    "cropped jacket open, bra visible, waist exposed, tattoos glowing, confident pose",
    "dark clubwear outfit, minimal top, strong silhouette, sexy cyberpunk vibe",
    "black techwear crop top, low-rise cargo pants, rounded waist visible, neon tattoo lines",
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
    "rainy asphalt street, warm red taillights, pink reflections under boots",
    "dark cyberpunk club hallway, magenta lasers, red velvet shadows, smoke haze",
]

AURA_VARIATIONS = [
    "deep magenta electric sparks tracing her silhouette from waist and boots upward",
    "dark red energy smoke rising around her boots and legs",
    "hot pink glitch distortion at the edges of her body",
    "violet shadow tendrils curling around her arms and legs",
    "crimson plasma aura wrapping her lower body, controlled and dark",
    "dark ink bleeding effect at silhouette edges, magenta glow inside",
    "warm orange heat shimmer rising from ground near her boots",
    "pink neon particles orbiting around her body, subtle but alive",
    "magenta cyberpunk halo behind her head, dark queen icon energy",
    "red-violet smoke forming claw shapes behind her, cute but dangerous",
    "glowing tattoo lines pulsing softly on waist and arms",
]

ART_STYLE_VARIATIONS = [
    "premium dark 2D anime, ultra sharp lineart, polished high contrast cel shading, cinematic cover quality",
    "dark cyberpunk anime illustration, crisp clean lines, deep shadows, professional music cover energy",
    "underground trap anime art, bold silhouette, neon accents, viral thumbnail composition",
    "dark anime key visual style, cinematic lighting, clean anatomy, phonk trapstar aesthetic",
    "high quality dark anime poster art, moody atmosphere, dark queen protagonist energy",
    "music video anime cover art, sharp expressive face, detailed sensual streetwear, dramatic neon",
    "cyberpunk manga cover style, glossy eyes, bold shape language, dark pop energy",
    "high CTR anime thumbnail art, beautiful character, strong silhouette, unforgettable vibe",
]

MOOD_VARIATIONS = [
    "cinematic yandere cyberpunk mood, cute but unstable, beautiful but dangerous",
    "soft pretty face, villain eyes, obsessive aura, sensual confidence",
    "adorable but emotionally dangerous, cyberpunk bad girl, hypnotic stare",
    "cold trap queen, sweet smile, crazy stare, dark romance energy",
    "fofa maluca malvada, beautiful and unpredictable, glowing eyes",
    "calm exterior, chaotic obsessive eyes, dark cyberpunk muse",
    "innocent smile, dangerous mind, neon villain energy",
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
    key = f"{style}|{filename}|{short_num}|darkmark_v34_cinematic_sensual"
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

        # CONSISTÊNCIA DE CANAL
        f"{CONSISTENCY_LOCK}, "
        f"{CINEMATIC_COLOR_LOCK}, "

        # VARIAÇÕES DINÂMICAS — pose vem antes de hair/eyes
        f"pose: {pose}, "
        f"outfit: {outfit}, "
        f"body detail: visible waist, rounded feminine waist, stylish sensual cyberpunk silhouette, glowing tattoos, "
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
    "whole body visible, legs visible, boots visible, complete figure, visible waist, "
    "beautiful adult cyberpunk anime girl, sensual but stylish, yandere vibe, cute but dangerous, "
    "glowing colorful eyes, colorful neon hair, black outfit, less clothing but not nude, "
    "bra top or crop top visible, exposed waist, tattoos, chains, piercings, "
    "premium 2D anime art, sharp lineart, polished cel shading, clean cinematic color grading, "
    "dark cyberpunk phonk music cover aesthetic, "
    "magenta dominant, hot pink neon, deep violet shadows, crimson red accents, vibrant colors, "
    "NO BLUE, NO CYAN, NO TEAL, no ugly filter, no cold color grading, "
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
        description="AI Image Generator — DJ DARK MARK v34 Cinematic Sensual Cyberpunk Engine"
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
