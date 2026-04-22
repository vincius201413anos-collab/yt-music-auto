"""
main.py — Bot de automação YouTube Shorts v3.0
===============================================
- Títulos únicos por música via hash determinístico (sem repetição jamais)
- Descrições variadas com rotação inteligente
- DJ darkMark branding consistente
- Suporte a YouTube + Facebook Reels
- Genre cache para evitar re-análise
- Upload timing com delay humano realista
"""

import os
import json
import re
import random
import time
import hashlib
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

DRIVE_FOLDER_ID        = os.getenv("DRIVE_FOLDER_ID")
DRIVE_BACKUP_FOLDER_ID = os.getenv("DRIVE_BACKUP_FOLDER_ID", "").strip()

SPOTIFY_LINK  = "https://open.spotify.com/intl-pt/artist/1zyM1Pyi4YLAQgrSVRAYEy"
TIKTOK_LINK   = "https://www.tiktok.com/@darkmrkedit"
CHANNEL_NAME  = "DJ darkMark"

ENABLE_YOUTUBE  = os.getenv("ENABLE_YOUTUBE",  "true").lower()  == "true"
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
    log(f"Waiting {secs}s before upload...")
    time.sleep(secs)


# ══════════════════════════════════════════════════════════════════════
# SISTEMA DE TÍTULOS v3 — Únicos, determinísticos, sem repetição
# Cada combinação música+short_num gera sempre o mesmo título
# (idempotente), mas diferentes entre si.
# ══════════════════════════════════════════════════════════════════════

# Hooks divididos por camadas de intenção — cada camada cria
# reação psicológica diferente no viewer antes de clicar

HOOKS_CURIOSITY = {
    "phonk":      ["you weren't ready for this", "they buried this on purpose", "algorithm finally did something right", "can't explain what this does to me", "this one doesn't exist on the radio"],
    "trap":       ["nobody's talking about this yet", "streets already know", "too clean to be this underground", "before it reaches everyone else", "this producer is about to be everywhere"],
    "rock":       ["this riff doesn't ask permission", "first 3 seconds and I was done", "guitar is back and it came angry", "shouldn't be this good in 2024", "this band deserves 10x the rooms they play"],
    "metal":      ["too heavy for most. you're not most.", "the underground doesn't want you finding this", "survive the breakdown", "this transcends genre at this point", "ancient and brutal and I can't stop"],
    "lofi":       ["noise in my head stopped for this", "forgot I had a to-do list", "this one holds your hand without asking", "focus unlocked. don't ask how.", "3am and finally quiet"],
    "indie":      ["said what I couldn't find words for", "sounds like nostalgia that doesn't hurt yet", "found this before everyone else and I'm protective", "can't explain why this hits. just does.", "one listen and I knew I'd be back"],
    "electronic": ["drop hit before my brain caught up", "built for stages that don't exist yet", "producer is taking notes somewhere right now", "this frequency belongs in stadiums", "found the ID I was chasing"],
    "dark":       ["makes sense after midnight only", "beautiful in a way that has no name", "this melody wasn't made for daylight", "can't explain what this does", "try to skip before the end. you won't."],
    "cinematic":  ["paused everything. just listened.", "the build is almost unfair", "makes you feel like the protagonist", "harder than any film score this year", "needs a film worthy of it"],
    "funk":       ["couldn't stay in my chair", "the groove took over before I agreed to it", "cleanest thing I found this week", "try not to move. you physically can't.", "pure groove no explanation needed"],
    "pop":        ["in your head before the chorus finishes", "hook ruins every song after it", "try to get it out. impossible.", "skipped it once. came back immediately.", "genuinely good pop. rare."],
    "default":    ["algorithm finally got it right", "found before it blows up", "can't skip this one", "too good to be this hidden", "one listen changes everything"],
}

HOOKS_EMOTIONAL = {
    "phonk":      ["3am and can't stop replaying this", "dark side of the underground found", "midnight energy arrived uninvited", "obsessed after 10 seconds", "this one got into me"],
    "trap":       ["early on this and can't stop", "luxury feels like this sounds", "this is what the playlist was missing", "the 808 I needed without knowing it", "elevated immediately"],
    "rock":       ["turn it up immediately", "volume up or don't bother", "found this at 1am and I'm still here", "every listen harder than the last", "no skip possible even if I tried"],
    "metal":      ["full volume or don't bother", "not for quiet rooms", "the heads already know", "pure sonic weight that you feel", "breakdown hits you physically"],
    "lofi":       ["perfect 3am company arrived", "slow everything down this way", "peace I didn't know I needed", "best study session just happened", "loop this all night"],
    "indie":      ["deserves bigger rooms and more time", "honest in a way music rarely is", "added before it finished playing", "the bridge. that's the whole review.", "early on this artist and staying"],
    "electronic": ["max volume dark room and just this", "can't stand still during the drop", "my body moved before I decided", "the future already sounds like this", "early on this producer"],
    "dark":       ["3 days in my head now", "not for everyone and that's the point", "darkness with a pulse is rare", "some frequencies were buried for a reason", "found hiding in the margins"],
    "cinematic":  ["eyes closed. instantly.", "epic from the first second", "the scene they cut for being too good", "one listen. seriously.", "composer nobody talks about yet"],
    "funk":       ["weekend energy any day of the week", "replayed twice before believing it", "your body already knows what to do", "this feels genuinely alive", "bass hit before I was ready"],
    "pop":        ["this is why pop still matters", "cleanest hook this year", "added before it finished", "can't unhear this now", "one listen and it's permanent"],
    "default":    ["early on this one", "your playlist needed this", "found this at midnight", "obsessed after 10 seconds", "just trust me on this one"],
}

