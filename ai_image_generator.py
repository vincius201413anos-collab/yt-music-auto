"""
ai_image_generator.py — DJ DARK MARK v35 GLOWING EYES CUTE DARK ENERGY
=============================================================
CHANGELOG v35:
- ESTÉTICA REFORMULADA: baseada em 4 imagens de referência reais analisadas
- OLHOS BRILHANTES EXTREMOS: glow dominante, reflexo intenso, efeito chama/plasma nos íris
- ACESSÓRIOS DEMONÍACOS: chifres pequenos, orelhas de gato, correntes — como nas refs
- AURA ENERGY: chamas, correntes brilhantes, glitch, tentáculos de energia
- FUNDO PURO ESCURO: personagem iluminado só pelos próprios efeitos
- ESTILO "CUTE BUT DARK": fofo-perturbador, expressões intesas, olhos dominantes
- COMPOSIÇÃO: mais portrait/bust shot para capturar o glow extremo dos olhos
- BODY_LOCK ajustado: aceita portrait quando o estilo pede (como refs 1, 2, 3)
- PALETA: mantém magenta/violet/crimson, mas permite green como opção secundária (ref 1)
- CEL SHADING BRUTAL: contraste alto, linhas limpas, highlight glossy intenso
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
    # Animagine XL — melhor para anime dark cute, respeita bem composição
    "cjwbw/animagine-xl-3.1",
    # Fallback: Anything v5 — clássico anime, linhas limpas
    "lucataco/anything-v5-better-vae",
    # Último fallback: Flux-dev
    "black-forest-labs/flux-dev",
]

FLUX_PARAMS = {
    # 768x1024 — portrait quad, ideal para capturar olhos brilhantes e expressão
    "width":               int(os.getenv("FLUX_WIDTH",    "768")),
    "height":              int(os.getenv("FLUX_HEIGHT",   "1024")),
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
    "dark cute anime muse, glowing eyes dominant, cute but dangerous energy, "
    "dark phonk trap dark pop music cover art, "
    "magenta violet crimson palette, energy auras, chains, demon aesthetic, "
    "premium YouTube Shorts thumbnail universe"
)


# ══════════════════════════════════════════════════════════════════════
# CORE CHARACTER — V35 CUTE DARK GLOWING EYES
# ══════════════════════════════════════════════════════════════════════

TRAPSTAR_DNA = (
    "one adult anime woman, clearly adult, "
    "beautiful dark cute cyberpunk muse, cute but deeply unsettling, "
    "yandere dark energy, fofa maluca malvada supreme, "
    # OLHOS — elemento dominante como nas referências
    "EYES ARE THE FOCAL POINT: extremely large glowing anime eyes, "
    "intense neon glow radiating from irises, pupils with flame or plasma effect, "
    "neon light reflected in eyes, tears of neon glow, "
    "eyes full of unstable obsessive dark energy, hypnotic beautiful stare, "
    # ROSTO
    "beautiful detailed anime face, glossy lips, "
    "sharp cat eyeliner, dramatic eyelashes, soft cheeks with subtle blush, "
    "cute smile hiding something dark, grin with visible teeth, "
    # ACESSÓRIOS DEMONÍACOS — como nas referências
    "small cute demon horns OR fluffy cat ears, black choker collar with ring, "
    "chain necklace, ear piercings, fang teeth visible in smile, "
    # CORPO/ROUPA — sem nudez, mas sensual dark
    "dark cyberpunk outfit, cropped jacket OR dark corset top, "
    "chains draped over shoulders, glowing tattoos on visible skin, "
    # IDENTIDADE
    "alone, single character, no other people"
)

# ══════════════════════════════════════════════════════════════════════
# COMPOSIÇÃO — V35: PORTRAIT FIRST (como nas refs)
# ══════════════════════════════════════════════════════════════════════

COMPOSITION_LOCK = (
    "portrait or upper body composition, face dominant in frame, "
    "eyes occupying large portion of frame, "
    "character centered, dark background with energy effects surrounding, "
    "subject glowing from within, cinematic portrait framing, "
    "vertical 9:16 thumbnail composition, clean space for text overlays"
)

# ══════════════════════════════════════════════════════════════════════
# AURA ENERGY — ELEMENTO CENTRAL DAS REFS
# ══════════════════════════════════════════════════════════════════════

AURA_ENERGY_LOCK = (
    "dramatic energy effects surrounding character, "
    "glowing flames OR energy chains OR glitch distortion OR dark tendrils surrounding her, "
    "energy particles floating around her, "
    "neon sparks and embers in the air, "
    "aura visible from behind and sides creating halo effect, "
    "energy effect same color as eye glow, coherent color throughout, "
    "smoke and fog at edges blending into black background"
)

# ══════════════════════════════════════════════════════════════════════
# STYLE LOCK — DARK CUTE ANIME ESPECÍFICO
# ══════════════════════════════════════════════════════════════════════

STYLE_LOCK = (
    "premium 2D dark anime illustration, "
    "extremely clean sharp lineart, bold cel shading high contrast, "
    "glossy reflections on eyes and lips and hair, "
    "deep cinematic shadows on face, "
    "neon glow effects blended naturally into dark background, "
    "professional anime music cover art quality, "
    "dark cute aesthetic, not generic, not realistic, not 3D, "
    "inspired by dark anime character art, yandere character design"
)

# ══════════════════════════════════════════════════════════════════════
# PALETA — MAGENTA/VIOLET/CRIMSON + GREEN OPCIONAL
# ══════════════════════════════════════════════════════════════════════

PALETTE_HARD_LOCK = (
    "dominant dark palette with neon accents, "
    "near-black background, character illuminated only by her own energy glow, "
    "eye glow is the primary light source on her face, "
    "magenta OR violet OR crimson OR green neon glow coherent throughout, "
    "no mixed incompatible colors, single dominant neon color per image, "
    "hair glowing with same neon color as eyes, "
    "chains and accessories reflecting neon light, "
    "deep shadows, high contrast, dramatic dark mood"
)

# ══════════════════════════════════════════════════════════════════════
# LIGHTING — EYES AS LIGHT SOURCE
# ══════════════════════════════════════════════════════════════════════

LIGHTING_LOCK = (
    "eyes emit strong neon glow illuminating the face from within, "
    "eye glow creates soft light on cheeks and nose, "
    "rim lighting from energy aura behind her, "
    "face in dramatic shadow except where lit by own glow, "
    "no external light sources, character is the light source, "
    "deep blacks, strong contrast, glossy highlights on eyes and lips"
)

# ══════════════════════════════════════════════════════════════════════
# SKIN
# ══════════════════════════════════════════════════════════════════════

SKIN_LOCK = (
    "warm pale anime skin tone, slightly illuminated by neon glow, "
    "soft blush, clean smooth skin, "
    "neon light casting colored tint on skin matching eye color"
)

RETENTION_LOCK = (
    "scroll-stopping dark anime thumbnail, "
    "EYES are the first thing viewer sees, massive visual impact, "
    "instantly recognizable DJ Dark Mark visual identity, "
    "beautiful but unsettling, cute but dangerous, "
    "high CTR dark phonk trap thumbnail energy"
)

QUALITY_LOCK = (
    "masterpiece, best quality, ultra detailed anime illustration, "
    "beautiful detailed face, sharp expressive glowing eyes, "
    "clean anatomy, detailed outfit and accessories, "
    "professional dark anime art, high resolution, crisp lineart, "
    "polished shading, premium channel branding quality"
)

CONSISTENCY_LOCK = (
    "consistent channel branding, same visual universe, "
    "recognizable recurring dark cute anime muse, "
    "glowing eyes signature feature, dark outfit, neon energy identity, "
    "not random, not generic"
)


# ══════════════════════════════════════════════════════════════════════
# NEGATIVE PROMPT V35
# ══════════════════════════════════════════════════════════════════════

NEGATIVE_PROMPT = (
    # Cores erradas
    "washed out colors, desaturated, flat colors, muddy palette, "
    "ugly filter, bad color grading, cold washed filter, "
    # Anatomia ruim
    "ugly, bad anatomy, bad face, distorted face, asymmetrical eyes, "
    "bad hands, extra fingers, missing fingers, fused limbs, broken body, "
    "long neck, disfigured, mutated, melted face, uncanny valley, "
    "blurry, low quality, jpeg artifacts, noise, "
    # Estilo errado
    "photorealistic, realistic, photography, real person, 3D render, CGI, "
    "doll, plastic skin, western cartoon, simple cartoon, "
    # Idade
    "child, underage, loli, baby face, very young, "
    # Conteúdo explícito
    "nude, explicit nudity, genitalia, nipples, porn, erotic explicit, "
    # Múltiplos personagens
    "multiple people, crowd, two girls, group, duplicate character, "
    # Texto
    "text, words, logo, watermark, signature, letters, numbers, "
    # Composição ruim
    "boring pose, generic anime girl, plain background without effects, "
    "flat background, no energy effects, no glow, dull eyes, "
    "normal eyes without glow, realistic eyes, "
    # Overexposure
    "overexposed, too much glow, bloom overload, color chaos, "
    "rainbow colors, too many colors"
)


# ══════════════════════════════════════════════════════════════════════
# VARIAÇÕES — V35 CUTE DARK ENERGY
# ══════════════════════════════════════════════════════════════════════

HAIR_VARIATIONS = [
    "black hair with glowing magenta edges, neon trim highlights, messy cute style",
    "white platinum hair with magenta glow, soft flowing, black roots",
    "dark violet hair with pink neon streaks, glossy finish",
    "black wolfcut hair with crimson hot pink neon glow at tips",
    "deep blue-black hair glowing with purple light, sleek and sharp",
    "silver hair with violet rim glow, futuristic beautiful look",
    "dark purple ombre hair flowing with energy wisps",
    "black spiky hair with neon pink electricity crackling",
    "long dark hair billowing as if in wind made of energy",
    "white twin tails with glowing violet tips, edgy cute style",
    "short black hair with glowing red-crimson edges, sharp jaw-length cut",
    "dark hair with glowing strands weaving between energy effects",
]

EYE_VARIATIONS = [
    # OLHOS SÃO O ELEMENTO CENTRAL — descrições muito detalhadas
    "GLOWING MAGENTA EYES: massive anime eyes, iris filled with pink plasma flame, "
    "neon light bursting outward, pupils like dark voids surrounded by fire",
    
    "GLOWING VIOLET EYES: large glowing anime eyes, purple energy radiating from irises, "
    "sparks of violet light, deep hypnotic stare, glow illuminating face",
    
    "GLOWING CRIMSON RED EYES: intense red neon eyes, dark flame inside iris, "
    "dangerous stare, blood red glow on surrounding face",
    
    "GLOWING PINK NEON EYES: bright hot pink anime eyes, electric spark effects inside iris, "
    "tears of glowing pink light at corners, overwhelming cute but unhinged look",
    
    "GLOWING GREEN EYES: bright toxic green glowing anime eyes, emerald fire in iris, "
    "unsettling beautiful stare, green rim light on face",
    
    "GLOWING DEEP VIOLET EYES: large glowing purple-violet eyes, halo effect around iris, "
    "obsessive hypnotic stare, violet light casting on cheeks",
    
    "GLOWING DUAL-COLOR EYES: heterochromia, one eye magenta one eye violet, "
    "both glowing intensely, chaotic unstable beautiful look",
    
    "GLOWING WHITE-CORE EYES: eyes with bright white core surrounded by magenta ring, "
    "overwhelming light, like looking into neon stars",
    
    "GLOWING ROSE PINK EYES: soft but intense rose neon eyes, romantic but unstable, "
    "glossy wet look with inner glow, cute overwhelm",
    
    "GLOWING ELECTRIC PURPLE EYES: electric purple eyes with lightning cracks in iris, "
    "dangerous cute stare, purple light on nose and cheeks",
]

EXPRESSION_VARIATIONS = [
    # Como nas referências — expressões intensas mas cute
    "wide grin showing teeth, eyes glowing intensely, unhinged adorable smile",
    "calm soft smile but eyes absolutely burning with obsession, yandere peak",
    "shy cute smile with overwhelming eye contact, too intense to look away",
    "gleeful smile, eyes full of chaotic energy, adorable but dangerous",
    "expressionless face but eyes screaming unstable energy, eerie beautiful",
    "sweet gentle smile, eyes too wide, too bright, deeply unsettling",
    "small smirk, half-lidded glowing eyes, confident dark queen energy",
    "open mouth smile showing fang, eyes bright with excitement and madness",
    "melancholic expression, glowing eyes downcast but burning, sad villain energy",
    "playful tongue-out, one eye winking glowing, chaotic cute energy",
    "slightly open mouth, dazed beautiful expression, glowing eyes unfocused",
    "intense direct stare, lips slightly parted, eyes consuming the viewer",
]

DEMON_ACCESSORY_VARIATIONS = [
    # Como nas referências
    "small cute curved black demon horns growing from forehead",
    "fluffy black cat ears with inner neon glow matching eye color",
    "small twisted demon horns with glowing cracks in same color as eyes",
    "wolf ears dark and fluffy, alert and expressive",
    "elegant curved horns with neon markings etched into them",
    "tiny imp horns barely visible through dark hair, subtle cute detail",
    "cat ears with glowing tips, matching energy color of her aura",
    "broken halo hovering crookedly above her head, dark angel aesthetic",
    "ram-style curved horns, dark and polished, intimidating but cute",
    "no horns, just strong dark energy halo behind head like dark saint",
]

AURA_VARIATIONS = [
    # ENERGIA VISÍVEL — como nas referências
    "dark neon flames surrounding her entire silhouette, same color as eye glow, "
    "fire licking upward behind head and shoulders, embers floating",
    
    "glowing chains wrapping around her body and floating in air beside her, "
    "chains pulse with neon light, links detailed and sharp",
    
    "dark energy tendrils curling outward from her silhouette, "
    "organic flowing shapes, same neon color as eyes, alive and moving",
    
    "glitch distortion surrounding edges of her form, "
    "digital corruption aesthetic, neon pixels and scan lines at border",
    
    "dark petals and thorns made of neon energy floating around her, "
    "gothic dark romance energy, petals glowing same color as eyes",
    
    "electrical arc chains floating beside her, neon lightning coiling, "
    "energy cracking between floating chain links",
    
    "dark smoke pouring upward from around her, lit from within by neon glow, "
    "fog and embers surrounding silhouette",
    
    "sharp crystal shards of energy radiating outward behind her, "
    "dark gemstone aesthetic, shards glowing with neon color",
    
    "dark water ripple energy emanating outward from her, "
    "neon-lit concentric rings distorting space around her",
    
    "floating dark feathers surrounding her, each feather edge glowing neon, "
    "fallen angel aesthetic, feathers drifting slowly upward",
]

SCENE_VARIATIONS = [
    # Fundo extremamente escuro — personagem é a única luz (como nas refs)
    "pure absolute black background, character is the only light source, "
    "neon glow from eyes and aura painting the darkness",
    
    "near-black void background with faint smoke and particles, "
    "depth created only by layers of dark fog",
    
    "black background with subtle dark texture, "
    "energy effects creating all visible color and light",
    
    "deep dark environment barely visible, ruins or alley, "
    "character's glow illuminating immediate surroundings only",
    
    "dark cinematic background, blurred and abstract, "
    "neon smears of background light, bokeh effect, character sharp in foreground",
    
    "dark void with floating debris lit by character's glow, "
    "particles of dust and embers in foreground",
]

ART_STYLE_VARIATIONS = [
    "ultra detailed dark anime illustration, bold clean lineart, "
    "high contrast cel shading, glossy eye highlights dominant, "
    "professional dark character art, music cover quality",
    
    "premium dark anime character design, sharp expressive features, "
    "detailed neon glow effects, clean polished finish, "
    "yandere character art aesthetic",
    
    "high quality dark cute anime art, detailed eyes are focal point, "
    "clean anatomy, bold color contrast, viral thumbnail composition",
    
    "dark anime key visual, cinematic portrait lighting, "
    "detailed glow effects, sharp lineart, professional music cover",
    
    "dark pop anime cover art, beautiful character with intense eyes, "
    "dramatic energy aura, premium phonk trap visual identity",
]

MOOD_VARIATIONS = [
    "fofa maluca malvada supreme — sweet face, broken mind, beautiful energy",
    "cute exterior hiding chaotic obsessive soul, dark romance",
    "adorable but emotionally dangerous, beautiful and unstable",
    "cold dark queen with burning obsessive eyes, terrifying cute",
    "sweet innocent smile, villain eyes, yandere at max level",
    "calm serene face over boiling dark energy within",
    "loveable but unpredictable, cute but haunted",
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

GENRE_PALETTES = {
    "phonk": [
        "dominant color: hot magenta — eye glow magenta, aura magenta, "
        "hair neon pink or black, near-black background",
        "dominant color: crimson red — eye glow red, aura deep crimson flame, "
        "hair dark with red highlights, absolute black background",
        "dominant color: violet — eye glow deep violet, aura violet energy, "
        "hair black-purple, background near-black void",
    ],
    "trap": [
        "dominant color: hot pink — neon pink eyes, pink energy chains, "
        "black outfit with pink glow, dark background",
        "dominant color: magenta violet — violet eyes glowing, magenta rim, "
        "dark streetwear, near-black cyberpunk void",
        "dominant color: electric pink — bright pink neon eyes, pink sparks, "
        "dramatic dark environment",
    ],
    "electronic": [
        "dominant color: electric violet — violet glowing eyes, purple plasma aura, "
        "dark background with violet particles",
        "dominant color: magenta — hot magenta eyes and aura, electric sparks, "
        "dark digital void background",
        "dominant color: deep purple — purple energy field, dark atmosphere, "
        "character glowing purple from within",
    ],
    "dark": [
        "dominant color: deep crimson — blood red glowing eyes, dark flame aura, "
        "absolute black background, minimal glow",
        "dominant color: dark violet — muted violet eyes glowing, shadow tendrils, "
        "deep black atmosphere",
        "dominant color: cold white — white glowing eyes with violet rim, "
        "dark ghost energy, near-black void",
    ],
    "default": [
        "dominant color: magenta violet — magenta eyes, violet aura energy, "
        "dark background, professional palette",
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
    key = f"{style}|{filename}|{short_num}|darkmark_v35_glowing_eyes_cute_dark"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % (10**9)


def _rng(style: str, filename: str, short_num: int) -> random.Random:
    return random.Random(_seed(style, filename, short_num))


def _song_detail(song_name: str) -> str:
    clean = song_name.lower()
    if any(w in clean for w in ["bass", "808", "drop"]):
        return "shockwave rings of energy radiating outward from her"
    if any(w in clean for w in ["dark", "shadow", "ghost", "night", "madrugada"]):
        return "shadow tendrils wrapping around her, dark midnight energy aura"
    if any(w in clean for w in ["rage", "fire", "burn"]):
        return "flames surrounding her, aggressive fire energy aura"
    if any(w in clean for w in ["drive", "drift", "car", "speed"]):
        return "speed lines and energy streaks surrounding her form"
    if any(w in clean for w in ["red", "blood", "demon", "devil"]):
        return "dark blood red energy chains floating around her"
    if any(w in clean for w in ["queen", "king", "rule", "boss"]):
        return "dark crown energy halo, commanding powerful aura"
    return "subtle neon energy particles orbiting around her silhouette"


# ══════════════════════════════════════════════════════════════════════
# PROMPT PRINCIPAL — V35
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
    demon_acc   = rng.choice(DEMON_ACCESSORY_VARIATIONS)
    aura        = rng.choice(AURA_VARIATIONS)
    scene       = rng.choice(SCENE_VARIATIONS)
    art         = rng.choice(ART_STYLE_VARIATIONS)
    mood_mix    = rng.choice(MOOD_VARIATIONS)
    palette     = rng.choice(GENRE_PALETTES.get(mapped, GENRE_PALETTES["default"]))
    detail      = _song_detail(song_name)

    genre_text = ", ".join([style] + [s for s in styles if s and s != style])

    prompt = (
        # ══ OLHOS VÊM PRIMEIRO — elementos dominantes nas refs ══
        f"{eyes}, "

        # EXPRESSÃO IMEDIATA
        f"expression: {expression}, "

        # PERSONAGEM COMPLETO
        f"{TRAPSTAR_DNA}, "

        # ACESSÓRIO DEMONÍACO
        f"accessories: {demon_acc}, "

        # AURA DE ENERGIA
        f"{AURA_ENERGY_LOCK}, "
        f"specific aura: {aura}, "

        # COMPOSIÇÃO
        f"{COMPOSITION_LOCK}, "

        # ESTILO VISUAL
        f"{STYLE_LOCK}, "

        # PALETA
        f"{PALETTE_HARD_LOCK}, "
        f"{palette}, "

        # ILUMINAÇÃO
        f"{LIGHTING_LOCK}, "

        # PELE
        f"{SKIN_LOCK}, "

        # ENGAJAMENTO
        f"{RETENTION_LOCK}, "

        # QUALIDADE
        f"{QUALITY_LOCK}, "
        f"{CONSISTENCY_LOCK}, "

        # VARIAÇÕES DINÂMICAS
        f"hair: {hair}, "
        f"scene: {scene}, "
        f"mood: {mood_mix}, "
        f"song detail: {detail}, "

        # CONTEXTO MUSICAL
        f"art style: {art}, "
        f"genre mood: {genre_text}, "
        f"song mood: {song_name}, "

        # REFORÇO FINAL
        "glowing eyes dominant, dark background, energy aura visible, "
        "cute but dangerous, fofa maluca malvada, "
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
# SUFIXO DE REFORÇO V35
# ══════════════════════════════════════════════════════════════════════

GENERATION_SUFFIX = (
    ", "
    # OLHOS — repetição intencional para reforço máximo
    "glowing anime eyes, massive glowing iris, neon light emanating from eyes, "
    "eyes illuminating the face, beautiful intense glowing stare, "
    # AURA
    "energy aura surrounding character, neon glow effects, "
    "dark background contrasting with neon, "
    # PERSONAGEM
    "beautiful adult dark cute anime girl, yandere energy, "
    "cute but dangerous, fofa maluca malvada, "
    "demon horns OR cat ears, chains, dark cyberpunk outfit, "
    # ESTILO
    "premium 2D anime art, ultra sharp lineart, bold cel shading, "
    "high contrast dark illustration, professional music cover quality, "
    # PALETA
    "vibrant neon single dominant color, dark background, deep shadows, "
    # PROIBIÇÕES
    "no text, no logo, no watermark, no extra characters"
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
        description="AI Image Generator — DJ DARK MARK v35 Glowing Eyes Cute Dark Energy"
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
