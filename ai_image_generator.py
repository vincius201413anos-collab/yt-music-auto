"""
ai_image_generator.py — DJ DARK MARK v36 HIGH-CTR CHANNEL-OPTIMIZED
=============================================================
CHANGELOG v36 — BASEADO EM DADOS REAIS DO CANAL:

DIAGNÓSTICO DO v35:
- Dark neon glowing eyes (Black Cherry Lips): 224 views → PIOR performer
- O estilo "yandere dark neon" não converte no algoritmo

O QUE REALMENTE PERFORMA (dados do canal):
- 1.9k views: performer real com fogo dramático → energia humana/quente
- 508-417 views: anime girl azul/teal moody, composição limpa → paleta fria clara
- 399-304 views: anime girl warm golden/sunset, expressão emocional → paleta quente
- 288-215 views: sunset city anime girl → fundo dourado cinematic

NOVA ESTRATÉGIA v36:
- PALETA PRINCIPAL: warm golden/amber/sunset (maior CTR consistente)
- PALETA SECUNDÁRIA: moody blue/teal (segunda maior performance)
- DARK NEON: mantido como variação, mas nunca dominante
- PERSONAGEM: expressivo, emocional, cute acessível — NÃO yandere perigosa
- COMPOSIÇÃO: portrait limpo, menos poluído, foco na expressão facial
- ILUMINAÇÃO: luz quente (golden hour, sunset, luz ambiente) > só escuridão
- ELEMENTOS: fones de ouvido, microfone, headphones — música visível
- REGRA DE CTR: uma só cor dominante, alto contraste, face centralizada

REFERÊNCIAS DE PERFORMANCE:
- Teal/blue moody clean → 400-500 views
- Warm golden sunset → 280-400 views
- Cute emotional face dominant → +30% CTR (dado vidIQ)
- Composição simples > efeitos complexos (pesquisa 2025)
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
    # Animagine XL — melhor qualidade anime, paletas ricas
    "cjwbw/animagine-xl-3.1",
    # Anything v5 — linhas limpas, rostos expressivos
    "lucataco/anything-v5-better-vae",
    # Flux-dev — fallback final
    "black-forest-labs/flux-dev",
]

FLUX_PARAMS = {
    # Portrait vertical — rosto dominante, olhos expressivos
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
# IDENTIDADE DO CANAL — v36 REALINHADA COM CTR REAL
# ══════════════════════════════════════════════════════════════════════

CHANNEL_IDENTITY = (
    "DJ Dark Mark music channel visual identity, "
    "emotional anime muse, expressive face dominant, beautiful melancholic energy, "
    "dark pop trap phonk electronic music cover art, "
    "warm golden OR moody teal OR cinematic dark palette, "
    "premium YouTube Shorts thumbnail universe, high CTR emotional hook"
)


# ══════════════════════════════════════════════════════════════════════
# CORE CHARACTER — v36 EMOTIONAL CUTE HIGH-CTR
# ══════════════════════════════════════════════════════════════════════

TRAPSTAR_DNA = (
    "one adult anime woman, clearly adult, "
    "beautiful expressive anime muse, emotionally resonant, "
    "cute melancholic energy, deeply felt, relatable but intense, "
    # ROSTO — elemento #1 de CTR (dado: faces = +30% CTR)
    "FACE IS THE FOCAL POINT: beautiful detailed anime face, "
    "large expressive emotional anime eyes, visible emotion in eyes, "
    "eyes with depth and feeling, catching light naturally, "
    "soft glossy lips, defined eyelashes, subtle blush on cheeks, "
    "expression that makes viewer stop scrolling, "
    # CABELO — define o mood
    "detailed flowing hair catching ambient light, "
    "hair with natural sheen and movement, "
    # ROUPA — sutil, não dominante
    "dark aesthetic outfit, tasteful, "
    "subtle accessory details, clean look, "
    # IDENTIDADE
    "alone, single character, no other people, no text"
)


# ══════════════════════════════════════════════════════════════════════
# COMPOSIÇÃO — v36 CLEAN PORTRAIT FIRST
# ══════════════════════════════════════════════════════════════════════

COMPOSITION_LOCK = (
    "tight portrait or close upper body shot, "
    "face filling majority of frame, eyes at upper third of composition, "
    "character centered or slightly off-center for dynamic feel, "
    "clean uncluttered composition, one clear focal point, "
    "vertical 9:16 format optimized for mobile, "
    "generous negative space around character for text placement, "
    "mobile-first design: readable at small thumbnail size, "
    "cinematic portrait framing, professional music cover composition"
)


# ══════════════════════════════════════════════════════════════════════
# STYLE LOCK — v36 CLEAN ANIME HIGH QUALITY
# ══════════════════════════════════════════════════════════════════════

STYLE_LOCK = (
    "premium 2D anime illustration, ultra clean sharp lineart, "
    "professional cel shading, smooth gradient shading, "
    "glossy reflections on eyes and hair, "
    "detailed face with visible emotion, "
    "NOT overly dark, NOT cluttered with excessive effects, "
    "clean background that complements character, "
    "professional music cover art quality, "
    "anime key visual aesthetic, beautiful character design"
)


# ══════════════════════════════════════════════════════════════════════
# LIGHTING — v36 WARM/CINEMATIC FIRST (dados mostram isso performa mais)
# ══════════════════════════════════════════════════════════════════════

LIGHTING_LOCK_WARM = (
    "warm golden hour lighting bathing the scene, "
    "soft amber light on character's face and hair, "
    "warm light from slightly behind creating rim effect, "
    "golden glow on environment, warm shadows, "
    "natural cinematic warmth, sunset color temperature, "
    "high contrast warm vs dark shadows for drama"
)

LIGHTING_LOCK_TEAL = (
    "moody cool teal/blue ambient lighting, "
    "cinematic blue-teal color grading, "
    "soft cool light on character's face, "
    "atmospheric cool mist or bokeh in background, "
    "high contrast cool light vs dark shadows, "
    "film noir meets anime aesthetic"
)

LIGHTING_LOCK_DARK = (
    "dramatic dark cinematic lighting, "
    "single strong light source illuminating character, "
    "deep shadows creating mood and mystery, "
    "colored rim light from background, "
    "professional dark music cover lighting, "
    "strong contrast between light and shadow"
)


# ══════════════════════════════════════════════════════════════════════
# PALETA — v36 BASEADA EM PERFORMANCE REAL
# ══════════════════════════════════════════════════════════════════════

# PALETA A — Warm Golden/Sunset (288-400+ views, melhor consistência)
PALETTE_WARM = (
    "warm golden amber palette, "
    "sunset orange and golden yellow tones dominating, "
    "warm background with orange/amber bokeh or environment, "
    "character bathed in warm golden light, "
    "hair catching golden sunlight, skin warm and glowing, "
    "orange-amber-gold color story throughout, "
    "warm cinematic film look"
)

# PALETA B — Moody Blue/Teal (400-508 views, segundo mais forte)
PALETTE_TEAL = (
    "moody blue-teal cinematic palette, "
    "deep navy and teal tones, cool atmospheric mood, "
    "teal ambient glow in environment, "
    "cool blue shadows and highlights, "
    "hair catching cool blue-teal light, "
    "atmospheric depth with cool color story, "
    "cinematic blue-teal film look"
)

# PALETA C — Dark Dramatic (mantida para fontes dark/phonk intenso)
PALETTE_DARK = (
    "dark dramatic cinematic palette, "
    "near-black background with strong single accent color, "
    "accent color: deep magenta OR violet OR crimson, "
    "character lit dramatically against dark, "
    "high contrast dark vs accent, "
    "professional dark music cover look"
)

# PALETA D — Pink/Rose Emotional (para dark pop)
PALETTE_ROSE = (
    "soft rose and deep pink cinematic palette, "
    "warm pink ambient light in background, "
    "deep rose shadows and pink highlights, "
    "romantic but dark emotional mood, "
    "pink bokeh and atmospheric depth, "
    "dark pink to crimson gradient color story"
)

# PALETA E — Purple/Violet Atmospheric
PALETTE_VIOLET = (
    "deep violet and purple atmospheric palette, "
    "rich purple ambient light and fog, "
    "violet tones in background and shadows, "
    "character with purple atmospheric rim light, "
    "moody purple-indigo cinematic look"
)


# ══════════════════════════════════════════════════════════════════════
# QUALITY & RETENTION LOCKS
# ══════════════════════════════════════════════════════════════════════

QUALITY_LOCK = (
    "masterpiece, best quality, ultra detailed anime illustration, "
    "beautiful expressive face, detailed shining eyes, clean anatomy, "
    "professional music cover art, high resolution crisp lineart, "
    "polished cel shading, premium channel visual identity"
)

RETENTION_LOCK = (
    "scroll-stopping thumbnail, "
    "FACE is the first thing viewer sees, immediate emotional impact, "
    "expression triggers curiosity or emotional resonance, "
    "high CTR dark music thumbnail energy, "
    "beautiful character that makes viewer want to know more, "
    "visual hook in first millisecond"
)

CONSISTENCY_LOCK = (
    "consistent channel branding, "
    "recognizable anime muse recurring character, "
    "dark music aesthetic with emotional depth, "
    "professional, not generic, not stock art"
)

SKIN_LOCK = (
    "warm pale to medium anime skin tone, "
    "smooth clear skin with natural shading, "
    "skin reacting to ambient lighting color, "
    "soft blush on cheeks, healthy luminous skin"
)


# ══════════════════════════════════════════════════════════════════════
# NEGATIVE PROMPT v36 — AJUSTADO PARA CTR
# ══════════════════════════════════════════════════════════════════════

NEGATIVE_PROMPT = (
    # Qualidade ruim
    "ugly, bad anatomy, bad face, distorted face, asymmetrical eyes, "
    "bad hands, extra fingers, missing fingers, fused limbs, broken body, "
    "long neck, disfigured, mutated, melted face, uncanny valley, "
    "blurry, low quality, jpeg artifacts, heavy noise, "
    # Estilo errado
    "photorealistic, real person, 3D render, CGI, "
    "doll, plastic skin, western cartoon, simple cartoon, flat shading, "
    # Composição que NÃO converte (dados do canal)
    "cluttered background, busy background, too many effects, "
    "overwhelming neon overload, too dark to see face, "
    "face too small in frame, far away character, full body tiny, "
    "excessive glitch effects, extreme neon chaos, "
    # Conteúdo proibido/indesejado
    "nude, explicit nudity, genitalia, nipples, "
    "child, underage, loli, very young, baby face, "
    "multiple people, crowd, two girls, duplicate character, "
    # Texto na imagem
    "text, words, logo, watermark, signature, letters, numbers, "
    # Paleta que não performa
    "washed out, desaturated, muddy colors, flat boring colors, "
    "overly saturated rainbow chaos, mixed incompatible colors, "
    # Overexposure de efeitos (v35 tinha isso em excesso)
    "overexposed bloom, excessive glow overload, neon everywhere, "
    "dark void where face is invisible, eyes lost in darkness"
)


# ══════════════════════════════════════════════════════════════════════
# VARIAÇÕES — v36 CALIBRADAS POR PERFORMANCE
# ══════════════════════════════════════════════════════════════════════

HAIR_VARIATIONS = [
    # Warm tones — mais alto CTR
    "long flowing dark brown hair with warm golden highlights, catching sunset light",
    "dark black hair with warm amber rim light, glossy and detailed",
    "rich dark auburn hair with golden sun catching through strands",
    "chocolate brown hair flowing naturally, warm light creating shine",
    "dark hair with rose-tinted highlights, romantic warm glow",
    # Cool/teal tones — segundo maior CTR
    "dark blue-black hair with cool teal highlights, cinematic and moody",
    "deep navy hair with subtle cool blue sheen, atmospheric depth",
    "silver-white hair with blue-teal tint, futuristic melancholic look",
    "dark hair with violet-blue shimmer, moody and expressive",
    # Neutros versáteis
    "black hair with natural shine catching ambient color light",
    "dark purple-black hair with soft glow from environment lighting",
    "deep brown to black ombre hair, detailed natural strands",
]

EYE_VARIATIONS = [
    # OLHOS EXPRESSIVOS — foco em emoção não em neon
    # v36: emoção > efeito
    "warm amber-honey eyes catching golden light, deep and emotional, "
    "glossy natural reflections, expressive and beautiful",

    "deep teal green eyes with natural sparkle, intense emotional gaze, "
    "real depth and feeling, catching cool ambient light",

    "soft rose pink eyes with gentle glow, romantic melancholic look, "
    "glossy natural reflections, beautiful and expressive",

    "deep violet purple eyes, atmospheric and dreamlike, "
    "natural iris detail, emotionally resonant stare",

    "rich brown eyes with golden light reflected, warm and deep, "
    "glossy natural sheen, soulful and expressive",

    "blue-grey eyes with silver light catching, cinematic cool tone, "
    "detailed iris, intense emotional depth",

    "warm copper-orange eyes with amber depth, glowing naturally from light, "
    "expressive and emotionally intense",

    "dark crimson eyes with deep emotional resonance, "
    "glossy natural sheen, intense but beautiful",

    "bright emerald green eyes catching light, vivid and expressive, "
    "detailed iris, emotionally electric stare",

    "soft gray-blue eyes with melancholic depth, cinematic muted cool, "
    "emotional and resonant, natural glossy beauty",
]

EXPRESSION_VARIATIONS = [
    # BASEADO NOS TOPS DO CANAL — expressões que funcionam
    # Simples, emocionais, relacionáveis
    "soft melancholic gaze into distance, quiet longing expression, beautiful sadness",
    "gentle slight smile with deep emotional eyes, warm and inviting, relatable",
    "wide curious eyes slightly parted lips, moment of wonder and discovery",
    "calm serene expression with subtle emotional depth in eyes, peaceful intensity",
    "soft vulnerable expression, eyes slightly glistening, emotional moment",
    "direct confident gaze at viewer, slight knowing smile, magnetic eye contact",
    "pensive thoughtful expression, head slightly tilted, eyes full of thought",
    "warm gentle smile not quite reaching eyes, something deeper underneath",
    "slightly surprised expression, eyes bright and open, moment of realization",
    "quiet intense stare, lips barely parted, overwhelming emotional presence",
    "soft bittersweet smile, eyes carrying something unspoken, emotional weight",
    "dreamy distant look, eyes half-lidded with feeling, lost in music",
]

MUSIC_ELEMENT_VARIATIONS = [
    # Elementos musicais — aumentam relevância do contexto
    "wearing sleek dark over-ear headphones around neck or on ears",
    "holding a microphone loosely, casual performance energy",
    "headphones resting on head, casual and cool",
    "earbuds in, immersed in music, authentic listening moment",
    "no music element, pure character expression",
    "no music element, pure character expression",  # peso maior sem elemento
    "no music element, pure character expression",  # peso maior sem elemento
    "subtle music note motif in background, very minimal",
    "faint waveform visualization in background, atmospheric",
    "holding nothing, pure emotional portrait, music implied by mood",
]

BACKGROUND_VARIATIONS = [
    # WARM — maior CTR consistente no canal
    "warm golden sunset sky background, city silhouette distant, bokeh light, "
    "rich amber and orange atmospheric depth",

    "warm golden room interior background, soft window light, bokeh, "
    "cozy but cinematic amber atmosphere",

    "sunset urban skyline background, warm orange glow, "
    "city lights beginning to appear, cinematic warm depth",

    "warm golden forest or nature background, soft sunlight filtering, "
    "bokeh leaves and light, beautiful natural warmth",

    "golden hour open space background, sky deep orange and amber, "
    "wide cinematic warmth, emotional depth",

    # TEAL/BLUE — segundo maior CTR
    "moody night city background, cool teal blue neon reflections on wet street, "
    "cinematic rain atmosphere, deep blue mood",

    "cool blue-teal abstract background, atmospheric fog and depth, "
    "cinematic moody interior, blue ambient glow",

    "night sky background with cool blue-purple atmosphere, "
    "stars faint, cinematic night mood",

    "dark blue urban interior background, neon reflections in glass, "
    "rain-soaked cinematic atmosphere, teal mood",

    # DARK — para fontes mais pesadas
    "deep dark background with single warm or cool accent, "
    "character cleanly lit against darkness, professional dark cover",

    "abstract dark atmosphere with subtle depth, "
    "faint environmental glow framing character",
]

MOOD_VARIATIONS = [
    # Moods que conectam com audiência musical
    "the feeling you get when a song hits exactly right",
    "melancholic beauty, bittersweet emotional resonance",
    "quiet intensity, music felt rather than heard",
    "nostalgic longing, emotional depth under calm surface",
    "dark romance, beautiful sadness, emotional richness",
    "late night introspection, alone but feeling everything",
    "the moment before everything changes, suspended feeling",
    "overstimulated emotional overwhelm expressed through stillness",
    "controlled chaos within, serene outside, dark pop energy",
]

ART_STYLE_VARIATIONS = [
    "premium dark anime key visual, clean expressive lineart, "
    "detailed emotional face, professional music cover quality",

    "cinematic anime illustration, rich color depth, "
    "emotional storytelling through expression, high production value",

    "clean detailed anime character art, beautiful face dominant, "
    "professional shading, high contrast, emotional resonance",

    "dark pop anime aesthetic, moody but beautiful, "
    "expressive character, rich environmental background",

    "high quality anime portrait illustration, face as focal point, "
    "detailed eyes catching light, premium digital art finish",
]


# ══════════════════════════════════════════════════════════════════════
# MAPEAMENTO DE GÊNERO — v36 COM PALETAS CALIBRADAS
# ══════════════════════════════════════════════════════════════════════

GENRE_MAP = {
    "phonk":      "phonk",
    "trap":       "trap",
    "dark":       "dark",
    "darkpop":    "darkpop",
    "dark pop":   "darkpop",
    "electronic": "electronic",
    "edm":        "electronic",
    "dubstep":    "electronic",
    "funk":       "trap",
    "rock":       "rock",
    "metal":      "dark",
    "cinematic":  "darkpop",
    "lofi":       "darkpop",
    "indie":      "darkpop",
    "pop":        "darkpop",
}

# v36: paletas rankeadas por CTR do canal real
# Warm golden > Teal/blue > Dark neon (em termos de views)
GENRE_PALETTES = {
    "phonk": [
        # Phonk: dark/dramático mas com luz quente ou fria clara
        ("warm", PALETTE_WARM, LIGHTING_LOCK_WARM,
         "dominant warm golden phonk energy, dramatic sunset, "
         "cinematic amber warmth matching heavy 808 bass"),

        ("teal", PALETTE_TEAL, LIGHTING_LOCK_TEAL,
         "moody blue-teal phonk underground atmosphere, "
         "cool cinematic depth, bass-heavy nighttime energy"),

        ("dark", PALETTE_DARK, LIGHTING_LOCK_DARK,
         "dark dramatic phonk, deep crimson accent, "
         "single light source, powerful dark music cover"),
    ],
    "trap": [
        ("warm", PALETTE_WARM, LIGHTING_LOCK_WARM,
         "warm trap energy, golden urban sunset, "
         "street cinematic warmth, city trap mood"),

        ("rose", PALETTE_ROSE, LIGHTING_LOCK_DARK,
         "dark rose trap aesthetic, pink-crimson drama, "
         "emotional trap energy, dark pop crossover"),

        ("teal", PALETTE_TEAL, LIGHTING_LOCK_TEAL,
         "cool urban trap atmosphere, blue-teal city night, "
         "moody cinematic trap energy"),
    ],
    "electronic": [
        ("teal", PALETTE_TEAL, LIGHTING_LOCK_TEAL,
         "electronic music teal-blue atmosphere, "
         "clean cool electronic energy, futuristic mood"),

        ("violet", PALETTE_VIOLET, LIGHTING_LOCK_DARK,
         "electronic violet atmospheric depth, "
         "rich purple electronic sound visualization"),

        ("warm", PALETTE_WARM, LIGHTING_LOCK_WARM,
         "warm electronic energy, golden analog warmth, "
         "emotional electronic music mood"),
    ],
    "darkpop": [
        # Dark pop: mais emocional, warm funciona muito bem
        ("warm", PALETTE_WARM, LIGHTING_LOCK_WARM,
         "warm emotional dark pop, golden melancholic beauty, "
         "bittersweet warm aesthetic, dark pop crossing into light"),

        ("rose", PALETTE_ROSE, LIGHTING_LOCK_DARK,
         "dark rose pop romance, deep pink emotional depth, "
         "beautiful dark pop feeling"),

        ("teal", PALETTE_TEAL, LIGHTING_LOCK_TEAL,
         "cool melancholic dark pop, blue-teal emotional mood, "
         "cinematic dark pop atmosphere"),
    ],
    "dark": [
        ("dark", PALETTE_DARK, LIGHTING_LOCK_DARK,
         "dark dramatic music cover, deep and powerful, "
         "single accent color against darkness, intense mood"),

        ("teal", PALETTE_TEAL, LIGHTING_LOCK_TEAL,
         "dark teal atmospheric intensity, "
         "cool cinematic dark music energy"),

        ("warm", PALETTE_WARM, LIGHTING_LOCK_WARM,
         "warm dark contrast, golden light in darkness, "
         "dramatic chiaroscuro warm dark energy"),
    ],
    "rock": [
        ("warm", PALETTE_WARM, LIGHTING_LOCK_WARM,
         "dramatic warm rock energy, fire and amber, "
         "performance energy captured, warm concert atmosphere"),

        ("dark", PALETTE_DARK, LIGHTING_LOCK_DARK,
         "dark rock power, intense dramatic lighting, "
         "raw energy and emotion"),

        ("teal", PALETTE_TEAL, LIGHTING_LOCK_TEAL,
         "cool rock atmosphere, cinematic dark blue energy, "
         "intense moody rock mood"),
    ],
}

# Fallback
GENRE_PALETTES["default"] = GENRE_PALETTES["darkpop"]


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
    return re.sub(r"\s+", " ", name).strip() or "dark phonk"


def _seed(style: str, filename: str, short_num: int) -> int:
    key = f"{style}|{filename}|{short_num}|darkmark_v36_high_ctr_channel_optimized"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % (10**9)


def _rng(style: str, filename: str, short_num: int) -> random.Random:
    return random.Random(_seed(style, filename, short_num))


def _song_mood_boost(song_name: str) -> str:
    """Detecção de mood da música para ajustar descrição emocional do personagem."""
    clean = song_name.lower()

    if any(w in clean for w in ["dark", "shadow", "ghost", "night", "madrugada", "noite"]):
        return (
            "character with quiet haunted beauty, "
            "eyes holding darkness and longing, "
            "nighttime melancholic energy"
        )
    if any(w in clean for w in ["fire", "burn", "rage", "fury", "rage"]):
        return (
            "character with intense passionate energy, "
            "eyes bright with contained fire, "
            "powerful emotional intensity"
        )
    if any(w in clean for w in ["love", "heart", "amor", "coraçao", "rose", "cherry"]):
        return (
            "character with deep romantic feeling, "
            "eyes full of emotion and longing, "
            "beautiful dark romantic energy"
        )
    if any(w in clean for w in ["lost", "alone", "lonely", "sozinho", "perdido"]):
        return (
            "character with profound loneliness, "
            "eyes glistening with quiet sadness, "
            "beautiful isolated melancholy"
        )
    if any(w in clean for w in ["drive", "speed", "run", "race", "corrida"]):
        return (
            "character with focused determined energy, "
            "eyes sharp and forward, "
            "driven intense expression"
        )
    if any(w in clean for w in ["queen", "king", "boss", "power", "rule"]):
        return (
            "character with commanding quiet confidence, "
            "eyes of someone who owns the room, "
            "dark queen energy expressed through stillness"
        )
    if any(w in clean for w in ["dream", "sonho", "sleep", "cloud"]):
        return (
            "character with dreamy distant expression, "
            "eyes half-caught in another world, "
            "ethereal floating feeling"
        )

    # Default genérico emocional
    return (
        "character with deep emotional presence, "
        "eyes carrying the weight of the music, "
        "expressive and resonant"
    )


def _pick_palette(
    genre: str,
    rng: random.Random,
    force_warm: bool = False,
    force_teal: bool = False,
) -> tuple[str, str, str, str]:
    """
    Retorna (palette_name, palette_str, lighting_str, genre_detail).
    v36: lógica de CTR — warm tem maior probabilidade.
    """
    options = GENRE_PALETTES.get(genre, GENRE_PALETTES["default"])

    if force_warm:
        warm_opts = [o for o in options if o[0] == "warm"]
        if warm_opts:
            return warm_opts[0]

    if force_teal:
        teal_opts = [o for o in options if o[0] == "teal"]
        if teal_opts:
            return teal_opts[0]

    # Pesos baseados em CTR real do canal:
    # warm = ~40% chance, teal = ~35% chance, dark/rose/violet = ~25%
    weights = []
    for opt in options:
        name = opt[0]
        if name == "warm":
            weights.append(40)
        elif name == "teal":
            weights.append(35)
        else:
            weights.append(25)

    total = sum(weights)
    r = rng.random() * total
    cumulative = 0
    for opt, w in zip(options, weights):
        cumulative += w
        if r <= cumulative:
            return opt

    return options[0]


# ══════════════════════════════════════════════════════════════════════
# PROMPT PRINCIPAL — v36 HIGH-CTR
# ══════════════════════════════════════════════════════════════════════

def build_ai_prompt(
    style: str,
    filename: str,
    styles: list | None = None,
    short_num: int = 1,
    force_warm: bool = False,
    force_teal: bool = False,
) -> str:
    styles = styles or []
    mapped = GENRE_MAP.get((style or "default").lower().strip(), "default")
    rng = _rng(mapped, filename, short_num)
    song_name = _clean_song_name(filename)

    # Seleção de variações
    hair = rng.choice(HAIR_VARIATIONS)
    eyes = rng.choice(EYE_VARIATIONS)
    expression = rng.choice(EXPRESSION_VARIATIONS)
    music_elem = rng.choice(MUSIC_ELEMENT_VARIATIONS)
    background = rng.choice(BACKGROUND_VARIATIONS)
    art_style = rng.choice(ART_STYLE_VARIATIONS)
    mood_mix = rng.choice(MOOD_VARIATIONS)
    song_mood = _song_mood_boost(song_name)

    # Paleta com lógica de CTR
    palette_name, palette_str, lighting_str, genre_detail = _pick_palette(
        mapped, rng, force_warm=force_warm, force_teal=force_teal
    )

    genre_text = ", ".join([style] + [s for s in styles if s and s != style])

    prompt = (
        # ROSTO/EXPRESSÃO VÊM PRIMEIRO (CTR: face dominant)
        f"beautiful adult anime woman, {expression}, "
        f"{eyes}, "

        # PERSONAGEM COMPLETO
        f"{TRAPSTAR_DNA}, "

        # DETALHES VISUAIS
        f"hair: {hair}, "
        f"music element: {music_elem}, "

        # COMPOSIÇÃO LIMPA
        f"{COMPOSITION_LOCK}, "

        # BACKGROUND CONTEXTUAL
        f"background: {background}, "

        # ESTILO
        f"{STYLE_LOCK}, "

        # PALETA (escolhida por CTR)
        f"{palette_str}, "

        # ILUMINAÇÃO (combinada com paleta)
        f"{lighting_str}, "

        # PELE
        f"{SKIN_LOCK}, "

        # MOOD DA MÚSICA (contextual)
        f"character mood: {song_mood}, "
        f"emotional vibe: {mood_mix}, "

        # DETALHE DE GÊNERO
        f"genre atmosphere: {genre_detail}, "

        # RETENÇÃO/CTR
        f"{RETENTION_LOCK}, "

        # QUALIDADE
        f"{QUALITY_LOCK}, "
        f"{CONSISTENCY_LOCK}, "

        # ARTE
        f"art style: {art_style}, "

        # CONTEXTO MUSICAL
        f"genre: {genre_text}, "
        f"song mood: {song_name}, "

        # REFORÇO FINAL CTR
        "beautiful expressive face dominant, eyes connecting with viewer, "
        "emotional resonance, clean composition, "
        "dark music aesthetic, premium quality, "
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
# SUFIXO DE REFORÇO v36 — CALIBRADO POR CTR
# ══════════════════════════════════════════════════════════════════════

GENERATION_SUFFIX = (
    ", "
    # FACE DOMINANT — dado de CTR
    "beautiful detailed anime face, expressive emotional eyes, "
    "face filling frame, portrait composition dominant, "
    # QUALIDADE
    "masterpiece quality, ultra detailed, clean sharp lineart, "
    "professional anime illustration, beautiful character art, "
    # PALETA LIMPA
    "rich coherent color palette, high contrast, clean background, "
    "cinematic color grading, professional music cover quality, "
    # PROIBIÇÕES EXPLÍCITAS
    "no text, no logo, no watermark, no extra people, "
    "no excessive neon overload, no cluttered effects, "
    "face clearly visible, eyes expressive and readable"
)


# ══════════════════════════════════════════════════════════════════════
# GERAÇÃO DE IMAGEM (REPLICATE) — sem alteração funcional
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
# FUNÇÕES DE CONVENIÊNCIA — v36
# ══════════════════════════════════════════════════════════════════════

def generate_background_image(
    style: str = "phonk",
    output_path: str = "assets/background.png",
    seed_variant: int = 0,
    max_retries: int = 3,
    force_warm: bool = False,
    force_teal: bool = False,
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
# CLI — v36
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="AI Image Generator — DJ DARK MARK v36 High-CTR Channel-Optimized"
    )
    parser.add_argument("--style",       default="phonk",
                        help="Gênero musical (phonk, trap, electronic, dark, darkpop, rock)")
    parser.add_argument("--filename",    default="dark phonk.mp3",
                        help="Nome da música (varia o prompt e o mood)")
    parser.add_argument("--short-num",   type=int, default=1,
                        help="Número do short (varia seed)")
    parser.add_argument("--output",      default="assets/background.png")
    parser.add_argument("--force-warm",  action="store_true",
                        help="Força paleta warm golden (maior CTR histórico do canal)")
    parser.add_argument("--force-teal",  action="store_true",
                        help="Força paleta teal/blue (segundo maior CTR)")
    parser.add_argument("--prompt-only", action="store_true",
                        help="Só imprime o prompt, não gera imagem")
    args = parser.parse_args()

    prompt = build_ai_prompt(
        style=args.style,
        filename=args.filename,
        styles=[args.style],
        short_num=args.short_num,
        force_warm=getattr(args, "force_warm", False),
        force_teal=getattr(args, "force_teal", False),
    )

    if args.prompt_only:
        print("=== PROMPT v36 ===")
        print(prompt)
        print("\n=== NEGATIVE PROMPT ===")
        print(NEGATIVE_PROMPT)
        print("\n=== GENERATION SUFFIX ===")
        print(GENERATION_SUFFIX)
    else:
        path = generate_image(prompt, args.output)
        print(f"✅ Salvo: {path}" if path else "✗ Falha na geração.")
