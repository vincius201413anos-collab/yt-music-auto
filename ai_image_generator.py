"""
ai_image_generator.py — DJ DARK MARK v41.0 CYBERPUNK WAIFU EDITION
====================================================================
100 waifus nomeadas em tema cyberpunk com iluminação cinematográfica
Estilos: fofas, vilãs, trapstar, tatuadas, dark queens
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
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ======================= CONFIG =======================
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")

REPLICATE_MODELS = [
    "black-forest-labs/flux-dev",
    "cjwbw/animagine-xl-3.1",
]

FLUX_PARAMS = {
    "width": 768,
    "height": 1024,
    "num_inference_steps": 38,
    "guidance_scale": 8.0,
    "num_outputs": 1,
    "output_format": "png",
    "output_quality": 100,
    "disable_safety_checker": True,
}

# ══════════════════════════════════════════════════════════════════════
# 100 CYBERPUNK WAIFUS — v41.0 (personagens nomeadas, tema cyberpunk,
# iluminação cinematográfica, estilo variado: fofa / vilã / trapstar / tatuada)
# ══════════════════════════════════════════════════════════════════════
TREND_WAIFUS = [
    # 1-10 Sword Art Online / Naruto
    "Asuna Yuuki SAO-inspired, long chestnut hair with neon blue highlights, cyberpunk knight armor with glowing orange circuitry, warm golden rim light, elegant but dangerous",
    "Hinata Hyuga Naruto-inspired, lavender hair in loose waves, shy cute energy turned cyberpunk street medic, soft violet bioluminescent eyes, gentle neon lilac glow",
    "Rem ReZero-inspired, short sky blue hair, cyberpunk maid bodyguard, electric blue neon under-eyes, emotional intense gaze, teal rim light on face",
    "Emilia ReZero-inspired, long silver hair with icy blue streaks, cyberpunk ice sorceress, crystalline neon aura, arctic blue holographic dress, cold but warm eyes",
    "Mikasa Ackerman AOT-inspired, black hair with neon red streaks, cyberpunk soldier elite, intense focused gaze, crimson light on sharp jawline, combat-ready beauty",
    "Zero Two DITF-inspired, long pink hair with black horns glowing neon red, cyberpunk pilot queen, hot pink neon visor marks under eyes, wild confident grin",
    "Rias Gremory DxD-inspired, crimson long hair cascading, cyberpunk demon noble, deep red neon halo, regal dangerous beauty, violet and crimson lighting drama",
    "Akeno Himejima DxD-inspired, long black hair in ponytail with purple neon clips, cyberpunk thunder witch, electric violet aura crackling, seductive controlled expression",
    "Esdeath Akame-inspired, long blue-white hair, ice cold cyberpunk general, arctic neon blue military coat, commanding gaze, frost particles floating around her",
    "Akame Akame-inspired, long straight black hair, crimson eyes glowing neon, cyberpunk assassin, dark bodysuit with red circuit lines, katana silhouette behind her",

    # 11-20 Date A Live / Bunny Girl / Kaguya
    "Kurumi Tokisaki DateALive-inspired, split black-white hair, heterochromic eye one clock-gold one crimson neon, cyberpunk time spirit, gothic dark energy, clock gears floating",
    "Tohka Yatogami DateALive-inspired, long purple hair, cyberpunk spirit queen, violet neon blade energy, innocent but powerful expression, deep purple cinematic light",
    "Mai Sakurajima BunnySenpai-inspired, short dark purple hair, cyberpunk actress bunny, neon purple spotlight, elegant mysterious gaze, subtle rose holographic dress",
    "Kaguya Shinomiya-inspired, long black hair with red flower pins glowing neon, cyberpunk noble strategist, red and gold neon palace lighting, sharp intelligent eyes",
    "Chika Fujiwara-inspired, pink hair with white ribbon glowing, bubbly cyberpunk trickster, pink neon confetti aura, mischievous bright smile, soft pink bokeh",
    "Nezuko Kamado-inspired, long black hair with pink ombre neon tips, cyberpunk demon beauty, bamboo muzzle replaced by glowing pink filter mask, ember eyes glowing",
    "Shinobu Kocho-inspired, long yellow-to-lavender gradient hair, cyberpunk insect wisteria doctor, purple flower neon aura, soft deadly smile, teal butterfly particles",
    "Makima ChainsawMan-inspired, auburn hair in neat braid, cyberpunk control authority, rings of golden neon eyes floating behind her, eerie calm gaze, deep red lighting",
    "Power ChainsawMan-inspired, blonde hair with neon pink horns, chaotic cyberpunk devil, blood-red neon streaks, wild grin, high-energy messy beautiful look",
    "Himeno ChainsawMan-inspired, short white hair with eyepatch glowing neon green, cyberpunk devil hunter, cool casual confidence, teal green neon bar lighting",

    # 21-30 One Piece / Spy x Family
    "Nami OnePiece-inspired, orange wavy hair with neon gold highlights, cyberpunk navigator thief, warm amber neon light, confident sexy navigator look, holographic weather staff",
    "Nico Robin OnePiece-inspired, long black hair, cool cyberpunk archaeologist, purple neon cloak, mysterious half-smile, ancient holographic runes floating around her",
    "Boa Hancock OnePiece-inspired, long black hair with serpent neon clips, cyberpunk empress, deep magenta neon throne light, proud breathtaking beauty, snakes glowing neon",
    "Yor Forger SpyFamily-inspired, black hair with rose pin glowing red neon, cyberpunk assassin mother, elegant black bodysuit with red circuit lines, dual neon daggers",
    "Anya Forger SpyFamily-inspired, pink hair with dark tips, adorably cute cyberpunk little spy, green mind-scan neon halo, wide curious eyes, small and charming",

    # 26-30 Cyberpunk Edgerunners / Fate
    "Lucy Edgerunners-inspired, teal-white hair floating in zero-g, cyberpunk netrunner drifting in data space, electric teal aura, haunted beautiful expression, holographic data streams",
    "Rebecca Edgerunners-inspired, short two-tone blue pink hair, tiny fierce cyberpunk gunner, huge neon pink gun, explosive energy, punk attitude, neon graffiti background",
    "Saber FateSeries-inspired, gold blonde hair in braid, cyberpunk magic swordsman, emerald neon Excalibur energy, noble fierce expression, golden armor with light circuits",
    "Rin Tohsaka Fate-inspired, twin black-tied tails with red ribbon glowing, cyberpunk mage, deep crimson neon gem aura, confident tsundere energy, elegant dark look",
    "Jeanne d'Arc Fate-inspired, long silver white hair, cyberpunk holy knight, golden divine neon standard, serene powerful expression, warm holy light with cool cyber edge",

    # 31-40 Konosuba / Shield Hero / Fairy Tail
    "Megumin Konosuba-inspired, short black hair under wizard hat with neon stars, cyberpunk explosion mage, crimson eye neon, chuunibyou dramatic pose, dark energy crackling",
    "Aqua Konosuba-inspired, long blue hair with neon water droplets, cyberpunk goddess (broke one), electric blue aura, beautiful but exasperated expression, water particles",
    "Darkness Konosuba-inspired, long blonde hair, cyberpunk crusader masochist knight, blue-silver armor with neon runes, noble expression hiding wild inner energy",
    "Raphtalia ShieldHero-inspired, brown raccoon ears and long hair, cyberpunk demi-human swordmaster, warm neon amber light, determined loyal expression, fluffy tail glow",
    "Filo ShieldHero-inspired, white fluffy wings with neon tips, tiny blonde cyberpunk filolial queen, bright sky energy, cute powerful smile, white neon feather particles",
    "Erza Scarlet FairyTail-inspired, long scarlet red hair, cyberpunk requip armor knight, multiple neon armors switching, fierce battle-ready expression, red neon sparks",
    "Lucy Heartfilia FairyTail-inspired, long blonde hair with keys glowing, cyberpunk celestial spirit mage, golden star neon portal energy, cheerful brave expression",
    "Juvia Lockser FairyTail-inspired, blue hair in drills, cyberpunk water mage, deep blue neon water veil around her, intense loving expression, rain neon droplets",
    "Bulma DragonBall-inspired, short blue hair, cyberpunk genius scientist, teal holographic blueprints floating, confident brilliant expression, lab coat with neon accents",
    "Android 18 DragonBall-inspired, blonde hair tucked back, cyberpunk android warrior, cool blue neon power rings, emotionless beautiful efficiency, sleek metallic light",

    # 41-50 Dragon Ball / Naruto continued
    "Videl DragonBall-inspired, short black pigtails, cyberpunk street fighter champion, warm neon orange fight energy, determined fierce expression, black gi with circuit lines",
    "Tsunade Naruto-inspired, blonde long hair with diamond mark glowing neon, cyberpunk legendary medic, pink healing neon chakra aura, powerful commanding beauty",
    "Sakura Haruno Naruto-inspired, short pink hair, cyberpunk medic fighter, pink and green dual neon, focused intense expression, fist charged with glowing energy",
    "Ino Yamanaka Naruto-inspired, long platinum blonde hair, cyberpunk mind transfer specialist, mind-violet neon wave aura, confident fashionable street look",
    "Temari Naruto-inspired, four blonde pigtails, cyberpunk wind kunoichi, teal wind neon slashes, serious powerful expression, giant holographic fan behind her",
    "Yoruichi Shihouin Bleach-inspired, dark skin short purple hair, cyberpunk flash goddess, golden speed neon trails, playful grin hiding terrifying power, cat ears optional",
    "Rukia Kuchiki Bleach-inspired, short black hair, cyberpunk soul reaper artist, white and violet neon zanpakuto energy, calm cute but deadly expression, ice flowers",
    "Orihime Inoue Bleach-inspired, long auburn hair with hairpins glowing orange, cyberpunk barrier healer, warm orange neon shields floating, gentle kind beautiful face",
    "Rangiku Matsumoto Bleach-inspired, long wavy strawberry blonde hair, cyberpunk soul reaper vice captain, sakura petal neon storm, laid-back but fierce expression",
    "Nelliel Bleach-inspired, green hair with horned helmet glowing neon, cyberpunk espada, teal green powerful neon energy, mature elegant warrior expression",

    # 51-60 My Hero Academia
    "Momo Yaoyorozu MHA-inspired, long black hair tied high, cyberpunk creation hero, neon white material manifesting from skin, intelligent elegant serious expression",
    "Ochaco Uraraka MHA-inspired, short brown hair, cute cyberpunk gravity hero, pink anti-gravity neon orbs floating around her, cheerful determined round eyes",
    "Himiko Toga MHA-inspired, blonde twin buns, cyberpunk blood copy villain, yellow-gold feral neon eyes, psycho cute smile, syringes glowing neon, pink blood splash art",
    "Midnight MHA-inspired, long black with white streak hair, cyberpunk sleep hero, purple dream neon mist curling from wrists, confident sultry heroic expression",
    "Mirko MHA-inspired, white rabbit ears and hair, cyberpunk rabbit hero, powerful athletic body, moon silver neon light, fierce battle grin, kick energy trails",

    # 56-60 Jujutsu Kaisen
    "Nobara Kugisaki JJK-inspired, orange-brown bob hair, cyberpunk straw doll shaman, dark neon ritual energy, fierce blunt attitude expression, glowing hammer and nails",
    "Maki Zenin JJK-inspired, short dark hair with glasses glowing neon green, cyberpunk sorcery weapon master, jade neon weapon aura, sharp intense warrior gaze",
    "Mei Mei JJK-inspired, long blonde twin-braid, cyberpunk mercenary shaman, gold neon aura of greed and power, cool calculated expression, crows with neon eyes",
    "Utahime Iori JJK-inspired, long dark hair with scar glowing faint, cyberpunk chant barrier sorcerer, warm violet neon song wave aura, composed strong expression",
    "Shoko Ieiri JJK-inspired, short dark hair, cyberpunk reverse curse doctor, green healing neon hands, calm unfazed expression, medical holographic displays",

    # 61-70 Slice of life / Steins Gate
    "Marin Kitagawa-inspired, long wavy blonde hair with pink highlights, cyberpunk cosplay idol, vibrant neon fabric aura, enthusiastic passionate expression, shimmer particles",
    "Shizuku Kuroe-inspired, short black bob hair, quiet cyberpunk doll artist, dark indigo neon, calm mysterious expression, small glowing doll figures around her",
    "Nagatoro-inspired, tanned skin long black hair, cyberpunk teaser gremlin, sharp neon green eyes grinning, playful aggressive beautiful energy, urban street setting",
    "Uzaki Hana-inspired, short silver-white hair, energetic cyberpunk loud friend, bright neon yellow energy, wide grin, bubbly overwhelming cute presence",
    "Komi Shouko-inspired, long black hair with violet sheen, cyberpunk silent communication goddess, soft violet neon letter particles floating, shy stunning beauty",
    "Najimi Osana-inspired, short orange wavy hair, chaotic neutral cyberpunk social butterfly, rainbow neon aura, unpredictable cheerful expression, everyone's friend energy",
    "Yuno Gasai FutureDiary-inspired, long pink hair, yandere cyberpunk time survival queen, pink-red cracked neon eyes, loving and terrifying duality expression, diary glowing",
    "Kurisu Makise SteinsGate-inspired, long reddish-brown hair, cyberpunk time machine scientist, teal data neon streams, intelligent sarcastic brilliant expression",
    "Mayuri Shiina SteinsGate-inspired, short black hair, sweetest cyberpunk lab member, warm amber neon, soft innocent smile that hides cosmic importance, stars around her",
    "Suzuha Amane SteinsGate-inspired, brown hair under military cap, cyberpunk time soldier from future, cool determined expression, green neon timeline energy",

    # 71-80 Violet Evergarden / Fate / Code Geass
    "Violet Evergarden-inspired, long golden blonde hair, cyberpunk auto memory doll with prosthetic neon arms, violet letter neon paper floating, melancholic beautiful expression",
    "Saber Alter Fate-inspired, dark grey armored Artoria, dark energy Excalibur glowing black-violet neon, intimidating dark beauty, corrupted but powerful expression",
    "Astolfo Fate-inspired, long pink hair and cute face, cyberpunk paladin trap, pink-gold neon lance, bright cheerful beautiful expression, flamboyant heroic aura",
    "Illyasviel Fate-inspired, long white hair with ruby eyes, cyberpunk magical girl dark, crimson neon magic circle, cute child face hiding immense power, snow flakes neon",
    "Kallen Kozuki CodeGeass-inspired, red hair in wild cyberpunk resistance queen look, Knightmare neon red cockpit light, fierce passionate rebel expression, red neon streaks",
    "CC CodeGeass-inspired, long green hair, mysterious cyberpunk witch immortal, jade green neon code mark on forehead, eternal bored beautiful expression, gold markings glow",
    "Shirley Fenette CodeGeass-inspired, long orange hair, sweet cyberpunk student caught in war, warm sunset neon, emotional loving expression, innocence in dark world",
    "Milly Ashford CodeGeass-inspired, short blonde hair, cyberpunk student council president, gold neon festive energy, bright organizing chaos energy, cheerful commanding look",
    "Winry Rockbell FMA-inspired, long blonde hair in ponytail with wrench glowing, cyberpunk automail engineer, warm amber neon sparks, passionate loving expression",
    "Riza Hawkeye FMA-inspired, pulled back blonde hair, cyberpunk military sharpshooter, golden scope neon sight, cool composed absolute loyalty expression, guns gleaming",

    # 81-90 FMA / Spice Wolf / Toradora / Oregairu
    "Lust FMA-inspired, long black hair, ultimate cyberpunk homunculus femme fatale, dark crimson neon Ouroboros mark, fingernails extending glowing, deadly seductive expression",
    "Olivier Armstrong FMA-inspired, blonde hair in military braid, cyberpunk northern wall general, ice blue neon blade, fearless absolute commander expression, frost aura",
    "Holo SpiceWolf-inspired, long brown hair with wolf ears and tail glowing neon amber, cyberpunk ancient wolf goddess, warm harvest neon, wise playful beautiful expression",
    "Taiga Aisaka Toradora-inspired, long brown hair, tiny cyberpunk palm-top tiger, fierce neon orange energy, tsundere fierce cute expression, wooden sword glowing",
    "Minori Kushieda Toradora-inspired, short orange hair, energetic cyberpunk softball girl, bright warm neon sun energy, enthusiastic honest beautiful smile",
    "Ami Kawashima Toradora-inspired, long blonde wavy hair, cyberpunk model manipulator, cool icy blue neon, dual face sweet-then-sharp, elegant calculating gaze",
    "Yukino Yukinoshita Oregairu-inspired, long black hair with blue sheen, cyberpunk service club perfectionist, cool silver-blue neon, elegant cold intellectual expression",
    "Yui Yuigahama Oregairu-inspired, pink dip-dyed short hair, cyberpunk cheerful social butterfly, warm coral neon, kind expressive emotional face, ribbon glowing",
    "Iroha Isshiki Oregairu-inspired, brown hair in side ponytail glowing, cyberpunk cunning student president, soft pink neon, sly cute devious smile hiding sharp mind",
    "Ichika Nakano Quint-inspired, long blonde hair with star clips glowing neon, cyberpunk big sister, soft gold neon, gentle responsible beautiful expression",

    # 91-100 Quintuplets / Re:Zero
    "Nino Nakano Quint-inspired, long blonde twin pigtails, tsundere cyberpunk cook, warm rose neon, fierce protective sister expression, kitchen holographic tools glowing",
    "Miku Nakano Quint-inspired, long blonde hair with headphones glowing neon deep blue, cyberpunk history music lover, indigo neon, shy reserved beautiful intensity",
    "Yotsuba Nakano Quint-inspired, short blonde hair with bow glowing neon green, most cheerful cyberpunk sister, bright lime neon energy, pure bright energetic smile",
    "Itsuki Nakano Quint-inspired, long blonde hair with star clips, serious cyberpunk teacher sister, gold neon warm lighting, composed studious beautiful expression",
    "Echidna ReZero-inspired, long white hair with black streaks, cyberpunk witch of greed, dark void neon tea party aesthetic, eerily beautiful smile hiding evil, bone china glow",
    "Satella ReZero-inspired, silver half-shadow half-radiant hair, cyberpunk witch of envy, black and violet neon shadow hands, deeply emotional tragic expression, stars crying",
    "Frederica Baumann ReZero-inspired, long golden hair with beast eyes neon slit, cyberpunk half-beast gate guardian, warm neon amber, elegant composed dangerous grin",
    "Elsa Granhiert ReZero-inspired, dark hair with red neon streaks, cyberpunk bowel hunter assassin, crimson neon blades, sadistic beautiful smile, blood-art aesthetic clean",
    "Ram ReZero-inspired, short pink hair with demon horn glowing bright neon pink, cyberpunk elite maid demon, sharp condescending beauty, pink energy cracking around her",
    "Priscilla Barielle ReZero-inspired, long scarlet red hair, cyberpunk solar empress, golden solar neon crown aura, absolute arrogant gorgeous expression, sun deity energy",
]

# ══════════════════════════════════════════════════════════════════════
# LOCKS DE QUALIDADE / COMPOSIÇÃO / ESTILO — CYBERPUNK EDITION
# ══════════════════════════════════════════════════════════════════════
CHANNEL_IDENTITY = (
    "DJ Dark Mark viral trap phonk anime visual, premium cyberpunk anime key visual, "
    "adult extremely beautiful woman, 20+, scroll-stopping YouTube Shorts first frame, "
    "cyberpunk neon world aesthetic"
)

CORE_CHARACTER = (
    "one adult anime woman, clearly adult, mature proportions, "
    "beautiful waifu character, expressive face, hypnotic eyes, "
    "magnetic emotional presence, strong visual identity, "
    "alone, single character, no other people, no text"
)

COMPOSITION_LOCK = (
    "vertical 9:16 mobile-first composition, "
    "face and upper body dominant, eyes in upper third, "
    "character large in frame, readable at tiny phone size, "
    "clean cyberpunk background, strong silhouette, clear focal point, "
    "opening frame for YouTube Shorts, designed to stop scrolling immediately"
)

STYLE_LOCK = (
    "premium cyberpunk anime key visual, clean sharp lineart, "
    "high-end 2D anime illustration, polished cel shading, "
    "cinematic neon lighting, glossy detailed eyes, detailed hair, "
    "rich neon colors, high contrast, professional music cover art quality, "
    "not photorealistic, not 3d render, anime art style"
)

CYBERPUNK_LIGHTING = (
    "cinematic cyberpunk lighting setup: strong colored rim light from behind, "
    "contrasting fill light from front, neon reflections on skin, "
    "volumetric light rays, neon-lit atmosphere, "
    "beautiful dramatic face illumination, eyes catching neon glow, "
    "professional key visual lighting quality"
)

MOTION_LOCK = (
    "alive frame, subtle sense of motion, hair moving in wind, "
    "floating neon particles and light specks, cinematic depth of field, "
    "glowing energy in the air, dynamic but not cluttered, "
    "neon bokeh in background"
)

VIRAL_HOOK_LOCK = (
    "one strong visual hook: glowing neon tear OR intense neon eye reflection OR "
    "dramatic face neon light split OR hair blown by cyber wind OR "
    "small power aura around character, "
    "instantly recognizable visual moment, memorable cyberpunk frame"
)

QUALITY_LOCK = (
    "masterpiece, best quality, ultra detailed, crisp lineart, "
    "beautiful face, detailed shining neon-lit eyes, clean anatomy, "
    "professional channel branding, high resolution, premium finish, "
    "beautiful illumination, stunning visual quality"
)

# ══════════════════════════════════════════════════════════════════════
# PALETAS CYBERPUNK
# ══════════════════════════════════════════════════════════════════════
PALETTE_TEAL_PINK = (
    "dominant teal and hot pink cyberpunk palette, deep navy shadows, "
    "teal and magenta neon split lighting, cool-warm contrast, "
    "classic cyberpunk color duality, electric atmosphere"
)
PALETTE_PURPLE_GOLD = (
    "dominant deep purple and gold cyberpunk palette, "
    "violet shadows with golden neon highlights, "
    "luxurious dark cyberpunk royalty mood, rich high contrast"
)
PALETTE_CRIMSON_BLUE = (
    "dominant crimson and electric blue cyberpunk palette, "
    "dark dramatic shadows, blood-red and sapphire neon contrast, "
    "intense phonk cyberpunk energy, dangerous beautiful mood"
)
PALETTE_GREEN_ORANGE = (
    "dominant toxic green and amber cyberpunk palette, "
    "dark background, bio-neon green accents, warm orange rim light, "
    "edgy hacker aesthetic, high contrast neon pop"
)
PALETTE_WHITE_BLUE = (
    "dominant ice white and electric blue cyberpunk palette, "
    "cold clean atmosphere, frost and neon blue contrast, "
    "elegant cyberpunk winter aesthetic, crisp and cinematic"
)

PALETTES = [
    ("teal_pink",    PALETTE_TEAL_PINK,    30),
    ("purple_gold",  PALETTE_PURPLE_GOLD,  25),
    ("crimson_blue", PALETTE_CRIMSON_BLUE, 20),
    ("green_orange", PALETTE_GREEN_ORANGE, 15),
    ("white_blue",   PALETTE_WHITE_BLUE,   10),
]

# ══════════════════════════════════════════════════════════════════════
# GÊNEROS
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

GENRE_BOOSTS = {
    "phonk":      "phonk cyberpunk atmosphere, heavy 808 bass visual energy, dark neon street feeling, aggressive clean cyberpunk aesthetic",
    "trap":       "trap cyberpunk atmosphere, urban night neon energy, stylish confidence, warm neon street premium aesthetic",
    "electronic": "electronic cyberpunk atmosphere, futuristic digital energy, teal data streams, clean cyber rhythm visual",
    "darkpop":    "dark pop cyberpunk emotional atmosphere, romantic sadness in neon city, cinematic beauty, warm-cold color story",
    "dark":       "dark cyberpunk atmosphere, dramatic neon shadows, intense emotional presence, single accent neon color in darkness",
    "rock":       "rock cyberpunk energy, electric concert neon, raw emotional power, dramatic rim neon lighting, stage energy",
    "default":    "dark cyberpunk atmosphere, emotional anime beauty, cinematic neon contrast, premium viral Shorts visual",
}

# ══════════════════════════════════════════════════════════════════════
# FACE HOOKS e BACKGROUNDS CYBERPUNK
# ══════════════════════════════════════════════════════════════════════
FACE_HOOKS = [
    "hypnotic direct eye contact, neon reflected in pupils, viewer feels watched",
    "one glowing neon tear trailing down cheek catching colored light",
    "eyes reflecting cyberpunk city skyline and holographic displays",
    "slight dangerous confident smile with deep emotional neon-lit eyes",
    "wide luminous eyes with neon catchlights, lips slightly parted",
    "half-lidded powerful gaze, magnetic cyberpunk calm",
    "vulnerable melancholic stare bathed in cold neon, beautiful sadness",
    "subtle intensity in expression, beautiful and controlled power",
    "dreamy upward gaze as neon lights drift past her face",
    "sharp cyberpunk queen stare, absolute confidence, commanding presence",
]

BACKGROUND_VARIATIONS = [
    "rainy cyberpunk neon city street, wet neon reflections, teal and pink bokeh",
    "cyberpunk rooftop at golden hour with neon city sprawl far below",
    "dark holographic data center with glowing server rows behind her",
    "cyberpunk alley with blurred neon kanji signs, rain mist, depth",
    "night cyberpunk skyline with flying vehicles and neon advertisements",
    "underground neon club with laser beams and smoke, dark and vibrant",
    "cyberpunk laboratory with holographic screens and blue light",
    "dark concert stage with neon light beams, smoke machine, music energy",
    "void black with single strong neon rim light and floating data particles",
    "cyberpunk market street, neon vendor signs, warm amber and teal mix",
]

MUSIC_ELEMENTS = [
    "sleek cyberpunk headphones around neck glowing neon",
    "one wireless neon earbud, immersed in the music",
    "small holographic music waveform behind character, subtle",
    "cyberpunk microphone silhouette blurred in background neon",
    "neon music visualizer particles around her, tasteful amount",
    "no music prop, emotion carries the music energy",
    "no music prop, pure cinematic cyberpunk anime portrait",
]

# ══════════════════════════════════════════════════════════════════════
# NEGATIVE PROMPT
# ══════════════════════════════════════════════════════════════════════
NEGATIVE_PROMPT = (
    "ugly, bad anatomy, bad face, distorted face, asymmetrical eyes, "
    "bad hands, extra fingers, missing fingers, fused limbs, broken body, "
    "long neck, disfigured, mutated, melted face, uncanny valley, "
    "blurry, low quality, jpeg artifacts, heavy noise, flat boring image, "
    "photorealistic, real person, 3d render, CGI, doll, plastic skin, "
    "western cartoon, simple cartoon, childish style, "
    "child, underage, loli, young girl, schoolgirl, baby face, "
    "nude, explicit nudity, nipples, genitalia, sexual act, pornographic, "
    "multiple people, crowd, two girls, duplicate character, "
    "text, words, logo, watermark, signature, letters, numbers, "
    "too dark to see face, face too small, full body tiny, "
    "cluttered background, excessive neon overload, "
    "overexposed bloom, muddy colors, washed out, desaturated, "
    "messy composition, no focal point, bad eyes, dead eyes, "
    "low contrast, boring lighting, flat lighting, no neon, dull colors"
)

GENERATION_SUFFIX = (
    ", beautiful expressive adult anime face, eyes readable at small size, "
    "first frame optimized for Shorts feed, high contrast neon lighting, "
    "clear silhouette, alive cinematic cyberpunk frame, motion feeling, "
    "polished anime art, gorgeous illumination, "
    "no text, no logo, no watermark, no extra people"
)

# ══════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════
def _compact(text: str, max_len: int = 3000) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace(" ,", ",").replace(",,", ",")
    return text[:max_len].rstrip(" ,")


def _clean_song_name(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(r"[_\-]+", " ", name)
    return name.strip()


def _seed(style: str, filename: str, short_num: int) -> int:
    key = f"{style}|{filename}|{short_num}|darkmark_v41.0_cyberpunk"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % (10**9)


def _rng(style: str, filename: str, short_num: int) -> random.Random:
    return random.Random(_seed(style, filename, short_num))


def _weighted_palette(rng: random.Random) -> tuple[str, str]:
    total = sum(w for _, _, w in PALETTES)
    r = rng.random() * total
    acc = 0
    for name, palette, weight in PALETTES:
        acc += weight
        if r <= acc:
            return name, palette
    return PALETTES[0][0], PALETTES[0][1]


def _song_mood_boost(song_name: str) -> str:
    clean = song_name.lower()
    if any(w in clean for w in ["dark", "shadow", "ghost", "night", "madrugada", "noite"]):
        return "haunted neon night emotion, lonely but powerful, neon eyes carrying darkness"
    if any(w in clean for w in ["fire", "burn", "rage", "fury", "angry"]):
        return "intense cyberpunk fire emotion, contained rage, electric passionate stare"
    if any(w in clean for w in ["love", "heart", "amor", "coracao", "rose", "cherry"]):
        return "dark cyberpunk romantic emotion, longing neon eyes, beautiful bittersweet mood"
    if any(w in clean for w in ["lost", "alone", "lonely", "sozinho", "perdido"]):
        return "deep lonely cyberpunk emotion, quiet neon sadness, isolated cinematic feeling"
    if any(w in clean for w in ["drive", "speed", "run", "race", "corrida"]):
        return "cyberpunk speed motion energy, focused eyes, wind and neon blur feeling"
    if any(w in clean for w in ["queen", "king", "boss", "power", "rule"]):
        return "dominant cyberpunk queen aura, neon crown energy, commanding powerful stare"
    if any(w in clean for w in ["dream", "sonho", "sleep", "cloud"]):
        return "dreamy floating cyberpunk emotion, soft holographic atmosphere, ethereal neon eyes"
    return "emotion matching the music, cyberpunk magnetic presence, cinematic neon feeling"


# ══════════════════════════════════════════════════════════════════════
# PROMPT PRINCIPAL — v41.0 CYBERPUNK WAIFU EDITION
# ══════════════════════════════════════════════════════════════════════
def build_ai_prompt(
    style: str = "phonk",
    filename: str = "song.mp3",
    styles: Optional[list] = None,
    short_num: int = 1,
    force_teal_pink: bool = False,
    force_purple_gold: bool = False,
    force_crimson_blue: bool = False,
    force_back: bool = False,
) -> str:
    styles = styles or []
    mapped = GENRE_MAP.get((style or "default").lower().strip(), "default")
    rng = _rng(mapped, filename, short_num)
    song_name = _clean_song_name(filename)

    # Seleciona waifu aleatória das 100 personagens
    char = rng.choice(TREND_WAIFUS)

    # Vista de costas
    back_view = (
        "dramatic back view with strong neon rim light splitting colors, "
        "long flowing hair glowing with neon, mysterious cyberpunk silhouette, side profile slightly visible, "
        if force_back else ""
    )

    # Face hook e elementos visuais
    face_hook = rng.choice(FACE_HOOKS)
    background = rng.choice(BACKGROUND_VARIATIONS)
    music_element = rng.choice(MUSIC_ELEMENTS)
    song_mood = _song_mood_boost(song_name)

    # Paleta
    if force_teal_pink:
        palette_name, palette = "teal_pink", PALETTE_TEAL_PINK
    elif force_purple_gold:
        palette_name, palette = "purple_gold", PALETTE_PURPLE_GOLD
    elif force_crimson_blue:
        palette_name, palette = "crimson_blue", PALETTE_CRIMSON_BLUE
    else:
        palette_name, palette = _weighted_palette(rng)

    genre_text = ", ".join([style] + [s for s in styles if s and s != style])
    genre_boost = GENRE_BOOSTS.get(mapped, GENRE_BOOSTS["default"])

    prompt = (
        f"{CHANNEL_IDENTITY}, "
        f"{CORE_CHARACTER}, "
        f"character inspiration: {char}, "
        f"{back_view}"
        f"face hook: {face_hook}, "
        f"{VIRAL_HOOK_LOCK}, "
        f"music element: {music_element}, "
        f"{COMPOSITION_LOCK}, "
        f"{CYBERPUNK_LIGHTING}, "
        f"{MOTION_LOCK}, "
        f"background: {background}, "
        f"dominant palette: {palette_name}, {palette}, "
        f"genre atmosphere: {genre_boost}, "
        f"genre: {genre_text}, "
        f"song title mood: {song_name}, "
        f"song emotion: {song_mood}, "
        f"{STYLE_LOCK}, "
        f"{QUALITY_LOCK}, "
        "opening frame for viral music Short, "
        "beautiful adult cyberpunk anime waifu, emotional, trendy, memorable, "
        "stunning neon illumination, gorgeous cinematic quality, "
        "no text, no watermark, no logo"
    )

    return _compact(prompt, max_len=3000)


def build_prompt(style: str = "phonk", seed_variant: int = 0) -> tuple[str, str]:
    fake_filename = f"{style}_variant_{seed_variant}.mp3"
    prompt = build_ai_prompt(
        style=style,
        filename=fake_filename,
        styles=[style],
        short_num=seed_variant + 1,
    )
    return prompt, fake_filename


# ══════════════════════════════════════════════════════════════════════
# GERAÇÃO DE IMAGEM (REPLICATE)
# ══════════════════════════════════════════════════════════════════════
def generate_image(prompt: str, output_path: Optional[str] = None) -> Optional[str]:
    if not REPLICATE_API_TOKEN:
        logger.error("❌ REPLICATE_API_TOKEN não configurado!")
        return None

    output_path = output_path or "temp/generated_background.png"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    full_prompt = _compact(prompt + GENERATION_SUFFIX, max_len=3300)

    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }

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
                resp = requests.post(
                    f"https://api.replicate.com/v1/models/{model}/predictions",
                    headers=headers,
                    json=payload,
                    timeout=40,
                )
                resp.raise_for_status()
                pred = resp.json()

                poll_url = (
                    pred.get("urls", {}).get("get")
                    or f"https://api.replicate.com/v1/predictions/{pred['id']}"
                )

                for _ in range(90):
                    time.sleep(2.5)
                    sr = requests.get(poll_url, headers=headers, timeout=30)
                    sr.raise_for_status()
                    data = sr.json()
                    status = data.get("status")

                    if status == "succeeded":
                        output = data.get("output")
                        image_url = output[0] if isinstance(output, list) else output
                        if not image_url:
                            raise RuntimeError("Replicate retornou output vazio.")
                        img = requests.get(image_url, timeout=60)
                        img.raise_for_status()
                        Path(output_path).write_bytes(img.content)
                        logger.info(f"✅ Imagem salva: {output_path}")
                        return output_path

                    if status == "failed":
                        raise RuntimeError(data.get("error", "Unknown error"))

                logger.warning("⏳ Timeout atingido")

            except Exception as e:
                logger.error(f"❌ Falha tentativa {attempt} com {model}: {e}")
                time.sleep(4)

    logger.error("❌ Todas as tentativas falharam")
    return None


# ══════════════════════════════════════════════════════════════════════
# FUNÇÕES DE CONVENIÊNCIA
# ══════════════════════════════════════════════════════════════════════
def generate_background_image(
    style: str = "phonk",
    output_path: str = "assets/background.png",
    seed_variant: int = 0,
    max_retries: int = 3,
    force_teal_pink: bool = False,
    force_purple_gold: bool = False,
    force_crimson_blue: bool = False,
    force_back: bool = False,
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
    )
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
) -> Optional[str]:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    existing = list(Path(output_dir).glob(f"{style}_bg_*.png"))
    if existing:
        return str(random.choice(existing))
    variant = random.randint(0, 99)
    output_path = str(Path(output_dir) / f"{style}_bg_{variant:02d}.png")
    return generate_background_image(style=style, output_path=output_path, seed_variant=variant)


def generate_background_batch(
    styles: list,
    output_dir: str = "assets/backgrounds",
    variants_per_style: int = 3,
) -> dict:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    results: dict = {}
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
        description="AI Image Generator — DJ DARK MARK v41.0 Cyberpunk Waifu Edition"
    )
    parser.add_argument("--style",            default="phonk",
                        help="Gênero: phonk, trap, electronic, dark, darkpop, rock")
    parser.add_argument("--filename",         default="dark phonk.mp3",
                        help="Nome da música (muda o mood do prompt)")
    parser.add_argument("--short-num",        type=int, default=1,
                        help="Número do short (varia seed e waifu)")
    parser.add_argument("--output",           default="assets/background.png")
    parser.add_argument("--force-teal-pink",  action="store_true",
                        help="Força paleta teal + pink")
    parser.add_argument("--force-purple-gold",action="store_true",
                        help="Força paleta purple + gold")
    parser.add_argument("--force-crimson-blue",action="store_true",
                        help="Força paleta crimson + blue")
    parser.add_argument("--back",             action="store_true",
                        help="Força vista de costas neon")
    parser.add_argument("--prompt-only",      action="store_true",
                        help="Só imprime o prompt, não gera imagem")
    args = parser.parse_args()

    prompt = build_ai_prompt(
        style=args.style,
        filename=args.filename,
        styles=[args.style],
        short_num=args.short_num,
        force_teal_pink=args.force_teal_pink,
        force_purple_gold=args.force_purple_gold,
        force_crimson_blue=args.force_crimson_blue,
        force_back=args.back,
    )

    if args.prompt_only:
        print("=== PROMPT v41.0 CYBERPUNK ===")
        print(prompt)
        print("\n=== NEGATIVE PROMPT ===")
        print(NEGATIVE_PROMPT)
    else:
        generate_image(prompt, args.output)
