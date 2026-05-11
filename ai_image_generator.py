"""
ai_image_generator.py — DJ DARK MARK v53.0 ██ THUMBNAIL-FIRST EDITION ██
══════════════════════════════════════════════════════════════════════════

ANÁLISE v52 → v53:
  Wildfire Heart Electronic (close-up olhos rosa) = 113 views ✅
  Signal Fire (close/médio) = 89-106 views ✅
  Street Trap (back view, personagem pequeno) = 2 views ❌
  Back views / full body sem rosto = morte do view ❌

MUDANÇAS PRINCIPAIS v53:
  [FIX 1]  EXTREME_CLOSEUP agora tem peso 45% — o rosto VENDE
  [FIX 2]  Back view removida / peso quase zero
  [FIX 3]  EYE_GLOW_LOCK: instrução obrigatória de olhos brilhantes
  [FIX 4]  THUMBNAIL_CONTRAST_LOCK: contraste brutal forçado em todo frame
  [FIX 5]  Paletas mais saturadas / menos lama
  [FIX 6]  Claude prompt reescrito para focar no rosto primeiro
  [FIX 7]  NEGATIVE_PROMPT expandido contra personagem pequeno
  [FIX 8]  COMPOSITION_WEIGHTS: close-up 45%, 3/4 35%, full body 18%, back 2%
  [FIX 9]  Novo EYE_ARCHETYPE system — tipo de olho por gênero
  [FIX 10] GENRE_COLOR_PUNCH: saturação e contraste forçados por gênero
"""

from __future__ import annotations

import hashlib
import logging
import os
import random
import re
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger("ai_image_generator_v53")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# ═══════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════

REPLICATE_API_TOKEN: str = os.getenv("REPLICATE_API_TOKEN", "")

REPLICATE_MODELS = [
    "black-forest-labs/flux-dev",
    "black-forest-labs/flux-schnell",
]

FLUX_DEV_PARAMS: dict = {
    "aspect_ratio": "9:16",
    "num_inference_steps": 50,      # +10 steps = mais detalhes no rosto
    "guidance": 6.5,                 # guidance mais alto = mais fiel ao prompt
    "output_format": "png",
    "output_quality": 100,
    "disable_safety_checker": True,
}

FLUX_SCHNELL_PARAMS: dict = {
    "aspect_ratio": "9:16",
    "num_inference_steps": 4,
    "go_fast": True,
    "output_format": "png",
    "output_quality": 100,
    "disable_safety_checker": True,
}

VERSION = "v53.0-THUMBNAIL-FIRST"


def get_anthropic_model() -> str:
    return os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")


# ═══════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════

class CharType(Enum):
    WAIFU   = auto()
    SHOUNEN = auto()


class EmotionArchetype(Enum):
    COLD_QUEEN      = "cold_queen"
    YANDERE_SMILE   = "yandere_smile"
    SEDUCTIVE_GAZE  = "seductive_gaze"
    DOMINANT_VIBE   = "dominant_vibe"
    PLAYFUL_DANGER  = "playful_danger"
    ETHEREAL_SORROW = "ethereal_sorrow"
    BATTLE_FURY     = "battle_fury"
    SOFT_OBSESSION  = "soft_obsession"
    COLD_RAGE       = "cold_rage"
    I_AM_HIM        = "i_am_him"
    FINAL_FORM      = "final_form"
    SILENT_APEX     = "silent_apex"


# ═══════════════════════════════════════════════════════════════════════
# [FIX 3] EYE GLOW SYSTEM — o olho é o hook principal
# Baseado em análise: Wildfire Heart (close-up olhos rosas) = melhor performance
# ═══════════════════════════════════════════════════════════════════════

EYE_GLOW_BY_GENRE: dict[str, str] = {
    "phonk": (
        "EYES: irises glowing deep violet-purple #9B30FF from within like neon tubes, "
        "pupils slit and luminous, seven or more distinct catchlights reflecting city neon, "
        "eye whites slightly tinted lavender from power overflow, "
        "under-eye neon shadow casting violet onto cheekbone, "
        "EYES MUST BE THE BRIGHTEST POINT IN THE FRAME — readable at 40px thumbnail"
    ),
    "trap": (
        "EYES: irises burning blood-crimson #FF1A1A from within with gold ring at iris edge, "
        "pupils dark and piercing with three gold catchlights, "
        "intense locked-on gaze radiating absolute street authority, "
        "eye whites slightly red from power pressure, "
        "EYES MUST RADIATE DANGER — readable at 40px thumbnail"
    ),
    "electronic": (
        "EYES: irises electric cyan #00FFFF glowing with nested blue-white rings, "
        "pupils luminous white at center fading to deep blue at edge, "
        "six catchlights including one large circular reflection of city tunnel, "
        "tear-duct area glowing faint cyan, "
        "EYES MUST FEEL ELECTRIC AND ALIVE — readable at 40px thumbnail"
    ),
    "darkpop": (
        "EYES: irises deep purple-rose #CC44FF glowing with inner pink-silver ring, "
        "pupils large and expressive, single large moonlight catchlight plus two neon points, "
        "wet with held-back emotion making neon reflections multiply, "
        "mascara-trace glow beneath eye from tear-neon interaction, "
        "EYES MUST HIT AN EMOTIONAL NERVE — readable at 40px thumbnail"
    ),
    "dark": (
        "EYES: irises glowing single saturated neon color in near-total darkness, "
        "maximum contrast between dark face and luminous iris, "
        "EYES ARE THE ONLY LIGHT SOURCE IN THE FRAME"
    ),
    "default": (
        "EYES: irises glowing vivid neon from within, multiple bright catchlights, "
        "pupils luminous and expressive, EYES ARE THE PRIMARY SCROLL-STOP ELEMENT"
    ),
}

# [FIX 9] Tipos de olho por gênero — estética diferente
EYE_SHAPE_WAIFU = (
    "large almond-shaped anime eyes with thick upper lash line, "
    "lower lash delicate, iris taking up 60% of visible eye area, "
    "double eyelid with subtle neon highlight line, "
    "expressive brows arched with emotion"
)

EYE_SHAPE_SHOUNEN = (
    "sharp determined anime eyes with strong brow, "
    "iris glowing bright, intense focused gaze locked forward, "
    "slightly narrowed — predator energy, "
    "jaw set beneath expressive brows"
)


# ═══════════════════════════════════════════════════════════════════════
# [FIX 1+8] COMPOSITION SYSTEM — close-up DOMINA
# Dados: close-up = 113 views, back view = 2 views
# ═══════════════════════════════════════════════════════════════════════

COMPOSITION_STYLES: list[dict] = [
    {
        "name": "extreme_closeup",
        "prompt": (
            "EXTREME CLOSE-UP — face and upper chest filling 9:16 frame completely, "
            "eyes positioned at center of frame, irises at 30% frame width each, "
            "FACE TAKES UP 70% OF TOTAL FRAME HEIGHT, "
            "jaw at lower 20%, crown of head at upper 5%, "
            "pores and individual eyelashes rendered at maximum detail, "
            "dramatic split-lighting sculpting cheekbones and jaw, "
            "glowing eyes immediately visible from any thumbnail distance"
        ),
        "waifu_weight": 45,
        "shounen_weight": 38,
    },
    {
        "name": "bust_closeup",
        "prompt": (
            "BUST/CHEST SHOT — character from mid-chest to crown filling 9:16 frame, "
            "face in upper 55% of frame with eyes at visual center, "
            "signature outfit collar/necklace/armor visible at bottom third, "
            "one hand or technique rising into frame from below, "
            "intense facial expression legible at small thumbnail, "
            "dramatic cinematic lighting on face — 1 key light, 1 neon rim"
        ),
        "waifu_weight": 30,
        "shounen_weight": 30,
    },
    {
        "name": "three_quarter_cinematic",
        "prompt": (
            "3/4 BODY CINEMATIC — character from mid-thigh to crown in vertical 9:16 frame, "
            "face in upper 35%, eyes readable at small scale — expression dramatic, "
            "full outfit and signature weapon/technique visible, "
            "Dutch angle adding kinetic energy to composition, "
            "character razor-sharp, background blurred and glowing behind"
        ),
        "waifu_weight": 18,
        "shounen_weight": 25,
    },
    {
        "name": "full_body_power",
        "prompt": (
            "FULL BODY — character head to toe, 85% of frame height, "
            "LOW ANGLE looking up making them godlike in scale, "
            "face MUST be readable — do NOT make face too small, "
            "technique/aura consuming background dramatically, "
            "silhouette clear, every detail of outfit rendered"
        ),
        "waifu_weight": 5,
        "shounen_weight": 5,
    },
]


