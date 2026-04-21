import os
import json
import re
import random
import time
from pathlib import Path
from datetime import datetime

from drive_service import (
    get_drive_service,
    find_folder_id,
    list_audio_files_in_folder,
    download_drive_file,
    upload_file_to_drive,
)
from background_selector import get_random_background
from genre_detector import detect_genre, detect_genre_multi
from video_generator import create_short
from youtube_service import upload_video
from facebook_service import upload_to_facebook
from ai_image_generator import generate_image, build_ai_prompt

STATE_FILE = Path("state.json")
SHORTS_PER_TRACK = 5

DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")
DRIVE_BACKUP_FOLDER_ID = os.getenv("DRIVE_BACKUP_FOLDER_ID", "").strip()

SPOTIFY_LINK = "https://open.spotify.com/intl-pt/artist/1zyM1Pyi4YLAQgrSVRAYEy"
TIKTOK_LINK = "https://www.tiktok.com/@darkmrkedit"

ENABLE_YOUTUBE = os.getenv("ENABLE_YOUTUBE", "true").lower() == "true"
# Facebook desligado por padrão até configurar as chaves
ENABLE_FACEBOOK = os.getenv("ENABLE_FACEBOOK", "false").lower() == "true"


def log(msg: str):
    print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] {msg}")