HOOKS_IDENTITY = {
    "phonk":      ["not for everyone • found it anyway", "underground certified", "dark side music", "the ones who know • know", "phonk for the ones who listen in the dark"],
    "trap":       ["underground certified", "straight from the underground", "for the ones who recognize quality", "certified", "the ones paying attention already know"],
    "rock":       ["no mainstream necessary", "for the ones who still turn it up", "real guitar still exists and here it is", "the rock that didn't die", "certified loud"],
    "metal":      ["for the ones who can handle it", "underground approved", "heavy certified", "the ones who need the weight", "certified brutal"],
    "lofi":       ["for the ones who study in silence", "certified chill", "lofi for people who actually feel things", "the ones who listen at 3am", "quiet hours certified"],
    "indie":      ["for the ones paying attention", "early listeners know", "certified hidden gem", "underground before underground was cool", "the ones who find them first"],
    "electronic": ["early listener certified", "for the ones on the dancefloor before the song", "certified electronic", "rave certified", "for the ones who feel frequencies"],
    "dark":       ["not for daylight", "certified dark", "the ones who listen alone at night", "underground and staying there", "for the ones who understand"],
    "cinematic":  ["for the ones who listen with eyes closed", "certified epic", "film-score energy", "for the ones who feel music as stories", "cinematic certified"],
    "funk":       ["groove certified", "for the ones who can't sit still", "the people who know how to dance", "certified groove", "for the ones who feel it before they hear it"],
    "pop":        ["the pop that actually holds up", "certified earworm", "for the ones who like good songs", "hook certified", "genuinely good pop"],
    "default":    ["certified underground", "early listener", "for the ones paying attention", "found before it blows up", "the good ones always hide first"],
}

# Templates de título — variados, todos com DJ darkMark
TITLE_TEMPLATES = [
    "DJ darkMark — {title} | {hook}",
    "DJ darkMark | {hook} — {title}",
    "{hook} | {title} · DJ darkMark",
    "DJ darkMark 🎧 {title} | {hook}",
    "{title} — DJ darkMark | {hook}",
    "DJ darkMark: {title} {emoji} {hook}",
    "{title} {emoji} {hook} — DJ darkMark",
    "DJ darkMark drops: {title} | {hook}",
]

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


def _dhash(text: str) -> int:
    """Hash determinístico rápido para int."""
    return int(hashlib.md5(text.encode()).hexdigest(), 16)


def build_title(base: str, style: str, short_num: int) -> str:
    """
    Título 100% determinístico por música + short_num.
    Mesmo input → mesmo output sempre (idempotente).
    Inputs diferentes → outputs diferentes (anti-repetição).

    Usa 3 camadas de hooks (curiosidade, emocional, identidade)
    rotacionando por short_num para que 3 shorts da mesma música
    tenham abordagens psicológicas diferentes.
    """
    emoji = GENRE_EMOJI.get(style, "🎵")

    hook_layers = [
        HOOKS_CURIOSITY.get(style, HOOKS_CURIOSITY["default"]),
        HOOKS_EMOTIONAL.get(style, HOOKS_EMOTIONAL["default"]),
        HOOKS_IDENTITY.get(style, HOOKS_IDENTITY["default"]),
    ]

    # Cada short usa uma camada diferente de hook
    layer = hook_layers[(short_num - 1) % len(hook_layers)]

    hook_seed = _dhash(f"{base}|hook|{short_num}")
    tmpl_seed = _dhash(f"{base}|tmpl|{short_num}")

    hook     = layer[hook_seed % len(layer)]
    template = TITLE_TEMPLATES[tmpl_seed % len(TITLE_TEMPLATES)]

    title = template.format(hook=hook, title=base, emoji=emoji)

    # Garante DJ darkMark (dupla segurança)
    if "DJ darkMark" not in title and "dj darkmark" not in title.lower():
        title = f"DJ darkMark | {title}"

    return title[:100]


