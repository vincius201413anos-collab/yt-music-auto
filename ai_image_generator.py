"""
ai_image_generator.py — v3.0 HYPER-SPECIFIC VISUAL IDENTITY
============================================================
Cada gênero tem DNA visual único e inconfundível.
Personagens com aparências ESPECÍFICAS e distintas — sem "young woman with dark hair" genérico.
Composições cinematográficas que param o scroll instantaneamente.
Anti-repetição máxima via seed determinística por música + short_num.
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
# DNA VISUAL POR GÊNERO
# Cada gênero tem paleta, personagem, composição e atmosfera ÚNICOS
# ══════════════════════════════════════════════════════════════════════

GENRE_DNA = {

    # ── LOFI ──────────────────────────────────────────────────────────────
    "lofi": {
        "palette": [
            "deep amber desk lamp warmth bleeding into cold blue moonlight through rain-streaked window, rich contrast between warm interior and cold exterior night",
            "oversaturated golden-hour orange fading into deep indigo shadow, warm as memory feels, film grain adding texture and depth",
            "vivid burnt sienna lamp light against midnight navy room, steam rising visible in warm air, cozy maximum contrast",
            "deep honey-gold glow from below, every surface catching warm light, cold blue rectangle of night window in background",
            "rich terracotta warm and saturated teal moonlight, vintage film warmth, colors deep like overexposed analog film",
            "glowing amber-orange from string lights creating halos, surrounding deep purple-blue room darkness, intimate warmth",
            "deep coral sunset warmth through curtains, cool lavender shadow on opposite wall, soft yet saturated contrast",
        ],
        "characters": [
            "pale Japanese-Korean woman, short asymmetric black bob with blunt cut, dark half-moon eyes with ink liner, tiny silver nose stud, oversized cream vintage university hoodie, headphones resting on shoulders, paint-stained fingers holding mug",
            "freckled redheaded woman, messy copper curls half-pinned up with pencils sticking out, round wire-frame glasses fogged slightly, green-hazel eyes, large soft knit cardigan in oatmeal beige, open sketchbook in lap",
            "dark-skinned woman with natural 4C hair in loose puff held by silk scrunchie, deep brown eyes with sleepy warmth, small gauze bandage on chin from art accident, oversized faded band tee, cozy ankle socks with cats",
            "Southeast Asian woman, long straight dark hair with blunt fringe perfectly cut, large rectangular glasses with clear frames, tired but content dark brown eyes, blue-grey vintage oversized sweater, cup of tea in both hands",
            "Latina woman with wavy dark brown hair loose and a bit tangled, warm caramel skin, dark eyes with crescent shadows under them, cozy ribbed turtleneck in dusty rose, small gold hoop earrings, paint smudge on cheek",
            "mixed-race woman, tight dark curls with some escaping a loose bun, honey-brown eyes behind round tortoiseshell glasses, soft oversized flannel in deep green plaid, knees pulled to chest, vinyl record visible nearby",
            "pale woman with silver-bleached short hair grown out showing dark roots, slightly asymmetric face with gap tooth showing in soft smile, large forest green hoodie, fingers with small rings, mug of ramen visible",
        ],
        "compositions": [
            "tight face-and-shoulders portrait, face half warm amber from desk lamp on right, half cool blue moonlight from window on left, rain visible blurred on glass behind, intimate and emotionally real",
            "medium side-profile shot, girl absorbed in sketchbook at wooden desk, lamp casting dramatic one-sided warm light, window showing blurred city lights in rain, her world small and complete",
            "close portrait with soft shallow depth of field, face in sharp focus, string lights behind creating golden bokeh that fills entire background, one eye slightly obscured by hair",
            "medium shot from slightly above, girl cross-legged on bed surrounded by books and a small plant, full moon visible in window directly behind her creating soft halo effect",
            "rear shot over shoulder through fogged window, viewer looking through the glass at city lights reflected and blurred, her silhouette before the glass from warm side",
            "extreme close crop: just eyes and above in focus, below nose soft, steam rising from mug at bottom edge of frame, fairy lights creating subtle bokeh highlights in eyes",
            "three-quarter medium shot, girl looking directly at viewer with tired but warm expression, lamp and window both visible in frame, the whole cozy ecosystem around her visible",
        ],
    },

    # ── PHONK ─────────────────────────────────────────────────────────────
    "phonk": {
        "palette": [
            "single brutal crimson neon slash cutting pitch-black frame, blood-red wet concrete reflections below, no other color exists in this world",
            "cold electric violet-purple against total charcoal black, neon reflecting in puddles, hypercontrast urban underground, no softness anywhere",
            "burning orange sodium vapor lamp creating one harsh pool of light in infinite black, industrial noir, shadows have weight",
            "magenta-pink neon ONLY source of light in jet black world, aggressive single-color dominance, reflections everywhere like a crime scene",
            "split: ice-cold blue LED on left half, deep rust-red sodium on right half, center shadow divides them, maximum tension",
            "deep red-orange factory light and total darkness fighting each other, empty concrete structure, gritty texture everywhere",
            "toxic green neon cutting black sky, wet asphalt turning everything to mirrors below, hostile and beautiful",
        ],
        "characters": [
            "Japanese woman, razor-straight jet black hair with geometric undercut showing, sharp almond eyes with cold empty expression that holds nothing back, no makeup except dark liner, black technical jacket with chest zipper, face half in shadow half harsh neon",
            "Black woman, long microbraids with burgundy highlights, angular strong features with full lips set in absolute neutrality, septum ring, oversized black parka hood half-up, deep brown eyes reflecting neon like water",
            "Eastern European woman, platinum silver buzzcut with shaved temple showing skin, pale almost translucent skin, ice-grey eyes with zero emotion, black structured jacket collar up, single small scar on cheekbone",
            "Korean woman, sleek dark hair in tight high ponytail pulling face smooth, sharp monolid eyes with cat-eye liner wing, angular jaw, dark fitted jacket with too many unnecessary zippers, controlled stillness",
            "Brazilian woman with natural dark tight curls, deep brown skin, wide nose, expressionless full lips, dark fitted technical hoodie, gold earring studs only jewelry, arms crossed like a closed door",
            "mixed-race woman, dark hair shaved on sides leaving strip of curls on top in loose mohawk, strong cheekbones, deep-set eyes with slow intelligence, matte black jacket, bare wrists",
            "Chinese woman, blunt-cut black bob with one streak of bleached blonde, sharp angular face, hollow cheeks, eyes looking through camera not at it, black oversized coat, no expression to read",
        ],
        "compositions": [
            "extreme close portrait, face filling 80% of frame, single crimson neon slash lighting one eye and cheekbone, everything below chin in absolute black, manga-panel negative space above",
            "medium shot, figure leaning against concrete wall in empty parking structure at 3am, arms crossed, single purple neon tube reflected in wet floor below her feet, harsh and still",
            "low-angle looking up at figure crouching on concrete barrier, harsh sodium light from side, city visible far below and behind, commanding and cold",
            "rear shot: figure walking away down empty tunnel toward distant light, she never looks back, every step deliberate, mist at ankle level",
            "tight face crop: only eyes and nose visible, rest obscured by shadow and hood, neon reflection visible in one iris, the mystery is the point",
            "three-quarter medium shot, figure at edge of empty rooftop, city grid below like a circuit board, wind pulling hair slightly, cold and removed from it all",
            "reflected shot: face seen in rain-wet car window glass, slightly distorted by water, city and neon inverted behind the reflection, two realities at once",
        ],
    },

    # ── TRAP ──────────────────────────────────────────────────────────────
    "trap": {
        "palette": [
            "deep midnight navy blue and pure burnished gold, luxury cold with warm edges, the palette of penthouse and ambition",
            "champagne gold and rich velvet black, premium contrast, expensive at first glance, the visual language of arrival",
            "electric teal and rose gold, premium streetwear editorial, vivid luxury palette that stops the eye immediately",
            "ice blue-white moonlight and deep rich copper, cold ambition and warm achievement, premium contrast",
            "deep purple-navy and bright silver chrome, elevated urban twilight, the city as backdrop to power",
            "vivid coral against deep midnight, warm luxury against cold night, the color story of confidence",
            "black marble and vivid electric indigo, pure aesthetic luxury, modern and cold and beautiful",
        ],
        "characters": [
            "Nigerian woman, natural afro with gold thread woven through, flawless deep brown skin, sharp angular face with cheekbones that cut, composed cold expression, luxury white turtleneck under structured black coat, small diamond studs",
            "Korean-American woman, sleek black hair with money-piece highlights, high sharp cheekbones, fox-shaped eyes with clean professional liner, pearl skin, fitted beige tailored set with chunky gold chain",
            "Dominican woman, long honey-brown boxer braids past shoulders, deep olive skin, cat-shaped dark eyes with thin brow, strong jaw, black oversized designer crewneck, ear full of studs climbing the cartilage",
            "Japanese woman, sharp bob with gold highlights at tips, neutral expression that reads as power, clean liner, light skin, fitted luxury crop set in dove grey, layered gold chains of different lengths",
            "Ghanaian woman, long Senegalese twists with silver cuffs, deep rich skin, wide-set eyes that assess everything, no-smile composure, structured leather set, rings on every finger but one",
            "mixed-race woman, natural loose curls slicked back, warm medium skin, strong Latina features, mascara-only makeup, fitted dark set with architectural cut, thin gold necklace at collarbone",
            "Chinese woman, sleek middle-part straight black hair, porcelain pale with sharp features, clean no-makeup-makeup, structured camel coat over black, one thick gold cuff wrist, controlled",
        ],
        "compositions": [
            "medium shot at floor-to-ceiling window, figure facing camera with entire city grid spread behind her at night, arms loose, the city is context not destination",
            "editorial three-quarter shot, strong lighting from floor lamp creating dramatic upward shadow, figure composed and still, luxury room visible but unfocused",
            "close portrait, city lights soft behind large window, face perfectly lit, neutral expression that holds everything back, luxury at rest",
            "low-angle medium shot looking up slightly, figure walking forward, city skyline behind through car window, the kind of shot that means arrival",
            "side-lit close portrait, single window of light grazing cheekbone and jaw, deep shadow on other half, the luxury of negative space",
            "wide shot, figure small against massive lit penthouse window, city spread below in all directions, scale makes her look more powerful not less",
            "reflected in dark glass: face in foreground, city lights blurred and reflected in surface, two layers of image creating depth",
        ],
    },

    # ── DARK ──────────────────────────────────────────────────────────────
    "dark": {
        "palette": [
            "near-monochrome silver-grey and absolute black with single bleeding crimson accent, stark as a cut, manga aesthetic maximized",
            "deep jewel violet and cold silver moonlight, gothic beauty with rich purple shadow filling everything not lit",
            "black ink and saturated blood red, complete tonal contrast, horror made into art",
            "ash-white and deep charcoal with ghostly cyan light, supernatural cold, color of things that shouldn't exist",
            "pitch black with vivid absinthe-green luminescence, toxic beauty, the color of old poison",
            "deep prussian blue-black and pale silver, cold and ancient, the palette of old cemeteries and frozen water",
            "matte black and vivid electric violet, dark energy given form, the color of power without warmth",
        ],
        "characters": [
            "ghostly pale Japanese woman, impossibly long straight black hair spreading around her, irises that glow deep crimson against white, slight smile that understands something terrible, dressed in layered black fabric that moves like water",
            "Scandinavian-looking woman with silver-white hair, hollow silver-grey eyes that catch light like a cat's, sharp defined features, dark gothic dress with high collar, black tear-streak markings on cheekbones",
            "Chinese woman with black hair partially obscuring one eye, the visible eye a glowing violet-purple, pale skin with faint veining visible at temples, dark layered outfit, fingers with too many joints visible",
            "dark-skinned woman, natural hair with silver strands woven through, black irises that absorb all light, expression of a person who has seen and survived everything, intricate dark markings on arms, dressed in structured darkness",
            "pale woman with bleached white short hair, deep-set eyes ringed with dark shadow like bruises, expression peaceful as sleeping, black ink tattoos covering neck and hands, dark Victorian-influenced outfit",
            "ambiguous-featured woman with angular face, one eye completely black sclera, one eye glowing amber, dark ink-black hair floating slightly as if underwater, minimal dark outfit, presence that fills empty space",
            "Middle Eastern woman with jet black hair and strong defined features, deep brown eyes that glow with violet inner light, geometric black markings on face, dark structured outfit with gold accents at collar",
        ],
        "compositions": [
            "extreme close portrait, face filling frame, one eye sharp and luminous, hair drifting into black void corners of frame, negative space used as active element",
            "medium shot in moonlit ruins, single shaft of silver light from above catching face, mist at ground level obscuring feet, scale of decay around her",
            "wide atmospheric shot, small figure at center of vast dark space, single source of vivid colored light surrounding her, the void is presence",
            "extreme crop of single glowing eye filling half the frame, surrounded by dark hair and shadow, the other half pure black, minimal and overwhelming",
            "medium shot reflected in still black water, figure above and reflection below, moonlight from directly above, mirror symmetry as horror element",
            "rear shot in dark corridor, figure walking toward single light source ahead, her shadow stretching back toward viewer, what is she walking toward",
            "close portrait from below, face tilted down looking at viewer from above, dramatic underlighting creating inverted shadow that feels wrong, beautiful and wrong",
        ],
    },

    # ── ELECTRONIC ────────────────────────────────────────────────────────
    "electronic": {
        "palette": [
            "electric cyan and deep magenta in equal war, complementary clash at maximum saturation, rave light as sculpture",
            "UV electric purple making white surfaces glow vivid, fluorescent green in shadows, the physics of blacklight",
            "strobing white laser and rainbow chromatic aberration edges, techno cathedral light quality, precision and chaos",
            "neon pink and electric teal, vivid complementary palate of the 4am rave, excess as aesthetic principle",
            "holographic rainbow spectrum across deep black, interference patterns as background, the light of the future",
            "vivid acid-yellow and deep electric blue, the most aggressive complementary pair, visual as sound wave",
            "laser red and electric cyan split-lit, two colors at maximum intensity, halation and bloom everywhere",
        ],
        "characters": [
            "Japanese woman with electric midnight-blue hair in bold geometric bob cut with blunt fringe, violet LED-lit eyes, cyberpunk graphic face paint in neon, holographic bodysuit with light-reactive panels",
            "Black woman with natural 4C hair dyed vivid neon magenta, glowing UV-reactive skin art on shoulders and collarbone, ecstatic eyes open wide, chrome reflective jacket with laser burns as design",
            "Korean woman with silver chrome undercut, long top section in vivid electric green, cyberpunk contact lenses making eyes glow blue-white, technical festival fashion with LED strips",
            "mixed-race woman with shaved head and neon yellow geometric lines drawn on scalp with paint, strong features in UV festival makeup, reflective jumpsuit, face caught in ecstasy mid-song",
            "white woman with chaotic bleached hair going every direction, neon festival paint on face and neck, eyes that catch every light and scatter it back, mesh and holographic layered outfit",
            "Filipina woman with waist-length hair dyed deep electric purple, bioluminescent face paint activated by UV around eyes, technical fashion from future era, caught mid-movement arms raised",
            "androgynous-featured woman with platinum buzzcut, glowing bionic-looking teal eye implant aesthetic, sharp geometric face paint, chrome-and-neon armor-fashion, commanding the stage",
        ],
        "compositions": [
            "rear shot from stage level, figure arms raised against ocean of phone lights and crowd, laser beams cutting fog above in multiple colors, the scale of it",
            "close portrait, face lit by rapid color-changing stage lights, eyes closed in ecstasy, chromatic aberration at frame edges, motion blur on lights only",
            "medium silhouette against massive LED wall with abstract vivid visuals, only outline defined, color explosion compositing around dark form",
            "aerial-feeling wide shot, single figure at center of outdoor festival, massive LED stage as bright core, crowd ocean surrounding, stars above completing the circle",
            "medium shot through crowd, figure in foreground sharp, crowd behind as smear of light and motion blur, she is still while everything moves",
            "extreme close shot of eye catching laser light, iris reflecting colored beams, pupil surrounded by concentric rings of colored light, abstraction and beauty",
            "three-quarter medium shot, hands on DJ equipment, face lit from below by vivid deck lighting, crowd hands at frame edges raising toward her",
        ],
    },

    # ── ROCK ──────────────────────────────────────────────────────────────
    "rock": {
        "palette": [
            "deep amber stage fire and pure darkness, live show drama, warm volcanic against cold shadow, raw energy in light",
            "harsh white spotlight and pitch-black shadows, the binary of performance, no grey anywhere, commitment",
            "vivid red and cold blue split light, two temperatures in conflict, the tension is the point",
            "deep orange ember tones and concrete grey, industrial warmth, raw venue with history in the walls",
            "backlit smoke creating orange-amber corona, silhouette dark against glowing fog, the shape of sound",
            "vivid warm stage flood against deep navy sky, outdoor show at dusk, the moment between world and music",
            "hot white lamp and deep shadow creating half-face drama, the classic rock image, timeless contrast",
        ],
        "characters": [
            "white woman with fiery copper-orange short pixie with shaved undercut showing, blazing amber eyes, leather jacket covered in hand-sewn band patches and pins, torn fishnet arm, mid-song face",
            "Black woman with wild natural 4C afro fanned out dramatically, fierce wide eyes, winged liner precise despite chaos, sleeveless band tee knotted at waist, silver rings stacked on fingers, guitar strap visible",
            "Latina woman with long dark waves wild and electric with stage movement, intense green eyes catching spotlight, ripped band tee showing attitude, leather jacket hanging off one shoulder, caught mid-riff face",
            "Japanese woman with bleached short choppy hair with dark roots, sharp dramatic eyeliner, intense direct gaze, vintage band tee cut into crop, high-waist jeans, guitar pick between teeth",
            "mixed-race woman with loose dark curls dyed vivid red-auburn at tips, freckled warm skin, fierce open-mouth expression mid-scream into mic, fishnet and leather layers, ear full of hoops",
            "white woman with long straight dark hair sticking to sweaty neck and face, heavy kohl liner, expression between pain and transcendence that only performance produces, band tee decades old",
            "Korean-American woman with wild bleached waves, sharp facial features, black liner wings, shredded leather vest over white tee, arms mid-windmill guitar motion, pure kinetic",
        ],
        "compositions": [
            "tight close performance portrait, face and mic in frame, expression caught between pain and release that only happens in songs, stage light harsh and beautiful",
            "medium shot from stage floor looking up, figure backlit by wall of stage lights creating halo around wild hair, crowd hands visible at bottom edge as sea",
            "wide silhouette, figure against wall of white concert lights, arms open, crowd silhouette at feet as suggestion of mass",
            "three-quarter medium shot, guitar solo moment, head thrown back, face at exact angle between pain and transcendence, spotlight from directly above",
            "extreme close crop, fingers on guitar frets in focus, face soft-focused above, the instrument and the player equal subjects",
            "medium shot frozen mid-jump off riser, all gravity suspended, stage lights below and behind, crowd blur surrounding moment",
            "intimate rear shot from stage wing, figure facing crowd, the enormous space of the room visible, she commands all of it",
        ],
    },

    # ── METAL ─────────────────────────────────────────────────────────────
    "metal": {
        "palette": [
            "volcanic deep orange-red and absolute char-black, apocalyptic heat, the palette of destruction with beauty",
            "deep crimson and pure charcoal grey, brutal contrast, nothing wasted, everything at maximum",
            "cold lightning white-blue and storm-black sky, raw electrical power, nature at its most hostile",
            "amber ember glow and total darkness, fire as the only light source, primitive and overwhelming",
            "ice crystal pale blue and black stone, ancient evil cold, the palette of things that predate humanity",
            "burning orange and deep storm purple, the sky during the worst storm you've survived, vivid and threatening",
            "matte grey and vivid electric red, industrial power, machinery and violence in color form",
        ],
        "characters": [
            "white woman, impossibly long straight dark hair with blood-red dyed under-layer visible in movement, one natural eye one vivid red glowing eye, dark gothic armor-influenced clothing with intricate detailing, warrior queen who has won every war",
            "Scandinavian woman, ice-white long flowing hair that moves in wind that isn't there, pale cool skin, stoic commanding expression that has seen the end and chosen to continue, dark structured warrior outfit",
            "South Asian woman, dark waist-length hair in elaborate warrior braid, deep amber eyes with battle intensity, strong defined features, dark aesthetic with gold accent jewelry, warrior queen energy",
            "mixed-race woman, wild dark hair matted with rain, warm brown skin with battle-paint markings on cheeks, amber warrior eyes, dark powerful outfit, the kind of presence that ends silences",
            "pale woman, long dark hair floating slightly as if charged with electricity, glowing purple eyes, dark flowing garment with structured armor elements at shoulders, surrounded by barely visible shadow energy",
            "Black woman, natural hair pulled into elaborate dark crown, deep rich skin, glowing golden eyes that judge everything, dark intricate outfit with metalwork detail, absolute presence",
            "Chinese woman, long black hair with geometric silver-white streaks, cold grey eyes with inner light, angular strong face, dark structured outfit with flowing elements, ancient and current simultaneously",
        ],
        "compositions": [
            "close portrait, face lit from below by fire or volcanic glow, everything above head in storm-black, expression absolute and serene in chaos",
            "wide atmospheric shot, small figure on elevated rock or cliff, storm sky with multiple lightning strikes surrounding, scale of natural power framing human will",
            "medium shot surrounded by floating embers and ash, fire glow from below, face serene amid active destruction, beauty and chaos as partners",
            "extreme close face shot, unflinching gaze forward, volcanic or storm light catching every feature at maximum, primal intensity",
            "dramatic medium from below looking up, figure descending dark stone steps, dark fabric in motion, ancient stronghold behind creating epic scale",
            "silhouette wide, figure atop extreme high point, multiple lightning strikes simultaneously, the storm obeys her or is afraid of her",
            "medium shot in dark cathedral or ancient space, candle light casting dramatic long shadows, figure commanding the space simply by being present in it",
        ],
    },

    # ── INDIE ─────────────────────────────────────────────────────────────
    "indie": {
        "palette": [
            "deep honey-amber of last golden hour before sunset, everything warm and ending, natural beauty at maximum",
            "overcast silver-white light, rich saturated earth tones, honest color, the beauty of cloudy afternoon",
            "late afternoon deep orange amber, long shadows, the feeling that this moment is almost over and was perfect",
            "dusk gradient from vivid salmon pink to deep indigo purple, the sky on the best day, magic hour is real",
            "morning soft golden light shaft through dust, the world before it remembers to be complicated, warm and quiet",
            "deep green of overgrown places and warm golden light catching leaves from behind, natural and vivid",
            "rich warm honey and deep burgundy, autumn tones, the color of nostalgia that doesn't hurt yet",
        ],
        "characters": [
            "white woman with long honey-blonde waves genuinely natural and uncurated, warm sea-glass eyes, honest freckles, vintage slip dress with worn denim jacket that has pins and badges, absolutely herself",
            "Black woman with natural 4C hair loose and full, warm deep skin, genuine bright eyes, sundress with oversized open cardigan, looking directly at viewer with something true",
            "Latina woman with short natural dark waves, warm olive skin with real freckles, gap tooth visible in soft real smile, wide-leg vintage trousers and knit crop, looks like a person not a model",
            "mixed-race woman with loose natural curls, warm medium skin, honey eyes, expression of someone who just thought of something that made her smile, layers of vintage finds that shouldn't work together but do",
            "Asian woman with wavy dark hair, soft warm features, eyes that hold specific thought not just beauty, genuine casual style, the kind of person who finds the good vinyl at the thrift store",
            "white woman with copper-red loose curls genuinely not quite under control, freckled pale skin, warm grey eyes, flannel over band shirt, the person you want to know",
            "Filipino woman with natural dark waves, warm brown skin and honest expression, handmade earrings, embroidered jacket that someone important gave her, deeply present in the moment",
        ],
        "compositions": [
            "medium close shot, face in rich golden-hour light with specific warmth that feels like a specific day, environment suggesting more than showing",
            "intimate shot from passenger seat looking at driver, late afternoon light through windshield catching hair and profile, movement implied by everything",
            "close portrait with film photography aesthetic, slight beautiful analog overexposure, warm grain giving texture to light, genuinely unposed expression",
            "medium shot on rooftop or fire escape, dusk sky transitioning vivid colors behind, figure with city soft below, neither nostalgia nor escape, just here",
            "wide atmospheric shot, figure small in field of tall golden grass, late sun turning everything the color of memory, arms naturally out not performatively",
            "close shot through café or apartment window, condensation at edges, warm inside cold outside, face looking out at rain, honest and present",
            "medium shot in beautiful overgrown forgotten place, afternoon light through broken ceiling or branches, life reclaiming beauty, she found it",
        ],
    },

    # ── CINEMATIC ─────────────────────────────────────────────────────────
    "cinematic": {
        "palette": [
            "vivid teal and rich orange color science of premium cinematography, complementary grading maximized, film quality",
            "desaturated environment with single vivid golden beam of light, everything else grey, that one thing glowing",
            "cold blue exterior and warm amber interior split perfectly, dramatic contrast, the grammar of film lighting",
            "deep rich shadows and luminous gold highlights, chiaroscuro technique at cinematic scale, Rembrandt in motion",
            "fog-diffused atmosphere with one brilliant warm light source in grey world, smoke making light visible",
            "storm break, ray of amber light through dark clouds, the world about to change, epic atmospheric scale",
            "vivid blue hour and warm artificial light, the most cinematic time of day, world in transition",
        ],
        "characters": [
            "mixed-race woman, long dark hair moving in wind from direction we can't see, strong features with natural presence that cameras love, dramatic long coat, the kind of face that tells a story in every frame",
            "white woman with short silver-grey hair despite apparent youth, cool intelligent grey eyes, structured tailored jacket, presence suggesting the most interesting person in every room she enters",
            "Black woman with elaborate braids in motion, luminous warm skin, eyes that observe everything, cinematic fashion with architectural structure, she has already lived the story she's telling",
            "East Asian woman, dark hair partially obscuring face from wind, expression of someone making a difficult decision that only she knows about, understated outfit that film would light perfectly",
            "Latina woman, long dark waves catching dramatic light, strong features, warm skin that cinematography was designed for, powerful stance that means something specific",
            "South Asian woman with long dark hair in motion, deep brown eyes that hold complete inner life, cinematic outfit with movement, the protagonist energy that fills a frame",
            "white woman with natural blonde hair catching light, jawline that film lighting was invented to find, composed expression that holds back exact right amount, dressed simply because she doesn't need more",
        ],
        "compositions": [
            "wide cinematic shot, small figure against vast dramatic landscape — cliff, impossible sky, storm breaking — scale making the human feel both small and brave",
            "close portrait, extreme cinematic depth of field, face sharp, environment behind soft-suggested like memory, anamorphic lens quality, widescreen feel in vertical",
            "medium atmospheric shot, figure walking through deep fog toward single light source, the path between known and unknown, film noir with beauty instead of dread",
            "close medium shot in rain, figure facing the rain rather than sheltering, city or dramatic environment behind, the specific choice of being present in bad weather",
            "silhouette against impossible sky, storm break releasing last light, double horizon, the sky itself a painting she stands inside",
            "perspective medium shot, figure at end of long architectural corridor, single vanishing point, the precision of intention, she is walking somewhere specific",
            "split composition, upper half figure, lower half her reflection in still water, almost perfect mirror, the line between them slightly wrong in interesting way",
        ],
    },

    # ── FUNK ──────────────────────────────────────────────────────────────
    "funk": {
        "palette": [
            "deep warm orange and rich red-brown of late night venue lighting, soulful heat, colors that feel alive",
            "electric yellow and deep purple, the classic groove complementary pair, vivid as celebration feels",
            "vivid coral-sunset and deep warm teal, saturated alive, the color of music that makes you move before you decide to",
            "deep gold and rich dark mahogany, soulful warmth, the texture of old wood and good music",
            "neon warm magenta and amber, night venue energy, vivid as the best part of any night out",
            "vivid orange and electric cobalt blue, high-energy contrast, groove has a color and this is it",
            "rich red-orange and deep purple, warm against cool, the tension that makes music feel inevitable",
        ],
        "characters": [
            "Black woman with voluminous natural afro, gold and amber beaded pins throughout, deep rich warm skin, expression of someone who has been the best dancer in every room, colorful fitted vintage inspired outfit",
            "Afro-Latina woman with long box braids with bright thread woven through, warm brown skin, wide genuine smile that changes the shape of her face, vibrant fitted outfit, gold jewelry stacked",
            "Black woman with short natural twists and strong defined features, warm deep skin, knowing smile that holds the whole history of music, colorful expressive retro-inspired style",
            "mixed-race woman with loose natural curls, medium warm skin, freckles, wide expressive brown eyes full of joy, vibrant layered colorful clothing, the person who makes others dance",
            "West African woman with elaborate natural hair braided into artistic crown, deep rich skin, expressive warm eyes, brightly colored traditional-influenced modern outfit, gold at ears and wrists",
            "Latina woman with long natural waves, warm olive skin, genuine laugh caught in photo, vibrant vintage-style outfit with interesting details, the energy in the room",
            "Black woman with high natural puff hair, deep warm skin, dancing-eyes that make contact, colorful fitted outfit with detail, small gold hoops, pure presence",
        ],
        "compositions": [
            "medium close shot in warm-lit venue, face caught in genuine mid-groove expression, warm colored stage lights making skin glow, crowd blur of color behind",
            "three-quarter medium shot, caught mid-dance movement at exact perfect moment, warm venue light, arms and hair slightly blurred by motion, frozen joy",
            "close portrait, warm deep orange-gold lighting from venue stage, natural expressive face with real expression, rich saturated background of lights",
            "medium shot on outdoor rooftop or courtyard, sunset bathing everything warm, genuine relaxed freedom, city soft and warm below",
            "intimate close portrait, golden bokeh lights filling background completely, face warm and luminous in that light, the feeling of the song in her face",
            "wide atmospheric shot, night venue or outdoor space, she is the center of natural attention without trying, warm beautiful chaos around",
            "medium shot caught between songs, brief exhale and smile, the real moment between performances, warm light and genuine expression",
        ],
    },

    # ── DEFAULT ───────────────────────────────────────────────────────────
    "default": {
        "palette": [
            "vivid neon purple and deep black, atmospheric and specifically moody, premium saturation",
            "cold electric blue and warm gold split, cinematic contrast, the visual language of quality",
            "deep rich teal and vivid rose, editorial beauty, saturated and sharp as good design",
            "steel grey and electric blue, urban poetry, cold and beautiful as the city at 3am",
            "midnight navy and luminous silver, quiet power, deep contrast for deep feeling",
            "vivid amber and deep indigo, warm cold contrast, cinematic as it gets",
            "electric cyan and deep burgundy, complementary vivid, premium visual drama",
        ],
        "characters": [
            "young adult woman, striking features with strong individual identity, expressive eyes, confident composed presence, stylish outfit with specific personality",
            "young adult woman, distinctive appearance that stays with you, warm genuine expression, editorial fashion with real-world energy",
            "young adult woman, short distinctive hair, sharp features, cool intelligence in expression, modern style that's uniquely hers",
            "young adult woman, flowing hair with movement, striking features, dramatic presence, fashion that tells a story",
            "young adult woman, natural hair, luminous skin tone, commanding presence that fills the frame, modern aesthetic",
            "young adult woman, specific distinguishing features, quiet intensity in expression, sophisticated minimal style",
            "young adult woman, face with real character and genuine expression, layered artistic fashion, someone worth knowing",
        ],
        "compositions": [
            "close portrait with dramatic lighting, expressive specific face, atmospheric background in soft focus, premium visual quality",
            "medium shot with strong environmental storytelling, character and place in conversation, moody and deeply intentional",
            "wide atmospheric shot, figure against significant environment, scale creating emotional resonance",
            "tight medium shot, editorial composition, strong vivid color palette, character commanding frame",
            "close portrait, beautiful dramatic lighting, rich detailed background, premium illustration quality throughout",
            "silhouette medium shot against dramatic sky or strong light source, form and mood over detail",
            "three-quarter medium shot with interesting environment creating depth and story in every part of frame",
        ],
    },
}


# ══════════════════════════════════════════════════════════════════════
# QUALITY & NEGATIVE
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
    "sketch only, unfinished lineart, low quality, oversaturated to point of noise, "
    "generic anime waifu, bland background, same composition as always"
)


# ══════════════════════════════════════════════════════════════════════
# SEED DETERMINÍSTICA — garante variação sem repetição
# ══════════════════════════════════════════════════════════════════════

def _seed(filename: str, short_num: int) -> int:
    """Seed única por música + posição — garante que short 1, 2, 3 da mesma música
    sempre gerem personagens/composições diferentes entre si, e também diferentes
    de outros arquivos de música com a mesma posição."""
    key = f"{filename}|{short_num}|v6"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % (10 ** 9)


def _pick(pool: list, filename: str, short_num: int, offset: int = 0):
    """Seleciona item do pool com RNG determinístico.
    offset diferente para cada componente garante que personagem, composição e paleta
    sejam selecionados de forma independente (não correlacionada)."""
    rng = random.Random(_seed(filename, short_num) + offset * 999983)
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
    """
    Monta prompt com DNA visual específico do gênero.
    Cada componente (personagem, composição, paleta) é selecionado independentemente
    via seed determinística — garantindo máxima variação sem repetição.
    """
    song_name = _clean_song_name(filename)
    dna = GENRE_DNA.get(style, GENRE_DNA["default"])

    character   = _pick(dna["characters"],   filename, short_num, offset=0)
    composition = _pick(dna["compositions"], filename, short_num, offset=1)
    palette     = _pick(dna["palette"],      filename, short_num, offset=2)
    all_styles  = ", ".join(s.title() for s in styles) if styles else style.title()

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
        "You are an elite anime art director. Your prompts generate illustrations that stop people "
        "mid-scroll. You work like a cinematographer and a character designer at once — "
        "every prompt has a SPECIFIC visual identity, not generic anime beauty.\n\n"
        "LAWS YOU NEVER BREAK:\n"
        "1. ONE adult woman (18+), specific and distinctive, not interchangeable\n"
        "2. ULTRA-VIVID colors with deep blacks — never flat, never washed out\n"
        "3. SPECIFIC lighting: the light source has a location, color, and intensity\n"
        "4. DETAILED background that tells a story — never a gradient void\n"
        "5. The image must FEEL like the music genre — not just decorate it\n"
        "6. 9:16 vertical format\n"
        "7. Platform safe, non-sexualized\n"
        "8. Output ONLY the final prompt: comma-separated, 100-140 words, no preamble, no explanation"
    )

    user = f"""Create a scroll-stopping anime illustration prompt for a music YouTube Short.

