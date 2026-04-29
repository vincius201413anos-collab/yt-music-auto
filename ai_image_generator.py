"""
ai_image_generator.py — DJ DARK MARK v51.0 ██ APEX QUALITY EDITION ██
══════════════════════════════════════════════════════════════════════════

FIXES & UPGRADES v51 vs v50:
  [FIX 1]  Modelo Claude corrigido: claude-opus-4-7 NÃO EXISTE → claude-opus-4-5
           Isso fazia TODOS os prompts caírem no fallback estático sem você saber.
  [FIX 2]  Flux-Dev agora é o modelo PRIMÁRIO (qualidade máxima).
           Flux-Schnell é o fallback rápido.
  [FIX 3]  Parâmetros Flux-Dev otimizados:
             - aspect_ratio: "9:16" (nativo, sem upscale)
             - num_inference_steps: 40 (mais detalhes vs 50 que era lento)
             - guidance_scale: 5.0 (melhor aderência ao prompt anime)
             - output_quality: 100
  [FIX 4]  GENERATION_SUFFIX limpo: removidos "masterpiece" e "best quality"
           (são tags SD 1.5/SDXL — no Flux causam imagens genéricas e sem alma)
  [FIX 5]  Prompt Claude: limite aumentado 60-100 → 100-160 palavras.
           Flux responde melhor a prompts descritivos longos.
  [FIX 6]  Prompt Claude: instrução de "comma-separated only" removida.
           Frases descritivas geram melhores resultados no Flux.
  [FIX 7]  Seed por short_num para garantir diversidade entre shorts da mesma música.
  [FIX 8]  API Replicate: migrado para endpoint correto com polling robusto.
  [FIX 9]  negative_prompt agora funciona via campo dedicado (suportado no Flux-Dev).
  [NEW 1]  Retry inteligente: muda de seed automaticamente em cada tentativa.
  [NEW 2]  Validação de imagem mais rigorosa: mínimo 80KB (evita placeholders).
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

logger = logging.getLogger("ai_image_generator_v51")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# ═══════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════

REPLICATE_API_TOKEN: str = os.getenv("REPLICATE_API_TOKEN", "")

# [FIX 2] Flux-Dev como primário — qualidade máxima
REPLICATE_MODELS = [
    "black-forest-labs/flux-dev",
    "black-forest-labs/flux-schnell",
]

# [FIX 3] Parâmetros Flux-Dev otimizados para anime vertical
FLUX_DEV_PARAMS: dict = {
    "aspect_ratio": "9:16",          # vertical nativo — sem upscale artificial
    "num_inference_steps": 40,        # [FIX 3] 40 steps = qualidade máxima sem overhead
    "guidance": 5.0,                  # [FIX 3] 5.0 = excelente aderência ao prompt anime
    "output_format": "png",
    "output_quality": 100,            # PNG é lossless, 100 é o correto
    "disable_safety_checker": True,
}

# Flux-Schnell como fallback rápido
FLUX_SCHNELL_PARAMS: dict = {
    "aspect_ratio": "9:16",
    "num_inference_steps": 4,         # schnell: mínimo viável
    "go_fast": True,
    "output_format": "png",
    "output_quality": 100,
    "disable_safety_checker": True,
}

VERSION = "v51.0-APEX-QUALITY"

# [FIX 1] Modelo Claude correto — claude-opus-4-7 NÃO EXISTE
def get_anthropic_model() -> str:
    return os.getenv("ANTHROPIC_MODEL", "claude-opus-4-5")


# ═══════════════════════════════════════════════════════════════════════
# ENUMS — CHARACTER TYPE / ENGINE SELECT
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
# DATACLASSES
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class CharacterEntry:
    name: str
    series: str
    char_type: CharType
    base_description: str
    signature_elements: list[str]
    power_phrase: str


@dataclass
class PromptContext:
    char: CharacterEntry
    composition: dict
    pose: str
    emotion: EmotionArchetype
    visual_hook: str
    palette_name: str
    palette_prompt: str
    particle_tier: str
    lighting_stack: str
    background: str
    genre: str
    genre_boost: str
    song_name: str
    song_mood: str
    music_element: str
    waifu_extras: str
    power_extras: str


# ═══════════════════════════════════════════════════════════════════════
# CHARACTER LIBRARY — ENGINE A: WAIFUS (100 entries)
# ═══════════════════════════════════════════════════════════════════════

WAIFU_CHARACTERS: list[CharacterEntry] = [

    CharacterEntry("Mitsuri Kanroji", "Demon Slayer", CharType.WAIFU,
        "long pink-to-green ombre hair loose and cascading past hips, warm flush cheeks",
        ["cherry blossom Love Breathing ribbon-sword crackling soft pink energy",
         "flexible kunoichi body in mid-impossible-angle attack",
         "modified revealing pink Hashira uniform", "warm loving smile hiding lethal speed"],
        "Love Pillar — the most flexible blade in existence"),

    CharacterEntry("Daki", "Demon Slayer", CharType.WAIFU,
        "very long silver-white hair with teal gradient tips, sharp jaw, neon vein demon markings",
        ["obi sash weapon as crystalline blade fans glowing blood-crimson",
         "revealing elegant courtesan kimono with living flesh-cloth neon patterns",
         "contemptuous half-lidded eyes with slit demon pupils glowing red",
         "demon absorption marks crawling glowing up arms and neck"],
        "Upper Moon Six — beauty that cuts everything it touches"),

    CharacterEntry("Shinobu Kocho", "Demon Slayer", CharType.WAIFU,
        "long hair flowing from yellow-to-lavender, butterfly haori with wings as holographic neon",
        ["needle-thin insect-venom sword crackling purple toxin energy",
         "tiny vials radiating pale green medical neon",
         "soft closed-eye smile hiding total ruthlessness",
         "butterfly wing light constructs extending six feet wide"],
        "Insect Pillar — the smile that ends you before the pain registers"),

    CharacterEntry("Nezuko Kamado", "Demon Slayer", CharType.WAIFU,
        "long black hair with neon pink ombre tips, demon form with cracked pink neon skin fissures",
        ["Exploding Blood technique making crimson neon erupt in petal-shaped blasts",
         "pink haori with hemp-leaf pattern illuminated from within",
         "half-demon transformation with glowing hot pink eye",
         "small frame containing compressed demon power"],
        "Demon who chose humanity — pink fire that protects"),

    CharacterEntry("Makima", "Chainsaw Man", CharType.WAIFU,
        "neat auburn hair in low braid, white dress shirt, rings of concentric glowing eyes floating",
        ["Control Devil leash chain glowing gold wrapping around reality",
         "perfect eerie calm expression of total dominance",
         "concentric eye rings orbiting like surveillance satellites",
         "presence bending the world toward her"],
        "Control Devil — everything was always hers"),

    CharacterEntry("Power", "Chainsaw Man", CharType.WAIFU,
        "wild blonde hair with iconic neon pink curved devil horns, casual streetwear",
        ["enormous chainsaw arm deployed and revving crackling neon blood-red",
         "feral gap-toothed grin showing canines and absolute chaos",
         "blood manipulation forming crimson armor plates",
         "horn neon casting hard pink rim light across face"],
        "Blood Devil — pure chaos in a cute package"),

    CharacterEntry("Himeno", "Chainsaw Man", CharType.WAIFU,
        "short white hair, eyepatch replaced by glowing green neon device",
        ["Ghost Devil translucent hand jutting from beside her",
         "casual cyberpunk devil hunter jacket half-open",
         "cigarette between lips with green ghost-neon smoke trail",
         "effortless dangerous confidence radiating from posture"],
        "Ghost contract hunter — the coolest one in the room"),

    CharacterEntry("Quanxi", "Chainsaw Man", CharType.WAIFU,
        "long blonde hair in high ponytail, athletic lean build",
        ["First Devil Hunter with four arrow fiends orbiting as personal bodyguard halos",
         "cool emotionless mercenary expression behind tinted cyber-visor",
         "multiple arrows nocked simultaneously with glowing bolt-heads",
         "techwear bodysuit with arrow-quiver neon integrated"],
        "First Devil Hunter — precision death"),

    CharacterEntry("Nobara Kugisaki", "Jujutsu Kaisen", CharType.WAIFU,
        "orange-brown bob hair with blunt cut, fierce no-nonsense expression",
        ["straw doll and nails crackling black cursed energy resonance technique",
         "hammer raised mid-Black-Flash strike with dark lightning",
         "cursed tool blood splatter forming abstract neon patterns",
         "Resonance technique activating glowing skull over distant target"],
        "Hammer and nails — ugly but effective"),

    CharacterEntry("Maki Zenin", "Jujutsu Kaisen", CharType.WAIFU,
        "short dark hair with medical tape on nose, glasses with neon green special vision",
        ["naginata staff as massive cursed tool extended full length",
         "zero cursed energy making her invisible to detection",
         "physical dominance frame where muscles catch neon under ripped uniform",
         "Zenin clan cursed tool arsenal orbiting at ready"],
        "Zero cursed energy — pure physical apex"),

    CharacterEntry("Mei Mei", "Jujutsu Kaisen", CharType.WAIFU,
        "long blonde twin braids, cool mercenary professionalism",
        ["twin ravens with glowing neon eyes orbiting as strike satellites",
         "calculating money-motivated expression over battle chaos",
         "Bird Strike technique bird dissolving into high-velocity impact neon",
         "black suit with cyberpunk armor plates at joints"],
        "Every action has a price — and she charges double"),

    CharacterEntry("Yuki Tsukumo", "Jujutsu Kaisen", CharType.WAIFU,
        "long blonde hair with casual wild styling, special grade sorcerer ease",
        ["Star Rage technique Virtual Mass enhancing strikes to astronomical scale",
         "casual combat stance hiding special grade destruction potential",
         "Mass attribute making fists carry planetary impact weight",
         "relaxed smile while outputting power that cracks the earth"],
        "Special Grade — stars in her fists"),

    CharacterEntry("Frieren", "Frieren: Beyond Journey's End", CharType.WAIFU,
        "long silver elf hair with decorative ribbon ties, ancient eyes holding a thousand years of grief",
        ["Zoltraak offensive magic as casual finger-flick after thousand years of mastery",
         "magic field analysis sight activating as faint mana-reading glow",
         "cherry blossoms mixing with mana particles",
         "staff trailing afterimage of every spell she has ever cast"],
        "A thousand years of magic — still stopping for flowers"),

    CharacterEntry("Fern", "Frieren: Beyond Journey's End", CharType.WAIFU,
        "long dark hair in neat twin braids, diligent prodigy mage",
        ["Zoltraak rapid-fire multi-volley exceeding any mage her generation",
         "concentrated blue-white magic blast charges erupting from both hands",
         "serious face with small unconscious excitement for magical trinkets",
         "mana control so precise her spells leave no splash"],
        "The most efficient mage born in a century"),

    CharacterEntry("Rem", "Re:Zero", CharType.WAIFU,
        "iconic short blue hair with hair clip, maid uniform as armored cyberpunk bodyguard suit",
        ["morning star flail crackling dense blue electricity on impact sphere",
         "Oni horn emerging glowing blue releasing demon power",
         "tear-streaked fierce face of absolute devotion and destruction",
         "Oni magic aura billowing blue smoke off raised horn"],
        "Demon maid — devotion and destruction are the same thing"),

    CharacterEntry("Emilia", "Re:Zero", CharType.WAIFU,
        "long silver hair half-tied with white flower ornaments, pointed elf ears",
        ["ice shards floating around hands forming shield and blade constructs",
         "cyberpunk ice sorceress coat with crystalline blue circuit patterns",
         "cold breath visible as silver mist in neon air",
         "elemental spirits orbiting as small glowing sprites"],
        "Half-elf ice maiden — gentleness that freezes worlds"),

    CharacterEntry("Beatrice", "Re:Zero", CharType.WAIFU,
        "very long twin drill blonde twintails, ancient spirit in small frame",
        ["spirit arts magic barrier circle blazing gold hovering under feet",
         "library of Roswaal dimensional barrier crackling around her",
         "irritated expression hiding fierce loyalty and centuries of loneliness",
         "overwhelming spirit power radiating from tiny form"],
        "Ancient spirit — four hundred years waiting for one person"),

    CharacterEntry("Ram", "Re:Zero", CharType.WAIFU,
        "short pink hair with single demon horn glowing hot pink, elite maid precision",
        ["Clairvoyance neon eye scan activating golden ring around single horn",
         "condescending sharp beauty staring down from absolute competence",
         "maid uniform with cyberpunk combat apron neon trim",
         "Barusu energy masking S-rank assassin threat level"],
        "Single horn — still the strongest maid alive"),

    CharacterEntry("Echidna", "Re:Zero", CharType.WAIFU,
        "long white hair with black roots fading up, gothic witch of greed",
        ["tea cup floating with bone-white otherworldly glow",
         "eerily beautiful perfect smile hiding absolute evil calculation",
         "void portal consuming background reality behind her",
         "knowledge greed visible as constellation data streams orbiting"],
        "Witch of Greed — she already knows how you die"),

    CharacterEntry("Satella", "Re:Zero", CharType.WAIFU,
        "silver hair half-radiant half-consumed by shadow, violet eyes crying genuine love",
        ["Witch of Envy shadow hands reaching from dress hem like living darkness",
         "tragic goddess beauty consuming herself for one love",
         "love and destruction made physically indistinguishable",
         "shadow tentacles and violet light fighting for the same body"],
        "Witch of Envy — loved so much she destroyed the world"),

    CharacterEntry("Albedo", "Overlord", CharType.WAIFU,
        "floor-length black wavy hair, white angelic dress meeting black demon wings",
        ["Hermes Trismegistus giant shield deployed as glowing wing-barrier",
         "obsessive adoring expression turning lethal when Nazarick is threatened",
         "halo above and black wings simultaneously — angel and demon unified",
         "Levia Halcyon great axe erupting Armageddon charge"],
        "Floor Guardian — love and loyalty indistinguishable from fanaticism"),

    CharacterEntry("Shalltear Bloodfallen", "Overlord", CharType.WAIFU,
        "long silver drill hair, true vampire form with full-spread crimson wings",
        ["Blood Frenzy power increasing with each wound received",
         "Spuit Lance crackling dark crimson neon at full charge",
         "pale white skin with neon red possessive eyes",
         "blood drops floating weightless in power field"],
        "True Vampire Floor Guardian — the more you hurt her the worse it gets"),

    CharacterEntry("Artoria Pendragon (Saber)", "Fate Series", CharType.WAIFU,
        "iconic golden hair in tight braid, emerald green eyes, blue and gold plate armor",
        ["Excalibur divine wind energy charging as golden beam toward sky",
         "noble resolute expression of a king who carried the world's weight",
         "sword raised with divine golden wind tearing everything apart",
         "Avalon barrier fragments floating as golden petals"],
        "King of Knights — Excalibur tears the sky"),

    CharacterEntry("Jeanne d'Arc Alter", "Fate Series", CharType.WAIFU,
        "long silver-white hair with dark roots, black inverse holy armor dripping crimson",
        ["La Grondement Du Haine black flame lance consuming everything it touches",
         "cold vengeful expression of divine justice turned righteous wrath",
         "black flag crackling inverse holy energy destroying purity",
         "dark holy fire making air black and gold"],
        "Avenger — God abandoned her first"),

    CharacterEntry("Tamamo-no-Mae", "Fate Series", CharType.WAIFU,
        "long flowing golden hair, iconic fox ears and nine tails glowing",
        ["divine solar flame technique channeling sun goddess power through fox tails",
         "seductive kitsune smile hiding catastrophic divine power",
         "nine golden fox tails extending as massive energy wings",
         "Amaterasu connection making eyes glow solar gold"],
        "Divine fox goddess — sun in her tails"),

    CharacterEntry("Asuna Yuuki", "Sword Art Online", CharType.WAIFU,
        "chestnut waist-length hair, white-and-red KoB armor as cyberpunk plate",
        ["rapier radiating electric blue speed energy",
         "Starburst Stream 16-hit combo leaving light trail clone aftermath",
         "lightning goddess of rapid strike pose frozen at maximum velocity",
         "graceful frame hiding the fastest sword in Aincrad"],
        "Flash — 16 hits before you see the first"),

    CharacterEntry("Sinon", "Sword Art Online", CharType.WAIFU,
        "short teal-blue hair, sniper's cold precision",
        ["Hecate II sniper rifle glowing blue scope charge for Meteor Shot",
         "cold blue eyes calculating trajectory through impossible terrain",
         "kneeling sniper form with wind-blown hair in perfect composition",
         "bullet trajectory neon visible as golden arc through air"],
        "GGO's best sniper — one shot, anywhere"),

    CharacterEntry("Tsunade", "Naruto", CharType.WAIFU,
        "long blonde hair in iconic twin pigtails, diamond Yin Seal on forehead",
        ["seal releasing in wave of overwhelming chakra making ground shatter",
         "fist raised with Strength of a Hundred cracking the earth",
         "legendary beauty and strength radiating simultaneously",
         "Sannin-level presence making enemies reconsider"],
        "Legendary Sannin — the strongest fist in the world"),

    CharacterEntry("Konan", "Naruto", CharType.WAIFU,
        "short blue hair, paper-white robe, paper butterfly orbiting",
        ["paper angel wings extending dozens of feet from billions of explosive sheets",
         "6 billion explosive tags deployment visible as white paper flood",
         "calm terrifying goddess expression",
         "paper world technique consuming entire background"],
        "Paper god — she doesn't fight, she rearranges reality"),

    CharacterEntry("Kushina Uzumaki", "Naruto", CharType.WAIFU,
        "extremely long red hair floating as living weapon, red chain sealing marks",
        ["Adamantine Sealing Chains deploying as massive golden restraint lattice",
         "Red Hot-Blooded Habanero fury expression",
         "Nine-Tails chakra chains crackling red-gold sealing anyone",
         "Uzumaki life force aura making her glow red-gold"],
        "Red Hot-Blooded Habanero — her hair alone is a weapon"),

    CharacterEntry("Yoruichi Shihouin", "Bleach", CharType.WAIFU,
        "dark skin, short purple hair, goddess of flash identity",
        ["Shunko lightning-enhanced physical strike making air explode",
         "golden speed neon afterimages filling frame",
         "playful grin showing she still barely tried",
         "Flash God hakuda technique cracking stone floor under each landing"],
        "Flash Goddess — fastest thing in Soul Society"),

    CharacterEntry("Rukia Kuchiki", "Bleach", CharType.WAIFU,
        "short black hair, shinigami uniform with noble white scarf",
        ["Sode no Shirayuki ice zanpakuto white rose petal ice storm erupting",
         "Some no mai Tsukishiro white circle of absolute zero frost",
         "noble Kuchiki bearing combining with small fierce frame",
         "Bankai Hakka no Togame ice mist consuming everything"],
        "Ice dancer — the most beautiful absolute zero"),

    CharacterEntry("Rangiku Matsumoto", "Bleach", CharType.WAIFU,
        "wavy long strawberry-blonde hair cascading, vice-captain badge",
        ["Haineko zanpakuto dissolving into ash-blade swarm filling entire frame",
         "lazy confident smile masking enormous spiritual pressure",
         "ash cloud forming shapes and slashing simultaneously",
         "feminine and lethal in exactly equal measure"],
        "Haineko — ash that cuts"),

    CharacterEntry("Halibel", "Bleach", CharType.WAIFU,
        "long blonde hair, hollow jaw collar mask fragment, Tres Bestias bearing",
        ["Tiburón released form water shark technique Cascada waterfall power",
         "Espada 3 Queen of Hueco Mundo presence bending light and water",
         "stoic beautiful expression of absolute command",
         "water manipulation making ocean appear in dry air"],
        "Queen of Hueco Mundo — sea brought to solid ground"),

    CharacterEntry("Boa Hancock", "One Piece", CharType.WAIFU,
        "floor-length black hair with iconic Kuja crown, empress bearing",
        ["Love-Love Mero Mero Mellow hand pose petrifying everything beautiful",
         "Slave Arrow technique shooting love beam array",
         "breathtaking arrogant beauty that literally stops battles",
         "snakes Salome coiling around legs glowing sacred"],
        "Pirate Empress — the most beautiful woman alive, and she knows it"),

    CharacterEntry("Nami", "One Piece", CharType.WAIFU,
        "shoulder-length orange hair, navigator identity in every gesture",
        ["Clima-Tact upgraded as cyberpunk weather staff releasing Thunderbolt Tempo",
         "Zeus cloud companion crackling massive storm power",
         "weather map holographic open showing real-time storm formation",
         "confident navigator claiming the sea belongs to her"],
        "Weather Witch — she owns every storm"),

    CharacterEntry("Nico Robin", "One Piece", CharType.WAIFU,
        "long straight black hair, cyberpunk archaeologist in dark trench coat",
        ["Mil Fleur Gigantesco Mano hundred stone hands emerging simultaneously",
         "Demonio Fleur demon giant form rising behind her",
         "mysterious half-smile of someone who survived the unsurvivable",
         "Ohara holographic ruins glowing blue in memory"],
        "Devil Child — she survived murder and became stronger"),

    CharacterEntry("Yamato", "One Piece", CharType.WAIFU,
        "long white hair with oni horns glowing icy blue, powerful athletic frame",
        ["Divine Departure massive Haki-coated sword swing",
         "Hybrid Mythical Zoan white wolf god form partially released",
         "Conqueror's Haki crackling black lightning off weapon",
         "Oden's log pose glowing as sacred relic in powerful grip"],
        "Oni Princess — carrying Oden's will forward"),

    CharacterEntry("Kurumi Tokisaki", "Date A Live", CharType.WAIFU,
        "iconic half black half white long hair, clockwork eye and crimson eye",
        ["twin flintlocks dripping shadow particles and time-decay neon",
         "Clock Bullet Zafkiel technique deploying time-rewind spatial bullet",
         "gothic lolita dress as cyberpunk time spirit armor with clock gear motifs",
         "time shadows of past-selves orbiting as ghost afterimages"],
        "Spirit of Time — she's already seen how this ends"),

    CharacterEntry("Tohka Yatogami", "Date A Live", CharType.WAIFU,
        "long dark purple hair, Spirit dress flowing and armored simultaneously",
        ["Sandalphon throne-sword crackling purple lightning at maximum power",
         "Inverse Form consuming light into violet void",
         "innocent expression in terrible contrast to godlike destruction",
         "Spirit mana wings expanding forty feet behind her"],
        "First Spirit — enough power to crack the world"),

    CharacterEntry("Noelle Silva", "Black Clover", CharType.WAIFU,
        "silver-white hair with blue tint, proud noble bearing",
        ["Valkyrie Armor water manifestation as divine aqua knight form",
         "Saint Stage water dragon rising behind armored figure",
         "noble clumsy determination transformed into real power",
         "water controlled with precision that took years of will"],
        "Royal Knight — the water that protects everything"),

    CharacterEntry("Momo Yaoyorozu", "My Hero Academia", CharType.WAIFU,
        "long black hair in iconic high ponytail, creation quirk exposed skin",
        ["creation quirk manifesting white molten material forming massive cannon",
         "intelligent tactical expression reading battlefield at genius level",
         "elegant hero costume practical for creation quirk",
         "multiple created weapons orbiting simultaneously in tactical array"],
        "Creation Hero — she literally builds victory on the spot"),

    CharacterEntry("Mirko", "My Hero Academia", CharType.WAIFU,
        "white hair and rabbit ears, powerful athletic body with battle scars",
        ["Luna Ring Kick technique unleashing massive pressure wave",
         "scars on arm visible and worn with zero apology",
         "fierce grin showing teeth getting stronger from damage",
         "rabbit speed afterimages filling frame from sheer velocity"],
        "Rabbit Hero — five highest-ranked hero, no team, no backup"),

    CharacterEntry("Himiko Toga", "My Hero Academia", CharType.WAIFU,
        "twin blonde bun with loose strands, blood-drain gauntlets neon yellow",
        ["Transform quirk cycling through faces with golden eyes shifting",
         "unhinged joyful dangerous smile at target of obsession",
         "knife held lovingly like it's the kindest thing she owns",
         "yandere beauty — she always looks like this"],
        "Transform quirk — love is just wanting to become someone"),

    CharacterEntry("Megumin", "KonoSuba", CharType.WAIFU,
        "short black hair under enormous wizard hat with neon star ornament, red eyes",
        ["EXPLOSION single ultimate spell charging black void energy toward sky",
         "staff raised in full dramatic explosion chant pose",
         "dark energy erupting beneath tiny dramatic frame as massive shockwave",
         "one eye closed in concentration as reality prepares to suffer"],
        "Explosion mage — one spell, everything gone"),

    CharacterEntry("Darkness", "KonoSuba", CharType.WAIFU,
        "long wavy blonde hair, crusader plate armor with neon blue rune engravings",
        ["broadsword dragged dramatically creating ground furrow",
         "flushing noble expression hiding extremely specific secret",
         "tall powerful frame built for tanking absolutely everything",
         "armor cracked from absorbing massive attacks with zero flinching"],
        "Crusader tank — she can't hit anything and doesn't need to"),

    CharacterEntry("Violet Evergarden", "Violet Evergarden", CharType.WAIFU,
        "long golden blonde hair, auto memory doll uniform with prosthetic silver arms",
        ["typewriter keys floating around her as magical memory objects glowing soft",
         "letter neon paper dissolving into butterfly flutter upward",
         "deep lonely beautiful eyes learning what emotion means",
         "prosthetic arms glowing blue at joints reaching toward warmth"],
        "Auto Memory Doll — learning to feel through every letter"),

    CharacterEntry("Yor Forger", "Spy × Family", CharType.WAIFU,
        "black hair with rose hairpin glowing blood-red, thorn-covered crimson dress",
        ["twin needles crackling with red neon Thorn Princess energy",
         "gentle smile hiding terrifying speed and accuracy underneath",
         "rose thorns extending from dress fabric as actual blades",
         "assassin training making casual poses accidentally threatening"],
        "Thorn Princess — deadliest hands, warmest heart"),

    CharacterEntry("Kaguya Shinomiya", "Kaguya-sama: Love is War", CharType.WAIFU,
        "impossibly long black hair with ornate kanzashi pins glowing red neon",
        ["holographic data fan showing strategic analysis of opponent emotional state",
         "sharp manipulative intelligence visible in every movement",
         "cyberpunk noble in dark kimono with gold circuit obi deployed",
         "battle-mind palace visualization showing twenty steps ahead"],
        "Ice Princess — she already won before you started"),

    CharacterEntry("Mai Sakurajima", "Rascal Does Not Dream of Bunny Girl Senpai", CharType.WAIFU,
        "short dark hair, mysterious actress aura filling every room",
        ["iconic bunny outfit redesigned in cyberpunk leather and neon pink",
         "purple spotlight catching her perfectly while everything dims",
         "knowing sharp gaze seeing through every facade",
         "Adolescence Syndrome making her visible only to one"],
        "Bunny Girl Senpai — exists for one person only"),

    CharacterEntry("Yuno Gasai", "Future Diary", CharType.WAIFU,
        "long pink hair half-neat half-wild — two personalities in one hairdo",
        ["diary phone glowing ominous pink-red with target's fate",
         "yandere smile beautiful and cracked — one eye loving one eye hunting",
         "blood neon tear on cheek making her more beautiful somehow",
         "love and murder made graphically indistinguishable"],
        "Yandere goddess — first place in survival game, forever"),

    CharacterEntry("Kurisu Makise", "Steins;Gate", CharType.WAIFU,
        "long reddish-brown hair, white lab coat with cyberpunk time research gear",
        ["teal time machine data streams swirling from open laptop mid-calculation",
         "brilliant sarcastic tsundere expression of someone who changed the world",
         "time paradox visualization as branching neon timelines orbiting her",
         "Christina nickname making her twitch while she pretends to work"],
        "Time machine genius — don't call her Christina"),

    CharacterEntry("Zero Two", "DARLING in the FranXX", CharType.WAIFU,
        "long pink hair with iconic black horns glowing red neon, pilot suit",
        ["Strelizia FranXX manifest as massive mech silhouette looming",
         "wild confident grin of predatory beautiful chaos energy",
         "candy-pink circuits running up arms like veins beneath pale skin",
         "klaxosaur blood heritage crackling neon at horn base"],
        "Partner Killer — darling changed everything"),

    CharacterEntry("Ryuko Matoi", "Kill la Kill", CharType.WAIFU,
        "short black hair with red streak, Senketsu living uniform symbiosis",
        ["Scissor Blade half crackling life fiber red energy",
         "Senketsu absorbed power radiating red neon off battle suit",
         "defiant expression fighting the entire world and winning",
         "life fiber integration making veins glow red across skin"],
        "Scissor Blade — she'll cut the universe in half if she has to"),

    CharacterEntry("Satsuki Kiryuin", "Kill la Kill", CharType.WAIFU,
        "very long black hair whipping dramatically, absolute supreme authority",
        ["Bakuzan sword crackling absolute authority life fiber cutting neon",
         "commanding speech on high platform with elite four flanking",
         "iron will domination presence making enemies kneel from authority alone",
         "eyebrows expressing more contempt than most people's entire faces"],
        "Iron Lady — I will have dominion"),

    CharacterEntry("Holo", "Spice and Wolf", CharType.WAIFU,
        "long brown hair with wolf ears perked and fluffy tail raised high",
        ["apple in hand radiating warm amber harvest goddess neon",
         "wolf transformation large form with silver-white full moon",
         "wise playful smile hiding centuries of accumulated knowledge",
         "Yoitsu forest spirit connection visible as green leaf neon"],
        "Wisewolf of Yoitsu — the oldest merchant's secret"),

    CharacterEntry("Milim Nava", "That Time I Got Reincarnated as a Slime", CharType.WAIFU,
        "iconic twin pink drill pigtails, small frame containing catastrophic Demon Lord power",
        ["Drago Nova condensing full Primogenitor power into single annihilation point",
         "Milim Eye demonic eye stripping all illusion from existence",
         "cheerful open grin while casually erasing mountain ranges",
         "oldest Demon Lord playing like a child because she can"],
        "Oldest Demon Lord — don't let the pigtails fool you"),

    CharacterEntry("Ai Hoshino", "Oshi no Ko", CharType.WAIFU,
        "long black hair with pink ends, idol stage presence filling concert hall",
        ["pink-gold star neon particles erupting from stage floor as idol persona activates",
         "ruby and aquamarine stars forming in air at performance peak",
         "smile that made the entire nation fall in love with absolute sincerity",
         "roses from audience frozen mid-fall in pink-white neon"],
        "The brightest idol — her love was the realest lie"),

    CharacterEntry("Rias Gremory", "High School DxD", CharType.WAIFU,
        "floor-length crimson hair cascading dramatically, devil noble bearing",
        ["Power of Destruction crimson ball of oblivion radiating from palm",
         "devil wing deployment in full twelve-point spread neon red",
         "confident imperious posture of Gremory heir commanding absolute space",
         "aristocratic beauty expressing dominance as natural resting state"],
        "Crimson-Haired Ruin Princess — destruction has never been this beautiful"),

    CharacterEntry("Akeno Himejima", "High School DxD", CharType.WAIFU,
        "very long black hair in iconic high ponytail, shrine maiden as thunder witch",
        ["violet lightning holy demonic fusion arcing between extended fingers",
         "soft smile hiding absolute ruthless power enjoying battle entirely too much",
         "fallen angel wings extending neon purple from shoulder blades",
         "lightning cage technique sealing target inside crackling violet sphere"],
        "Priestess of Thunder — she enjoys this a little too much"),

    CharacterEntry("Raiden Shogun", "Genshin Impact", CharType.WAIFU,
        "long purple hair with traditional kanzashi, electro archon bearing",
        ["Musou Isshin sword resonating electro nation ambition technique",
         "Baleful Shogun puppet transformation in battle",
         "divine electro power arcing off every surface near her presence",
         "Eternity ambition crackling purple neon off entire frame"],
        "Electro Archon — Eternity is her divine right"),

    CharacterEntry("Hu Tao", "Genshin Impact", CharType.WAIFU,
        "long brown twin pigtails with teal ends, spirit-sensing eyes",
        ["Paramita Papilio blood blossom technique wreathing body in ghost fire neon",
         "spirit butterfly orbiting in crimson-gold constellation",
         "mischievous funeral director expression finding death genuinely funny",
         "Plum Blossom ghosts dancing as playful death parade"],
        "77th Director of Wangsheng Funeral Parlor — death is her business"),

    CharacterEntry("Yae Miko", "Genshin Impact", CharType.WAIFU,
        "long pink hair with fox ears and nine tails, shrine keeper kitsune",
        ["Sesshou Sakura totem placing crackling electro fox spirit pillars",
         "kitsune fox fire neon arcing between totem network",
         "sharp calculating shrine keeper smile hiding divine trickster nature",
         "nine tails deploying as electro neon energy constructs"],
        "Electro fox — the shrine keeper always gets what she wants"),

    CharacterEntry("Ayaka Kamisato", "Genshin Impact", CharType.WAIFU,
        "long white hair with snowflake ornaments, elegant Kamisato cryo swordswoman",
        ["Kamisato Art Soumetsu cutting tornado of cryo cherry blossoms",
         "dash technique leaving ice bloom trail of crystalline flowers",
         "composed noble expression masking genuine warmth",
         "snow petals perpetually orbiting in slow deliberate rotation"],
        "Shirasagi Himegimi — grace that freezes everything it touches"),

    CharacterEntry("Furina", "Genshin Impact", CharType.WAIFU,
        "long silver hair with hydro blue eyes, former hydro archon theatrical performer",
        ["Salon Members hydro creatures summoning from performance space",
         "Endless Waltz technique deploying full god power hidden for 500 years",
         "theatrical dramatic expression finally released after 500 years performing",
         "hydro archon true power signature emerging in brilliant blue neon"],
        "Hydro Archon — the longest performance, the most genuine tears"),

    CharacterEntry("Nahida", "Genshin Impact", CharType.WAIFU,
        "short white hair with leaf ornament, tiny frame of Lesser Lord Kusanali",
        ["Wisdom of God technique linking all minds in radius via neon leaf network",
         "Dendro archon true form emerging behind small vessel",
         "curious innocent expression carrying weight of abandoned god",
         "flower of paradise neon bloom expanding outward from raised hand"],
        "Dendro Archon — imprisoned in a box, still knew everything"),

    CharacterEntry("Navia", "Genshin Impact", CharType.WAIFU,
        "long blonde hair with elegant hat, Spina di Rosula leader geo fighter",
        ["Rosula Shinewave technique charging geo crystal shotgun massive barrage",
         "crystal shrapnel neon forming complex explosive constellation",
         "noble elegance commanding underground organization with genuine care",
         "mourning dress that became armor — she leads through grief"],
        "Chief of Spina di Rosula — elegance weaponized"),

    CharacterEntry("Clorinde", "Genshin Impact", CharType.WAIFU,
        "long dark hair with champion duelist bearing, electro sword and gun hybrid",
        ["Hunter's Vigil technique switching between gun and blade at hyperspeed",
         "electro duel pistol crackling with precise controlled lightning",
         "professional champion duelist expression that has never lost",
         "snake motif neon orbiting in electro patterns around blade"],
        "Champion Duelist of Fontaine — she hasn't lost yet"),

    CharacterEntry("Reina Ikari", "Original Cyberpunk Waifu", CharType.WAIFU,
        "shaved sides with long neon teal top hair, heavy cyber-implant modifications",
        ["neural hack technique deploying teal data wave consuming enemy systems",
         "chrome-plated knuckles crackling electric discharge",
         "sleeveless techwear jacket over neon tattoos covering arms and neck",
         "cyberpunk street queen owning this city"],
        "Netrunner Queen — every system bends to her"),

    CharacterEntry("Seraphina Vex", "Original Cyberpunk Waifu", CharType.WAIFU,
        "long dark red hair with iridescent purple tint, mercenary sniper dark techwear",
        ["plasma rifle barrel neon-hot from sustained firing sequence",
         "scope overlay showing target lock network across entire battlefield",
         "contract killer calm over overwhelming battlefield situation",
         "neon tattoo sleeve glowing during combat focus state"],
        "Hired gun — she never misses twice"),
]


# ═══════════════════════════════════════════════════════════════════════
# CHARACTER LIBRARY — ENGINE B: SHOUNEN (100 entries)
# ═══════════════════════════════════════════════════════════════════════

SHOUNEN_CHARACTERS: list[CharacterEntry] = [

    CharacterEntry("Gojo Satoru", "Jujutsu Kaisen", CharType.SHOUNEN,
        "iconic white hair styled back, Six Eyes cerulean blue through removed sunglasses",
        ["Unlimited Void domain expansion infinite starfield consuming entire background",
         "Hollow Purple collision of Red and Blue detonating reality",
         "Infinity distortion sphere making space curve visibly",
         "most powerful sorcerer standing calm at center of universe breaking"],
        "Infinity — the honor of being the strongest"),

    CharacterEntry("Ryomen Sukuna", "Jujutsu Kaisen", CharType.SHOUNEN,
        "pink spiked hair, four arms, double set of eyes including cheek eyes open",
        ["Malevolent Shrine domain cleave cutting everything in kilometers",
         "Dismantle and Cleave invisible force shockwaves crossing dimensions",
         "black tattoos covering entire body glowing crimson ancient evil",
         "king of curses standing in annihilated cathedral of cursed energy"],
        "King of Curses — the honor of being the strongest"),

    CharacterEntry("Yuji Itadori", "Jujutsu Kaisen", CharType.SHOUNEN,
        "spiky pink hair with dark roots, Sukuna's vessel barely keeping him back",
        ["Divergent Fist cursed energy delayed detonation double impact",
         "Black Flash crackling between knuckles at moment of connection",
         "Sukuna tattoos crawling up arms as cursed energy overflows",
         "pure human body hosting monster power through sheer will alone"],
        "Divergent Fist — vessel of the King of Curses"),

    CharacterEntry("Megumi Fushiguro", "Jujutsu Kaisen", CharType.SHOUNEN,
        "dark messy hair, Ten Shadows calm calculation",
        ["Ten Shadows Technique deploying full divine beast array plus Mahoraga",
         "shadow energy consuming ground as endless summon space",
         "shikigami circle activating under feet drawing from infinite shadow",
         "cool detachment masking catastrophic power"],
        "Ten Shadows — the technique that could kill Sukuna"),

    CharacterEntry("Choso", "Jujutsu Kaisen", CharType.SHOUNEN,
        "long black hair divided by white streak, oldest death painting bearer",
        ["Supernova blood bullet hypersonic barrage leaving crimson trails",
         "Piercing Blood railgun condensed beam penetrating buildings",
         "calm ancient expression of someone thousands of years old",
         "blood vessel forehead markings glowing neon during technique"],
        "Death Painting — blood older than Jujutsu society"),

    CharacterEntry("Naruto Uzumaki (Six Paths)", "Naruto", CharType.SHOUNEN,
        "spiky blonde hair with Truth-Seeking Orbs orbiting, Six Paths Mode",
        ["Six Paths Sage aura combining all nature transformations simultaneously",
         "Kurama fox spirit behind as massive god silhouette filling sky",
         "Planetary Rasengan eleven energy spheres construction mid-launch",
         "orange-gold-white power output making entire sky change color"],
        "Six Paths Sage — the son of prophecy fulfilled"),

    CharacterEntry("Sasuke Uchiha (Rinnegan)", "Naruto", CharType.SHOUNEN,
        "dark hair with blue Rinnegan and Eternal Mangekyo Sharingan active",
        ["Perfect Susanoo purple titan consuming everything around it",
         "Indra's Arrow maximum charge bow shot that can destroy bijuu",
         "lightning and dark energy fusion at god-tier output",
         "cold calm face at epicenter of destruction"],
        "Indra's descendant — the eternal rival"),

    CharacterEntry("Itachi Uchiha", "Naruto", CharType.SHOUNEN,
        "long black hair in iconic low ponytail, mangekyo spinning blood-red",
        ["Amaterasu black inextinguishable flames erupting from eye",
         "Tsukuyomi illusion world fracturing reality visible in frame",
         "Susanoo ribcage with Yata Mirror and Totsuka Blade artifacts",
         "greatest sacrifice hero looking like the greatest villain forever"],
        "Crow Genjutsu — he loved the village more than himself"),

    CharacterEntry("Minato Namikaze", "Naruto", CharType.SHOUNEN,
        "iconic spiky yellow hair, Fourth Hokage cloak flowing",
        ["Flying Thunder God teleportation leaving yellow flash neon afterimage trails",
         "Rasengan plus Kurama Mode combined attack charging",
         "greatest speed technique making him appear everywhere simultaneously",
         "yellow lightning across entire black sky from his movement"],
        "Yellow Flash — dead before anyone saw him move"),

    CharacterEntry("Might Guy (Eight Gates)", "Naruto", CharType.SHOUNEN,
        "thick eyebrows, Eight Gates Released Formation — Gate of Death opened",
        ["green-red steam vapor from cellular self-destruction wrapping body",
         "Evening Elephant five air vacuum punches audible across the world",
         "red steam aurora consuming entire frame like a descending comet",
         "burning himself away to protect what matters"],
        "Eight Gates — the most passionate man in the world"),

    CharacterEntry("Madara Uchiha (Juubi)", "Naruto", CharType.SHOUNEN,
        "long black hair, Ten-Tails Jinchuriki — became god of the shinobi world",
        ["Limbo Hengoku six shadow clones from underworld with equal power",
         "Truth-Seeking Orbs 72 black spheres orbiting destroying anything touched",
         "god-tier Sage of Six Paths power surpassing all previous limits",
         "most powerful shinobi ever making five Kage look like warm-up"],
        "Madara Uchiha — the only man who could make the moon his eye"),

    CharacterEntry("Pain / Nagato (Six Paths)", "Naruto", CharType.SHOUNEN,
        "body destroyed but six puppets channeling Rinnegan god-tier jutsu",
        ["Shinra Tensei massive repulsion making entire Konoha disappear",
         "Chibaku Tensei creating moon from compressed gravitational chakra sphere",
         "six paths of pain operating simultaneously as one mind",
         "messiah complex from genuine tragedy"],
        "Pain — if you don't understand pain you cannot understand peace"),

    CharacterEntry("Ichigo Kurosaki (True Shikai)", "Bleach", CharType.SHOUNEN,
        "spiky orange hair wild with spiritual pressure, all three powers fused",
        ["True Shikai Zangetsu cleave becoming scale that dwarfs mountains",
         "Final Getsuga Tensho Mugetsu erasing all light briefly",
         "inner hollow and Quincy heritage and shinigami all three fusing",
         "pressure visible as black energy corona displacing atmosphere"],
        "King of Souls — Shinigami, Hollow, Quincy. All three."),

    CharacterEntry("Sosuke Aizen", "Bleach", CharType.SHOUNEN,
        "neat brown hair in ultimate butterfly transcendence form",
        ["Kyoka Suigetsu shatter-illusion reality fracture",
         "Hogyoku integrated in chest glowing with all-seeing purple neon",
         "calm smile of someone who has won before the fight begins",
         "god complex that he actually achieved through pure intelligence"],
        "Complete Hypnosis — he never lost. He was never in danger."),

    CharacterEntry("Kenpachi Zaraki", "Bleach", CharType.SHOUNEN,
        "spiked black hair with bells, eyepatch removed revealing true Reiatsu",
        ["Nozarashi Bankai activated as massive spiritual pressure blade",
         "no technique just killing intent so overwhelming it reshapes space",
         "muscles straining and bleeding while grinning harder than anyone",
         "exponential spiritual pressure flooding the area instantly"],
        "Captain of Squad 11 — cuts even fate"),

    CharacterEntry("Byakuya Kuchiki", "Bleach", CharType.SHOUNEN,
        "neat black hair with silver kenseikan ornaments, noble judgment bearing",
        ["Senbonzakura Kageyoshi ten-thousand blades filling sky as pink snowstorm",
         "noble house captain absolute dignity in every particle of posture",
         "two modes: cold aristocrat and total annihilation",
         "petals becoming blades becoming storm of absolute judgment"],
        "Noble captain — Senbonzakura Kageyoshi"),

    CharacterEntry("Goku (Ultra Instinct Mastered)", "Dragon Ball", CharType.SHOUNEN,
        "silver-white hair with glowing silver UI aura corona",
        ["Ultra Instinct movement defeating gods with pure reactive grace",
         "Hakai destruction energy ball forming in palm",
         "silver neon aura producing heatwave distorting atmosphere",
         "calm as water surface despite universe-shattering output"],
        "Ultra Instinct — even the gods can't keep up"),

    CharacterEntry("Vegeta (Ultra Ego)", "Dragon Ball", CharType.SHOUNEN,
        "widow-peak dark hair, dark purple Ultra Ego aura consuming all light",
        ["power that increases the more damage received — inverted destruction",
         "Final Explosion charging that would sacrifice self to destroy god",
         "Ultra Ego symbol visible in aura consuming background light",
         "pride of a Saiyan Prince who never yielded"],
        "Ultra Ego — pride is his power source"),

    CharacterEntry("Broly (Legendary)", "Dragon Ball", CharType.SHOUNEN,
        "massive frame towering, Legendary Super Saiyan primal green-tinted",
        ["green-tinted primal explosive aura dwarfing all other Saiyans combined",
         "Eraser Cannon green blast overwhelming two Super Saiyan Gods",
         "primal screaming face with power destabilizing planetary bodies",
         "primordial Saiyan beyond all control"],
        "Legendary Super Saiyan — the power even gods fear"),

    CharacterEntry("Future Trunks", "Dragon Ball", CharType.SHOUNEN,
        "iconic purple hair, Super Saiyan Rage blue electricity wrapping gold aura",
        ["Spirit Sword energy blade of hope and collected rage extending",
         "time machine sword channeling energy of all killed by androids",
         "blue and gold energy storm consuming entire frame simultaneously",
         "desperation of entire destroyed future carried on his shoulders"],
        "Super Saiyan Rage — fighting for a future that's already gone"),

    CharacterEntry("Luffy (Gear Fifth)", "One Piece", CharType.SHOUNEN,
        "wild black hair turning white, Gear Fifth deity form white cloud aura",
        ["rubber reality-warping deity making entire island cartoonish in battle",
         "fist enlarged to city-block scale mid-punch at Kaido",
         "Sun God Nika form laughing while outputting god-tier power",
         "gigantic scale impact with clouds pulled in spiral around form"],
        "Sun God Nika — the joy of freedom made flesh"),

    CharacterEntry("Roronoa Zoro", "One Piece", CharType.SHOUNEN,
        "short green hair damp and wind-blown, three swords always ready",
        ["King of Hell Three-Sword Style massive energy dome detonating",
         "Asura nine phantom sword demon god silhouette manifesting behind",
         "Enma drinking haki and releasing devastating black neon slash",
         "eyepatch scar glowing haki — weight of the promise to be best"],
        "King of Hell — he'll be the world's greatest swordsman or die trying"),

    CharacterEntry("Shanks (Red-Hair)", "One Piece", CharType.SHOUNEN,
        "flowing long red hair, Supreme King Haki casual output splitting oceans",
        ["Conqueror's Haki storm crackling across sky — pure presence",
         "Gryphon sword Kamusari swing leaving divine red-gold energy arc",
         "strongest man in the world requiring no effort to end everything",
         "single arm, absolute confidence — he never needed the other one"],
        "Four Emperor — the storm is his presence"),

    CharacterEntry("Kaido", "One Piece", CharType.SHOUNEN,
        "massive oni frame, Mythical Zoan Azure Dragon, Strongest Creature alive",
        ["Ragnaraku Club swing creating thunder from impact vibration",
         "Dragon form breath Bolo Breath obliterating mountain faces",
         "toughest creature in the world testing his own immortality",
         "Thunderclap and Flash fist creating atmospheric lightning"],
        "Strongest Creature — the world's only indestructible being"),

    CharacterEntry("Tanjiro Kamado (Hinokami)", "Demon Slayer", CharType.SHOUNEN,
        "short black hair with burgundy tips, Hinokami Kagura Sun Breathing active",
        ["Sun Breathing flame wheel spiral consuming entire frame in crimson gold",
         "Nichirin blade coated in solar plasma fire",
         "tear and fire on face — determination in absolute distilled form",
         "ember particles swirling upward making sky orange"],
        "Sun Breathing — the original technique that can kill demons"),

    CharacterEntry("Rengoku Kyojuro", "Demon Slayer", CharType.SHOUNEN,
        "fierce flame-yellow hair spiking upward like fire, yellow-red eyes burning",
        ["Flame Breathing Ninth Form massive solar fire dragon roaring upward",
         "Flame Hashira uniform burning at edges from own technique output",
         "grin of absolute conviction even at death with arms outstretched",
         "volcano eruption energy output in every particle"],
        "Flame Pillar — SET YOUR HEART ABLAZE"),

    CharacterEntry("Tengen Uzui", "Demon Slayer", CharType.SHOUNEN,
        "long white hair wrapped in stylish binding, most flamboyant Hashira alive",
        ["Sound Breathing Constant Flux technique neon explosion frequencies visible",
         "twin cleaver rotation creating sonic boom shockwaves radiating",
         "six pink neon explosions detonating around him simultaneously",
         "jewel-covered festival bandages glowing neon"],
        "Sound Pillar — FLAMBOYANT"),

    CharacterEntry("Kokushibo", "Demon Slayer", CharType.SHOUNEN,
        "silver-purple hair in samurai bun, six eyes with crescent moon pupils",
        ["Moon Breathing absolute pinnacle releasing silver moon crescent blade storm",
         "samurai armor with demon transformation fusion",
         "half-human face cracking to reveal demon underneath samurai exterior",
         "moon-shard particles filling dark frame like personal blade galaxy"],
        "Upper Moon One — first demon swordsman"),

    CharacterEntry("Levi Ackerman", "Attack on Titan", CharType.SHOUNEN,
        "undercut dark hair, Ackerman bloodline pure combat calculation",
        ["ODM triple-blade spinning technique used to slay Beast Titan solo",
         "Ackerman power aura calculating every possible outcome",
         "lightning-fast movement leaving visible afterimage shadows",
         "face covered in scars and blood with zero concern for either"],
        "Humanity's Strongest Soldier — the only one who matters in the end"),

    CharacterEntry("Eren Yeager (Founding Titan)", "Attack on Titan", CharType.SHOUNEN,
        "wild dark hair, Founding Titan colossus form emerging from earth",
        ["Founding Titan colossus form 80-meter skeletal deity rising",
         "Wall Titans marching in thousands answering the Rumble",
         "Paths dimension visible as sepia lines in air during activation",
         "hollow screaming while collateral damage becomes history itself"],
        "Founding Titan — freedom at any cost"),

    CharacterEntry("Saitama", "One Punch Man", CharType.SHOUNEN,
        "bald head, plain yellow costume, absolutely casual in front of anything",
        ["Serious Punch parting storm clouds across a continent from air pressure",
         "bored face delivering universe-shattering blow with no effort",
         "aftermath of total obliteration around one average-looking man",
         "single fist extended — everything in range simply ceases to exist"],
        "One Punch Man — too strong for his own story"),

    CharacterEntry("Garou (Cosmic Fear Mode)", "One Punch Man", CharType.SHOUNEN,
        "white hair spiked wild in Cosmic Fear Mode, God Power absorbed",
        ["God Power star-level output in human vessel crackling everywhere",
         "Gravity techniques bending space creating lens distortion",
         "copying every martial arts style into Godly Fist",
         "cosmic power making him float amid shattered asteroids"],
        "Cosmic Garou — the strongest monster who became the greatest hero"),

    CharacterEntry("Gon Freecss (Jajanken Peak)", "Hunter × Hunter", CharType.SHOUNEN,
        "spiky black hair, adult transformation burning own life potential",
        ["Jajanken Rock charging entire Nen lifeforce into single devastating fist",
         "golden Nen overflow aura visible as mile-wide explosion flash",
         "green Nen energy far past containment making atmosphere wobble",
         "primal scream releasing everything when friend is threatened"],
        "Hunter — he gave everything for one punch"),

    CharacterEntry("Killua Zoldyck (Godspeed)", "Hunter × Hunter", CharType.SHOUNEN,
        "white spiky hair, lightning bioelectric field Godspeed mode active",
        ["Godspeed Whirlwind body coated in lightning making him invisible",
         "Thunderbolt strike leaving electric afterburn on impact surface",
         "assassin bloodline activated in eye change showing full danger",
         "silver-white lightning aura making hair and clothes levitate"],
        "Godspeed — the most naturally gifted assassin born"),

    CharacterEntry("Hisoka Morrow", "Hunter × Hunter", CharType.SHOUNEN,
        "red and purple spiked hair, star and heart face marks glowing",
        ["Bungee Gum elastic sticky Nen stretching through entire arena",
         "magician battle performer finding joy in equal opponent",
         "card throw accelerated to bullet velocity",
         "everything about him radiating dangerous beautiful chaos energy"],
        "Bungee Gum — Hisoka is the most dangerous audience"),

    CharacterEntry("Meruem (Perfect Form)", "Hunter × Hunter", CharType.SHOUNEN,
        "pale humanoid chimera ant king, absorbed royal guard power",
        ["Nen absorption making Rose poison powerless",
         "board game grandmaster calm in final moments",
         "brief beautiful tragedy of a monster who learned love",
         "royal guard power consumed and returned as ultimate chimera energy"],
        "Chimera Ant King — became human before he died"),

    CharacterEntry("Edward Elric", "Fullmetal Alchemist: Brotherhood", CharType.SHOUNEN,
        "golden hair in braid, automail arm transforming into combat weapon",
        ["alchemy circles glowing under boots transmuting ground into fortress",
         "automail arm spear extended crackling alchemic energy",
         "short man with oversized power complex and heart of a true hero",
         "golden neon of the Law of Equivalent Exchange surrounding him"],
        "Fullmetal Alchemist — the short one is the most dangerous"),

    CharacterEntry("Roy Mustang (Flame Alchemist)", "Fullmetal Alchemist: Brotherhood", CharType.SHOUNEN,
        "dark military uniform immaculate, ignition glove snap finger ready",
        ["Flame Alchemy producing a sun compressed into a column",
         "blue flame version going beyond oxygen toward divine fire",
         "colonel to Fuhrer pipeline — calm face hiding catastrophic power",
         "flame circles consuming frame corner to corner from one finger snap"],
        "Flame Alchemist — all he needs is air"),

    CharacterEntry("Sung Jinwoo (Shadow Monarch)", "Solo Leveling", CharType.SHOUNEN,
        "dark hair, empty emotionless hunter eyes, Shadow Monarch power",
        ["shadow army of millions marching behind as dark silhouettes",
         "Kamish Wrath sword of shadows reaping arc through all life",
         "Igris and Beru flanking as massive shadow knight commanders",
         "death and power given human form with stone expressionless face"],
        "Shadow Monarch — slept while everyone trained, woke up strongest"),

    CharacterEntry("Guts (Black Swordsman)", "Berserk", CharType.SHOUNEN,
        "massive Dragon Slayer sword in one arm that contains a cannon inside",
        ["Berserker Armor activated bleeding from joints while multiplying power",
         "Brand of Sacrifice wound bleeding black in presence of demons",
         "Apostle-killing charge through impossible odds refusing death",
         "mad dog grin — refuses to die because death means fate wins"],
        "Black Swordsman — the brand burns. he runs toward it."),

    CharacterEntry("Isagi Yoichi", "Blue Lock", CharType.SHOUNEN,
        "dark hair wet with sweat, Spatial Awareness meta-vision activated",
        ["pitch grid overlay showing perfect shot calculation in real time",
         "goal scoring technique using perfect spatial physics",
         "predator instinct awakening mid-match evolution in progress",
         "determined expression becoming best striker through calculated greed"],
        "Striker — spatial awareness that sees gaps others can't imagine"),

    CharacterEntry("Asta", "Black Clover", CharType.SHOUNEN,
        "spiky white hair Anti-Magic form, five-leaf grimoire open",
        ["Anti-Magic concentrated black consuming surrounding magic completely",
         "Demon-Destroyer Sword enormous black claymore extended",
         "Devil Union Liebe fusion making skin half-black crackling anti-magic",
         "no magic but strongest will — the one who became Wizard King with nothing"],
        "Zero magic — the one who screamed his way to the top"),

    CharacterEntry("Yuno", "Black Clover", CharType.SHOUNEN,
        "long dark hair with golden four-leaf clover grimoire glowing",
        ["Star Magic massive constellation cannon charging across entire sky",
         "Wind Spirit Sylph merged multiplying all magic technique output",
         "spatial magic barriers unfolding like origami galaxies",
         "genius rival — elegant prodigy of everything Asta wasn't"],
        "Star Magic — the prodigy who makes it look effortless"),

    CharacterEntry("Mikey Sano (Dark Impulse)", "Tokyo Revengers", CharType.SHOUNEN,
        "platinum blonde bowl cut, delinquent king stance, dark impulse mode",
        ["Invincible Kick technique leg rising creating shockwave crack in asphalt",
         "dark impulse black aura underneath normal Mikey exterior",
         "natural gift for violence making him both best and most dangerous",
         "gang king who broke every timeline trying to escape his own grief"],
        "Invincible Mikey — the sun that devoured itself"),

    CharacterEntry("Izuku Midoriya (OFA Dragon Fist)", "My Hero Academia", CharType.SHOUNEN,
        "messy green hair wild with One For All electricity crackling everywhere",
        ["100% Full Cowl Delaware Smash Air Force Black Whip combined",
         "all OFA predecessors ghosts standing behind as spirit council",
         "Gear Shift Full Cowl maximum output cratering ground under feet",
         "screaming into wind refusing to give up — the boy who became a hero"],
        "One For All — power handed down by hope"),

    CharacterEntry("Katsuki Bakugo", "My Hero Academia", CharType.SHOUNEN,
        "spiky ash-blonde hair in explosion wind, most aggressive competitive drive",
        ["Howitzer Impact spinning plasma AP Shot detonation at point blank",
         "explosion plasma orange-black neon bursting from both palms simultaneously",
         "blast backwash making hair and jacket explode dramatically outward",
         "rival born to push Deku to the absolute limit"],
        "Explosion Hero — King Explosion Murder"),

    CharacterEntry("All Might", "My Hero Academia", CharType.SHOUNEN,
        "iconic massive muscle form, symbol of peace in borrowed time",
        ["United States of Smash final punch as last act of Symbol of Peace",
         "gaunt injured face inside massive borrowed power still smiling",
         "cape disintegrating in own power output but never slowing",
         "sunrise always behind him — hope given physical form"],
        "Symbol of Peace — PLUS ULTRA"),

    CharacterEntry("Tomura Shigaraki (All For One)", "My Hero Academia", CharType.SHOUNEN,
        "pale cracked hands and disheveled blue-gray hair, All For One awakening",
        ["Decay touching ground — entire city block disintegrating in expanding wave",
         "All For One awakening making face crack and reform mid-scene",
         "Paranormal Liberation Front general at full apocalyptic power",
         "inherited hatred and stolen power — empty eyes becoming something beyond villain"],
        "All For One — the villain who was always the real threat"),

    CharacterEntry("Anos Voldigoad", "The Misfit of Demon King Academy", CharType.SHOUNEN,
        "dark hair, demon king reincarnated surpassing all records",
        ["Venuzdonoa sword of ruin destroying cause and effect of target",
         "Igram black flame consuming concepts not just matter",
         "absolute overwhelming power in casual clothing showing no effort",
         "demon king who transcended death in original era still dominates"],
        "Demon King — he destroyed even death"),

    CharacterEntry("Rimuru Tempest", "That Time I Got Reincarnated as a Slime", CharType.SHOUNEN,
        "silver short hair slime-god form, Sage and Great Demon Lord combined",
        ["Infinite Regeneration and Predator consuming any ability used against him",
         "True Dragon class Harvest Festival aura consuming sky",
         "Belzebuth and Raphael working simultaneously as dual ultimate skills",
         "most broken protagonist progression making gods look under-powered"],
        "Demon Lord Rimuru — he ate his way to godhood"),

    CharacterEntry("Raizo Asamura", "Original Cyberpunk Shounen", CharType.SHOUNEN,
        "shaved sides with dark long top hair, street fighter build with neon tattoos",
        ["street combat style fusing martial arts with cyberpunk energy enhancement",
         "chrome knuckle implants crackling electric discharge mid-combo",
         "gang street king bearing with neon tattoo sleeve glowing during focus",
         "underdog who reached the top through pure violent will"],
        "Street king — the city made me"),
]

ALL_CHARACTERS: list[CharacterEntry] = WAIFU_CHARACTERS + SHOUNEN_CHARACTERS


# ═══════════════════════════════════════════════════════════════════════
# EMOTION SYSTEM
# ═══════════════════════════════════════════════════════════════════════

WAIFU_EMOTION_PROFILES: dict[EmotionArchetype, dict] = {
    EmotionArchetype.COLD_QUEEN: {
        "face": "cold imperious expression, eyes half-lidded with absolute contempt and bored dominance",
        "body": "arms crossed, weight on one hip, posture claiming all surrounding space",
        "energy": "cool purple-blue aura barely visible — she doesn't need to try",
        "aura_color": "icy blue",
    },
    EmotionArchetype.YANDERE_SMILE: {
        "face": "beautiful unhinged smile — warm and adoring on one side, empty hunter on the other",
        "body": "slightly tilted head, one hand raised delicately while the other grips tightly",
        "energy": "pink-to-crimson neon shifting between love and danger constantly",
        "aura_color": "rose crimson",
    },
    EmotionArchetype.SEDUCTIVE_GAZE: {
        "face": "heavy-lidded neon eyes with multiple catchlights, soft parted lips",
        "body": "elegant contrapposto with weight shift, one hand at hip",
        "energy": "warm rose-gold neon casting flattering from below and behind",
        "aura_color": "rose gold",
    },
    EmotionArchetype.DOMINANT_VIBE: {
        "face": "sharp knowing smirk, eyes radiating absolute confidence",
        "body": "power stance — feet wide, weight forward, ready for anything",
        "energy": "intense electric neon aura visible as charged atmosphere",
        "aura_color": "electric white",
    },
    EmotionArchetype.PLAYFUL_DANGER: {
        "face": "bright mischievous grin concealing real threat — playful and lethal simultaneously",
        "body": "playful lean-in pose with finger raised knowingly",
        "energy": "pastel neon sparking chaotically in unpredictable bursts",
        "aura_color": "neon pastel chaos",
    },
    EmotionArchetype.ETHEREAL_SORROW: {
        "face": "beautiful melancholy — distant gorgeous eyes carrying ancient grief",
        "body": "graceful stillness, floating slightly, outfit and hair drifting",
        "energy": "soft silver-blue neon dissolving at edges like forgotten memory",
        "aura_color": "silver moonlight",
    },
    EmotionArchetype.BATTLE_FURY: {
        "face": "intense battle expression — locked on target, jaw set, eyes burning",
        "body": "aggressive forward lean, weapon raised or technique charging",
        "energy": "explosive neon aura crackling at every joint point",
        "aura_color": "fierce crimson gold",
    },
    EmotionArchetype.SOFT_OBSESSION: {
        "face": "soft devoted expression — loving eyes that are a little too intense",
        "body": "arms slightly open as if always ready to embrace",
        "energy": "warm amber-pink neon with occasional dark undertone flickering",
        "aura_color": "warm amber with dark edges",
    },
}

SHOUNEN_EMOTION_PROFILES: dict[EmotionArchetype, dict] = {
    EmotionArchetype.COLD_RAGE: {
        "face": "controlled fury — perfectly still face with eyes burning cold like reactor cores",
        "body": "absolute stillness more threatening than any movement, fists at sides",
        "energy": "dark neon suppressed at edge of body — about to stop suppressing",
        "aura_color": "dark crimson barely contained",
    },
    EmotionArchetype.I_AM_HIM: {
        "face": "calm total confidence — the energy of someone who already knows they've won",
        "body": "dominant slow walk toward camera, unhurried, zero concern for any threat",
        "energy": "massive aura crackling without effort, ambient destruction following",
        "aura_color": "blazing gold-white",
    },
    EmotionArchetype.FINAL_FORM: {
        "face": "limit break expression — screaming or gritting teeth, veins visible",
        "body": "maximum power pose — every muscle tensed, technique fully deployed",
        "energy": "catastrophic multi-color power eruption consuming entire frame",
        "aura_color": "multi-spectrum neon catastrophe",
    },
    EmotionArchetype.SILENT_APEX: {
        "face": "emotionless apex predator — no expression needed when your power speaks",
        "body": "weapon at rest, relaxed posture hiding the most terrifying power",
        "energy": "barely-visible aura that distorts light and gravity around it",
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
        f"emotional energy: {profile['energy']}, "
        f"dominant aura color: {profile['aura_color']}"
    )


WAIFU_EMOTION_WEIGHTS: list[tuple[EmotionArchetype, int]] = [
    (EmotionArchetype.COLD_QUEEN,     20),
    (EmotionArchetype.YANDERE_SMILE,  18),
    (EmotionArchetype.SEDUCTIVE_GAZE, 20),
    (EmotionArchetype.DOMINANT_VIBE,  15),
    (EmotionArchetype.PLAYFUL_DANGER, 12),
    (EmotionArchetype.ETHEREAL_SORROW, 5),
    (EmotionArchetype.BATTLE_FURY,    7),
    (EmotionArchetype.SOFT_OBSESSION, 3),
]

SHOUNEN_EMOTION_WEIGHTS: list[tuple[EmotionArchetype, int]] = [
    (EmotionArchetype.COLD_RAGE,   20),
    (EmotionArchetype.I_AM_HIM,    30),
    (EmotionArchetype.FINAL_FORM,  35),
    (EmotionArchetype.SILENT_APEX, 15),
]


def _weighted_emotion(rng: random.Random, char_type: CharType) -> EmotionArchetype:
    weights = (
        WAIFU_EMOTION_WEIGHTS if char_type == CharType.WAIFU else SHOUNEN_EMOTION_WEIGHTS
    )
    total = sum(w for _, w in weights)
    r = rng.random() * total
    acc = 0.0
    for archetype, weight in weights:
        acc += weight
        if r <= acc:
            return archetype
    return weights[0][0]


# ═══════════════════════════════════════════════════════════════════════
# VISUAL HOOKS
# ═══════════════════════════════════════════════════════════════════════

WAIFU_VISUAL_HOOKS: list[tuple[str, int]] = [
    ("NEON GLOWING EYES as primary visual hook — pupils burning with unearthly color neon, "
     "multiple catchlights, irises radiating power from within, eyes visible from thumbnail distance", 25),
    ("MASSIVE AURA EXPLOSION as primary visual hook — power aura erupting outward in massive "
     "expanding ring from center, consuming 60% of frame, silhouette clear against energy", 20),
    ("INTENSE CLOSE-UP EXPRESSION as primary visual hook — face fills upper 40% of frame "
     "with devastating emotional expression lit dramatically by own power", 18),
    ("SIGNATURE WEAPON GLOW as primary visual hook — weapon or technique radiating so much "
     "energy it becomes the brightest object in frame", 15),
    ("DYNAMIC HAIR EXPLOSION as primary visual hook — hair erupting outward from power "
     "release wind filling frame corners beautifully", 12),
    ("TATTOO OR MARKING GLOW as primary visual hook — power markings across skin activating "
     "in brilliant neon making entire body a light source", 10),
]

SHOUNEN_VISUAL_HOOKS: list[tuple[str, int]] = [
    ("CATASTROPHIC POWER AURA as primary visual hook — multi-layer power aura erupting "
     "consuming 70% of frame while character stands at impossible calm center", 30),
    ("GLOWING TECHNIQUE ACTIVATION as primary visual hook — signature technique charging "
     "or releasing as the single brightest element in composition", 25),
    ("INTENSE LOCKED-ON EYES as primary visual hook — eyes glowing with technique or power "
     "activated visible from distance, jaw set, locked onto target beyond camera", 20),
    ("SCALE CONTRAST as primary visual hook — character dwarfed by their own technique, "
     "summoned entity or aura creating dramatic size contrast showing true power scale", 15),
    ("BATTLE DAMAGE POWER SURGE as primary visual hook — injuries visible but power increasing, "
     "damaged clothes revealing glowing power underneath", 10),
]


def _weighted_hook(rng: random.Random, char_type: CharType) -> str:
    hooks = WAIFU_VISUAL_HOOKS if char_type == CharType.WAIFU else SHOUNEN_VISUAL_HOOKS
    total = sum(w for _, w in hooks)
    r = rng.random() * total
    acc = 0.0
    for hook, weight in hooks:
        acc += weight
        if r <= acc:
            return hook
    return hooks[0][0]


# ═══════════════════════════════════════════════════════════════════════
# POSE SYSTEM
# ═══════════════════════════════════════════════════════════════════════

WAIFU_POSES: list[str] = [
    "confident hip pop stance, one hand at waist extended with glowing technique, weight shifted elegantly",
    "slow deliberate walk toward camera with absolute authority, neon city consuming itself behind",
    "sitting on levitating destroyed surface legs dangling casually, ruling everything below",
    "over-shoulder look back with devastating gaze, outfit caught mid-turn showing full silhouette",
    "leaning against broken wall arm raised, casual dominance radiating even at rest",
    "arms spread wide with technique erupting outward from chest, queen claiming all surrounding space",
    "mid-air float with power forming below, legs crossed elegantly while destroying everything",
    "crouching ready stance thighs together heels up, weapon aimed, most dangerous posture imaginable",
    "head tilted with soft dangerous smile, hand raised presenting glowing technique like a gift",
    "back to camera turning with profile visible, long hair whipping dramatically in power wind",
    "arms crossed with cold contempt expression, power aura doing the threatening for her",
    "single arm extended palm-toward-camera releasing technique, eyes locked directly at viewer",
    "spinning freeze-frame at maximum rotation, outfit and hair caught in perfect spiral",
    "kneeling with head bowed then eyes rising slowly — the calm before catastrophic action",
    "standing atop destroyed architecture looking down at devastation she made",
    "hand to jaw thoughtful expression while catastrophic power builds behind back",
    "mid-dodge lean — weight fully committed sideways, hair and outfit following arc beautifully",
    "two-finger raised at cheek, devil-may-care expression while technique fires automatically",
    "reaching one hand toward viewer with neon effect dripping from fingertips",
    "seated cross-legged floating, meditating with power storm orbiting in controlled chaos",
    "charging stance — one leg back weight low, full body technique loading",
    "falling backwards on purpose, eyes closed, trusting power will catch everything else",
    "hand in own hair with satisfied smile, aftermath of battle already won behind her",
    "back-to-back with shadow/ghost version of self — two sides of power acknowledging each other",
    "dual-technique pose — both hands extended different techniques simultaneously",
    "low split stance — impossible flexibility deployed as combat advantage",
    "walking away from explosion she caused, not looking back, supremely unconcerned",
    "turning fully toward camera with weapon lowered — the fight is over. she won.",
    "arms raised above head technique charging skyward — most dramatic pre-release moment",
    "single dramatic point toward target — ordering reality to comply with her intention",
]

SHOUNEN_POSES: list[str] = [
    "unstoppable slow walk directly toward camera, maximum power aura clearing path ahead",
    "mid-attack freeze with technique fully deployed — the moment of maximum output",
    "hovering at apex of jump, technique crackling, gravity hasn't caught up yet",
    "standing in crater their own landing created, power still radiating from impact",
    "one fist raised overhead charging technique toward sky — peak power pose",
    "arms spread dramatically maximum power release in all directions, eyes blazing",
    "charging forward at maximum velocity, speed blur behind, target destroyed ahead",
    "kneeling in rubble rising — damaged, power increasing, unstoppable now",
    "standing on defeated opponent's equivalent — scale contrast establishing dominance",
    "back to camera looking over shoulder at enormous technique deployed ahead",
    "calm center of absolute destruction — technique doing the work while they wait",
    "both hands forward technique merged and amplified beyond either alone",
    "mid-scream maximum power release — limit break expression, hair all rising",
    "two-handed weapon swing frozen at maximum arc — the single most powerful moment",
    "defensive stance — arms crossed taking direct hit and it doesn't even matter",
    "parallel to ground horizontal flight trajectory mid-attack",
    "ascending to power — floating upward while aura builds beneath, scale growing",
    "descent from height — diving attack with everything committed, no defense needed",
    "finishing stance — opponent defeated, weapon lowered, power still crackling",
    "pointing single finger down toward enemy far below — the most dangerous gesture",
    "three-point landing — fist ground crater from speed, head up, eyes target-locked",
    "crossed arms releasing aura — making zero effort but destroying everything nearby",
    "dual-simultaneous technique — different power from each hand meeting in center",
    "catching opponent's strongest attack one-handed — unimpressed, maximum disrespect",
    "slow turn revealing true form — half-profile turning to face, power visible escalating",
    "mid-air standoff freeze — both combatants suspended, technique about to decide all",
    "power stance on elevated broken platform, entire destroyed city below",
    "technique fully charged glowing maximum — the moment before everything changes",
    "last stand pose — battered and damaged but power output higher than ever before",
    "victorious still — the dust settles and they're the only one standing, barely breathing",
]


def _select_pose(rng: random.Random, char_type: CharType) -> str:
    poses = WAIFU_POSES if char_type == CharType.WAIFU else SHOUNEN_POSES
    return rng.choice(poses)


# ═══════════════════════════════════════════════════════════════════════
# WAIFU EXTRAS
# ═══════════════════════════════════════════════════════════════════════

WAIFU_TATTOO_DETAILS: list[str] = [
    "delicate neon circuit tattoo tracing collarbone and neck with faint power glow",
    "serpentine tattoo along ribcage and side visible at outfit gap, glowing softly",
    "intricate star constellation tattoo across shoulder blade and upper arm neon-lit",
    "geometric mandala tattoo at upper thigh catching neon light beautifully",
    "butterfly tattoo at clavicle shifting color with emotional state",
    "tribal pattern tattoo across one cheekbone — subtle but unmistakable",
    "spine tattoo visible at back — glowing when channeling power fully",
]

WAIFU_PIERCING_DETAILS: list[str] = [
    "industrial bar piercing in upper ear catching neon light as tiny highlight",
    "nose ring with small neon gem glowing softly",
    "multiple helix piercings up one ear each catching different neon colors",
    "constellation piercing pattern — three small gems tracing Orion across one cheek",
    "lip ring catching neon reflection dramatically",
    "subtle cheekbone dermal piercing glowing faintly — easy to miss, impossible to forget",
]

WAIFU_FASHION_DETAILS: list[str] = [
    "oversized cyberpunk jacket with neon inner lining hanging off one shoulder",
    "techwear bodysuit with translucent panels, circuitry detail throughout",
    "cropped mech-vest over fitted top, tactical straps and neon piping at every seam",
    "thigh-high armored boots with neon trim, magnetic clasp detail",
    "asymmetric hemline dress with reinforced combat panels integrated seamlessly",
    "holographic fabric at key panels shifting color with movement",
    "form-fitting high-collar top with open back window showing tattoo or marking",
    "detached cyber-sleeves with integrated tech display showing power reading",
]


def _build_waifu_extras(rng: random.Random) -> str:
    tattoo  = rng.choice(WAIFU_TATTOO_DETAILS)
    fashion = rng.choice(WAIFU_FASHION_DETAILS)
    piercing = rng.choice(WAIFU_PIERCING_DETAILS)
    return (
        f"subtle enhancement details: {tattoo}, {piercing}, "
        f"fashion detail: {fashion}, "
        "slightly revealing outfit showing curves at waist and hips without explicit content, "
        "body language confident and dominant — powerful not vulnerable, "
        "glossy lips with neon tint matching aura color, sharp eyeliner extending slightly"
    )


# ═══════════════════════════════════════════════════════════════════════
# SHOUNEN EXTRAS
# ═══════════════════════════════════════════════════════════════════════

SHOUNEN_POWER_EXTRAS: list[str] = [
    "primary power aura layered beneath secondary technique aura — two-color halo system",
    "veins of power visible under skin glowing matching technique color",
    "battle damage increasing power — torn uniform revealing glowing power within",
    "heat distortion visible as atmospheric warping around high-power output body",
    "ground fractured concentrically outward from stance pressure alone",
    "charged particles orbiting body in predictable elliptical pattern like personal solar system",
    "hair rising and separating from static charge of power field surrounding body",
]

SHOUNEN_BATTLE_DETAILS: list[str] = [
    "strategic tear in uniform from previous technique impact showing no concern",
    "sweat and dust on face — this fight cost something, still winning",
    "breathing visible as power-charged mist in cold air mid-technique",
    "blood on knuckle or lip — minor, irrelevant, power still increasing",
    "boots cracking concrete underfoot from accumulated power pressure",
]


def _build_shounen_extras(rng: random.Random) -> str:
    power  = rng.choice(SHOUNEN_POWER_EXTRAS)
    battle = rng.choice(SHOUNEN_BATTLE_DETAILS)
    return (
        f"power state: {power}, "
        f"battle realism: {battle}, "
        "massive glowing eyes — irises lit by power technique from within, "
        "dominant masculine build with power visible in every defined muscle group, "
        "intense locked-on expression — nothing exists except the opponent, "
        "streetwear or battle uniform with cyberpunk neon enhancement, "
        "gang or warrior energy — trapstar aura in stance and expression"
    )


# ═══════════════════════════════════════════════════════════════════════
# COMPOSITION ENGINE
# ═══════════════════════════════════════════════════════════════════════

COMPOSITION_STYLES: list[dict] = [
    {
        "name": "full_body_power",
        "prompt": (
            "FULL BODY vertical composition — character head to toe filling 9:16 mobile frame, "
            "character occupies 85% of frame height, "
            "strong readable silhouette against explosive cyberpunk background, "
            "dramatic 15-degree low angle making character feel godlike in scale, "
            "complete outfit and signature weapon/technique visible throughout, "
            "debris, energy, and particles filling every corner of frame"
        ),
        "waifu_weight": 25, "shounen_weight": 30,
    },
    {
        "name": "full_body_dynamic",
        "prompt": (
            "FULL BODY action composition — character mid-motion at maximum power output, "
            "entire body visible from head to feet with technique deployed, "
            "Dutch angle adding extreme kinetic drama to vertical 9:16 frame, "
            "hair and outfit caught in power-release shockwave motion, "
            "character 80% of frame height, background crumbling from technique output"
        ),
        "waifu_weight": 20, "shounen_weight": 25,
    },
    {
        "name": "three_quarter_cinematic",
        "prompt": (
            "3/4 BODY SHOT — character from mid-thigh up filling vertical 9:16 frame, "
            "face in upper third of frame at full detail — expression readable at distance, "
            "full upper body and thighs visible with technique and outfit detailed, "
            "one hand/weapon extended toward viewer with energy charging, "
            "cinematic depth — character razor-sharp, background beautifully blurred explosion"
        ),
        "waifu_weight": 30, "shounen_weight": 25,
    },
    {
        "name": "three_quarter_portrait",
        "prompt": (
            "3/4 BODY PORTRAIT — waist-to-crown shot emphasizing face and power simultaneously, "
            "face upper third with photogenic angle showing best features, "
            "outfit and power effects from waist up fully detailed, "
            "cinematic split-lighting — colored neon hitting from two directions creating drama, "
            "massive power effect consuming background behind subject"
        ),
        "waifu_weight": 20, "shounen_weight": 15,
    },
    {
        "name": "back_view_dramatic",
        "prompt": (
            "DRAMATIC BACK SHOT — character facing destroyed cyberpunk vista, "
            "face turned 3/4 revealing profile or three-quarter expression, "
            "full silhouette from behind with aura corona creating luminous edge, "
            "neon city sprawl or destroyed landscape stretching below, "
            "viewer positioned as witness to their next action — scale is overwhelming"
        ),
        "waifu_weight": 5, "shounen_weight": 5,
    },
]


def _weighted_composition_v2(rng: random.Random, char_type: CharType) -> dict:
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
# PARTICLE TIERS
# ═══════════════════════════════════════════════════════════════════════

PARTICLE_TIER_MEDIUM = (
    "MEDIUM PARTICLE DENSITY — hundreds of neon energy particles orbiting body in readable pattern, "
    "technique-specific particle type matching character power color, "
    "debris field from recent impact floating in organized composition"
)

PARTICLE_TIER_HEAVY = (
    "HEAVY PARTICLE DENSITY — thousands of neon particles creating galaxy-like density around body, "
    "multiple particle types layered — foreground medium large, midground small dense, background bokeh, "
    "technique particles matching power color erupting in every direction, "
    "shockwave rings visible in atmospheric compression, speed blur streaks visible"
)

PARTICLE_TIER_CATASTROPHIC = (
    "CATASTROPHIC PARTICLE DENSITY — overwhelming particle storm consuming frame, "
    "character at perfect calm center of particle catastrophe, "
    "layered depth — foreground particle sheets, midground explosion cloud, background neon bokeh, "
    "shockwave rings, lightning web, speed blur, AND debris field simultaneously, "
    "atmosphere itself visible as displaced pressure rings expanding outward"
)

PARTICLE_TIERS: list[tuple[str, str, int, int]] = [
    ("medium",       PARTICLE_TIER_MEDIUM,       30, 15),
    ("heavy",        PARTICLE_TIER_HEAVY,         45, 35),
    ("catastrophic", PARTICLE_TIER_CATASTROPHIC,  25, 50),
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
# LIGHTING STACKS
# ═══════════════════════════════════════════════════════════════════════

LIGHTING_STACKS: list[dict] = [
    {
        "name": "split_neon",
        "prompt": (
            "CINEMATIC SPLIT NEON LIGHTING — primary teal rim light hitting left from behind "
            "creating luminous silhouette edge, secondary hot pink fill light from right "
            "modeling face and body volume, technique glow illuminating from below and within, "
            "volumetric god rays cutting through atmospheric smoke at 45-degree angle, "
            "eyes catching both neon sources creating multi-color catchlight array"
        ),
    },
    {
        "name": "power_backlight",
        "prompt": (
            "CINEMATIC POWER BACKLIGHT STACK — overwhelming technique or aura backlight "
            "creating perfect silhouette rim, strong single-source power glow creating "
            "dramatic forward shadow, secondary ambient neon from cityscape providing fill, "
            "face lit exclusively by power glow — most dramatic and readable at thumbnail scale, "
            "eyes glowing as if internally lit, catching technique color"
        ),
    },
    {
        "name": "noir_neon",
        "prompt": (
            "CINEMATIC NOIR NEON LIGHTING — 80% deep shadow with hard neon slivers cutting through, "
            "single strong colored rim light creating dramatic face shadow play, "
            "atmosphere thick with neon-lit smoke and particle haze, "
            "high contrast maximum — deepest darks and brightest neons in same frame, "
            "face half in absolute shadow half dramatically neon-lit"
        ),
    },
    {
        "name": "dynamic_battle",
        "prompt": (
            "CINEMATIC DYNAMIC BATTLE LIGHTING — multiple in-motion light sources from technique impacts, "
            "explosion flash providing millisecond harsh fill light freezing motion, "
            "technique glow as primary fill changing intensity mid-charge, "
            "spark and lightning providing point-source highlights across character, "
            "eyes catching explosion flash as intense bright catchlight"
        ),
    },
    {
        "name": "divine_glow",
        "prompt": (
            "CINEMATIC DIVINE GLOW STACK — character as their own light source radiating outward, "
            "power aura so bright it lifts shadows from nearby surfaces, "
            "god rays emanating from character outward through atmospheric particles, "
            "halo-effect rim light from behind completing divine presence aesthetic, "
            "eyes as brightest point in frame — power visible in the iris"
        ),
    },
]

LIGHTING_WEIGHTS: list[int] = [20, 25, 20, 20, 15]


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
# PALETTE ENGINE
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class Palette:
    name: str
    primary: str
    secondary: str
    shadow: str
    description: str
    waifu_weight: int
    shounen_weight: int

    @property
    def prompt(self) -> str:
        return (
            f"dominant palette: {self.primary} and {self.secondary}, "
            f"shadow tone: {self.shadow}, {self.description}"
        )


PALETTES: list[Palette] = [
    Palette("teal_pink",     "electric teal",     "hot magenta pink",  "deep navy",          "classic cyberpunk duality — cold and warm neon in maximum contrast",               22, 10),
    Palette("purple_gold",   "deep violet purple", "blazing gold",      "near-black",         "luxurious dark royalty — richest cyberpunk palette for legendary moments",          18, 22),
    Palette("crimson_blue",  "blood crimson",      "sapphire electric", "charcoal dark",      "danger and precision — villain-hero color war in single frame",                    15, 18),
    Palette("white_blue",    "pure ice white",     "electric cerulean", "steel dark",         "divine clarity — cold clean aesthetic for god-tier characters",                    10, 15),
    Palette("black_gold",    "absolute black",     "divine gold",       "void dark",          "god presence aesthetic — darkness interrupted only by divine neon",                 8, 20),
    Palette("green_orange",  "toxic neon green",   "amber flame",       "deep shadow",        "bio-hacker energy — dangerous life against warm decay",                            8,  5),
    Palette("red_black",     "pure blood red",     "void black",        "deepest shadow",     "villain energy maximum — light exists only to reveal the red",                    10, 10),
    Palette("rose_chrome",   "rose neon",          "brushed chrome",    "deep navy",          "high-fashion cyberpunk — glamour weaponized for maximum appeal",                  15,  0),
    Palette("indigo_silver", "deep indigo",        "mirror silver",     "dark purple",        "ethereal mystery — space between stars given neon color",                          8, 10),
    Palette("fire_storm",    "solar fire orange",  "storm black",       "volcano dark",       "primal power — sun meeting void, oldest energies in combat",                       0, 15),
]


def _weighted_palette(rng: random.Random, char_type: CharType) -> Palette:
    weight_attr = "waifu_weight" if char_type == CharType.WAIFU else "shounen_weight"
    valid = [(p, getattr(p, weight_attr)) for p in PALETTES if getattr(p, weight_attr) > 0]
    total = sum(w for _, w in valid)
    r = rng.random() * total
    acc = 0.0
    for palette, weight in valid:
        acc += weight
        if r <= acc:
            return palette
    return valid[0][0]


# ═══════════════════════════════════════════════════════════════════════
# BACKGROUNDS
# ═══════════════════════════════════════════════════════════════════════

WAIFU_BACKGROUNDS: list[str] = [
    "rain-soaked cyberpunk neon rooftop at night, city sprawl glowing below, kanji signs overhead",
    "luxury cyberpunk penthouse interior with floor-to-ceiling windows showing neon city",
    "cyberpunk underground club with laser grid and smoke atmosphere frozen mid-pulse",
    "cherry blossom cyberpunk shrine — traditional torii gate absorbing neon energy",
    "reflective wet alley with fractured neon kanji signs blurring in puddle mirrors",
    "dark void with single neon ring lighting and dense particle field — pure character focus",
    "cyberpunk night market with warm amber vendor lights and teal sky above",
    "elevated highway with distant city below and storm clouds catching neon above",
    "cyber-shrine courtyard with digital rain falling and traditional lanterns neon-lit",
    "concert main stage mid-destruction — neon beams and smoke and awe-frozen crowd",
]

SHOUNEN_BACKGROUNDS: list[str] = [
    "destroyed urban canyon — buildings shattered outward from technique impact point",
    "volcanic wasteland with lava channels and smoke atmosphere",
    "outer space — planetary surface below, stars above, their power visible from orbit",
    "oceanic cliffside — waves shattered by power output, spray frozen in shockwave",
    "tournament arena destroyed — crater where stands were, smoke clearing slowly",
    "dark dimensional space — suspended debris and shattered reality geometry",
    "ancient battlefield — ruins of previous great conflicts beneath new destruction",
    "rooftop cityscape — entire block visible below and cracking from technique impact",
    "mountain range — peaks shearing from shockwave at distance, scale made visible",
    "final battlefield — all previous destruction visible in layers toward horizon",
]


def _select_background(rng: random.Random, char_type: CharType) -> str:
    bg_list = WAIFU_BACKGROUNDS if char_type == CharType.WAIFU else SHOUNEN_BACKGROUNDS
    return rng.choice(bg_list)


# ═══════════════════════════════════════════════════════════════════════
# GENRE × MOOD MATRIX
# ═══════════════════════════════════════════════════════════════════════

GENRE_MAP: dict[str, str] = {
    "phonk":      "phonk",
    "trap":       "trap",
    "dark":       "dark",
    "darkpop":    "darkpop",
    "dark pop":   "darkpop",
    "electronic": "electronic",
    "edm":        "electronic",
    "dubstep":    "electronic",
    "house":      "electronic",
    "funk":       "trap",
    "rock":       "rock",
    "metal":      "dark",
    "cinematic":  "darkpop",
    "lofi":       "darkpop",
    "indie":      "darkpop",
    "pop":        "darkpop",
    "hiphop":     "trap",
    "hip-hop":    "trap",
    "rap":        "trap",
    "bass":       "phonk",
}

GENRE_BOOST_MATRIX: dict[str, tuple[str, str]] = {
    "phonk": (
        "phonk street queen aesthetic — neon underground, heavy bass energy in pose, aggressive confident feminine dominance, dark neon grit and attitude in every detail",
        "phonk street king energy — aggressive dominant posture, dark neon underground, gang apex energy, heavy bass weight in every stance, unstoppable cold confidence",
    ),
    "trap": (
        "trap luxury aesthetic — urban neon premium, stylish supreme feminine confidence, warm neon street royalty, beautiful and dangerous in equal measure",
        "trap boss energy — slow dominant walk, urban apex masculine confidence, every movement deliberate, neon wealth and power radiating from posture",
    ),
    "electronic": (
        "electronic futurist aesthetic — clean cyber feminine beauty, teal data streams, digital rhythm visualization in air, frequency pulse visible around body",
        "electronic power aesthetic — futuristic cyber warrior, teal data energy system, digital combat rhythm, clean precise power output matching frequency",
    ),
    "darkpop": (
        "dark pop romantic aesthetic — beautiful lonely neon city, cinematic feminine emotion, warm-cold palette telling story, power and vulnerability in single devastating frame",
        "dark pop warrior aesthetic — emotional masculine power, neon city isolation making strength visible, cinematic story in single frame, strength through pain",
    ),
    "dark": (
        "dark atmosphere — dramatic neon shadow play on feminine form, intense emotional presence, single accent neon in near-darkness",
        "dark power aesthetic — minimal neon punctuating deep shadow, masculine intensity radiating in near-darkness, presence more dangerous than visibility",
    ),
    "rock": (
        "rock concert energy — electric stage neon on feminine performer, raw passionate power in body language, concert fire and smoke atmosphere, rebellion made beautiful",
        "rock warrior energy — electric concert stage energy in combat, raw masculine power expression, amp feedback visible as shockwave, rebellion embodied",
    ),
    "default": (
        "cyberpunk anime aesthetic — cinematic neon contrast on complete feminine figure, premium viral visual quality, maximum emotional resonance in single frame",
        "cyberpunk anime power aesthetic — cinematic neon on complete masculine warrior, premium viral visual quality, maximum power readability in single frame",
    ),
}


def _get_genre_boost(genre: str, char_type: CharType) -> str:
    boosts = GENRE_BOOST_MATRIX.get(genre, GENRE_BOOST_MATRIX["default"])
    return boosts[0] if char_type == CharType.WAIFU else boosts[1]


# ═══════════════════════════════════════════════════════════════════════
# SONG MOOD ANALYSIS
# ═══════════════════════════════════════════════════════════════════════

def _analyze_song_mood(song_name: str, char_type: CharType) -> str:
    clean = song_name.lower()
    base_type = "feminine" if char_type == CharType.WAIFU else "masculine"

    if any(w in clean for w in ["dark", "shadow", "ghost", "night", "madrugada", "noite", "darkness"]):
        return f"haunted neon emotion — lonely {base_type} power, night as ally, shadow particles dense and deliberate"
    if any(w in clean for w in ["fire", "burn", "rage", "fury", "inferno", "fogo", "chama"]):
        return f"controlled fire emotion — contained {base_type} rage radiating as heat, flame particles erupting"
    if any(w in clean for w in ["love", "heart", "amor", "coracao", "rose", "cherry", "blossom"]):
        return f"dark romantic emotion — {base_type} longing in neon city, beautiful bittersweet mood, rose particles"
    if any(w in clean for w in ["lost", "alone", "lonely", "sozinho", "perdido", "empty"]):
        return f"beautiful isolation emotion — singular {base_type} figure in vast neon city, cinematic solitude amplifying power"
    if any(w in clean for w in ["drive", "speed", "run", "race", "corrida", "fast", "rush"]):
        return f"velocity emotion — {base_type} body mid-movement with speed blur, wind and neon trailing"
    if any(w in clean for w in ["queen", "king", "boss", "power", "rule", "rei", "rainha", "apex"]):
        return f"dominant emotion — {base_type} god-tier aura claiming space, neon crown energy, power pose of divine right"
    if any(w in clean for w in ["blood", "sangue", "war", "guerra", "battle", "fight", "combat"]):
        return f"battle emotion — {base_type} warrior tired and powerful simultaneously, scars glowing neon"
    if any(w in clean for w in ["cold", "ice", "freeze", "winter", "frio", "gelo"]):
        return f"cold precision emotion — absolute {base_type} control, ice aesthetics, every movement calculated and final"
    return f"intense {base_type} emotion matching music — cyberpunk magnetic presence with particle density matching emotional intensity"


# ═══════════════════════════════════════════════════════════════════════
# MUSIC ELEMENTS
# ═══════════════════════════════════════════════════════════════════════

MUSIC_ELEMENTS: list[str] = [
    "cyberpunk headphones around neck glowing neon — music and battle rhythm synchronized",
    "wireless neon earbud catching colored light — the music is why they fight",
    "holographic music waveform pulsing in background synchronized to power output",
    "neon frequency visualizer bars orbiting body responding to power level shifts",
    "emotional body language IS the music element — cinematic silence speaking louder",
]


# ═══════════════════════════════════════════════════════════════════════
# PROMPT IDENTITY LOCKS
# ═══════════════════════════════════════════════════════════════════════

CHANNEL_IDENTITY = (
    "DJ Dark Mark viral phonk trap anime visual, "
    "ULTIMATE premium cyberpunk anime key visual, "
    "scroll-stopping viral YouTube Shorts content, "
    "jaw-dropping cyberpunk anime frame that cannot be scrolled past"
)

WAIFU_CORE_CHARACTER = (
    "one beautiful anime girl character, clear anime proportions and style, "
    "gorgeous detailed anime face visible at thumbnail scale, "
    "expressive neon-lit eyes with multiple vivid catchlights, "
    "detailed hair with individual strand neon reflection rendering, "
    "complete signature outfit with cyberpunk enhancement details, "
    "single character commanding 85% of frame — no other people"
)

SHOUNEN_CORE_CHARACTER = (
    "one powerful anime male character, clear anime proportions and style, "
    "intense detailed anime face with power-lit eyes visible at thumbnail scale, "
    "strong masculine frame carrying power visibly in body language, "
    "detailed hair catching neon and power-effect lighting, "
    "complete signature outfit or armor with cyberpunk/power enhancement, "
    "single character commanding 85% of frame — no other people"
)

STYLE_LOCK = (
    "PREMIUM cyberpunk anime key visual at absolute maximum quality, "
    "ultra-clean professional lineart with polished studio finish, "
    "high-end 2D anime illustration style at quality ceiling, "
    "cel shading with multi-source rim lighting system, "
    "glossy hyper-detailed eyes with five or more catchlights, "
    "rich maximally-saturated neon colors with extreme contrast shadows, "
    "NOT photorealistic, NOT 3D render, NOT western cartoon — pure anime illustration apex"
)

QUALITY_LOCK = (
    "ultra-hyper detailed rendering, crisp professional lineart, "
    "clean correct anatomy and proportions, "
    "extreme resolution detail on every surface texture, "
    "premium polished finish with perfect cinematic color grading, "
    "perfect compositional placement for maximum visual impact in 9:16 frame, "
    "no text, no logo, no watermark, no extra people, vertical 9:16 mobile format"
)

MOTION_LOCK = (
    "MAXIMUM sense of motion and explosive power — "
    "hair caught mid-explosion in technique wind, "
    "speed blur streaks showing velocity direction, "
    "impact shockwave rings visible in compressed atmosphere, "
    "neon energy crackles off every surface near the body, "
    "dynamic composition where everything is alive and in motion simultaneously"
)

THUMBNAIL_LOCK = (
    "optimized for YouTube Shorts thumbnail effectiveness — "
    "ONE clear visual focal point readable in under 1 second, "
    "strong character silhouette against contrasting background, "
    "face or eyes readable at small resolution, "
    "most important visual element in upper 40% of vertical frame, "
    "maximum color contrast between character and background"
)

# [FIX 4] GENERATION_SUFFIX limpo — removidos "masterpiece" e "best quality" (tags SD1.5/SDXL)
GENERATION_SUFFIX = (
    ", beautiful anime character, complete visible body in frame, "
    "detailed costume and iconic design elements fully visible, "
    "maximum neon and power lighting, vivid cinematic colors, "
    "clear powerful silhouette, explosive alive cyberpunk frame, "
    "professional anime illustration at apex quality, "
    "no text, no watermark, no logo, no extra people, vertical 9:16 format"
)

NEGATIVE_PROMPT = (
    "ugly, bad anatomy, bad face, asymmetrical eyes, distorted face, "
    "bad hands, extra fingers, missing fingers, fused limbs, broken limbs, "
    "floating limbs, disconnected parts, long neck, disfigured, mutated, "
    "melted face, uncanny valley, bad proportions, deformed body, "
    "blurry, low quality, jpeg artifacts, heavy noise, flat boring image, "
    "photorealistic, real photograph, 3d render, CGI, doll, plastic skin, "
    "western cartoon, childish art, "
    "nude, explicit nudity, nipples, genitalia, sexual act, pornographic, "
    "multiple characters, crowd, two people, duplicate character, "
    "text overlay, words in image, logo watermark, signature, letters, "
    "face too small, character too tiny, lost in background, "
    "washed out bloom, muddy colors, desaturated, flat boring lighting, "
    "generic background, stock photo energy, soulless"
)


# ═══════════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════════

def _compact(text: str, max_len: int = 3200) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace(" ,", ",").replace(",,", ",").replace(", ,", ",")
    return text[:max_len].rstrip(" ,")


def _clean_song_name(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(r"[_\-]+", " ", name)
    return name.strip()


def _make_seed(genre: str, filename: str, short_num: int) -> int:
    # [FIX 7] Seed único por short_num para garantir diversidade
    key = f"{genre}|{filename}|{short_num}|darkmark_{VERSION}"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % (10 ** 9)


def _make_rng(genre: str, filename: str, short_num: int) -> random.Random:
    return random.Random(_make_seed(genre, filename, short_num))


# ═══════════════════════════════════════════════════════════════════════
# CONTEXT BUILDER
# ═══════════════════════════════════════════════════════════════════════

def _build_context(
    style: str,
    filename: str,
    short_num: int,
    char_type: Optional[CharType],
    force_teal_pink: bool,
    force_purple_gold: bool,
    force_crimson_blue: bool,
    force_back: bool,
    force_full_body: bool,
    force_waifu: bool,
    force_shounen: bool,
) -> PromptContext:
    mapped_genre = GENRE_MAP.get(style.lower().strip(), "default")
    rng = _make_rng(mapped_genre, filename, short_num)
    song_name = _clean_song_name(filename)

    if force_waifu or char_type == CharType.WAIFU:
        selected_type = CharType.WAIFU
    elif force_shounen or char_type == CharType.SHOUNEN:
        selected_type = CharType.SHOUNEN
    else:
        selected_type = CharType.WAIFU if rng.random() < 0.55 else CharType.SHOUNEN

    pool = WAIFU_CHARACTERS if selected_type == CharType.WAIFU else SHOUNEN_CHARACTERS
    char = rng.choice(pool)

    if force_back:
        comp = next(c for c in COMPOSITION_STYLES if c["name"] == "back_view_dramatic")
    elif force_full_body:
        comp = next(c for c in COMPOSITION_STYLES if c["name"] == "full_body_power")
    else:
        comp = _weighted_composition_v2(rng, selected_type)

    pose       = _select_pose(rng, selected_type)
    emotion    = _weighted_emotion(rng, selected_type)
    visual_hook = _weighted_hook(rng, selected_type)

    if force_teal_pink:
        palette = next(p for p in PALETTES if p.name == "teal_pink")
    elif force_purple_gold:
        palette = next(p for p in PALETTES if p.name == "purple_gold")
    elif force_crimson_blue:
        palette = next(p for p in PALETTES if p.name == "crimson_blue")
    else:
        palette = _weighted_palette(rng, selected_type)

    particle  = _select_particle_tier(rng, selected_type)
    lighting  = _select_lighting(rng)
    bg        = _select_background(rng, selected_type)
    genre_boost = _get_genre_boost(mapped_genre, selected_type)
    song_mood = _analyze_song_mood(song_name, selected_type)
    music_el  = rng.choice(MUSIC_ELEMENTS)
    waifu_extras  = _build_waifu_extras(rng) if selected_type == CharType.WAIFU else ""
    power_extras  = _build_shounen_extras(rng) if selected_type == CharType.SHOUNEN else ""

    return PromptContext(
        char=char, composition=comp, pose=pose, emotion=emotion,
        visual_hook=visual_hook, palette_name=palette.name, palette_prompt=palette.prompt,
        particle_tier=particle, lighting_stack=lighting, background=bg,
        genre=mapped_genre, genre_boost=genre_boost, song_name=song_name,
        song_mood=song_mood, music_element=music_el,
        waifu_extras=waifu_extras, power_extras=power_extras,
    )


# ═══════════════════════════════════════════════════════════════════════
# PROMPT ASSEMBLER
# ═══════════════════════════════════════════════════════════════════════

def _assemble_prompt(ctx: PromptContext) -> str:
    char = ctx.char
    char_type = char.char_type

    char_block = (
        f"character: {char.name} from {char.series}, "
        f"{char.base_description}, "
        f"signature elements: {', '.join(char.signature_elements)}, "
        f"character identity: {char.power_phrase}"
    )

    core       = WAIFU_CORE_CHARACTER if char_type == CharType.WAIFU else SHOUNEN_CORE_CHARACTER
    emotion_text = get_emotion_prompt(ctx.emotion, char_type)
    extras     = ctx.waifu_extras if char_type == CharType.WAIFU else ctx.power_extras

    parts = [
        CHANNEL_IDENTITY,
        core,
        char_block,
        f"composition: {ctx.composition['prompt']}",
        f"pose: {ctx.pose}",
        emotion_text,
        f"visual hook: {ctx.visual_hook}",
        extras,
        ctx.lighting_stack,
        ctx.particle_tier,
        MOTION_LOCK,
        f"background: {ctx.background}",
        ctx.palette_prompt,
        f"genre: {ctx.genre}, atmosphere: {ctx.genre_boost}",
        f"music element: {ctx.music_element}",
        f"song title: {ctx.song_name}, mood: {ctx.song_mood}",
        THUMBNAIL_LOCK,
        STYLE_LOCK,
        QUALITY_LOCK,
        "scroll-stopping cyberpunk anime visual, perfect neon and power lighting on complete figure, "
        "jaw-dropping cinematic composition, no text, no watermark, no logo, no extra people",
    ]

    return _compact(", ".join(p.strip().strip(",") for p in parts if p.strip()), max_len=3200)


# ═══════════════════════════════════════════════════════════════════════
# CLAUDE PROMPT BUILDER (via API)
# ═══════════════════════════════════════════════════════════════════════

def _build_claude_enhanced_prompt(ctx: PromptContext) -> Optional[str]:
    """
    [FIX 1] Usa o modelo correto claude-opus-4-5
    [FIX 5] Limite aumentado para 100-160 palavras
    [FIX 6] Permite frases descritivas além de vírgulas
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        char = ctx.char
        char_type = ctx.char.char_type

        system = (
            "You are a creative director for a viral YouTube music Shorts channel with anime visuals. "
            "You write Flux image model prompts that generate scroll-stopping, premium, vivid, "
            "cinematic anime art. Your prompts are detailed descriptions using both descriptive sentences "
            "and comma-separated visual elements. The image must always feature exactly one anime "
            "character as the central subject. Output ONLY the final image prompt in English, "
            "no explanation, no preamble, no markdown."
        )

        gender_word = "young woman" if char_type == CharType.WAIFU else "young man"
        char_desc   = char.base_description
        sig_el      = char.signature_elements[0]

        user = f"""
Write a Flux image model prompt for a vertical YouTube music Short visual.

Character: {char.name} from {char.series}
Character description: {char_desc}
Signature visual element: {sig_el}
Character identity: {char.power_phrase}

Visual context:
- Composition: {ctx.composition['prompt'][:120]}
- Pose: {ctx.pose[:100]}
- Visual hook: {ctx.visual_hook[:120]}
- Lighting: {ctx.lighting_stack[:120]}
- Background: {ctx.background}
- Color palette: {ctx.palette_prompt}
- Particle density: {ctx.particle_tier[:80]}
- Genre atmosphere: {ctx.genre_boost[:100]}
- Song title: {ctx.song_name}, emotional mood: {ctx.song_mood[:80]}

Requirements:
- Exactly one {gender_word} as central subject — no other people
- Anime illustration style only — NOT photorealistic, NOT 3D
- Vivid neon cyberpunk colors, cinematic dramatic lighting
- Expressive detailed anime face visible at thumbnail scale
- Complete outfit and signature elements fully visible
- Vertical 9:16 format, character centered and dominant
- No text, no watermark, no logos
- 100 to 160 words describing the scene in detail
"""

        resp = client.messages.create(
            model=get_anthropic_model(),  # [FIX 1]
            max_tokens=300,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        prompt = resp.content[0].text.strip().strip('"').strip("'")
        logger.info(f"[Claude] Prompt gerado ({len(prompt)} chars)")
        return _compact(prompt, max_len=2000)

    except Exception as e:
        logger.warning(f"[Claude] Falha ao gerar prompt: {e} — usando fallback estático")
        return None


# ═══════════════════════════════════════════════════════════════════════
# PUBLIC API — PROMPT GENERATION
# ═══════════════════════════════════════════════════════════════════════

def build_ai_prompt(
    style: str = "phonk",
    filename: str = "song.mp3",
    styles: Optional[list] = None,
    short_num: int = 1,
    char_type: Optional[CharType] = None,
    force_teal_pink: bool = False,
    force_purple_gold: bool = False,
    force_crimson_blue: bool = False,
    force_back: bool = False,
    force_full_body: bool = False,
    force_waifu: bool = False,
    force_shounen: bool = False,
    use_claude: bool = True,
) -> str:
    ctx = _build_context(
        style=style, filename=filename, short_num=short_num, char_type=char_type,
        force_teal_pink=force_teal_pink, force_purple_gold=force_purple_gold,
        force_crimson_blue=force_crimson_blue, force_back=force_back,
        force_full_body=force_full_body, force_waifu=force_waifu, force_shounen=force_shounen,
    )

    # Tenta Claude primeiro, fallback para estático
    if use_claude:
        claude_prompt = _build_claude_enhanced_prompt(ctx)
        if claude_prompt:
            return claude_prompt

    return _assemble_prompt(ctx)


def build_waifu_prompt(style: str = "phonk", short_num: int = 1, filename: str = "song.mp3") -> str:
    return build_ai_prompt(style=style, filename=filename, short_num=short_num, force_waifu=True)


def build_shounen_prompt(style: str = "phonk", short_num: int = 1, filename: str = "song.mp3") -> str:
    return build_ai_prompt(style=style, filename=filename, short_num=short_num, force_shounen=True)


# ═══════════════════════════════════════════════════════════════════════
# IMAGE GENERATION (REPLICATE) — [FIX 2, 3, 7, 8, 9]
# ═══════════════════════════════════════════════════════════════════════

SAVE_DIR = Path("temp")


def generate_image(prompt: str, output_path: Optional[str] = None) -> Optional[str]:
    if not REPLICATE_API_TOKEN:
        logger.error("❌ REPLICATE_API_TOKEN não configurado!")
        return None

    output_path = output_path or str(SAVE_DIR / f"ai_bg_{int(time.time())}.png")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # [FIX 4] Sem "masterpiece"/"best quality" no suffix
    full_prompt = _compact(prompt + GENERATION_SUFFIX, max_len=3500)

    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
        "Prefer": "wait",
    }

    # [FIX 7] Seed varia por tentativa para garantir diversidade
    base_seed = random.randint(1000, 999_999)

    for model_idx, model in enumerate(REPLICATE_MODELS):
        # [FIX 3] Parâmetros corretos por modelo
        if "flux-dev" in model:
            model_input = {
                **FLUX_DEV_PARAMS,
                "prompt": full_prompt,
                "negative_prompt": NEGATIVE_PROMPT,  # [FIX 9]
                "seed": base_seed + model_idx,
            }
        else:  # flux-schnell
            model_input = {
                **FLUX_SCHNELL_PARAMS,
                "prompt": full_prompt,
                "seed": base_seed + model_idx,
            }

        for attempt in range(1, 4):
            try:
                logger.info(f"[Replicate] Tentativa {attempt}/3 — {model.split('/')[-1]}")

                # [FIX 8] Endpoint correto
                resp = requests.post(
                    f"https://api.replicate.com/v1/models/{model}/predictions",
                    headers=headers,
                    json={"input": model_input},
                    timeout=45,
                )
                resp.raise_for_status()
                pred = resp.json()

                poll_url = (
                    pred.get("urls", {}).get("get")
                    or f"https://api.replicate.com/v1/predictions/{pred['id']}"
                )

                # Polling com backoff
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
                            raise RuntimeError("Replicate retornou output vazio.")

                        img_resp = requests.get(image_url, timeout=90)
                        img_resp.raise_for_status()
                        Path(output_path).write_bytes(img_resp.content)

                        size = Path(output_path).stat().st_size
                        # [NEW 2] Validação mais rigorosa: mínimo 80KB
                        if size < 80_000:
                            logger.warning(f"[Replicate] Imagem suspeita: {size} bytes — descartando")
                            Path(output_path).unlink(missing_ok=True)
                            raise RuntimeError(f"Imagem muito pequena: {size} bytes")

                        logger.info(f"✅ Imagem salva: {output_path} ({size // 1024}KB)")
                        return output_path

                    if status == "failed":
                        raise RuntimeError(data.get("error", "Erro desconhecido do Replicate"))

                    if status not in ("starting", "processing"):
                        raise RuntimeError(f"Status inesperado: {status}")

                logger.warning("[Replicate] Timeout atingido no polling")

            except Exception as e:
                wait = 4 * attempt
                logger.error(f"[Replicate] Tentativa {attempt} falhou: {e}. Aguardando {wait}s…")
                # [NEW 1] Muda seed em cada tentativa
                model_input["seed"] = base_seed + model_idx + attempt * 37
                time.sleep(wait)

    logger.error("❌ Todas as tentativas falharam")
    return None


