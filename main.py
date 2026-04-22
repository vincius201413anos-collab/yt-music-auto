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

SHORTS_PER_TRACK = int(os.getenv("SHORTS_PER_TRACK", "1"))

DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")
DRIVE_BACKUP_FOLDER_ID = os.getenv("DRIVE_BACKUP_FOLDER_ID", "").strip()

SPOTIFY_LINK = "https://open.spotify.com/intl-pt/artist/1zyM1Pyi4YLAQgrSVRAYEy"
TIKTOK_LINK = "https://www.tiktok.com/@darkmrkedit"
CHANNEL_NAME = "DJ darkMark"

ENABLE_YOUTUBE = os.getenv("ENABLE_YOUTUBE", "true").lower() == "true"
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
    log(f"Waiting {secs}s before next upload...")
    time.sleep(secs)


# ══════════════════════════════════════════════════════════════════════
# TITLE SYSTEM V3 — English Only, DJ darkMark Branding
# ══════════════════════════════════════════════════════════════════════

# Hooks por gênero — curtos, impactantes, em inglês
STYLE_HOOKS = {
    "phonk": [
        "you weren't ready for this",
        "found before it blows up",
        "3am and can't stop replaying",
        "the algorithm finally got it right",
        "dark side of the underground",
        "this one hits different",
        "can't skip this one",
        "not for everyone",
        "midnight energy",
        "obsessed after 10 seconds",
    ],
    "trap": [
        "streets already know",
        "underground certified",
        "before it's everywhere",
        "the 808 you needed",
        "too clean to ignore",
        "nobody's talking about this yet",
        "drop hits hard",
        "early on this one",
        "straight from the underground",
        "this one's different",
    ],
    "rock": [
        "riff doesn't ask permission",
        "guitar is back",
        "can't air guitar and stay still",
        "turn it up immediately",
        "first riff stopped me cold",
        "shouldn't be this good",
        "volume up. now.",
        "found this at 1am",
        "this band deserves more",
        "no skip possible",
    ],
    "metal": [
        "too heavy for most. not for you",
        "breakdown hits physically",
        "the underground doesn't want you finding this",
        "survive the breakdown",
        "full volume or don't bother",
        "not for quiet rooms",
        "ancient and brutal",
        "this one transcends genre",
        "the heads already know",
        "pure sonic weight",
    ],
    "lofi": [
        "noise in my head stopped",
        "calm but addictive",
        "perfect 3am company",
        "forgot I had a to-do list",
        "loop this all night",
        "focus unlocked",
        "best study session soundtrack",
        "slow everything down",
        "peace you didn't know you needed",
        "this one holds your hand",
    ],
    "indie": [
        "said what I couldn't find words for",
        "added before it finished",
        "the bridge. that's the whole post.",
        "found this before everyone else",
        "sounds like nostalgia feels",
        "just one listen",
        "can't explain why this hits",
        "early on this artist",
        "deserves bigger rooms",
        "this one stays with you",
    ],
    "electronic": [
        "drop hits different in the dark",
        "my body moved before my brain did",
        "early on this producer",
        "built for festival stages that don't exist yet",
        "max volume, dark room",
        "can't stand still during the drop",
        "this frequency belongs in stadiums",
        "the future already sounds like this",
        "producers are taking notes",
        "found the ID I was looking for",
    ],
    "dark": [
        "makes sense after midnight only",
        "beautiful in a way that hurts",
        "this melody wasn't made for daylight",
        "found hiding in the margins",
        "can't explain what this does",
        "try to skip before the end",
        "some frequencies were buried for a reason",
        "darkness with a pulse",
        "not for everyone",
        "3 days in my head",
    ],
    "cinematic": [
        "paused everything and just listened",
        "the build is almost unfair",
        "eyes closed. instantly.",
        "makes you feel like the main character",
        "composer nobody talks about yet",
        "harder than any film this year",
        "epic from the first second",
        "the scene they cut for being too good",
        "needs a film worthy of it",
        "one listen. seriously.",
    ],
    "funk": [
        "couldn't stay seated",
        "the groove took over",
        "bass hit before I was ready",
        "try not to move. impossible.",
        "weekend energy, any day",
        "cleanest groove I found this week",
        "this feels alive",
        "pure groove, no explanation needed",
        "replayed it twice before believing it",
        "your body already knows what to do",
    ],
    "pop": [
        "in your head before the chorus",
        "can't unhear this",
        "added before it finished",
        "hook ruins everything after it",
        "one listen and it's stuck",
        "try to get it out of your head",
        "this is why pop still matters",
        "cleanest hook this year",
        "skipped once. came back immediately.",
        "genuinely good pop",
    ],
    "default": [
        "found before it blows up",
        "can't skip this",
        "algorithm finally got it right",
        "one listen changes everything",
        "early on this one",
        "found this at midnight",
        "too good to be this hidden",
        "your playlist needed this",
        "obsessed after 10 seconds",
        "just trust me on this one",
    ],
}