def _weighted_composition(rng: random.Random, char_type: CharType) -> dict:
    weight_key = "waifu_weight" if char_type == CharType.WAIFU else "shounen_weight"
    total = sum(c[weight_key] for c in COMPOSITION_STYLES)
    r = rng.random() * total
    acc = 0.0
    for comp in COMPOSITION_STYLES:
        acc += comp[weight_key]
        if r <= acc:
            return comp
    return COMPOSITION_STYLES[0]


# ═══════════════════════════════════════════════════════════════════════
# [FIX 4+10] THUMBNAIL CONTRAST LOCK + GENRE COLOR PUNCH
# Problema v52: paletas lamacentas, contraste baixo
# ═══════════════════════════════════════════════════════════════════════

THUMBNAIL_CONTRAST_LOCK = (
    "THUMBNAIL CONTRAST MANDATE — "
    "the image must read with extreme clarity at 120x200px thumbnail resolution: "
    "ONE clear bright element (face/eyes) against ONE dark background — zero ambiguity, "
    "minimum 85% contrast ratio between character and background, "
    "maximum color saturation — HSB saturation above 90% on all neon elements, "
    "NO muddy midtones, NO washed-out bloom, NO gray fog obscuring features, "
    "skin must be clearly distinguishable from hair and background, "
    "face silhouette must be readable in under 0.3 seconds"
)

GENRE_COLOR_PUNCH: dict[str, str] = {
    "phonk": (
        "COLOR MANDATE — violet #8B00FF at maximum saturation, "
        "background pure black #050508, ZERO gray or brown in neon elements, "
        "character skin pale cool white contrasting against dark, "
        "a single HOT MAGENTA #FF00CC accent on one detail only, "
        "VHS grain adds texture NOT desaturation — keep colors vivid underneath"
    ),
    "trap": (
        "COLOR MANDATE — blood red #FF1500 at maximum saturation, "
        "gold #FFD700 as hard accent on 1-2 jewelry/power details, "
        "background pure black with red rim light, "
        "smoke in cool gray-blue to separate — NOT brown, "
        "skin warm brown or pale — sharply contrasted against dark background"
    ),
    "electronic": (
        "COLOR MANDATE — electric cyan #00F5FF at maximum saturation, "
        "deep navy #000033 background — NOT black, the navy reads as electronic, "
        "HOT MAGENTA #FF00BB as secondary accent, "
        "white #FFFFFF at particle centers and catchlights, "
        "ZERO warm tones — this is a cold neon world"
    ),
    "darkpop": (
        "COLOR MANDATE — rose neon #FF44AA and deep purple #6600CC, "
        "background near-black with purple undertone, "
        "silver-white moonlight as rim light source, "
        "lilac #DDAAFF on highlight details, "
        "beautiful high contrast — NOT muddy dark red"
    ),
    "dark": (
        "COLOR MANDATE — 90% absolute black, ONE vivid neon color at maximum saturation, "
        "no other colors compete — maximum purity in the single accent"
    ),
    "default": (
        "COLOR MANDATE — electric teal and hot magenta at maximum saturation, "
        "deep black background, zero muddy midtones"
    ),
}


# ═══════════════════════════════════════════════════════════════════════
# CHANNEL DNA
# ═══════════════════════════════════════════════════════════════════════

CHANNEL_DNA = (
    "DJ Dark Mark viral anime phonk trap music channel — "
    "scroll-stopping 9:16 vertical Short thumbnail image, "
    "cinematic anime face dominating the frame, "
    "glowing eyes as the single most powerful visual element, "
    "dark neon underground premium aesthetic"
)

GENRE_MAP: dict[str, str] = {
    "phonk": "phonk", "trap": "trap", "dark": "dark",
    "darkpop": "darkpop", "dark pop": "darkpop",
    "electronic": "electronic", "edm": "electronic",
    "dubstep": "electronic", "house": "electronic",
    "funk": "trap", "rock": "dark", "metal": "dark",
    "cinematic": "darkpop", "lofi": "darkpop",
    "indie": "darkpop", "pop": "darkpop",
    "hiphop": "trap", "hip-hop": "trap", "rap": "trap",
    "bass": "phonk", "drift": "phonk",
    "phonkbr": "phonk", "funk br": "trap",
    "funk brasileiro": "trap",
}


# ═══════════════════════════════════════════════════════════════════════
# [FIX 5] PALETAS MELHORADAS — mais saturadas, menos lama
# ═══════════════════════════════════════════════════════════════════════

GENRE_PALETTE_LOCK: dict[str, str] = {
    "phonk": (
        "primary: violet #8B00FF neon at 100% saturation, "
        "secondary: hot magenta #FF00CC as accent only, "
        "background: pure black #050508, "
        "skin: cool pale illuminated by violet, "
        "NO brown, NO orange, NO warm tones — pure violet nightmare"
    ),
    "trap": (
        "primary: blood crimson #FF1500 at 100% saturation, "
        "secondary: pure gold #FFD700 on jewelry only, "
        "background: absolute black #050505 with red rim, "
        "skin: warm contrasted against black, "
        "smoke: cool blue-gray ONLY — no brown smoke"
    ),
    "electronic": (
        "primary: electric cyan #00F5FF at 100% saturation, "
        "secondary: hot magenta #FF00BB as contrast neon, "
        "background: deep navy #000022, "
        "particles: white core fading to cyan, "
        "zero warm tones — cold electric world"
    ),
    "darkpop": (
        "primary: rose neon #FF44AA, "
        "secondary: violet #7700CC, "
        "background: near-black purple #0D0018, "
        "accent: lilac #DDAAFF on light sources, "
        "silver-white moonlight rim — beautiful and haunting"
    ),
    "dark": (
        "background: absolute black #050508, "
        "single neon accent at 100% saturation — maximum purity"
    ),
    "default": (
        "primary: electric teal #00FFCC, "
        "secondary: hot magenta #FF00BB, "
        "background: deep black, maximum saturation"
    ),
}


# ═══════════════════════════════════════════════════════════════════════
# VIRAL HOOK MATRIX — primeiro frame por gênero
# ═══════════════════════════════════════════════════════════════════════

VIRAL_HOOK_MATRIX: dict[str, str] = {
    "phonk": (
        "SCROLL-STOP HOOK: extreme close-up anime face with violet glowing eyes filling frame, "
        "3am underground energy, VHS grain adding texture, "
        "single violet neon light source making everything else black"
    ),
    "trap": (
        "SCROLL-STOP HOOK: powerful anime face with crimson-gold glowing eyes dominating frame, "
        "smoke rising behind, urban royalty energy, "
        "gold and red neon as the only warmth in a black environment"
    ),
    "electronic": (
        "SCROLL-STOP HOOK: anime face with electric cyan glowing eyes and particle field, "
        "hypnotic forward energy, neon tunnel or geometry behind, "
        "cold electric precision in every detail"
    ),
    "darkpop": (
        "SCROLL-STOP HOOK: anime face with rose-purple glowing eyes, rain or mirror, "
        "beautiful emotional expression that hits before sound registers, "
        "loneliness made gorgeous"
    ),
    "dark": (
        "SCROLL-STOP HOOK: face emerging from near-total darkness, "
        "glowing eyes as only light source, maximum contrast"
    ),
    "default": (
        "SCROLL-STOP HOOK: anime face with vivid glowing eyes dominating frame, "
        "maximum contrast, dark background, readable at thumbnail distance"
    ),
}


# ═══════════════════════════════════════════════════════════════════════
# BACKGROUNDS — por gênero
# ═══════════════════════════════════════════════════════════════════════

GENRE_BACKGROUND_MATRIX: dict[str, list[str]] = {
    "phonk": [
        "pure black void with heavy violet neon rim light from behind, VHS grain throughout",
        "rain-soaked Japanese parking lot at 3am, sodium-violet overhead, wet concrete glow",
        "dark underground parking structure, purple neon tube lights, atmospheric fog",
        "mountain pass at night, tire smoke, violet neon reflections in wet asphalt",
        "cyberpunk alley, kanji purple neon signs overhead, mist at ankle level",
        "near-total darkness, single violet neon tube to the left, VHS static overlay",
    ],
    "trap": [
        "pure black with crimson-gold rim light, smoke drifting, brick texture behind",
        "urban rooftop at night, city lights sprawling below, gold-red haze in sky",
        "dark alley, single red streetlight above, gold neon from corner store",
        "black void with smoke and a single gold spotlight from directly above",
        "warehouse interior, red industrial lamp, single beam through smoke",
        "bridge underpass, city lights in water below, crimson neon from structure",
    ],
    "electronic": [
        "infinite cyan neon tunnel vanishing point behind character, particles floating",
        "deep navy void with teal particle field orbiting character",
        "aerial cyberpunk city in rain, cyan-magenta neon reflections everywhere",
        "abstract geometry space, crystalline torus, electric blue light on surfaces",
        "server corridor, blue-cyan LED strips, endless racks to vanishing point",
        "dark void with neon waveform terrain, electric blue peaks",
    ],
    "darkpop": [
        "dark room with large rainy window, purple-rose neon from outside through glass",
        "shattered mirror reflecting purple light, dark gothic surroundings",
        "empty gothic corridor, candles, moonlight through arched window",
        "near-black with single rose-purple spotlight from directly above",
        "rain-soaked rooftop, rose neon puddle reflections, city below",
        "abandoned greenhouse at night, cracked glass ceiling, moonlight silver-purple",
    ],
    "dark": [
        "absolute black with single neon accent rim from behind — maximum void",
        "near-total darkness, atmospheric fog, single neon source point",
    ],
    "default": [
        "dark cyberpunk void with neon rim light, atmospheric particles",
        "black void with electric neon accent from behind",
    ],
}


