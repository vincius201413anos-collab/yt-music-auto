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
ENABLE_FACEBOOK = os.getenv("ENABLE_FACEBOOK", "true").lower() == "true"


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
# SISTEMA DE TÍTULOS — ULTRA VARIADO, ANTI-SHADOWBAN
# ══════════════════════════════════════════════════════════════════════

STYLE_HOOKS_MATRIX = {
    "phonk": {
        "vibe": [
            "Only real ones know this sound 🌑",
            "The underground called and left this 📲",
            "Some sounds don't belong in daylight 🌙",
            "This hit different at 3am 🕒",
            "Your night just got darker 🖤",
        ],
        "reaction": [
            "I wasn't ready for this one 😳",
            "Replayed this 47 times already 🔁",
            "Couldn't stop after the first 10 seconds 🎧",
            "This broke my headphones (worth it) 🎧",
            "My playlist deleted itself to make room 💀",
        ],
        "challenge": [
            "Try not to feel this one 😈",
            "Listen without losing focus. Impossible. 🚫",
            "Tell me you're not addicted after this 🔁",
            "One play and you'll understand 🌑",
            "First listen changes you. Not sorry. 😈",
        ],
        "discovery": [
            "You found this before it blows up 📌",
            "Save this. You'll want it at midnight. 💾",
            "Algorithm brought you here for a reason 🌐",
            "This was hiding. Now it found you. 🕵️",
            "Underground doesn't cover it 🔒",
        ],
    },
    "trap": {
        "vibe": [
            "Your playlist just got expensive 💸",
            "Only sounds this clean cost this much 💎",
            "The bass that changed the standard 🔊",
            "This is what confidence sounds like 👑",
            "Not everyone has taste. You do. 🖤",
        ],
        "reaction": [
            "The drop hit before I expected it 😮",
            "I've had this on repeat since 2am 🔁",
            "My speakers weren't built for this 🔊",
            "Skipped every other song after finding this 💀",
            "Couldn't finish it the first time. Too good. 😮",
        ],
        "challenge": [
            "Play this and see who looks up 👀",
            "Put this on at 3am, no headphones 🔊",
            "Try to stay seated during the bridge 😤",
            "Tell me you didn't feel that 808 🥁",
            "Find a reason to skip this. I'll wait. 🕐",
        ],
        "discovery": [
            "Before this hits 10 million 📈",
            "The streets know. Now you do. 🏙️",
            "Quietly destroying playlists everywhere 🔥",
            "Nobody's talking about this yet 🤫",
            "Underground certified, overground ready 🚀",
        ],
    },
    "rock": {
        "vibe": [
            "This guitar doesn't ask permission 🎸",
            "Built for stages that don't exist yet ⚡",
            "Not everyone will get it. That's the point. 🤘",
            "This is what pure energy sounds like 🔥",
            "The riff that demands your full attention 🎸",
        ],
        "reaction": [
            "First riff and I forgot what I was doing 🎸",
            "Headbanged alone in my car 🤘",
            "This shouldn't be this good 😤",
            "I paused everything to find this track 🔍",
            "The bridge destroyed me (in the best way) ⚡",
        ],
        "challenge": [
            "Don't move during the solo. Impossible. 🎸",
            "Try not to turn this up until it distorts 🔊",
            "Listen without air-guitaring. Bet you can't. 🤘",
            "Find one skip on this track. You won't. ⏭️",
            "Tell me this doesn't deserve louder 📢",
        ],
        "discovery": [
            "This band should be headlining already 🎪",
            "Rock still has something to say 🎸",
            "What you've been looking for without knowing ⚡",
            "The comeback of actual guitar 🎸",
            "Discovered this at 1am, no regrets 🌙",
        ],
    },
    "metal": {
        "vibe": [
            "This isn't music. This is a force of nature. ⚠️",
            "Built to break things that needed breaking 🔥",
            "The heaviness you asked the universe for 🌑",
            "Not for the faint of heart or quiet of room 🔊",
            "This transcends genre. It's pure weight. ⚡",
        ],
        "reaction": [
            "My neighbors finally moved because of this 😈",
            "This drop hit me physically 💀",
            "I needed to sit down after the breakdown 🤯",
            "Couldn't process this on first listen 🔁",
            "This changed what I thought was possible ⚡",
        ],
        "challenge": [
            "Full volume, full commitment, full damage 🔊",
            "Don't look away during the breakdown 😈",
            "Survive the drop and earn your metal card 🤘",
            "Max volume or don't even bother 🔊",
            "Find something heavier. I challenge you. ⚔️",
        ],
        "discovery": [
            "The underground doesn't want you to find this 🔒",
            "This exists and not enough people know it ⚠️",
            "Real heads already know. Now you know. 🤘",
            "Buried in the algorithm for a reason 📉",
            "Too good to stay hidden much longer 🌑",
        ],
    },
    "lofi": {
        "vibe": [
            "This is what 3am sounds like when it's okay 🌙",
            "Found the soundtrack to your unread thoughts 📖",
            "Some music holds your hand without you asking 🎧",
            "Peace you didn't know you needed today ☁️",
            "The sound of an exhale after a long day 🌙",
        ],
        "reaction": [
            "I paused everything to just exist in this 😮",
            "First 10 seconds and I slowed down 🌿",
            "This made the noise in my head quiet 🧠",
            "Accidentally stayed up 2 hours with this on 🌙",
            "Forgot I had a to-do list listening to this 📋",
        ],
        "challenge": [
            "Try to listen without getting lost in thought 💭",
            "One loop and tell me you're not calmer 🧘",
            "Find a better study companion. I'll wait. 📚",
            "Try to feel nothing during this. You can't. 🎧",
            "Listen once and not add it to your playlist 🔁",
        ],
        "discovery": [
            "The lofi gem that got away until now 💎",
            "This deserved more than it got 🕊️",
            "Playing this at the café and nobody asks to change it ☕",
            "Algorithm finally did something right 🙏",
            "Some music finds you at the right time ⏱️",
        ],
    },
    "indie": {
        "vibe": [
            "This band sounds like how nostalgia feels 🌅",
            "Written for everyone who felt this before words 📝",
            "Music that makes you miss something you can't name 🌙",
            "This is the feeling, not just the song 🌿",
            "Your heart needed this before you did 💙",
        ],
        "reaction": [
            "First verse hit and I stopped scrolling 🛑",
            "I've replayed the bridge six times already 🔁",
            "This song said what I couldn't find words for 💬",
            "Added to my playlist before the song even ended ⚡",
            "I don't know this band yet but I will 🔍",
        ],
        "challenge": [
            "Try to explain why this one hits different 🤔",
            "One listen and pretend it didn't stay with you 🎶",
            "Don't add this to a playlist. I dare you. 📌",
            "Find the moment you stopped hearing and started feeling 🎧",
            "Explain the bridge without getting emotional 😤",
        ],
        "discovery": [
            "Before everyone discovers this one 🔮",
            "Some artists deserve more rooms than they get 🎪",
            "Hidden because it's real, not because it's bad 💎",
            "The internet finds everything eventually. Found. 🌐",
            "Heard this once and wanted to tell everyone 📣",
        ],
    },
    "electronic": {
        "vibe": [
            "This drop exists in a different dimension 🌀",
            "Built for speakers that could handle it 🔊",
            "Some frequencies were made for stadiums 🏟️",
            "This is what the future sounds like already 🚀",
            "Peak energy. No other explanation needed. ⚡",
        ],
        "reaction": [
            "The drop came when I wasn't ready 💀",
            "This made me pace my apartment at midnight 🌙",
            "Heard it once in a set and hunted it for weeks 🔍",
            "This is why I don't sleep before festivals 🎉",
            "My body moved before my brain processed this 🕺",
        ],
        "challenge": [
            "Stay still during the drop. Not possible. 🕺",
            "Full volume, dark room, and no regrets 🔊",
            "Don't feel the bass in your chest. Can't. 🫀",
            "Find a harder drop anywhere. Go ahead. 🔎",
            "Listen without wanting to be in a crowd 🏟️",
        ],
        "discovery": [
            "Before this fills every festival stage 🌍",
            "Producers are taking notes right now 📝",
            "The ID you were looking for 🔍",
            "Underground until it isn't. Watch. 👀",
            "This producer is about to be everywhere 🚀",
        ],
    },
    "dark": {
        "vibe": [
            "Some music only makes sense past midnight 🌑",
            "Beautiful in a way that makes you ache 🖤",
            "This melody was not made for daylight 🕯️",
            "The sound of something vast and quiet 🌌",
            "Darkness with a pulse 🌑",
        ],
        "reaction": [
            "This stopped me completely. Just listened. 🕯️",
            "I don't know what this made me feel but it was real 😶",
            "This rewired something I didn't know was wired 🧠",
            "Listened four times trying to understand it 🔁",
            "This stayed in my head for three days 💭",
        ],
        "challenge": [
            "Listen alone at night and feel nothing. Can't. 🌑",
            "Explain the feeling this gives you. You can't. 🖤",
            "Try to skip this before the end. Won't. 🎧",
            "Describe it to someone. Watch them not understand. 🌌",
            "Find the word for what this makes you feel 📖",
        ],
        "discovery": [
            "This existed before you found it. Glad you did. 🕯️",
            "Not everything good gets loud. This proves it. 🌑",
            "The quiet ones always hit deepest 🖤",
            "Some music lives in the margins. Worth finding. 🔍",
            "Hidden in plain sight for whoever was ready 🌌",
        ],
    },
    "cinematic": {
        "vibe": [
            "This sounds like the scene they cut for being too good 🎬",
            "Built for a movie that hasn't been made yet 🎥",
            "Some music makes you feel like the main character 🌅",
            "This expands whatever room you're in 🌌",
            "The score your life didn't know it needed 🎻",
        ],
        "reaction": [
            "I stopped moving and just let this play 🎬",
            "This hit harder than any film I've seen this year 🎥",
            "The build up is almost unfair 🌊",
            "I needed a moment after this ended 😶",
            "This unlocked something I hadn't felt in a while 🌅",
        ],
        "challenge": [
            "Listen without closing your eyes. Impossible. 🎬",
            "Try not to imagine a whole scene in your head 🎥",
            "Feel nothing during the climax. You won't. 🌊",
            "One listen and tell me this isn't cinematic 🎻",
            "Don't get lost in this. Warning. 🌌",
        ],
        "discovery": [
            "The composer nobody talks about yet 🎼",
            "This score deserves a film worthy of it 🎬",
            "Found this at 2am and couldn't stop 🌙",
            "Cinematic music that doesn't need a screen 🎥",
            "This existed quietly. Now you know. 🌅",
        ],
    },
    "funk": {
        "vibe": [
            "Your body already knows what to do 🕺",
            "Groove that doesn't ask, just takes over 🎵",
            "This is what the weekend sounds like 🔥",
            "Pure Brazilian energy, no explanation needed 🇧🇷",
            "The kind of funk that moves furniture 🕺",
        ],
        "reaction": [
            "I was sitting down. Key word: was. 🕺",
            "This broke my focus immediately 😤",
            "Nobody warned me about the bassline 🎸",
            "Had to replay it twice before I believed it 🔁",
            "The groove hit and I lost track of time 🕐",
        ],
        "challenge": [
            "Stay still during this bassline. Can't. 🕺",
            "Don't nod your head. Impossible. 🎵",
            "One play without dancing. I dare you. 💃",
            "Try to listen without smiling. Won't happen. 😁",
            "Find a cleaner groove. I'll wait. 🎸",
        ],
        "discovery": [
            "Brazilian funk before the rest of the world catches on 🇧🇷",
            "This groove was hiding and now it isn't 🕵️",
            "The find that changes your playlist forever 📌",
            "Underground Brazilian sound, overground energy 🚀",
            "This producer is too good for how quiet it's been 🎼",
        ],
    },
    "pop": {
        "vibe": [
            "This is why pop still matters 🎵",
            "Addictive before the chorus even drops 🔁",
            "Built to be stuck in your head for days 🧠",
            "Clean, sharp, and impossible to skip 💫",
            "The hook that ruins every other song after it 🎵",
        ],
        "reaction": [
            "I didn't expect this to hit that hard 😮",
            "The chorus came and I replayed from the start 🔁",
            "This is what 'earworm' actually means 🎧",
            "Caught myself humming this hours later 🎵",
            "Skipped it once. Came back immediately. 🔁",
        ],
        "challenge": [
            "Try to get the chorus out of your head 🧠",
            "One listen and don't hum it for the rest of the day 🎵",
            "Skip before the hook. You physically cannot. ⏭️",
            "Find a cleaner chorus this year. Go ahead. 🔎",
            "Listen once and not add it. Impossible. 📌",
        ],
        "discovery": [
            "Pop music still has surprises left 🎵",
            "Before this is on every playlist everywhere 📈",
            "The song that's about to be inescapable 🌍",
            "Early on this one. Remember that. 📌",
            "This artist is about to be very famous 🚀",
        ],
    },
    "default": {
        "vibe": [
            "Music that doesn't need an introduction 🎵",
            "Some sounds work immediately and you don't know why 🎧",
            "This deserves your best pair of headphones 🎧",
            "The playlist addition you didn't plan for 🎵",
            "Real ones recognize quality instantly 💎",
        ],
        "reaction": [
            "First 15 seconds and I was done for 🎧",
            "This changed the energy of whatever I was doing 🔁",
            "I stopped to find out who made this 🔍",
            "This hit like it was made for me specifically 🎵",
            "Couldn't skip it even when I tried 🔁",
        ],
        "challenge": [
            "One play and pretend you're not coming back 🔁",
            "Find a reason to take this off your playlist 🔎",
            "Skip this. See what happens. You won't. ⏭️",
            "Argue that this doesn't belong in your favorites 💎",
            "Listen without it improving your mood. Impossible. 😌",
        ],
        "discovery": [
            "Before this belongs to everyone else 🔮",
            "The early find you'll tell people about 📣",
            "Some things arrive before their moment. This is that. ⏱️",
            "You found this. That means something. 📌",
            "Early listener energy. This grows. 🌱",
        ],
    },
}

