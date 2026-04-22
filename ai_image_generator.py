"""
ai_image_generator.py — Geração de imagem IA cinematográfica por gênero.
VERSÃO 2.0 — Cores ultra-vibrantes, prompts únicos por música, anti-repetição máxima.
Inspirado em: anime key visual premium, lofi aesthetic, cyberpunk illustration, dark fantasy art.
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
# PALETAS DE COR POR GÊNERO — Ultra-vibrantes, alto contraste
# ══════════════════════════════════════════════════════════════════════

GENRE_COLOR_PALETTES = {
    "lofi": [
        "warm amber and deep navy, glowing orange desk lamp, cool moonlit blue from window, rich golden shadows",
        "vivid dusty rose and saturated teal, vintage film warmth, deep candlelight honey-orange",
        "intense golden hour orange bleeding into deep violet night, nostalgic warm saturation",
        "rich coral and deep slate blue, cozy interior warmth, electric blue moonlight on glass",
        "burnt sienna and midnight indigo, lo-fi warm grain with glowing amber accents",
        "deep burgundy lamp light and cool cerulean moonlight, high-contrast cozy atmosphere",
        "rich ochre yellow and deep purple shadow, warm vintage warmth with cool night contrast",
    ],
    "phonk": [
        "deep crimson neon slicing pitch black, single brutal harsh light, extreme contrast, blood red reflections on wet concrete",
        "cold electric purple-violet and absolute charcoal, neon-wet concrete reflections, hypercontrast urban",
        "burning orange sodium vapor and total shadow, industrial noir, deep blacks with neon orange glow",
        "magenta slash of violent neon on pure black, color as aggression, single saturated streak",
        "electric red and blue split light, both harsh and cold, noir shadow everywhere else",
        "vivid white-blue LED and deep rust shadow, empty parking structure, contrast maxed",
        "neon pink over jet black, aggressive saturation, single color rules everything",
    ],
    "trap": [
        "ice crystal blue moonlight and deep gold, luxury cold palette, rich shadows with warm gold edges",
        "deep velvet black with champagne gold highlights, penthouse at night, premium contrast",
        "electric purple twilight and silver chrome, elevated urban with rich glow",
        "deep navy and luminous rose gold, modern luxury at altitude, vivid warmth against cold blue",
        "white marble luminous and midnight blue deep, clean expensive high-contrast",
        "rich teal and burnished copper gold, premium editorial night",
        "electric indigo and bright silver, cold luxury with vivid depth",
    ],
    "dark": [
        "desaturated silver-grey with single vivid blood crimson accent, stark manga horror contrast",
        "deep jewel violet and cold silver moonlight, gothic beauty, rich purple shadows",
        "jet black and saturated blood red, zero compromise contrast, violence made visual",
        "ash grey with glowing electric purple supernatural energy, ethereal darkness",
        "pitch black with vivid cyan-blue cold light, silence made luminous",
        "deep navy black with vivid violet energy glow, supernatural atmosphere",
        "rich dark teal and sharp crimson, dark fantasy palette with vivid accent",
    ],
    "electronic": [
        "electric cyan and deep magenta, rave light sculpture, vivid complementary clash",
        "holographic rainbow spectrum on deep black, neon-lit future nightclub",
        "UV electric purple and vivid neon green, warehouse rave, vivid as possible",
        "laser white and chromatic aberration rainbow edges, techno cathedral light",
        "strobing electric blue and deep sunset orange, festival stage high energy",
        "vivid teal and hot pink, cyberpunk complementary contrast, maximum saturation",
        "electric lime and deep violet, rave aesthetic, neon against darkness",
    ],
    "rock": [
        "deep amber stage fire and pitch shadow, live show drama, warm against cold",
        "vivid red and cold white harsh spotlights split, concert energy, maximum contrast",
        "industrial warm grey with vivid amber backlight, raw venue glow",
        "rich orange ember tones and deep smoke grey, rock atmosphere with depth",
        "cool electric blue and burning orange split light, dramatic duality maxed",
        "hot white spotlight and deep navy shadow, performance drama",
        "vivid amber and deep purple, rock show warm against night",
    ],
    "metal": [
        "volcanic orange fire and ash black, apocalyptic, vivid destruction",
        "deep crimson and pure charcoal, brutal contrast, nothing wasted",
        "cold lightning white-blue and black storm, power palette, raw electricity",
        "deep amber ember glow and total darkness, vivid hellscape warmth",
        "ice crystal blue moonlight on black stone, ancient evil, cold beauty",
        "vivid electric red and deep shadow grey, intense metal energy",
        "burning orange and cold silver, war palette, vivid and brutal",
    ],
    "indie": [
        "rich golden hour warmth, long soft shadows, natural magic, vivid amber",
        "overcast but rich diffused light, vivid earth tones, honest saturated beauty",
        "late afternoon deep amber, vivid dust in sunbeams, nostalgic warmth",
        "dusk gradient from vivid salmon pink to deep indigo purple, magic hour",
        "soft morning with warm golden light shaft, quiet but vivid poetry",
        "rich green and golden light, nature saturated, late afternoon glow",
        "vivid honey warm and deep burgundy cool, indie atmospheric contrast",
    ],
    "cinematic": [
        "vivid teal and rich orange cinematic grade, film color science maximized",
        "desaturated environment with vivid golden highlights, epic scope palette",
        "cold exterior blue and warm interior amber, dramatic contrast, cinematic split",
        "deep rich shadows and luminous golden highlights, chiaroscuro maximized",
        "fog-diffused atmosphere with single brilliant warm light source against grey",
        "vivid amber and deep blue, classic cinematic split-tone, maximum depth",
        "electric purple atmosphere and golden beam, epic cinematic drama",
    ],
    "funk": [
        "warm deep orange and rich red, soulful heat, vivid and alive",
        "electric yellow and deep purple, groove energy, vivid complementary",
        "sunset vivid coral and deep teal, vibrant alive saturated warmth",
        "deep gold and rich dark brown, soulful warmth, textured richness",
        "neon magenta and warm amber, night energy, vivid as a celebration",
        "vivid orange and electric blue, high energy contrast, groove visual",
        "rich red-orange and deep navy, warm groove against cool night",
    ],
    "default": [
        "vivid neon purple and deep black, atmospheric and moody, maximum saturation",
        "cold electric blue and warm gold, cinematic contrast, vivid split",
        "deep rich teal and vivid rose, editorial beauty, saturated and sharp",
        "steel grey and vivid electric blue, urban poetry, cold and vivid",
        "midnight navy and luminous silver, quiet power, deep contrast",
        "vivid amber and deep indigo, warm cold contrast, cinematic drama",
        "electric cyan and deep burgundy, complementary vivid drama",
    ],
}

# ══════════════════════════════════════════════════════════════════════
# COMPOSIÇÕES VISUAIS POR GÊNERO — Cinematográficas, variadas
# ══════════════════════════════════════════════════════════════════════

GENRE_COMPOSITIONS = {
    "lofi": [
        "close portrait, face softly lit by warm glowing desk lamp, headphones around neck, cozy bedroom with fairy lights and rain-streaked window behind her, intimate and emotionally warm",
        "medium shot from side, girl at wooden desk with headphones on, face turned toward rain-streaked window with moonlit city visible, warm lamp light, books and plants around",
        "three-quarter shot, girl cross-legged on bed surrounded by vinyl records and soft pillows, full moon visible through tall window, string lights creating golden bokeh above",
        "wide intimate shot, small figure of girl by large window at night, city lights spread below, warm room behind, inside looking at her silhouette against glowing city",
        "close-up face shot, girl with dreamy half-closed eyes looking upward, soft bokeh fairy lights behind, warm amber from desk lamp, cool blue moonlight from window side",
        "overhead close shot, girl lying on bed looking up at viewer, headphones on, polaroids and sketchbooks around her, warm lamp casting long shadows across everything",
        "side profile close shot, girl's face in profile looking at rain-streaked window, city blurred amber lights behind glass, single warm lamp rim-lighting her features perfectly",
        "rear medium shot, girl at open window overlooking night city, headphones on, cozy room behind her, entire city lights spread to horizon, atmospheric depth of field",
    ],
    "phonk": [
        "extreme close portrait, cold expressionless face, single blood-red neon slash of light cutting across eyes, everything else near-black, high contrast manga aesthetic",
        "medium shot, girl leaning on car in empty parking structure, arms crossed, red neon reflection in wet concrete below, single harsh fluorescent above, cold urban 3am",
        "tight face shot with hood partially covering, only eyes and below visible, purple neon from out-of-frame casting violet, dark empty street behind in deep shadow",
        "rear medium shot, girl walking away down empty lit highway at 3am, just silhouette and road stretching to vanishing point, single red light ahead in distance",
        "close shot of girl's face reflected in car window, distorted slightly by glass, city inverted in reflection, cold and detached, neon colors bleeding across surface",
        "low angle medium shot, girl crouching on concrete barrier, looking into camera from above, empty parking deck below, harsh sodium light from side, commanding",
        "silhouette wide shot, girl standing at tunnel entrance, backlit by distant headlights, form dark against approaching light, mist curling around feet",
        "close portrait, half face in total shadow, half lit by intense orange streetlight, expressionless, city soft blur behind, cinematic maximum contrast",
    ],
    "dark": [
        "tight manga-style close portrait, black and white with only eyes glowing deep crimson, black hair falling over face, dark and haunting, high-quality manga art style",
        "medium shot, gothic girl in dark stone environment, dramatic single candle from below casting upward shadows, rich darkness everywhere, painterly dark fantasy illustration",
        "medium close shot, girl surrounded by floating dark chains and shadow tendrils, violet energy glow as only light source, rich atmospheric darkness surrounding her",
        "extreme close face shot, glowing purple irises against absolute dark background, black hair framing face, minimal light, maximum emotional impact, premium anime quality",
        "wide atmospheric shot, small figure in moonlit ruins, silver moonlight from directly above, dense mist at ground level, dramatic gothic composition scale",
        "medium shot, girl at edge of dark perfectly reflective water, her mirror reflection below, moonlight directly above, surrounding total darkness, mirror symmetry",
        "low angle close shot looking up at girl's face, dramatic rich purple underlighting, expression serene and overwhelming, background deep storm sky with lightning",
        "extreme close crop of single eye, iris glowing crimson, surrounded by falling black hair, light reflection in pupil, absolute minimalism and emotional impact",
    ],
    "electronic": [
        "rear shot from stage level, girl looking over sea of phone lights and crowd, laser beams cutting fog above, arms slightly raised, festival scale and euphoria",
        "close portrait, face lit by rapidly changing colored stage lights, ecstatic expression eyes closed, laser beams and smoke visible behind, concert energy radiating",
        "silhouette medium shot, girl's form against massive LED wall with abstract vivid visuals, only outline defined, color explosion surrounding the dark shape",
        "medium shot, girl in motion on dancefloor, UV light making everything glow vivid, crowd a blur of color, caught mid-movement, pure kinetic energy",
        "close portrait, cyberpunk aesthetic, holographic light elements reflecting on face, glowing electric eyes, futuristic club visible behind in vivid depth of field",
        "aerial-feeling wide shot, figure at center of outdoor festival, LED stage bright core, crowd ocean around her, stars above, sacred scale and color",
        "medium shot, girl walking through corridor of synchronized strobe lights, motion blur in lights while she is sharp, tunnel of vivid color surrounding her",
        "close medium shot, girl at DJ booth, one hand raised, face lit from below by vivid deck lights, crowd hands at edge of frame, commanding the room",
    ],
    "rock": [
        "close performance shot, girl with eyes closed at microphone, face lit by single white spotlight, everything else deep shadow, pure commitment and raw emotion",
        "medium shot, girl with electric guitar, fingers on frets, vivid stage lights creating dramatic halo backlight, smoke at floor level, rock goddess framing",
        "wide silhouette shot, girl against wall of concert lights, arms open, crowd at feet as suggestion, massive scale of performance, backlit and powerful",
        "tight close portrait, intense direct stare into camera, stage lighting harsh from side, sweat visible, raw and real performance energy, fearless",
        "medium shot catching frozen mid-jump off drum riser, mid-air, stage lights below and behind creating halo, crowd blur surrounding",
        "intimate medium shot, girl backstage before show, lights framing mirror, guitar in hand, quiet moment of power before chaos begins",
        "wide atmospheric shot, outdoor stage against dramatic storm sky, lightning in distance, crowd silhouettes, the epic scale of it all",
        "three-quarter shot, guitar solo moment, head thrown back slightly, face between pain and transcendence, spotlight directly above",
    ],
    "metal": [
        "close portrait, girl looking up at sky, dramatic rich underlighting from fire, storm behind with lightning, absolute power expression, metal goddess energy",
        "wide atmospheric shot, small figure on cliff against massive storm sky with multiple lightning strikes, scale creates overwhelming awe",
        "medium shot, girl surrounded by floating embers and ash, deep fire glow from below, face serene amid chaos, dark warrior energy and beauty",
        "extreme close shot of face, intense unflinching stare forward, volcanic or storm light, cold and commanding, primal force",
        "medium shot in dark gothic cathedral, candle light casting long dramatic shadows, figure commanding the ancient space with presence",
        "silhouette wide shot, figure atop high point, multiple lightning strikes behind and around simultaneously, storm framing the power",
        "extreme low angle medium shot looking up at standing figure, fire or storm above, she fills the frame with overwhelming force",
        "dramatic medium shot from below, girl descending dark stone steps, cloak or dark fabric in motion, ancient stronghold behind her",
    ],
    "trap": [
        "medium shot at penthouse window, girl looking at camera with entire city grid behind through floor-to-ceiling glass, night luxury, cold and composed",
        "close portrait, cold composed expression, city blurred behind large window at night, gold and navy palette, premium editorial fashion aesthetic",
        "medium shot, girl's reflection in dark glass overlaid with city lights, double image effect, cool and expensive, luxury visual",
        "wide elevated shot, small figure at rooftop railing, entire city grid below at night, scale of wealth and altitude, freedom",
        "side profile close portrait, perfect jaw and neck line, city light from window grazing cheekbone, blue-black night palette, fashion editorial power",
        "intimate medium shot, girl in backseat of luxury car at night, rain on windows, city lights blurred through water on glass, private world",
        "close medium shot at mirror, warm bathroom light surrounded by cool night through window, reflection showing the room, composed",
        "wide nighttime shot, girl standing on empty rooftop helipad, city sprawl in all directions below, wind implied, altitude and freedom",
    ],
    "indie": [
        "medium close shot, girl in rich golden hour light, sun low and warm, natural environment soft behind, eyes catching light, genuine unposed beauty",
        "close shot, girl at café window looking at rainy street, warm interior behind, cold wet outside, warm cup in hands, melancholy comfort",
        "medium shot, girl on rooftop garden at dusk, city soft behind, wildflowers in broken concrete, sky transitioning vivid orange to deep blue",
        "intimate medium shot from passenger seat, girl at wheel, window showing moving scenery, late afternoon golden light, road trip feeling",
        "close portrait with film photography aesthetic, slight beautiful overexposure, warm grain, genuine expression, honest natural light",
        "medium shot on empty train car, girl looking out window at passing landscape, afternoon light through glass, solitude as peace",
        "wide medium shot, figure alone in field of tall grass at golden hour, late afternoon sun turning everything vivid gold, arms slightly out",
        "atmospheric medium shot, girl among overgrown plants in abandoned greenhouse, afternoon light through broken glass, life reclaiming beauty",
    ],
    "cinematic": [
        "wide cinematic shot, small figure against vast dramatic landscape — cliff, ocean, storm sky — the scale creating pure emotion",
        "close portrait with extreme cinematic depth of field, face sharp, epic environment behind suggested softly, anamorphic lens quality",
        "medium atmospheric shot, figure walking through deep fog, single light source ahead creating a path, film noir mystery and depth",
        "close medium shot in rain, girl facing the rain rather than sheltering, city or dramatic landscape behind, acceptance as power",
        "wide silhouette against impossible sky — storm break, sunset fire, double horizon — the sky itself a painting",
        "perspective medium shot, figure at end of long corridor of light, architectural drama, single vanishing point, cinematic precision",
        "split composition, upper half figure, lower half perfect mirror reflection in water, abstract and cinematically beautiful",
        "exterior medium shot through window, warm light inside framing figure against cold night outside, separation and intimacy",
    ],
    "funk": [
        "medium close shot, girl in vibrant warm-lit street environment, deep orange and yellow neon, expressive joyful energy, night street life",
        "medium shot on dancefloor, caught mid-movement, warm colored stage lights, crowd energy around but she is the magnetic subject",
        "close portrait, warm deep orange-gold lighting from side, natural expressive face, groove and soul in expression, rich saturated background",
        "medium atmospheric shot, outdoor music scene, warm night air, string lights above, authentic community and joy",
        "close performance shot, singing or dancing, warm spotlight, genuine joy radiating, expressive and totally alive",
        "medium shot, sunset rooftop, city warm below, girl bathed in last vivid golden light, free and vibrant",
        "atmospheric medium shot, night market behind, colored vendor lights, warm bustling energy, she is calm center of motion",
        "close portrait, golden bokeh lights filling background, face warm and luminous, groove feeling in every detail",
    ],
    "default": [
        "close portrait with dramatic single light source, expressive face, atmospheric background in soft focus, cinematic premium quality",
        "medium shot with strong environmental storytelling, character and place equally important, moody and deeply intentional",
        "wide atmospheric shot, small figure against significant environment, scale creates emotional resonance and depth",
        "tight medium shot, editorial composition, strong vivid color palette, character commanding the frame",
        "close portrait, beautiful dramatic lighting, rich detailed background in deep focus, premium illustration quality",
        "silhouette medium shot against dramatic sky or light source, form and mood over detail, powerful",
        "three-quarter medium shot with interesting environment, depth and story in every corner of the frame",
        "close atmospheric shot, character partially in shadow, mystery and depth, invitation to look closer",
    ],
}

# ══════════════════════════════════════════════════════════════════════
# PERSONAGENS — Variadas, adultas, anime premium
# ══════════════════════════════════════════════════════════════════════

CHARACTERS = {
    "lofi": [
        "young adult woman, long dark hair with messy bun and loose strands, soft tired eyes with warmth, natural face with subtle beauty, oversized university sweater, headphones around neck",
        "young adult woman, auburn wavy hair loose and flowing, freckles on nose, half-lidded dreamy eyes, cozy oversized knit sweater, genuine and unposed warmth",
        "young adult woman, short dark bob, round glasses slightly askew, soft melancholy expression with hidden depth, vintage band tee and open cardigan",
        "young adult woman, long straight black hair parted center, peaceful closed-eye expression, big soft hoodie, large headphones on head, serene",
        "young adult woman, silver-dyed short hair with natural texture, small nose piercing, tired but content expression, large cream sweater",
        "young adult woman, natural afro loosely contained with pins, warm brown eyes full of soul, genuine soft smile, plaid oversized shirt",
        "young adult woman, twin braids dyed teal at tips, fair skin with freckles, dreamy upward gaze, knit cardigan with small patches",
        "young adult woman, honey-blonde messy hair, half-awake expression of comfort, large mug held in both hands, soft aesthetic warmth",
    ],
    "phonk": [
        "young adult woman, straight jet-black hair, sharp bangs perfectly cut, cold empty expression, dark oversized hoodie, face partially in shadow",
        "young adult woman, dark hair in tight high ponytail, sharp angular features, expressionless commanding gaze, dark fitted jacket, controlled",
        "young adult woman, black undercut with long flowing top, pierced brow, controlled neutral expression, dark fitted techwear jacket",
        "young adult woman, long dark hair with one dyed white streak, half-lidded unfazed eyes, oversized dark parka with hood down",
        "young adult woman, platinum short hair with dark roots showing, cool ice-grey eyes, blank intimidating expression, dark fitted jacket",
        "young adult woman, long black braids, sharp defined cheekbones, slow confident smirk, dark hood partially pulled up",
        "young adult woman, dark hair in space buns, face partially shadowed by hood, glimpse of intense piercing eyes visible",
        "young adult woman, natural dark curls, deep brown eyes with quiet menace, dark bomber jacket, arms crossed, immovable",
    ],
    "dark": [
        "young adult woman, long straight black hair, glowing crimson eyes, pale porcelain skin, dark gothic outfit, haunting expressionless stare",
        "young adult woman, black hair with silver-white streak, violet glowing eyes, dark layered clothing, ethereal and unsettling beauty",
        "young adult woman, black hair partially covering one eye, deep crimson iris visible, pale skin with dark ink collar marking",
        "young adult woman, silver-white hair, hollow sad violet eyes, dark layered clothing, ghost-like luminous quality",
        "young adult woman, ink-black hair, glowing purple irises, fangs at lip edge, dark beauty, premium gothic anime style",
        "young adult woman, dark teal hair, one red eye one dark eye heterochromia, expressionless, shadow elements surrounding",
        "young adult woman, very long black hair spreading like ink around her, pale near-white skin, crimson eyes, horror beauty",
        "young adult woman, short dark purple hair, eyes like burning violet embers, pale luminous skin, supernatural presence",
    ],
    "electronic": [
        "young adult woman, midnight blue hair with electric teal streaks, glowing violet eyes, cyberpunk graphic makeup, futuristic fitted outfit",
        "young adult woman, neon pink pixie cut, ecstatic open expression, holographic bodysuit elements, festival ready energy",
        "young adult woman, silver hair with rainbow prism when light hits, futuristic sharp features, high-tech fashion forward",
        "young adult woman, black hair with glowing LED accent strips woven in, sharp cat-eye makeup, cyberpunk aesthetic",
        "young adult woman, bleached white hair, UV festival paint on face, reflective outfit elements catching light",
        "young adult woman, neon green twin high pigtails, glowing bionic teal eyes, hacker-punk aesthetic outfit",
        "young adult woman, natural dark hair under laser light creating vivid color halo, ecstatic open-eyed expression",
        "young adult woman, platinum undercut with long flowing top section, chromatic iridescent eyes, festival electronic fashion",
    ],
    "rock": [
        "young adult woman, fiery orange-red pixie cut with shaved sides, blazing amber eyes, leather jacket covered in band pins",
        "young adult woman, long auburn waves wild and free, intense green eyes, sleeveless band shirt, silver rings on every finger",
        "young adult woman, wild dark curly hair, fierce open smile, ripped fishnet layers, leather jacket, raw energy",
        "young adult woman, bleached blonde with dark roots, sharp dramatic eyeliner, vintage band tee, aggressive confident energy",
        "young adult woman, short choppy black hair, intense forward stare, guitar strap visible, stage-worn outfit with history",
        "young adult woman, long straight dark hair, dramatic winged liner, skinny jeans and leather, full performance mode",
        "young adult woman, copper red loose curls, genuine fierce expression, band shirt knotted at waist, boots",
        "young adult woman, shaved sides with long textured top, silver hoop earrings, muscle shirt, raw rock energy",
    ],
    "metal": [
        "young adult woman, long straight black hair with blood-red underlayer showing, red heterochromia eye, dark gothic armor-influenced outfit",
        "young adult woman, ice-white long flowing hair, pale cool skin, stoic commanding expression, dark warrior outfit",
        "young adult woman, dark hair with geometric patterns, golden eyes, jeweled dark accessories, dark warrior queen energy",
        "young adult woman, wild dark hair, amber warrior eyes, battle-paint aesthetic makeup, dark powerful commanding outfit",
        "young adult woman, long flowing dark hair, glowing purple eyes, dark cloak catching wind, ethereal metal goddess",
        "young adult woman, black hair with electric silver highlights, cold grey eyes, armored dark outfit elements",
        "young adult woman, ink-black hair in warrior braid, fierce sharp features, dark elaborate dramatic outfit",
        "young adult woman, long silver flowing hair, glowing red eyes, pale luminous skin, dark cathedral dress aesthetic",
    ],
    "trap": [
        "young adult woman, sleek black hair in sharp high ponytail, cool composed expression, luxury fashion outfit, premium",
        "young adult woman, long honey-blonde waves perfectly styled, sea-blue eyes, premium streetwear, effortlessly expensive look",
        "young adult woman, short silver buzz cut, deep dark skin, sharp avant-garde features, high fashion luxury editorial",
        "young adult woman, black hair with galaxy deep-blue highlights, flawless dark skin, premium fitted outfit, regal presence",
        "young adult woman, long rose-gold hair perfectly styled, warm skin, composed elegant expression, tailored luxury fashion",
        "young adult woman, natural black hair slicked back cleanly, brown skin, strong jaw, premium monochrome outfit",
        "young adult woman, straight black blunt bob, neutral composed expression, designer tracksuit, luxury minimal aesthetic",
        "young adult woman, long wavy dark hair, deep expressive eyes, fitted designer coat, premium street aesthetic",
    ],
    "indie": [
        "young adult woman, long honey-blonde waves natural and free, warm sea-blue eyes, vintage slip dress and worn denim jacket",
        "young adult woman, short messy auburn hair, genuine freckled face, warm expression, wide-leg vintage trousers, knit crop",
        "young adult woman, natural curly dark hair, warm brown skin, sundress with oversized open cardigan, genuine beauty",
        "young adult woman, long caramel waves natural, honey-warm eyes, authentic unposed expression, linen wide pants and simple tee",
        "young adult woman, copper-red curls natural and wild, light skin with golden freckles, layered vintage finds",
        "young adult woman, short brown bedhead hair, genuinely unposed expression, soft flannel and worn jeans, real",
        "young adult woman, long dark hair with natural light highlights, bare face natural beauty, flowing vintage dress",
        "young adult woman, twin braids in natural brown, expressive dark eyes full of story, embroidered jacket, authentic style",
    ],
    "cinematic": [
        "young adult woman, long dark hair in wind, strong composed features, dramatic cinematic coat, commanding cinematic presence",
        "young adult woman, short silver hair, cool grey eyes, structured tailored jacket, editorial cinematic look",
        "young adult woman, long flowing auburn hair, green eyes catching dramatic light, cinematic outfit with movement",
        "young adult woman, black hair partially obscuring face, mysterious expression, cinematic dark fashion",
        "young adult woman, blonde hair catching dramatic golden light, strong jawline, film-quality presence and beauty",
        "young adult woman, long braids in motion, warm luminous skin, powerful stance, cinematic warrior-poet energy",
        "young adult woman, dark hair in elegant updo, sharp features, tailored cinematic outfit, composed power",
        "young adult woman, natural hair catching wind, brown skin luminous and glowing, cinematic wide-angle presence",
    ],
    "funk": [
        "young adult woman, voluminous natural afro with gold pins, deep rich skin, luminous warm expression, vibrant colorful outfit",
        "young adult woman, long box braids with gold thread woven in, warm brown skin, knowing smile, colorful fitted outfit",
        "young adult woman, wild curly natural hair full of life, expressive dark eyes, bright confident energy, fun colorful fashion",
        "young adult woman, short natural twists, warm genuine smile, groove energy in every feature, colorful retro outfit",
        "young adult woman, long flowing hair in warm ombre, medium brown skin, joyful expression, vibrant colorful clothes",
        "young adult woman, big natural curls, freckles across nose, wide genuine smile, colorful expressive style",
        "young adult woman, high natural puff hair, deep warm skin, eyes full of warmth and joy, retro-funk inspired look",
        "young adult woman, braided crown style, warm skin tone, elegant groove, vintage-inspired colorful outfit",
    ],
    "default": [
        "young adult woman, long dark hair, expressive deep eyes, confident composed expression, stylish dark outfit",
        "young adult woman, medium brown hair, genuine warm eyes, editorial fashion, magnetic commanding presence",
        "young adult woman, short textured hair, strong features, cool confident expression, modern style",
        "young adult woman, flowing hair in wind, striking mixed features, dramatic look, atmospheric fashion",
        "young adult woman, natural hair, brown skin, commanding presence, modern editorial aesthetic",
        "young adult woman, blonde highlights, grey eyes, quiet intensity, sophisticated minimal style",
        "young adult woman, dark hair with face-framing pieces, sharp features, cool urban fashion",
        "young adult woman, long waves, warm skin, dreamy expression, layered artistic fashion",
    ],
}

# ══════════════════════════════════════════════════════════════════════
# QUALITY TAGS — Ultra-premium, cores ultra-vibrantes
# ══════════════════════════════════════════════════════════════════════

QUALITY_TAGS = (
    "masterpiece, best quality, ultra-detailed anime illustration, "
    "professional anime key visual, perfect cel shading, clean sharp lineart, "
    "ultra-vibrant saturated colors, maximum color depth, rich vivid hues, "
    "deep blacks and luminous highlights, cinematic composition, razor-sharp focus, "
    "richly detailed background with atmospheric depth, volumetric lighting, "
    "dynamic light and shadow interplay, studio-level production quality, "
    "trending on pixiv, ArtStation quality, 9:16 vertical format, single character, "
    "scroll-stopping visual impact, premium anime visual novel quality"
)

NEGATIVE_PROMPT = (
    "photorealistic, hyperrealistic, photography, 3D render, CGI, real human face, "
    "text, watermark, signature, logo, border, frame, "
    "multiple characters, extra limbs, deformed hands, fused fingers, bad anatomy, "
    "distorted face, wrong proportions, malformed body parts, "
    "child appearance, young teen face, childlike proportions, "
    "explicit nudity, fetish content, inappropriate content, "
    "blurry, muddy colors, flat boring lighting, desaturated washed-out colors, "
    "generic gradient background, plain studio void, empty background, "
    "airbrushed plastic skin, uncanny valley, "
    "Western cartoon, Pixar style, chibi, super deformed, "
    "sketch only, unfinished lineart, low quality, oversaturated to point of noise"
)


# ══════════════════════════════════════════════════════════════════════
# SELEÇÃO DETERMINÍSTICA (sem repetição entre shorts da mesma música)
# ══════════════════════════════════════════════════════════════════════

def _seed(filename: str, short_num: int) -> int:
    key = f"{filename}|{short_num}|v5"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % (10 ** 9)


def _pick(pool: list, filename: str, short_num: int, offset: int = 0):
    rng = random.Random(_seed(filename, short_num) + offset * 131)
    return rng.choice(pool)


def _clean_song_name(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(r"\[[^\]]*\]|\{[^\}]*\}|\([^\)]*\)", "", name)
    name = re.sub(r"[_\-]+", " ", name).strip().title()
    return name or "Untitled"


def _compact(text: str, max_chars: int = 1600) -> str:
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
        "Your prompts generate PREMIUM cinematic, emotionally resonant anime illustrations "
        "inspired by the best of pixiv, lofi aesthetic art, cyberpunk manga, and dark fantasy illustration. "
        "\n\nCRITICAL VISUAL RULES — NEVER SKIP THESE:"
        "\n- ONE adult anime woman (18+), never children"
        "\n- ULTRA-VIBRANT, RICH, SATURATED COLORS — never flat or washed out"
        "\n- Deep rich blacks with luminous vivid highlights — maximum contrast"
        "\n- Dynamic volumetric lighting that creates atmosphere and depth"
        "\n- Composition: close portrait, medium shot, three-quarter, or wide — choose what serves the mood"
        "\n- DETAILED BACKGROUND — never empty, always tells a story"
        "\n- The color palette must be vivid and intentional, not generic"
        "\n- 9:16 vertical format"
        "\n- Platform safe, no explicit content"
        "\n- The IMAGE must visually connect to the song title and genre mood"
        "\n- Output ONLY the prompt: comma-separated descriptors, 100-140 words, no explanations, no preamble"
    )

    user = f"""Create a PREMIUM ultra-vibrant anime illustration prompt for a music YouTube Short.