# ═══════════════════════════════════════════════════════════════════════
# GENRE BOOST — por gênero e tipo de personagem
# ═══════════════════════════════════════════════════════════════════════

GENRE_BOOST_MATRIX: dict[str, tuple[str, str]] = {
    "phonk": (
        "phonk 3am underground aesthetic — violet neon queen, "
        "VHS grain, Japanese street culture, feminine dominance",

        "phonk JDM king aesthetic — cold violet neon, "
        "drift culture, sigma male energy, VHS grain, underground power",
    ),
    "trap": (
        "trap luxury queen — crimson-gold neon royalty, "
        "urban dominance, beautiful and dangerous",

        "trap boss king — slow walk energy, "
        "crimson-gold status symbols, smoke, street royalty",
    ),
    "electronic": (
        "electronic cyber goddess — cyan particle field, "
        "futurist precision, cold electric deity",

        "electronic cyber warrior — teal neon, "
        "data combat, forward momentum, digital god",
    ),
    "darkpop": (
        "dark pop romantic — rose-purple neon loneliness, "
        "beautiful isolation, cinematic emotion",

        "dark pop warrior — strength through pain, "
        "neon warmth against purple cold, masculine emotion as power",
    ),
    "dark": (
        "dark mystery — single neon in void, apex feminine power",
        "dark power — void darkness, single neon, apex predator",
    ),
    "default": (
        "cyberpunk anime — dark neon, cinematic contrast, premium",
        "cyberpunk anime power — dark neon, maximum intensity",
    ),
}


def _get_genre_boost(genre: str, char_type: CharType) -> str:
    boosts = GENRE_BOOST_MATRIX.get(genre, GENRE_BOOST_MATRIX["default"])
    return boosts[0] if char_type == CharType.WAIFU else boosts[1]


# ═══════════════════════════════════════════════════════════════════════
# CHARACTER LIBRARY — WAIFUS (mantido do v52, lista completa)
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class CharacterEntry:
    name: str
    series: str
    char_type: CharType
    base_description: str
    signature_elements: list[str]
    power_phrase: str


WAIFU_CHARACTERS: list[CharacterEntry] = [
    CharacterEntry("Makima", "Chainsaw Man", CharType.WAIFU,
        "neat auburn hair in low braid, white dress shirt, rings of concentric glowing eyes",
        ["Control Devil leash chain glowing gold", "eerie perfect calm expression of total dominance",
         "concentric eye rings orbiting like satellites"],
        "Control Devil — everything was always hers"),

    CharacterEntry("Power", "Chainsaw Man", CharType.WAIFU,
        "wild blonde hair with iconic neon pink curved devil horns, casual streetwear",
        ["enormous chainsaw arm revving blood-red neon", "feral gap-toothed grin showing canines",
         "blood manipulation crimson armor plates"],
        "Blood Devil — pure chaos in a cute package"),

    CharacterEntry("Himiko Toga", "My Hero Academia", CharType.WAIFU,
        "twin blonde bun with loose strands, blood-drain gauntlets neon yellow",
        ["Transform quirk cycling through faces golden eyes shifting",
         "unhinged joyful dangerous smile", "knife held lovingly"],
        "Transform quirk — love is just wanting to become someone"),

    CharacterEntry("Zero Two", "DARLING in the FranXX", CharType.WAIFU,
        "long pink hair with iconic black horns glowing red neon, pilot suit",
        ["Strelizia FranXX silhouette looming behind",
         "wild confident predatory grin", "pink circuits running up arms like veins"],
        "Partner Killer — darling changed everything"),

    CharacterEntry("Ryuko Matoi", "Kill la Kill", CharType.WAIFU,
        "short black hair with red streak, Senketsu living uniform symbiosis",
        ["Scissor Blade crackling life fiber red energy",
         "defiant expression fighting the entire world", "life fiber veins glow red"],
        "Scissor Blade — she'll cut the universe in half"),

    CharacterEntry("Maki Zenin", "Jujutsu Kaisen", CharType.WAIFU,
        "short dark hair with medical tape on nose, special vision glasses neon green",
        ["naginata staff as massive cursed tool full length",
         "zero cursed energy making her invisible to detection",
         "physical dominance frame muscles catching neon"],
        "Zero cursed energy — pure physical apex"),

    CharacterEntry("Nobara Kugisaki", "Jujutsu Kaisen", CharType.WAIFU,
        "orange-brown bob hair with blunt cut, fierce expression",
        ["straw doll and nails crackling black cursed energy",
         "hammer raised mid-Black-Flash dark lightning",
         "blood splatter forming abstract neon patterns"],
        "Hammer and nails — ugly but effective"),

    CharacterEntry("Daki", "Demon Slayer", CharType.WAIFU,
        "very long silver-white hair with teal gradient tips, demon markings neon vein",
        ["obi sash weapon crystalline blade fans blood-crimson",
         "revealing kimono with living flesh-cloth patterns",
         "contemptuous demon slit pupils glowing red"],
        "Upper Moon Six — beauty that cuts everything"),

    CharacterEntry("Shinobu Kocho", "Demon Slayer", CharType.WAIFU,
        "long hair yellow-to-lavender, butterfly haori wings as holographic neon",
        ["needle-thin insect-venom sword crackling purple toxin",
         "soft closed-eye smile hiding total ruthlessness",
         "butterfly wing light constructs six feet wide"],
        "Insect Pillar — the smile that ends you before pain registers"),

    CharacterEntry("Raiden Shogun", "Genshin Impact", CharType.WAIFU,
        "long purple hair with traditional kanzashi, electro archon bearing",
        ["Musou Isshin sword electro nation technique",
         "divine electro power arcing off every surface",
         "Eternity ambition crackling purple neon"],
        "Electro Archon — Eternity is her divine right"),

    CharacterEntry("Hu Tao", "Genshin Impact", CharType.WAIFU,
        "long brown twin pigtails with teal ends, spirit-sensing crimson eyes",
        ["Paramita Papilio blood blossom ghost fire neon",
         "spirit butterfly orbiting crimson-gold",
         "mischievous funeral director expression"],
        "77th Director of Wangsheng Funeral Parlor — death is her business"),

    CharacterEntry("Kurumi Tokisaki", "Date A Live", CharType.WAIFU,
        "iconic half black half white long hair, clockwork eye and crimson eye",
        ["twin flintlocks dripping shadow particles and time-decay neon",
         "gothic lolita dress as cyberpunk time spirit armor",
         "time shadows of past-selves orbiting"],
        "Spirit of Time — she's already seen how this ends"),

    CharacterEntry("Yuno Gasai", "Future Diary", CharType.WAIFU,
        "long pink hair half-neat half-wild, yandere energy",
        ["diary phone glowing ominous pink-red",
         "yandere smile beautiful and cracked",
         "blood neon tear on cheek"],
        "Yandere goddess — first place in survival game, forever"),

    CharacterEntry("Yor Forger", "Spy x Family", CharType.WAIFU,
        "black hair with rose hairpin glowing blood-red, thorn crimson dress",
        ["twin needles crackling red neon Thorn Princess energy",
         "gentle smile hiding terrifying speed",
         "rose thorns extending from dress as actual blades"],
        "Thorn Princess — deadliest hands, warmest heart"),

    CharacterEntry("Violet Evergarden", "Violet Evergarden", CharType.WAIFU,
        "long golden blonde hair, auto memory doll uniform with prosthetic silver arms",
        ["typewriter keys floating as magical memory objects",
         "letter paper dissolving into butterfly flutter",
         "prosthetic arms glowing blue at joints"],
        "Auto Memory Doll — learning to feel through every letter"),

    CharacterEntry("Satsuki Kiryuin", "Kill la Kill", CharType.WAIFU,
        "very long black hair whipping dramatically, absolute supreme authority",
        ["Bakuzan sword crackling authority neon",
         "commanding presence making enemies kneel",
         "eyebrows expressing contempt"],
        "Iron Lady — I will have dominion"),

    CharacterEntry("Frieren", "Frieren: Beyond Journey's End", CharType.WAIFU,
        "long silver elf hair with ribbon ties, ancient eyes holding thousand years of grief",
        ["Zoltraak magic as casual finger-flick after thousand years",
         "cherry blossoms mixing with mana particles",
         "staff trailing afterimage of every spell cast"],
        "A thousand years of magic — still stopping for flowers"),

    CharacterEntry("Rem", "Re:Zero", CharType.WAIFU,
        "iconic short blue hair with hair clip, maid uniform as armored bodyguard",
        ["morning star flail crackling dense blue electricity",
         "Oni horn glowing blue releasing demon power",
         "tear-streaked fierce face of absolute devotion"],
        "Demon maid — devotion and destruction are the same thing"),

    CharacterEntry("Kaguya Shinomiya", "Kaguya-sama: Love is War", CharType.WAIFU,
        "impossibly long black hair with kanzashi pins glowing red neon",
        ["holographic data fan showing strategic analysis",
         "sharp manipulative intelligence in every movement",
         "battle-mind palace visualization twenty steps ahead"],
        "Ice Princess — she already won before you started"),

    CharacterEntry("Ai Hoshino", "Oshi no Ko", CharType.WAIFU,
        "long black hair with pink ends, idol stage presence",
        ["pink-gold star neon particles erupting from stage floor",
         "ruby and aquamarine stars forming in air",
         "smile that made entire nation fall in love"],
        "The brightest idol — her love was the realest lie"),
]