HOOK_CATEGORY_ROTATION = ["vibe", "reaction", "challenge", "discovery", "vibe"]

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

TITLE_TEMPLATES = [
    "{hook} | {base}",
    "{base} — {hook}",
    "{hook} 👇 | {base}",
    "{base} | {hook}",
    "🎵 {base} | {hook}",
]


def build_title(base: str, style: str, short_num: int) -> str:
    category = HOOK_CATEGORY_ROTATION[(short_num - 1) % len(HOOK_CATEGORY_ROTATION)]
    hooks_by_style = STYLE_HOOKS_MATRIX.get(style, STYLE_HOOKS_MATRIX["default"])
    hooks = hooks_by_style.get(category, hooks_by_style["vibe"])
    hook_idx = (short_num - 1) % len(hooks)
    hook = hooks[hook_idx]
    template = TITLE_TEMPLATES[(short_num - 1) % len(TITLE_TEMPLATES)]
    return template.format(hook=hook, base=base)[:100]


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
        t.setdefault("genre", None)  # cache do gênero detectado

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

    try:
        log("Baixando audio do Drive...")
        download_drive_file(service, track["id"], audio_path)
        log("Download concluido.")

        # ── DETECÇÃO DE GÊNERO ACÚSTICA ──────────────────────────────
        # Usa cache do state.json se já detectou antes (evita re-análise)
        cached_genre = track.get("genre")
        if cached_genre:
            style = cached_genre
            styles = detect_genre_multi(audio_path)
            log(f"Genero (cache): {style}")
        else:
            log("Detectando genero por analise acustica...")
            style = detect_genre(audio_path)
            styles = detect_genre_multi(audio_path)
            track["genre"] = style  # salva no cache
            save_state(state)
            log(f"Genero detectado: {style} | Secundarios: {', '.join(styles[1:] or ['nenhum'])}")

        date = datetime.utcnow().strftime("%Y-%m-%d")
        output_dir = Path("output") / date / style
        output_dir.mkdir(parents=True, exist_ok=True)
        video_path = str(
            output_dir / f"{date}__{style}__{safe_filename(title_base)}__s{short_num}.mp4"
        )

        log(f"Gerando background (short {short_num})...")
        bg = resolve_background(style, name, short_num, styles)

        log("Gerando video...")
        video_path = create_short(audio_path, bg, video_path, style, song_name=title_base)
        log(f"Video pronto: {video_path}")

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
