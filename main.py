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
from background_selector import detect_style, detect_styles, get_random_background
from video_generator import create_short
from youtube_service import upload_video
from facebook_service import upload_to_facebook
from ai_image_generator import generate_image, build_ai_prompt

# ══════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════

STATE_FILE = Path("state.json")
SHORTS_PER_TRACK = 5

DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")
DRIVE_BACKUP_FOLDER_ID = os.getenv("DRIVE_BACKUP_FOLDER_ID", "").strip()
ENABLE_DRIVE_BACKUP = os.getenv("ENABLE_DRIVE_BACKUP", "false").lower() == "true"

SPOTIFY_LINK = "https://open.spotify.com/intl-pt/artist/1zyM1Pyi4YLAQgrSVRAYEy"
TIKTOK_LINK = "https://www.tiktok.com/@darkmrkedit"

ENABLE_YOUTUBE = os.getenv("ENABLE_YOUTUBE", "true").lower() == "true"
ENABLE_FACEBOOK = os.getenv("ENABLE_FACEBOOK", "true").lower() == "true"


def log(msg: str):
    print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] {msg}")


# ══════════════════════════════════════════════════════════════════════
# UTILITÁRIOS
# ══════════════════════════════════════════════════════════════════════

def clean_title(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(r"\[[^\]]*\]|\{[^\}]*\}|\([^\)]*\)", "", name)
    name = re.sub(r"[_\-]+", " ", name)
    return re.sub(r"\s+", " ", name).strip().title()


def safe_filename(text: str) -> str:
    text = re.sub(r"[^\w\s\-]", "", text.lower())
    return re.sub(r"\s+", "_", text)[:60]


def human_delay():
    secs = random.randint(10, 40)
    log(f"Aguardando {secs}s...")
    time.sleep(secs)


# ══════════════════════════════════════════════════════════════════════
# METADATA
# ══════════════════════════════════════════════════════════════════════

STYLE_HOOKS = {
    "phonk": ["Night mode: activated 🖤", "Save this for the night drive 🌙", "Underground anthem 🔥", "This doesn't belong on a playlist 😳", "Your city needs this energy 😈"],
    "trap": ["This one built different 💎", "Luxury frequency unlocked 💎", "That baseline just walked in 🔥", "Certified banger 🏆", "Your headphones deserved this 👑"],
    "rock": ["Your speakers won't forgive you 🎸", "Can't skip, won't skip 🎸", "This guitar hit different tonight 🔥", "This one goes to 11 ⚡", "Your playlist needed this 🔥"],
    "metal": ["Warning: extremely heavy ⚠️", "Not for the faint-hearted 🔥", "Your ears aren't ready 🖤", "This drop is unreal 😈", "This hits like a freight train 😈"],
    "lofi": ["Sleep to this tonight 🌙", "3am and this is perfect ☁️", "Your study playlist found its anchor 📚", "This is what calm sounds like 🎧", "Quiet enough to think, beautiful enough to feel 🌙"],
    "indie": ["You'll replay this all week 🎧", "Your next favorite song 🎵", "Someone left this feeling in a song 🌙", "The feeling you couldn't name 🎧", "This one stays with you 🌅"],
    "electronic": ["That drop will break your brain 🤯", "The festival you never attended ⚡", "This frequency doesn't exist yet ⚡", "The drop you won't see coming 🤯", "Your ears are about to time travel 🚀"],
    "dark": ["This found you at the right moment 🌑", "Beautiful and haunting 🖤", "The darkness has a melody 🖤", "Your soul needed this 🌑", "Some songs carry entire nights 🌙"],
    "default": ["Your playlist needed this upgrade 🎵", "You won't regret pressing play 🎧", "Found: your new favorite 🎵", "Don't say we didn't warn you 🎧", "This is the one 🔥"],
}

STYLE_HASHTAGS = {
    "phonk": "#phonk #darkphonk #phonkmusic #drift #phonkvibes #phonkedit",
    "trap": "#trap #trapmusic #808 #trapbeats #hiphop #banger",
    "rock": "#rock #rockmusic #guitarmusic #hardrock #alternative",
    "metal": "#metal #heavymetal #metalhead #metalcore #deathmetal",
    "lofi": "#lofi #lofihiphop #studymusic #chillvibes #lofibeats",
    "indie": "#indie #indiemusic #alternativemusic #emotional #indievibes",
    "electronic": "#electronic #edm #synthwave #electronicmusic #rave",
    "dark": "#dark #darkmusic #gothic #darkambient #darkwave",
    "default": "#music #newmusic #viralmusic #underground #musiclover",
}
UNIVERSAL = "#shorts #youtubeshorts #reels #fbreels #viral #fyp #trending #musicshorts"


def build_title(base: str, style: str, short_num: int) -> str:
    hooks = STYLE_HOOKS.get(style, STYLE_HOOKS["default"])
    hook = hooks[(short_num - 1) % len(hooks)]
    formats = {
        1: f"{hook} | {base}",
        2: f"{base} | {hook}",
        3: f"You need to hear this 🎧 {base}",
        4: f"{hook} — {base}",
        5: f"{base} 🎵 {hook}",
    }
    return formats.get(short_num, f"{hook} | {base}")[:100]


def build_description(base: str, style: str) -> str:
    tags = STYLE_HASHTAGS.get(style, STYLE_HASHTAGS["default"])
    return (
        f"🎵 {base}\n\n"
        f"🎧 Spotify:\n{SPOTIFY_LINK}\n\n"
        f"📲 TikTok:\n{TIKTOK_LINK}\n\n"
        f"🔔 Inscreva-se para musica todo dia!\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{tags}\n{UNIVERSAL}"
    )


# ══════════════════════════════════════════════════════════════════════
# ESTADO — fila alfabética, 1 short por música por rodada
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

    return state


def save_state(state: dict):
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def sync_tracks(state: dict, files: list):
    existing = {t["name"]: t for t in state["tracks"]}

    for f in files:
        if f["name"] not in existing:
            log(f"🆕 Nova musica: {f['name']}")
            state["tracks"].append({
                "id": f["id"],
                "name": f["name"],
                "done": 0,
                "is_new": True,
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
        log(f"🆕 Prioridade para nova: {chosen['name']}")
        chosen["is_new"] = False
        return chosen

    n = len(tracks)
    idx = state.get("alpha_index", 0) % n

    for i in range(n):
        t = tracks[(idx + i) % n]
        if t.get("done", 0) < SHORTS_PER_TRACK:
            state["alpha_index"] = (idx + i + 1) % n
            return t

    log("🔄 Rodada completa — resetando todos os shorts.")
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
            log(f"Imagem IA gerada: {img}")
            return img
    except Exception as e:
        log(f"IA falhou, usando fallback: {e}")

    try:
        bg = get_random_background(style, filename)
        if bg and not str(bg).startswith("__AUTO"):
            return bg
    except Exception:
        pass

    fallback = "assets/backgrounds/default.jpg"
    if os.path.exists(fallback):
        return fallback

    raise FileNotFoundError("Nenhum background disponivel.")


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
    log("=" * 50)
    log("BOT INICIANDO - YouTube Shorts + Facebook Reels")
    log(f"  YouTube : {'ATIVO' if ENABLE_YOUTUBE else 'DESABILITADO'}")
    log(f"  Facebook: {'ATIVO' if ENABLE_FACEBOOK else 'DESABILITADO'}")
    log(f"  Backup   : {'ATIVO' if ENABLE_DRIVE_BACKUP else 'DESABILITADO'}")
    log("=" * 50)

    if not DRIVE_FOLDER_ID:
        raise ValueError("DRIVE_FOLDER_ID nao configurado.")

    service = get_drive_service()
    inbox_id = find_folder_id(service, DRIVE_FOLDER_ID, "inbox")
    if not inbox_id:
        raise ValueError("Pasta 'inbox' nao encontrada no Drive.")

    files = list_audio_files_in_folder(service, inbox_id)
    log(f"Audios no Drive: {len(files)}")

    state = load_state()
    sync_tracks(state, files)
    save_state(state)

    if not state["tracks"]:
        log("Sem musicas. Encerrando.")
        return

    track = get_next_track(state)
    if not track:
        log("Nenhuma faixa disponivel.")
        return

    name = track["name"]
    short_num = track.get("done", 0) + 1
    styles = detect_styles(name)
    style = detect_style(name)
    title_base = clean_title(name)

    log(f"Musica : {name}")
    log(f"Estilo : {style} | Short {short_num}/{SHORTS_PER_TRACK}")

    os.makedirs("temp", exist_ok=True)
    audio_path = f"temp/{name}"

    date = datetime.utcnow().strftime("%Y-%m-%d")
    output_dir = Path("output") / date / style
    output_dir.mkdir(parents=True, exist_ok=True)
    video_path = str(
        output_dir / f"{date}__{style}__{safe_filename(title_base)}__s{short_num}.mp4"
    )

    bg = None

    try:
        log("Baixando audio do Drive...")
        download_drive_file(service, track["id"], audio_path)
        log("Download concluido.")

        bg = resolve_background(style, name, short_num, styles)

        log("Gerando video...")
        video_path = create_short(audio_path, bg, video_path, style, song_name=title_base)
        log(f"Video pronto: {video_path}")

        title = build_title(title_base, style, short_num)
        description = build_description(title_base, style)
        log(f"Titulo: {title}")

        results = publish(video_path, title, description)

        if ENABLE_DRIVE_BACKUP:
            try:
                if DRIVE_BACKUP_FOLDER_ID:
                    log("Salvando backup no Drive...")
                    upload_file_to_drive(service, DRIVE_BACKUP_FOLDER_ID, video_path)
                    log("  Backup salvo!")
                else:
                    log("  Backup ignorado: DRIVE_BACKUP_FOLDER_ID nao configurado.")
            except Exception as e:
                log(f"  Backup falhou (nao critico): {e}")
        else:
            log("  Backup desabilitado.")

        any_ok = any(r.get("ok") for r in results.values())
        all_skipped = all(r.get("skipped") for r in results.values())

        if not any_ok and not all_skipped:
            raise RuntimeError("Nenhuma plataforma recebeu o video.")

        track["done"] = short_num
        save_state(state)

        log("=" * 50)
        log(f"CONCLUIDO — {name} (short {short_num}/{SHORTS_PER_TRACK})")
        log("=" * 50)

    finally:
        for path in [audio_path, video_path, bg]:
            try:
                if path and isinstance(path, str) and os.path.exists(path):
                    if path.startswith("temp/") or path.startswith("output/"):
                        os.remove(path)
                        log(f"Temporario removido: {path}")
            except Exception:
                pass


if __name__ == "__main__":
    main()