def clean_title(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(r"\[[^\]]*\]|\{[^\}]*\}|\([^\)]*\)", "", name)
    name = re.sub(r"[_\-]+", " ", name)
    return re.sub(r"\s+", " ", name).strip().title()


def safe_filename(text: str) -> str:
    text = re.sub(r"[^\w\s\-]", "", text.lower())
    return re.sub(r"\s+", "_", text)[:60]


def human_delay():
    secs = random.randint(15, 45)
    log(f"Aguardando {secs}s antes do proximo upload...")
    time.sleep(secs)


# ══════════════════════════════════════════════════════════════════════
# SISTEMA DE TÍTULOS — NATURAL, VARIADO, ANTI-SHADOWBAN
# ══════════════════════════════════════════════════════════════════════

TITLE_BANK = {
    "phonk": [
        [
            "{base} — you found this before it blows up 🌑",
            "this one's different. {base} 🖤",
            "{base} | the underground just found you 📲",
            "save this. {base} 🌙",
            "the algorithm finally got it right 🌑 | {base}",
            "{base} — some sounds don't belong in daylight 🕒",
        ],
        [
            "i wasn't ready for {base} 😳",
            "{base} — replayed this more times than i'll admit 🔁",
            "put this on at 3am and lost track of time | {base} 🌙",
            "{base} | first 10 seconds. done. 🎧",
            "this one got me | {base} 🖤",
            "{base} — wasn't expecting to feel this 😮",
        ],
        [
            "try not to feel {base} 😈",
            "{base} | tell me you're not coming back to this 🔁",
            "one play and you'll understand | {base} 🌑",
            "{base} — first listen changes something 😈",
            "listen once. just once. | {base} 🎧",
            "{base} | if you know, you know 🖤",
        ],
        [
            "{base} — 3am in an empty parking lot 🌑",
            "the sound of driving nowhere at midnight | {base} 🚗",
            "{base} | dark energy, no explanation needed 🖤",
            "this is what focus sounds like | {base} 😤",
            "{base} — cold, calculated, different 🌙",
            "night driving music | {base} 🌑",
        ],
        [
            "{base} 🌑",
            "{base} | this one speaks for itself 🖤",
            "just listen. {base} 🎧",
            "{base} — no words needed 🌙",
            "🖤 {base}",
            "{base} | you already know 😈",
        ],
    ],
    "trap": [
        [
            "{base} — before this hits everywhere 📈",
            "the streets know | {base} 🏙️",
            "{base} | found this and couldn't move on 💎",
            "nobody's talking about this yet | {base} 🤫",
            "{base} — this one's different 👑",
            "underground certified | {base} 🔒",
        ],
        [
            "the bass on {base} hit different 🔊",
            "{base} | my speakers weren't ready 💀",
            "skipped everything else after hearing {base} 🔁",
            "{base} — the drop came early and i wasn't ready 😮",
            "this 808 | {base} 🥁",
            "{base} | replayed the drop six times 🔊",
        ],
        [
            "play {base} and see who looks up 👀",
            "{base} | tell me you didn't feel that 😤",
            "find a reason to skip this. i'll wait | {base} 🕐",
            "{base} — one play and you'll understand 💎",
            "try not to nod to {base} 🔊",
            "{base} | if you skipped this you're missing out 👑",
        ],
        [
            "{base} — this is what confidence sounds like 👑",
            "luxury audio | {base} 💸",
            "{base} | not everyone has taste. you do. 🖤",
            "clean, expensive, different | {base} 💎",
            "{base} — the standard just changed 📈",
            "penthouse vibes | {base} 🏙️",
        ],
        [
            "{base} 💎",
            "🏙️ {base}",
            "{base} | speaks for itself 👑",
            "just run it | {base} 🔊",
            "{base} — trust me 💸",
            "👑 {base}",
        ],
    ],
    "rock": [
        [
            "{base} — this riff doesn't ask permission 🎸",
            "rock still has something to say | {base} ⚡",
            "{base} | found this at 1am, no regrets 🌙",
            "this band should be headlining | {base} 🎪",
            "{base} — the comeback of actual guitar 🎸",
            "what you've been looking for | {base} ⚡",
        ],
        [
            "the first riff on {base} made me stop 🎸",
            "{base} | headbanged alone in my car 🤘",
            "this shouldn't be this good | {base} 😤",
            "{base} — the bridge got me 🎸",
            "paused everything to find this | {base} 🔍",
            "{base} | the solo hit different ⚡",
        ],
        [
            "don't move during the solo. impossible | {base} 🎸",
            "{base} | tell me this doesn't deserve louder 📢",
            "listen without air guitaring. bet you can't | {base} 🤘",
            "{base} — find one skip. you won't ⏭️",
            "full volume. now. | {base} 🔊",
            "{base} | try not to feel this one ⚡",
        ],
        [
            "{base} — built for stages that don't exist yet ⚡",
            "pure energy | {base} 🔥",
            "{base} | this is what real sounds like 🎸",
            "the energy on this | {base} ⚡",
            "{base} — raw and real 🎸",
            "this is rock | {base} 🤘",
        ],
        [
            "{base} 🎸",
            "⚡ {base}",
            "{base} | play it loud 🔊",
            "🤘 {base}",
            "{base} — full volume ⚡",
            "just turn it up | {base} 🎸",
        ],
    ],
    "metal": [
        [
            "{base} — the underground doesn't want you finding this 🔒",
            "too heavy for most. not you | {base} 🌑",
            "{base} | this exists and not enough people know 🤘",
            "real heads know | {base} ⚠️",
            "{base} — buried in the algorithm for a reason 📉",
            "this band is too good for how quiet it's been | {base} 🌑",
        ],
        [
            "the breakdown on {base} hit physically 💀",
            "{base} | my neighbors moved because of this 😈",
            "couldn't process this on first listen | {base} 🔁",
            "{base} — needed to sit after the drop 🤯",
            "this changed what i thought was possible | {base} ⚡",
            "{base} | wasn't ready 💀",
        ],
        [
            "max volume or don't bother | {base} 🔊",
            "{base} | find something heavier. i challenge you ⚔️",
            "survive the breakdown | {base} 🤘",
            "{base} — full commitment, full damage 🔊",
            "don't look away during this | {base} 😈",
            "{base} | this isn't for everyone. maybe for you ⚠️",
        ],
        [
            "{base} — this isn't music. it's a force. ⚠️",
            "pure weight | {base} 🌑",
            "{base} | the heaviness you asked the universe for 🔥",
            "not for the quiet of room | {base} 🔊",
            "{base} — it transcends genre ⚡",
            "ancient and brutal | {base} 🌑",
        ],
        [
            "{base} ⚠️",
            "🌑 {base}",
            "{base} | if you know you know 🤘",
            "just experience it | {base} ⚔️",
            "{base} — no words 💀",
            "⚡ {base}",
        ],
    ],
    "lofi": [
        [
            "{base} — some music finds you at the right time ⏱️",
            "this lofi gem deserved more | {base} 💎",
            "{base} | algorithm finally did something right 🙏",
            "the one playing at the café | {base} ☕",
            "{base} — this deserved more than it got 🕊️",
            "found this late. better than never | {base} 🌙",
        ],
        [
            "paused everything to exist in {base} 😮",
            "{base} | first 10 seconds and i slowed down 🌿",
            "this made the noise in my head quiet | {base} 🧠",
            "{base} — accidentally stayed up with this on 🌙",
            "forgot i had a to-do list | {base} 📋",
            "{base} | this one pulled me out of it 🎧",
        ],
        [
            "try to listen without getting lost | {base} 💭",
            "{base} | one loop and tell me you're not calmer 🧘",
            "find a better study companion. i'll wait | {base} 📚",
            "{base} — try to feel nothing. you can't 🎧",
            "listen once and not save it | {base} 🔁",
            "{base} | just put it on and breathe ☁️",
        ],
        [
            "{base} — this is what 3am sounds like when it's okay 🌙",
            "the soundtrack to your unread thoughts | {base} 📖",
            "{base} | peace you didn't know you needed ☁️",
            "the sound of an exhale after a long day | {base} 🌙",
            "{base} — quiet and real 🌿",
            "this holds your hand without asking | {base} 🎧",
        ],
        [
            "{base} 🌙",
            "☁️ {base}",
            "{base} | late night feels 🎧",
            "just {base} 🌿",
            "{base} — cozy season 🌙",
            "🎧 {base}",
        ],
    ],
    "indie": [
        [
            "{base} — before everyone discovers this one 🔮",
            "some artists deserve more rooms | {base} 🎪",
            "{base} | heard this once and told everyone 📣",
            "the internet finds everything eventually | {base} 🌐",
            "{base} — hidden because it's real 💎",
            "early on this one | {base} 📌",
        ],
        [
            "first verse on {base} and i stopped scrolling 🛑",
            "{base} | replayed the bridge six times 🔁",
            "this said what i couldn't find words for | {base} 💬",
            "{base} — added before it ended ⚡",
            "i don't know this band yet but i will | {base} 🔍",
            "{base} | wasn't expecting to feel something 😮",
        ],
        [
            "try to explain why {base} hits like this 🤔",
            "{base} | pretend it didn't stay with you 🎶",
            "don't add this to a playlist. i dare you | {base} 📌",
            "{base} — the bridge. that's it. that's the post 😤",
            "find the moment you stopped hearing | {base} 🎧",
            "{base} | one listen. just one 🌅",
        ],
        [
            "{base} — sounds like how nostalgia feels 🌅",
            "music that makes you miss something you can't name | {base} 🌙",
            "{base} | the feeling, not just the song 🌿",
            "your heart needed this | {base} 💙",
            "{base} — written for everyone who felt this before words 📝",
            "this is the feeling | {base} 🌅",
        ],
        [
            "{base} 🌅",
            "🌿 {base}",
            "{base} | just feel it 💙",
            "🎶 {base}",
            "{base} — still thinking about it 🌙",
            "just {base} 🌅",
        ],
    ],
    "electronic": [
        [
            "{base} — before this fills every festival stage 🌍",
            "producers are taking notes | {base} 📝",
            "{base} | the ID you were looking for 🔍",
            "underground until it isn't. watch | {base} 👀",
            "{base} — this producer is about to be everywhere 🚀",
            "early on {base} | remember this 📌",
        ],
        [
            "the drop on {base} came when i wasn't ready 💀",
            "{base} | paced my apartment at midnight after this 🌙",
            "heard this once in a set and hunted it for weeks | {base} 🔍",
            "{base} — this is why i don't sleep before festivals 🎉",
            "my body moved before my brain did | {base} 🕺",
            "{base} | the drop hit different 🔊",
        ],
        [
            "stay still during the drop. not possible | {base} 🕺",
            "{base} | find a harder drop. go ahead 🔎",
            "full volume, dark room | {base} 🔊",
            "{base} — don't feel the bass in your chest. can't 🫀",
            "listen without wanting to be in a crowd | {base} 🏟️",
            "{base} | try not to move. impossible 🕺",
        ],
        [
            "{base} — this drop exists in a different dimension 🌀",
            "built for speakers that could handle it | {base} 🔊",
            "{base} | peak energy, no explanation needed ⚡",
            "some frequencies were made for stadiums | {base} 🏟️",
            "{base} — the future sounds like this already 🚀",
            "this is what the drop feels like | {base} ⚡",
        ],
        [
            "{base} ⚡",
            "🌀 {base}",
            "{base} | the drop 🔊",
            "🚀 {base}",
            "{base} — just run it ⚡",
            "turn it up | {base} 🔊",
        ],
    ],
    "dark": [
        [
            "{base} — this existed before you found it 🕯️",
            "not everything good gets loud | {base} 🌑",
            "{base} | the quiet ones hit deepest 🖤",
            "hidden in plain sight for whoever was ready | {base} 🌌",
            "{base} — some music lives in the margins 🔍",
            "this one found you for a reason | {base} 🕯️",
        ],
        [
            "{base} stopped me completely 🕯️",
            "i don't know what this made me feel but it was real | {base} 😶",
            "{base} — stayed in my head for three days 💭",
            "listened four times trying to understand | {base} 🔁",
            "{base} | this rewired something 🧠",
            "just sat with {base} for a while 🌑",
        ],
        [
            "listen alone at night | {base} 🌑",
            "{base} | explain the feeling. you can't 🖤",
            "try to skip this before the end. won't | {base} 🎧",
            "{base} — find the word for what this makes you feel 📖",
            "describe it to someone. watch them not get it | {base} 🌌",
            "{base} | just be in it 🕯️",
        ],
        [
            "{base} — some music only makes sense past midnight 🌑",
            "beautiful in a way that makes you ache | {base} 🖤",
            "{base} | this melody wasn't made for daylight 🕯️",
            "darkness with a pulse | {base} 🌑",
            "{base} — the sound of something vast and quiet 🌌",
            "this isn't for everyone | {base} 🖤",
        ],
        [
            "{base} 🖤",
            "🌑 {base}",
            "{base} | midnight 🕯️",
            "just {base} 🌌",
            "{base} — you'll understand 🖤",
            "🕯️ {base}",
        ],
    ],
    "cinematic": [
        [
            "{base} — this score deserves a film worthy of it 🎬",
            "cinematic music that doesn't need a screen | {base} 🎥",
            "{base} | found this at 2am and couldn't stop 🌙",
            "the composer nobody talks about yet | {base} 🎼",
            "{base} — this existed quietly. now you know 🌅",
            "early on {base} | watch what happens 📌",
        ],
        [
            "stopped moving and let {base} play 🎬",
            "{base} | the buildup is almost unfair 🌊",
            "this hit harder than any film this year | {base} 🎥",
            "{base} — needed a moment after this ended 😶",
            "this unlocked something | {base} 🌅",
            "{base} | wasn't ready for that climax 🎻",
        ],
        [
            "listen without closing your eyes. impossible | {base} 🎬",
            "{base} | try not to imagine a whole scene 🎥",
            "feel nothing during the climax. you won't | {base} 🌊",
            "{base} — don't get lost in this. warning 🌌",
            "tell me this isn't cinematic | {base} 🎻",
            "{base} | one listen. seriously 🎬",
        ],
        [
            "{base} — sounds like the scene they cut for being too good 🎬",
            "built for a movie that hasn't been made yet | {base} 🎥",
            "{base} | makes you feel like the main character 🌅",
            "the score your life didn't know it needed | {base} 🎻",
            "{base} — this expands whatever room you're in 🌌",
            "epic from the first second | {base} 🎬",
        ],
        [
            "{base} 🎬",
            "🎻 {base}",
            "{base} | just experience it 🌌",
            "🌅 {base}",
            "{base} — no words 🎥",
            "just {base} 🎬",
        ],
    ],
    "funk": [
        [
            "{base} — brazilian funk before the world catches on 🇧🇷",
            "this groove was hiding | {base} 🕵️",
            "{base} | the find that changes your playlist 📌",
            "underground sound, overground energy | {base} 🚀",
            "{base} — too good for how quiet it's been 🎼",
            "early on {base} | trust me 📌",
        ],
        [
            "i was sitting down. key word: was | {base} 🕺",
            "{base} | nobody warned me about the bassline 🎸",
            "the groove hit and i lost track of time | {base} 🕐",
            "{base} — replayed it twice before i believed it 🔁",
            "this broke my focus immediately | {base} 😤",
            "{base} | wasn't expecting this 🕺",
        ],
        [
            "stay still during this bassline. can't | {base} 🕺",
            "{base} | don't nod your head. impossible 🎵",
            "one play without dancing. i dare you | {base} 💃",
            "{base} — find a cleaner groove. i'll wait 🎸",
            "try to listen without smiling | {base} 😁",
            "{base} | just try 🕺",
        ],
        [
            "{base} — your body already knows what to do 🕺",
            "groove that just takes over | {base} 🎵",
            "{base} | this is what the weekend sounds like 🔥",
            "pure energy, no explanation | {base} 🇧🇷",
            "{base} — the kind that moves furniture 🕺",
            "this feels alive | {base} 🔥",
        ],
        [
            "{base} 🕺",
            "🔥 {base}",
            "{base} | just move 🎵",
            "💃 {base}",
            "{base} — you'll understand 🕺",
            "🇧🇷 {base}",
        ],
    ],
    "pop": [
        [
            "{base} — before this is on every playlist 📈",
            "pop music still has surprises | {base} 🎵",
            "{base} | early on this one. remember that 📌",
            "the song that's about to be inescapable | {base} 🌍",
            "{base} — this artist is about to be famous 🚀",
            "caught this before it blew up | {base} 📌",
        ],
        [
            "didn't expect {base} to hit that hard 😮",
            "{base} | the chorus came and i replayed from the start 🔁",
            "caught myself humming {base} hours later 🎵",
            "{base} — skipped it once. came back immediately 🔁",
            "this is what earworm actually means | {base} 🎧",
            "{base} | addictive from second one 🔁",
        ],
        [
            "try to get {base} out of your head 🧠",
            "{base} | skip before the hook. you can't ⏭️",
            "find a cleaner chorus this year | {base} 🔎",
            "{base} — don't hum this for the rest of the day. impossible 🎵",
            "listen once and not add it | {base} 📌",
            "{base} | try to forget this 🧠",
        ],
        [
            "{base} — addictive before the chorus even drops 🔁",
            "built to stay in your head | {base} 🧠",
            "{base} | clean and impossible to skip 💫",
            "the hook that ruins everything after | {base} 🎵",
            "{base} — this is why pop still matters 🎵",
            "genuinely good pop | {base} 💫",
        ],
        [
            "{base} 🎵",
            "💫 {base}",
            "{base} | trust 🔁",
            "🎵 {base}",
            "{base} — you'll see 📈",
            "just {base} 💫",
        ],
    ],
    "default": [
        [
            "{base} — found this before it blows up 🔮",
            "early on this one | {base} 📌",
            "{base} | some things arrive before their moment 🌱",
            "the early find you'll tell people about | {base} 📣",
            "{base} — this grows 🌱",
            "you found this. that means something | {base} 📌",
        ],
        [
            "first 15 seconds on {base} and i was done 🎧",
            "{base} | couldn't skip it even when i tried 🔁",
            "this hit like it was made for me | {base} 🎵",
            "{base} — stopped to find out who made this 🔍",
            "changed the energy of my entire day | {base} 🔁",
            "{base} | wasn't expecting this 🎧",
        ],
        [
            "one play and pretend you're not coming back | {base} 🔁",
            "{base} | find a reason to take this off your playlist 🔎",
            "skip this. see what happens | {base} ⏭️",
            "{base} — listen without it improving your mood. impossible 😌",
            "argue this doesn't belong in your favorites | {base} 💎",
            "{base} | just try to skip it 🔁",
        ],
        [
            "{base} — real ones recognize quality immediately 💎",
            "this deserves your best headphones | {base} 🎧",
            "{base} | the playlist addition you didn't plan for 🎵",
            "some sounds work immediately | {base} 🎧",
            "{base} — doesn't need an introduction 🎵",
            "magnetic from the start | {base} 💎",
        ],
        [
            "{base} 🎵",
            "🎧 {base}",
            "{base} | just listen 💎",
            "🎶 {base}",
            "{base} — trust me 🎵",
            "just {base} 🎧",
        ],
    ],
}

STYLE_HASHTAGS = {
    "phonk":      "#phonk #darkphonk #phonkmusic #phonkdrift #phonkvibes #phonkedit #phonkcar",
    "trap":       "#trap #trapmusic #808s #trapbeats #undergroundhiphop #trapvibes #newmusic",
    "rock":       "#rock #rockmusic #guitarmusic #hardrock #alternative #alternativerock #newrock",
    "metal":      "#metal #heavymetal #metalhead #metalcore #extrememetal #newmetal #heavymusic",
    "lofi":       "#lofi #lofihiphop #studymusic #chillvibes #lofibeats #relaxingmusic #lofichill",
    "indie":      "#indie #indiemusic #alternativemusic #indiepop #indierock #emotionalmusic #indievibes",
    "electronic": "#electronic #edm #synthwave #electronicmusic #techno #dancemusic #festivalmusic",
    "cinematic":  "#cinematic #cinematicmusic #epicmusic #orchestral #filmmusic #epicorchestral #dramatic",
    "funk":       "#funk #funkmusic #groove #brazilianmusic #soulmusic #funkychill #groovemusic",
    "dark":       "#dark #darkmusic #gothic #darkambient #darkwave #atmospheric #hauntingmusic",
    "pop":        "#pop #popmusic #popvibes #newmusic #chart #top40 #hitmusic",
    "default":    "#music #newmusic #viralmusic #underground #musiclover #musicdiscovery #hiddengems",
}

UNIVERSAL = "#shorts #youtubeshorts #viral #fyp #trending #musicshorts #shortsvideo"


def build_title(base: str, style: str, short_num: int) -> str:
    bank = TITLE_BANK.get(style, TITLE_BANK["default"])
    group_idx = (short_num - 1) % len(bank)
    group = bank[group_idx]

    import hashlib
    seed = int(hashlib.md5(f"{base}|{short_num}".encode()).hexdigest(), 16) % len(group)
    template = group[seed]
    title = template.format(base=base)
    return title[:100]


def build_description(base: str, style: str, short_num: int) -> str:
    tags = STYLE_HASHTAGS.get(style, STYLE_HASHTAGS["default"])
    ctas = [
        "Subscribe if you want more finds like this.",
        "Drop a comment if this hit right.",
        "Save this for later — you'll want it back.",
        "Follow for daily uploads of underground music.",
        "Like if this deserved more than it got.",
    ]
    cta = ctas[(short_num - 1) % len(ctas)]
    spotify_lines = [
        f"🎧 Full track on Spotify:\n{SPOTIFY_LINK}",
        f"🎵 Listen everywhere:\n{SPOTIFY_LINK}",
        f"🎧 Stream it:\n{SPOTIFY_LINK}",
        f"🔊 Full version on Spotify:\n{SPOTIFY_LINK}",
        f"📻 On Spotify now:\n{SPOTIFY_LINK}",
    ]
    spotify_line = spotify_lines[(short_num - 1) % len(spotify_lines)]
    return (
        f"🎵 {base}\n\n"
        f"{cta}\n\n"
        f"{spotify_line}\n\n"
        f"📲 TikTok:\n{TIKTOK_LINK}\n\n"
        f"{tags}\n{UNIVERSAL}"
    )


# ══════════════════════════════════════════════════════════════════════
# ESTADO
# ══════════════════════════════════════════════════════════════════════

def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"tracks": [], "alpha_index": 0}

    with STATE_FILE.open("r", encoding="utf-8") as f:
        state = json.load(f)

    state.pop("queue_index", None)
    state.pop("index", None)
    state.setdefault("tracks", [])
    state.setdefault("alpha_index", 0)

    for t in state["tracks"]:
        t.setdefault("done", 0)
        t.setdefault("is_new", False)
        t.setdefault("genre", None)

    return state