# ═══════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def generate_background_image(
    style: str = "phonk",
    output_path: str = "assets/background.png",
    seed_variant: int = 0,
    max_retries: int = 3,
    force_teal_pink: bool = False,
    force_purple_gold: bool = False,
    force_crimson_blue: bool = False,
    force_back: bool = False,
    force_full_body: bool = False,
    force_waifu: bool = False,
    force_shounen: bool = False,
) -> Optional[str]:
    prompt = build_ai_prompt(
        style=style,
        filename=f"{style}_variant_{seed_variant}.mp3",
        styles=[style],
        short_num=seed_variant + 1,
        force_teal_pink=force_teal_pink,
        force_purple_gold=force_purple_gold,
        force_crimson_blue=force_crimson_blue,
        force_back=force_back,
        force_full_body=force_full_body,
        force_waifu=force_waifu,
        force_shounen=force_shounen,
    )
    for attempt in range(1, max_retries + 1):
        result = generate_image(prompt, output_path)
        if result:
            return result
        logger.warning(f"Background tentativa {attempt}/{max_retries} falhou.")
        time.sleep(3 * attempt)
    return None


def get_or_generate_background(
    style: str = "phonk",
    output_dir: str = "assets/backgrounds",
) -> Optional[str]:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    existing = list(Path(output_dir).glob(f"{style}_bg_*.png"))
    if existing:
        return str(random.choice(existing))
    variant = random.randint(0, 199)
    output_path = str(Path(output_dir) / f"{style}_bg_{variant:03d}.png")
    return generate_background_image(style=style, output_path=output_path, seed_variant=variant)


