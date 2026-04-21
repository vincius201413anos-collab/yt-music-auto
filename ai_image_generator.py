"""
ai_image_generator.py — Geração de imagem IA cinematográfica por gênero.
Foco: qualidade visual premium, variedade real, anti-repetição, anti-shadowban.
Inspirado em: anime key visual, lofi aesthetic, cyberpunk illustration, dark fantasy art.
"""

import os
import re
import time
import random
import hashlib
import requests
from pathlib import Path

import replicate
import anthropic

SAVE_DIR = Path("temp")
MAX_TRIES = 3

_anthropic_client: anthropic.Anthropic | None = None


def get_anthropic_client() -> anthropic.Anthropic:
    global _anthropic_client
    if _anthropic_client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY nao configurado.")
        _anthropic_client = anthropic.Anthropic(api_key=api_key)
    return _anthropic_client


def get_anthropic_model() -> str:
    return os.getenv("ANTHROPIC_MODEL", "claude-opus-4-5")


# ══════════════════════════════════════════════════════════════════════
# PALETAS DE COR POR GÊNERO
# ══════════════════════════════════════════════════════════════════════

GENRE_COLOR_PALETTES = {
    "lofi": [
        "warm amber and deep navy, soft orange lamp glow, cool moonlight blue",
        "dusty rose and muted teal, vintage film grain colors, warm candlelight",
        "golden hour orange bleeding into night purple, nostalgic warm tones",
        "soft coral and slate blue, cozy interior warmth against cold window night",
        "burnt sienna and midnight blue, lo-fi grainy warmth",
    ],
    "phonk": [
        "deep red neon and pitch black, single harsh light source, high contrast",
        "cold purple-blue and charcoal, wet concrete reflections, urban night",
        "orange sodium vapor and deep shadow, industrial noir palette",
        "crimson slash of light on black, nothing wasted, pure contrast",
        "magenta neon bleed on dark street, color as violence",
    ],
    "trap": [
        "ice blue moonlight and gold accent, luxury cold palette",
        "deep black with champagne gold highlights, penthouse night",
        "purple twilight and silver chrome, elevated urban cool",
        "navy and rose gold, modern luxury at altitude",
        "white marble and midnight blue, clean expensive contrast",
    ],
    "dark": [
        "desaturated grey with single red accent, manga horror palette",
        "deep violet and silver moonlight, gothic beauty",
        "black and blood crimson, stark and violent contrast",
        "ash grey and glowing purple, supernatural atmosphere",
        "pitch black with barely-there blue light, silence made visual",
    ],
    "electronic": [
        "electric cyan and deep magenta, rave light sculpture",
        "holographic rainbow on black, future nightclub",
        "UV purple and neon green, warehouse rave palette",
        "laser white and chromatic aberration, techno cathedral",
        "strobing blue and orange, festival stage energy",
    ],
    "rock": [
        "amber stage light and deep shadow, live show drama",
        "red and white harsh spotlights, concert energy",
        "industrial grey with warm backlight, raw venue",
        "orange ember tones and dark smoke, rock atmosphere",
        "cool blue and burning orange split light, dramatic duality",
    ],
    "metal": [
        "volcanic orange and ash black, apocalyptic",
        "deep crimson and charcoal, brutal contrast",
        "cold silver lightning and black storm, power palette",
        "ember glow and total darkness, hellscape",
        "ice blue moonlight on black stone, ancient evil",
    ],
    "indie": [
        "golden hour warmth, long soft shadows, natural magic",
        "overcast diffused light, muted earth tones, honest beauty",
        "late afternoon amber, dust in sunbeams, nostalgic",
        "dusk gradient from salmon to deep purple, magic hour",
        "soft morning grey with single warm light, quiet poetry",
    ],
    "cinematic": [
        "teal and orange cinematic grade, film color science",
        "desaturated with golden highlights, epic scope palette",
        "cold exterior and warm interior, dramatic contrast",
        "deep shadows and luminous highlights, chiaroscuro",
        "fog-diffused grey with single brilliant light source",
    ],
    "funk": [
        "warm orange and deep red, soulful heat palette",
        "electric yellow and purple, groove energy",
        "sunset coral and teal, vibrant and alive",
        "gold and deep brown, rich warm richness",
        "neon magenta and warm amber, night energy",
    ],
    "default": [
        "neon purple and deep black, atmospheric and moody",
        "cold blue and warm gold, cinematic contrast",
        "deep teal and rose, editorial beauty",
        "steel grey and electric blue, urban poetry",
        "midnight navy and silver, quiet power",
    ],
}