def save_state(state: dict):
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def sync_tracks(state: dict, files: list):
    existing = {t["name"]: t for t in state["tracks"]}

    for f in files:
        if f["name"] not in existing:
            log(f"Nova musica: {f['name']}")
            state["tracks"].append({
                "id": f["id"],
                "name": f["name"],
                "done": 0,
                "is_new": True,
                "genre": None,
            })
        else:
            existing[f["name"]]["id"] = f["id"]

    drive_names = {f["name"] for f in files}
    state["tracks"] = [t for t in state["tracks"] if t["name"] in drive_names]
    state["tracks"].sort(key=lambda t: t["name"].lower())

    n = len(state["tracks"])
    state["alpha_index"] = state.get("alpha_index", 0) % n if n else 0


def get_next_track(state: dict) -> dict | None:
    tracks = state["tracks"]
    if not tracks:
        return None

    new_tracks = [t for t in tracks if t.get("is_new") and t.get("done", 0) == 0]
    if new_tracks:
        chosen = new_tracks[0]
        log(f"Prioridade para nova musica: {chosen['name']}")
        chosen["is_new"] = False
        return chosen

    n = len(tracks)
    idx = state.get("alpha_index", 0) % n

    for i in range(n):
        t = tracks[(idx + i) % n]
        if t.get("done", 0) < SHORTS_PER_TRACK:
            state["alpha_index"] = (idx + i + 1) % n
            return t

    log("Rodada completa — resetando todos os contadores.")
    for t in tracks:
        t["done"] = 0
    state["alpha_index"] = 0
    return tracks[0]