SHOUNEN_CHARACTERS: list[CharacterEntry] = [
    CharacterEntry("Gojo Satoru", "Jujutsu Kaisen", CharType.SHOUNEN,
        "iconic white hair styled back, Six Eyes cerulean blue through removed sunglasses",
        ["Unlimited Void domain expansion starfield consuming background",
         "Hollow Purple detonating reality", "Infinity distortion sphere curving space"],
        "Infinity — the honor of being the strongest"),

    CharacterEntry("Ryomen Sukuna", "Jujutsu Kaisen", CharType.SHOUNEN,
        "pink spiked hair, four arms, double set of eyes including cheek eyes open",
        ["Malevolent Shrine domain cleave cutting everything in kilometers",
         "black tattoos covering entire body glowing crimson",
         "king of curses in annihilated cathedral"],
        "King of Curses — the honor of being the strongest"),

    CharacterEntry("Itachi Uchiha", "Naruto", CharType.SHOUNEN,
        "long black hair in iconic low ponytail, mangekyo spinning blood-red",
        ["Amaterasu black inextinguishable flames from eye",
         "Susanoo ribcage with Yata Mirror and Totsuka Blade",
         "greatest sacrifice hero looking like greatest villain"],
        "Crow Genjutsu — he loved the village more than himself"),

    CharacterEntry("Madara Uchiha", "Naruto", CharType.SHOUNEN,
        "long black hair, Ten-Tails Jinchuriki god of the shinobi world",
        ["Limbo Hengoku shadow clones from underworld",
         "Truth-Seeking Orbs 72 black spheres orbiting",
         "god-tier Sage of Six Paths surpassing all limits"],
        "Madara Uchiha — the only man who could make the moon his eye"),

    CharacterEntry("Ichigo Kurosaki", "Bleach", CharType.SHOUNEN,
        "spiky orange hair wild with spiritual pressure, all three powers fused",
        ["True Shikai Zangetsu cleave dwarfing mountains",
         "Final Getsuga Tensho Mugetsu erasing light",
         "inner hollow and Quincy and shinigami fused"],
        "King of Souls — Shinigami, Hollow, Quincy. All three."),

    CharacterEntry("Sosuke Aizen", "Bleach", CharType.SHOUNEN,
        "neat brown hair ultimate butterfly transcendence form",
        ["Kyoka Suigetsu shatter-illusion reality fracture",
         "Hogyoku in chest glowing all-seeing purple neon",
         "calm smile of someone who won before the fight began"],
        "Complete Hypnosis — he never lost. He was never in danger."),

    CharacterEntry("Sung Jinwoo", "Solo Leveling", CharType.SHOUNEN,
        "dark hair, empty emotionless hunter eyes, Shadow Monarch power",
        ["shadow army millions marching as dark silhouettes",
         "Kamish Wrath sword of shadows reaping arc",
         "Igris and Beru flanking as massive shadow knight commanders"],
        "Shadow Monarch — slept while everyone trained, woke up strongest"),

    CharacterEntry("Guts", "Berserk", CharType.SHOUNEN,
        "massive Dragon Slayer sword in one arm containing a cannon",
        ["Berserker Armor activated bleeding from joints",
         "Brand of Sacrifice wound bleeding black in presence of demons",
         "mad dog grin refusing death because death means fate wins"],
        "Black Swordsman — the brand burns. he runs toward it."),

    CharacterEntry("Luffy (Gear Fifth)", "One Piece", CharType.SHOUNEN,
        "wild black hair turning white, Gear Fifth deity form white cloud aura",
        ["rubber reality-warping deity making island cartoonish in battle",
         "fist enlarged to city-block scale mid-punch",
         "Sun God Nika form laughing while outputting god-tier power"],
        "Sun God Nika — the joy of freedom made flesh"),

    CharacterEntry("Goku (Ultra Instinct)", "Dragon Ball", CharType.SHOUNEN,
        "silver-white hair with glowing silver UI aura corona",
        ["Ultra Instinct movement defeating gods with pure reactive grace",
         "silver neon aura producing heatwave distorting atmosphere",
         "calm as water surface despite universe-shattering output"],
        "Ultra Instinct — even the gods can't keep up"),

    CharacterEntry("Vegeta (Ultra Ego)", "Dragon Ball", CharType.SHOUNEN,
        "widow-peak dark hair, dark purple Ultra Ego aura consuming all light",
        ["power that increases the more damage received",
         "Ultra Ego symbol consuming background light",
         "pride of a Saiyan Prince who never yielded"],
        "Ultra Ego — pride is his power source"),

    CharacterEntry("Anos Voldigoad", "Misfit of Demon King Academy", CharType.SHOUNEN,
        "dark hair, demon king reincarnated surpassing all records",
        ["Venuzdonoa sword of ruin destroying cause and effect",
         "absolute overwhelming power in casual clothing",
         "demon king who transcended death still dominates"],
        "Demon King — he destroyed even death"),

    CharacterEntry("Garou (Cosmic Fear)", "One Punch Man", CharType.SHOUNEN,
        "white hair spiked wild in Cosmic Fear Mode, God Power absorbed",
        ["God Power star-level output crackling everywhere",
         "Gravity techniques bending space with lens distortion",
         "copying every martial art into Godly Fist"],
        "Cosmic Garou — the strongest monster who became the greatest hero"),

    CharacterEntry("Tanjiro Kamado", "Demon Slayer", CharType.SHOUNEN,
        "short black hair with burgundy tips, Hinokami Kagura Sun Breathing active",
        ["Sun Breathing flame wheel spiral crimson gold consuming frame",
         "Nichirin blade coated in solar plasma fire",
         "tear and fire on face — determination distilled"],
        "Sun Breathing — the original technique that can kill demons"),

    CharacterEntry("Eren Yeager", "Attack on Titan", CharType.SHOUNEN,
        "wild dark hair, Founding Titan colossus emerging from earth",
        ["Founding Titan 80-meter skeletal deity rising",
         "Wall Titans marching in thousands answering the Rumble",
         "hollow screaming while collateral damage becomes history"],
        "Founding Titan — freedom at any cost"),
]

ALL_CHARACTERS = WAIFU_CHARACTERS + SHOUNEN_CHARACTERS

# Tier 1 por gênero — maior comunidade = mais engajamento
PHONK_TRAP_TIER1_WAIFUS = ["Makima", "Himiko Toga", "Power", "Zero Two", "Maki Zenin", "Daki", "Kurumi Tokisaki", "Yuno Gasai", "Raiden Shogun", "Hu Tao"]
ELECTRONIC_TIER1_WAIFUS = ["Raiden Shogun", "Frieren", "Rem", "Zero Two", "Violet Evergarden"]
DARKPOP_TIER1_WAIFUS = ["Violet Evergarden", "Frieren", "Yor Forger", "Ai Hoshino", "Rem"]

PHONK_TRAP_TIER1_SHOUNEN = ["Gojo Satoru", "Ryomen Sukuna", "Itachi Uchiha", "Madara Uchiha", "Sung Jinwoo", "Guts"]
ELECTRONIC_TIER1_SHOUNEN = ["Gojo Satoru", "Anos Voldigoad", "Goku (Ultra Instinct)"]
DARKPOP_TIER1_SHOUNEN = ["Itachi Uchiha", "Guts", "Eren Yeager", "Garou (Cosmic Fear)"]


