"""
ai_image_generator.py — DJ DARK MARK v50.0 ██ APEX EDITION ██
══════════════════════════════════════════════════════════════════
FULL REBUILD — MODULAR ARCHITECTURE — DUAL-ENGINE SYSTEM

  ┌─────────────────────────────────────────────────────────┐
  │  ENGINE A → WAIFU GENERATOR    (viral beauty / appeal)  │
  │  ENGINE B → SHOUNEN GENERATOR  (power / legendary)      │
  └─────────────────────────────────────────────────────────┘

Systems rebuilt from scratch:
  ▸ Emotion System       — 12 emotion archetypes per engine
  ▸ Visual Hook System   — single dominant scroll-stopper per image
  ▸ Pose System v2       — 30 waifu + 30 shounen poses
  ▸ Palette Engine v2    — mood-matched palettes + contrast locks
  ▸ Particle System v2   — density tiers (medium/heavy/catastrophic)
  ▸ Composition Engine   — 9:16 mobile-first lock
  ▸ Lighting Stack v2    — 5-layer cinematic neon system
  ▸ Anti-repetition RNG  — weighted deduplication per session
  ▸ Genre × Mood Matrix  — fine-grained prompt tuning per genre
  ▸ Viral CTR Hooks      — thumbnail-first design logic

Target: 10M+ view level cyberpunk anime visuals for music content
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

logger = logging.getLogger("ai_image_generator_v50")
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
    "cjwbw/animagine-xl-3.1",
]

FLUX_PARAMS: dict = {
    "width": 768,
    "height": 1024,
    "num_inference_steps": 50,
    "guidance_scale": 10.0,
    "num_outputs": 1,
    "output_format": "png",
    "output_quality": 100,
    "disable_safety_checker": True,
}

VERSION = "v50.0-APEX"


# ═══════════════════════════════════════════════════════════════════════
# ENUMS — CHARACTER TYPE / ENGINE SELECT
# ═══════════════════════════════════════════════════════════════════════

class CharType(Enum):
    WAIFU   = auto()
    SHOUNEN = auto()


class EmotionArchetype(Enum):
    # WAIFU archetypes
    COLD_QUEEN     = "cold_queen"
    YANDERE_SMILE  = "yandere_smile"
    SEDUCTIVE_GAZE = "seductive_gaze"
    DOMINANT_VIBE  = "dominant_vibe"
    PLAYFUL_DANGER = "playful_danger"
    ETHEREAL_SORROW= "ethereal_sorrow"
    BATTLE_FURY    = "battle_fury"
    SOFT_OBSESSION = "soft_obsession"
    # SHOUNEN archetypes
    COLD_RAGE      = "cold_rage"
    I_AM_HIM       = "i_am_him"
    FINAL_FORM      = "final_form"
    SILENT_APEX    = "silent_apex"


# ═══════════════════════════════════════════════════════════════════════
# DATACLASSES
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class CharacterEntry:
    name: str
    series: str
    char_type: CharType
    base_description: str
    signature_elements: list[str]   # iconic design markers
    power_phrase: str               # short identity tag


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
    waifu_extras: str               # tattoos / piercings / fashion (waifu only)
    power_extras: str               # aura / battle damage (shounen only)


# ═══════════════════════════════════════════════════════════════════════
# ══════════════ CHARACTER LIBRARY — ENGINE A: WAIFUS ══════════════════
# 100 entries, full cyberpunk appeal, high-viral design
# ═══════════════════════════════════════════════════════════════════════

WAIFU_CHARACTERS: list[CharacterEntry] = [

    # ─── DEMON SLAYER ───────────────────────────────────────────────
    CharacterEntry("Mitsuri Kanroji", "Demon Slayer", CharType.WAIFU,
        "long pink-to-green ombre hair loose and cascading past hips, uniquely colored gradient locks with warm flush cheeks",
        ["cherry blossom Love Breathing ribbon-sword crackling soft pink energy", "flexible kunoichi body in mid-impossible-angle attack",
         "modified revealing pink Hashira uniform clinging to athletic curves", "warm loving smile that hides lethal speed"],
        "Love Pillar — the most flexible blade in existence"),

    CharacterEntry("Daki", "Demon Slayer", CharType.WAIFU,
        "very long silver-white hair with teal gradient tips, sharp jaw, tall lean elegant frame with neon vein demon markings across skin",
        ["obi sash demon weapon extending as crystalline blade fans glowing blood-crimson", "revealing elegant courtesan kimono made of living flesh-cloth neon patterns",
         "contemptuous half-lidded eyes with slit demon pupils glowing red", "demon absorption marks crawling glowing up arms and neck"],
        "Upper Moon Six — beauty that cuts everything it touches"),

    CharacterEntry("Shinobu Kocho", "Demon Slayer", CharType.WAIFU,
        "long hair flowing from yellow-to-lavender, butterfly haori with wings glowing as holographic neon constructs",
        ["needle-thin insect-venom sword crackling purple toxin energy at tip", "tiny vials and doctor bag radiating pale green medical neon",
         "soft closed-eye smile hiding total ruthlessness", "butterfly wing light constructs extending six feet wide behind shoulders"],
        "Insect Pillar — the smile that ends you before the pain registers"),

    CharacterEntry("Nezuko Kamado", "Demon Slayer", CharType.WAIFU,
        "long black hair with neon pink ombre tips, bamboo muzzle replaced by glowing pink filter mask, demon form with cracked pink neon skin fissures",
        ["Exploding Blood technique making crimson neon erupt in petal-shaped blasts", "pink haori with hemp-leaf pattern illuminated from within",
         "half-demon transformation with one eye slit and glowing hot pink", "small frame containing disproportionate compressed demon power"],
        "Demon who chose humanity — pink fire that protects"),

    # ─── CHAINSAW MAN ───────────────────────────────────────────────
    CharacterEntry("Makima", "Chainsaw Man", CharType.WAIFU,
        "neat auburn hair in low braid, white dress shirt and tie, rings of concentric glowing eyes floating behind her like divine halos",
        ["Control Devil leash chain glowing gold wrapping around reality", "perfect eerie calm expression of total dominance",
         "concentric eye rings orbiting her head like surveillance satellites", "presence bending the world visibly toward her"],
        "Control Devil — everything and everyone was always hers"),

    CharacterEntry("Power", "Chainsaw Man", CharType.WAIFU,
        "wild blonde hair with iconic neon pink curved devil horns, casual streetwear soaked in red energy",
        ["enormous chainsaw arm deployed and revving crackling neon blood-red", "feral gap-toothed grin showing canines and absolute chaos",
         "blood manipulation forming crimson armor plates across body", "horn neon casting hard pink rim light across face"],
        "Blood Devil — pure chaos in a cute package"),

    CharacterEntry("Himeno", "Chainsaw Man", CharType.WAIFU,
        "short white hair, eyepatch replaced by sleek glowing green neon device scanning everything",
        ["Ghost Devil translucent hand jutting from beside her with razor grip", "casual cyberpunk devil hunter jacket half-open",
         "cigarette between lips with green ghost-neon smoke trail", "effortless dangerous confidence radiating from entire posture"],
        "Ghost contract hunter — the coolest one in the room"),

    CharacterEntry("Quanxi", "Chainsaw Man", CharType.WAIFU,
        "long blonde hair in high ponytail, athletic lean build, crossbow arrow tips visible over shoulders",
        ["First Devil Hunter with four arrow fiends orbiting as personal bodyguard halos", "cool emotionless mercenary expression behind tinted cyber-visor",
         "multiple arrows nocked simultaneously with glowing bolt-heads", "techwear bodysuit with arrow-quiver neon integrated"],
        "First Devil Hunter — precision death"),

    # ─── JUJUTSU KAISEN ─────────────────────────────────────────────
    CharacterEntry("Nobara Kugisaki", "Jujutsu Kaisen", CharType.WAIFU,
        "orange-brown bob hair with blunt cut, fierce no-nonsense expression that takes nothing from anyone",
        ["straw doll and nails crackling black cursed energy resonance technique", "hammer raised mid-Black-Flash strike with dark lightning on fist",
         "cursed tool blood splatter forming abstract neon patterns on uniform", "Resonance technique activating glowing skull over distant target"],
        "Hammer and nails — ugly but effective"),

    CharacterEntry("Maki Zenin", "Jujutsu Kaisen", CharType.WAIFU,
        "short dark hair with medical tape on nose, glasses with neon green special grade vision sight",
        ["naginata or panda staff as massive cursed tool extended full length", "zero cursed energy making her invisible to curse detection — ghost fighter",
         "physical dominance frame where muscles catch neon under ripped uniform", "Zenin clan cursed tool arsenal orbiting at ready"],
        "Zero cursed energy — pure physical apex"),

    CharacterEntry("Mei Mei", "Jujutsu Kaisen", CharType.WAIFU,
        "long blonde twin braids, cool mercenary professionalism in every gesture",
        ["twin ravens with glowing neon eyes orbiting as bird strike satellites", "calculating money-motivated expression over battle chaos",
         "Bird Strike technique bird dissolving into high-velocity impact neon", "black suit with cyberpunk armor plates integrated at joints"],
        "Every action has a price — and she charges double"),

    CharacterEntry("Yuki Tsukumo", "Jujutsu Kaisen", CharType.WAIFU,
        "long blonde hair with casual wild styling, special grade sorcerer ease in every move",
        ["Star Rage technique Virtual Mass enhancing physical strikes to astronomical scale", "casual combat stance hiding special grade destruction potential",
         "Mass attribute making fists carry planetary impact weight", "relaxed smile while outputting power that cracks the earth"],
        "Special Grade — stars in her fists"),

    # ─── FRIEREN ────────────────────────────────────────────────────
    CharacterEntry("Frieren", "Frieren: Beyond Journey's End", CharType.WAIFU,
        "long silver elf hair with decorative ribbon ties at intervals, ancient eyes holding a thousand years of grief",
        ["Zoltraak offensive magic now casual finger-flick after thousand years of mastery", "magic field analysis sight activating as faint mana-reading glow over everything",
         "cherry blossoms mixing with mana particles because she stopped to pick flowers mid-journey", "staff trailing afterimage of every spell she has ever cast"],
        "A thousand years of magic — still stopping for flowers"),

    CharacterEntry("Fern", "Frieren: Beyond Journey's End", CharType.WAIFU,
        "long dark hair in neat twin braids, diligent prodigy mage with efficient zero-waste mana output",
        ["Zoltraak rapid-fire multi-volley exceeding any mage her generation", "concentrated blue-white magic blast charges erupting from both hands",
         "serious face with small unconscious excitement for magical trinkets", "mana control so precise her spells leave no splash"],
        "The most efficient mage born in a century"),

    CharacterEntry("Stark", "Frieren: Beyond Journey's End", CharType.WAIFU,
        "messy red-orange hair, powerful warrior build with arms that could end battles",
        ["Warrior's instinct technique charging explosive physical strike with hero-level output", "embarrassed expression contradicting the city-leveling power output",
         "Aura disruption shockwave making air visible in rings outward", "scared but doing it anyway — the most honest kind of courage"],
        "Afraid of everything — strongest warrior alive"),

    # ─── REZERO ─────────────────────────────────────────────────────
    CharacterEntry("Rem", "Re:Zero", CharType.WAIFU,
        "iconic short blue hair with hair clip, maid uniform reimagined as armored cyberpunk bodyguard suit",
        ["morning star flail crackling dense blue electricity on impact sphere", "Oni horn emerging glowing blue releasing demon power",
         "tear-streaked fierce face of absolute devotion and destruction", "Oni magic aura billowing blue smoke off raised horn"],
        "Demon maid — devotion and destruction are the same thing"),

    CharacterEntry("Emilia", "Re:Zero", CharType.WAIFU,
        "long silver hair half-tied with white flower ornaments, pointed elf ears, serene face hiding tremendous ice power",
        ["ice shards floating around hands forming shield and blade constructs", "cyberpunk ice sorceress coat with crystalline blue circuit patterns",
         "cold breath visible as silver mist in neon air", "elemental spirits orbiting as small glowing sprites"],
        "Half-elf ice maiden — gentleness that freezes worlds"),

    CharacterEntry("Beatrice", "Re:Zero", CharType.WAIFU,
        "very long twin drill blonde twintails, ancient spirit housed in small loli frame",
        ["spirit arts magic barrier circle blazing gold hovering under feet", "library of Roswaal dimensional barrier crackling around her",
         "irritated expression hiding fierce loyalty and centuries of loneliness", "I suppose energy while outputting overwhelming spirit power"],
        "Ancient spirit — four hundred years waiting for one person"),

    CharacterEntry("Ram", "Re:Zero", CharType.WAIFU,
        "short pink hair with single demon horn glowing hot pink, elite maid precision in every movement",
        ["Clairvoyance neon eye scan activating golden ring around single horn", "condescending sharp beauty staring down from absolute competence",
         "maid uniform with cyberpunk combat apron detailing neon trim", "Barusu energy masking S-rank assassin threat level"],
        "Single horn — still the strongest maid alive"),

    CharacterEntry("Echidna", "Re:Zero", CharType.WAIFU,
        "long white hair with black roots fading up, gothic witch of greed tea party dress as dark cosmic armor",
        ["tea cup floating with bone-white otherworldly glow", "eerily beautiful perfect smile hiding absolute evil calculation",
         "void portal consuming background reality behind her", "knowledge greed visible as constellation data streams orbiting"],
        "Witch of Greed — she already knows how you die"),

    CharacterEntry("Satella", "Re:Zero", CharType.WAIFU,
        "silver hair half-radiant half-consumed by encroaching shadow, violet eyes crying genuine love",
        ["Witch of Envy shadow hands reaching from dress hem like living darkness", "tragic goddess beauty consuming herself for one love",
         "love and destruction made physically indistinguishable", "shadow tentacles and violet light fighting for the same body"],
        "Witch of Envy — loved so much she destroyed the world"),

    # ─── OVERLORD ───────────────────────────────────────────────────
    CharacterEntry("Albedo", "Overlord", CharType.WAIFU,
        "floor-length black wavy hair, white angelic dress meeting black demon wings in striking contrast",
        ["Hermes Trismegistus giant shield deployed as glowing wing-barrier", "obsessive adoring expression turning lethal when Nazarick is threatened",
         "halo above and black wings simultaneously — angel and demon unified", "Levia Halcyon great axe erupting Armageddon charge"],
        "Floor Guardian — love and loyalty indistinguishable from fanaticism"),

    CharacterEntry("Shalltear Bloodfallen", "Overlord", CharType.WAIFU,
        "long silver drill hair, true vampire form with full-spread crimson wings, gothic battle dress",
        ["Blood Frenzy power increasing with each wound received — reverse damage", "Spuit Lance crackling dark crimson neon at full charge",
         "pale white skin with neon red eyes locking onto viewer with possessive hunger", "blood drops floating weightless in power field around her"],
        "True Vampire Floor Guardian — the more you hurt her the worse it gets"),

    CharacterEntry("Shizu", "Overlord", CharType.WAIFU,
        "blonde hair and dark automaton frame, quiet disciplined android warrior",
        ["fire and wind combined techniques creating plasma lance from twin elements", "emotionless android face with single human warmth in eyes",
         "mechanical precision in every stance making combat look effortless", "Element system activating with both hands deployed simultaneously"],
        "Automaton warrior — the most elegant killer in Nazarick"),

    # ─── FATE ───────────────────────────────────────────────────────
    CharacterEntry("Artoria Pendragon (Saber)", "Fate Series", CharType.WAIFU,
        "iconic golden hair in tight braid, emerald green eyes, blue and gold plate armor",
        ["Excalibur divine wind energy charging as golden beam toward sky", "noble resolute expression of a king who carried the world's weight",
         "sword raised with divine golden wind tearing everything near it apart", "Avalon barrier fragments floating as golden petals"],
        "King of Knights — Excalibur tears the sky"),

    CharacterEntry("Rin Tohsaka", "Fate Series", CharType.WAIFU,
        "twin black pigtails with red ribbon bows glowing, black turtleneck and red skirt as combat mage outfit",
        ["twin glowing jewel gems charged with massive compressed mana detonating", "tsundere fierce determination face mid-gem-throw", 
         "archer class summoning circle glowing under feet", "mana burst visible as red energy waves off fingertips"],
        "Top student mage — she'll never admit she's scared"),

    CharacterEntry("Jeanne d'Arc", "Fate Series", CharType.WAIFU,
        "very long silver-white hair streaming behind, divine holy armor with gold circuit neon",
        ["sacred flame banner crackling brilliant white-gold divine energy", "serene face of absolute faith even in catastrophe",
         "holy neon shield barrier dome expanding outward", "divine light splitting dramatic shadow across frame"],
        "Ruler — God's standard never wavered"),

    CharacterEntry("Jeanne d'Arc Alter", "Fate Series", CharType.WAIFU,
        "long silver-white hair with dark roots, black inverse holy armor dripping crimson",
        ["La Grondement Du Haine black flame lance consuming everything it touches", "cold vengeful expression of divine justice turned into righteous wrath",
         "black flag crackling inverse holy energy destroying purity", "dark holy fire making the air around her black and gold"],
        "Avenger — God abandoned her first"),

    CharacterEntry("Tamamo-no-Mae", "Fate Series", CharType.WAIFU,
        "long flowing golden hair, iconic fox ears and nine tails glowing",
        ["divine solar flame technique channeling sun goddess power through fox tails", "seductive kitsune smile hiding catastrophic divine power",
         "nine golden fox tails extending as massive energy wings", "Amaterasu connection making eyes glow solar gold"],
        "Divine fox goddess — sun in her tails"),

    # ─── SWORD ART ONLINE ───────────────────────────────────────────
    CharacterEntry("Asuna Yuuki", "Sword Art Online", CharType.WAIFU,
        "chestnut waist-length hair, white-and-red KoB armor redesigned as cyberpunk plate with glowing orange circuitry",
        ["rapier sheathed and radiating electric blue speed energy", "Starburst Stream 16-hit combo leaving light trail clone aftermath",
         "lightning goddess of rapid strike pose frozen at maximum velocity", "graceful frame hiding the fastest sword in Aincrad"],
        "Flash — 16 hits before you see the first"),

    CharacterEntry("Sinon", "Sword Art Online", CharType.WAIFU,
        "short teal-blue hair, sniper's cold precision in every posture",
        ["Hecate II sniper rifle glowing blue scope charge for Meteor Shot", "cold blue eyes calculating trajectory through impossible terrain",
         "kneeling sniper form with wind-blown hair in perfect composition", "bullet trajectory neon visible as golden arc through air"],
        "GGO's best sniper — one shot, anywhere"),

    CharacterEntry("Alice Zuberg", "Sword Art Online", CharType.WAIFU,
        "very long golden blonde hair, Integrity Knight armor of brilliant gold",
        ["Fragrant Olive Sword releasing golden flower-petal blade storm", "flawless perfectionist knight expression of absolute golden authority",
         "Perfect Control Art flowering sword releasing thousand golden petals", "blue sky above cracking from divine sword energy output"],
        "Integrity Knight — perfection made human"),

    # ─── NARUTO ─────────────────────────────────────────────────────
    CharacterEntry("Tsunade", "Naruto", CharType.WAIFU,
        "long blonde hair in iconic twin pigtails, diamond Yin Seal on forehead",
        ["seal releasing in wave of overwhelming chakra making ground shatter pre-impact", "fist raised with Strength of a Hundred cracking the earth ten feet early",
         "legendary beauty and strength radiating simultaneously", "Sannin-level presence making enemies reconsider their life choices"],
        "Legendary Sannin — the strongest fist in the world"),

    CharacterEntry("Temari", "Naruto", CharType.WAIFU,
        "four spiky blonde ponytails, wind kunoichi identity in every line",
        ["enormous iron fan fully extended crackling teal wind neon on all three moons", "Cyclone Scythe technique creating visible pressure wave obliterating frame edge",
         "powerful wide stance of someone who controls the battlefield from distance", "wind displacement visible as atmospheric distortion behind fan"],
        "Wind kunoichi — she doesn't aim at you, she aims at the air around you"),

    CharacterEntry("Konan", "Naruto", CharType.WAIFU,
        "short blue hair, paper-white robe, paper butterfly constantly orbiting",
        ["paper angel wings extending dozens of feet made of billions of explosive paper sheets", "6 billion explosive tags deployment visible as white paper flood",
         "calm terrifying goddess expression of someone who planned this for years", "paper world technique consuming entire background in white sheets"],
        "Paper god — she doesn't fight, she rearranges reality"),

    CharacterEntry("Kushina Uzumaki", "Naruto", CharType.WAIFU,
        "extremely long red hair floating and whipping as living weapon, red chain sealing marks visible",
        ["Adamantine Sealing Chains deploying as massive golden restraint lattice", "Red Hot-Blooded Habanero fury expression about to destroy someone",
         "Nine-Tails chakra chains crackling red-gold sealing anyone who approaches", "Uzumaki life force aura making her glow red-gold"],
        "Red Hot-Blooded Habanero — her hair alone is a weapon"),

    # ─── BLEACH ─────────────────────────────────────────────────────
    CharacterEntry("Yoruichi Shihouin", "Bleach", CharType.WAIFU,
        "dark skin, short purple hair, goddess of flash identity",
        ["Shunko lightning-enhanced physical strike technique making air explode", "golden speed neon afterimages filling frame as dozens of ghost-poses",
         "playful grin showing she still barely tried after devastating attack", "Flash God hakuda technique cracking stone floor under each landing"],
        "Flash Goddess — fastest thing in Soul Society"),

    CharacterEntry("Rukia Kuchiki", "Bleach", CharType.WAIFU,
        "short black hair, shinigami uniform with noble white scarf of house Kuchiki",
        ["Sode no Shirayuki ice zanpakuto white rose petal ice storm erupting", "Some no mai Tsukishiro white circle of absolute zero frost",
         "noble Kuchiki bearing combining with small fierce frame beautifully", "Bankai Hakka no Togame ice mist consuming everything in sight"],
        "Ice dancer — the most beautiful absolute zero"),

    CharacterEntry("Rangiku Matsumoto", "Bleach", CharType.WAIFU,
        "wavy long strawberry-blonde hair cascading, vice-captain badge catching neon light",
        ["Haineko zanpakuto dissolving into ash-blade swarm filling entire frame", "lazy confident smile masking enormous spiritual pressure",
         "ash cloud forming shapes and slashing simultaneously as body art and weapon", "feminine and lethal in exactly equal measure"],
        "Haineko — ash that cuts"),

    CharacterEntry("Nelliel Tu Odelschwanck", "Bleach", CharType.WAIFU,
        "green hair with helmet cracked revealing horn, adult form with powerful athletic figure",
        ["Lanzador Verde lance crackling green cero energy launched at relativistic speed", "Cero Doble absorbing and returning opponent's blast doubled",
         "gentle warrior expression showing espada power quietly reawakening", "fraccion loyalty as orbiting silhouettes behind her"],
        "Espada 3 — the gentle one is always the most dangerous"),

    CharacterEntry("Halibel", "Bleach", CharType.WAIFU,
        "long blonde hair, hollow jaw collar mask fragment, Tres Bestias commander bearing",
        ["Tiburón released form water shark technique Cascada waterfall power", "Espada 3 Queen of Hueco Mundo presence bending light and water",
         "stoic beautiful expression of absolute command", "water manipulation making ocean appear in dry air"],
        "Queen of Hueco Mundo — sea brought to solid ground"),

    # ─── ONE PIECE ──────────────────────────────────────────────────
    CharacterEntry("Boa Hancock", "One Piece", CharType.WAIFU,
        "floor-length black hair with iconic Kuja crown, empress bearing that bends the world",
        ["Love-Love Mero Mero Mellow hand pose petrifying everything beautiful in range", "Slave Arrow technique shooting love beam array",
         "breathtaking arrogant beauty that literally stops battles by existing", "snakes Salome coiling around legs glowing sacred"],
        "Pirate Empress — the most beautiful woman alive, and she knows it"),

    CharacterEntry("Nami", "One Piece", CharType.WAIFU,
        "shoulder-length orange hair, navigator identity in every confident gesture",
        ["Clima-Tact upgraded as cyberpunk weather staff releasing lightning orb Thunderbolt Tempo", "Zeus cloud companion crackling massive storm power",
         "weather map holographic open showing real-time storm formation control", "confident navigator hand on hip claiming the sea belongs to her"],
        "Weather Witch — she owns every storm"),

    CharacterEntry("Nico Robin", "One Piece", CharType.WAIFU,
        "long straight black hair, cyberpunk archaeologist in dark trench coat",
        ["Mil Fleur Gigantesco Mano hundred stone hands emerging from any surface simultaneously", "Demonio Fleur demon giant form rising behind her",
         "mysterious half-smile of someone who has survived the unsurvivable", "Ohara holographic ruins glowing blue behind her in memory"],
        "Devil Child — she survived an island of murder and became stronger"),

    CharacterEntry("Yamato", "One Piece", CharType.WAIFU,
        "long white hair with oni horns glowing icy blue, powerful athletic frame",
        ["Divine Departure Kozuki Oden technique massive Haki-coated sword swing", "Hybrid Mythical Zoan white wolf god form partially released",
         "Conqueror's Haki crackling black lightning off weapon", "Oden's log pose glowing as sacred relic held in powerful grip"],
        "Oni Princess — carrying Oden's will forward"),

    # ─── DATE A LIVE ────────────────────────────────────────────────
    CharacterEntry("Kurumi Tokisaki", "Date A Live", CharType.WAIFU,
        "iconic half black half white long hair, one golden clockwork eye and one crimson eye",
        ["twin flintlocks dripping shadow particles and time-decay neon", "Clock Bullet Zafkiel technique deploying time-rewind spatial bullet",
         "gothic lolita dress redesigned as cyberpunk time spirit armor with clock gear motifs", "time shadows of past-selves orbiting her as ghost afterimages"],
        "Spirit of Time — she's already seen how this ends"),

    CharacterEntry("Tohka Yatogami", "Date A Live", CharType.WAIFU,
        "long dark purple hair, Spirit dress flowing and armored simultaneously",
        ["Sandalphon throne-sword crackling purple lightning at maximum revealed power", "Inverse Form consuming light around her into violet void",
         "innocent expression existing in terrible contrast to godlike destruction output", "Spirit mana wings expanding forty feet behind her frame"],
        "First Spirit — enough power to crack the world"),

    # ─── BLACK CLOVER ───────────────────────────────────────────────
    CharacterEntry("Noelle Silva", "Black Clover", CharType.WAIFU,
        "silver-white hair with blue tint, proud noble bearing softened by genuine growth",
        ["Valkyrie Armor water manifestation as divine aqua knight form", "Saint Stage water dragon rising behind armored figure",
         "noble clumsy determination transformed into absolute real power", "water controlled with precision that took years of pure will to achieve"],
        "Royal Knight — the water that protects everything"),

    CharacterEntry("Mimosa Vermillion", "Black Clover", CharType.WAIFU,
        "very long orange hair in elaborate updo, elegant noble healer bearing",
        ["Ultimate Magic Plant Flower healing field consuming entire battlefield in gold flowers", "Healing flowers orbiting as medical neon aura",
         "gentle kind expression carrying house Vermillion nobility effortlessly", "offensive plant technique summoning thorn titan behind healer form"],
        "Noble healer — the flowers that end wars"),

    # ─── QUINTESSENTIAL QUINTUPLETS ─────────────────────────────────
    CharacterEntry("Nino Nakano", "Quintessential Quintuplets", CharType.WAIFU,
        "long blonde twin pigtails fierce and bouncy, most intense protective sister energy",
        ["kitchen knife crackling rose neon as absurd improvised weapon in serious chef hands", "fierce protective rage expression at whoever threatens her sisters",
         "tsundere wall breaking visibly in single frame as love conquers pride", "chef determination making cooking look like battle art"],
        "Second Quint — the one who fights the hardest for what she loves"),

    CharacterEntry("Miku Nakano", "Quintessential Quintuplets", CharType.WAIFU,
        "long blonde hair with iconic deep blue headphones glowing neon blue",
        ["sound wave indigo neon emanating from headphone cup she presses to ear", "withdrawn intensity of someone who feels everything at maximum volume",
         "headphone glow casting blue rim light across shy beautiful face", "music data stream visible as indigo flowing notation in air around her"],
        "Third Quint — the quiet one loves loudest"),

    CharacterEntry("Ichika Nakano", "Quintessential Quintuplets", CharType.WAIFU,
        "long blonde hair with five-star hairpin glowing gold, actress composure at all times",
        ["big sister calm holding everything together at center of five-sister storm", "actress mask slipping briefly to reveal genuine emotion underneath",
         "warm responsible expression of someone who gives everything and asks for nothing", "star hairpin projecting small but real light in darkness"],
        "First Quint — the actress who forgot to act around him"),

    # ─── MY HERO ACADEMIA ───────────────────────────────────────────
    CharacterEntry("Momo Yaoyorozu", "My Hero Academia", CharType.WAIFU,
        "long black hair in iconic high ponytail, creation quirk requiring skin exposure to work",
        ["creation quirk manifesting white molten material from skin forming massive cannon", "intelligent tactical expression reading battlefield at genius level",
         "elegant hero costume practical for creation quirk exposure needs", "multiple created weapons orbiting simultaneously in tactical array"],
        "Creation Hero — she literally builds victory on the spot"),

    CharacterEntry("Mirko", "My Hero Academia", CharType.WAIFU,
        "white hair and rabbit ears, powerful athletic body with scars telling stories",
        ["Luna Ring Kick technique unleashing massive pressure wave at lunar force scale", "scars on arm visible and worn with zero apology",
         "fierce grin showing teeth of someone who only gets stronger from damage", "rabbit speed afterimages filling frame from sheer velocity"],
        "Rabbit Hero — five highest-ranked hero, no team, no backup"),

    CharacterEntry("Himiko Toga", "My Hero Academia", CharType.WAIFU,
        "twin blonde bun with loose strands, blood-drain gauntlets neon yellow",
        ["Transform quirk cycling through faces with golden eyes shifting identities", "unhinged joyful dangerous smile at target of obsession",
         "knife held lovingly like it's the kindest thing she owns", "yandere beauty baseline expression — she always looks like this"],
        "Transform quirk — love is just wanting to become someone"),

    CharacterEntry("Midnight", "My Hero Academia", CharType.WAIFU,
        "long black and white hair wild, mature heroine confidence in every pose",
        ["Somnambulist sleep quirk neon purple somnambulant mist pouring from wrists in curtains", "whip raised in confident mature heroine battle pose",
         "teaching and battle merged in single commanding stance", "purple mist swallowing background as she advances"],
        "Rated R Hero — put everyone to sleep before the fight starts"),

    # ─── KONOSUBA ───────────────────────────────────────────────────
    CharacterEntry("Megumin", "KonoSuba", CharType.WAIFU,
        "short black hair under enormous oversized wizard hat with neon star ornament, red eyes glowing",
        ["EXPLOSION single ultimate spell charging black void energy toward sky", "staff raised in full dramatic explosion chant pose",
         "dark energy erupting beneath tiny dramatic frame as massive shockwave", "one eye closed in concentration as reality prepares to suffer"],
        "Explosion mage — one spell, everything gone"),

    CharacterEntry("Darkness", "KonoSuba", CharType.WAIFU,
        "long wavy blonde hair, crusader plate armor with neon blue rune engravings",
        ["broadsword dragged dramatically creating ground furrow while she advances undaunted", "flushing noble expression hiding the extremely specific secret she has",
         "tall powerful frame built for tanking absolutely everything", "armor cracked from absorbing massive attacks with zero flinching"],
        "Crusader tank — she can't hit anything and doesn't need to"),

    # ─── MISC HIGH-APPEAL ───────────────────────────────────────────
    CharacterEntry("Violet Evergarden", "Violet Evergarden", CharType.WAIFU,
        "long golden blonde hair, auto memory doll uniform with prosthetic silver arms at joints",
        ["typewriter keys floating around her as magical memory objects glowing soft", "letter neon paper dissolving into butterfly flutter upward",
         "deep lonely beautiful eyes learning what emotion means one letter at a time", "prosthetic arms glowing blue at joints reaching toward warmth"],
        "Auto Memory Doll — learning to feel through every letter"),

    CharacterEntry("Yor Forger", "Spy × Family", CharType.WAIFU,
        "black hair with rose hairpin glowing blood-red, thorn-covered crimson dress as cyberpunk armor",
        ["twin needles crackling with red neon Thorn Princess energy extending", "gentle smile hiding the terrifying speed and accuracy underneath",
         "rose thorns extending from dress fabric as actual blades", "assassin training making casual poses accidentally threatening"],
        "Thorn Princess — deadliest hands, warmest heart"),

    CharacterEntry("Kaguya Shinomiya", "Kaguya-sama: Love is War", CharType.WAIFU,
        "impossibly long black hair with ornate kanzashi pins glowing red neon, noble strategist bearing",
        ["holographic data fan open showing strategic analysis of opponent emotional state", "sharp manipulative intelligence visible in every movement",
         "cyberpunk noble in dark kimono with gold circuit obi deployed", "battle-mind palace visualization showing twenty steps ahead in neon"],
        "Ice Princess — she already won before you started"),

    CharacterEntry("Mai Sakurajima", "Rascal Does Not Dream of Bunny Girl Senpai", CharType.WAIFU,
        "short dark hair, mysterious actress aura that fills every room she enters",
        ["iconic bunny outfit redesigned in cyberpunk leather and neon pink accents", "purple spotlight catching her perfectly while everything else dims",
         "knowing sharp gaze of someone who sees through every facade", "Adolescence Syndrome observation anomaly making her visible only to one"],
        "Bunny Girl Senpai — exists for one person only"),

    CharacterEntry("Yuno Gasai", "Future Diary", CharType.WAIFU,
        "long pink hair half-neat half-wild — two personalities in one hairdo",
        ["diary phone glowing ominous pink-red with next 90 days of her target's fate", "yandere smile beautiful and cracked — one eye loving one eye hunting",
         "blood neon tear on cheek making her more beautiful somehow", "love and murder made graphically indistinguishable in single expression"],
        "Yandere goddess — first place in survival game, forever"),

    CharacterEntry("Kurisu Makise", "Steins;Gate", CharType.WAIFU,
        "long reddish-brown hair, white lab coat with cyberpunk time research gear",
        ["teal time machine data streams swirling from open laptop mid-calculation", "brilliant sarcastic tsundere expression of someone who changed the world",
         "time paradox visualization as branching neon timelines orbiting her", "Christina nickname making her twitch while she pretends to work"],
        "Time machine genius — don't call her Christina"),

    CharacterEntry("Zero Two", "DARLING in the FranXX", CharType.WAIFU,
        "long pink hair with iconic black horns now glowing red neon, pilot suit redesigned as cyberpunk jumpsuit",
        ["Strelizia FranXX manifest as massive mech silhouette looming behind her", "wild confident grin of predatory beautiful chaos energy",
         "candy-pink circuits running up arms like veins beneath pale skin", "klaxosaur blood heritage crackling neon at horn base"],
        "Partner Killer — darling changed everything"),

    CharacterEntry("Ryuko Matoi", "Kill la Kill", CharType.WAIFU,
        "short black hair with red streak, Senketsu living uniform symbiosis",
        ["Scissor Blade half crackling life fiber red energy on enormous scale", "Senketsu absorbed power radiating red neon off revealing battle suit",
         "defiant expression of someone fighting the entire world and winning", "life fiber integration making veins glow red across skin"],
        "Scissor Blade — she'll cut the universe in half if she has to"),

    CharacterEntry("Satsuki Kiryuin", "Kill la Kill", CharType.WAIFU,
        "very long black hair whipping dramatically, absolute supreme authority in every posture",
        ["Bakuzan sword crackling absolute authority life fiber cutting neon", "commanding speech on high platform with elite four flanking as silhouettes",
         "iron will domination presence making enemies kneel from sheer authority alone", "eyebrows expressing more contempt than most people's entire faces"],
        "Iron Lady — I will have dominion"),

    CharacterEntry("Holo", "Spice and Wolf", CharType.WAIFU,
        "long brown hair with wolf ears perked and fluffy tail raised high, ancient harvest goddess eyes",
        ["apple in hand radiating warm amber harvest goddess neon", "wolf transformation large form with silver-white full moon behind",
         "wise playful smile hiding centuries of accumulated knowledge", "Yoitsu forest spirit connection visible as green leaf neon orbiting"],
        "Wisewolf of Yoitsu — the oldest merchant's secret"),

    CharacterEntry("Milim Nava", "That Time I Got Reincarnated as a Slime", CharType.WAIFU,
        "iconic twin pink drill pigtails, small frame containing catastrophic Demon Lord power",
        ["Drago Nova condensing full Primogenitor power into single annihilation point", "Milim Eye demonic eye stripping all illusion from existence",
         "cheerful open grin while casually erasing mountain ranges", "oldest and strongest Demon Lord playing like a child because she can"],
        "Oldest Demon Lord — don't let the pigtails fool you"),

    CharacterEntry("Tohru", "Miss Kobayashi's Dragon Maid", CharType.WAIFU,
        "long blonde hair with iconic horns and visible tail, dragon-maid energy",
        ["dragon transformation partial release showing scale wings and tail neon", "maid uniform coexisting with visible dragon power crackling",
         "absolute devotion expression barely containing dragon territory instincts", "divine dragon breath held back behind loving smile"],
        "Dragon maid — she could destroy the world, she makes pancakes instead"),

    CharacterEntry("Ai Hoshino", "Oshi no Ko", CharType.WAIFU,
        "long black hair with pink ends, idol stage presence filling concert hall",
        ["pink-gold star neon particles erupting from stage floor as idol persona activates", "ruby and aquamarine stars forming in air at performance peak",
         "smile that made the entire nation fall in love with absolute sincerity", "roses from audience frozen mid-fall in pink-white neon"],
        "The brightest idol — her love was the realest lie"),

    CharacterEntry("Rias Gremory", "High School DxD", CharType.WAIFU,
        "floor-length crimson hair cascading dramatically, devil noble bearing",
        ["Power of Destruction crimson ball of oblivion radiating from palm consuming matter", "devil wing deployment in full twelve-point spread neon red",
         "confident imperious posture of Gremory heir commanding absolute space", "aristocratic beauty expressing dominance as her natural resting state"],
        "Crimson-Haired Ruin Princess — destruction has never been this beautiful"),

    CharacterEntry("Akeno Himejima", "High School DxD", CharType.WAIFU,
        "very long black hair in iconic high ponytail, shrine maiden robe as cyberpunk thunder witch",
        ["violet lightning holy demonic fusion arcing between extended fingers", "soft smile hiding absolute ruthless power enjoying battle entirely too much",
         "fallen angel wings extending neon purple from shoulder blades", "lightning cage technique sealing target inside crackling violet sphere"],
        "Priestess of Thunder — she enjoys this a little too much"),

    CharacterEntry("Albedo (Genshin)", "Genshin Impact", CharType.WAIFU,
        "long white hair, alchemist of Mondstadt with homunculus secret",
        ["Tectonic Tide Geo platform eruption technique crystalline earth rising", "solar isotoma construct floating as golden platform crystal",
         "calm scientific expression analyzing everything with artist's eye", "Geo crystal neon orbiting in algorithmic patterns around hands"],
        "Chief Alchemist — the earth itself is his canvas"),

    CharacterEntry("Hu Tao", "Genshin Impact", CharType.WAIFU,
        "long brown twin pigtails with teal ends, spirit-sensing eyes",
        ["Paramita Papilio blood blossom technique wreathing body in ghost fire neon", "spirit butterfly orbiting in crimson-gold constellation",
         "mischievous funeral director expression that finds death genuinely funny", "Plum Blossom ghosts dancing behind her as playful death parade"],
        "77th Director of Wangsheng Funeral Parlor — death is her business and business is good"),

    CharacterEntry("Raiden Shogun", "Genshin Impact", CharType.WAIFU,
        "long purple hair with traditional kanzashi, electro archon bearing",
        ["Musou Isshin sword resonating electro nation ambition technique", "Baleful Shogun puppet taking over body in battle transformation",
         "divine electro power arcing off every surface near her presence", "Eternity ambition crackling purple neon off entire frame"],
        "Electro Archon — Eternity is her divine right"),

    CharacterEntry("Mona", "Genshin Impact", CharType.WAIFU,
        "long black twin pigtails, hydro astrologist in star-covered outfit",
        ["Mirror Reflection of Doom technique creating hydro mirror dimension", "star map holographic open showing fate prediction neon",
         "broke astrologer with incredible power refusing to monetize properly", "hydro bubble dome capturing target in alternate reality"],
        "Astrologist — she knows your fate and won't tell you"),

    CharacterEntry("Eula", "Genshin Impact", CharType.WAIFU,
        "long blonde hair, Aristocrat of Lawrence clan cryo claymore fighter",
        ["Glacial Illumination sword crackling cryo crystalline energy at maximum", "Vengeance pact building to explosive Lightfall detonation",
         "dancer's grace in every combat movement despite massive weapon", "noble bearing announcing she will remember this slight forever"],
        "Spindrift Knight — she will remember this"),

    CharacterEntry("Yae Miko", "Genshin Impact", CharType.WAIFU,
        "long pink hair with fox ears and nine tails, shrine keeper kitsune",
        ["Sesshou Sakura totem placing crackling electro fox spirit pillars", "kitsune fox fire neon arcing between totem network",
         "sharp calculating shrine keeper smile hiding divine trickster nature", "nine tails deploying partially as electro neon energy constructs"],
        "Electro fox — the shrine keeper always gets what she wants"),

    CharacterEntry("Fischl", "Genshin Impact", CharType.WAIFU,
        "long blonde twin pigtails with eyepatch, chuunibyou princess alter-ego",
        ["Oz crow companion deploying as electro laser cannon precision strike", "Midnight Phantasmagoria full transformation into true self",
         "dramatic theatrical expression fully committing to princess alter-ego identity", "electro neon orbiting in elaborate constellation formations"],
        "Princess of Immernachtreich — her delusion is also true"),

    CharacterEntry("Ayaka Kamisato", "Genshin Impact", CharType.WAIFU,
        "long white hair with snowflake ornaments, elegant Kamisato clan cryo swordswoman",
        ["Kamisato Art Soumetsu cutting tornado of cryo cherry blossoms", "dash technique leaving ice bloom trail of crystalline flowers",
         "composed noble expression masking genuine warmth underneath", "snow petals perpetually orbiting in slow deliberate rotation"],
        "Shirasagi Himegimi — grace that freezes everything it touches"),

    CharacterEntry("Lumine", "Genshin Impact", CharType.WAIFU,
        "blonde hair with star clip, Outlander Traveler with adaptable elemental power",
        ["seven element switching technique showing all elemental forms cycling", "sibling constellation connection glowing silver above head",
         "determined outsider expression of someone seeking lost family across worlds", "worlds-crossing light wings deploying as golden energy constructs"],
        "Traveler — from another world, fighting for this one"),

    CharacterEntry("Nahida", "Genshin Impact", CharType.WAIFU,
        "short white hair with leaf ornament, tiny frame of Lesser Lord Kusanali",
        ["Wisdom of God technique linking all minds in radius via neon leaf network", "Dendro archon true form emerging behind small vessel briefly",
         "curious innocent expression carrying the weight of abandoned god", "flower of paradise neon bloom expanding outward from raised hand"],
        "Dendro Archon — imprisoned in a box, still knew everything"),

    CharacterEntry("Furina", "Genshin Impact", CharType.WAIFU,
        "long silver hair with hydro blue eyes, former hydro archon theatrical performer",
        ["Salon Members hydro creatures summoning from performance space", "Endless Waltz technique deploying full god power hidden for 500 years",
         "theatrical dramatic expression of someone performing for 500 years finally released", "hydro archon true power signature emerging in brilliant blue neon"],
        "Hydro Archon — the longest performance, the most genuine tears"),

    CharacterEntry("Xianyun", "Genshin Impact", CharType.WAIFU,
        "white crane adepti form with long silver hair, anemo archon companion",
        ["Cloud Retainer plume technique shooting white crane feather lance", "adepti transformation half-crane half-human form glowing",
         "dignified ancient being adjusting to modern world with genuine difficulty", "white crane feathers orbiting in anemo neon spiral formation"],
        "Cloud Retainer — ten thousand years, still learning"),

    CharacterEntry("Navia", "Genshin Impact", CharType.WAIFU,
        "long blonde hair with elegant hat, Spina di Rosula leader geo fighter",
        ["Rosula Shinewave technique charging geo crystal shotgun massive barrage", "crystal shrapnel neon forming complex explosive constellation",
         "noble elegance commanding underground organization with genuine care", "mourning dress that became armor — she leads through grief"],
        "Chief of Spina di Rosula — elegance weaponized"),

    CharacterEntry("Clorinde", "Genshin Impact", CharType.WAIFU,
        "long dark hair with champion duelist bearing, electro sword and gun hybrid",
        ["Hunter's Vigil technique switching between gun and blade at hyperspeed", "electro duel pistol crackling with precise controlled lightning",
         "professional champion duelist expression that has never lost", "snake motif neon orbiting in electro patterns around blade"],
        "Champion Duelist of Fontaine — she hasn't lost yet"),

    # ─── MORE HIGH APPEAL ────────────────────────────────────────────
    CharacterEntry("Reina Ikari", "Original Cyberpunk Waifu", CharType.WAIFU,
        "shaved sides with long neon teal top hair, heavy cyber-implant modifications visible at temples",
        ["neural hack technique deploying teal data wave consuming enemy systems", "chrome-plated knuckles crackling electric discharge",
         "sleeveless techwear jacket over neon tattoos covering arms and neck", "cyberpunk street queen expression of someone who owns this city"],
        "Netrunner Queen — every system bends to her"),

    CharacterEntry("Seraphina Vex", "Original Cyberpunk Waifu", CharType.WAIFU,
        "long dark red hair with iridescent purple tint, mercenary sniper dark techwear",
        ["plasma rifle barrel neon-hot from sustained firing sequence", "scope overlay showing target lock network across entire battlefield",
         "contract killer calm over overwhelming battlefield situation", "neon tattoo sleeve down arm glowing during combat focus state"],
        "Hired gun — she never misses twice"),
]


# ═══════════════════════════════════════════════════════════════════════
# ══════════════ CHARACTER LIBRARY — ENGINE B: SHOUNEN ════════════════
# 100 entries, full power/legendary design, high-impact visuals
# ═══════════════════════════════════════════════════════════════════════

SHOUNEN_CHARACTERS: list[CharacterEntry] = [

    # ─── JUJUTSU KAISEN ─────────────────────────────────────────────
    CharacterEntry("Gojo Satoru", "Jujutsu Kaisen", CharType.SHOUNEN,
        "iconic white hair styled back, Six Eyes cerulean blue through removed sunglasses",
        ["Unlimited Void domain expansion infinite starfield consuming entire background", "Hollow Purple collision of Red and Blue detonating reality",
         "Infinity distortion sphere making space curve visibly around body", "most powerful sorcerer standing calm at center of universe breaking"],
        "Infinity — the honor of being the strongest"),

    CharacterEntry("Ryomen Sukuna", "Jujutsu Kaisen", CharType.SHOUNEN,
        "pink spiked hair, four arms, double set of eyes including cheek eyes open",
        ["Malevolent Shrine domain cleave cutting everything in kilometers", "Dismantle and Cleave invisible force shockwaves crossing dimensions",
         "black tattoos covering entire body glowing crimson ancient evil", "king of curses standing in annihilated cathedral of cursed energy"],
        "King of Curses — the honor of being the strongest"),

    CharacterEntry("Yuji Itadori", "Jujutsu Kaisen", CharType.SHOUNEN,
        "spiky pink hair with dark roots, Sukuna's vessel barely keeping him back",
        ["Divergent Fist cursed energy delayed detonation double impact", "Black Flash crackling between knuckles at moment of connection",
         "Sukuna tattoos crawling up arms as cursed energy overflows containment", "pure human body hosting monster power through sheer will alone"],
        "Divergent Fist — vessel of the King of Curses"),

    CharacterEntry("Megumi Fushiguro", "Jujutsu Kaisen", CharType.SHOUNEN,
        "dark messy hair, Ten Shadows calm calculation in every movement",
        ["Ten Shadows Technique deploying full divine beast array plus Mahoraga", "shadow energy consuming ground as endless summon space",
         "shikigami circle activating under feet drawing from infinite shadow", "cool detachment masking catastrophic power and real sacrifice"],
        "Ten Shadows — the technique that could kill Sukuna"),

    CharacterEntry("Yuta Okkotsu", "Jujutsu Kaisen", CharType.SHOUNEN,
        "messy dark hair, most cursed energy in the series output",
        ["Rika Queen of Curses massive specter consuming entire background", "Copy technique replicating all techniques simultaneously", 
         "overwhelming cursed energy output that dwarfs any sorcerer alive", "quiet gentle face creating maximum contrast with catastrophic power"],
        "Special Grade — universe of curses orbiting him"),

    CharacterEntry("Choso", "Jujutsu Kaisen", CharType.SHOUNEN,
        "long black hair divided by white streak, oldest death painting bearer",
        ["Supernova blood bullet hypersonic barrage leaving crimson trails", "Piercing Blood railgun condensed beam penetrating buildings",
         "calm ancient expression of someone thousands of years old in battle", "blood vessel forehead markings glowing neon during technique"],
        "Death Painting — blood older than Jujutsu society"),

    # ─── NARUTO ─────────────────────────────────────────────────────
    CharacterEntry("Naruto Uzumaki (Six Paths)", "Naruto", CharType.SHOUNEN,
        "spiky blonde hair with Truth-Seeking Orbs orbiting, Six Paths Mode",
        ["Six Paths Sage aura combining all nature transformations simultaneously", "Kurama fox spirit behind as massive god silhouette filling sky",
         "Planetary Rasengan eleven energy spheres construction mid-launch", "orange-gold-white power output making entire sky change color"],
        "Six Paths Sage — the son of prophecy fulfilled"),

    CharacterEntry("Sasuke Uchiha (Rinnegan)", "Naruto", CharType.SHOUNEN,
        "dark hair with blue Rinnegan and Eternal Mangekyo Sharingan active",
        ["Perfect Susanoo purple titan consuming everything around it", "Indra's Arrow maximum charge bow shot that can destroy bijuu",
         "lightning and dark energy fusion technique at god-tier output", "rival to god energy with cold calm face at epicenter of destruction"],
        "Indra's descendant — the eternal rival"),

    CharacterEntry("Itachi Uchiha", "Naruto", CharType.SHOUNEN,
        "long black hair in iconic low ponytail, mangekyo spinning blood-red",
        ["Amaterasu black inextinguishable flames erupting from eye", "Tsukuyomi illusion world fracturing reality visible in frame",
         "Susanoo ribcage with Yata Mirror and Totsuka Blade artifacts glowing", "greatest sacrifice hero looking like the greatest villain forever"],
        "Crow Genjutsu — he loved the village more than he loved himself"),

    CharacterEntry("Minato Namikaze", "Naruto", CharType.SHOUNEN,
        "iconic spiky yellow hair, Fourth Hokage cloak flowing",
        ["Flying Thunder God teleportation leaving yellow flash neon afterimage trails across frame", "Rasengan plus Kurama Mode combined attack charging",
         "greatest speed technique making him appear everywhere simultaneously", "yellow lightning across entire black sky from his movement alone"],
        "Yellow Flash — dead before anyone saw him move"),

    CharacterEntry("Might Guy (Eight Gates)", "Naruto", CharType.SHOUNEN,
        "thick eyebrows, Eight Gates Released Formation — Gate of Death opened",
        ["green-red steam vapor from cellular self-destruction wrapping body", "Evening Elephant five air vacuum punches audible across the world",
         "red steam aurora consuming entire frame like a descending comet", "burning himself away to protect what matters — peak determination"],
        "Eight Gates — the most passionate man in the world"),

    CharacterEntry("Kakashi Hatake (Six Paths)", "Naruto", CharType.SHOUNEN,
        "silver hair wild, Dual Mangekyo Sharingan both eyes revealed",
        ["Perfect Susanoo blue towering warrior god assembled around him", "Kamui lightning blade in right hand Susanoo sword in left",
         "gravity of legend visible in every particle orbiting frame", "masked face conveying absolute authority with single eye detail"],
        "Copy Ninja — Kakashi of the Sharingan"),

    CharacterEntry("Rock Lee", "Naruto", CharType.SHOUNEN,
        "bowl cut, bushy eyebrows, green Taijutsu jumpsuit",
        ["Eight Inner Gates partial opening with green-gold flame aura releasing", "Primary Lotus full speed drop technique crushing shockwave on impact",
         "training weights released creating craters from falling alone", "no ninjutsu no genjutsu just the hardest worker in the world"],
        "Taijutsu master — guts over genius"),

    # ─── BLEACH ─────────────────────────────────────────────────────
    CharacterEntry("Ichigo Kurosaki (True Shikai)", "Bleach", CharType.SHOUNEN,
        "spiky orange hair wild with spiritual pressure, all three powers fused",
        ["True Shikai Zangetsu cleave becoming scale that dwarfs mountains", "Final Getsuga Tensho Mugetsu erasing all light in universe briefly",
         "inner hollow and Quincy heritage and shinigami all three fusing at once", "pressure visible as black energy corona displacing atmosphere"],
        "King of Souls — Shinigami, Hollow, Quincy. All three."),

    CharacterEntry("Sosuke Aizen", "Bleach", CharType.SHOUNEN,
        "neat brown hair in ultimate butterfly transcendence form",
        ["Kyoka Suigetsu shatter-illusion reality fracture making impossible real", "Hogyoku integrated in chest glowing with all-seeing purple neon",
         "calm smile of someone who has won before the fight begins — every time", "god complex that he actually achieved through pure intelligence"],
        "Complete Hypnosis — he never lost. He was never in danger."),

    CharacterEntry("Kenpachi Zaraki", "Bleach", CharType.SHOUNEN,
        "spiked black hair with bells, eyepatch removed revealing true Reiatsu",
        ["Nozarashi Bankai activated as massive spiritual pressure blade cutting fate", "no technique just killing intent so overwhelming it reshapes space",
         "muscles straining and bleeding while grinning harder than anyone", "eye patch off — exponential spiritual pressure flooding the area instantly"],
        "Captain of Squad 11 — cuts even fate"),

    CharacterEntry("Byakuya Kuchiki", "Bleach", CharType.SHOUNEN,
        "neat black hair with silver kenseikan ornaments, noble judgment bearing",
        ["Senbonzakura Kageyoshi ten-thousand blades filling sky as pink snowstorm", "noble house captain absolute dignity in every particle of posture",
         "two modes: cold aristocrat and total annihilation — no middle", "petals becoming blades becoming storm of absolute judgment"],
        "Noble captain — Senbonzakura Kageyoshi"),

    CharacterEntry("Yamamoto Genryuusai", "Bleach", CharType.SHOUNEN,
        "ancient massive elder frame, old scar bisecting face and chest",
        ["Zanka no Tachi Nishi Zanjitsu Gokui technique absorbing all flames in existence", "Bankai solar sphere consuming everything in temperature reference",
         "oldest captain still the most devastating absolute apex of shinigami", "thousand years of fighting distilled into one Bankai release"],
        "Head Captain — he IS the fire"),

    CharacterEntry("Ulquiorra Cifer", "Bleach", CharType.SHOUNEN,
        "pale face with tear marks, Segunda Etapa final resurrection form",
        ["Lanza del Relampago javelin condensed Cero destroying entire areas on detonation", "black and green Cero power crackling from palm",
         "existential nihilism given perfect lethal form — highest Espada", "massive bat wings of pure condensed Reiatsu unfurled in final form"],
        "Espada 4 — he sees the heart in those who claim to lack one"),

    # ─── DRAGON BALL ────────────────────────────────────────────────
    CharacterEntry("Goku (Ultra Instinct Mastered)", "Dragon Ball", CharType.SHOUNEN,
        "silver-white hair with glowing silver UI aura corona",
        ["Ultra Instinct movement defeating gods with pure reactive grace", "Hakai destruction energy ball forming in palm threatening existence",
         "silver neon aura producing heatwave distorting atmosphere around body", "calm as water surface despite universe-shattering output"],
        "Ultra Instinct — even the gods can't keep up"),

    CharacterEntry("Vegeta (Ultra Ego)", "Dragon Ball", CharType.SHOUNEN,
        "widow-peak dark hair, dark purple Ultra Ego aura consuming all light",
        ["power that increases the more damage received — inverted destruction", "Final Explosion charging that would sacrifice self to destroy god",
         "Ultra Ego symbol visible in aura consuming background light", "pride of a Saiyan Prince who never yielded — not once"],
        "Ultra Ego — pride is his power source"),

    CharacterEntry("Gohan (Beast)", "Dragon Ball", CharType.SHOUNEN,
        "long white awakened hair, beyond all previous limits in Beast mode",
        ["explosive white neon aura cascading in sheets from body", "Special Beam Cannon charging in tribute to father figure Piccolo",
         "glasses broken on floor — scholar became the most powerful hybrid", "power making surrounding fighters feel gravity increase just from proximity"],
        "Beast Gohan — anger for Piccolo broke every limit"),

    CharacterEntry("Broly (Legendary)", "Dragon Ball", CharType.SHOUNEN,
        "massive frame towering, Legendary Super Saiyan primal green-tinted",
        ["green-tinted primal explosive aura dwarfing all other Saiyans combined", "Eraser Cannon green blast overwhelming two Super Saiyan Gods",
         "primal screaming face with power destabilizing planetary bodies nearby", "primordial Saiyan beyond all control — oldest power returning"],
        "Legendary Super Saiyan — the power even gods fear"),

    CharacterEntry("Future Trunks", "Dragon Ball", CharType.SHOUNEN,
        "iconic purple hair, Super Saiyan Rage blue electricity wrapping gold aura",
        ["Spirit Sword energy blade of hope and collected rage of destroyed future extending", "time machine sword channeling energy of all killed by androids",
         "blue and gold energy storm consuming entire frame simultaneously", "desperation of entire destroyed future carried on his shoulders home"],
        "Super Saiyan Rage — fighting for a future that's already gone"),

    CharacterEntry("Jiren", "Dragon Ball", CharType.SHOUNEN,
        "massive build, Universe 11 Pride Trooper absolute limit breaker",
        ["Power Impact ultra-concentrated ki sphere that destroys universes", "Limit Breaker aura making all surrounding space crack and fragment",
         "stoic face of someone who chose power over everything else", "full power release making spectators bleed from sheer proximity"],
        "Pride Trooper — power through solitude"),

    # ─── ONE PIECE ──────────────────────────────────────────────────
    CharacterEntry("Luffy (Gear Fifth)", "One Piece", CharType.SHOUNEN,
        "wild black hair turning white, Gear Fifth deity form white cloud aura",
        ["rubber reality-warping deity making entire island cartoonish in battle", "fist enlarged to city-block scale mid-punch at Kaido",
         "Sun God Nika form laughing while outputting god-tier power", "gigantic scale impact with clouds pulled in spiral around form"],
        "Sun God Nika — the joy of freedom made flesh"),

    CharacterEntry("Roronoa Zoro", "One Piece", CharType.SHOUNEN,
        "short green hair damp and wind-blown, three swords always ready",
        ["King of Hell Three-Sword Style massive energy dome detonating", "Asura nine phantom sword demon god silhouette manifesting behind",
         "Enma drinking haki and releasing devastating black neon slash", "eyepatch scar glowing haki — the weight of the promise to be best"],
        "King of Hell — he'll be the world's greatest swordsman or die trying"),

    CharacterEntry("Shanks (Red-Hair)", "One Piece", CharType.SHOUNEN,
        "flowing long red hair, Supreme King Haki casual output splitting oceans",
        ["Conqueror's Haki storm crackling across sky — pure presence", "Gryphon sword Kamusari swing leaving divine red-gold energy arc",
         "strongest man in the world requiring no effort to end everything", "single arm, absolute confidence — he never needed the other one"],
        "Four Emperor — the storm is his presence"),

    CharacterEntry("Whitebeard", "One Piece", CharType.SHOUNEN,
        "massive ancient titan frame, paramount war commander bearing",
        ["Gura Gura no Mi earthquake vibration technique splitting the sea in two", "quake bubble on bisento creating fault line in the air itself",
         "greatest pirate who ever lived accepting death standing", "world's strongest man falling standing — never hit his knees"],
        "Strongest Man in the World — died standing"),

    CharacterEntry("Dracule Mihawk", "One Piece", CharType.SHOUNEN,
        "dark hawk eyes under broad hat brim, world's greatest swordsman bearing",
        ["Kokuto Yoru sword slash extending miles in black crescent arc", "Haki-coated blade capable of slicing entire warships from range",
         "judgmental hawk eye gaze measuring everyone and finding them wanting", "world's greatest swordsman requiring single stroke for absolute result"],
        "World's Greatest Swordsman — Zoro's north star"),

    CharacterEntry("Kaido", "One Piece", CharType.SHOUNEN,
        "massive oni frame, Mythical Zoan Azure Dragon, Strongest Creature alive",
        ["Ragnaraku Club swing creating thunder from impact vibration", "Dragon form breath Bolo Breath obliterating mountain faces",
         "toughest creature in the world choosing to test his own immortality", "Thunderclap and Flash fist move creating atmospheric lightning"],
        "Strongest Creature — the world's only indestructible being"),

    # ─── DEMON SLAYER ───────────────────────────────────────────────
    CharacterEntry("Tanjiro Kamado (Hinokami)", "Demon Slayer", CharType.SHOUNEN,
        "short black hair with burgundy tips, Hinokami Kagura Sun Breathing active",
        ["Sun Breathing flame wheel spiral consuming entire frame in crimson gold", "Nichirin blade coated in solar plasma fire radiating heat",
         "tear and fire on face — determination in absolute distilled form", "ember particles swirling upward in thousands making sky orange"],
        "Sun Breathing — the original technique that can kill demons"),

    CharacterEntry("Rengoku Kyojuro", "Demon Slayer", CharType.SHOUNEN,
        "fierce flame-yellow hair spiking upward like fire, yellow-red eyes burning",
        ["Flame Breathing Ninth Form massive solar fire dragon roaring upward", "Flame Hashira uniform burning at edges from own technique output",
         "grin of absolute conviction even at death with arms outstretched", "volcano eruption energy output in every particle around body"],
        "Flame Pillar — SET YOUR HEART ABLAZE"),

    CharacterEntry("Tengen Uzui", "Demon Slayer", CharType.SHOUNEN,
        "long white hair wrapped in stylish binding, most flamboyant Hashira alive",
        ["Sound Breathing Constant Flux technique neon explosion frequencies made visible", "twin cleaver rotation creating sonic boom shockwaves radiating outward",
         "six pink neon explosions detonating around him simultaneously", "jewel-covered festival bandages glowing neon catching every light source"],
        "Sound Pillar — FLAMBOYANT"),

    CharacterEntry("Inosuke Hashibira", "Demon Slayer", CharType.SHOUNEN,
        "wild spiky black hair, iconic boar skull mask cracked open revealing feral face",
        ["Beast Breathing dual jagged blade wind slash carving massive terrain cuts", "beast instinct crackling as electric blue neon all over muscular frame",
         "savage crouching beast stance unleashing full feral power mode", "rocks and debris exploding outward from sheer aggressive output"],
        "Beast Breathing — feral power that senses everything"),

    CharacterEntry("Kokushibo", "Demon Slayer", CharType.SHOUNEN,
        "silver-purple hair in samurai bun, six eyes with crescent moon pupils glowing",
        ["Moon Breathing absolute pinnacle releasing silver moon crescent blade storm all directions", "samurai armor with demon transformation fusion",
         "half-human face cracking to reveal demon underneath samurai exterior", "moon-shard particles filling dark frame like personal blade galaxy"],
        "Upper Moon One — first demon swordsman"),

    # ─── ATTACK ON TITAN ────────────────────────────────────────────
    CharacterEntry("Levi Ackerman", "Attack on Titan", CharType.SHOUNEN,
        "undercut dark hair, Ackerman bloodline pure combat calculation",
        ["ODM triple-blade spinning technique used to slay Beast Titan solo", "Ackerman power aura calculating every possible outcome simultaneously",
         "lightning-fast movement leaving visible afterimage shadows", "face covered in scars and blood with zero concern for either"],
        "Humanity's Strongest Soldier — the only one who matters in the end"),

    CharacterEntry("Eren Yeager (Founding Titan)", "Attack on Titan", CharType.SHOUNEN,
        "wild dark hair, Founding Titan colossus form emerging from earth",
        ["Founding Titan colossus form 80-meter skeletal deity rising", "Wall Titans marching in thousands answering the Rumble",
         "Paths dimension visible as sepia lines in air during activation", "hollow screaming while collateral damage becomes history itself"],
        "Founding Titan — freedom at any cost"),

    CharacterEntry("Reiner Braun", "Attack on Titan", CharType.SHOUNEN,
        "blonde hair, Armored Titan warrior duty forcing smile through trauma",
        ["Armored Titan crystalline armor deploying as ultimate defense", "warrior duty cracking alongside traumatized mind in same frame",
         "most responsible for everything and still standing — weight of worlds", "titan shell cracking to reveal human underneath — always both"],
        "Armored Titan — duty cost him everything"),

    # ─── ONE PUNCH MAN ──────────────────────────────────────────────
    CharacterEntry("Saitama", "One Punch Man", CharType.SHOUNEN,
        "bald head, plain yellow costume, absolutely casual in front of anything",
        ["Serious Punch parting storm clouds across a continent from air pressure alone", "bored face delivering universe-shattering blow with no effort",
         "aftermath of total obliteration around one average-looking man", "single fist extended — everything in range simply ceases to exist"],
        "One Punch Man — too strong for his own story"),

    CharacterEntry("Garou (Cosmic Fear Mode)", "One Punch Man", CharType.SHOUNEN,
        "white hair spiked wild in Cosmic Fear Mode, God Power absorbed into human body",
        ["God Power star-level output in human vessel crackling everywhere", "Gravity techniques bending space in combat creating lens distortion",
         "copying every martial arts style into Godly Fist surpassing all limits", "cosmic power making him float amid shattered asteroids"],
        "Cosmic Garou — the strongest monster who became the greatest hero"),

    CharacterEntry("Tatsumaki", "One Punch Man", CharType.SHOUNEN,
        "short childlike figure, intense green eyes, floating black dress, maximum Psychokinesis",
        ["lifting entire destroyed city block above her in single telekinetic field", "compressed green psychic force barriers orbiting as shields",
         "arms crossed with absolute contempt while performing impossible feat", "most powerful esper in history looking bored by it"],
        "Tornado of Terror — bored by everyone, dangerous to all"),

    # ─── HUNTER X HUNTER ────────────────────────────────────────────
    CharacterEntry("Gon Freecss (Jajanken Peak)", "Hunter × Hunter", CharType.SHOUNEN,
        "spiky black hair, adult transformation burning own life potential for one moment",
        ["Jajanken Rock charging entire Nen lifeforce into single devastating fist", "golden Nen overflow aura visible as mile-wide explosion flash",
         "green Nen energy far past containment making atmosphere wobble", "primal scream releasing everything when friend is threatened"],
        "Hunter — he gave everything for one punch"),

    CharacterEntry("Killua Zoldyck (Godspeed)", "Hunter × Hunter", CharType.SHOUNEN,
        "white spiky hair, lightning bioelectric field Godspeed mode active",
        ["Godspeed Whirlwind body coated in lightning making him invisible from speed", "Thunderbolt strike leaving electric afterburn on impact surface",
         "assassin bloodline activated in eye change showing full dangerous potential", "silver-white lightning aura making hair and clothes levitate from charge"],
        "Godspeed — the most naturally gifted assassin born"),

    CharacterEntry("Hisoka Morrow", "Hunter × Hunter", CharType.SHOUNEN,
        "red and purple spiked hair, star and heart face marks glowing",
        ["Bungee Gum elastic sticky Nen stretching through entire arena", "magician battle performer finding joy in equal opponent",
         "card throw accelerated to bullet velocity with Bungee Gum assist", "everything about him radiating dangerous beautiful chaos energy"],
        "Bungee Gum — Hisoka is the most dangerous audience"),

    CharacterEntry("Meruem (Perfect Form)", "Hunter × Hunter", CharType.SHOUNEN,
        "pale humanoid chimera ant king, absorbed royal guard power",
        ["Nen absorption making Rose poison powerless by consuming Neferpitou and Shaiapouf power", "board game grandmaster calm in final moments",
         "brief beautiful tragedy of a monster who learned love from a blind girl", "royal guard power consumed and returned as ultimate chimera energy"],
        "Chimera Ant King — became human before he died"),

    CharacterEntry("Kurapika", "Hunter × Hunter", CharType.SHOUNEN,
        "blonde bangs, Emperor Time activated Scarlet Eyes full clan crimson iris",
        ["Emperor Time unlocking 100% nen system efficiency at cost of own lifespan", "Judgement Chain wrapping around opponent's heart with conditions",
         "grief and revenge and hope all burning in impossible red Kurta clan eyes", "chain jail inescapable restraint deploying from trained Conjuration"],
        "Scarlet Eyes — vengeance even at the cost of his own life"),

    # ─── FULLMETAL ALCHEMIST ─────────────────────────────────────────
    CharacterEntry("Edward Elric", "Fullmetal Alchemist: Brotherhood", CharType.SHOUNEN,
        "golden hair in braid, automail arm transforming into combat weapon",
        ["alchemy circles glowing under boots transmuting ground into entire fortress", "automail arm spear extended crackling alchemic energy",
         "short man with oversized power complex and the heart of a true hero", "golden neon of the Law of Equivalent Exchange surrounding him"],
        "Fullmetal Alchemist — the short one is the most dangerous"),

    CharacterEntry("Roy Mustang (Flame Alchemist)", "Fullmetal Alchemist: Brotherhood", CharType.SHOUNEN,
        "dark military uniform immaculate, ignition glove snap finger ready",
        ["Flame Alchemy producing a sun compressed into a column destroying facility", "blue flame version going beyond oxygen toward divine fire",
         "colonel to Fuhrer pipeline — calm face hiding catastrophic power", "flame circles consuming frame corner to corner from one finger snap"],
        "Flame Alchemist — all he needs is air"),

    CharacterEntry("King Bradley (Wrath)", "Fullmetal Alchemist: Brotherhood", CharType.SHOUNEN,
        "slicked hair, eye patch removed revealing Ultimate Eye tracking all",
        ["Ultimate Eye seeing all trajectories simultaneously — no attack lands", "five swords deployed hitting every weakness in one fluid motion",
         "Homunculus Wrath physical perfection making him fastest non-alchemy fighter", "Fuhrer cutting through opposition without receiving a single wound"],
        "Fuhrer King Bradley — the eye that sees all trajectories"),

    CharacterEntry("Greed (Ling)", "Fullmetal Alchemist: Brotherhood", CharType.SHOUNEN,
        "dark wild hair, Ultimate Shield carbon armor crackling",
        ["Ultimate Shield carbon-body technique making skin harder than diamond", "Greed and Ling dual consciousness fighting for control simultaneously",
         "greedy grin — wants everything and understands friends are worth more", "carbon armor partially deployed showing transformation mid-shift"],
        "The Greedy Homunculus — he wanted everything, gave everything"),

    # ─── SOLO LEVELING ──────────────────────────────────────────────
    CharacterEntry("Sung Jinwoo (Shadow Monarch)", "Solo Leveling", CharType.SHOUNEN,
        "dark hair, empty emotionless hunter eyes, Shadow Monarch power",
        ["shadow army of millions marching behind as dark silhouettes extending", "Kamish Wrath sword of shadows reaping arc through all life in range",
         "Igris and Beru flanking as massive shadow knight commanders", "death and power given human form with stone expressionless face"],
        "Shadow Monarch — slept while everyone trained, woke up strongest"),

    CharacterEntry("Sung Jinwoo (Dragon Scale Armor)", "Solo Leveling", CharType.SHOUNEN,
        "dark hair, full Shadow Monarch armor deployed, dragon-scale dark plate",
        ["full Monarch armor deployment shifting shadow to solid in wave", "Ruler's Authority technique levitating all metal in vicinity",
         "Dragon's Heart power amplifying all Shadow Monarch techniques", "iron resolve inside ultimate armor — the man who leveled alone"],
        "Arise — every hunter bows to the Shadow King"),

    # ─── BERSERK ─────────────────────────────────────────────────────
    CharacterEntry("Guts (Black Swordsman)", "Berserk", CharType.SHOUNEN,
        "massive Dragon Slayer sword in one arm that contains a cannon inside",
        ["Berserker Armor activated bleeding from joints while multiplying power", "Brand of Sacrifice wound bleeding black in presence of demons",
         "Apostle-killing charge through impossible odds refusing death", "mad dog grin — refuses to die because death means fate wins"],
        "Black Swordsman — the brand burns. he runs toward it."),

    CharacterEntry("Griffith (Femto)", "Berserk", CharType.SHOUNEN,
        "long white hair, Femto God Hand form with massive black wings",
        ["telekinesis and gravity manipulation warping everything in the vicinity", "God Hand reality distortion making physical laws suggestions",
         "cold beautiful face of absolute ambition achieving the dream at everything's cost", "Band of the Hawk shadow orbiting as sacrificed memory"],
        "Femto — the Hawk that flew above everything"),

    # ─── BLUE LOCK ──────────────────────────────────────────────────
    CharacterEntry("Isagi Yoichi", "Blue Lock", CharType.SHOUNEN,
        "dark hair wet with sweat, Spatial Awareness meta-vision activated",
        ["pitch grid overlay showing perfect shot calculation in real time", "goal scoring technique using perfect spatial physics leaving keeper helpless",
         "predator instinct awakening mid-match evolution in progress", "determined expression of someone becoming best striker through calculated greed"],
        "Striker — spatial awareness that sees gaps others can't imagine"),

    CharacterEntry("Rin Itoshi", "Blue Lock", CharType.SHOUNEN,
        "long dark hair tied back, Direct Drive Zone technique activated",
        ["Almighty Tornado blast combining spin and power breaking any goalkeeper", "predictive reaction body moving before thought in Direct Drive Zone",
         "cold eyes hiding rage and love for brother in exactly equal measure", "teal and dark aura of absolute technical soccer mastery"],
        "Blue Lock ace — born to be the best"),

    CharacterEntry("Bachira Meguru", "Blue Lock", CharType.SHOUNEN,
        "curly messy hair, Monster Inside instinct awakened",
        ["chaotic dribbling style no defensive system can pattern-match", "phantom monster visualization guiding feet through impossible path between defenders",
         "rainbow neon dribble path trail left behind feet through all defenders", "smile of someone who found his pack — pure joy of individual expression"],
        "Monster dribbler — the chaos they can't predict"),

    # ─── VINLAND SAGA ───────────────────────────────────────────────
    CharacterEntry("Thorfinn (Warrior Reborn)", "Vinland Saga", CharType.SHOUNEN,
        "long blonde hair wild from years of slavery, pacifist warrior",
        ["pure technique empty of bloodlust defeating berserkers without injury", "phantom lance strike so refined it wins without wanting to kill",
         "scar across face from the world's cruelty worn as evidence", "bearing weight of father's murder and own sins toward a land of peace"],
        "Vinland — the strongest man who chose not to fight"),

    CharacterEntry("Askeladd", "Vinland Saga", CharType.SHOUNEN,
        "short silver-blond hair, Roman-Welsh noble bearing in Viking world",
        ["Luin of Celtchar spear technique making him most dangerous individual combatant in Viking Age", "chess master reading every faction simultaneously",
         "warm dangerous smile of the greatest villain who was the greatest mentor", "winter breath visible in cold northern air above battlefield"],
        "Welsh Prince — the greatest schemer in the Norse age"),

    CharacterEntry("Thorkell the Tall", "Vinland Saga", CharType.SHOUNEN,
        "massive titan Nordic frame, laughing in the face of being outnumbered",
        ["throwing log as projectile weapon at supersonic range", "laughter audible through entire battle even as wounds accumulate",
         "berserker joy in finding stronger opponents making him live harder", "tower of a man making everyone else look proportionally small"],
        "Jomsviking giant — finds paradise in battle"),

    # ─── BLACK CLOVER ───────────────────────────────────────────────
    CharacterEntry("Asta", "Black Clover", CharType.SHOUNEN,
        "spiky white hair Anti-Magic form, five-leaf grimoire open",
        ["Anti-Magic concentrated black consuming surrounding magic completely", "Demon-Destroyer Sword enormous black claymore extended",
         "Devil Union Liebe fusion making skin half-black crackling anti-magic", "no magic but strongest will — the one who became Wizard King with nothing"],
        "Zero magic — the one who screamed his way to the top"),

    CharacterEntry("Yuno", "Black Clover", CharType.SHOUNEN,
        "long dark hair with golden four-leaf clover grimoire glowing",
        ["Star Magic massive constellation cannon charging across entire sky", "Wind Spirit Sylph merged multiplying all magic technique output",
         "spatial magic barriers unfolding like origami galaxies", "genius rival always a step ahead — elegant prodigy of everything Asta wasn't"],
        "Star Magic — the prodigy who makes it look effortless"),

    CharacterEntry("Licht", "Black Clover", CharType.SHOUNEN,
        "long silver hair, Sword Magic as first Wizard King",
        ["Sword Magic thousand blade array creating silver constellation storm", "World-ending Demon Slayer Sword technique in original Elf King form",
         "grief-fueled power beyond anyone alive carried in every slash", "first Wizard King — the weight of that era still crushing him"],
        "Licht — the first and greatest Wizard King"),

    # ─── TOKYO REVENGERS ────────────────────────────────────────────
    CharacterEntry("Mikey Sano (Dark Impulse)", "Tokyo Revengers", CharType.SHOUNEN,
        "platinum blonde bowl cut, delinquent king stance, dark impulse mode",
        ["Invincible Kick technique leg rising creating shockwave crack in asphalt", "dark impulse black aura underneath normal Mikey exterior breaking through",
         "natural gift for violence making him both best person to know and most dangerous", "gang king who broke every timeline trying to escape his own grief"],
        "Invincible Mikey — the sun that devoured itself"),

    CharacterEntry("Draken", "Tokyo Revengers", CharType.SHOUNEN,
        "long side-shaved hair with dragon tattoo on temple glowing blue",
        ["Dragon's Fang technique releasing visible blue impact ring on landing", "towering loyal frame protecting his king without question",
         "old-school delinquent with heart made entirely of gold", "most reliable person in any gang fighting for the right reasons"],
        "Vice Captain — the dragon who held everything together"),

    # ─── MHA ────────────────────────────────────────────────────────
    CharacterEntry("Izuku Midoriya (OFA Dragon Fist)", "My Hero Academia", CharType.SHOUNEN,
        "messy green hair wild with One For All electricity crackling everywhere",
        ["100% Full Cowl Delaware Smash Air Force Black Whip combined", "all OFA predecessors ghosts standing behind as spirit council",
         "Gear Shift Full Cowl maximum output cratering ground under feet", "screaming into wind refusing to give up — the boy who became a hero"],
        "One For All — power handed down by hope"),

    CharacterEntry("Katsuki Bakugo", "My Hero Academia", CharType.SHOUNEN,
        "spiky ash-blonde hair in explosion wind, most aggressive competitive drive",
        ["Howitzer Impact spinning plasma AP Shot detonation at point blank range", "explosion plasma orange-black neon bursting from both palms simultaneously",
         "blast backwash making hair and jacket explode dramatically outward", "rival born to push Deku to the absolute limit"],
        "Explosion Hero — King Explosion Murder"),

    CharacterEntry("Shoto Todoroki", "My Hero Academia", CharType.SHOUNEN,
        "half-white half-red hair split perfectly down center, Phosphor white flame",
        ["left side ice glacier right side fire pillar simultaneously at maximum", "Phosphor bright white flame radiating from entire body",
         "both powers fully combined accepting both halves of himself finally", "path chosen by himself not his father — the real resolution"],
        "Half Cold Half Hot — his power, his choice"),

    CharacterEntry("All Might", "My Hero Academia", CharType.SHOUNEN,
        "iconic massive muscle form, symbol of peace in borrowed time",
        ["United States of Smash final punch as last act of Symbol of Peace", "gaunt injured face inside massive borrowed power still smiling",
         "cape disintegrating in own power output but never slowing", "sunrise always behind him — hope given physical form"],
        "Symbol of Peace — PLUS ULTRA"),

    CharacterEntry("Tomura Shigaraki (All For One)", "My Hero Academia", CharType.SHOUNEN,
        "pale cracked hands and disheveled blue-gray hair, All For One awakening",
        ["Decay touching ground — entire city block disintegrating in expanding wave", "All For One awakening making face crack and reform mid-scene",
         "Paranormal Liberation Front general at full apocalyptic power output", "inherited hatred and stolen power — empty eyes becoming something beyond villain"],
        "All For One — the villain who was always the real threat"),

    CharacterEntry("Overhaul", "My Hero Academia", CharType.SHOUNEN,
        "plague mask and spiky brown hair, Shie Hassaikai yakuza bearing",
        ["Overhaul quirk reconstructing entire buildings as weapons in combat", "body modification fusing with subordinates to create new forms",
         "absolute disgust at dirt and disorder while creating chaos himself", "destroying and rebuilding reality as weapon simultaneously"],
        "Overhaul — he can unmake you and remake you wrong"),

    # ─── MISC POWER TIER ─────────────────────────────────────────────
    CharacterEntry("Anos Voldigoad", "The Misfit of Demon King Academy", CharType.SHOUNEN,
        "dark hair, demon king reincarnated surpassing all records",
        ["Venuzdonoa sword of ruin destroying cause and effect of target", "Igram black flame consuming concepts not just matter",
         "absolute overwhelming power in casual clothing showing no effort needed", "demon king who transcended death in original era still dominates"],
        "Demon King — he destroyed even death"),

    CharacterEntry("Rimuru Tempest", "That Time I Got Reincarnated as a Slime", CharType.SHOUNEN,
        "silver short hair slime-god form, Sage and Great Demon Lord combined",
        ["Infinite Regeneration and Predator consuming any ability used against him", "True Dragon class Harvest Festival aura consuming sky",
         "Belzebuth and Raphael working simultaneously as dual ultimate skills", "most broken protagonist progression making gods look under-powered"],
        "Demon Lord Rimuru — he ate his way to godhood"),

    CharacterEntry("Isshiki Otsutsuki", "Boruto", CharType.SHOUNEN,
        "massive frame with Otsutsuki clan divine bearing, Sukunahikona active",
        ["Sukunahikona shrinking targets to microscopic scale, Daikokuten storing them", "Chakra level dwarfing all tailed beasts combined easily",
         "divine tree cultivation mission making him existential threat to planet", "dying Otsutsuki choosing one last devastating act"],
        "Otsutsuki — the parasite that eats planets"),

    CharacterEntry("Code", "Boruto", CharType.SHOUNEN,
        "white hair with limiters removed, claw marks extending as warp tunnels",
        ["Limitless Claw Marks warping across global distances instantly", "power exceeding even Isshiki after limiter removal",
         "fanatic devotion to Otsutsuki cause making him existential weapon", "claw mark space folding making physical distance meaningless in combat"],
        "Code — limitless, unstoppable, devoted to annihilation"),

    CharacterEntry("Madara Uchiha (Juubi Jinchuriki)", "Naruto", CharType.SHOUNEN,
        "long black hair, Ten-Tails Jinchuriki — became god of the shinobi world",
        ["Limbo Hengoku six shadow clones from underworld with equal power", "Truth-Seeking Orbs 72 black spheres orbiting destroying anything touched",
         "god-tier Sage of Six Paths power surpassing all previous limits", "most powerful shinobi who ever lived making five Kage look like warm-up"],
        "Madara Uchiha — the only man who could make the moon his eye"),

    CharacterEntry("Obito Uchiha (Ten-Tails)", "Naruto", CharType.SHOUNEN,
        "swirled mask removed revealing Obito's true identity and Rinnegan",
        ["Kamui dimension phasing making all physical attacks pass through", "Ten-Tails Jinchuriki world-scale power before final redemption",
         "redemption arc changing history from inside a dying body", "the child who became a god who became human again in the end"],
        "Obito — the tragedy that powered a generation of villains"),

    CharacterEntry("Pain / Nagato (Six Paths)", "Naruto", CharType.SHOUNEN,
        "body destroyed but six puppets channeling Rinnegan god-tier jutsu",
        ["Shinra Tensei massive repulsion making entire Konoha disappear in impact", "Chibaku Tensei creating moon from compressed gravitational chakra sphere",
         "six paths of pain operating simultaneously as one mind with six bodies", "messiah complex from genuine tragedy making him most relatable villain"],
        "Pain — if you don't understand pain you cannot understand peace"),

    CharacterEntry("Raizo Asamura", "Original Cyberpunk Shounen", CharType.SHOUNEN,
        "shaved sides with dark long top hair, street fighter build with neon tattoos",
        ["street combat style fusing martial arts with cyberpunk energy enhancement", "chrome knuckle implants crackling electric discharge mid-combo",
         "gang street king bearing with neon tattoo sleeve glowing during focus", "underdog who reached the top through pure violent will"],
        "Street king — the city made me"),
]


# All characters combined
ALL_CHARACTERS: list[CharacterEntry] = WAIFU_CHARACTERS + SHOUNEN_CHARACTERS


# ═══════════════════════════════════════════════════════════════════════
# EMOTION SYSTEM v2
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
        "body": "elegant contrapposto with weight shift, confident curves visible, one hand at hip",
        "energy": "warm rose-gold neon casting flattering from below and behind",
        "aura_color": "rose gold",
    },
    EmotionArchetype.DOMINANT_VIBE: {
        "face": "sharp knowing smirk, eyes radiating absolute confidence of someone who always wins",
        "body": "power stance — feet wide, weight forward, ready for anything",
        "energy": "intense electric neon aura visible as charged atmosphere around body",
        "aura_color": "electric white",
    },
    EmotionArchetype.PLAYFUL_DANGER: {
        "face": "bright mischievous grin concealing real threat — playful and lethal simultaneously",
        "body": "playful lean-in pose with finger raised knowingly, feet never still",
        "energy": "pastel neon sparking chaotically in unpredictable bursts around frame",
        "aura_color": "neon pastel chaos",
    },
    EmotionArchetype.ETHEREAL_SORROW: {
        "face": "beautiful melancholy — distant gorgeous eyes carrying ancient grief",
        "body": "graceful stillness, floating slightly, outfit and hair drifting in absent wind",
        "energy": "soft silver-blue neon dissolving at edges like forgotten memory",
        "aura_color": "silver moonlight",
    },
    EmotionArchetype.BATTLE_FURY: {
        "face": "intense battle expression — locked on target, jaw set, eyes burning with focus",
        "body": "aggressive forward lean, weapon raised or technique charging, in motion",
        "energy": "explosive neon aura crackling at every joint point of body",
        "aura_color": "fierce crimson gold",
    },
    EmotionArchetype.SOFT_OBSESSION: {
        "face": "soft devoted expression — loving eyes that are a little too intense for comfort",
        "body": "arms slightly open as if always ready to embrace, tilted toward subject",
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
        "face": "limit break expression — screaming or gritting teeth, veins visible, unleashing everything",
        "body": "maximum power pose — every muscle tensed, technique fully deployed",
        "energy": "catastrophic multi-color power eruption consuming entire frame",
        "aura_color": "multi-spectrum neon catastrophe",
    },
    EmotionArchetype.SILENT_APEX: {
        "face": "emotionless apex predator — no expression needed when your power speaks",
        "body": "weapon at rest, relaxed posture that hides the most terrifying power",
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
        WAIFU_EMOTION_WEIGHTS
        if char_type == CharType.WAIFU
        else SHOUNEN_EMOTION_WEIGHTS
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
# VISUAL HOOK SYSTEM — ONE SCROLL-STOPPER PER IMAGE
# ═══════════════════════════════════════════════════════════════════════

WAIFU_VISUAL_HOOKS: list[tuple[str, int]] = [
    # (hook description, weight)
    ("NEON GLOWING EYES as primary visual hook — pupils burning with unearthly color neon, multiple catchlights, irises radiating power from within, eyes visible from thumbnail distance", 25),
    ("MASSIVE AURA EXPLOSION as primary visual hook — power aura erupting outward in massive expanding ring from center, consuming 60% of frame, silhouette clear against energy", 20),
    ("INTENSE CLOSE-UP EXPRESSION as primary visual hook — face fills upper 40% of frame with devastating emotional expression lit dramatically by own power", 18),
    ("SIGNATURE WEAPON GLOW as primary visual hook — weapon or technique radiating so much energy it becomes the brightest object in frame, everything else lit by it", 15),
    ("DYNAMIC HAIR EXPLOSION as primary visual hook — hair erupting outward from power release wind filling frame corners beautifully", 12),
    ("TATTOO OR MARKING GLOW as primary visual hook — power markings across skin activating in brilliant neon making entire body a light source", 10),
]

SHOUNEN_VISUAL_HOOKS: list[tuple[str, int]] = [
    ("CATASTROPHIC POWER AURA as primary visual hook — multi-layer power aura erupting consuming 70% of frame while character stands at impossible calm center", 30),
    ("GLOWING TECHNIQUE ACTIVATION as primary visual hook — signature technique charging or releasing as the single brightest element in composition, undeniable focal point", 25),
    ("INTENSE LOCKED-ON EYES as primary visual hook — eyes glowing with technique or power activated visible from distance, jaw set, locked onto target beyond camera", 20),
    ("SCALE CONTRAST as primary visual hook — character dwarfed by their own technique, summoned entity or aura to create dramatic size contrast showing true power scale", 15),
    ("BATTLE DAMAGE POWER SURGE as primary visual hook — injuries visible but power increasing from them, damaged clothes revealing glowing power underneath", 10),
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
# POSE SYSTEM v2
# ═══════════════════════════════════════════════════════════════════════

WAIFU_POSES: list[str] = [
    "confident hip pop stance, one hand at waist and other extended with glowing technique, weight shifted to one leg elegantly",
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
    "spinning freeze-frame at maximum rotation, outfit and hair caught in perfect spiral of motion",
    "kneeling with head bowed then eyes rising slowly — the calm before catastrophic action",
    "standing atop destroyed architecture looking down at destroyed cityscape she made",
    "hand to jaw thoughtful expression while obvious catastrophic power builds behind back",
    "mid-dodge lean — weight fully committed sideways, hair and outfit following arc beautifully",
    "two-finger raised at cheek, devil-may-care expression while technique fires automatically behind",
    "reaching one hand toward viewer with neon effect dripping from fingertips",
    "seated cross-legged floating, meditating with power storm orbiting in controlled chaos",
    "charging stance — one leg back weight low, full body technique loading for release",
    "falling backwards on purpose, eyes closed, trusting power will catch and everything else won't matter",
    "hand in own hair with satisfied smile, aftermath of battle already won behind her",
    "back-to-back with shadow/ghost version of self — two sides of power acknowledging each other",
    "dual-technique pose — both hands extended different techniques from each hand simultaneously",
    "low split stance — impossible flexibility deployed as combat advantage with technique extending",
    "walking away from explosion she caused, not looking back, supremely unconcerned",
    "turning fully toward camera with weapon lowered — the fight is over. she won.",
    "arms raised above head technique charging skyward — the most dramatic pre-release moment",
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
    "back to camera looking over shoulder at enormous technique deployed ahead of them",
    "calm center of absolute destruction — technique doing the work while they wait",
    "both hands forward technique merged and amplified beyond either alone",
    "mid-scream maximum power release — limit break expression, hair all rising",
    "two-handed weapon swing frozen at maximum arc — the single most powerful moment",
    "defensive stance — arms crossed taking direct hit and it doesn't even matter",
    "parallel to ground horizontal flight trajectory mid-attack — fastest combat speed",
    "ascending to power — floating upward while aura builds beneath, scale growing",
    "descent from height — diving attack with everything committed, no defense needed",
    "finishing stance — opponent defeated, weapon lowered, power still crackling in air",
    "pointing single finger down toward enemy far below — the most dangerous gesture",
    "three-point landing — fist ground crater from speed, head up, eyes target-locked",
    "crossed arms releasing aura — making zero effort but destroying everything nearby",
    "dual-simultaneous technique — different power from each hand meeting in center",
    "catching opponent's strongest attack one-handed — unimpressed, maximum disrespect",
    "slow turn revealing true form — half-profile turning to face, power visible escalating",
    "mid-air standoff freeze — both combatants suspended, technique about to decide all",
    "power stance on elevated broken platform, entire destroyed city below as backdrop",
    "technique fully charged glowing maximum — the moment before everything changes",
    "last stand pose — battered and damaged but power output higher than ever before",
    "victorious still — the dust settles and they're the only one standing, barely breathing",
]


def _select_pose(rng: random.Random, char_type: CharType) -> str:
    poses = WAIFU_POSES if char_type == CharType.WAIFU else SHOUNEN_POSES
    return rng.choice(poses)


# ═══════════════════════════════════════════════════════════════════════
# WAIFU-SPECIFIC EXTRAS (tattoos, piercings, fashion)
# ═══════════════════════════════════════════════════════════════════════

WAIFU_TATTOO_DETAILS: list[str] = [
    "delicate neon circuit tattoo tracing collarbone and neck with faint power glow",
    "serpentine tattoo along ribcage and side visible at outfit gap, glowing softly during power use",
    "intricate star constellation tattoo pattern across shoulder blade and upper arm neon-lit",
    "geometric mandala tattoo at upper thigh catching neon light beautifully",
    "script tattoo along inner forearm in fictional language that means power",
    "butterfly tattoo at clavicle shifting color with emotional state",
    "tribal pattern tattoo across one cheekbone — subtle but unmistakable",
    "spine tattoo visible at back — glowing when channeling power fully",
]

WAIFU_PIERCING_DETAILS: list[str] = [
    "industrial bar piercing in upper ear catching neon light as tiny highlight",
    "nose ring with small neon gem glowing softly",
    "eyebrow piercing casting tiny rim shadow on brow bone",
    "multiple helix piercings up one ear each catching different neon colors",
    "constellation piercing pattern — three small gems tracing Orion across one cheek",
    "lip ring catching neon reflection dramatically",
    "septum ring in clean polished silver reflecting environment lighting",
    "subtle cheekbone dermal piercing glowing faintly — easy to miss, impossible to forget",
]

WAIFU_FASHION_DETAILS: list[str] = [
    "oversized cyberpunk jacket with neon inner lining hanging off one shoulder",
    "techwear bodysuit with translucent panels over key areas, circuitry detail throughout",
    "cropped mech-vest over fitted top, tactical straps and neon piping at every seam",
    "thigh-high armored boots with neon trim, magnetic clasp detail",
    "fishnet underlayer beneath armor plate — street punk meets high-tech",
    "asymmetric hemline dress with reinforced combat panels integrated seamlessly",
    "holographic fabric at key panels shifting color with movement and light angle",
    "form-fitting high-collar top with open back window showing tattoo or marking",
    "detached cyber-sleeves with integrated tech display showing power reading",
    "micro-armor plates floating magnetically at shoulder and hip — protective and striking",
]


def _build_waifu_extras(rng: random.Random) -> str:
    tattoo = rng.choice(WAIFU_TATTOO_DETAILS)
    piercing = rng.choice(WAIFU_PIERCING_DETAILS)
    fashion = rng.choice(WAIFU_FASHION_DETAILS)
    return (
        f"subtle enhancement details: {tattoo}, {piercing}, "
        f"fashion detail: {fashion}, "
        "slightly revealing outfit showing curves at waist and hips without explicit content, "
        "body language confident and dominant — seductive but powerful not vulnerable, "
        "glossy lips with neon tint matching aura color, sharp eyeliner extending slightly, "
        "clean healthy skin with power-glow reflection pooling at key points"
    )


# ═══════════════════════════════════════════════════════════════════════
# SHOUNEN-SPECIFIC EXTRAS (auras, battle states)
# ═══════════════════════════════════════════════════════════════════════

SHOUNEN_POWER_EXTRAS: list[str] = [
    "primary power aura layered beneath secondary technique aura — two-color halo system",
    "veins of power visible under skin glowing matching technique color",
    "battle damage increasing power — torn uniform revealing glowing power within",
    "heat distortion visible as atmospheric warping around high-power output body",
    "ground fractured concentrically outward from stance pressure alone",
    "gravity distortion bending light around character during peak power state",
    "charged particles orbiting body in predictable elliptical pattern like personal solar system",
    "sound wave rings visible as circular atmospheric compression from power breathing",
    "pressure differential making enemy's approach visible as wind toward character",
    "hair rising and separating from static charge of power field surrounding body",
]

SHOUNEN_BATTLE_DETAILS: list[str] = [
    "strategic tear in uniform from previous technique impact showing no concern for it",
    "sweat and dust on face — this fight cost something, still winning",
    "opponent's impact visible as crater behind — they took the hit and it didn't matter",
    "breathing visible as power-charged mist in cold air mid-technique",
    "blood on knuckle or lip — minor, irrelevant, power still increasing",
    "one eye slightly damaged — still more dangerous than anything untouched",
    "boots cracking concrete underfoot from accumulated power pressure",
    "echo of technique visible as ghost imprint on air behind strike path",
]


def _build_shounen_extras(rng: random.Random) -> str:
    power = rng.choice(SHOUNEN_POWER_EXTRAS)
    battle = rng.choice(SHOUNEN_BATTLE_DETAILS)
    return (
        f"power state: {power}, "
        f"battle realism: {battle}, "
        "massive glowing eyes — irises lit by power technique from within, "
        "dominant masculine build with power visible in every defined muscle group, "
        "intense locked-on expression — nothing in the world exists except the opponent, "
        "streetwear or battle uniform appropriate to series with cyberpunk neon enhancement, "
        "gang or warrior energy — trapstar aura in stance and expression"
    )


# ═══════════════════════════════════════════════════════════════════════
# COMPOSITION ENGINE — 9:16 MOBILE-FIRST
# ═══════════════════════════════════════════════════════════════════════

COMPOSITION_STYLES: list[dict] = [
    {
        "name": "full_body_power",
        "prompt": (
            "FULL BODY vertical composition — character head to toe filling 9:16 mobile frame, "
            "character occupies 85% of frame height with feet on ground or mid-air, "
            "strong readable silhouette against explosive cyberpunk background, "
            "dramatic 15-degree low angle making character feel godlike in scale, "
            "complete outfit and signature weapon/technique visible throughout, "
            "debris, energy, and particles filling every corner of frame"
        ),
        "waifu_weight": 25,
        "shounen_weight": 30,
    },
    {
        "name": "full_body_dynamic",
        "prompt": (
            "FULL BODY action composition — character mid-motion at maximum power output, "
            "entire body visible from head to feet with technique deployed, "
            "Dutch angle adding extreme kinetic drama to vertical 9:16 frame, "
            "hair and outfit caught in power-release shockwave motion, "
            "impact shockwave rings visible in atmosphere around body, "
            "character 80% of frame height, background crumbling from technique output"
        ),
        "waifu_weight": 20,
        "shounen_weight": 25,
    },
    {
        "name": "three_quarter_cinematic",
        "prompt": (
            "3/4 BODY SHOT — character from mid-thigh up filling vertical 9:16 frame, "
            "face in upper third of frame at full detail — expression readable at distance, "
            "full upper body and thighs visible with technique and outfit detailed, "
            "one hand/weapon extended toward viewer with energy charging, "
            "cinematic depth — character razor-sharp, background beautifully blurred explosion, "
            "energy corona and particle system surrounding entire visible frame"
        ),
        "waifu_weight": 30,
        "shounen_weight": 25,
    },
    {
        "name": "three_quarter_portrait",
        "prompt": (
            "3/4 BODY PORTRAIT — waist-to-crown shot emphasizing face and power simultaneously, "
            "face upper third with photogenic angle showing best features, "
            "outfit and power effects from waist up fully detailed, "
            "cinematic split-lighting — colored neon hitting from two directions creating drama, "
            "massive power effect consuming background behind subject, "
            "vertical 9:16 with perfect character centering for mobile viewing"
        ),
        "waifu_weight": 20,
        "shounen_weight": 15,
    },
    {
        "name": "back_view_dramatic",
        "prompt": (
            "DRAMATIC BACK SHOT — character facing destroyed cyberpunk vista, "
            "face turned 3/4 revealing profile or three-quarter expression, "
            "full silhouette from behind with aura corona creating luminous edge, "
            "outfit, hair, and power effects breathtaking from rear perspective, "
            "neon city sprawl or destroyed landscape stretching below, "
            "viewer positioned as witness to their next action — scale is overwhelming"
        ),
        "waifu_weight": 5,
        "shounen_weight": 5,
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
# PARTICLE DENSITY TIERS
# ═══════════════════════════════════════════════════════════════════════

PARTICLE_TIER_MEDIUM = (
    "MEDIUM PARTICLE DENSITY — hundreds of neon energy particles orbiting body in readable pattern, "
    "technique-specific particle type matching character's power color, "
    "debris field from recent impact floating in organized composition, "
    "neon bokeh orbs in background depth softly glowing"
)

PARTICLE_TIER_HEAVY = (
    "HEAVY PARTICLE DENSITY — thousands of neon particles creating galaxy-like density around body, "
    "multiple particle types layered — foreground medium large, midground small dense, background bokeh, "
    "technique particles matching power color erupting in every direction from epicenter, "
    "shockwave rings visible in atmospheric compression, speed blur streaks visible"
)

PARTICLE_TIER_CATASTROPHIC = (
    "CATASTROPHIC PARTICLE DENSITY — overwhelming particle storm consuming frame, "
    "character at perfect calm center of particle catastrophe, "
    "layered depth — foreground particle sheets, midground explosion cloud, background neon bokeh, "
    "each particle casting individual neon shadow on nearby surfaces, "
    "shockwave rings, lightning web, speed blur, AND debris field simultaneously, "
    "atmosphere itself visible as displaced pressure rings expanding outward"
)

PARTICLE_TIERS: list[tuple[str, str, int, int]] = [
    # (name, prompt, waifu_weight, shounen_weight)
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
# LIGHTING STACK v2 — 5-LAYER CINEMATIC NEON SYSTEM
# ═══════════════════════════════════════════════════════════════════════

LIGHTING_STACKS: list[dict] = [
    {
        "name": "split_neon",
        "prompt": (
            "CINEMATIC SPLIT NEON LIGHTING — primary teal rim light hitting left from behind creating luminous silhouette edge, "
            "secondary hot pink fill light from right modeling face and body volume, "
            "technique glow illuminating character from below and within, "
            "neon color pool reflections shimmering on skin and costume surfaces, "
            "volumetric god rays cutting through atmospheric smoke at 45-degree angle, "
            "eyes catching both neon sources creating multi-color catchlight array"
        ),
    },
    {
        "name": "power_backlight",
        "prompt": (
            "CINEMATIC POWER BACKLIGHT STACK — overwhelming technique or aura backlight creating perfect silhouette rim, "
            "strong single-source power glow from technique creating dramatic forward shadow, "
            "secondary ambient neon from cityscape environment providing fill, "
            "practical light from weapon or power marking as tertiary character light source, "
            "face lit exclusively by power glow — most dramatic and readable at thumbnail scale, "
            "eyes glowing as if internally lit, catching technique color"
        ),
    },
    {
        "name": "noir_neon",
        "prompt": (
            "CINEMATIC NOIR NEON LIGHTING — 80% deep shadow with hard neon slivers cutting through, "
            "single strong colored rim light creating dramatic face shadow play, "
            "neon signs and environment providing asymmetric practical fills, "
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
            "environmental fire or energy providing warm practical backlight, "
            "eyes catching explosion flash as intense bright catchlight"
        ),
    },
    {
        "name": "divine_glow",
        "prompt": (
            "CINEMATIC DIVINE GLOW STACK — character as their own light source radiating in all directions, "
            "power aura so bright it lifts shadows from nearby surfaces, "
            "secondary contrast neon from environment preventing overexposure, "
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
# PALETTE ENGINE v2
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
    Palette("rose_chrome",   "rose neon",          "brushed chrome",    "deep navy",          "high-fashion cyberpunk — glamour weaponized for maximum appeal",                  15,  0),  # waifu only
    Palette("indigo_silver", "deep indigo",        "mirror silver",     "dark purple",        "ethereal mystery — space between stars given neon color",                          8, 10),
    Palette("fire_storm",    "solar fire orange",  "storm black",       "volcano dark",       "primal power — sun meeting void, oldest energies in combat",                       0, 15),  # shounen only
]


def _weighted_palette_v2(rng: random.Random, char_type: CharType) -> Palette:
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
# BACKGROUND LIBRARY v2
# ═══════════════════════════════════════════════════════════════════════

WAIFU_BACKGROUNDS: list[str] = [
    "rain-soaked cyberpunk neon rooftop at night, city sprawl glowing below, kanji signs overhead",
    "luxury cyberpunk penthouse interior with floor-to-ceiling windows showing neon city",
    "cyberpunk underground club with laser grid and smoke atmosphere frozen mid-pulse",
    "cherry blossom cyberpunk shrine — traditional torii gate absorbing neon energy",
    "reflective wet alley with fractured neon kanji signs blurring in puddle mirrors",
    "cyberpunk fashion district with holographic model displays flickering",
    "abandoned server hall with blue equipment light striping through smoke",
    "dark void with single neon ring lighting and dense particle field — pure character focus",
    "cyberpunk night market with warm amber vendor lights and teal sky above",
    "elevated highway with distant city below and storm clouds catching neon above",
    "cyber-shrine courtyard with digital rain falling and traditional lanterns neon-lit",
    "concert main stage mid-destruction — neon beams and smoke and awe-frozen crowd",
]

SHOUNEN_BACKGROUNDS: list[str] = [
    "destroyed urban canyon — buildings shattered outward from technique impact point",
    "volcanic wasteland with lava channels and smoke atmosphere for power-level settings",
    "outer space — planetary surface below, stars above, their power visible from orbit",
    "oceanic cliffside — waves shattered by power output, spray frozen in shockwave",
    "tournament arena destroyed — crater where stands were, smoke clearing slowly",
    "dark dimensional space — suspended debris and shattered reality geometry in shadow realm",
    "ancient battlefield — ruins of previous great conflicts beneath new destruction",
    "rooftop cityscape — entire block visible below and cracking from technique impact",
    "underground cavern — cave walls cracking from power output, dust falling upward",
    "mountain range — peaks shearing from shockwave at distance, scale made visible",
    "train wreckage — industrial destruction as backdrop for industrial power output",
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

# (waifu boost, shounen boost)
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
        "dark atmosphere — dramatic neon shadow play on feminine form, intense emotional presence, single accent neon in near-darkness, depth of shadow as character element",
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
        return f"haunted neon emotion — lonely {base_type} power, night as ally not enemy, shadow particles dense and deliberate"
    if any(w in clean for w in ["fire", "burn", "rage", "fury", "inferno", "fogo", "chama"]):
        return f"controlled fire emotion — contained {base_type} rage radiating as heat, flame particles erupting in emotional surges"
    if any(w in clean for w in ["love", "heart", "amor", "coracao", "rose", "cherry", "blossom"]):
        return f"dark romantic emotion — {base_type} longing in neon city, beautiful bittersweet mood, rose particles"
    if any(w in clean for w in ["lost", "alone", "lonely", "sozinho", "perdido", "empty"]):
        return f"beautiful isolation emotion — singular {base_type} figure in vast neon city, cinematic solitude amplifying power"
    if any(w in clean for w in ["drive", "speed", "run", "race", "corrida", "fast", "rush"]):
        return f"velocity emotion — {base_type} body mid-movement with speed blur, wind and neon trailing, pure kinetic energy"
    if any(w in clean for w in ["queen", "king", "boss", "power", "rule", "rei", "rainha", "apex"]):
        return f"dominant emotion — {base_type} god-tier aura claiming space, neon crown energy, power pose of divine right"
    if any(w in clean for w in ["blood", "sangue", "war", "guerra", "battle", "fight", "combat"]):
        return f"battle emotion — {base_type} warrior tired and powerful simultaneously, scars glowing neon, power rising from every wound"
    if any(w in clean for w in ["dream", "sonho", "sleep", "cloud", "ethereal", "heaven"]):
        return f"ethereal emotion — {base_type} figure between worlds, soft floating quality despite power level, dream-logic visual"
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
    "subtle vinyl record motif in background bokeh — the music lives in everything",
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
    "MASTERPIECE maximum quality, ultra-hyper detailed rendering, "
    "crisp professional lineart, clean correct anatomy and proportions, "
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
    "generic background, stock photo energy, corporate safe, soulless"
)

GENERATION_SUFFIX = (
    ", beautiful anime character, complete visible body in frame, "
    "detailed costume and iconic design elements fully visible, "
    "maximum neon and power lighting, "
    "clear powerful silhouette, explosive alive cyberpunk frame, "
    "professional anime art at absolute apex quality, "
    "no text, no watermark, no logo, no extra people, vertical 9:16 format"
)


# ═══════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
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
    key = f"{genre}|{filename}|{short_num}|darkmark_{VERSION}"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % (10 ** 9)


def _make_rng(genre: str, filename: str, short_num: int) -> random.Random:
    return random.Random(_make_seed(genre, filename, short_num))


def _weighted_choice(rng: random.Random, items: list, weights: list[int]):
    total = sum(weights)
    r = rng.random() * total
    acc = 0.0
    for item, weight in zip(items, weights):
        acc += weight
        if r <= acc:
            return item
    return items[0]


# ═══════════════════════════════════════════════════════════════════════
# CONTEXT BUILDER — assembles all systems into PromptContext
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

    # Determine character type
    if force_waifu or char_type == CharType.WAIFU:
        selected_type = CharType.WAIFU
    elif force_shounen or char_type == CharType.SHOUNEN:
        selected_type = CharType.SHOUNEN
    else:
        # weighted split: waifus slightly more viral for music content
        selected_type = CharType.WAIFU if rng.random() < 0.55 else CharType.SHOUNEN

    # Select character pool
    pool = WAIFU_CHARACTERS if selected_type == CharType.WAIFU else SHOUNEN_CHARACTERS
    char = rng.choice(pool)

    # Composition
    if force_back:
        comp = next(c for c in COMPOSITION_STYLES if c["name"] == "back_view_dramatic")
    elif force_full_body:
        comp = next(c for c in COMPOSITION_STYLES if c["name"] == "full_body_power")
    else:
        comp = _weighted_composition_v2(rng, selected_type)

    # Pose
    pose = _select_pose(rng, selected_type)

    # Emotion
    emotion = _weighted_emotion(rng, selected_type)

    # Visual hook
    visual_hook = _weighted_hook(rng, selected_type)

    # Palette
    if force_teal_pink:
        palette = next(p for p in PALETTES if p.name == "teal_pink")
    elif force_purple_gold:
        palette = next(p for p in PALETTES if p.name == "purple_gold")
    elif force_crimson_blue:
        palette = next(p for p in PALETTES if p.name == "crimson_blue")
    else:
        palette = _weighted_palette_v2(rng, selected_type)

    # Particle tier
    particle = _select_particle_tier(rng, selected_type)

    # Lighting
    lighting = _select_lighting(rng)

    # Background
    bg = _select_background(rng, selected_type)

    # Genre boost
    genre_boost = _get_genre_boost(mapped_genre, selected_type)

    # Song mood
    song_mood = _analyze_song_mood(song_name, selected_type)

    # Music element
    music_el = rng.choice(MUSIC_ELEMENTS)

    # Type-specific extras
    waifu_extras = _build_waifu_extras(rng) if selected_type == CharType.WAIFU else ""
    power_extras = _build_shounen_extras(rng) if selected_type == CharType.SHOUNEN else ""

    return PromptContext(
        char=char,
        composition=comp,
        pose=pose,
        emotion=emotion,
        visual_hook=visual_hook,
        palette_name=palette.name,
        palette_prompt=palette.prompt,
        particle_tier=particle,
        lighting_stack=lighting,
        background=bg,
        genre=mapped_genre,
        genre_boost=genre_boost,
        song_name=song_name,
        song_mood=song_mood,
        music_element=music_el,
        waifu_extras=waifu_extras,
        power_extras=power_extras,
    )


# ═══════════════════════════════════════════════════════════════════════
# PROMPT ASSEMBLER
# ═══════════════════════════════════════════════════════════════════════

def _assemble_prompt(ctx: PromptContext) -> str:
    char = ctx.char
    char_type = char.char_type

    # Build character block
    char_block = (
        f"character: {char.name} from {char.series}, "
        f"{char.base_description}, "
        f"signature elements: {', '.join(char.signature_elements)}, "
        f"character identity: {char.power_phrase}"
    )

    # Core character prompt by type
    core = WAIFU_CORE_CHARACTER if char_type == CharType.WAIFU else SHOUNEN_CORE_CHARACTER

    # Emotion block
    emotion_text = get_emotion_prompt(ctx.emotion, char_type)

    # Extras block
    extras = ctx.waifu_extras if char_type == CharType.WAIFU else ctx.power_extras

    # Assemble
    parts = [
        CHANNEL_IDENTITY,
        core,
        char_block,
        f"composition: {ctx.composition['prompt']}",
        f"pose: {ctx.pose}",
        emotion_text,
        f"visual hook: {ctx.visual_hook}",
        extras,
        f"{ctx.lighting_stack}",
        f"{ctx.particle_tier}",
        MOTION_LOCK,
        f"background: {ctx.background}",
        ctx.palette_prompt,
        f"genre: {ctx.genre}, atmosphere: {ctx.genre_boost}",
        f"music element: {ctx.music_element}",
        f"song title: {ctx.song_name}, mood: {ctx.song_mood}",
        THUMBNAIL_LOCK,
        STYLE_LOCK,
        QUALITY_LOCK,
        "scroll-stopping cyberpunk anime visual, "
        "perfect neon and power lighting on complete figure, "
        "jaw-dropping cinematic composition, "
        "no text, no watermark, no logo, no extra people",
    ]

    return _compact(", ".join(p.strip().strip(",") for p in parts if p.strip()), max_len=3200)


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
) -> str:
    """
    Build a complete optimized image prompt for one music visual.

    Args:
        style:              Music genre (phonk, trap, dark, darkpop, electronic, rock)
        filename:           Song filename — used for seed and mood analysis
        styles:             Additional genre tags
        short_num:          Short sequence number — varies character and effects
        char_type:          Force CharType.WAIFU or CharType.SHOUNEN (None = auto)
        force_teal_pink:    Override palette to teal+pink
        force_purple_gold:  Override palette to purple+gold
        force_crimson_blue: Override palette to crimson+blue
        force_back:         Force back-view composition
        force_full_body:    Force full-body composition
        force_waifu:        Force waifu engine
        force_shounen:      Force shounen engine

    Returns:
        Complete prompt string ready for Replicate API
    """
    ctx = _build_context(
        style=style,
        filename=filename,
        short_num=short_num,
        char_type=char_type,
        force_teal_pink=force_teal_pink,
        force_purple_gold=force_purple_gold,
        force_crimson_blue=force_crimson_blue,
        force_back=force_back,
        force_full_body=force_full_body,
        force_waifu=force_waifu,
        force_shounen=force_shounen,
    )
    return _assemble_prompt(ctx)


def build_prompt(style: str = "phonk", seed_variant: int = 0) -> tuple[str, str]:
    """Convenience wrapper that auto-generates a fake filename for seeding."""
    fake_filename = f"{style}_variant_{seed_variant}.mp3"
    prompt = build_ai_prompt(
        style=style,
        filename=fake_filename,
        styles=[style],
        short_num=seed_variant + 1,
    )
    return prompt, fake_filename


def build_waifu_prompt(style: str = "phonk", short_num: int = 1, filename: str = "song.mp3") -> str:
    """Direct waifu engine shortcut."""
    return build_ai_prompt(style=style, filename=filename, short_num=short_num, force_waifu=True)


def build_shounen_prompt(style: str = "phonk", short_num: int = 1, filename: str = "song.mp3") -> str:
    """Direct shounen engine shortcut."""
    return build_ai_prompt(style=style, filename=filename, short_num=short_num, force_shounen=True)


# ═══════════════════════════════════════════════════════════════════════
# IMAGE GENERATION (REPLICATE)
# ═══════════════════════════════════════════════════════════════════════

def generate_image(prompt: str, output_path: Optional[str] = None) -> Optional[str]:
    if not REPLICATE_API_TOKEN:
        logger.error("❌ REPLICATE_API_TOKEN not configured!")
        return None

    output_path = output_path or "temp/generated_background.png"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    full_prompt = _compact(prompt + GENERATION_SUFFIX, max_len=3500)

    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }

    for model in REPLICATE_MODELS:
        for attempt in range(1, 4):
            try:
                logger.info(f"[Replicate] Attempt {attempt}/3 — {model}")

                if "flux" in model:
                    model_input = {
                        **FLUX_PARAMS,
                        "prompt": full_prompt,
                        "negative_prompt": NEGATIVE_PROMPT,
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

                resp = requests.post(
                    f"https://api.replicate.com/v1/models/{model}/predictions",
                    headers=headers,
                    json={"input": model_input},
                    timeout=40,
                )
                resp.raise_for_status()
                pred = resp.json()

                poll_url = (
                    pred.get("urls", {}).get("get")
                    or f"https://api.replicate.com/v1/predictions/{pred['id']}"
                )

                for _ in range(120):
                    time.sleep(2.5)
                    sr = requests.get(poll_url, headers=headers, timeout=30)
                    sr.raise_for_status()
                    data = sr.json()
                    status = data.get("status")

                    if status == "succeeded":
                        output = data.get("output")
                        image_url = output[0] if isinstance(output, list) else output
                        if not image_url:
                            raise RuntimeError("Replicate returned empty output.")
                        img = requests.get(image_url, timeout=60)
                        img.raise_for_status()
                        Path(output_path).write_bytes(img.content)
                        logger.info(f"✅ Image saved: {output_path}")
                        return output_path

                    if status == "failed":
                        raise RuntimeError(data.get("error", "Unknown error"))

                logger.warning("⏳ Timeout reached")

            except Exception as e:
                logger.error(f"❌ Attempt {attempt} failed with {model}: {e}")
                time.sleep(4 * attempt)

    logger.error("❌ All attempts failed")
    return None


# ═══════════════════════════════════════════════════════════════════════
# CONVENIENCE GENERATION FUNCTIONS
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
        logger.warning(f"Background attempt {attempt}/{max_retries} failed.")
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
                style=style,
                output_path=output_path,
                seed_variant=v,
                force_waifu=force_waifu,
                force_shounen=force_shounen,
            )
            if path:
                results[style].append(path)
    return results


# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description=f"AI Image Generator — DJ DARK MARK {VERSION}"
    )
    parser.add_argument("--style",              default="phonk",
                        help="Genre: phonk, trap, electronic, dark, darkpop, rock")
    parser.add_argument("--filename",           default="dark phonk.mp3",
                        help="Song filename (affects mood and seed)")
    parser.add_argument("--short-num",          type=int, default=1,
                        help="Short number (varies seed, character, and effects)")
    parser.add_argument("--output",             default="assets/background.png")
    parser.add_argument("--waifu",              action="store_true",
                        help="Force WAIFU engine")
    parser.add_argument("--shounen",            action="store_true",
                        help="Force SHOUNEN engine")
    parser.add_argument("--force-teal-pink",    action="store_true")
    parser.add_argument("--force-purple-gold",  action="store_true")
    parser.add_argument("--force-crimson-blue", action="store_true")
    parser.add_argument("--back",               action="store_true",
                        help="Force back-view dramatic composition")
    parser.add_argument("--full-body",          action="store_true",
                        help="Force full-body composition")
    parser.add_argument("--prompt-only",        action="store_true",
                        help="Print prompt only, do not generate image")
    parser.add_argument("--list-waifus",        action="store_true",
                        help="List all waifu characters")
    parser.add_argument("--list-shounen",       action="store_true",
                        help="List all shounen characters")
    parser.add_argument("--batch",              action="store_true",
                        help="Generate batch across all genres")
    parser.add_argument("--batch-n",            type=int, default=3,
                        help="Variants per genre in batch mode")

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
            styles=genres,
            variants_per_style=args.batch_n,
            force_waifu=args.waifu,
            force_shounen=args.shounen,
        )
        for genre, paths in results.items():
            print(f"  {genre}: {len(paths)} generated")
        raise SystemExit(0)

    prompt = build_ai_prompt(
        style=args.style,
        filename=args.filename,
        styles=[args.style],
        short_num=args.short_num,
        force_teal_pink=args.force_teal_pink,
        force_purple_gold=args.force_purple_gold,
        force_crimson_blue=args.force_crimson_blue,
        force_back=args.back,
        force_full_body=getattr(args, "full_body", False),
        force_waifu=args.waifu,
        force_shounen=args.shounen,
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
        print(f"  Emotion archetypes: {len(list(EmotionArchetype))}")
        print(f"  Palettes:           {len(PALETTES)}")
        print(f"  Lighting stacks:    {len(LIGHTING_STACKS)}")
        print(f"  Genres supported:   {len(set(GENRE_MAP.values()))}")
    else:
        generate_image(prompt, args.output)