# ══════════════════════════════════════════════════════════════════════
# BACKGROUND
# ══════════════════════════════════════════════════════════════════════

def resolve_background(style: str, filename: str, short_num: int, styles: list) -> str:
    os.makedirs("temp", exist_ok=True)

    try:
        prompt = build_ai_prompt(style, filename, styles, short_num=short_num)
        dest = f"temp/{Path(filename).stem}_{short_num}.png"
        img = generate_image(prompt, output_path=dest)
        if img and os.path.exists(img):
            log(f"Imagem IA gerada com sucesso: {img}")
            return img
    except Exception as e:
        log(f"IA falhou, tentando fallback local: {e}")

    try:
        bg = get_random_background(style, filename)
        if bg and not str(bg).startswith("__AUTO"):
            log(f"Usando background local: {bg}")
            return bg
    except Exception as e:
        log(f"Background local falhou: {e}")

    fallback = "assets/backgrounds/default.jpg"
    if os.path.exists(fallback):
        log("Usando background fallback padrao")
        return fallback

    raise FileNotFoundError("Nenhum background disponivel (IA, local e fallback falharam).")


# ══════════════════════════════════════════════════════════════════════
# PUBLICAÇÃO
# ══════════════════════════════════════════════════════════════════════

def publish(video_path: str, title: str, description: str) -> dict:
    results = {}

    if ENABLE_YOUTUBE:
        try:
            log("Postando no YouTube...")
            res = upload_video(video_path, title, description, [], "public")
            yt_id = res.get("id", "?") if isinstance(res, dict) else "?"
            log(f"  YouTube OK -> https://youtu.be/{yt_id}")
            results["youtube"] = {"ok": True, "id": yt_id}
            human_delay()
        except Exception as e:
            log(f"  YouTube ERRO: {e}")
            results["youtube"] = {"ok": False, "error": str(e)}
    else:
        results["youtube"] = {"ok": False, "skipped": True}

    if ENABLE_FACEBOOK:
        try:
            log("Postando no Facebook Reels...")
            res = upload_to_facebook(video_path, title, description)
            fb_id = res.get("id") or res.get("video_id", "?")
            log(f"  Facebook OK -> ID: {fb_id}")
            results["facebook"] = {"ok": True, "id": fb_id}
        except EnvironmentError as e:
            log(f"  Facebook nao configurado: {e}")
            results["facebook"] = {"ok": False, "skipped": True}
        except Exception as e:
            log(f"  Facebook ERRO: {e}")
            results["facebook"] = {"ok": False, "error": str(e)}
    else:
        results["facebook"] = {"ok": False, "skipped": True}

    return results


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════