# Templates de título — DJ darkMark sempre presente
TITLE_TEMPLATES = [
    "DJ darkMark | {hook} — {title}",
    "DJ darkMark — {title} | {hook}",
    "{hook} | {title} · DJ darkMark",
    "DJ darkMark 🎧 {title} | {hook}",
    "{title} — DJ darkMark | {hook}",
    "DJ darkMark: {hook} 🎵 {title}",
]

# Emojis por gênero para o título
GENRE_EMOJI = {
    "phonk":      "🌑",
    "trap":       "💎",
    "rock":       "🎸",
    "metal":      "⚠️",
    "lofi":       "🎧",
    "indie":      "🌅",
    "electronic": "⚡",
    "dark":       "🕯️",
    "cinematic":  "🎬",
    "funk":       "🕺",
    "pop":        "💫",
    "default":    "🎵",
}

STYLE_HASHTAGS = {
    "phonk":      "#phonk #darkphonk #phonkmusic #phonkdrift #phonkvibes #phonkedit #djdarkmark",
    "trap":       "#trap #trapmusic #808s #trapbeats #undergroundhiphop #trapvibes #djdarkmark",
    "rock":       "#rock #rockmusic #guitarmusic #hardrock #alternative #alternativerock #djdarkmark",
    "metal":      "#metal #heavymetal #metalhead #metalcore #extrememetal #heavymusic #djdarkmark",
    "lofi":       "#lofi #lofihiphop #studymusic #chillvibes #lofibeats #relaxingmusic #djdarkmark",
    "indie":      "#indie #indiemusic #alternativemusic #indiepop #indierock #emotionalmusic #djdarkmark",
    "electronic": "#electronic #edm #synthwave #electronicmusic #techno #dancemusic #djdarkmark",
    "cinematic":  "#cinematic #cinematicmusic #epicmusic #orchestral #filmmusic #epicorchestral #djdarkmark",
    "funk":       "#funk #funkmusic #groove #soulmusic #funkychill #groovemusic #djdarkmark",
    "dark":       "#dark #darkmusic #gothic #darkambient #darkwave #atmospheric #djdarkmark",
    "pop":        "#pop #popmusic #popvibes #newmusic #chart #hitmusic #djdarkmark",
    "default":    "#music #newmusic #viralmusic #underground #musiclover #musicdiscovery #djdarkmark",
}

UNIVERSAL = "#shorts #youtubeshorts #viral #fyp #trending #musicshorts #shortsvideo #djdarkmark"


def build_title(base: str, style: str, short_num: int) -> str:
    """
    Gera título em inglês com DJ darkMark sempre presente.
    Usa hash determinístico para variar sem repetir padrões.
    """
    import hashlib

    hooks = STYLE_HOOKS.get(style, STYLE_HOOKS["default"])
    emoji = GENRE_EMOJI.get(style, "🎵")

    # Seleciona hook e template via hash (determinístico por música + short)
    hook_seed = int(hashlib.md5(f"{base}|hook|{short_num}".encode()).hexdigest(), 16)
    tmpl_seed = int(hashlib.md5(f"{base}|tmpl|{short_num}".encode()).hexdigest(), 16)

    hook = hooks[hook_seed % len(hooks)]
    template = TITLE_TEMPLATES[tmpl_seed % len(TITLE_TEMPLATES)]

    title = template.format(hook=hook, title=base)

    # Garante que DJ darkMark está presente (segurança dupla)
    if "DJ darkMark" not in title and "dj darkmark" not in title.lower():
        title = f"DJ darkMark | {title}"

    # Adiciona emoji do gênero se não tiver emoji nenhum
    if not any(c for c in title if ord(c) > 127 and c not in "áéíóúàâêôãõüçÁÉÍÓÚÀÂÊÔÃÕÜÇ"):
        title = f"{title} {emoji}"

    return title[:100]