def build_description(base: str, style: str, short_num: int) -> str:
    """
    Descrição rotativa — 5 variantes diferentes por short_num.
    Cada uma com tom diferente para manter autenticidade.
    """
    tags  = STYLE_HASHTAGS.get(style, STYLE_HASHTAGS["default"])
    emoji = GENRE_EMOJI.get(style, "🎵")

    idx = (short_num - 1) % 5

    # Linha de abertura — 5 tons diferentes
    openers = [
        f"{emoji} {base}\n\n{CHANNEL_NAME} found this before it blows up.\n{CHANNEL_NAME} brings you the best underground {style} music daily.",
        f"{emoji} {base} — {CHANNEL_NAME}\n\nSome tracks deserve more ears. Found this so you didn't have to.",
        f"{emoji} {base}\n\nThe algorithm buried this. {CHANNEL_NAME} dug it up. Daily underground drops.",
        f"{emoji} {base} — {CHANNEL_NAME}\n\nNot everything good goes viral. {CHANNEL_NAME} makes sure you find it anyway.",
        f"{emoji} {base}\n\nEarly on this one. {CHANNEL_NAME} — daily music you won't find on the radio.",
    ]

    # CTA — 5 variantes
    ctas = [
        f"Subscribe to {CHANNEL_NAME} for daily underground music drops.",
        f"Follow {CHANNEL_NAME} — new music every single day.",
        f"Like if this deserved more plays.",
        f"Save this. You'll want it back.",
        f"Comment if this hit the way it was supposed to.",
    ]

    # Spotify — 5 variantes
    spotify_lines = [
        f"🎧 Full track:\n{SPOTIFY_LINK}",
        f"🎵 Stream it:\n{SPOTIFY_LINK}",
        f"🔊 Full version:\n{SPOTIFY_LINK}",
        f"📻 On Spotify:\n{SPOTIFY_LINK}",
        f"🎧 Listen here:\n{SPOTIFY_LINK}",
    ]

    return (
        f"{openers[idx]}\n\n"
        f"{ctas[idx]}\n\n"
        f"{spotify_lines[idx]}\n\n"
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
                "id":     f["id"],
                "name":   f["name"],
                "done":   0,
                "is_new": True,
                "genre":  None,
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

    n   = len(tracks)
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
        dest   = f"temp/{Path(filename).stem}_{short_num}.png"
        img    = generate_image(prompt, output_path=dest)
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

    raise FileNotFoundError("No background available.")


# ══════════════════════════════════════════════════════════════════════
# PUBLICAÇÃO
# ══════════════════════════════════════════════════════════════════════

def publish(video_path: str, title: str, description: str) -> dict:
    results = {}

    if ENABLE_YOUTUBE:
        try:
            log("Uploading to YouTube...")
            res   = upload_video(video_path, title, description, [], "public")
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
            res   = upload_to_facebook(video_path, title, description)
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
    log(f"  YouTube  : {'ACTIVE' if ENABLE_YOUTUBE  else 'DISABLED'}")
    log(f"  Facebook : {'ACTIVE' if ENABLE_FACEBOOK else 'DISABLED'}")
    log(f"  Backup   : {'ACTIVE' if DRIVE_BACKUP_FOLDER_ID else 'DISABLED'}")
    log(f"  Shorts/track: {SHORTS_PER_TRACK}")
    log("=" * 55)

    if not DRIVE_FOLDER_ID:
        raise ValueError("DRIVE_FOLDER_ID not configured.")

    service  = get_drive_service()
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
        log("No track available.")
        return

    name        = track["name"]
    short_num   = track.get("done", 0) + 1
    title_base  = clean_title(name)

    log(f"Track   : {name}")
    log(f"Short   : {short_num}/{SHORTS_PER_TRACK}")

    os.makedirs("temp", exist_ok=True)
    audio_path = f"temp/{name}"

    bg             = None
    style          = "default"
    styles         = ["default"]
    thumbnail_path = None

    try:
        log("Downloading audio from Drive...")
        download_drive_file(service, track["id"], audio_path)
        log("Download complete.")

        cached_genre = track.get("genre")
        if cached_genre:
            style  = cached_genre
            styles = detect_genre_multi(audio_path)
            log(f"Genre (cached): {style}")
        else:
            log("Detecting genre...")
            style  = detect_genre(audio_path)
            styles = detect_genre_multi(audio_path)
            track["genre"] = style
            save_state(state)
            log(f"Genre: {style} | Secondary: {', '.join(styles[1:] or ['none'])}")

        date       = datetime.utcnow().strftime("%Y-%m-%d")
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
            video_path     = render_result["output_path"]
            thumbnail_path = render_result.get("thumbnail_path")
        else:
            video_path     = render_result
            thumbnail_path = None

        log(f"Video ready: {video_path}")

        title       = build_title(title_base, style, short_num)
        description = build_description(title_base, style, short_num)
        log(f"Title   : {title}")

        results = publish(video_path, title, description)

        if DRIVE_BACKUP_FOLDER_ID:
            try:
                log("Saving backup to Drive...")
                upload_file_to_drive(service, DRIVE_BACKUP_FOLDER_ID, video_path)
                log("  Backup saved.")
            except Exception as e:
                log(f"  Backup failed (non-critical): {e}")

        any_ok      = any(r.get("ok") for r in results.values())
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
                        log(f"Temp removed: {path}")
            except Exception:
                pass


if __name__ == "__main__":
    main()
