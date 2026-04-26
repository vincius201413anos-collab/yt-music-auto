"""
ai_image_generator.py — DJ DARK MARK v27 FULL BODY HARD FIX
=============================================================
CHANGELOG v27:
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
# LOCKS PRINCIPAIS — V28 TRAPSTAR CYBERPUNK + ANTI-BLUE NUCLEAR
# ══════════════════════════════════════════════════════════════════════

TRAPSTAR_DNA = (
    # IDENTIDADE — trapstar real, não anime genérico
    "one adult anime woman, "
    "dark trapstar queen, underground phonk cyberpunk aesthetic, "
    "extremely beautiful face, mature and seductive, glossy lips, sharp cat eyeliner, "
    "heavy mascara, intense gaze, dangerous energy, "
    "trap queen vibe — confident, cold, powerful, slightly unhinged, "
    # ROUPA — real trapstar pieces
    "wearing: oversized black hoodie OR dark leather jacket OR black techwear vest, "
    "chunky gold or silver chain necklace, black choker, "
    "fingerless gloves OR arm sleeves, dark cargo pants OR black shorts with thigh-high boots, "
    "chunky platform boots OR combat boots, "
    "subtle neck tattoo OR arm tattoo visible, "
    "nose ring OR lip ring OR eyebrow piercing, "
    "alone, no other characters, no crowds"
)

# ══════════════════════════════════════════════════════════════════════
# BODY LOCK V4 — FRASES CURTAS + ORDEM PRIORITÁRIA
# ══════════════════════════════════════════════════════════════════════

BODY_LOCK = (
    "full body, "
    "full length, "
    "wide shot, "
    "long shot, "
    "head to toe, "
    "whole body visible, "
    "legs visible, "
    "boots visible, "
    "feet in frame, "
    "complete figure, "
    "outfit fully visible, "
    "face small in frame, "
    "body dominant composition, "
    "vertical poster framing, "
    "9:16 aspect ratio"
)

# ══════════════════════════════════════════════════════════════════════
# STYLE LOCK — CYBERPUNK TRAPSTAR ESPECÍFICO
# ══════════════════════════════════════════════════════════════════════

STYLE_LOCK = (
    # estilo de arte
    "2D anime illustration, "
    "dark cyberpunk anime art style, "
    "sharp clean lineart, "
    "polished cel shading, "
    "high contrast shadows, "
    "cinematic dark mood, "
    # referências visuais que os modelos conhecem bem
    "inspired by dark phonk music cover art, "
    "trap queen anime poster, "
    "underground cyberpunk streetwear aesthetic, "
    "similar to dark anime music video thumbnail"
)

# ══════════════════════════════════════════════════════════════════════
# PALETA — ANTI-AZUL NUCLEAR V28
# ══════════════════════════════════════════════════════════════════════

PALETTE_HARD_LOCK = (
    # O QUE DEVE EXISTIR — dito de forma positiva primeiro
    "warm color palette, "
    "magenta dominant, "
    "hot pink neon accents, "
    "deep violet shadows, "
    "crimson red highlights, "
    "warm orange secondary light, "
    "near-black background, "
    "dark red atmosphere, "
    # O QUE É PROIBIDO — repetido várias vezes de formas diferentes
    "no blue, no cyan, no teal, no turquoise, no aqua, "
    "no cold colors, no cool tones, no icy colors, "
    "not blue, not cyan, not teal, "
    "avoid blue, avoid cyan, avoid teal, "
    "warm tones only, hot colors only"
)

# ══════════════════════════════════════════════════════════════════════
# LIGHTING — QUENTE E DIRECIONAL
# ══════════════════════════════════════════════════════════════════════

LIGHTING_LOCK = (
    "dramatic cinematic lighting, "
    "warm orange or red key light from one side, "
    "hot magenta or violet rim light from opposite side, "
    "strong directional shadows, "
    "face beautifully lit, "
    "eyes glowing with neon reflection, "
    "dark background, subject brighter than background, "
    "no blue light, no cold light, no white overexposure"
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
    "scroll-stopping viral thumbnail, "
    "strong visual impact in under 1 second, "
    "character centered, full body dominant, "
    "space at bottom for DJ logo and waveform overlay, "
    "high CTR dark anime thumbnail energy"
)

QUALITY_LOCK = (
    "masterpiece, best quality, "
    "ultra detailed anime illustration, "
    "sharp lineart, clean anatomy, "
    "professional dark phonk anime poster"
)


# ══════════════════════════════════════════════════════════════════════
# NEGATIVE PROMPT V28 — ANTI-AZUL MÁXIMO + COMPOSIÇÃO FORÇADA
# ══════════════════════════════════════════════════════════════════════

NEGATIVE_PROMPT = (
    # ═══ AZUL/CYAN — LISTADO O MÁXIMO POSSÍVEL ═══
    "blue, cyan, teal, turquoise, aqua, cobalt, azure, cerulean, indigo, "
    "blue background, cyan background, teal background, "
    "blue hair, cyan hair, teal hair, blue highlights, cyan highlights, "
    "blue eyes, cyan eyes, teal eyes, blue iris, "
    "blue skin, cyan skin, teal skin, blue-tinted skin, cold skin, "
    "blue light, cyan light, teal light, cold light, ice light, "
    "blue neon, cyan neon, teal neon, blue glow, cyan glow, teal glow, "
    "blue aura, cyan aura, blue rim light, cyan rim light, teal rim light, "
    "blue atmosphere, cyan atmosphere, cold atmosphere, cold color palette, "
    "blue tones, cyan tones, cool tones, cold tones, icy tones, "
    "electric blue, ice blue, navy blue, sky blue, "

    # ═══ OUTRAS CORES INDESEJADAS ═══
    "green, green tones, green skin, "
    "yellow, yellow tones, "
    "washed out colors, desaturated, flat colors, "

    # ═══ QUALIDADE ANATÔMICA ═══
    "ugly, bad anatomy, bad face, distorted face, asymmetrical eyes, lazy eye, "
    "bad hands, extra fingers, missing fingers, fused limbs, long neck, "
    "melted face, uncanny valley, blurry, low quality, noise, jpeg artifacts, "

    # ═══ REALISMO ═══
    "photorealistic, realistic, photography, real person, 3D render, CGI, "
    "hyperrealistic, plastic skin, lifeless eyes, "

    # ═══ PERSONAGENS PROIBIDOS ═══
    "child, underage, loli, chibi, schoolgirl, baby face, "

    # ═══ NSFW ═══
    "nude, explicit nudity, genitalia, "

    # ═══ MÚLTIPLOS PERSONAGENS ═══
    "multiple people, crowd, two girls, group, duplicate, "

    # ═══ TEXTO ═══
    "text, words, logo, watermark, signature, letters, numbers, "

    # ═══ COMPOSIÇÃO ERRADA — CLOSE/ROSTO ═══
    "portrait, headshot, bust shot, close-up, extreme close-up, "
    "face shot, face focus, head focus, face filling frame, "
    "face dominant, zoomed face, face only, eyes only, "
    "upper body only, waist up, shoulders up, "
    "cropped legs, cropped body, missing legs, missing feet, missing lower body, "
    "half body, portrait framing, "

    # ═══ GLOW EXCESSIVO ═══
    "overexposed, too much glow, bloom overload, color chaos"
)


# ══════════════════════════════════════════════════════════════════════
# VARIAÇÕES — V28 TRAPSTAR CYBERPUNK, SEM AZUL
# ══════════════════════════════════════════════════════════════════════

HAIR_VARIATIONS = [
    # PRETO / DARK — principal
    "long straight black hair, glossy, lit by magenta rim light",
    "black hair with dark crimson streaks, edgy and bold",
    "black hair pulled into messy high bun, strands falling loose, gothic",
    "short sharp black bob, undercut sides, dark streetwear energy",
    "black hair under oversized dark hood, neon pink strands visible at edges",
    "black wavy hair with subtle dark red highlights, flowing",
    "black twintails secured with dark chains, alternative punk style",
    # BRANCO / PRATA — contraste dramático
    "long silver white hair with black roots, dramatic contrast, magenta glow",
    "white platinum hair, sharp straight cut bangs, violet rim backlight",
    "silver white hair streaked with hot pink, cyberpunk trapstar",
    # VERMELHO / VIOLETA — quente
    "dark maroon red hair, deep rich color, lit by warm neon",
    "black to deep violet gradient hair, rich dark ombre",
    "dark burgundy hair, glossy, cinematic warm lighting",
]

EYE_VARIATIONS = [
    "glowing neon magenta eyes, intense and hypnotic",
    "deep violet glowing eyes, dangerous and captivating",
    "bright hot pink eyes with star-shaped reflections",
    "deep crimson red eyes, cold killer stare",
    "glowing pink-violet eyes, seductive and dark",
    "sharp red eyes with vertical slit pupils, demonic energy",
]

EXPRESSION_VARIATIONS = [
    "cold dead stare directly into camera, dominant trap queen energy",
    "slow dangerous smirk, one eyebrow raised, confident and threatening",
    "slightly open mouth, glossy lips, heavy-lidded seductive gaze",
    "sharp psychotic smile, eyes wide and glowing, unhinged beauty",
    "expressionless cold face, jaw set, eyes burning with intensity",
    "subtle evil smile, looking down at viewer from above, superior energy",
    "fierce rage barely contained, clenched jaw, glowing eyes narrowed",
    "charming smile hiding danger, trap queen vibe, direct eye contact",
]

POSE_VARIATIONS = [
    # CORPO INTEIRO — forçar o modelo
    "full body standing pose, arms slightly out, legs apart, complete figure head to boots",
    "full body walking toward camera, coat or jacket flowing, chains moving, feet visible",
    "full body low angle shot, character looking down at viewer, boots in foreground, crown at top",
    "full body leaning on dark wall, one knee bent, hand on wall, complete body visible",
    "full body arms crossed, weight on one hip, dominant stance, complete silhouette",
    "full body sitting on concrete ledge, legs hanging, boots visible, full figure in frame",
    "full body back against wall, sliding down slightly, legs stretched out, full length",
    "full body standing with chain in hand, draped low, whole body from head to ankle visible",
    "full body three-quarter turn, looking back over shoulder, complete figure visible",
    "full body dynamic stance, hand reaching toward camera, full length visible behind",
]

OUTFIT_VARIATIONS = [
    # TRAPSTAR REAL — roupas específicas
    "oversized black Trapstar hoodie, matching dark joggers, chunky white sole sneakers, gold chain",
    "black leather biker jacket open, dark sports bra visible, black joggers, chunky black boots, silver chain",
    "dark techwear — black tactical vest, cargo pants with straps, platform boots, arm sleeves, chain belt",
    "black oversized puffer jacket, dark tracksuit underneath, gold Cuban chain, black boots",
    "black cropped hoodie with skull graphic, high-waisted black pants, chunky platform boots, choker and chains",
    "black full-length trench coat open, dark outfit underneath, heavy chains, combat boots",
    "dark gothic corset top, black wide-leg pants, platform stomper boots, multiple chain layers",
    "black zip-up tracksuit top half open, dark shorts, thigh-high black boots, chain accessories",
    "oversized black graphic tee tucked in, black mini skirt, thigh-high stockings, platform boots, chains",
    "black techwear bodysuit, dark cargo straps over it, chunky boots, fingerless gloves, choker",
]

SCENE_VARIATIONS = [
    # CENAS ESCURAS COM ILUMINAÇÃO QUENTE
    "dark rainy alley, neon magenta signs reflecting on wet asphalt, heavy shadows, red car lights far back",
    "underground parking garage, hot pink and violet neon tubes, concrete walls, dark atmosphere",
    "rooftop at night, blood red moon, violet fog, city lights blurred far below",
    "dark nightclub hallway, magenta laser beams, smoke machine haze, red velvet walls",
    "abandoned warehouse, single magenta spotlight from above, dust particles, pure darkness around",
    "pure black background, only character lit by dual neon: magenta left, red-orange right, no environment",
    "dark cyberpunk street, warm red and pink neon shop signs, wet black ground reflection",
    "dark concrete tunnel, violet neon strips along walls, red glow at end, foggy",
]

AURA_VARIATIONS = [
    "deep magenta electric sparks tracing her silhouette from feet upward",
    "dark red energy smoke rising from ground around her boots",
    "hot pink glitch distortion effect at edges of her body",
    "violet shadow tendrils curling around her arms and legs",
    "crimson flame aura wrapping her lower body, controlled and dark",
    "dark ink bleeding effect at edges of her silhouette, magenta glow within",
    "subtle warm orange heat shimmer rising from ground at her feet",
]

ART_STYLE_VARIATIONS = [
    "premium dark 2D anime, ultra sharp lineart, polished high-contrast cel shading, dark phonk poster quality",
    "dark cyberpunk anime illustration, crisp clean lines, deep shadows, professional music cover energy",
    "underground trap anime art, bold silhouette, neon accents, viral thumbnail composition",
    "dark anime key visual style, cinematic lighting, clean anatomy, phonk trapstar aesthetic",
    "high quality dark anime poster art, sharp details, moody atmosphere, dark queen protagonist energy",
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

# PALETAS SEM AZUL/CYAN — V26
GENRE_PALETTES = {
    "phonk": [
        "palette: black background, hot magenta dominant rim light, deep violet secondary shadow, warm red accent",
        "palette: near-black background, crimson red primary, deep purple secondary, magenta trim glow",
        "palette: dark background, neon magenta dominant, dark blood red accent, violet atmospheric haze",
    ],
    "trap": [
        "palette: black background, hot pink neon dominant, deep violet rim light, no blue allowed",
        "palette: near-black background, red neon primary, magenta glow secondary, gold jewelry accent warm",
        "palette: dark background, violet dominant, magenta street glow, warm dark red accent, clean palette",
    ],
    "electronic": [
        "palette: black background, neon magenta laser light dominant, violet digital atmosphere, no cyan or blue",
        "palette: deep black background, hot pink primary neon, violet glow secondary, no cold colors",
        "palette: dark background, electric purple dominant, magenta accent, warm dark red hint",
    ],
    "dark": [
        "palette: near black background, dark blood red eyes and accents, deep violet aura, minimal glow",
        "palette: black background, gray-black deep shadows, crimson red neon accent only, no blue",
        "palette: black background, white silver hair contrast, magenta-pink glow, cold tone ONLY from silver hair",
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
    key = f"{style}|{filename}|{short_num}|darkmark_v28_trapstar_noblue"
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
# PROMPT PRINCIPAL — V26
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
    # COMPOSIÇÃO — sempre primeiro
    ", full body, full length, wide shot, long shot, head to toe, "
    "legs visible, boots visible, complete figure, "
    # ESTILO
    "2D anime art, dark cyberpunk trapstar anime, "
    "dark phonk music cover aesthetic, "
    # PALETA — anti-azul repetido no sufixo também
    "warm magenta and violet palette, no blue, no cyan, no teal, not blue, not cyan, "
    "warm colors only, magenta dominant, "
    # PERSONAGEM
    "beautiful dark anime trapstar girl, sensual confident pose, "
    # BÁSICOS
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

                payload = {
                    "input": {
                        **FLUX_PARAMS,
                        "prompt":          full_prompt,
                        "negative_prompt": NEGATIVE_PROMPT,
                        "seed":            random.randint(1000, 999_999),
                    }
                }

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
        description="AI Image Generator — DJ DARK MARK v26 Full Body No Blue Engine"
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