SONG: "{song_name}"
PRIMARY GENRE: {style}
ALL GENRES: {all_styles}
SHORT #: {short_num} (make this DISTINCT from other shorts of this song)

CHARACTER (use this as foundation, make her SPECIFIC and MEMORABLE):
{character}

COMPOSITION (use this framing):
{composition}

COLOR PALETTE (execute this exactly — rich, vivid, maximum depth):
{palette}

CRITICAL: Connect the image to "{song_name}" emotionally — the SONG TITLE should influence
the specific mood, expression, or environment detail. Make someone feel the music just from the image.
100-140 words, comma-separated descriptors only."""

    resp = client.messages.create(
        model=get_anthropic_model(),
        max_tokens=400,
        system=system,
        messages=[{"role": "user", "content": user}],
    )

    raw  = resp.content[0].text.strip().strip('"').strip("'")
    full = f"{raw}, {QUALITY_TAGS}"
    print(f"  [Claude] Prompt gerado ({len(full)} chars) — short #{short_num}")
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
# GERAÇÃO VIA REPLICATE — Flux otimizado para anime vibrante
# ══════════════════════════════════════════════════════════════════════

REPLICATE_MODELS = [
    "black-forest-labs/flux-dev",
    "black-forest-labs/flux-schnell",
]

MODEL_PARAMS = {
    "black-forest-labs/flux-dev": {
        "num_inference_steps": 35,
        "aspect_ratio": "9:16",
        "guidance": 4.5,       # Alto para fidelidade ao prompt e cores vivas
        "output_format": "png",
        "output_quality": 98,
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
        print("  [Replicate] Token não configurado.")
        return None

    os.environ["REPLICATE_API_TOKEN"] = token
    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    full_prompt = _compact(
        prompt
        + ", anime illustration style, NOT photorealistic, NOT 3D render, "
        + "ultra-vibrant saturated colors, deep rich shadows, luminous vivid highlights, "
        + "sharp clean lineart, premium anime key visual quality, "
        + "specific distinctive character design, NOT generic"
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
                    print("  [Replicate] URL não encontrada")
                    continue
                saved = _download_image(url, output_path)
                if saved:
                    print(f"  [Replicate] Salvo: {saved}")
                    return saved
            except Exception as e:
                wait = 2 ** attempt
                print(f"  [Replicate] Erro: {e}. Aguardando {wait}s...")
                time.sleep(wait)

    print("  [Replicate] Todas as tentativas falharam.")
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
            print(f"  [Replicate] Imagem muito pequena ({size} bytes), descartando")
            os.remove(output_path)
            return None

        return output_path
    except Exception as e:
        print(f"  [Replicate] Download falhou: {e}")
        return None