def _select_viral_character(rng: random.Random, genre: str, char_type: CharType) -> CharacterEntry:
    use_tier1 = rng.random() < 0.70
    if use_tier1:
        if char_type == CharType.WAIFU:
            names = PHONK_TRAP_TIER1_WAIFUS if genre in ("phonk", "trap", "dark") else \
                    ELECTRONIC_TIER1_WAIFUS if genre == "electronic" else DARKPOP_TIER1_WAIFUS
            tier1 = [c for c in WAIFU_CHARACTERS if c.name in names]
        else:
            names = PHONK_TRAP_TIER1_SHOUNEN if genre in ("phonk", "trap", "dark") else \
                    ELECTRONIC_TIER1_SHOUNEN if genre == "electronic" else DARKPOP_TIER1_SHOUNEN
            tier1 = [c for c in SHOUNEN_CHARACTERS if c.name in names]
        if tier1:
            return rng.choice(tier1)
    pool = WAIFU_CHARACTERS if char_type == CharType.WAIFU else SHOUNEN_CHARACTERS
    return rng.choice(pool)


# ═══════════════════════════════════════════════════════════════════════
# EMOTION SYSTEM
# ═══════════════════════════════════════════════════════════════════════

WAIFU_EMOTION_PROFILES: dict[EmotionArchetype, dict] = {
    EmotionArchetype.COLD_QUEEN: {
        "face": "cold imperious expression, eyes half-lidded with absolute contempt, jaw slightly raised",
        "body": "arms crossed, weight on one hip",
        "energy": "cool violet-blue aura barely visible", "aura_color": "icy blue",
    },
    EmotionArchetype.YANDERE_SMILE: {
        "face": "beautiful unhinged smile — warm and adoring on one side, empty hunter on the other",
        "body": "slightly tilted head, one hand raised delicately",
        "energy": "pink-to-crimson neon shifting between love and danger",
        "aura_color": "rose crimson",
    },
    EmotionArchetype.SEDUCTIVE_GAZE: {
        "face": "heavy-lidded neon eyes with multiple catchlights, soft parted lips",
        "body": "elegant contrapposto with weight shift",
        "energy": "warm rose-gold neon", "aura_color": "rose gold",
    },
    EmotionArchetype.DOMINANT_VIBE: {
        "face": "sharp knowing smirk, eyes radiating absolute confidence",
        "body": "power stance — ready for anything",
        "energy": "intense electric neon aura", "aura_color": "electric white",
    },
    EmotionArchetype.PLAYFUL_DANGER: {
        "face": "bright mischievous grin concealing real threat",
        "body": "playful lean-in with finger raised",
        "energy": "pastel neon sparking chaotically", "aura_color": "neon pastel chaos",
    },
    EmotionArchetype.ETHEREAL_SORROW: {
        "face": "beautiful melancholy, distant gorgeous eyes carrying ancient grief",
        "body": "graceful stillness, floating slightly",
        "energy": "soft silver-blue neon dissolving at edges", "aura_color": "silver moonlight",
    },
    EmotionArchetype.BATTLE_FURY: {
        "face": "intense battle expression, locked on target, eyes burning",
        "body": "aggressive forward lean, weapon raised",
        "energy": "explosive neon aura crackling at every joint", "aura_color": "fierce crimson gold",
    },
    EmotionArchetype.SOFT_OBSESSION: {
        "face": "soft devoted expression, loving eyes a little too intense",
        "body": "arms slightly open as if ready to embrace",
        "energy": "warm amber-pink neon with dark undertone", "aura_color": "warm amber dark edge",
    },
}

SHOUNEN_EMOTION_PROFILES: dict[EmotionArchetype, dict] = {
    EmotionArchetype.COLD_RAGE: {
        "face": "controlled fury, perfectly still face with eyes burning cold like reactor cores",
        "body": "absolute stillness more threatening than any movement",
        "energy": "dark neon suppressed at edge — about to stop suppressing",
        "aura_color": "dark crimson barely contained",
    },
    EmotionArchetype.I_AM_HIM: {
        "face": "calm total confidence, energy of someone who already knows they've won",
        "body": "dominant slow walk toward camera, unhurried",
        "energy": "massive aura crackling without effort",
        "aura_color": "blazing gold-white",
    },
    EmotionArchetype.FINAL_FORM: {
        "face": "limit break expression, screaming or gritting teeth, veins visible",
        "body": "maximum power pose, every muscle tensed",
        "energy": "catastrophic multi-color power eruption consuming entire frame",
        "aura_color": "multi-spectrum neon catastrophe",
    },
    EmotionArchetype.SILENT_APEX: {
        "face": "emotionless apex predator, no expression needed",
        "body": "weapon at rest, relaxed posture hiding terrifying power",
        "energy": "barely-visible aura distorting light and gravity",
        "aura_color": "invisible distortion with neon edge",
    },
}


def get_emotion_prompt(archetype: EmotionArchetype, char_type: CharType) -> str:
    if char_type == CharType.WAIFU:
        profile = WAIFU_EMOTION_PROFILES.get(archetype, WAIFU_EMOTION_PROFILES[EmotionArchetype.DOMINANT_VIBE])
    else:
        profile = SHOUNEN_EMOTION_PROFILES.get(archetype, SHOUNEN_EMOTION_PROFILES[EmotionArchetype.I_AM_HIM])
    return (
        f"emotion: {profile['face']}, "
        f"body language: {profile['body']}, "
        f"energy: {profile['energy']}, "
        f"dominant aura color: {profile['aura_color']}"
    )


WAIFU_EMOTION_WEIGHTS = [
    (EmotionArchetype.COLD_QUEEN, 22), (EmotionArchetype.YANDERE_SMILE, 18),
    (EmotionArchetype.SEDUCTIVE_GAZE, 20), (EmotionArchetype.DOMINANT_VIBE, 16),
    (EmotionArchetype.PLAYFUL_DANGER, 12), (EmotionArchetype.ETHEREAL_SORROW, 4),
    (EmotionArchetype.BATTLE_FURY, 6), (EmotionArchetype.SOFT_OBSESSION, 2),
]

SHOUNEN_EMOTION_WEIGHTS = [
    (EmotionArchetype.COLD_RAGE, 18), (EmotionArchetype.I_AM_HIM, 32),
    (EmotionArchetype.FINAL_FORM, 35), (EmotionArchetype.SILENT_APEX, 15),
]


def _weighted_emotion(rng: random.Random, char_type: CharType) -> EmotionArchetype:
    weights = WAIFU_EMOTION_WEIGHTS if char_type == CharType.WAIFU else SHOUNEN_EMOTION_WEIGHTS
    total = sum(w for _, w in weights)
    r = rng.random() * total
    acc = 0.0
    for archetype, weight in weights:
        acc += weight
        if r <= acc:
            return archetype
    return weights[0][0]


# ═══════════════════════════════════════════════════════════════════════
# LIGHTING STACKS — melhorados para close-up
# ═══════════════════════════════════════════════════════════════════════

LIGHTING_STACKS: list[dict] = [
    {
        "name": "split_neon_face",
        "prompt": (
            "SPLIT NEON FACE LIGHTING — primary colored neon rim hitting one cheek from behind, "
            "sculpting jaw and cheekbone with hard colored light edge, "
            "secondary fill neon from opposite side at 20% intensity, "
            "technique glow or power glow illuminating eye area from slightly below, "
            "CATCHLIGHTS: minimum 5 distinct points in each iris — all different colors, "
            "skin gains depth through colored shadow interaction"
        ),
    },
    {
        "name": "power_backlight",
        "prompt": (
            "POWER BACKLIGHT STACK — overwhelming aura from behind creates perfect silhouette rim, "
            "single power glow from below and slightly forward lights face dramatically, "
            "face lit exclusively by own power — dramatic, readable, "
            "eyes catching technique color as bright internal glow, "
            "CATCHLIGHTS: three bright neon points plus one wide diffuse reflection"
        ),
    },
    {
        "name": "dramatic_underlighting",
        "prompt": (
            "DRAMATIC UNDERLIGHTING — primary neon source from below chin, "
            "casting deep shadows upward across face — the most dramatic face lighting, "
            "eyes catch under-light as intense upward-facing catchlights, "
            "hair silhouetted against dark above, "
            "single rim light from behind creating separation from background"
        ),
    },
    {
        "name": "noir_neon_split",
        "prompt": (
            "NOIR NEON SPLIT — hard colored neon slivers cutting through 80% shadow, "
            "face 60% in absolute shadow, 40% in vivid neon light — maximum drama, "
            "eyes MUST catch the neon even in shadow — they glow internally, "
            "high contrast maximum — deepest darks and brightest neons sharing frame, "
            "no fill light — hard single source only"
        ),
    },
    {
        "name": "divine_close_glow",
        "prompt": (
            "DIVINE CLOSE GLOW — character is own light source, power radiating outward, "
            "face glowing from within as if deity revealing true form, "
            "halo rim effect from behind completing divine presence, "
            "eyes as absolute brightest point in frame — power visible in the iris, "
            "surrounding air slightly distorted by power heat"
        ),
    },
]