def main():
    log("=" * 55)
    log("BOT INICIANDO — YouTube Shorts + Facebook Reels")
    log(f"  YouTube  : {'ATIVO' if ENABLE_YOUTUBE else 'DESABILITADO'}")
    log(f"  Facebook : {'ATIVO' if ENABLE_FACEBOOK else 'DESABILITADO'}")
    log(f"  Backup   : {'ATIVO' if DRIVE_BACKUP_FOLDER_ID else 'DESABILITADO'}")
    log("=" * 55)

    if not DRIVE_FOLDER_ID:
        raise ValueError("DRIVE_FOLDER_ID nao configurado nas variaveis de ambiente.")

    service = get_drive_service()
    inbox_id = find_folder_id(service, DRIVE_FOLDER_ID, "inbox")
    if not inbox_id:
        raise ValueError("Pasta 'inbox' nao encontrada no Drive.")

    files = list_audio_files_in_folder(service, inbox_id)
    log(f"Audios encontrados no Drive: {len(files)}")

    state = load_state()
    sync_tracks(state, files)
    save_state(state)

    if not state["tracks"]:
        log("Sem musicas para processar. Encerrando.")
        return

    track = get_next_track(state)
    if not track:
        log("Nenhuma faixa disponivel para processar.")
        return

    name = track["name"]
    short_num = track.get("done", 0) + 1
    title_base = clean_title(name)

    log(f"Musica  : {name}")
    log(f"Short   : {short_num}/{SHORTS_PER_TRACK}")

    os.makedirs("temp", exist_ok=True)
    audio_path = f"temp/{name}"

    bg = None
    style = "default"
    styles = ["default"]
    thumbnail_path = None

    try:
        log("Baixando audio do Drive...")
        download_drive_file(service, track["id"], audio_path)
        log("Download concluido.")

        cached_genre = track.get("genre")
        if cached_genre:
            style = cached_genre
            styles = detect_genre_multi(audio_path)
            log(f"Genero (cache): {style}")
        else:
            log("Detectando genero por analise acustica...")
            style = detect_genre(audio_path)
            styles = detect_genre_multi(audio_path)
            track["genre"] = style
            save_state(state)
            log(f"Genero detectado: {style} | Secundarios: {', '.join(styles[1:] or ['nenhum'])}")

        date = datetime.utcnow().strftime("%Y-%m-%d")
        output_dir = Path("output") / date / style
        output_dir.mkdir(parents=True, exist_ok=True)
        planned_video_path = str(
            output_dir / f"{date}__{style}__{safe_filename(title_base)}__s{short_num}.mp4"
        )

        log(f"Gerando background (short {short_num})...")
        bg = resolve_background(style, name, short_num, styles)

        log("Gerando video...")
        render_result = create_short(
            audio_path,
            bg,
            planned_video_path,
            style,
            song_name=title_base,
        )

        # Compatibilidade: create_short pode retornar string antiga
        # ou dict novo com output_path/thumbnail_path
        if isinstance(render_result, dict):
            video_path = render_result["output_path"]
            thumbnail_path = render_result.get("thumbnail_path")
        else:
            video_path = render_result
            thumbnail_path = None

        log(f"Video pronto: {video_path}")
        if thumbnail_path:
            log(f"Thumbnail pronta: {thumbnail_path}")

        title = build_title(title_base, style, short_num)
        description = build_description(title_base, style, short_num)
        log(f"Titulo  : {title}")

        results = publish(video_path, title, description)

        if DRIVE_BACKUP_FOLDER_ID:
            try:
                log("Salvando backup no Drive...")
                upload_file_to_drive(service, DRIVE_BACKUP_FOLDER_ID, video_path)
                log("  Backup salvo com sucesso.")
            except Exception as e:
                log(f"  Backup falhou (nao critico): {e}")
        else:
            log("  Backup desabilitado (DRIVE_BACKUP_FOLDER_ID nao configurado).")

        any_ok = any(r.get("ok") for r in results.values())
        all_skipped = all(r.get("skipped") for r in results.values())

        if not any_ok and not all_skipped:
            raise RuntimeError("Nenhuma plataforma recebeu o video com sucesso.")

        track["done"] = short_num
        save_state(state)

        log("=" * 55)
        log(f"CONCLUIDO — {name} (short {short_num}/{SHORTS_PER_TRACK})")
        log("=" * 55)

    finally:
        for path in [audio_path, bg]:
            try:
                if path and isinstance(path, str) and os.path.exists(path):
                    if path.startswith("temp/"):
                        os.remove(path)
                        log(f"Temporario removido: {path}")
            except Exception:
                pass


if __name__ == "__main__":
    main()