def build_description(base: str, style: str, short_num: int) -> str:
    tags = STYLE_HASHTAGS.get(style, STYLE_HASHTAGS["default"])
    emoji = GENRE_EMOJI.get(style, "🎵")

    ctas = [
        f"Subscribe to {CHANNEL_NAME} for daily underground music drops.",
        f"Follow {CHANNEL_NAME} — new music every day.",
        f"Like if this deserved more plays.",
        f"Save this — you'll want it back later.",
        f"Comment if this hit the way it was supposed to.",
    ]

    spotify_lines = [
        f"🎧 Full track on Spotify:\n{SPOTIFY_LINK}",
        f"🎵 Stream everywhere:\n{SPOTIFY_LINK}",
        f"🔊 Full version on Spotify:\n{SPOTIFY_LINK}",
        f"📻 Now on Spotify:\n{SPOTIFY_LINK}",
        f"🎧 Listen here:\n{SPOTIFY_LINK}",
    ]

    hooks = [
        f"Found this before it blows up. {CHANNEL_NAME} brings you the best underground {style} music daily.",
        f"Some tracks deserve more ears. {CHANNEL_NAME} is here to fix that.",
        f"Early on this one. {CHANNEL_NAME} drops daily music you won't find anywhere else.",
        f"The algorithm buried this. {CHANNEL_NAME} dug it up.",
        f"Not everything good goes viral. {CHANNEL_NAME} makes sure you find it anyway.",
    ]

    idx = (short_num - 1) % len(ctas)
    cta = ctas[idx]
    spotify_line = spotify_lines[idx]
    hook = hooks[idx]

    return (
        f"{emoji} {base} | {CHANNEL_NAME}\n\n"
        f"{hook}\n\n"
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
            log(f"New track: {f['name']}")
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
        log(f"Priority: new track — {chosen['name']}")
        chosen["is_new"] = False
        return chosen

    n = len(tracks)
    idx = state.get("alpha_index", 0) % n

    for i in range(n):
        t = tracks[(idx + i) % n]
        if t.get("done", 0) < SHORTS_PER_TRACK:
            state["alpha_index"] = (idx + i + 1) % n
            return t

    log("Full cycle complete — resetting all counters.")
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
            log(f"AI image generated: {img}")
            return img
    except Exception as e:
        log(f"AI image failed, trying local fallback: {e}")

    try:
        bg = get_random_background(style, filename)
        if bg and not str(bg).startswith("__AUTO"):
            log(f"Using local background: {bg}")
            return bg
    except Exception as e:
        log(f"Local background failed: {e}")

    fallback = "assets/backgrounds/default.jpg"
    if os.path.exists(fallback):
        log("Using default fallback background")
        return fallback

    raise FileNotFoundError("No background available (AI, local, and fallback all failed).")


# ══════════════════════════════════════════════════════════════════════
# PUBLICAÇÃO
# ══════════════════════════════════════════════════════════════════════

def publish(video_path: str, title: str, description: str) -> dict:
    results = {}

    if ENABLE_YOUTUBE:
        try:
            log("Uploading to YouTube...")
            res = upload_video(video_path, title, description, [], "public")
            yt_id = res.get("id", "?") if isinstance(res, dict) else "?"
            log(f"  YouTube OK -> https://youtu.be/{yt_id}")
            results["youtube"] = {"ok": True, "id": yt_id}
            human_delay()
        except Exception as e:
            log(f"  YouTube ERROR: {e}")
            results["youtube"] = {"ok": False, "error": str(e)}
    else:
        results["youtube"] = {"ok": False, "skipped": True}

    if ENABLE_FACEBOOK:
        try:
            log("Uploading to Facebook Reels...")
            res = upload_to_facebook(video_path, title, description)
            fb_id = res.get("id") or res.get("video_id", "?")
            log(f"  Facebook OK -> ID: {fb_id}")
            results["facebook"] = {"ok": True, "id": fb_id}
        except EnvironmentError as e:
            log(f"  Facebook not configured: {e}")
            results["facebook"] = {"ok": False, "skipped": True}
        except Exception as e:
            log(f"  Facebook ERROR: {e}")
            results["facebook"] = {"ok": False, "error": str(e)}
    else:
        results["facebook"] = {"ok": False, "skipped": True}

    return results


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════

def main():
    log("=" * 55)
    log(f"BOT STARTING — {CHANNEL_NAME} | YouTube Shorts + Facebook Reels")
    log(f"  YouTube  : {'ACTIVE' if ENABLE_YOUTUBE else 'DISABLED'}")
    log(f"  Facebook : {'ACTIVE' if ENABLE_FACEBOOK else 'DISABLED'}")
    log(f"  Backup   : {'ACTIVE' if DRIVE_BACKUP_FOLDER_ID else 'DISABLED'}")
    log(f"  Shorts/track: {SHORTS_PER_TRACK}")
    log("=" * 55)

    if not DRIVE_FOLDER_ID:
        raise ValueError("DRIVE_FOLDER_ID not configured in environment variables.")

    service = get_drive_service()
    inbox_id = find_folder_id(service, DRIVE_FOLDER_ID, "inbox")
    if not inbox_id:
        raise ValueError("'inbox' folder not found in Drive.")

    files = list_audio_files_in_folder(service, inbox_id)
    log(f"Audio files found in Drive: {len(files)}")

    state = load_state()
    sync_tracks(state, files)
    save_state(state)

    if not state["tracks"]:
        log("No tracks to process. Exiting.")
        return

    track = get_next_track(state)
    if not track:
        log("No track available to process.")
        return

    name = track["name"]
    short_num = track.get("done", 0) + 1
    title_base = clean_title(name)

    log(f"Track   : {name}")
    log(f"Short   : {short_num}/{SHORTS_PER_TRACK}")

    os.makedirs("temp", exist_ok=True)
    audio_path = f"temp/{name}"

    bg = None
    style = "default"
    styles = ["default"]
    thumbnail_path = None

    try:
        log("Downloading audio from Drive...")
        download_drive_file(service, track["id"], audio_path)
        log("Download complete.")

        cached_genre = track.get("genre")
        if cached_genre:
            style = cached_genre
            styles = detect_genre_multi(audio_path)
            log(f"Genre (cached): {style}")
        else:
            log("Detecting genre by acoustic analysis...")
            style = detect_genre(audio_path)
            styles = detect_genre_multi(audio_path)
            track["genre"] = style
            save_state(state)
            log(f"Genre detected: {style} | Secondary: {', '.join(styles[1:] or ['none'])}")

        date = datetime.utcnow().strftime("%Y-%m-%d")
        output_dir = Path("output") / date / style
        output_dir.mkdir(parents=True, exist_ok=True)
        planned_video_path = str(
            output_dir / f"{date}__{style}__{safe_filename(title_base)}__s{short_num}.mp4"
        )

        log(f"Generating background (short {short_num})...")
        bg = resolve_background(style, name, short_num, styles)

        log("Generating video...")
        render_result = create_short(
            audio_path,
            bg,
            planned_video_path,
            style,
            song_name=title_base,
        )

        if isinstance(render_result, dict):
            video_path = render_result["output_path"]
            thumbnail_path = render_result.get("thumbnail_path")
        else:
            video_path = render_result
            thumbnail_path = None

        log(f"Video ready: {video_path}")
        if thumbnail_path:
            log(f"Thumbnail ready: {thumbnail_path}")

        title = build_title(title_base, style, short_num)
        description = build_description(title_base, style, short_num)
        log(f"Title   : {title}")

        results = publish(video_path, title, description)

        if DRIVE_BACKUP_FOLDER_ID:
            try:
                log("Saving backup to Drive...")
                upload_file_to_drive(service, DRIVE_BACKUP_FOLDER_ID, video_path)
                log("  Backup saved successfully.")
            except Exception as e:
                log(f"  Backup failed (non-critical): {e}")
        else:
            log("  Backup disabled (DRIVE_BACKUP_FOLDER_ID not configured).")

        any_ok = any(r.get("ok") for r in results.values())
        all_skipped = all(r.get("skipped") for r in results.values())

        if not any_ok and not all_skipped:
            raise RuntimeError("No platform received the video successfully.")

        track["done"] = short_num
        save_state(state)

        log("=" * 55)
        log(f"DONE — {name} (short {short_num}/{SHORTS_PER_TRACK})")
        log("=" * 55)

    finally:
        for path in [audio_path, bg]:
            try:
                if path and isinstance(path, str) and os.path.exists(path):
                    if path.startswith("temp/"):
                        os.remove(path)
                        log(f"Temp file removed: {path}")
            except Exception:
                pass


if __name__ == "__main__":
    main()