# ══════════════════════════════════════════════════════════════════════
# COMPOSIÇÕES VISUAIS POR GÊNERO
# (variam entre close, meio corpo, plano americano — nunca só full body)
# ══════════════════════════════════════════════════════════════════════

GENRE_COMPOSITIONS = {
    "lofi": [
        # Close emocional — rosto + ambiente atrás
        "close portrait shot, face softly lit by warm desk lamp, headphones around neck, cozy bedroom visible in background with fairy lights and rain-streaked window, intimate and calm",
        # Meio corpo com ambiente rico
        "medium shot from side, girl sitting at wooden desk with headphones on, face turned toward window showing moonlit city, warm lamp on left, books and plants around her, ambient lofi atmosphere",
        # Plano americano — personagem + cenário juntos
        "three-quarter shot, girl cross-legged on bed surrounded by vinyl records and soft pillows, moon visible through tall window, string lights above, warm golden hour interior mood",
        # Quase full mas ambiente domina
        "wide intimate shot, small figure of girl by large window at night, city lights spread below, warm room behind her, shot from inside looking at her silhouette against the city",
        # Close dramático com profundidade
        "close-up face shot, girl looking up with dreamy half-closed eyes, soft bokeh of fairy lights in background, warm amber from one side, cool blue window light from other",
        # Perspectiva de cima
        "overhead close shot, girl lying on bed looking up at viewer, headphones on, polaroids and sketchbooks around her, warm lamp casting long shadows",
        # Perfil com janela
        "side profile close shot, girl's face in perfect profile looking out rain-streaked window, city a soft blur of amber lights behind glass, single warm lamp rim lighting her features",
        # Personagem de costas olhando cidade
        "shot from behind at medium distance, girl at open window overlooking night city, headphones on, cozy room behind her, city lights spread to horizon, atmospheric depth",
    ],
    "phonk": [
        # Rosto frio e direto
        "extreme close portrait, cold expressionless face, single red neon slash of light across eyes, everything else near-black, high contrast manga-influenced style",
        # Meio corpo com rua atrás
        "medium shot, girl leaning on car in empty parking structure, arms crossed, red neon reflection in wet concrete below, single harsh light from above, cold urban night",
        # Olhos apenas em sombra parcial
        "tight face shot with hood partially covering top half of face, only eyes and below visible, purple neon from out of frame casting color, street visible behind in deep shadow",
        # De costas na rua vazia
        "rear medium shot, girl walking away down empty lit highway at 3am, just her silhouette and the road stretching to vanishing point, one distant red light ahead",
        # Reflexo no carro
        "close shot of girl's face reflected in car window, distorted slightly by glass, city inverted in reflection, cold and detached mood, neon colors smeared",
        # Crouching street level
        "low angle medium shot, girl crouching on concrete barrier, looking directly into camera from above, cold empty parking deck below, harsh sodium light from side",
        # Silhueta no túnel
        "silhouette wide shot, girl standing at tunnel entrance, backlit by distant headlights, her form dark against the approaching light, fog around feet",
        # Close with dramatic shadow
        "close portrait, half her face in total shadow, half lit by intense orange streetlight, expressionless, city a soft blur behind, cinematic and cold",
    ],
    "dark": [
        # Manga close — olhos vermelhos em preto e branco
        "tight manga-style close portrait, black and white with only eyes glowing deep red, black hair falling over face, dark and haunting, high quality manga art style",
        # Meio corpo gótico
        "medium shot, gothic girl in dark environment, dramatic lighting from single candle below her face, stone walls behind, rich shadows, painterly dark fantasy style",
        # Personagem cercada de correntes/sombras
        "medium close shot, girl surrounded by floating dark chains or shadow tendrils, purple energy glow as only light source, dark atmospheric background",
        # Close com olhos brilhantes únicos
        "extreme close face shot, glowing purple eyes against dark background, black hair framing face, minimal light, maximum impact, anime illustration quality",
        # Cena de cemitério / ruína
        "wide atmospheric shot showing small figure in moonlit ruins or cemetery, silver moonlight from above, mist at ground level, dramatic gothic composition",
        # Reflexo na água negra
        "medium shot, girl at edge of dark reflective water, her perfect reflection below, moonlight from directly above, surrounding darkness, mirror symmetry",
        # De baixo para cima — imponente
        "low angle close shot looking up at girl's face, dramatic underlighting in deep purple, her expression serene and overwhelming, background: dark storm sky",
        # Close olho único em destaque
        "extreme close crop of single eye, iris glowing crimson or violet, surrounded by black hair, tear or light reflection in pupil, absolute minimalism and impact",
    ],
    "electronic": [
        # No festival olhando crowd
        "rear shot from stage level, girl looking out over sea of phone lights and crowd, laser beams cutting through fog above, arms slightly raised, festival euphoria",
        # Close com luzes de laser atrás
        "close portrait, face lit by rapidly colored stage lights, ecstatic expression with eyes closed, laser beams and fog visible behind, concert energy",
        # Silhueta no LED wall
        "silhouette medium shot, girl's form against massive LED wall with abstract visuals, only her outline defined, color explosion surrounding the dark shape",
        # Meio corpo em dancefloor
        "medium shot, girl in motion on dancefloor, UV light making outfit glow, crowd a colorful blur behind, caught mid-movement, kinetic energy",
        # Close cyberpunk com elementos holográficos
        "close portrait, cyberpunk aesthetic, holographic light elements reflecting on face, glowing eyes, futuristic club environment visible behind in depth",
        # De cima no festival noturno
        "aerial-feeling wide shot showing figure at center of outdoor festival, LED stage bright core, crowd as ocean around, stars above, the sacred scale",
        # Túnel de luz
        "medium shot, girl walking through corridor of synchronized strobe lights, motion in the lights while she is sharp, tunnel of color",
        # DJ booth close
        "close medium shot, girl at DJ booth, one hand raised, face lit from below by decks, crowd hands visible at edge of frame, in command",
    ],
    "rock": [
        # Close performance — olhos fechados perdida na música
        "close performance shot, girl with eyes closed at microphone, face illuminated by single white spotlight, everything else shadows, pure commitment",
        # Meio corpo com guitarra
        "medium shot, girl with electric guitar, fingers on frets, stage lights behind creating dramatic backlight halo, smoke at floor level",
        # Silhueta no palco contra parede de luz
        "wide silhouette shot, girl's form against wall of concert lights, arms open, crowd at feet as suggestion, massive scale of performance",
        # Close agressivo olhando câmera
        "tight close portrait, intense direct stare into camera, stage lighting harsh from side, sweat, raw and real performance energy",
        # Jump frozen mid-air
        "medium shot catching frozen jump off drum riser, mid-air, stage lights below and behind, crowd movement blur",
        # Backstage íntimo
        "intimate medium shot, girl backstage before show, mirror with lights frame, guitar in hand, quiet moment before chaos",
        # Outdoor show dramático
        "wide atmospheric shot, outdoor stage against stormy sky, lightning in distance, crowd silhouettes, the scale of it all",
        # Meio corpo guitarrista
        "three-quarter shot, guitar solo moment, head thrown back slightly, face caught between pain and joy, spotlight from above",
    ],
    "metal": [
        # Close ritual imponente
        "close portrait, girl looking up at sky or camera, dramatic underlighting, storm or fire behind, absolute power expression",
        # Figura pequena contra cenário épico
        "wide atmospheric shot, small figure on cliff or ruins against massive storm sky with lightning, scale creates awe",
        # Meio corpo com elementos de fogo/cinzas
        "medium shot, girl surrounded by floating embers and ash, fire glow from below, face serene amid chaos, dark warrior energy",
        # Close olhos — poderoso
        "extreme close shot of face, intense unflinching stare, metal band or dark crown at edge of frame, volcanic or storm light",
        # Catedral dark fantasy
        "medium shot in dark cathedral or ancient ruins, candle light creating long shadows, figure commanding the space, gothic scale",
        # Silhueta com trovão
        "silhouette wide shot, figure atop high point, multiple lightning strikes behind and around, storm framing the power",
        # De baixo dramático
        "extreme low angle medium shot, looking up at standing figure, fire or storm above, she fills the frame with force",
        # Warrior descending
        "dramatic medium shot from below, girl descending dark stone steps, cloak or dark fabric in motion, ancient stronghold behind",
    ],
    "trap": [
        # Penthouse view
        "medium shot at penthouse window, girl looking at camera with city grid behind through floor-to-ceiling glass, night luxury, cool and composed",
        # Close premium — ice cold expression
        "close portrait, cold composed expression, city blurred behind large window at night, gold and navy color palette, premium editorial aesthetic",
        # Reflexo no vidro
        "medium shot, girl's reflection in dark glass overlaid with city lights, double image effect, cool and expensive visual",
        # Vista de cima da cidade
        "wide elevated shot, small figure at rooftop railing, entire city grid below at night, scale of wealth and altitude",
        # Close de perfil — aristocrático
        "side profile close portrait, perfect jaw and neck line, city light from window grazing cheekbone, blue-black night palette, fashion editorial",
        # Chuva no carro
        "intimate medium shot, girl in backseat of luxury car at night, rain on windows, city lights blurred through water on glass, private world",
        # Espelho de banheiro
        "close medium shot, girl at bathroom mirror, reflection shows the room behind, warm bathroom light surrounded by cool night visible through window",
        # Telhado com heliporto
        "wide nighttime shot, girl standing on empty rooftop helipad, city sprawl in all directions below, wind implied, freedom at altitude",
    ],
    "indie": [
        # Golden hour field
        "medium close shot, girl in golden hour light, sun low and warm, natural environment soft behind, eyes catching light, genuine unposed beauty",
        # Janela de café
        "close shot, girl at café window looking out at rainy street, warm interior behind, cold wet outside, cup of something warm nearby, melancholy comfort",
        # Rooftop garden at dusk
        "medium shot, girl on rooftop garden at dusk, city soft behind, wildflowers in broken concrete around her, sky transitioning from orange to blue",
        # Driving shot
        "intimate medium shot from passenger seat, girl at wheel or beside, window showing moving scenery, late afternoon light, road trip feeling",
        # Film photo aesthetic
        "close portrait with film photography aesthetic, slight overexposure, warm grain, genuine expression, natural outdoor light, honest and real",
        # Empty train
        "medium shot on empty train car, girl looking out window at passing landscape, orange seat, afternoon light through glass, solitude as peace",
        # Field at golden hour
        "wide medium shot, figure alone in field of tall grass or sunflowers, late afternoon sun turning everything gold, arms slightly out, presence",
        # Abandoned greenhouse
        "atmospheric medium shot, girl among overgrown plants in abandoned greenhouse, afternoon light through broken glass, green and gold, life reclaiming",
    ],
    "cinematic": [
        # Epic landscape tiny figure
        "wide cinematic shot, tiny figure against vast dramatic landscape — cliff, ocean, storm sky, the scale creating emotion",
        # Close with epic depth of field
        "close portrait with extreme cinematic depth of field, face sharp, epic environment suggested softly behind, anamorphic lens quality",
        # Fog composition
        "medium atmospheric shot, figure walking through deep fog, single light source ahead, the unknown as subject, film noir quality",
        # Rain scene
        "close medium shot in rain, girl facing rain rather than sheltering from it, city or dramatic landscape behind, acceptance as power",
        # Silhouette against impossible sky
        "wide silhouette shot, figure against sky with impossible lighting — double sunset, storm break, eclipse — the sky as painting",
        # Long corridor
        "perspective medium shot, figure at end of long corridor of light, architectural drama, single vanishing point, approaching or leaving",
        # Reflection shot
        "split composition, upper half figure, lower half perfect reflection in water or glass, abstract and beautiful",
        # Through window from outside
        "exterior medium shot looking through window at interior, warm light inside framing figure, cold night outside, separation and intimacy",
    ],
    "funk": [
        # Vibrant street
        "medium close shot, girl in vibrant lit street environment, warm orange and yellow neon, expressive joyful energy, night street life around her",
        # Dance floor
        "medium shot on dancefloor, caught mid-movement, warm colored stage lights, crowd energy around but she is the subject",
        # Close portrait with warmth
        "close portrait, warm orange-gold lighting from side, natural expressive face, groove and soul in the expression, rich background",
        # Street music scene
        "medium atmospheric shot, outdoor music scene, warm night air, string lights above, authentic community energy",
        # Performance close
        "close performance shot, singing or dancing, warm spotlight, genuine joy, expressive and alive",
        # Rooftop at sunset
        "medium shot, sunset rooftop, city warm below, girl bathed in last golden light, free and vibrant",
        # Night market
        "atmospheric medium shot, night market behind, colored vendor lights, warm bustling energy, she is calm center of motion",
        # Close with golden bokeh
        "close portrait, golden bokeh lights filling background from bokeh of city or venue lights, face warm and luminous",
    ],
    "default": [
        "close portrait with dramatic single light source, expressive face, atmospheric background in soft focus, cinematic quality",
        "medium shot with strong environmental storytelling, character and place equally important, moody and intentional",
        "wide atmospheric shot placing small figure against significant environment, scale creates emotional resonance",
        "tight medium shot, editorial composition, strong color palette, character commanding the frame",
        "close portrait, beautiful lighting, rich detailed background in deep focus, premium illustration quality",
        "silhouette medium shot against dramatic sky or light source, form and mood over detail",
        "three-quarter medium shot with interesting environment, depth and story in every corner",
        "close atmospheric shot, character partially in shadow, mystery and depth, invitation to look closer",
    ],
}

