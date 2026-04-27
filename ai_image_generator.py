"""
ai_image_generator.py — DJ DARK MARK v43.0 CYBERPUNK ULTIMATE EDITION
=======================================================================
200 personagens de anime em tema cyberpunk com iluminação cinematográfica MÁXIMA
Composições variadas: corpo inteiro, 3/4, poses dinâmicas, vista de costas
Estilos: waifu sensuais, guerreiros épicos, vilões fodões, dark queens
TODOS OS EFEITOS: partículas, auras, energia, explosões de poder, neon extremo
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
    "num_inference_steps": 45,
    "guidance_scale": 9.5,
    "num_outputs": 1,
    "output_format": "png",
    "output_quality": 100,
    "disable_safety_checker": True,
}

# ══════════════════════════════════════════════════════════════════════
# 100 PERSONAGENS ORIGINAIS — CYBERPUNK WAIFUS v42.0
# ══════════════════════════════════════════════════════════════════════
TREND_WAIFUS_ORIGINAL = [
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
    # 11-20
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
    # 21-30
    "Nami OnePiece, shoulder-length orange hair, iconic Clima-Tact upgraded as cyberpunk weather staff with lightning orbs, bikini top and jeans redesigned as navigator's cyberpunk gear with neon amber accents, confident hand on hip, navigator queen",
    "Nico Robin OnePiece, long straight black hair, cyberpunk archaeologist in dark trench coat, hundred stone hands emerging from shadows in bloom, mysterious half-smile, Ohara holographic ruins behind her, cool intellectual power",
    "Boa Hancock OnePiece, floor-length black hair with iconic Kuja crown now neon, snake earrings glowing, revealing empress dress as cyberpunk authority gown, Love-Love beam hand pose, breathtaking arrogant beauty, snakes coiling around legs glowing",
    "Yor Forger SpyFamily, black hair with rose hairpin glowing blood-red, thorn-covered crimson dress redesigned as cyberpunk assassin armor, twin needles crackling with red neon energy, gentle smile hiding terrifying speed and strength",
    "Anya Forger SpyFamily, signature pink hair with dark tips, wide curious mind-reading green halo flickering, spy outfit way too big for tiny frame, iconic excited face with mouth agape, adorably small amid big neon spy world",
    "Lucy Edgerunners, teal-white hair floating weightless in cyberspace, pale skin with glowing neural ports, arms outstretched in data ocean, expression between bliss and breakdown, electric teal data streams curling around body like wings",
    "Rebecca Edgerunners, tiny frame with big attitude, two-tone blue-pink pigtails, oversized cyberpunk jacket sliding off shoulder, enormous Guts shotgun dragging on ground, standing wide-legged grinning wildly, punk energy in every pixel",
    "Saber Artoria FateSeries, iconic golden hair in tight braid, emerald green eyes, blue and gold plate armor crackling with Excalibur wind aura, sword raised with divine golden wind, noble resolute expression, heroic king energy",
    "Rin Tohsaka Fate, twin black pigtails with signature red ribbon bows glowing, black turtleneck and red skirt as cyberpunk mage combat outfit, twin glowing jewel gems charged with massive mana, tsundere determined fierce expression",
    "Jeanne d'Arc Fate, very long silver-white hair streaming behind, holy armor with divine neon gold circuits, standard banner crackling with sacred flame, serene determined expression of absolute faith, light and shadow split dramatically",
    # 31-40
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
    # 41-50
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
    # 51-60
    "Momo Yaoyorozu MHA, long black hair in iconic high ponytail, creation quirk manifesting white molten material emerging from skin creating cannon, intelligent tactical expression, elegant heroic costume with cyberpunk analysis visor",
    "Ochaco Uraraka MHA, short brown hair, Zero Gravity quirk making rubble and opponent float with pink anti-grav neon orbs, cheerful face turned serious mid-battle, meteor shower of rocks floating above her, agile hero stance",
    "Himiko Toga MHA, twin blonde bun with strands loose, blood-drain gauntlets glowing neon yellow, transform quirk cycling through faces with golden eyes, unhinged joyful dangerous smile, knife in hand dripping neon, yandere villain beauty",
    "Midnight MHA, long black and white hair wild, sleep quirk neon purple somnambulant mist pouring from wrists in curtains, whip raised, confident mature heroine posture, teaching and fighting simultaneously, mist swallowing background",
    "Mirko MHA, white hair and rabbit ears, powerful athletic body mid flying kick delivering enormous impact wave, scars on arm telling stories, fierce grin showing teeth, moon behind her, rabbit hero at absolute full power output",
    "Nobara Kugisaki JJK, orange-brown bob hair, straw doll in one hand and nails glowing black cursed neon in other, hammer raised mid-resonance, fierce blunt no-nonsense expression, black flash cursed energy crackling on fist",
    "Maki Zenin JJK, short dark hair with tape on nose, glasses with neon green special grade sight, panda staff or naginata extended, cursed tool spirit manifesting, zero cursed energy making her invisible to curses, pure physical dominance",
    "Mei Mei JJK, long blonde twin braids, black suit with cyberpunk mercenary armor plates, twin ravens with neon eyes circling, confident calculating money-motivated expression, bird strike technique mid-deployment, cool and deadly",
    "Utahime Iori JJK, long dark hair, scar through face glowing faint purple, chant-type technique creating barrier song waves visible as neon musical notation in air, composed supervisor expression, strong quiet authority",
    "Shoko Ieiri JJK, short messy dark hair, reverse cursed technique green healing neon flowing from hands repairing catastrophic wounds, calm medical professional in crisis, cigarette balancing in corner of mouth, genius doctor energy",
    # 61-70
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
    # 71-80
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
    # 81-100
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
# 100 NOVOS PERSONAGENS — v43.0 ULTIMATE SHONEN EDITION
# Waifus sensuais + guerreiros épicos absurdos
# Todos os efeitos: auras, partículas, explosões de energia, plasma
# ══════════════════════════════════════════════════════════════════════
TREND_WAIFUS_NEW = [
    # ═══ DEMON SLAYER — GUERREIROS E SENSUAIS ═══
    "Tanjiro Kamado DemonSlayer, short black hair with burgundy tips, iconic scar on forehead glowing flame neon, Hinokami Kagura fire breathing technique active, Sun Breathing flame wheel expanding from body in massive spiral, Nichirin blade coated in solar plasma fire, haori half-burned half-intact catching embers, tears and fire on face, absolute determination to protect, eruption of crimson and gold flames consuming entire frame, ember particles swirling upward in thousands",
    "Rengoku Kyojuro DemonSlayer, fierce flame-yellow hair spiking upward like fire itself, yellow-red eyes burning with eternal will, Flame Breathing final form massive dragon made of pure solar fire roaring behind him, Flame Hashira uniform burning at edges, both arms outstretched channeling inferno pillar, grin of absolute conviction even at death, volcano eruption energy in every particle, gold and red neon plasma storm",
    "Tengen Uzui DemonSlayer, long white hair wrapped in stylish binding, massive twin cleavers crackling Sound Breathing neon explosion frequencies made visible, body wrapped in jewel-covered festival bandages, six neon pink explosions detonating around him simultaneously, flamboyant open jacket showing muscular chest with sound wave tattoos glowing, most flamboyant pose mid-combat, sonic boom shockwaves radiating outward",
    "Mitsuri Kanroji DemonSlayer, long pink and green gradient hair tumbling past waist, unique modified pink Hashira uniform showing slender curves and flexible fighter's body, Love Breathing flexible whip-sword coiling like flowing ribbon crackling pink-gold energy, sensual agile body caught mid-impossible-flexibility pose, soft face carrying immense strength, cherry blossom petals and pink neon particles swirling in dense cloud around curves",
    "Daki UpperMoon DemonSlayer, very long silver-white hair with hints of teal, obi sash demon weapon extending in sharp crystalline blades glowing blood-red and white, revealing elegant kimono of a courtesan now made of living flesh and neon vein patterns, sensual deadly expression of absolute contempt, demon mark patterns glowing all over exposed skin, sashes slicing building facades behind her, devastating beauty",
    "Kokushibo DemonSlayer, upper moon one, long silver-purple hair in samurai bun, six eyes with neon crescent moon pupils glowing crimson, Moon Breathing absolute pinnacle technique releasing silver moon crescent blade storm in all directions, samurai armor with demon transformation fusion, half-human face cracking to reveal demon, moon-shard particles filling entire dark frame like a galaxy of blades",
    "Inosuke Hashibira DemonSlayer, wild spiky black hair beneath iconic boar skull mask cracked open revealing fierce feral face, dual serrated jagged blades Beast Breathing technique carving massive wind slashes in rocky terrain, muscular shirtless feral body with beast instinct crackling as electric blue neon all over skin, savage crouching beast stance unleashing everything, rocks and debris exploding outward",

    # ═══ JUJUTSU KAISEN — PODER EXTREMO ═══
    "Gojo Satoru JJK, iconic white hair styled back post-blindfold removal, Six Eyes glowing impossible cerulean blue through removed sunglasses, Infinity domain expansion Unlimited Void visible as infinite starfield unfolding behind entire frame, both hands releasing blue and red Hollow Purple technique colliding and detonating, infinity sphere distorting space around body, suit partially dissolved by domain energy, most powerful sorcerer standing at center of universe breaking apart",
    "Yuji Itadori JJK, spiky pink hair with black roots, Divergent Fist cursed energy delayed detonation exploding from fist with double impact shockwave, Sukuna tattoos crawling up arms glowing crimson while Yuji resists, Black Flash black lightning crackling between knuckles at moment of impact, intense determined expression refusing to yield, cursed energy storm surrounding body, cracked ground beneath combat boots",
    "Ryomen Sukuna JJK, iconic pink spiked hair, four arms deployed simultaneously each crackling with domain energy, Malevolent Shrine cleave technique visible as massive invisible blade cutting reality itself, black tattoos covering entire body glowing crimson, second set of eyes on cheeks open revealing ancient evil, Dismantle and Cleave shockwaves crossing dimensions, king of curses standing in annihilated cathedral of cursed energy",
    "Megumi Fushiguro JJK, dark hair messy and damp, Ten Shadows Technique deploying entire divine dog pack plus Eight-Handled Sword Divergent Sila Shadow of the Zen'in demon dog pack with Mahoraga emerging behind him as massive divine beast, shadow energy consuming ground, cool detached expression hiding massive calculation, shikigami summoning circle glowing under feet, shadows alive and hungry",
    "Nanami Kento JJK, neat side-part blonde hair, dress shirt sleeves rolled up, Ratio Technique blade extended crackling with precise 7:3 cursed energy split point glowing, bandaged weapon enforcing weakpoint law of the universe, tired professional expression of a man who was done with this years ago but does it anyway, suit slightly torn, cursed energy disciplined and precise as a razor edge",
    "Yuta Okkotsu JJK, messy dark hair, Rika cursed spirit massive Queen of Curses manifesting behind him as enormous beautiful horrifying neon specter consuming background, Copy technique replicating every technique simultaneously, massive cursed energy output overwhelming entire frame, quiet gentle face contrasting catastrophic power output, most cursed energy in the series, universe of curses orbiting him",
    "Choso JJK, long black hair divided by white streak, blood manipulation technique Supernova shooting blood bullets at hypersonic speed leaving trails, Piercing Blood technique railgun condensed crimson beam piercing through buildings, calm ancient expression of someone thousands of years old, blood vessels on forehead glowing neon, blood armor forming across body, oldest death painting technique bearer",

    # ═══ ONE PIECE — LENDAS DO MAR ═══
    "Monkey D Luffy GearFifth OnePiece, wild black hair, Gear Fifth white hair and clouds surrounding body, rubber reality-warping deity form making entire island cartoonish, massive fist enlarged to city-block scale mid-punch at Kaido, clouds pulled in spiral around giant form, laughing wildly while punching god-tier adversary, Sun God Nika form with neon white aura making the impossible joyful, gigantic scale of impact",
    "Roronoa Zoro OnePiece, short green hair damp and wind-blown, three Meito swords in three-sword style Asura technique manifesting nine phantom sword duplicates behind him creating demon god silhouette, Enma blade drinking haki and releasing it as devastating black neon slash, King of Hell Three-Sword Style massive energy dome detonating, eyepatch scar glowing haki, Nine-Sword God stance consuming entire background",
    "Shanks RedHair OnePiece, flowing long red hair, Supreme King Haki Conqueror's emission visible as black lightning storm crackling across entire sky, presence alone making seas split and enemies collapse, powerful arm raised as casual gesture but output splitting storm clouds, Gryphon sword Kamusari swing leaving divine red-gold energy arc, strongest man in the world needing no effort to end everything",
    "Trafalgar Law OnePiece, dark hair under spotted hat, ROOM technique giant blue sphere engulfing multiple city blocks glowing electric blue lines, Shambles swapping objects and people mid-air, Gamma Knife penetrating body without external wound via invisible energy blade, K-Room Shock Wille technique massive neon surgery sphere, three K letters glowing, cool calculating surgeon of death expression",
    "Silvers Rayleigh OnePiece, gray hair and beard, Dark King prime form with massive Conqueror's and Armament Haki combined creating an invisible shockwave you can see only by its destruction, teaching-pose but devastating power visible in every relaxed stance, right-hand man of King of Pirates carrying that era's full weight, casual clothing hiding absolute apex predator",
    "Portgas D Ace OnePiece, short black hair with freckles, Fire Fist Ace Flame Commander technique massive wall of fire shaped like fist detonating, orange flame explosion consuming frame, pirate ace jacket open showing Whitebeard mark tattoo on back lit by own flames, brilliant smile seconds before everything goes wrong, fire becoming wings briefly before impact, legendary commander of Whitebeard pirates",

    # ═══ NARUTO / BORUTO — SHINOBI ÉPICOS ═══
    "Naruto Uzumaki SageOfSixPaths Naruto, long spiky blonde hair with Truth-Seeking Orbs orbiting, Six Paths Sage Mode aura combining all nature transformations simultaneously, Tailed Beast Mode overlay showing Kurama fox spirit behind as massive god silhouette filling sky, Rasengan Planetary construction of eleven massive energy spheres, orange-gold-white neon power output making the world orange, sheer energy tearing landscape apart",
    "Sasuke Uchiha Rinnegan Naruto, dark hair with single blue Rinnegan eye and Eternal Mangekyo Sharingan eye, Susanoo Perfect form purple humanoid titan covered in cursed mark patterns assembled around him, Indra's Arrow technique charging maximum power beam from bow, lightning and dark energy fusion technique that can destroy bijuu, rival-level to a god, cool calm face at epicenter of destruction",
    "Kakashi Hatake SixPaths Naruto, silver hair, Dual Mangekyo Sharingan activated both eyes, Perfect Susanoo summoned as towering blue warrior god, kamui lightning blade in one hand perfect Susanoo sword in other, gravity of legend visible in every particle, masked face with single eye conveying absolute calm authority, lightning crackling off every surface near him",
    "Itachi Uchiha Naruto, long black hair in iconic low ponytail, Mangekyo Sharingan blood-red spinning, Amaterasu black inextinguishable flames erupting, Tsukuyomi illusion world fracturing reality, Susanoo ribcage forming with Yata Mirror and Totsuka Blade artifacts, pale elegant face hiding terminal illness and supreme sacrifice, greatest genjutsu master in history surrounded by falling crows",
    "Minato Namikaze FourthHokage Naruto, iconic spiky yellow hair, Flying Thunder God jutsu teleportation leaving yellow flash afterimage trails across entire frame, Rasengan plus Kurama Mode combined attack charging, Jonin cloak flowing, greatest speed technique in shinobi history, calm cool face of a man who sacrificed himself for peace, yellow lightning across entire black sky",
    "Might Guy Naruto, thick eyebrows, Eight Gates Released Formation Gate of Death Hachimon Tonkou opened, entire body wrapped in green-red steam vapor from cellular destruction, Evening Elephant technique five consecutive air vacuum punches audible across continents, red steam aurora consuming entire frame like a comet, absolute power beyond human limit burning body away, the most passionate man in the world",

    # ═══ BLEACH — SHINIGAMI E HOLLOWS ═══
    "Ichigo Kurosaki TrueShikai Bleach, spiky orange hair wild with spiritual pressure, True Shikai form with Zangetsu cleave becoming massive scale that dwarfs mountains, Final Getsuga Tensho Mugetsu technique erasing all light in the universe briefly, inner hollow and Quincy heritage and shinigami power all three fusing simultaneously, pressure visible as black energy corona displacing atmosphere around body, king of souls",
    "Sosuke Aizen Bleach, neat brown hair descending to ultimate butterfly form transcending shinigami and hollow, Kyoka Suigetsu shatter-illusion reality fracturing making impossible moves appear real, presence alone distorting space, god complex completely earned because he actually achieved it, Hogyoku integrated into chest glowing with all-seeing purple neon, calm smile of someone who has won before the fight begins",
    "Kenpachi Zaraki Bleach, spiked black hair with bells at tips, eye patch off revealing true Reiatsu flooding out as terror incarnate making atmosphere pressurize, Yachiru true form Nozarashi unleashed as massive spiritual pressure blade that cuts fate itself, no technique just pure killing intent so overwhelming it reshapes space, muscles straining and bleeding and he's grinning harder",
    "Byakuya Kuchiki Bleach, neat black hair with silver kenseikan ornaments, Senbonzakura Kageyoshi ten-thousand cherry blossom blades filling entire sky as beautiful deadly pink snowstorm, noble house captain presence with absolute dignity, scarf floating in blade-wind, two modes: elegant aristocrat and absolute annihilation, petals becoming blades becoming storm, cold beauty of inevitable judgment",
    "Ulquiorra Cifer Bleach, pale face with tear marks, Segunda Etapa final resurrection releasing massive bat wings of pure condensed Reiatsu, Lanza del Relampago javelin of condensed Cero that destroys entire areas on detonation, black and green neon Cero power, highest espada existential nihilism given form, lance crackling with ultimate spiritual energy as rain falls around expressionless face",

    # ═══ DRAGON BALL — SUPER SAIYAJINS ═══
    "Goku UltraInstinct DragonBall, silver-white hair with glowing silver UI aura corona, Ultra Instinct Mastered movement so fast it defeats gods, silver neon aura producing heatwave visible as atmospheric distortion, Hakai Destruction energy ball in palm, Perfected Ultra Instinct face calm as water surface despite universe-shattering power output, fighting gods on their own level with casual grace and absolute peak performance",
    "Vegeta UltraEgo DragonBall, widow-peak dark hair, Ultra Ego form with dark purple aura consuming all light around him, power that increases the more damage received turning battle into pure ascending destruction, Hakai sphere in hand, Final Explosion energy charging that would sacrifice self to destroy god, Ultra Ego symbol visible in aura, pride of a Saiyan Prince who never yielded, universe shaking at his feet",
    "Gohan Beast DragonBall, long white hair awakened beyond all previous limits in Beast mode, eye twitching with barely-controlled rage when Piccolo is hurt, explosive white neon aura cascading off body in sheets, glasses broken on floor, scholar becoming the most powerful hybrid saiyan ever, Special Beam Cannon charging in tribute to father figure, power making surrounding fighters feel gravity increase",
    "Future Trunks DragonBall, iconic purple hair, Super Saiyan Rage form with blue electricity wrapping Super Saiyan gold aura, time machine sword channeling energy of all humans killed by androids, Spirit Sword energy blade of hope and collected rage extending enormous, traveling back through time with desperation of entire destroyed future on his shoulders, blue and gold energy storm consuming frame",
    "Broly Legendary DragonBall, massive frame towering, Legendary Super Saiyan form with green-tinted primal explosive aura dwarfing all other Saiyans, eyes going blank with pure rage and power, Eraser Cannon green energy blast that overwhelmed two Super Saiyan Gods simultaneously, primal screaming face with power output that destabilizes planetary bodies, primordial Saiyan beyond all control",

    # ═══ MY HERO ACADEMIA — HERÓIS E VILÕES ═══
    "Izuku Midoriya OFA DragonFist MHA, messy green hair wild with One For All electricity crackling all over body, 100% Full Cowl black whip Delaware Smash Air Force techniques combining, Gran Torino air pressure gauntlets forming, Blackwhip tendrils extending in all directions anchoring to everything, Gear Shift Full Cowl maximum output making ground crater under feet, determination face of someone who refused to give up screaming into wind, all predecessors' OFA ghosts standing behind",
    "Katsuki Bakugo MHA, spiky ash-blonde hair spiking up in explosion wind, Howitzer Impact technique spinning in air collecting sweat for maximum AP Shot point-blank detonation, Explosion quirk plasma orange and black neon bursting from both hands simultaneously, blast backwash making hair and jacket explode outward, most aggressive competitive expression, Explosion Creation is his destiny, rival to the strongest hero",
    "Shoto Todoroki MHA, half-white half-red hair split perfectly down center, left side erupting enormous ice glacier right side erupting massive fire pillar simultaneously, Hell Spider flame whip and glacier wall deployed at same time, Phosphor bright white flame technique radiating off entire body, both powers fully combined at maximum accepting both halves of himself, expression of someone who chose their own path",
    "All Might MHA, iconic muscle-form massive build, United States of Smash maximum power punch hitting target as last act of symbol of peace, neon gold and white Detroit Smash wind pressure wave moving at supersonic speed, cape disintegrating in his own power, gaunt injured face inside massive borrowed power, sunrise behind him always, ONE FOR ALL at its origin carried in this impossible hero body",
    "Tomura Shigaraki MHA, pale cracked hands and disheveled blue-gray hair, All For One awakening making face crack and reform, Decay quirk touching ground and entire city block disintegrating into expanding wave of destruction, Gigantomachia following behind as living mountain, Paranormal Liberation Front general standing in apocalyptic power, inherited hatred and stolen power at maximum output, empty eyes that have become something beyond villain",

    # ═══ ATTACK ON TITAN — TITÃS E GUERREIROS ═══
    "Levi Ackerman AOT, undercut dark hair, Ackerman bloodline awakening manifesting as black energy aura that calculates every possible outcome, ODM gear triple-blade spinning technique that killed the Beast Titan alone amid rain of boulders, lightning-fast movement leaving afterimage shadows visible to eye, face covered in scars and blood with zero concern, the strongest soldier in humanity standing in titan graveyard, thunder clapping from speed",
    "Eren Yeager Founding Titan AOT, wild dark hair, Founding Titan's true colossus form emerging from the earth as 80-meter skeletal deity, Wall Titans marching in thousands following the rumble of the world, Founding Titan power rewriting memories of all subjects, jaw titan and attack titan fused into one catastrophic form, hollow screaming while collateral damage becomes history itself, Paths dimension visible as sepia lines in air",
    "Erwin Smith AOT, thick blonde brows and commanding presence, Survey Corps Commander leading final charge directly into the Beast Titan's boulder barrage with one arm gone, every soldier following him knowing they will die for one moment of opportunity, ODM gear deployed at maximum with determination speech still ringing in the air, commander who chose victory over survival, leadership so absolute it changes outcomes from beyond the grave",

    # ═══ ONE PUNCH MAN — PODER ABSOLUTO ═══
    "Saitama OnePunchMan, bald head and plain yellow costume, Serious Series Serious Punch delivering a blow so powerful it parts storm clouds across continent, air pressure from single punch visible as tornado-scale atmospheric impact, casual bored face on body that delivers universe-shattering blows, empty eyes of someone who won too easily, one fist extended and everything within range simply ceases, aftermath of total obliteration around one average-looking man",
    "Genos OnePunchMan, metallic cybernetic body with neon blue power cores exposed all across torso and arms, Incineration Cannons arms transforming into dual plasma cannons charging Hellfire Burst discharge, particle beam so hot it creates plasma trail, heroic upgraded S-Class cyborg body rebuilt at cutting edge, glowing amber synthetic eyes determined to protect teacher, full power output melting surrounding terrain",
    "Garou OnePunchMan, white hair spiked wild in Cosmic Fear Mode, God Power absorbed into human body creating star-level output, Gravity techniques bending space in combat, copying every martial arts style into Godly Fist that surpasses all humans and gods, blood across face and torn outfit from battle with Saitama himself, the greatest monster who became the greatest hero, cosmic power making him float amid shattered asteroids",
    "Tatsumaki OnePunchMan, short childlike figure with intense green eyes and floating black dress, maximum Psychokinesis output lifting an entire destroyed city block above her in one continuous telekinetic field, barriers of compressed green energy floating like orbiting shields, arms crossed with absolute contempt for everyone present, most powerful esper in history looking bored while performing impossible feat, green neon storm consuming background",
    "Fubuki OnePunchMan, long black hair with bangs, Hell Storm technique channeling B-Class maximum Psychokinesis into spiraling tornado of solid psychic force lifting targets and crushing them, elegant fitted dress split for combat, psych shield bubble surrounding group, older sister pride and younger sister complex simultaneously, green psychic glow making surroundings float in debris field, blizzard group's queen at her best",

    # ═══ HUNTER X HUNTER ═══
    "Gon Freecss JajankenPeak HxH, spiky black hair, Jajanken Rock technique charging entire Nen lifeforce into single fist emitting golden Nen overflow aura visible as mile-wide explosion flash, adult transformation burning own life potential for one moment of power, green Nen energy overflowing far past containment, pure joy of hunting turning to pure ferocity when someone threatens friends, primal scream releasing everything",
    "Killua Zoldyck Godspeed HxH, white spiky hair, Godspeed Whirlwind technique body coated in lightning bioelectric field that makes him functionally invisible from speed alone, Thunderbolt hand strike leaving electric afterburn, Kilua eye change showing assassin bloodline activated, silver-white lightning aura making hair and clothes levitate from charge, most naturally talented nen user born into killing smile that means danger",
    "Hisoka Morrow HxH, red and purple spiked hair, Bungee Gum elastic and sticky Nen stretching and snapping clown suit through entire arena, card throw accelerated with Bungee Gum hitting with bullet velocity, magician battle performer grinning with pure predatory excitement finding a worthy opponent, star and heart face marks glowing neon, everything about him radiating dangerous beautiful chaos",
    "Kurapika HxH, blonde bangs and intense face, Scarlet Eyes activated full Kurta clan crimson iris flaring, Emperor Time Conjuration unlocking 100% efficiency of all nen systems simultaneously at cost of lifespan, chains Judement Chain wrapping around opponent's heart with conditions, Steal chain extracting nen abilities, chain jail inescapable restraint system, grief and revenge and hope all burning in those impossible red eyes",
    "Meruem PerfectForm HxH, pale humanoid chimera ant king in final form, Nen absorption making Rose poison dispersal powerless by absorbing Pouf and Youpi power doubling capacity, board game grandmaster calm strategic face destroyed by one human girl's refusal to lose, royal guard power consumed and returned as ultimate chimera energy, brief beautiful tragedy of a monster who learned what it is to love",

    # ═══ FULLMETAL ALCHEMIST ═══
    "Edward Elric FMA, golden hair in braid, automail arm transforming into full combat weapon with alchemical circle activation transmuting ground into entire fortress while transmuting air into weapon, Philosopher's Stone temporarily forbidden power glimpsed, alchemy circles glowing under boots, short man with oversized power complex and the heart of a true hero, brotherhood theme activating visually in golden neon",
    "Roy Mustang Flame Alchemist FMA, dark military uniform immaculate, Flame Alchemy ignition glove snap producing a flame that becomes an entire sun compressed into a column destroying entire Promised Day facility, blue flame version going beyond oxygen toward divine fire, colonel expression shifting from calm to terrifying when someone he protects falls, Fuhrer-level power in service of a better world through righteous flame",
    "King Bradley Wrath FMA, slicked hair, eye patch removed revealing Ultimate Eye that sees all trajectories in the world, five swords deployed simultaneously targeting every weakness in opponents, Homunculus Wrath physical perfection making him fastest purely-physical fighter in series, stone-cold military precision masking volcanic Wrath sin, Fuhrer cutting through entire military opposition without a single wound",

    # ═══ SOLO LEVELING ═══
    "Sung Jinwoo ShadowMonarch SoloLeveling, dark hair with empty emotionless hunter eyes, Shadow Monarch power erupting as massive black-purple aura of death energy consuming surroundings, shadow army of millions marching behind him as silhouettes, Kamish Wrath technique drawing sword of shadows and reaping all life in arc, Igris and Beru flanking as massive shadow knights, stone expressionless face of someone who became the strongest while everyone else slept, death and power given human form",
    "Thomas Andre SoloLeveling, massive titan build, National Level Hunter Reinforcement skill making body truly invulnerable while Collapse technique generates a gravitational collapse field around fist, crater forming underfoot, American powerhouse vs the Shadow Monarch in equal clash, overwhelming physical presence that bent national armies by existing",

    # ═══ BERSERK ═══
    "Guts BlackSwordsman Berserk, massive black Dragon Slayer sword carried in one arm that is actually a cannon, Brand of Sacrifice wound bleeding black, Berserker Armor activated making him bleed from every joint while multiplying power beyond human comprehension, Apostle-killing charge through impossible odds, one eye, mad dog grin of someone who refuses to die because death would be giving fate what it wants, absolute anti-hero defiance",

    # ═══ BLUE LOCK ═══
    "Isagi Yoichi BlueLock, dark hair wet with sweat, Spatial Awareness meta vision technique activating as glowing field grid overlay visible around entire pitch, direct shoot technique with perfect physics calculation catching opponents completely off-guard, evolution happening mid-match as predator instinct awakens, determined expression of someone becoming the world's best striker through pure calculated greed for goals",
    "Rin Itoshi BlueLock, long dark hair tied back, Direct Drive Zone technique entering state of perfect predictive reaction where body moves before thought, Almight Tornado blast shot combining spin and power to break any goalkeeper's hands, prodigy with a brother complex becoming soccer's greatest weapon, cold eyes hiding rage and love in equal measure, teal and dark aura of absolute technical mastery",
    "Bachira Meguru BlueLock, curly messy hair, Monster Inside awakened as instinctive chaotic dribbling style that no defensive system can pattern-match, phantom monster visualization guiding feet through impossible paths between defenders, uncontrollable joy of pure individual expression through soccer, smile of someone who found his pack, rainbow neon dribble path lines visible as light trail behind feet",

    # ═══ FRIEREN / WITCH / FANTASY WAIFUS ═══
    "Frieren AtTheEndOfJourney, long silver elf hair with decorable hair ties, ancient elven mage holding staff with accumulated thousand years of magic knowledge, Zoltraak offensive magic now casual finger-flick that one-shots Demon Lord lieutenants, magic field analysis sight activated as faint glow, elegant flat affect face that carries grief of watching everyone she knew age and die, cherry blossoms mixed with magic particle cascade because she stopped to pick them",
    "Fern FrierenDisciple, long dark hair in twin braids, prodigy mage Zoltraak rapid-fire multi-volley at maximum output far exceeding any mage her age, concentrated efficient mana expression without waste, serious diligent face secretly loving magical trinkets, cold eyes that warm around her master, blue-white magic blast charges erupting from both hands toward opponent, most efficient mage born in a century",
    "Mitsuri Kanroji SensualWaifu DemonSlayer, pink-green gradient long hair loose and wild in battle wind, flexible kunoichi-influenced fighting style wrapping Flame Breathing around incredibly flexible and powerful body moving through impossible angles, revealing pink Hashira uniform catching wind, warm smile of someone who just wants to be loved existing in a deadly body, cherry blossoms and flame neon surrounding curves",
    "Albedo Overlord, floor-length black wavy hair, white dress of an angel covering the most loyal Floor Guardian of Nazarick, Hermes Trismegistus ultimate shield deployed as enormous wing barrier, Levia Halcyon great axe erupting with Armageddon power, sensual face twisting between loving Ainz and protecting Nazarick with frightening obsession, halo and black wings simultaneously, perfect beauty with perfect evil loyalty",
    "Shalltear Bloodfallen Overlord, long silver drill hair, true vampire lord form with wings deployed, Blood Frenzy activated making her more powerful with each wound received, Spuit Lance crackling crimson, Floor Guardian level power, sensual form in red gothic battle dress covered in opponent's blood like war paint, pale skin with neon red eyes looking directly at viewer with possessive hunger",
    "Milim Nava ThatTimeSlime, iconic twin pink drill pigtails, Drago Nova channeling full Demon Primogenitor power into energy condensed to single point output exceeding nuclear fusion, Milim Eye demonic eye technique stripping all illusions from the world, small frame hiding catastrophic Demon Lord power, cheerful open grin while casually erasing mountains, the oldest and strongest Demon Lord playing like a child because she can",
    "Noelle Silva BlackClover, silver-white hair, Water Creation Magic Valkyrie Armor manifesting as divine water armor of raging seas channeled into knightly form, Saint Stage magic output making surrounding ocean rise up, noble clumsy determination growing into real power, beautiful aristocratic face carrying doubt turning to absolute confidence, water dragon manifestation spiraling around armored body",
    "Ai Hoshino OshiNoKo, long black hair with pink ends, idol stage performance costume catching concert lighting, pink-gold star neon particles erupting from stage floor as adored idol persona activates, warm mother's eyes hiding cosmic idol secret, ruby and aquamarine stars forming in air, unforgettable smile that made the entire nation fall in love, roses falling from above in pink and white neon",
    "Tatsumaki SexySister OnePunchMan, short petite frame and dramatic short green hair, older sister emerald eyes showing contempt and hidden pride, maximum Psychokinesis lifting entire meteor field above her simultaneously, elegant floating dress, arms crossed with absolute casual power, most powerful esper in the world dismissing everything, forest of floating debris framing petite figure in green energy corona",
    "Merlin SevenDeadlySins, elegant short dark hair, Infinity ability stopping all spells in permanent suspension making her unkillable by any technique, Aldan floating jewel sphere amplifying all magic beyond reasonable output, Boar's Hat mage in revealing combat attire, greatest mage alive carrying century of accumulated spells, mysterious half-smile of someone who knows much more than she reveals",

    # ═══ BLACK CLOVER ═══
    "Asta BlackClover, spiky white hair Anti-Magic form, five-leaf grimoire opening and pouring out concentrated Anti-Magic black energy consuming surrounding magic entirely, Demon-Destroyer Sword extended as enormous black claymore, Devil Union mode with Liebe merging making skin half-black crackling anti-magic, no magic but the strongest will in the world, bull-headed determination outscreaming destiny itself, the one who became Wizard King without a drop of magic",
    "Yuno StarMagicArcher BlackClover, long dark hair with golden four-leaf clover grimoire glowing, Wind Spirit Sylph merged into body multiplying all magic, Star Magic massive star-shaped energy cannon charging across entire sky, spatial magic barriers unfolding like origami made of galaxies, genius rival who was always a step ahead, elegant confident expression of prodigy born with everything Asta wasn't, golden light and star constellation patterns filling frame",

    # ═══ TOKYO REVENGERS ═══
    "Mikey Sano TokyoRevengers, platinum blonde bowl cut, delinquent king stance mid-kick delivering Invincible Kick technique with leg rising past vertical creating shockwave crack in asphalt, motorcycle jacket open, dark impulse mode visible as black aura underneath normal Mikey smile, natural gift for violence making him simultaneously the best person to know and most dangerous, gang leader who broke the future",
    "Draken TokyoRevengers, long side-shaved hair with dragon tattoo on temple glowing blue neon, towering frame mid-punch that caves in gang leader's guard, loyal right-hand of Mikey energy, Dragon's Fang technique releasing visible blue impact ring, old-school Tokyo delinquent with heart made entirely of gold, protective fury channeled through fists, most reliable person in any crew protecting what matters",

    # ═══ CHAINSAW MAN — HERÓIS ═══
    "Denji ChainsawMan, messy brown hair with iconic zipper pull in chest, chainsaw blades erupting from forehead and arms in full Chainsaw Devil manifestation, Pochita contract giving him ability to revive and escalate, blood-soaked wide grin of someone who wanted toast and got a devil war instead, primal hero energy, motor roaring as entire frame fills with blood and chainsaw neon, simple dream in impossible nightmare",
    "Aki Hayakawa ChainsawMan, neat dark hair and serious face, Future Devil contract showing him his death but choosing to continue, Fox Devil technique summoning enormous jaw snap consuming target, Sword Devil possession partially integrated showing cursed transformation beginning, government devil hunter cigarette lit and sword drawn, dignified soldier energy carrying foreknowledge of his own tragedy forward anyway",

    # ═══ VINLAND SAGA ═══
    "Thorfinn VinlandSaga, long blonde hair wild and unkempt after years of slavery, pacifist warrior who unlearned killing becoming more dangerous than ever with pure technique empty of bloodlust, phantom lance technique so refined it defeats berserkers without injury, scar across face from the world's cruelty, the most dangerous man in the north who chose not to be dangerous, bearing weight of father's murder and own sins toward a land of peace",
    "Askeladd VinlandSaga, short silver-blond hair, Roman-Welsh noble bearing mixed with Viking pragmatism, Luin of Celtchar spear technique making him the most dangerous individual combatant in the Danish great army, chess master manipulator three steps ahead of every faction, warm dangerous smile of the greatest villain who was also the greatest father figure, winter breath visible in cold northern air",

    # ═══ OVERLORD ═══
    "Ainz Ooal Gown Overlord, enormous black robes of the Sorcerer King, skeletal lich body with hypnotic glowing eyes in empty sockets, greatest guild Yggdrasil's World-Class Item Meteor Fall crashing from above destroying armies, dark magic corona of thousands of Death Knights summoned, overlord of Nazarick standing at apex of magical power, suppressing all emotion through undead body while secretly panicking about keeping up appearances as supreme ruler",
]

# ══════════════════════════════════════════════════════════════════════
# LISTA COMPLETA — 200 PERSONAGENS COMBINADOS
# ══════════════════════════════════════════════════════════════════════
TREND_WAIFUS = TREND_WAIFUS_ORIGINAL + TREND_WAIFUS_NEW

# ══════════════════════════════════════════════════════════════════════
# COMPOSIÇÕES — VARIEDADE MÁXIMA
# ══════════════════════════════════════════════════════════════════════
COMPOSITION_STYLES = [
    {
        "name": "full_body_power",
        "prompt": (
            "FULL BODY vertical shot, character from head to toe filling 9:16 frame, "
            "powerful dynamic stance, feet planted or mid-motion on crumbling ground, "
            "complete outfit and weapon visible with energy effects on every surface, "
            "character takes up 85% of frame height, "
            "strong silhouette against exploding cyberpunk background, "
            "dramatic low-angle perspective enhancing godlike scale, "
            "debris and energy particles filling every corner of frame"
        ),
        "weight": 25,
    },
    {
        "name": "full_body_dynamic",
        "prompt": (
            "FULL BODY action composition, character mid-attack or maximum power stance, "
            "massive energy effects erupting from hands and weapon in all directions, "
            "hair and clothes caught in shockwave motion, entire body visible in frame, "
            "Dutch angle adding extreme drama, cyberpunk city crumbling below, "
            "vertical mobile-first framing, impact shockwave rings visible, "
            "atmospheric pressure visible as energy distortion around body"
        ),
        "weight": 20,
    },
    {
        "name": "three_quarter_cinematic",
        "prompt": (
            "3/4 BODY SHOT from mid-thigh up, face and full upper body visible, "
            "face in upper portion, outfit and power effects fully readable, "
            "one hand extended toward viewer with charging energy or weapon drawn, "
            "cinematic vertical composition with dramatic depth, "
            "background explosion out of focus, character razor-sharp, "
            "natural proportions fully visible, energy corona around entire figure"
        ),
        "weight": 25,
    },
    {
        "name": "three_quarter_portrait",
        "prompt": (
            "3/4 BODY elegant power portrait, waist-to-top composition showing full face and torso, "
            "slight side angle showing depth and figure with aura emanating, "
            "face upper third, detailed outfit middle, massive power effects filling background, "
            "one arm at side one extended or weapon resting with energy crackling, "
            "dramatic cinematic split lighting with colored neon and power glow, vertical format"
        ),
        "weight": 20,
    },
    {
        "name": "back_view_dramatic",
        "prompt": (
            "DRAMATIC BACK VIEW full body, character facing destroyed cyberpunk city below, "
            "hair and cloak flowing wild in massive power release wind, "
            "face turned 3/4 showing profile or slight side view, "
            "outfit and powerful silhouette breathtaking from behind with aura corona, "
            "weapon or technique deployed upward into sky, "
            "neon city sprawl far below surrounded by their impact, viewer behind witnessing apex"
        ),
        "weight": 10,
    },
]

# ══════════════════════════════════════════════════════════════════════
# CHANNEL IDENTITY & LOCKS — v43.0 UPGRADED
# ══════════════════════════════════════════════════════════════════════
CHANNEL_IDENTITY = (
    "DJ Dark Mark viral trap phonk anime visual, ULTIMATE premium cyberpunk anime key visual, "
    "scroll-stopping viral YouTube Shorts thumbnail, cyberpunk neon world aesthetic at maximum intensity, "
    "professional music channel art that stops scrolling dead, "
    "jaw-dropping anime visual that demands a second look"
)

CORE_CHARACTER = (
    "one anime character with iconic design, clearly anime artstyle proportions, "
    "beautiful detailed anime character face with hypnotic neon-lit eyes, "
    "expressive detailed face with emotion reading clear from distance, "
    "detailed hair with individual strand rendering catching neon light, "
    "full signature outfit with all details and power effects, "
    "alone in frame, single character commanding entire composition"
)

STYLE_LOCK = (
    "PREMIUM cyberpunk anime key visual art at maximum quality, "
    "ultra-clean sharp detailed lineart with professional finish, "
    "high-end 2D anime illustration style pushing quality ceiling, "
    "polished cel shading with multi-source rim lighting setup, "
    "cinematic neon and power-effect lighting simultaneously, "
    "glossy hyper-detailed eyes with five or more catchlights, "
    "rich maximally saturated neon colors with extreme contrast shadows, "
    "professional music cover art quality finish + MASSIVE particle system, "
    "NOT photorealistic, NOT 3d render, pure anime illustration style at its apex"
)

CYBERPUNK_LIGHTING = (
    "CINEMATIC MAXIMUM cyberpunk lighting stack: "
    "primary colored rim light splitting hard from behind creating luminous silhouette edge, "
    "contrasting secondary neon fill light modeling face and body volume, "
    "neon color reflections pooling and shimmering on skin and costume surfaces, "
    "volumetric god rays cutting through smoke and particle atmosphere, "
    "power effect glow illuminating character from below and within, "
    "eyes internally lit with multiple colored neon catchlight reflections"
)

MOTION_LOCK = (
    "MAXIMUM sense of movement and explosive power: "
    "hair caught mid-explosion in technique wind, "
    "dense floating neon energy particles in thousands filling air, "
    "speed blur streaks showing trajectory, "
    "impact shockwave rings visible in atmosphere, "
    "glowing energy crackles rippling off every surface near character, "
    "dynamic composition where everything is alive and moving, "
    "neon bokeh orbs in hundreds softly glowing throughout background depth, "
    "debris and rubble frozen mid-air from shockwave impact"
)

VIRAL_HOOK_LOCK = (
    "ONE UNFORGETTABLE visual hook dominating composition: "
    "massive glowing energy technique erupting around body OR "
    "dramatic power aura expanding in all directions OR "
    "beautiful emotional expression lit by own power glow OR "
    "hair and outfit exploding dramatically in technique wind OR "
    "maximum power charging with reality-distortion light effects OR "
    "intense battle damage increasing power output, "
    "INSTANTLY iconic cyberpunk anime frame you cannot scroll past"
)

QUALITY_LOCK = (
    "MASTERPIECE maximum quality, best possible quality, ultra-hyper detailed rendering, "
    "crisp perfect lineart at professional studio level, "
    "ultra-detailed shining neon and power-lit eyes, "
    "clean correct anatomy and heroic proportions, "
    "high-end channel branding visual quality, "
    "extreme resolution detail on every surface, "
    "premium polished finish with perfect color grading, "
    "beautiful complex neon and power illumination on skin and costume, "
    "MAXIMUM particle density in effects, "
    "compositional mastery placing character for maximum visual impact"
)

# ══════════════════════════════════════════════════════════════════════
# EFEITOS DE PARTÍCULAS E ENERGIA — NOVO v43.0
# ══════════════════════════════════════════════════════════════════════
PARTICLE_EFFECTS = [
    "dense storm of glowing energy shards orbiting entire body like a personal galaxy, thousands of neon particles cascading",
    "massive power aura exploding outward from body pushing atmosphere aside in visible compression rings",
    "crystalline energy lattice forming and shattering around figure continuously as power fluctuates at limit",
    "rivers of plasma energy flowing upward from ground through body and launching skyward from fingertips",
    "shockwave rings expanding concentrically from impact point glowing neon at each compression wave",
    "lightning web crackling across entire frame connecting every surface to character as epicenter",
    "dimensional crack tears in reality opening behind character revealing inverse neon space",
    "swirling vortex of elemental power condensing toward character from all directions at once",
    "hundreds of floating debris pieces frozen in telekinetic field each casting individual neon shadow",
    "technique-specific particles: fire embers, water droplets, shadow fragments, ice crystals, blood mist, all neon-lit",
]

# ══════════════════════════════════════════════════════════════════════
# PALETAS CYBERPUNK — EXPANDIDAS v43.0
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
PALETTE_BLACK_GOLD = (
    "dominant pitch black and blazing gold cyberpunk palette, "
    "absolute darkness punctuated by divine golden neon, "
    "god-tier presence aesthetic, extreme contrast, mythological power color"
)
PALETTE_RED_BLACK = (
    "dominant blood red and black cyberpunk palette, "
    "shadows cut by crimson neon from every angle, "
    "dangerous villain energy, phonk-dark visual violence, "
    "deep saturated shadows against pure red neon"
)

PALETTES = [
    ("teal_pink",    PALETTE_TEAL_PINK,    20),
    ("purple_gold",  PALETTE_PURPLE_GOLD,  20),
    ("crimson_blue", PALETTE_CRIMSON_BLUE, 20),
    ("green_orange", PALETTE_GREEN_ORANGE, 10),
    ("white_blue",   PALETTE_WHITE_BLUE,   10),
    ("black_gold",   PALETTE_BLACK_GOLD,   10),
    ("red_black",    PALETTE_RED_BLACK,    10),
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
    "phonk":      "phonk cyberpunk atmosphere, heavy bass visual energy in pose, aggressive confident street aesthetic, dark neon underground feeling, maximum attitude in every pixel",
    "trap":       "trap cyberpunk atmosphere, urban night neon energy in stance, stylish supreme confidence, warm neon street premium look, flexing power like currency",
    "electronic": "electronic cyberpunk atmosphere, futuristic digital energy surrounding body, teal data streams, clean cyber rhythm visual pulse, frequency visualization in air",
    "darkpop":    "dark pop cyberpunk emotional atmosphere, romantic sadness in neon city, cinematic emotional beauty, warm-cold color story, power and vulnerability in single frame",
    "dark":       "dark cyberpunk atmosphere, dramatic neon shadow play on body, intense emotional presence, single accent neon in near-darkness, depth of shadow as character",
    "rock":       "rock cyberpunk energy, electric concert neon on stage, raw emotional power in body language, dramatic rim neon, performance energy, amp feedback visible as wave",
    "default":    "dark cyberpunk atmosphere, emotional anime beauty, cinematic neon contrast on full body, premium viral Shorts visual quality, maximum energy in every detail",
}

# ══════════════════════════════════════════════════════════════════════
# POSES DINÂMICAS
# ══════════════════════════════════════════════════════════════════════
POWER_POSES = [
    "standing with weapon raised overhead releasing massive energy burst toward sky, dominance apex pose",
    "mid-leap attack pose with full body technique deployed, energy trailing behind entire body",
    "arms spread wide with power aura erupting outward from chest in expanding ring, epicenter pose",
    "one hand extended toward viewer with technique fully charged and releasing, impact imminent",
    "crouching maximum-power ready-stance with eyes locked forward, coiled godlike power",
    "back slightly turned looking over shoulder with terrifying intensity, most dangerous elegance",
    "slow walk toward camera with absolute authority, neon city on fire behind, cannot be stopped",
    "sitting on destroyed rooftop legs dangling, casual supreme confidence, city below is rubble from their technique",
    "spinning attack frozen at maximum velocity, hair and energy in perfect spiral galaxy of force",
    "dual weapons or techniques crossed in guard stance, eyes issuing a challenge to the universe",
    "floating mid-air technique fully activated, ground beneath cracked by proximity to power alone",
    "screaming with maximum power release, hair all rising, atmosphere cracking, this is their limit break",
]

BACKGROUND_VARIATIONS = [
    "rainy cyberpunk neon city street level, wet pavement shattered from impact reflecting neon towers, teal and pink bokeh depth",
    "cyberpunk rooftop edge at night, sprawling neon city crumbling far below from technique shockwave, wind and height",
    "dark holographic data server hall partially destroyed by power output, glowing server stacks receding into darkness",
    "cyberpunk rain-soaked alley with blurred neon kanji signs overhead, steam vents, walls cracking from presence",
    "night cyberpunk skyline from above with flying vehicles scrambling and massive neon ad screens going dark",
    "underground neon fight club obliterated, crowd blur and laser beams and smoke atmosphere aftermath",
    "cyberpunk research lab with holographic screens shattered, experiments disrupted by power output",
    "dark concert main stage mid-destruction with neon light beams and smoke and crowd below frozen in awe",
    "pure void black with single strong neon rim split and maximum floating particle field like a personal universe",
    "cyberpunk night market obliterated, warm amber vendor neon tilted and teal sky, slow motion debris field",
    "abandoned cyberpunk shrine with broken torii now glowing neon from absorbed technique energy, rain and moss and destruction",
    "floating cyberpunk highway overpass crumbling, cars crushed below, wind and neon and structural failure",
    "exterior of Nazarick dungeon, ancient dark stone, magical torch neon, sky of a different world entirely",
    "endless shadow realm with warrior silhouettes, dimension between dimensions, pure power given space",
]

MUSIC_ELEMENTS = [
    "cyberpunk headphones around neck glowing neon, music and battle rhythm synchronized",
    "wireless neon earbud catching neon light, the music is why they fight",
    "subtle holographic music waveform pulsing in background in sync with power output",
    "their emotion IS the music element, cinematic cyberpunk anime body language speaks louder than words",
    "neon music visualizer frequency bars orbiting body responding to power level",
    "microphone silhouette in blurred neon background depth, this is the stage",
]

# ══════════════════════════════════════════════════════════════════════
# NEGATIVE PROMPT — v43.0
# ══════════════════════════════════════════════════════════════════════
NEGATIVE_PROMPT = (
    "ugly, bad anatomy, bad face, distorted face, asymmetrical eyes, "
    "bad hands, extra fingers, missing fingers, fused limbs, broken limbs, "
    "floating limbs, disconnected body parts, long neck, disfigured, mutated, "
    "melted face, uncanny valley, bad proportions, deformed body, "
    "blurry, low quality, jpeg artifacts, heavy noise, flat boring image, "
    "photorealistic, real photograph, real person, 3d render, CGI, doll, plastic skin, "
    "western cartoon style, simple cartoon, childish art style, "
    "nude, explicit nudity, nipples, genitalia, sexual act, pornographic content, "
    "multiple characters, crowd, two people in frame, duplicate character, "
    "text overlay, words in image, logo watermark, signature, letters in image, "
    "face too small to see, character too tiny in frame, lost in background, "
    "excessive busy overload drowning character, washed out overexposed bloom, "
    "muddy colors, desaturated, low contrast, boring flat lighting, no neon, dull lifeless, "
    "cropped body weirdly, floating head, missing lower body, cut off limbs, "
    "generic background, stock photo energy, corporate safe, soulless composition"
)

GENERATION_SUFFIX = (
    ", beautiful expressive anime character, full body or 3/4 body visible, "
    "detailed costume and iconic design elements, "
    "maximum neon and power-effect lighting on complete figure, "
    "clear powerful silhouette, dynamic alive explosive cyberpunk frame, "
    "polished professional anime art, gorgeous full-body neon and energy illumination, "
    "dense particle system, massive power effect, "
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
    key = f"{style}|{filename}|{short_num}|darkmark_v43.0_ultimate"
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
        return "haunted neon night emotion, lonely but powerful, eyes carrying darkness visible in full body language, shadow particles dense"
    if any(w in clean for w in ["fire", "burn", "rage", "fury", "angry"]):
        return "intense cyberpunk fire emotion, contained rage expressed through full body stance, electric passionate power, flame particles erupting"
    if any(w in clean for w in ["love", "heart", "amor", "coracao", "rose", "cherry"]):
        return "dark cyberpunk romantic emotion, longing in full pose and expression, beautiful bittersweet full-body mood, rose petal particles"
    if any(w in clean for w in ["lost", "alone", "lonely", "sozinho", "perdido"]):
        return "deep lonely cyberpunk emotion, isolated figure in neon city, cinematic solitude in body language, single neon light source"
    if any(w in clean for w in ["drive", "speed", "run", "race", "corrida"]):
        return "cyberpunk speed motion energy, body mid-movement with speed blur, wind and neon trailing the figure, velocity particles"
    if any(w in clean for w in ["queen", "king", "boss", "power", "rule", "rei", "rainha"]):
        return "dominant cyberpunk god-tier aura, full body commanding presence, neon crown energy, power pose of absolute authority"
    if any(w in clean for w in ["dream", "sonho", "sleep", "cloud"]):
        return "dreamy floating cyberpunk emotion, body slightly levitating, ethereal neon particles around full figure, soft glow"
    if any(w in clean for w in ["blood", "sangue", "war", "guerra", "battle", "fight"]):
        return "battle-worn intense cyberpunk emotion, exhausted and powerful, scars glowing neon, power rising from damage"
    return "emotion matching the music carried in full body pose and expression, cyberpunk magnetic presence, particle density matching intensity"


# ══════════════════════════════════════════════════════════════════════
# PROMPT PRINCIPAL — v43.0 ULTIMATE CYBERPUNK EDITION
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

    # Seleciona personagem aleatório dos 200
    char = rng.choice(TREND_WAIFUS)

    # Composição
    if force_back:
        composition = next(c for c in COMPOSITION_STYLES if c["name"] == "back_view_dramatic")
    elif force_full_body:
        composition = next(c for c in COMPOSITION_STYLES if c["name"] == "full_body_power")
    else:
        composition = _weighted_composition(rng)

    # Pose dinâmica e efeitos
    pose = rng.choice(POWER_POSES)
    particle_fx = rng.choice(PARTICLE_EFFECTS)
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
        f"particle effects: {particle_fx}, "
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
        "beautiful cyberpunk anime character with MAXIMUM power and particle effects, "
        "emotional body language that tells the entire story in one frame, "
        "stunning neon and energy illumination across entire figure, "
        "gorgeous cinematic full-body quality at absolute apex, "
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
    variant = random.randint(0, 199)
    output_path = str(Path(output_dir) / f"{style}_bg_{variant:03d}.png")
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
            output_path = str(Path(output_dir) / f"{style}_bg_{v:03d}.png")
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
        description="AI Image Generator — DJ DARK MARK v43.0 Ultimate Cyberpunk Edition"
    )
    parser.add_argument("--style",             default="phonk",
                        help="Gênero: phonk, trap, electronic, dark, darkpop, rock")
    parser.add_argument("--filename",          default="dark phonk.mp3",
                        help="Nome da música (muda o mood do prompt)")
    parser.add_argument("--short-num",         type=int, default=1,
                        help="Número do short (varia seed e personagem)")
    parser.add_argument("--output",            default="assets/background.png")
    parser.add_argument("--force-teal-pink",   action="store_true")
    parser.add_argument("--force-purple-gold", action="store_true")
    parser.add_argument("--force-crimson-blue",action="store_true")
    parser.add_argument("--back",              action="store_true",
                        help="Força vista de costas dramática")
    parser.add_argument("--full-body",         action="store_true",
                        help="Força composição de corpo inteiro")
    parser.add_argument("--prompt-only",       action="store_true",
                        help="Só imprime o prompt, não gera imagem")
    parser.add_argument("--list-chars",        action="store_true",
                        help="Lista todos os 200 personagens disponíveis")
    args = parser.parse_args()

    if args.list_chars:
        print(f"=== {len(TREND_WAIFUS)} PERSONAGENS DISPONÍVEIS ===")
        for i, char in enumerate(TREND_WAIFUS, 1):
            print(f"{i:3d}. {char[:80]}...")
        exit(0)

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
        print("=== PROMPT v43.0 ULTIMATE CYBERPUNK ===")
        print(prompt)
        print(f"\n=== TOTAL DE PERSONAGENS: {len(TREND_WAIFUS)} ===")
        print("\n=== NEGATIVE PROMPT ===")
        print(NEGATIVE_PROMPT)
    else:
        generate_image(prompt, args.output)
