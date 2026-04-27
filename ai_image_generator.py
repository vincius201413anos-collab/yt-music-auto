"""
ai_image_generator.py — DJ DARK MARK v42.0 CYBERPUNK WAIFU EDITION
====================================================================
100 waifus nomeadas em tema cyberpunk com iluminação cinematográfica
Composições variadas: corpo inteiro, 3/4, poses dinâmicas, vista de costas
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
# 100 CYBERPUNK WAIFUS — v42.0
# Personagens fiéis ao design original + upgrade cyberpunk
# Descrições detalhadas de roupa, cabelo, traços característicos
# ══════════════════════════════════════════════════════════════════════
TREND_WAIFUS = [
    # 1-10 Sword Art Online / Naruto / ReZero
    "Asuna Yuuki SAO, iconic chestnut waist-length hair, white-and-red KoB armor redesigned as cyberpunk plate with glowing orange circuitry seams, rapier sheathed glowing electric blue, tall elegant female warrior stance, graceful and lethal",
    "Hinata Hyuga Naruto, trademark lavender-white eyes with no pupils glowing faint violet, dark blue hair framing soft face, cyberpunk kunoichi bodysuit with byakugan neon scan lines, shy power held back, gentle but devastating",
    "Rem ReZero, iconic short blue hair with hair clip, maid uniform reimagined as armored cyberpunk bodyguard suit with teal neon trim, morning star weapon crackling electricity, intense tear-filled determination, devotion and power",
    "Emilia ReZero, long silver hair half-tied with white flowers, pointed ears, cyberpunk ice sorceress coat with crystalline blue circuits, ice shards floating around hands, serene face hiding tremendous power, ethereal cold beauty",
    "Mikasa Ackerman AOT, trademark black hair and red scarf now glowing crimson neon, Survey Corps jacket redesigned with ODM gear as cyberpunk harness, blades replaced by energy katanas, sharp jawline, absolute focused determination",
    "Zero Two DITF, long pink hair with iconic black horns now glowing red neon, pilot suit redesigned as skintight cyberpunk jumpsuit with candy-pink circuits, horns real and radiant, wild confident grin, chaotic beautiful energy",
    "Rias Gremory DxD, floor-length crimson hair cascading dramatically, cyberpunk demon noble coat with deep red power aura venting from hands, confident imperious posture, violet eyes gleaming, aristocratic beauty commanding space",
    "Akeno Himejima DxD, very long black hair in iconic high ponytail, shrine maiden robe redesigned as cyberpunk thunder witch outfit with violet lightning arcing between fingers, soft smile hiding ruthless power",
    "Esdeath Akame-inspired, waist-length silver-blue hair, military peaked cap with neon blue insignia, tight general uniform with ice crystal epaulettes, glowing blue tattoo on chest, frost breath visible, absolute commanding presence",
    "Akame Akame ga Kill, iconic waist-length straight black hair, crimson eyes glowing, black tight combat suit with glowing red circuit veins, Murasame katana crackling dark neon energy, silent assassin coiled to strike",

    # 11-20 Date A Live / Bunny Girl / Kaguya
    "Kurumi Tokisaki DateALive, iconic half black half white long hair, one clockwork golden eye and one crimson eye, gothic lolita dress redesigned as cyberpunk time spirit armor with clock gear motifs glowing, twin flintlocks dripping shadow",
    "Tohka Yatogami DateALive, long dark purple hair, Spirit dress reimagined as flowing cyberpunk armor with violet neon energy wings, Sandalphon sword crackling purple lightning, innocent expression contrasting godlike power",
    "Mai Sakurajima BunnySenpai, signature short dark hair, iconic bunny outfit redesigned in cyberpunk leather and neon pink accents, mysterious actress aura, purple spotlight on her, elegant crossed arms, sharp knowing gaze",
    "Kaguya Shinomiya, impossibly long black hair with ornate kanzashi pins glowing red neon, cyberpunk noble strategist in dark kimono with gold circuit obi, fan held open with holographic data, sharp manipulative intelligence",
    "Chika Fujiwara, bright pink hair with iconic white bow now glowing, cyberpunk idol trickster in pastel-dark outfit with surprise neon confetti explosions, mischievous wide grin, chaotic cute energy, dance pose mid-step",
    "Nezuko Kamado, long black hair with pink ombre neon glow at tips, bamboo muzzle replaced by glowing pink filter mask, pink haori with hemp leaf pattern illuminated, demon form with cracked pink neon skin marks glowing, fierce and haunting",
    "Shinobu Kocho, long hair shifting from yellow to lavender, iconic butterfly haori with wings as real cyberpunk light constructs, doctor bag glowing with vials, needle-thin sword crackling insect venom neon, soft deadly smile",
    "Makima ChainsawMan, neat auburn hair in iconic low braid, white dress shirt and tie as cyberpunk control authority uniform, rings of concentric glowing eyes floating behind her like halos, leash chain glowing gold, eerie perfect calm",
    "Power ChainsawMan, wild blonde hair with iconic neon pink curved horns, casual streetwear soaked in neon blood-red energy, huge chainsaw arm deployed crackling, feral gap-tooth grin, chaotic devil energy barely contained",
    "Himeno ChainsawMan, short white hair with eyepatch now a glowing green neon device, casual cyberpunk devil hunter jacket, ghost hand jutting beside her translucent, calm cool cigarette between lips, effortless dangerous confidence",

    # 21-30 One Piece / Spy x Family
    "Nami OnePiece, shoulder-length orange hair, iconic Clima-Tact upgraded as cyberpunk weather staff with lightning orbs, bikini top and jeans redesigned as navigator's cyberpunk gear with neon amber accents, confident hand on hip, navigator queen",
    "Nico Robin OnePiece, long straight black hair, cyberpunk archaeologist in dark trench coat, hundred stone hands emerging from shadows in bloom, mysterious half-smile, Ohara holographic ruins behind her, cool intellectual power",
    "Boa Hancock OnePiece, floor-length black hair with iconic Kuja crown now neon, snake earrings glowing, revealing empress dress as cyberpunk authority gown, Love-Love beam hand pose, breathtaking arrogant beauty, snakes coiling around legs glowing",
    "Yor Forger SpyFamily, black hair with rose hairpin glowing blood-red, thorn-covered crimson dress redesigned as cyberpunk assassin armor, twin needles crackling with red neon energy, gentle smile hiding terrifying speed and strength",
    "Anya Forger SpyFamily, signature pink hair with dark tips, wide curious mind-reading green halo flickering, spy outfit way too big for tiny frame, iconic excited face with mouth agape, adorably small amid big neon spy world",

    # 26-30 Cyberpunk Edgerunners / Fate
    "Lucy Edgerunners, teal-white hair floating weightless in cyberspace, pale skin with glowing neural ports, arms outstretched in data ocean, expression between bliss and breakdown, electric teal data streams curling around body like wings",
    "Rebecca Edgerunners, tiny frame with big attitude, two-tone blue-pink pigtails, oversized cyberpunk jacket sliding off shoulder, enormous Guts shotgun dragging on ground, standing wide-legged grinning wildly, punk energy in every pixel",
    "Saber Artoria FateSeries, iconic golden hair in tight braid, emerald green eyes, blue and gold plate armor crackling with Excalibur wind aura, sword raised with divine golden wind, noble resolute expression, heroic king energy",
    "Rin Tohsaka Fate, twin black pigtails with signature red ribbon bows glowing, black turtleneck and red skirt as cyberpunk mage combat outfit, twin glowing jewel gems charged with massive mana, tsundere determined fierce expression",
    "Jeanne d'Arc Fate, very long silver-white hair streaming behind, holy armor with divine neon gold circuits, standard banner crackling with sacred flame, serene determined expression of absolute faith, light and shadow split dramatically",

    # 31-40 Konosuba / Shield Hero / Fairy Tail
    "Megumin Konosuba, iconic short black hair under oversized wizard hat with neon star, red eyes glowing, tattered black cape, staff raised toward sky, single eye closed in EXPLOSION chant, dark energy erupting beneath her tiny dramatic frame",
    "Aqua Konosuba, very long blue hair in iconic high ponytail with bead ornaments, blue and white shrine outfit as cyberpunk water goddess robe, divine neon water halo above head, crying beautiful face mid-wail, surrounded by water orbs",
    "Darkness Lalatina Konosuba, long wavy blonde hair, crusader plate armor with neon blue runes, broadsword dragged along ground, flushing noble expression hiding her secret, tall powerful frame, absurdly tanky beautiful warrior",
    "Raphtalia ShieldHero, brown tanuki ears and long brown wavy hair, tail glowing amber, katana drawn crackling, demi-human swordmaster in elegant dark samurai cyberpunk armor, warm loyalty in eyes, hero's trusted companion energy",
    "Filo ShieldHero, tiny blonde girl with huge white angel wings tipped neon, Filolial Queen crown, cheerful unstoppable energy, foot mid-kick crackling with divine power, small and mighty, overwhelming speed aura",
    "Erza Scarlet FairyTail, long scarlet red hair, Requip magic mid-switch showing multiple neon armors layering, fierce battle cry expression, swords orbiting her like satellites, Titania queen of fairies absolutely dominant",
    "Lucy Heartfilia FairyTail, long blonde hair in ponytail, celestial gate keys glowing gold floating in circle, Aquarius and Leo spirit silhouettes behind her, warm smile turning fierce, whip extended crackling starlight",
    "Juvia Lockser FairyTail, blue hair in elaborate drills, rain always falling around her, water body half-dissolved and swirling dramatically, deep devoted eyes, water wings extending behind her, beautiful obsessive devotion",
    "Bulma DragonBall, short bright blue hair, orange capsule corp jumpsuit with cyberpunk tech vest, Dragon Radar holographic scan open, brilliant engineer surrounded by floating holographic blueprints, confident genius expression",
    "Android 18 DragonBall, blonde hair tucked behind ear, denim jacket cyberpunk modified with blue energy circuits, arms crossed with invisible ki aura making air ripple, cold beautiful efficiency, infinite power with zero expression",

    # 41-50 Dragon Ball / Naruto continued
    "Videl DragonBall, signature black short pigtails, Great Saiyaman helmet tucked under arm, gi upgraded with neon orange ki aura, learning-to-fly hover stance with confident fists, street fighter champion energy, determined girl",
    "Tsunade Naruto, long blonde hair in iconic twin pigtails, diamond Yin Seal on forehead glowing pink neon, Sannin robes as cyberpunk medic commander coat, fist ready to shatter ground, overwhelming presence, legendary beauty and strength",
    "Sakura Haruno Naruto, short pink hair, Shannaro energy fist crackling green and pink dual neon charging ground-shattering punch, Cha determination face, medic pouch and fighting stance, strength built from nothing",
    "Ino Yamanaka Naruto, long platinum blonde hair in ponytail, mind transfer violet neon wave leaving body, two poses of her simultaneously one real one spirit, fashionable kunoichi in cyberpunk floral bodysuit, clan jutsu beauty",
    "Temari Naruto, four spiky blonde ponytails, enormous iron fan fully extended crackling teal wind neon blades, wide fan swing mid-arc creating pressure wave, powerful confident shinobi expression, wind kunoichi dominance",
    "Yoruichi Shihouin Bleach, dark skin short purple hair, goddess of flash identity, golden speed neon afterimages trailing behind kick motion, casual sleeveless top, playful grin showing she barely tried, supreme mastery of speed",
    "Rukia Kuchiki Bleach, short black hair, Sode no Shirayuki ice zanpakuto raised, white rose petal ice scatter, shinigami uniform with noble white scarf, calm focused expression, kido blue glow from other hand, dual-threat beauty",
    "Orihime Inoue Bleach, very long auburn hair with flower hairpins glowing warm orange, Santen Kesshun shield dome crackling around her, gentle caring face with iron resolve protecting someone, healer turned warrior beauty",
    "Rangiku Matsumoto Bleach, wavy long strawberry-blonde hair cascading, Haineko zanpakuto dissolving into ash swarm, vice-captain badge catching neon light, lazy confident smile masking incredible power, feminine and fierce equally",
    "Nelliel Tu Bleach, green hair with helmet cracked showing horn, adult form with powerful mature figure, lance crackling green cero energy, gentle warrior expression, fraccion loyalty, espada power reawakening dramatically",

    # 51-60 My Hero Academia
    "Momo Yaoyorozu MHA, long black hair in iconic high ponytail, creation quirk manifesting white molten material emerging from skin creating cannon, intelligent tactical expression, elegant heroic costume with cyberpunk analysis visor",
    "Ochaco Uraraka MHA, short brown hair, Zero Gravity quirk making rubble and opponent float with pink anti-grav neon orbs, cheerful face turned serious mid-battle, meteor shower of rocks floating above her, agile hero stance",
    "Himiko Toga MHA, twin blonde bun with strands loose, blood-drain gauntlets glowing neon yellow, transform quirk cycling through faces with golden eyes, unhinged joyful dangerous smile, knife in hand dripping neon, yandere villain beauty",
    "Midnight MHA, long black and white hair wild, sleep quirk neon purple somnambulant mist pouring from wrists in curtains, whip raised, confident mature heroine posture, teaching and fighting simultaneously, mist swallowing background",
    "Mirko MHA, white hair and rabbit ears, powerful athletic body mid flying kick delivering enormous impact wave, scars on arm telling stories, fierce grin showing teeth, moon behind her, rabbit hero at absolute full power output",

    # 56-60 Jujutsu Kaisen
    "Nobara Kugisaki JJK, orange-brown bob hair, straw doll in one hand and nails glowing black cursed neon in other, hammer raised mid-resonance, fierce blunt no-nonsense expression, black flash cursed energy crackling on fist",
    "Maki Zenin JJK, short dark hair with tape on nose, glasses with neon green special grade sight, panda staff or naginata extended, cursed tool spirit manifesting, zero cursed energy making her invisible to curses, pure physical dominance",
    "Mei Mei JJK, long blonde twin braids, black suit with cyberpunk mercenary armor plates, twin ravens with neon eyes circling, confident calculating money-motivated expression, bird strike technique mid-deployment, cool and deadly",
    "Utahime Iori JJK, long dark hair, scar through face glowing faint purple, chant-type technique creating barrier song waves visible as neon musical notation in air, composed supervisor expression, strong quiet authority",
    "Shoko Ieiri JJK, short messy dark hair, reverse cursed technique green healing neon flowing from hands repairing catastrophic wounds, calm medical professional in crisis, cigarette balancing in corner of mouth, genius doctor energy",

    # 61-70 Slice of life / Steins Gate
    "Marin Kitagawa, very long wavy blonde hair with pink highlights, elaborate cosplay costume crackling with neon fabric magic, passionate open-mouth excited expression, surrounded by floating costume materials, gyaru beauty meets craft obsession",
    "Shizuku Kuroe, short black bob, dark indigo neon aura, small glowing doll figures dancing around hands, quiet mysterious artist expression, black dress simple and elegant, dark art magic barely visible at fingertips",
    "Nagatoro, long sleek black hair, dark tanned skin, sharp neon green teasing eyes mid-laugh, casual uniform unbuttoned slightly, leaning forward in bullying pose that hides deep affection, summer energy and predatory cute grin",
    "Uzaki Hana, short silver-white hair, Sugoi Dekai energy in every pose, loud expressive face mid-exclamation, bright yellow neon enthusiasm energy bursting out, energetic leaning forward invasion of personal space, overwhelming presence",
    "Komi Shouko, extraordinarily long straight black hair with violet sheen, neon letter particles floating as failed speech attempts, shy stunning beauty holding notepad, perfect elegant face flushed with communication anxiety, quiet goddess energy",
    "Najimi Osana, short wavy orange hair, chameleon friend energy with rainbow neon aura adapting to everyone, hands out in greeting, unpredictable cheerful expression, social butterfly hovering between genders, everyone's friend nobody's",
    "Yuno Gasai FutureDiary, long pink hair half-neat half-wild, diary phone glowing ominous pink-red, yandere smile beautiful and cracked, one eye loving one eye hunting, blood neon tear on cheek, love and murder indistinguishable",
    "Kurisu Makise SteinsGate, long reddish-brown hair, white lab coat with cyberpunk time research gear, teal time machine data streams swirling from open laptop, brilliant sarcastic tsundere expression, genius who changed the world",
    "Mayuri Shiina SteinsGate, short black hair with large hair clip, gentle round eyes, cosplay outfit mid-construction, Tutturu warm amber neon, innocent cosmic fate she carries without knowing, stars rotating slowly behind her smile",
    "Suzuha Amane SteinsGate, brown hair under army cap, future soldier fatigues with green timeline neon energy, bicycle leaning beside her, determined expression of someone who has seen terrible futures, time warrior at rest",

    # 71-80 Violet Evergarden / Fate / Code Geass
    "Violet Evergarden, long golden blonde hair, auto memory doll uniform with prosthetic silver arms now glowing neon blue at joints, typewriter keys floating around her like magic, violet letter neon paper dissolving into butterflies, deep lonely beautiful eyes",
    "Saber Alter, dark grey corrupted Artoria, black armor with corrupted Excalibur shooting black-violet neon beam upward, cold dark eyes with faint green glow, holy beauty swallowed by shadow, fallen king still standing proud",
    "Astolfo Fate, very long pink hair with braids, colorful knight armor redesigned as cyberpunk paladin, Hippogriff mount silhouette behind in neon, bright irresistible cheerful smile, flamboyant confident beautiful presence, pink neon lance",
    "Illyasviel von Einzbern Fate, waist-length white hair with curl, crimson eyes, magical girl outfit with giant magic kaleidoscope shield activating, cute face hiding Einzbern homunculus power, snowflake neon particles falling",
    "Kallen Kozuki CodeGeass, wild short red hair in cockpit glow, Knightmare Frame Guren cockpit cracked open with pilot half-emerged, resistance arm band, fierce passionate rebel expression, blood-red energy palm deployed",
    "CC CodeGeass, very long green hair past floor, Code geass mark on forehead glowing gold, white straightjacket opened to dress in flashback layers, eternal bored immortal expression, gold markings crawling skin, pizza box floating comedically",
    "Shirley Fenette CodeGeass, long orange hair, Ashford Academy uniform, love letter in hands glowing warm sunset neon, emotional loving expression caught between worlds, innocence in a world of war and code, tragic beautiful warmth",
    "Winry Rockbell FMA, long blonde hair in ponytail, mechanic overalls with automail arm blueprint holographic open, wrench tool glowing amber sparks, passionate determined expression, automail engineering genius hands already working",
    "Riza Hawkeye FMA, pulled-back blonde hair sharp and neat, military uniform, Black Hayate at heel, twin pistols raised with perfect posture and golden scope neon sight, Hawkeye sniper eye unnervingly calm, Roy's shield and weapon",
    "Lust FMA, impossibly long black hair dramatically falling, Ouroboros mark on chest glowing crimson, fingernails extending into Ultimate Lance blades neon-edged, deadly seductive expression, homunculus power barely leashed, femme fatale supreme",

    # 81-90 FMA / Spice Wolf / Toradora / Oregairu
    "Olivier Armstrong FMA, severe blonde hair in military braid under northern uniform, breath visibly cold, blue-neon ice blade Briggs sword drawn, fearless absolute zero expression, northern wall herself, rank intimidates god",
    "Holo SpiceWolf, long brown hair with wolf ears perked and fluffy tail raised high, harvest goddess ancient eyes, apple in hand, merchant travel cloak as cyberpunk trader coat, warm amber neon, wise playful smile hiding centuries",
    "Taiga Aisaka Toradora, long straight brown hair, tiny fierce frame in school uniform mid wooden-sword-swing, tiger palm strike releasing orange neon energy, tsundere attack face, palm-top tiger refusing to look small despite size",
    "Minori Kushieda Toradora, short orange hair, athletic uniform, softball bat swing mid-arc releasing warm sun neon energy wave, bright honest gorgeous smile, effortless athletic grace, summer best friend energy, warm and genuine",
    "Ami Kawashima Toradora, long blonde wavy hair, model pose with sharp eyes that shift from sweet to cold in same frame, dual face effect visible, elegant fashion forward, icy blue neon cold calculation beneath perfect performance",
    "Yukino Yukinoshita Oregairu, very long black hair with blue sheen, Sobu High uniform, book open with silver-blue neon analysis text projecting, cold perfectionist expression, legs crossed while standing somehow, elegant ice queen",
    "Yui Yuigahama Oregairu, short hair with pink dip-dye ends, warm coral neon, cheerful expressive face caught between smile and care, reaching hand toward viewer, social butterfly who learned real kindness, ribbon glowing soft",
    "Iroha Isshiki Oregairu, brown hair in cute side ponytail, student council badge glowing, sly perfect smile with eyes doing something different, manipulation wrapped in doe eyes, dangerous cute competence hiding real growth",
    "Ichika Nakano Quint, long blonde hair with five-star hairpin glowing gold, big sister composure mid-cooking scene, warm responsible expression, apron over elegant outfit, feeding everyone first, calm center of five chaos sisters",
    "Nino Nakano Quint, long blonde twin pigtails fierce and bouncy, tsundere chef with kitchen knife crackling rose neon, protective sister rage face turned shy love face in same frame, cooking for the person who broke her defenses",

    # 91-100 Quintuplets / Re:Zero
    "Miku Nakano Quint, long blonde hair with iconic deep blue headphones glowing neon, withdrawn but intense music lover, indigo sound wave neon emanating, fingers pressed to headphone cup listening to something only she hears, shy intense beauty",
    "Yotsuba Nakano Quint, short blonde hair with bright neon green bow, most cheerful sister at full sprint mid-jump, pure lime neon energy explosion, genuine bright smile with nothing hidden, athletic carefree sunlight made girl",
    "Itsuki Nakano Quint, long blonde hair with star hairpin, serious studious expression, teacher materials holographic in air, composed dignified sister, warm gold neon, most responsible and most underestimated, quiet power",
    "Echidna ReZero, long white hair with black roots, gothic witch of greed tea party dress redesigned as dark cosmic armor, tea cup floating with bone-white glow, eerily beautiful perfect smile hiding absolute evil, void portal behind her",
    "Satella ReZero, silver hair half-radiant half-consumed by shadow, witch of envy shadow hands reaching from dress hem like living darkness, violet crying eyes of genuine love and destruction, tragic goddess beauty consuming herself",
    "Frederica Baumann ReZero, long golden hair, beast transformation half-triggered showing slit eyes and neon amber glow, gate guardian uniform, elegant composed dangerous grin, half-beast half-noble, beautiful and feral simultaneously",
    "Elsa Granhiert ReZero, dark hair with red neon streak, black opera dress with curved blade hidden, bowel hunter grin of pure aesthetic sadism, blood neon art splatter as beautiful abstract pattern, deadly graceful movement frozen",
    "Ram ReZero, short pink hair with demon horn glowing bright hot pink, elite maid uniform with cyberpunk combat apron, Clairvoyance neon eye scan activating, condescending sharp beauty staring down at viewer, single horn radiating power",
    "Priscilla Barielle ReZero, very long scarlet red hair with elaborate crown, solar empress battle fan extended crackling golden sun neon, absolute arrogant gorgeous expression of someone who believes the world orbits them, divine right beauty",
    "Beatrice ReZero, very long drill blonde twintails, spirit arts magic circle glowing, library of Roswaal barrier crackling, loli witch irritated expression hiding fierce loyalty, I suppose energy, ancient spirit in small frame",
]

# ══════════════════════════════════════════════════════════════════════
# COMPOSIÇÕES — VARIEDADE MÁXIMA (sem travamento em close de rosto)
# ══════════════════════════════════════════════════════════════════════
COMPOSITION_STYLES = [
    # Corpo inteiro / full body
    {
        "name": "full_body_power",
        "prompt": (
            "FULL BODY vertical shot, character from head to toe filling 9:16 frame, "
            "powerful dynamic stance, feet planted or mid-motion, "
            "complete outfit and weapon visible, "
            "character takes up 85% of frame height, "
            "strong silhouette against cyberpunk background, "
            "dramatic low-angle perspective enhancing scale"
        ),
        "weight": 25,
    },
    {
        "name": "full_body_dynamic",
        "prompt": (
            "FULL BODY action composition, character mid-attack or power stance, "
            "energy effects emanating from hands or weapon, "
            "hair and clothes caught in motion, "
            "entire body visible in frame, "
            "Dutch angle adding drama, cyberpunk city below, "
            "vertical mobile-first framing"
        ),
        "weight": 20,
    },
    # 3/4 body — mostra rosto E corpo
    {
        "name": "three_quarter_cinematic",
        "prompt": (
            "3/4 BODY SHOT from mid-thigh up, face and full upper body and legs visible, "
            "face in upper portion, outfit fully readable, "
            "one hand extended toward viewer or weapon drawn, "
            "cinematic vertical composition, "
            "background out of focus, character sharp, "
            "natural attractive proportions fully visible"
        ),
        "weight": 25,
    },
    {
        "name": "three_quarter_portrait",
        "prompt": (
            "3/4 BODY elegant portrait, waist-to-top composition showing full face and torso, "
            "slight side angle showing depth and figure, "
            "face upper third, detailed outfit middle, "
            "one arm at side one extended or weapon resting, "
            "dramatic side lighting, vertical format"
        ),
        "weight": 20,
    },
    # Vista de costas com rosto visível
    {
        "name": "back_view_dramatic",
        "prompt": (
            "DRAMATIC BACK VIEW full body, character facing cyberpunk city below, "
            "hair flowing wild in neon wind, "
            "face turned 3/4 showing profile or slight side view, "
            "outfit and silhouette breathtaking from behind, "
            "weapon or energy held aloft, "
            "neon city sprawl far below, viewer perspective from behind"
        ),
        "weight": 10,
    },
]

# ══════════════════════════════════════════════════════════════════════
# CHANNEL IDENTITY & LOCKS
# ══════════════════════════════════════════════════════════════════════
CHANNEL_IDENTITY = (
    "DJ Dark Mark viral trap phonk anime visual, premium cyberpunk anime key visual, "
    "scroll-stopping YouTube Shorts thumbnail, cyberpunk neon world aesthetic, "
    "professional music channel art"
)

CORE_CHARACTER = (
    "one adult anime woman, clearly adult mature female proportions, "
    "beautiful detailed anime character, expressive detailed face, "
    "hypnotic eyes with neon catchlights, "
    "detailed hair with individual strand rendering, "
    "well-proportioned body with detailed costume, "
    "alone in frame, single character, no other people"
)

STYLE_LOCK = (
    "premium cyberpunk anime key visual art, "
    "clean sharp detailed lineart, "
    "high-end 2D anime illustration style, "
    "polished cel shading with rim lighting, "
    "cinematic neon lighting setup, "
    "glossy detailed eyes with multiple catchlights, "
    "rich saturated neon colors, high contrast shadows, "
    "professional music cover art quality finish, "
    "NOT photorealistic, NOT 3d render, anime illustration art style"
)

CYBERPUNK_LIGHTING = (
    "cinematic cyberpunk lighting: strong colored rim light splitting from behind, "
    "contrasting neon fill light on face and body, "
    "neon color reflections on skin and costume, "
    "volumetric light rays through atmosphere, "
    "beautiful dramatic body illumination from multiple neon sources, "
    "eyes catching and reflecting colored neon glow"
)

MOTION_LOCK = (
    "sense of movement and life: hair caught mid-motion in wind, "
    "floating neon particles and energy light specks, "
    "cinematic depth of field, foreground blur, "
    "glowing energy rippling in air around character, "
    "dynamic but not cluttered composition, "
    "neon bokeh spheres softly glowing in background"
)

VIRAL_HOOK_LOCK = (
    "one memorable visual hook: glowing energy weapon OR "
    "dramatic power aura surrounding body OR "
    "beautiful emotional expression with neon glow OR "
    "hair and outfit blown dramatically in cyber wind OR "
    "intense power charging with light effects, "
    "instantly memorable cyberpunk anime frame"
)

QUALITY_LOCK = (
    "masterpiece quality, best possible quality, ultra detailed rendering, "
    "crisp beautiful lineart, detailed shining neon-lit eyes, "
    "clean correct anatomy and proportions, "
    "professional channel branding quality, high resolution detail, "
    "premium polished finish, beautiful neon illumination on skin and clothes"
)

# ══════════════════════════════════════════════════════════════════════
# PALETAS CYBERPUNK
# ══════════════════════════════════════════════════════════════════════
PALETTE_TEAL_PINK = (
    "dominant teal and hot pink cyberpunk palette, deep navy shadows, "
    "teal and magenta neon split lighting on body, cool-warm contrast, "
    "classic cyberpunk color duality, electric atmosphere"
)
PALETTE_PURPLE_GOLD = (
    "dominant deep purple and gold cyberpunk palette, "
    "violet shadows with golden neon highlights on costume, "
    "luxurious dark cyberpunk royalty mood, rich high contrast"
)
PALETTE_CRIMSON_BLUE = (
    "dominant crimson and electric blue cyberpunk palette, "
    "dark dramatic shadows, blood-red and sapphire neon contrast across body, "
    "intense phonk cyberpunk energy, dangerous beautiful mood"
)
PALETTE_GREEN_ORANGE = (
    "dominant toxic green and amber cyberpunk palette, "
    "dark background, bio-neon green accents on outfit, warm orange rim light, "
    "edgy hacker aesthetic, high contrast neon pop"
)
PALETTE_WHITE_BLUE = (
    "dominant ice white and electric blue cyberpunk palette, "
    "cold clean atmosphere, frost and neon blue contrast across full frame, "
    "elegant cyberpunk winter aesthetic, crisp cinematic"
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
    "phonk":      "phonk cyberpunk atmosphere, heavy bass visual energy in pose, aggressive confident street aesthetic, dark neon underground feeling",
    "trap":       "trap cyberpunk atmosphere, urban night neon energy in stance, stylish supreme confidence, warm neon street premium look",
    "electronic": "electronic cyberpunk atmosphere, futuristic digital energy surrounding body, teal data streams, clean cyber rhythm visual pulse",
    "darkpop":    "dark pop cyberpunk emotional atmosphere, romantic sadness in neon city, cinematic emotional beauty, warm-cold color story on face",
    "dark":       "dark cyberpunk atmosphere, dramatic neon shadow play on body, intense emotional presence, single accent neon in near-darkness",
    "rock":       "rock cyberpunk energy, electric concert neon on stage, raw emotional power in body language, dramatic rim neon, performance energy",
    "default":    "dark cyberpunk atmosphere, emotional anime beauty, cinematic neon contrast on full body, premium viral Shorts visual quality",
}

# ══════════════════════════════════════════════════════════════════════
# POSES DINÂMICAS por composição
# ══════════════════════════════════════════════════════════════════════
POWER_POSES = [
    "standing with weapon raised overhead crackling energy, dominance pose",
    "mid-leap attack pose with energy trailing behind body",
    "arms spread wide with power aura expanding from chest outward",
    "one hand extended toward viewer with energy charging in palm",
    "crouching ready-stance with eyes locked forward, coiled power",
    "back slightly turned looking over shoulder with intensity, dangerous elegance",
    "walking toward camera slowly with absolute confidence, neon behind",
    "sitting on edge of rooftop legs dangling, relaxed supreme confidence",
    "spinning attack captured mid-rotation, hair and energy in spiral",
    "dual weapons crossed in guard stance, eyes challenging viewer",
]

BACKGROUND_VARIATIONS = [
    "rainy cyberpunk neon city street level, wet pavement reflecting neon towers, teal and pink bokeh depth",
    "cyberpunk rooftop edge at night, sprawling neon city far below, wind and height",
    "dark holographic data server hall, glowing blue server stacks receding into darkness",
    "cyberpunk rain-soaked alley with blurred neon kanji signs overhead, steam vents",
    "night cyberpunk skyline from above with flying vehicles and massive neon ad screens",
    "underground neon fight club, crowd blur and laser beams and smoke atmosphere",
    "cyberpunk research lab with holographic screens surrounding character position",
    "dark concert main stage with neon light beams and smoke machine, thousands blurred below",
    "pure void black with single strong neon rim split and floating data particle field",
    "cyberpunk night market, warm amber vendor neon and teal night sky, motion blur crowd",
    "abandoned cyberpunk shrine with broken torii glowing neon, rain and moss and tech",
    "floating cyberpunk highway overpass, cars blurred below, wind and neon and speed",
]

MUSIC_ELEMENTS = [
    "cyberpunk headphones around neck glowing neon accent color, immersed",
    "wireless neon earbud, music flowing through her changing the world color",
    "subtle holographic music waveform visible behind character, tasteful",
    "emotion IS the music element, pure cinematic cyberpunk anime body language",
    "neon music visualizer particles orbiting body softly, energetic",
    "microphone silhouette blurred in background neon depth",
]

# ══════════════════════════════════════════════════════════════════════
# NEGATIVE PROMPT
# ══════════════════════════════════════════════════════════════════════
NEGATIVE_PROMPT = (
    "ugly, bad anatomy, bad face, distorted face, asymmetrical eyes, "
    "bad hands, extra fingers, missing fingers, fused limbs, broken limbs, "
    "floating limbs, disconnected body parts, long neck, disfigured, mutated, "
    "melted face, uncanny valley, bad proportions, deformed body, "
    "blurry, low quality, jpeg artifacts, heavy noise, flat boring image, "
    "photorealistic, real photograph, real person, 3d render, CGI, doll, plastic skin, "
    "western cartoon style, simple cartoon, childish art style, "
    "child, underage appearance, loli, petite childlike body, baby face, school uniform only, "
    "nude, explicit nudity, nipples, genitalia, sexual act, pornographic content, "
    "multiple characters, crowd, two girls in frame, duplicate of character, "
    "text overlay, words in image, logo watermark, signature, letters, numbers in image, "
    "face too small to see, character too tiny in frame, lost in background, "
    "cluttered background overwhelming character, excessive busy neon overload, "
    "overexposed bloom washing out detail, muddy colors, washed out, desaturated, "
    "messy composition, no clear focal point, bad eyes, dead fish eyes, empty eyes, "
    "low contrast, boring flat lighting, no neon presence, dull lifeless colors, "
    "cropped body weirdly, floating head, missing lower body, cut off limbs"
)

GENERATION_SUFFIX = (
    ", beautiful expressive adult anime character, full body or 3/4 body visible, "
    "detailed costume and face, high contrast neon lighting on complete figure, "
    "clear powerful silhouette, dynamic alive cyberpunk frame, "
    "polished professional anime art, gorgeous full-body neon illumination, "
    "no text, no logo, no watermark, no extra people, vertical 9:16 mobile format"
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
    key = f"{style}|{filename}|{short_num}|darkmark_v42.0_cyberpunk"
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


def _weighted_composition(rng: random.Random) -> dict:
    total = sum(c["weight"] for c in COMPOSITION_STYLES)
    r = rng.random() * total
    acc = 0
    for comp in COMPOSITION_STYLES:
        acc += comp["weight"]
        if r <= acc:
            return comp
    return COMPOSITION_STYLES[0]


def _song_mood_boost(song_name: str) -> str:
    clean = song_name.lower()
    if any(w in clean for w in ["dark", "shadow", "ghost", "night", "madrugada", "noite"]):
        return "haunted neon night emotion, lonely but powerful, eyes carrying darkness visible in full body language"
    if any(w in clean for w in ["fire", "burn", "rage", "fury", "angry"]):
        return "intense cyberpunk fire emotion, contained rage expressed through full body stance, electric passionate power"
    if any(w in clean for w in ["love", "heart", "amor", "coracao", "rose", "cherry"]):
        return "dark cyberpunk romantic emotion, longing in full pose and expression, beautiful bittersweet full-body mood"
    if any(w in clean for w in ["lost", "alone", "lonely", "sozinho", "perdido"]):
        return "deep lonely cyberpunk emotion, isolated figure in neon city, cinematic solitude in body language"
    if any(w in clean for w in ["drive", "speed", "run", "race", "corrida"]):
        return "cyberpunk speed motion energy, body mid-movement with speed blur, wind and neon trailing the figure"
    if any(w in clean for w in ["queen", "king", "boss", "power", "rule"]):
        return "dominant cyberpunk queen aura, full body commanding presence, neon crown energy, power pose"
    if any(w in clean for w in ["dream", "sonho", "sleep", "cloud"]):
        return "dreamy floating cyberpunk emotion, body slightly levitating, ethereal neon particles around full figure"
    return "emotion matching the music carried in full body pose and expression, cyberpunk magnetic presence"


# ══════════════════════════════════════════════════════════════════════
# PROMPT PRINCIPAL — v42.0 CYBERPUNK WAIFU EDITION
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
    force_full_body: bool = False,
) -> str:
    styles = styles or []
    mapped = GENRE_MAP.get((style or "default").lower().strip(), "default")
    rng = _rng(mapped, filename, short_num)
    song_name = _clean_song_name(filename)

    # Seleciona waifu aleatória das 100 personagens
    char = rng.choice(TREND_WAIFUS)

    # Composição
    if force_back:
        composition = next(c for c in COMPOSITION_STYLES if c["name"] == "back_view_dramatic")
    elif force_full_body:
        composition = next(c for c in COMPOSITION_STYLES if c["name"] == "full_body_power")
    else:
        composition = _weighted_composition(rng)

    # Pose dinâmica
    pose = rng.choice(POWER_POSES)

    # Elementos visuais
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
        f"character design: {char}, "
        f"composition: {composition['prompt']}, "
        f"dynamic pose: {pose}, "
        f"{VIRAL_HOOK_LOCK}, "
        f"music element: {music_element}, "
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
        "beautiful adult cyberpunk anime character, emotional body language, trendy, memorable, "
        "stunning neon illumination across entire figure, gorgeous cinematic full-body quality, "
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
    force_full_body: bool = False,
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
        description="AI Image Generator — DJ DARK MARK v42.0 Cyberpunk Waifu Edition"
    )
    parser.add_argument("--style",             default="phonk",
                        help="Gênero: phonk, trap, electronic, dark, darkpop, rock")
    parser.add_argument("--filename",          default="dark phonk.mp3",
                        help="Nome da música (muda o mood do prompt)")
    parser.add_argument("--short-num",         type=int, default=1,
                        help="Número do short (varia seed e waifu)")
    parser.add_argument("--output",            default="assets/background.png")
    parser.add_argument("--force-teal-pink",   action="store_true",
                        help="Força paleta teal + pink")
    parser.add_argument("--force-purple-gold", action="store_true",
                        help="Força paleta purple + gold")
    parser.add_argument("--force-crimson-blue",action="store_true",
                        help="Força paleta crimson + blue")
    parser.add_argument("--back",              action="store_true",
                        help="Força vista de costas dramática")
    parser.add_argument("--full-body",         action="store_true",
                        help="Força composição de corpo inteiro")
    parser.add_argument("--prompt-only",       action="store_true",
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
        force_full_body=getattr(args, "full_body", False),
    )

    if args.prompt_only:
        print("=== PROMPT v42.0 CYBERPUNK ===")
        print(prompt)
        print("\n=== NEGATIVE PROMPT ===")
        print(NEGATIVE_PROMPT)
    else:
        generate_image(prompt, args.output)