# ══════════════════════════════════════════════════════════════════════
# PERSONAGENS — VARIADAS, ADULTAS, ANIME
# ══════════════════════════════════════════════════════════════════════

CHARACTERS = {
    "lofi": [
        "young adult woman, long dark hair with messy bun, soft tired eyes with warmth in them, natural face, oversized university sweater, headphones around neck",
        "young adult woman, auburn wavy hair loose, freckles on nose, half-lidded dreamy eyes, cozy oversized knit, genuine and unposed",
        "young adult woman, short bob dark hair, round glasses slightly askew, soft melancholy expression, vintage band tee and cardigan",
        "young adult woman, long straight black hair parted center, peaceful closed-eye expression, big soft hoodie, headphones on",
        "young adult woman, silver-dyed short hair, nose piercing, tired but content expression, large cream sweater",
        "young adult woman, natural afro loosely contained, warm brown eyes, genuine soft smile, plaid oversized shirt",
        "young adult woman, twin braids in teal, fair skin with freckles, dreamy upward gaze, knit cardigan with patches",
        "young adult woman, honey-blonde messy hair, half-awake expression, large mug held in both hands, soft comfort aesthetic",
    ],
    "phonk": [
        "young adult woman, straight jet-black hair, sharp bangs, cold empty expression, dark hoodie, face partially shadowed",
        "young adult woman, dark hair in high ponytail, sharp angular features, expressionless commanding gaze, dark jacket",
        "young adult woman, black undercut with long top, pierced brow, controlled neutral expression, dark techwear",
        "young adult woman, long dark hair with one dyed streak, half-lidded unfazed eyes, oversized dark parka",
        "young adult woman, platinum short hair with dark roots, cool ice-grey eyes, blank intimidating expression, dark fitted jacket",
        "young adult woman, black braids, sharp cheekbones, slow confident smirk, dark hood partially up",
        "young adult woman, dark hair in space buns, face shadowed by hood, glimpse of intense eyes visible",
        "young adult woman, natural dark curls, deep brown eyes with quiet menace, dark bomber jacket, arms crossed",
    ],
    "dark": [
        "young adult woman, long straight black hair, glowing red eyes, pale skin, black gothic outfit, haunting expressionless stare",
        "young adult woman, black hair with white streak, violet glowing eyes, dark clothing, ethereal and unsettling",
        "young adult woman, black hair partially covering one eye, deep crimson iris visible, pale skin with ink collar tattoo",
        "young adult woman, silver-white hair, hollow sad violet eyes, dark layered clothing, ghost-like translucent quality",
        "young adult woman, ink-black hair, glowing purple irises, fangs at lip edge, dark beauty, gothic anime style",
        "young adult woman, dark teal hair, one red eye one dark eye, expressionless, chains or shadow elements near",
        "young adult woman, very long black hair spreading like ink, pale near-white skin, red eyes, horror beauty",
        "young adult woman, short dark purple hair, glowing eyes like burning embers, pale and luminous skin",
    ],
    "electronic": [
        "young adult woman, midnight blue hair with electric teal streaks, glowing violet eyes, cyberpunk makeup, futuristic fitted outfit",
        "young adult woman, neon pink pixie cut, ecstatic expression, holographic bodysuit, festival ready",
        "young adult woman, silver hair with rainbow prism streaks in light, futuristic features, high-tech fashion",
        "young adult woman, black hair with LED accent lights woven in, sharp cat-eye makeup, cyberpunk aesthetic",
        "young adult woman, bleached white hair, rave-painted face under UV, reflective outfit elements",
        "young adult woman, neon green twin high pigtails, glowing bionic eyes, hacker-punk aesthetic",
        "young adult woman, natural dark hair under laser light creating color, ecstatic eyes-open expression",
        "young adult woman, platinum undercut with long flowing top, chromatic eyes, festival electronic fashion",
    ],
    "rock": [
        "young adult woman, fiery orange-red pixie cut with shaved sides, blazing amber eyes, leather jacket covered in pins",
        "young adult woman, long auburn waves, intense green eyes, sleeveless band shirt, silver rings on every finger",
        "young adult woman, wild dark curly hair, fierce open smile, ripped fishnet, leather jacket",
        "young adult woman, bleached blonde with dark roots, sharp eyeliner, vintage band tee, aggressive energy",
        "young adult woman, short choppy black hair, intense stare, guitar strap visible, stage-worn outfit",
        "young adult woman, long straight dark hair, dramatic winged liner, skinny jeans and leather, performance mode",
        "young adult woman, copper red loose curls, genuine fierce expression, band shirt knotted, boots",
        "young adult woman, shaved sides with long top, silver earrings, muscle shirt, raw rock energy",
    ],
    "metal": [
        "young adult woman, long straight black hair with blood-red underlayer, red heterochromia eye, dark gothic armor-influenced outfit",
        "young adult woman, ice-white long hair, pale cool skin, stoic commanding expression, dark warrior outfit",
        "young adult woman, dark hair with geometric patterns, golden eyes, jeweled accessories, dark warrior queen",
        "young adult woman, wild dark hair, amber warrior eyes, battle-paint aesthetic makeup, dark powerful outfit",
        "young adult woman, long flowing dark hair, glowing purple eyes, dark cloak, ethereal metal goddess",
        "young adult woman, black hair with electric silver highlights, cold grey eyes, armored dark outfit",
        "young adult woman, ink-black hair in warrior braid, fierce sharp features, dark elaborate outfit",
        "young adult woman, long silver hair, glowing red eyes, pale skin, dark cathedral dress aesthetic",
    ],
    "trap": [
        "young adult woman, sleek black hair in sharp high ponytail, cool composed expression, luxury fashion outfit",
        "young adult woman, long honey-blonde waves, sea-blue eyes, premium streetwear, effortless expensive look",
        "young adult woman, short silver buzz cut, dark skin, sharp avant-garde features, high fashion luxury",
        "young adult woman, black hair with galaxy highlights, flawless dark skin, premium fitted outfit, regal",
        "young adult woman, long rose-gold hair, warm skin, composed elegant expression, tailored luxury fashion",
        "young adult woman, natural black hair slicked back, brown skin, strong jaw, premium monochrome outfit",
        "young adult woman, straight black blunt bob, neutral expression, designer tracksuit, luxury minimal",
        "young adult woman, long wavy dark hair, deep eyes, fitted designer coat, premium street aesthetic",
    ],
    "indie": [
        "young adult woman, long honey-blonde waves, warm sea-blue eyes, vintage slip dress and worn denim jacket",
        "young adult woman, short messy auburn hair, genuine freckled face, wide-leg vintage trousers, knit crop",
        "young adult woman, natural curly dark hair, warm brown skin, sundress with oversized cardigan",
        "young adult woman, long caramel waves, honey eyes, natural authentic expression, linen wide pants and simple tee",
        "young adult woman, copper-red curls, light skin with golden freckles, layered vintage finds",
        "young adult woman, short brown bedhead hair, genuine unposed expression, soft flannel and jeans",
        "young adult woman, long dark hair with natural highlights, bare face beauty, flowing vintage dress",
        "young adult woman, twin braids in natural brown, expressive dark eyes, embroidered jacket, authentic style",
    ],
    "cinematic": [
        "young adult woman, long dark hair in wind, strong composed features, dramatic coat, cinematic presence",
        "young adult woman, short silver hair, cool grey eyes, structured jacket, editorial cinematic look",
        "young adult woman, long flowing auburn hair, green eyes catching light, dramatic cinematic outfit",
        "young adult woman, black hair partially obscuring face, mysterious expression, cinematic dark fashion",
        "young adult woman, blonde hair catching dramatic light, strong jawline, film-quality presence",
        "young adult woman, long braids in motion, warm skin, powerful stance, cinematic warrior-poet energy",
        "young adult woman, dark hair in elegant updo, sharp features, tailored cinematic outfit",
        "young adult woman, natural hair catching wind, brown skin luminous, cinematic wide-angle presence",
    ],
    "funk": [
        "young adult woman, voluminous natural afro with gold pins, deep rich skin, luminous warm expression, vibrant outfit",
        "young adult woman, long box braids with gold thread, warm brown skin, knowing smile, colorful fitted outfit",
        "young adult woman, wild curly natural hair, expressive dark eyes, bright confident energy, fun fashion",
        "young adult woman, short natural twists, warm smile, groove energy in every feature, colorful retro outfit",
        "young adult woman, long flowing hair in warm ombre, medium brown skin, joyful expression, vibrant clothes",
        "young adult woman, big natural curls, freckles, wide genuine smile, colorful expressive style",
        "young adult woman, high puff natural hair, deep skin, eyes full of warmth, retro-funk inspired look",
        "young adult woman, braided crown, warm skin tone, elegant groove, vintage-inspired colorful outfit",
    ],
    "default": [
        "young adult woman, long dark hair, expressive eyes, confident composed expression, stylish dark outfit",
        "young adult woman, medium brown hair, genuine warm eyes, editorial fashion, magnetic presence",
        "young adult woman, short textured hair, strong features, cool confident expression, modern style",
        "young adult woman, flowing hair in wind, mixed features, striking look, atmospheric fashion",
        "young adult woman, natural hair, brown skin, commanding presence, modern editorial aesthetic",
        "young adult woman, blonde highlights, grey eyes, quiet intensity, sophisticated minimal style",
        "young adult woman, dark hair with face-framing pieces, sharp features, cool urban fashion",
        "young adult woman, long waves, warm skin, dreamy expression, layered artistic fashion",
    ],
}