SONG TITLE: "{song_name}"
PRIMARY GENRE: {style}
ALL DETECTED GENRES: {all_styles}
SHORT NUMBER: {short_num}

CHARACTER DESCRIPTION:
{character}

COMPOSITION DIRECTION:
{composition}

COLOR PALETTE (USE THIS — make colors rich and vivid):
{palette}

CRITICAL REQUIREMENTS:
- Visually connect to the song title "{song_name}" — the image should FEEL like the song
- Ultra-rich colors: deep saturated hues, vivid contrasts, maximum color depth
- Atmospheric depth with detailed environment
- Cinematic lighting quality — volumetric, dramatic, intentional
- Expression tells a story that matches the genre mood
- Make someone STOP scrolling instantly when they see this
- 100-140 words total, comma-separated descriptors only"""

    resp = client.messages.create(
        model=get_anthropic_model(),
        max_tokens=400,
        system=system,
        messages=[{"role": "user", "content": user}],
    )

    raw = resp.content[0].text.strip().strip('"').strip("'")
    full = f"{raw}, {QUALITY_TAGS}"
    print(f"  [Claude] Prompt gerado ({len(full)} chars) short #{short_num}")
    return _compact(full)


def _static_prompt(character: str, composition: str, palette: str) -> str:
    prompt = (
        f"masterpiece, best quality, ultra-detailed premium anime illustration, "
        f"{character}, "
        f"{composition}, "
        f"color palette: {palette}, "
        f"ultra-vivid saturated colors, deep rich blacks, luminous highlights, "
        f"cinematic volumetric lighting, atmospheric depth, richly detailed background, "
        f"clean sharp anime lineart, perfect cel shading, maximum color depth, "
        f"9:16 vertical composition, single character, "
        f"scroll-stopping visual impact, pixiv trending premium quality"
    )
    return _compact(prompt)


# ══════════════════════════════════════════════════════════════════════
# GERAÇÃO VIA REPLICATE — Flux com parâmetros otimizados para cores vivas
# ══════════════════════════════════════════════════════════════════════

REPLICATE_MODELS = [
    "black-forest-labs/flux-dev",
    "black-forest-labs/flux-schnell",
]

MODEL_PARAMS = {
    "black-forest-labs/flux-dev": {
        "num_inference_steps": 35,
        "aspect_ratio": "9:16",
        "guidance": 4.5,          # Aumentado para cores mais vivas e fidelidade ao prompt
        "output_format": "png",
        "output_quality": 98,     # Qualidade máxima
        "disable_safety_checker": True,
    },
    "black-forest-labs/flux-schnell": {
        "num_inference_steps": 4,
        "aspect_ratio": "9:16",
        "output_format": "png",
        "output_quality": 98,
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

    # Reforça qualidade visual no prompt final enviado ao modelo
    full_prompt = _compact(
        prompt
        + ", anime illustration style, NOT photorealistic, NOT 3D render, "
        + "ultra-vibrant saturated colors, deep rich shadows, luminous vivid highlights, "
        + "sharp clean lineart, premium anime key visual quality"
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