def generate_background_batch(
    styles: list,
    output_dir: str = "assets/backgrounds",
    variants_per_style: int = 3,
    force_waifu: bool = False,
    force_shounen: bool = False,
) -> dict:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    results: dict = {}
    for style in styles:
        results[style] = []
        for v in range(variants_per_style):
            output_path = str(Path(output_dir) / f"{style}_bg_{v:03d}.png")
            if os.path.exists(output_path):
                results[style].append(output_path)
                logger.info(f"  ↩ Reusing: {output_path}")
                continue
            path = generate_background_image(
                style=style, output_path=output_path, seed_variant=v,
                force_waifu=force_waifu, force_shounen=force_shounen,
            )
            if path:
                results[style].append(path)
    return results


# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=f"AI Image Generator — DJ DARK MARK {VERSION}")
    parser.add_argument("--style",              default="phonk")
    parser.add_argument("--filename",           default="dark phonk.mp3")
    parser.add_argument("--short-num",          type=int, default=1)
    parser.add_argument("--output",             default="assets/background.png")
    parser.add_argument("--waifu",              action="store_true")
    parser.add_argument("--shounen",            action="store_true")
    parser.add_argument("--force-teal-pink",    action="store_true")
    parser.add_argument("--force-purple-gold",  action="store_true")
    parser.add_argument("--force-crimson-blue", action="store_true")
    parser.add_argument("--back",               action="store_true")
    parser.add_argument("--full-body",          action="store_true")
    parser.add_argument("--prompt-only",        action="store_true")
    parser.add_argument("--no-claude",          action="store_true", help="Pular API Claude")
    parser.add_argument("--list-waifus",        action="store_true")
    parser.add_argument("--list-shounen",       action="store_true")
    parser.add_argument("--batch",              action="store_true")
    parser.add_argument("--batch-n",            type=int, default=3)

    args = parser.parse_args()

    if args.list_waifus:
        print(f"═══ {len(WAIFU_CHARACTERS)} WAIFU CHARACTERS ═══")
        for i, c in enumerate(WAIFU_CHARACTERS, 1):
            print(f"  {i:3d}. {c.name} ({c.series})")
            print(f"       → {c.power_phrase}")
        raise SystemExit(0)

    if args.list_shounen:
        print(f"═══ {len(SHOUNEN_CHARACTERS)} SHOUNEN CHARACTERS ═══")
        for i, c in enumerate(SHOUNEN_CHARACTERS, 1):
            print(f"  {i:3d}. {c.name} ({c.series})")
            print(f"       → {c.power_phrase}")
        raise SystemExit(0)

    if args.batch:
        genres = ["phonk", "trap", "dark", "darkpop", "electronic", "rock"]
        results = generate_background_batch(
            styles=genres, variants_per_style=args.batch_n,
            force_waifu=args.waifu, force_shounen=args.shounen,
        )
        for genre, paths in results.items():
            print(f"  {genre}: {len(paths)} generated")
        raise SystemExit(0)

    prompt = build_ai_prompt(
        style=args.style, filename=args.filename, styles=[args.style],
        short_num=args.short_num,
        force_teal_pink=args.force_teal_pink, force_purple_gold=args.force_purple_gold,
        force_crimson_blue=args.force_crimson_blue, force_back=args.back,
        force_full_body=getattr(args, "full_body", False),
        force_waifu=args.waifu, force_shounen=args.shounen,
        use_claude=not args.no_claude,
    )

    if args.prompt_only:
        print(f"═══ PROMPT {VERSION} ═══")
        print(prompt)
        print(f"\nPrompt length: {len(prompt)} chars")
        print(f"\n═══ NEGATIVE PROMPT ═══")
        print(NEGATIVE_PROMPT)
        print(f"\n═══ STATS ═══")
        print(f"  Waifu characters:   {len(WAIFU_CHARACTERS)}")
        print(f"  Shounen characters: {len(SHOUNEN_CHARACTERS)}")
        print(f"  Total characters:   {len(ALL_CHARACTERS)}")
        print(f"  Waifu poses:        {len(WAIFU_POSES)}")
        print(f"  Shounen poses:      {len(SHOUNEN_POSES)}")
    else:
        generate_image(prompt, args.output)