# ══════════════════════════════════════════════════════════════════════
# QUALIDADE E NEGATIVE PROMPT
# ══════════════════════════════════════════════════════════════════════

QUALITY_TAGS = (
    "masterpiece, best quality, highly detailed anime illustration, "
    "professional anime key visual, smooth cel shading, clean lineart, "
    "vibrant colors, cinematic composition, sharp focus on subject, "
    "rich background detail, atmospheric depth, studio-level quality, "
    "trending on pixiv, 9:16 vertical format, single character"
)

NEGATIVE_PROMPT = (
    "photorealistic, hyperrealistic, photography, 3D render, CGI, real human face, "
    "text, watermark, signature, logo, border, frame, "
    "multiple characters, extra limbs, deformed hands, fused fingers, bad anatomy, "
    "distorted face, wrong proportions, malformed body parts, "
    "child appearance, young teen face, childlike proportions, "
    "explicit nudity, fetish content, inappropriate content, "
    "blurry, muddy colors, flat boring lighting, "
    "generic gradient background, plain studio void, "
    "airbrushed plastic skin, uncanny valley, "
    "Western cartoon, Pixar style, chibi, super deformed, "
    "sketch only, unfinished lineart, low quality"
)


# ══════════════════════════════════════════════════════════════════════
# SELEÇÃO DETERMINÍSTICA (sem repetição entre shorts da mesma música)
# ══════════════════════════════════════════════════════════════════════