LIGHTING_WEIGHTS = [25, 25, 20, 18, 12]


def _select_lighting(rng: random.Random) -> str:
    total = sum(LIGHTING_WEIGHTS)
    r = rng.random() * total
    acc = 0.0
    for stack, weight in zip(LIGHTING_STACKS, LIGHTING_WEIGHTS):
        acc += weight
        if r <= acc:
            return stack["prompt"]
    return LIGHTING_STACKS[0]["prompt"]


# ═══════════════════════════════════════════════════════════════════════
# PARTICLE TIERS
# ═══════════════════════════════════════════════════════════════════════

PARTICLE_TIER_MEDIUM = (
    "PARTICLE DENSITY MEDIUM — hundreds of neon particles orbiting in readable pattern, "
    "technique-specific type matching power color, small debris field"
)

PARTICLE_TIER_HEAVY = (
    "PARTICLE DENSITY HEAVY — thousands of neon particles creating galaxy density, "
    "layered depth: foreground large, midground dense, background bokeh, "
    "shockwave rings visible, speed blur streaks"
)

PARTICLE_TIER_CATASTROPHIC = (
    "PARTICLE DENSITY CATASTROPHIC — overwhelming storm consuming frame edges, "
    "character at perfect calm center, "
    "layered: foreground particle sheets, midground explosion, background bokeh, "
    "shockwave rings + lightning web + debris simultaneously"
)

PARTICLE_TIERS = [
    ("medium", PARTICLE_TIER_MEDIUM, 15, 10),
    ("heavy", PARTICLE_TIER_HEAVY, 50, 35),
    ("catastrophic", PARTICLE_TIER_CATASTROPHIC, 35, 55),
]


def _select_particle_tier(rng: random.Random, char_type: CharType) -> str:
    w_idx = 2 if char_type == CharType.WAIFU else 3
    total = sum(t[w_idx] for t in PARTICLE_TIERS)
    r = rng.random() * total
    acc = 0.0
    for name, prompt, ww, sw in PARTICLE_TIERS:
        acc += (ww if char_type == CharType.WAIFU else sw)
        if r <= acc:
            return prompt
    return PARTICLE_TIER_HEAVY


# ═══════════════════════════════════════════════════════════════════════
# LOOP HINTS
# ═══════════════════════════════════════════════════════════════════════

LOOP_DESIGN_HINTS: dict[str, str] = {
    "phonk": "LOOP: VHS grain and particle drift bridge loop point invisibly, cowbell rhythm supports visual loop",
    "trap": "LOOP: smoke drift creates natural continuity across loop point",
    "electronic": "LOOP: particle field or tunnel returns to start seamlessly, hypnotic loop drives replays",
    "darkpop": "LOOP: rain continues across loop, emotional weight makes viewers replay",
    "dark": "LOOP: neon flicker or atmospheric drift bridges loop invisibly",
    "default": "LOOP: ambient elements bridge loop cut naturally",
}

# ═══════════════════════════════════════════════════════════════════════
# [FIX 7] NEGATIVE PROMPT EXPANDIDO
# ═══════════════════════════════════════════════════════════════════════

NEGATIVE_PROMPT = (
    # Qualidade
    "ugly, bad anatomy, bad face, asymmetrical eyes, distorted face, "
    "bad hands, extra fingers, missing fingers, fused limbs, broken limbs, "
    "melted face, uncanny valley, bad proportions, deformed body, "
    "blurry, low quality, jpeg artifacts, heavy noise, "
    "photorealistic, 3D render, CGI, doll face, plastic skin, "
    "western cartoon, childish art, "
    # Conteúdo
    "nude, explicit nudity, nipples, genitalia, "
    "multiple characters, crowd, two people, duplicate, "
    "text overlay, words in image, logo, watermark, "
    # [FIX 7] Killer de views — personagem pequeno e sem rosto
    "character too small in frame, tiny character, "
    "face too small to read, face hidden, face turned away completely, "
    "full back view with no face visible, "
    "character lost in background, character too far from camera, "
    "busy composition with no clear focal point, "
    "muddy colors, washed out bloom, desaturated, "
    "gray haze obscuring face, fog covering features, "
    "low saturation neon, dull neon, muted colors, "
    "bright background, light background, white background, pastel background, "
    "happy cheerful bright pop aesthetic, "
    "forgettable frame, generic soulless anime, "
    "amateur editing, unprofessional output, "
    "stock photo energy, no focal point"
)

GENERATION_SUFFIX = (
    ", beautiful detailed anime character, expressive neon-lit face with glowing eyes, "
    "cinematic dark neon lighting, vivid saturated colors maximum contrast, "
    "face and eyes clearly visible and dominant in frame, "
    "professional anime illustration apex quality, "
    "no text, no watermark, vertical 9:16"
)


# ═══════════════════════════════════════════════════════════════════════
# IDENTITY LOCKS
# ═══════════════════════════════════════════════════════════════════════

CHANNEL_IDENTITY = (
    "DJ Dark Mark viral anime music Shorts visual — "
    "scroll-stopping 9:16 thumbnail, glowing eyes as primary hook, "
    "dark neon underground premium aesthetic"
)

WAIFU_CORE_CHARACTER = (
    "one beautiful anime girl as SOLE subject, "
    "gorgeous detailed anime face dominant in frame, "
    "expressive neon-lit eyes with 5+ vivid catchlights, "
    "detailed hair with individual strand neon reflections, "
    "complete signature outfit with cyberpunk detail, "
    "FACE MUST BE CLEARLY READABLE AT SMALL THUMBNAIL SIZE"
)

SHOUNEN_CORE_CHARACTER = (
    "one powerful anime male character as SOLE subject, "
    "intense detailed anime face dominant in frame, "
    "strong masculine frame with power-lit eyes CLEARLY READABLE at thumbnail, "
    "detailed hair catching neon and power-effect lighting, "
    "complete outfit with cyberpunk/power enhancement, "
    "FACE MUST BE VISIBLE AND READABLE — NOT HIDDEN"
)

STYLE_LOCK = (
    "PREMIUM cyberpunk anime illustration at maximum quality, "
    "ultra-clean professional lineart, polished studio finish, "
    "cel shading with multi-source rim lighting, "
    "glossy hyper-detailed eyes with 5+ catchlights, "
    "rich maximally-saturated neon colors with extreme contrast shadows, "
    "NOT photorealistic, NOT 3D, NOT western — pure anime apex"
)

QUALITY_LOCK = (
    "ultra-hyper detailed, crisp lineart, correct anatomy, "
    "extreme resolution detail on face especially eyes, "
    "perfect cinematic color grading, "
    "face and eyes as highest-detail region in frame, "
    "vertical 9:16 mobile format, no text, no logo, no watermark"
)

MOTION_LOCK = (
    "sense of power and motion — "
    "hair caught in technique wind, speed blur streaks, "
    "impact shockwave rings, neon energy crackling off body"
)


# ═══════════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════════

def _compact(text: str, max_len: int = 3200) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace(" ,", ",").replace(",,", ",")
    return text[:max_len].rstrip(" ,")