def _seed(filename: str, short_num: int) -> int:
    key = f"{filename}|{short_num}|v4"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % (10 ** 9)


def _pick(pool: list, filename: str, short_num: int, offset: int = 0):
    rng = random.Random(_seed(filename, short_num) + offset * 131)
    return rng.choice(pool)


def _clean_song_name(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(r"\[[^\]]*\]|\{[^\}]*\}|\([^\)]*\)", "", name)
    name = re.sub(r"[_\-]+", " ", name).strip().title()
    return name or "Untitled"


def _compact(text: str, max_chars: int = 1400) -> str:
    return re.sub(r"\s+", " ", text).strip()[:max_chars]


# ══════════════════════════════════════════════════════════════════════
# CONSTRUÇÃO DO PROMPT
# ══════════════════════════════════════════════════════════════════════

def build_ai_prompt(style: str, filename: str, styles: list, short_num: int = 1) -> str:
    song_name = _clean_song_name(filename)

    character = _pick(CHARACTERS.get(style, CHARACTERS["default"]), filename, short_num, 0)
    composition = _pick(GENRE_COMPOSITIONS.get(style, GENRE_COMPOSITIONS["default"]), filename, short_num, 1)
    palette = _pick(GENRE_COLOR_PALETTES.get(style, GENRE_COLOR_PALETTES["default"]), filename, short_num, 2)
    all_styles = ", ".join(s.title() for s in styles) if styles else style.title()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            return _claude_prompt(
                song_name=song_name,
                style=style,
                all_styles=all_styles,
                character=character,
                composition=composition,
                palette=palette,
                short_num=short_num,
            )
        except Exception as e:
            print(f"  [Claude] Prompt falhou: {e} — usando fallback")

    return _static_prompt(character, composition, palette)


def _claude_prompt(
    song_name: str,
    style: str,
    all_styles: str,
    character: str,
    composition: str,
    palette: str,
    short_num: int,
) -> str:
    client = get_anthropic_client()

    system = (
        "You are an elite anime art director creating scroll-stopping YouTube Shorts thumbnails. "
        "Your prompts generate cinematic, emotionally resonant anime illustrations "
        "inspired by the best of pixiv, lofi aesthetic art, cyberpunk manga, and dark fantasy illustration. "
        "\n\nCRITICAL RULES:"
        "\n- ONE adult anime woman (18+), never children"
        "\n- Composition can be: close portrait, medium shot, three-quarter, or wide — choose what serves the mood best"
        "\n- NO full body requirement — faces and partial figures are often MORE powerful"
        "\n- 9:16 vertical format"
        "\n- Background is as important as the character — rich, detailed environments"
        "\n- Platform safe, no explicit content"
        "\n- Output ONLY the prompt: comma-separated descriptors, 90-130 words, no explanations"
    )

    user = f"""Create a premium anime illustration prompt for a music YouTube Short.

SONG: "{song_name}"
GENRE: {style} ({all_styles})
SHORT NUMBER: {short_num} of 5 (must be visually different from other shorts)

CHARACTER:
{character}

COMPOSITION DIRECTION:
{composition}

COLOR PALETTE:
{palette}

REQUIREMENTS:
- Emotionally resonant, matches the {style} mood
- Rich detailed background with atmospheric depth
- Cinematic lighting quality
- The expression on her face should tell a story
- Make someone STOP scrolling when they see this
- 90-130 words total, comma-separated"""

    resp = client.messages.create(
        model=get_anthropic_model(),
        max_tokens=350,
        system=system,
        messages=[{"role": "user", "content": user}],
    )

    raw = resp.content[0].text.strip().strip('"').strip("'")
    full = f"{raw}, {QUALITY_TAGS}"
    print(f"  [Claude] Prompt gerado ({len(full)} chars) short #{short_num}")
    return _compact(full)


def _static_prompt(character: str, composition: str, palette: str) -> str:
    prompt = (
        f"masterpiece, best quality, premium anime illustration, highly detailed, "
        f"{character}, "
        f"{composition}, "
        f"color palette: {palette}, "
        f"cinematic lighting, atmospheric depth, rich background detail, "
        f"clean anime lineart, smooth shading, vibrant saturated colors, "
        f"9:16 vertical composition, single character, "
        f"scroll-stopping visual quality, pixiv trending style"
    )
    return _compact(prompt)


# ══════════════════════════════════════════════════════════════════════
# GERAÇÃO VIA REPLICATE
# ══════════════════════════════════════════════════════════════════════

REPLICATE_MODELS = [
    "black-forest-labs/flux-dev",
    "black-forest-labs/flux-schnell",
]

MODEL_PARAMS = {
    "black-forest-labs/flux-dev": {
        "num_inference_steps": 30,
        "aspect_ratio": "9:16",
        "guidance": 3.5,
        "output_format": "png",
        "output_quality": 95,
        "disable_safety_checker": True,
    },
    "black-forest-labs/flux-schnell": {
        "num_inference_steps": 4,
        "aspect_ratio": "9:16",
        "output_format": "png",
        "output_quality": 95,
        "go_fast": True,
        "disable_safety_checker": True,
    },
}


def generate_image(prompt: str, output_path: str | None = None) -> str | None:
    token = os.environ.get("REPLICATE_API_TOKEN")
    if not token:
        print("  [Replicate] Token nao configurado.")
        return None

    os.environ["REPLICATE_API_TOKEN"] = token
    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    full_prompt = _compact(
        prompt + ", anime illustration, NOT photorealistic, NOT 3D, sharp lineart"
    )

    for model in REPLICATE_MODELS:
        params = {**MODEL_PARAMS.get(model, {}), "prompt": full_prompt}
        if "flux-dev" in model:
            params["negative_prompt"] = NEGATIVE_PROMPT

        for attempt in range(1, MAX_TRIES + 1):
            try:
                model_short = model.split("/")[-1]
                print(f"  [Replicate] Tentativa {attempt}/{MAX_TRIES} — {model_short}")
                output = replicate.run(model, input=params)
                url = _extract_url(output)
                if not url:
                    print("  [Replicate] URL nao encontrada")
                    continue
                saved = _download_image(url, output_path)
                if saved:
                    print(f"  [Replicate] Salvo: {saved}")
                    return saved
            except Exception as e:
                wait = 2 ** attempt
                print(f"  [Replicate] Erro: {e}. Aguardando {wait}s...")
                time.sleep(wait)

    print("  [Replicate] Todas tentativas falharam.")
    return None


def _extract_url(output) -> str | None:
    if isinstance(output, str) and output.startswith("http"):
        return output
    if isinstance(output, list) and output:
        first = output[0]
        if hasattr(first, "url"):
            return str(first.url)
        if isinstance(first, str) and first.startswith("http"):
            return first
    try:
        for item in output:
            if hasattr(item, "url"):
                return str(item.url)
            if isinstance(item, str) and item.startswith("http"):
                return item
    except Exception:
        pass
    return None


def _download_image(url: str, output_path: str | None = None) -> str | None:
    try:
        resp = requests.get(url, timeout=90)
        resp.raise_for_status()

        if not output_path:
            output_path = str(SAVE_DIR / f"ai_bg_{int(time.time())}.png")

        with open(output_path, "wb") as f:
            f.write(resp.content)

        size = os.path.getsize(output_path)
        if size < 80_000:
            print(f"  [Replicate] Imagem pequena demais ({size} bytes), descartando")
            os.remove(output_path)
            return None

        return output_path
    except Exception as e:
        print(f"  [Replicate] Download falhou: {e}")
        return None