def _clean_song_name(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(r"[_\-]+", " ", name)
    return name.strip()


def _make_seed(genre: str, filename: str, short_num: int) -> int:
    key = f"{genre}|{filename}|{short_num}|darkmark_{VERSION}"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % (10 ** 9)


def _make_rng(genre: str, filename: str, short_num: int) -> random.Random:
    return random.Random(_make_seed(genre, filename, short_num))


def _analyze_song_mood(song_name: str, char_type: CharType) -> str:
    clean = song_name.lower()
    base = "feminine" if char_type == CharType.WAIFU else "masculine"
    if any(w in clean for w in ["dark", "shadow", "night", "noite", "darkness"]):
        return f"haunted neon {base} power, night as ally"
    if any(w in clean for w in ["fire", "burn", "rage", "fogo", "chama"]):
        return f"contained {base} fire radiating as heat"
    if any(w in clean for w in ["love", "heart", "amor", "rose"]):
        return f"dark romantic {base} longing in neon city"
    if any(w in clean for w in ["drive", "speed", "drift", "fast"]):
        return f"velocity {base} body mid-movement with speed blur"
    if any(w in clean for w in ["queen", "king", "boss", "power", "apex"]):
        return f"dominant {base} god-tier aura claiming space"
    if any(w in clean for w in ["cold", "ice", "freeze", "frio", "gelo"]):
        return f"cold precision absolute {base} control"
    return f"intense {base} cyberpunk magnetic presence"


MUSIC_ELEMENTS = [
    "cyberpunk headphones around neck glowing neon — rhythm synchronized with power",
    "wireless neon earbud catching colored light",
    "holographic music waveform pulsing in background",
    "emotional body language IS the music — cinematic silence",
]


# ═══════════════════════════════════════════════════════════════════════
# [FIX 6] CLAUDE PROMPT — reescrito com foco no rosto e olhos
# ═══════════════════════════════════════════════════════════════════════

def _build_claude_enhanced_prompt(
    char: CharacterEntry,
    genre: str,
    composition: dict,
    emotion: EmotionArchetype,
    lighting: str,
    background: str,
    palette: str,
    genre_boost: str,
    eye_glow: str,
    song_name: str,
    song_mood: str,
    loop_hint: str,
    char_type: CharType,
) -> Optional[str]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        gender_word = "young woman" if char_type == CharType.WAIFU else "young man"
        eye_shape = EYE_SHAPE_WAIFU if char_type == CharType.WAIFU else EYE_SHAPE_SHOUNEN

        system = (
            "You are the visual director of DJ Dark Mark, a viral YouTube Shorts music channel. "
            "Your job: write Flux image prompts that stop people from scrolling in under 1 second.\n\n"
            "CRITICAL INSIGHT from channel data:\n"
            "- Close-up face with glowing eyes = 113 views (best performer)\n"
            "- Back view / tiny character = 2 views (worst performer)\n"
            "- The FACE and EYES must dominate the frame. Always.\n\n"
            "RULES (non-negotiable):\n"
            "1. Face must fill at least 40% of the 9:16 frame — no tiny characters\n"
            "2. Glowing neon eyes are the PRIMARY scroll-stop element — describe them in detail\n"
            "3. Dark background ALWAYS — the channel is dark neon aesthetic\n"
            "4. ONE anime character only — no crowds, no extra people\n"
            "5. Anime illustration style — NOT photorealistic, NOT 3D\n"
            "6. Maximum color saturation — no muddy or washed-out neon\n"
            "7. No text, watermarks, logos in image\n"
            "8. Output ONLY the prompt in English, 100-150 words, no preamble."
        )

        user = (
            f"Write a Flux prompt for a {genre} music YouTube Short.\n\n"
            f"Character: {char.name} from {char.series}\n"
            f"Description: {char.base_description}\n"
            f"Signature: {char.signature_elements[0]}\n"
            f"Identity: {char.power_phrase}\n\n"
            f"Composition: {composition['prompt'][:80]}\n"
            f"Eye glow style: {eye_glow[:120]}\n"
            f"Eye shape: {eye_shape}\n"
            f"Lighting: {lighting[:100]}\n"
            f"Background: {background[:100]}\n"
            f"Colors: {palette[:100]}\n"
            f"Vibe: {genre_boost[:100]}\n"
            f"Song: {song_name}, mood: {song_mood}\n\n"
            f"PRIORITY ORDER for the prompt:\n"
            f"1. Describe the FACE and EYES first and in most detail\n"
            f"2. Describe the glowing eye color and catchlights\n"
            f"3. Describe the lighting sculpting the face\n"
            f"4. Describe background and color palette\n"
            f"5. Mention signature outfit/power element\n\n"
            f"One {gender_word}, anime style, dark neon, {genre} aesthetic, face dominant in frame."
        )

        resp = client.messages.create(
            model=get_anthropic_model(),
            max_tokens=350,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        prompt = resp.content[0].text.strip().strip('"').strip("'")
        logger.info(f"[Claude] Prompt gerado: {len(prompt)} chars")
        return _compact(prompt, max_len=2000)

    except Exception as e:
        logger.warning(f"[Claude] Falha: {e} — usando fallback")
        return None


# ═══════════════════════════════════════════════════════════════════════
# PROMPT ASSEMBLER — fallback sem Claude
# ═══════════════════════════════════════════════════════════════════════

def _assemble_prompt(
    char: CharacterEntry,
    composition: dict,
    emotion: EmotionArchetype,
    lighting: str,
    particle: str,
    background: str,
    palette: str,
    genre_boost: str,
    eye_glow: str,
    eye_shape: str,
    genre_color_punch: str,
    song_name: str,
    song_mood: str,
    loop_hint: str,
    music_element: str,
    char_type: CharType,
) -> str:
    core = WAIFU_CORE_CHARACTER if char_type == CharType.WAIFU else SHOUNEN_CORE_CHARACTER
    emotion_text = get_emotion_prompt(emotion, char_type)
    char_block = (
        f"{char.name} from {char.series}, "
        f"{char.base_description}, "
        f"signature: {char.signature_elements[0]}, "
        f"identity: {char.power_phrase}"
    )

    parts = [
        CHANNEL_IDENTITY, CHANNEL_DNA, core, char_block,
        f"COMPOSITION: {composition['prompt']}",
        f"EYES — HIGHEST PRIORITY: {eye_glow}",
        f"eye shape: {eye_shape}",
        emotion_text,
        lighting, particle, MOTION_LOCK,
        f"background: {background}",
        f"COLOR PALETTE: {palette}",
        genre_color_punch,
        f"genre vibe: {genre_boost}",
        f"music: {music_element}",
        f"song: {song_name}, mood: {song_mood}",
        THUMBNAIL_CONTRAST_LOCK,
        loop_hint,
        STYLE_LOCK, QUALITY_LOCK,
    ]

    return _compact(", ".join(p.strip().strip(",") for p in parts if p.strip()), max_len=3200)


# ═══════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════

def build_ai_prompt(
    style: str = "phonk",
    filename: str = "song.mp3",
    short_num: int = 1,
    force_waifu: bool = False,
    force_shounen: bool = False,
    use_claude: bool = True,
    styles: Optional[list] = None,
    char_type=None,
    force_teal_pink: bool = False,
    force_purple_gold: bool = False,
    force_crimson_blue: bool = False,
    force_full_body: bool = False,
) -> str:

    mapped_genre = GENRE_MAP.get(style.lower().strip(), "default")
    rng = _make_rng(mapped_genre, filename, short_num)
    song_name = _clean_song_name(filename)

    # Tipo de personagem — waifu 65% cross-gender
    if force_waifu:
        selected_type = CharType.WAIFU
    elif force_shounen:
        selected_type = CharType.SHOUNEN
    else:
        selected_type = CharType.WAIFU if rng.random() < 0.65 else CharType.SHOUNEN

    char = _select_viral_character(rng, mapped_genre, selected_type)

    # Composição — close-up tem peso 45%
    if force_full_body:
        comp = next(c for c in COMPOSITION_STYLES if c["name"] == "full_body_power")
    else:
        comp = _weighted_composition(rng, selected_type)

    emotion  = _weighted_emotion(rng, selected_type)
    lighting = _select_lighting(rng)
    particle = _select_particle_tier(rng, selected_type)

    bgs = GENRE_BACKGROUND_MATRIX.get(mapped_genre, GENRE_BACKGROUND_MATRIX["default"])
    background = rng.choice(bgs)

    palette = GENRE_PALETTE_LOCK.get(mapped_genre, GENRE_PALETTE_LOCK["default"])
    genre_boost = _get_genre_boost(mapped_genre, selected_type)
    genre_color_punch = GENRE_COLOR_PUNCH.get(mapped_genre, GENRE_COLOR_PUNCH["default"])

    eye_glow = EYE_GLOW_BY_GENRE.get(mapped_genre, EYE_GLOW_BY_GENRE["default"])
    eye_shape = EYE_SHAPE_WAIFU if selected_type == CharType.WAIFU else EYE_SHAPE_SHOUNEN

    song_mood = _analyze_song_mood(song_name, selected_type)
    music_element = rng.choice(MUSIC_ELEMENTS)
    loop_hint = LOOP_DESIGN_HINTS.get(mapped_genre, LOOP_DESIGN_HINTS["default"])

    if use_claude:
        claude_prompt = _build_claude_enhanced_prompt(
            char=char, genre=mapped_genre, composition=comp, emotion=emotion,
            lighting=lighting, background=background, palette=palette,
            genre_boost=genre_boost, eye_glow=eye_glow,
            song_name=song_name, song_mood=song_mood, loop_hint=loop_hint,
            char_type=selected_type,
        )
        if claude_prompt:
            return claude_prompt

    return _assemble_prompt(
        char=char, composition=comp, emotion=emotion,
        lighting=lighting, particle=particle, background=background,
        palette=palette, genre_boost=genre_boost, eye_glow=eye_glow,
        eye_shape=eye_shape, genre_color_punch=genre_color_punch,
        song_name=song_name, song_mood=song_mood, loop_hint=loop_hint,
        music_element=music_element, char_type=selected_type,
    )


def build_viral_short_prompt(
    genre: str,
    song_filename: str,
    short_num: int = 1,
    force_waifu: bool = False,
    force_shounen: bool = False,
    use_claude: bool = True,
) -> str:
    logger.info(f"[VIRAL v53] genre={genre} | short={short_num}")
    return build_ai_prompt(
        style=genre, filename=song_filename, short_num=short_num,
        force_waifu=force_waifu, force_shounen=force_shounen,
        use_claude=use_claude,
    )


def build_waifu_prompt(style: str = "phonk", short_num: int = 1, filename: str = "song.mp3") -> str:
    return build_ai_prompt(style=style, filename=filename, short_num=short_num, force_waifu=True)


def build_shounen_prompt(style: str = "phonk", short_num: int = 1, filename: str = "song.mp3") -> str:
    return build_ai_prompt(style=style, filename=filename, short_num=short_num, force_shounen=True)


# ═══════════════════════════════════════════════════════════════════════
# IMAGE GENERATION
# ═══════════════════════════════════════════════════════════════════════

SAVE_DIR = Path("temp")


def generate_image(prompt: str, output_path: Optional[str] = None) -> Optional[str]:
    if not REPLICATE_API_TOKEN:
        logger.error("❌ REPLICATE_API_TOKEN não configurado!")
        return None

    output_path = output_path or str(SAVE_DIR / f"ai_bg_{int(time.time())}.png")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    full_prompt = _compact(prompt + GENERATION_SUFFIX, max_len=3500)
    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
        "Prefer": "wait",
    }
    base_seed = random.randint(1000, 999_999)

    for model_idx, model in enumerate(REPLICATE_MODELS):
        if "flux-dev" in model:
            model_input = {
                **FLUX_DEV_PARAMS,
                "prompt": full_prompt,
                "negative_prompt": NEGATIVE_PROMPT,
                "seed": base_seed + model_idx,
            }
        else:
            model_input = {**FLUX_SCHNELL_PARAMS, "prompt": full_prompt, "seed": base_seed + model_idx}

        for attempt in range(1, 4):
            try:
                logger.info(f"[Replicate] Tentativa {attempt}/3 — {model.split('/')[-1]}")
                resp = requests.post(
                    f"https://api.replicate.com/v1/models/{model}/predictions",
                    headers=headers, json={"input": model_input}, timeout=45,
                )
                resp.raise_for_status()
                pred = resp.json()
                poll_url = pred.get("urls", {}).get("get") or f"https://api.replicate.com/v1/predictions/{pred['id']}"

                for poll in range(180):
                    time.sleep(2.0 if poll < 30 else 3.0)
                    sr = requests.get(poll_url, headers=headers, timeout=30)
                    sr.raise_for_status()
                    data = sr.json()
                    status = data.get("status")

                    if status == "succeeded":
                        output = data.get("output")
                        image_url = output[0] if isinstance(output, list) else output
                        if not image_url:
                            raise RuntimeError("Output vazio")
                        img_resp = requests.get(image_url, timeout=90)
                        img_resp.raise_for_status()
                        Path(output_path).write_bytes(img_resp.content)
                        size = Path(output_path).stat().st_size
                        if size < 80_000:
                            Path(output_path).unlink(missing_ok=True)
                            raise RuntimeError(f"Imagem pequena: {size} bytes")
                        logger.info(f"✅ Salvo: {output_path} ({size // 1024}KB)")
                        return output_path
                    if status == "failed":
                        raise RuntimeError(data.get("error", "Erro"))
                    if status not in ("starting", "processing"):
                        raise RuntimeError(f"Status: {status}")

            except Exception as e:
                wait = 4 * attempt
                logger.error(f"[Replicate] Tentativa {attempt} falhou: {e}. Aguardando {wait}s…")
                model_input["seed"] = base_seed + model_idx + attempt * 37
                time.sleep(wait)

    logger.error("❌ Todas as tentativas falharam")
    return None


def generate_background_image(
    style: str = "phonk",
    output_path: str = "assets/background.png",
    seed_variant: int = 0,
    max_retries: int = 3,
    force_waifu: bool = False,
    force_shounen: bool = False,
    **kwargs,
) -> Optional[str]:
    prompt = build_ai_prompt(
        style=style, filename=f"{style}_variant_{seed_variant}.mp3",
        short_num=seed_variant + 1, force_waifu=force_waifu, force_shounen=force_shounen,
    )
    for attempt in range(1, max_retries + 1):
        result = generate_image(prompt, output_path)
        if result:
            return result
        time.sleep(3 * attempt)
    return None


def get_or_generate_background(style: str = "phonk", output_dir: str = "assets/backgrounds") -> Optional[str]:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    existing = list(Path(output_dir).glob(f"{style}_bg_*.png"))
    if existing:
        return str(random.choice(existing))
    variant = random.randint(0, 199)
    return generate_background_image(style=style,
        output_path=str(Path(output_dir) / f"{style}_bg_{variant:03d}.png"),
        seed_variant=variant)


def generate_background_batch(
    styles: list, output_dir: str = "assets/backgrounds",
    variants_per_style: int = 3, force_waifu: bool = False, force_shounen: bool = False,
) -> dict:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    results: dict = {}
    for style in styles:
        results[style] = []
        for v in range(variants_per_style):
            output_path = str(Path(output_dir) / f"{style}_bg_{v:03d}.png")
            if os.path.exists(output_path):
                results[style].append(output_path)
                continue
            path = generate_background_image(style=style, output_path=output_path,
                seed_variant=v, force_waifu=force_waifu, force_shounen=force_shounen)
            if path:
                results[style].append(path)
    return results


# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=f"AI Image Generator — DJ DARK MARK {VERSION}")
    parser.add_argument("--style", default="phonk",
        choices=["phonk","trap","electronic","darkpop","dark","rock","drift","funk"])
    parser.add_argument("--filename", default="dark phonk.mp3")
    parser.add_argument("--short-num", type=int, default=1)
    parser.add_argument("--output", default="assets/background.png")
    parser.add_argument("--waifu", action="store_true")
    parser.add_argument("--shounen", action="store_true")
    parser.add_argument("--full-body", action="store_true")
    parser.add_argument("--prompt-only", action="store_true")
    parser.add_argument("--no-claude", action="store_true")
    parser.add_argument("--batch", action="store_true")
    parser.add_argument("--batch-n", type=int, default=3)
    parser.add_argument("--viral", action="store_true")
    args = parser.parse_args()

    if args.batch:
        genres = ["phonk", "trap", "dark", "darkpop", "electronic"]
        results = generate_background_batch(styles=genres, variants_per_style=args.batch_n,
            force_waifu=args.waifu, force_shounen=args.shounen)
        for g, paths in results.items():
            print(f"  {g}: {len(paths)} geradas")
    elif args.prompt_only:
        prompt = build_viral_short_prompt(
            genre=args.style, song_filename=args.filename, short_num=args.short_num,
            force_waifu=args.waifu, force_shounen=args.shounen, use_claude=not args.no_claude,
        )
        print(f"═══ PROMPT {VERSION} ═══")
        print(prompt)
        print(f"\n[{len(prompt)} chars]")
        print(f"\n═══ NEGATIVE PROMPT ═══")
        print(NEGATIVE_PROMPT)
        print(f"\n═══ MUDANÇAS v52→v53 ═══")
        print("  [FIX 1] EXTREME_CLOSEUP peso 45% (era inexistente)")
        print("  [FIX 2] Back view peso 2% (era 5%)")
        print("  [FIX 3] EYE_GLOW_LOCK por gênero")
        print("  [FIX 4] THUMBNAIL_CONTRAST_LOCK obrigatório")
        print("  [FIX 5] Paletas mais saturadas, sem lama")
        print("  [FIX 6] Claude prompt reescrito: rosto primeiro")
        print("  [FIX 7] Negative prompt: 'tiny character' bloqueado")
        print("  [FIX 8] Close-up 45% + bust 30% + 3/4 18% + full 5% + back 2%")
        print("  [FIX 9] Eye shape específico por gênero")
        print("  [FIX 10] GENRE_COLOR_PUNCH: saturação forçada")
        print(f"  [FIX 11] flux-dev: 50 steps + guidance 6.5 (era 40 + 5.0)")
    else:
        prompt = build_viral_short_prompt(
            genre=args.style, song_filename=args.filename, short_num=args.short_num,
            force_waifu=args.waifu, force_shounen=args.shounen, use_claude=not args.no_claude,
        )
        generate_image(prompt, args.output)
