"""
main.py — Bot de automação YouTube Shorts + Facebook Reels
Versão 3.0 — Sincronização YouTube ↔ Facebook na mesma execução.
"""

import os
import json
import re
import random
import time
import traceback
from pathlib import Path
from datetime import datetime

import anthropic

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

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO
# ══════════════════════════════════════════════════════════════════════════════

STATE_FILE = Path("state.json")
SHORTS_PER_TRACK = 5
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")
HUMAN_DELAY_MIN = 10
HUMAN_DELAY_MAX = 45
SPOTIFY_LINK = "https://open.spotify.com/intl-pt/artist/1zyM1Pyi4YLAQgrSVRAYEy?si=3fQcRGwSQ8O2vsqq6jOVow"
TIKTOK_LINK = "https://www.tiktok.com/@darkmrkedit?is_from_webapp=1&sender_device=pc"
AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".opus"}

# Controle de plataformas ativa/desativa sem mudar o código
ENABLE_YOUTUBE = os.getenv("ENABLE_YOUTUBE", "true").lower() == "true"
ENABLE_FACEBOOK = os.getenv("ENABLE_FACEBOOK", "true").lower() == "true"

# ══════════════════════════════════════════════════════════════════════════════
# SINGLETON ANTHROPIC
# ══════════════════════════════════════════════════════════════════════════════

_anthropic_client: anthropic.Anthropic | None = None

def get_anthropic_client() -> anthropic.Anthropic | None:
    global _anthropic_client
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    if _anthropic_client is None:
        _anthropic_client = anthropic.Anthropic(api_key=api_key)
    return _anthropic_client

def get_anthropic_model() -> str:
    return os.getenv("ANTHROPIC_MODEL", "claude-opus-4-5")

# ══════════════════════════════════════════════════════════════════════════════
# UTILITÁRIOS
# ══════════════════════════════════════════════════════════════════════════════

def log(msg: str):
    ts = datetime.utcnow().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

def clean_title(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(r"\[[^\]]*\]|\{[^\}]*\}|\([^\)]*\)", "", name)
    name = re.sub(r"[_\-]+", " ", name)
    return re.sub(r"\s+", " ", name).strip().title()

def clean_for_youtube(title: str) -> str:
    title = re.sub(r"\(\d+\)|\bshort\s*\d*\b|\bversion\s*\d*\b", "", title, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", title).strip(" -_|")

def safe_filename(text: str) -> str:
    text = re.sub(r"[^\w\s\-]", "", text.lower())
    return re.sub(r"\s+", "_", text)[:60]

def human_delay():
    secs = random.randint(HUMAN_DELAY_MIN, HUMAN_DELAY_MAX)
    log(f"Aguardando {secs}s (delay natural)…")
    time.sleep(secs)

# ══════════════════════════════════════════════════════════════════════════════
# TÍTULOS E METADATA
# ══════════════════════════════════════════════════════════════════════════════

STYLE_TIME_CONTEXT = {
    "lofi": "3am", "indie": "sunset", "rock": "full volume",
    "metal": "midnight", "phonk": "night drive", "trap": "the top",
    "electronic": "the drop", "dark": "2am", "pop": "max volume",
    "funk": "the party", "cinematic": "the moment", "default": "midnight",
}

STYLE_HOOKS = {
    "rock":       ["Your speakers won't forgive you 🎸", "This guitar hit different tonight 🔥", "Can't skip, won't skip 🎸", "This one goes to 11 ⚡", "Your playlist needed this 🔥"],
    "metal":      ["This drop is unreal 😈", "Not for the faint-hearted 🔥", "Your ears aren't ready 🖤", "Warning: extremely heavy ⚠️", "This hits like a freight train 😈"],
    "phonk":      ["Save this for the night drive 🌙", "Your city needs this energy 😈", "Underground anthem found 🔥", "This doesn't belong on a playlist 😳", "Night mode: activated 🖤"],
    "trap":       ["This one built different 💎", "Your headphones deserved this 👑", "That baseline just walked in 🔥", "Luxury frequency unlocked 💎", "Certified banger, no debate 🏆"],
    "indie":      ["You'll replay this all week 🎧", "Someone left this feeling in a song 🌙", "Your next favorite song 🎵", "This one stays with you 🌅", "The feeling you couldn't name 🎧"],
    "lofi":       ["Sleep to this tonight 🌙", "Your study playlist found its anchor 📚", "3am and this is perfect ☁️", "Quiet enough to think, beautiful enough to feel 🌙", "This is what calm sounds like 🎧"],
    "electronic": ["That drop will break your brain 🤯", "The festival you never attended ⚡", "Your ears are about to time travel 🚀", "This frequency doesn't exist yet ⚡", "The drop you won't see coming 🤯"],
    "cinematic":  ["This sounds like a movie scene 🎬", "Your moment has a soundtrack now 🎬", "The feeling before something changes 🌌", "This exists to give you chills 🎬", "Goosebumps loading… 🌌"],
    "funk":       ["Your body already knows this one 🕺", "Play this and watch the room change 🔥", "This groove is criminal 🎵", "You weren't ready for this 🕺", "Dance whether you want to or not 🔥"],
    "dark":       ["This found you at the right moment 🌑", "Beautiful and haunting 🖤", "Some songs carry entire nights 🌙", "Your soul needed this 🌑", "The darkness has a melody 🖤"],
    "pop":        ["This one's going on every playlist 🌟", "Warning: extremely catchy ✨", "You'll sing this all week 💫", "Certified earworm — you've been warned ✨", "The song you didn't know you needed 🌸"],
    "default":    ["Your playlist needed this upgrade 🎵", "You won't regret pressing play 🎧", "This is the one 🔥", "Found: your new favorite 🎵", "Don't say we didn't warn you 🎧"],
}

TITLE_FORMATS = {
    1: "{hook} | {title}",
    2: "{title} | {hook}",
    3: "You need to hear this 🎧 {title}",
    4: "{hook} — {title}",
    5: "Play this at {time} 🌙 {title}",
}

STYLE_HASHTAGS = {
    "phonk":      "#phonk #phonkmusic #darkphonk #phonkedit #drift #phonkvibes",
    "trap":       "#trap #trapmusic #trapbeats #hiphop #808 #banger",
    "rock":       "#rock #rockmusic #hardrock #guitarmusic #alternative",
    "metal":      "#metal #heavymetal #metalhead #deathmetal #metalcore",
    "indie":      "#indie #indiemusic #alternativemusic #indievibes #emotional",
    "lofi":       "#lofi #lofihiphop #studymusic #chillvibes #lofibeats",
    "electronic": "#electronic #edm #electronicmusic #synthwave #rave",
    "cinematic":  "#cinematic #cinematicmusic #epicmusic #filmmusic",
    "funk":       "#funk #groove #brazilianmusic #soulmusic",
    "dark":       "#dark #darkmusic #darkambient #gothic #darkwave",
    "pop":        "#pop #popmusic #hitmusic #chart #viral",
    "sertanejo":  "#sertanejo #musicabrasileira #sertanejouniversitario",
    "mpb":        "#mpb #bossanova #brasil #musicapopularbrasileira",
    "default":    "#music #newmusic #viralmusic #musiclover #underground",
}
UNIVERSAL_TAGS = "#shorts #youtubeshorts #viral #fyp #foryou #trending #musicshorts #reels #fbreels"


def generate_viral_title(base_title: str, style: str, styles: list[str], short_num: int = 1) -> str:
    client = get_anthropic_client()
    if client:
        try:
            return _claude_title(client, base_title, style, styles, short_num)
        except Exception as e:
            log(f"[Claude] Título fallback: {e}")
    return _static_title(base_title, style, short_num)


def _claude_title(client, base_title, style, styles, short_num):
    all_styles = ", ".join(styles) if styles else style
    position_hint = {
        1: "lead with an emotional hook, then the song name",
        2: "lead with the song name, end with a punchy hook",
        3: "use a curiosity question or statement",
        4: "use contrast or dramatic pause",
        5: "suggest when/where to listen to this song",
    }.get(short_num, "make it compelling and unique")

    resp = client.messages.create(
        model=get_anthropic_model(),
        max_tokens=120,
        system=(
            "You write viral YouTube Shorts and Facebook Reels titles for a music channel. "
            "Punchy, emotionally resonant, genre-specific. Max 80 chars. 1-2 emojis. "
            "Output ONLY the title — no quotes, no explanation."
        ),
        messages=[{"role": "user", "content": (
            f"Song: {base_title}\nGenre: {all_styles}\nStrategy: {position_hint}\n"
            f"Avoid: 'hits different', 'fire', 'banger', 'slaps'. Sound human."
        )}],
    )
    return resp.content[0].text.strip().strip('"').strip("'")[:100]


def _static_title(base_title: str, style: str, short_num: int) -> str:
    clean = clean_for_youtube(base_title)
    hooks = STYLE_HOOKS.get(style, STYLE_HOOKS["default"])
    hook = hooks[(short_num - 1) % len(hooks)]
    time_ctx = STYLE_TIME_CONTEXT.get(style, "midnight")
    fmt = TITLE_FORMATS.get(short_num, "{hook} | {title}")
    return fmt.format(hook=hook, title=clean, time=time_ctx)[:100]


def build_description(base_title: str, style: str, styles: list[str]) -> str:
    client = get_anthropic_client()
    if client:
        try:
            return _claude_description(client, base_title, style, styles)
        except Exception as e:
            log(f"[Claude] Descrição fallback: {e}")
    return _static_description(base_title, style, styles)


def _claude_description(client, base_title, style, styles):
    all_styles = ", ".join(styles) if styles else style
    resp = client.messages.create(
        model=get_anthropic_model(),
        max_tokens=400,
        system="YouTube/Facebook SEO expert for music channels. Keyword-rich, human, drives subs and streams.",
        messages=[{"role": "user", "content": (
            f"Description for: Song: {base_title} | Style: {all_styles}\n"
            f"Include: emotional hook, Spotify: [SPOTIFY], TikTok: [TIKTOK], subscribe CTA, hashtags for {style}."
        )}],
    )
    return (resp.content[0].text.strip()
            .replace("[SPOTIFY]", SPOTIFY_LINK)
            .replace("[TIKTOK]", TIKTOK_LINK))[:4500]


def _static_description(base_title: str, style: str, styles: list[str]) -> str:
    clean = clean_for_youtube(base_title)
    style_tags = STYLE_HASHTAGS.get(style, STYLE_HASHTAGS["default"])
    all_styles = " | ".join(s.title() for s in styles) if styles else style.title()
    return (
        f"🎵 {clean}\n\nStyle: {all_styles}\n\n"
        f"🎧 Spotify:\n{SPOTIFY_LINK}\n\n"
        f"📲 TikTok:\n{TIKTOK_LINK}\n\n"
        f"🔔 Subscribe for daily music drops\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{style_tags}\n{UNIVERSAL_TAGS}"
    )


def build_metadata(filename: str, short_num: int, style: str, styles: list[str]) -> tuple[str, str, list[str]]:
    base = clean_title(filename)
    clean = clean_for_youtube(base)
    title = generate_viral_title(clean, style, styles, short_num)
    desc = build_description(clean, style, styles)
    tags = list({
        "music", "shorts", "youtube shorts", "reels", "facebook reels",
        "viral music", "new music", style, f"{style} music",
        clean.lower(), *styles, *[f"{s} music" for s in styles],
        "anime aesthetic", "visual edit",
    })
    return title, desc, tags[:500]

# ══════════════════════════════════════════════════════════════════════════════
# ESTADO
# ══════════════════════════════════════════════════════════════════════════════

def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"tracks": [], "queue_index": 0, "last_posted_track": None}
    with STATE_FILE.open("r", encoding="utf-8") as f:
        state = json.load(f)
    state.setdefault("tracks", [])
    state.setdefault("queue_index", 0)
    state.setdefault("last_posted_track", None)
    for t in state["tracks"]:
        t.setdefault("shorts_done", 0)
        t.setdefault("done", False)
        t.setdefault("is_new", False)
    return state

def save_state(state: dict):
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def sync_tracks(state: dict, drive_files: list):
    existing = {t["name"]: t for t in state["tracks"]}
    for f in drive_files:
        if f["name"] not in existing:
            log(f"Nova música: {f['name']}")
            state["tracks"].append({"id": f["id"], "name": f["name"],
                                    "shorts_done": 0, "done": False, "is_new": True})
        else:
            existing[f["name"]]["id"] = f["id"]
    drive_names = {f["name"] for f in drive_files}
    state["tracks"] = [t for t in state["tracks"] if t["name"] in drive_names]
    n = len(state["tracks"])
    state["queue_index"] = state["queue_index"] % n if n else 0

def get_next_track(state: dict) -> dict | None:
    tracks = state["tracks"]
    if not tracks:
        return None
    last = state.get("last_posted_track")
    new = [t for t in tracks if t.get("is_new")]
    if new:
        chosen = next((t for t in new if t["name"] != last), new[0])
        chosen["is_new"] = False
        return chosen
    idx = state.get("queue_index", 0) % len(tracks)
    avail = []
    for i in range(len(tracks)):
        t = tracks[(idx + i) % len(tracks)]
        if t.get("shorts_done", 0) < SHORTS_PER_TRACK:
            avail.append(((idx + i) % len(tracks), t))
    if not avail:
        log("Todas as músicas completadas — resetando fila.")
        for t in tracks:
            t["shorts_done"] = 0
            t["done"] = False
        avail = list(enumerate(tracks))
    for i, t in avail:
        if t["name"] != last:
            state["queue_index"] = (i + 1) % len(tracks)
            return t
    i, t = avail[0]
    state["queue_index"] = (i + 1) % len(tracks)
    return t

# ══════════════════════════════════════════════════════════════════════════════
# BACKGROUND
# ══════════════════════════════════════════════════════════════════════════════

def resolve_background(style: str, filename: str, short_num: int, styles: list[str]) -> str:
    os.makedirs("temp", exist_ok=True)
    prompt = build_ai_prompt(style, filename, styles, short_num=short_num)
    log(f"Gerando imagem IA — gênero: {style}, variação {short_num}")
    dest = f"temp/{Path(filename).stem}_{short_num}.png"
    img = generate_image(prompt, output_path=dest)
    if img and os.path.exists(img):
        return img
    try:
        bg = get_random_background(style, filename)
        if bg and not str(bg).startswith("__AUTO"):
            return bg
    except Exception as e:
        log(f"Fallback local falhou: {e}")
    fallback = "assets/backgrounds/default.jpg"
    if os.path.exists(fallback):
        return fallback
    raise FileNotFoundError("Nenhum background disponível.")

def build_output_path(base_title: str, style: str, short_num: int) -> str:
    date = datetime.utcnow().strftime("%Y-%m-%d")
    folder = Path("output") / date / style
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{date}__{style}__{safe_filename(base_title)}__s{short_num}.mp4"
    return str(folder / name)

# ══════════════════════════════════════════════════════════════════════════════
# PUBLICAÇÃO — YOUTUBE + FACEBOOK EM SINCRONISMO
# ══════════════════════════════════════════════════════════════════════════════

def publish_to_all_platforms(
    video_path: str,
    title: str,
    description: str,
    tags: list[str],
) -> dict:
    """
    Posta o vídeo em todas as plataformas ativas.
    Retorna dict com resultados de cada plataforma.
    Falha em uma plataforma NÃO cancela as demais.
    """
    results = {}

    # ── YouTube ──────────────────────────────────────────────────────────────
    if ENABLE_YOUTUBE:
        try:
            log("📺 Publicando no YouTube…")
            yt_resp = upload_video(video_path, title, description, tags, "public")
            yt_id = yt_resp.get("id", "?") if isinstance(yt_resp, dict) else "?"
            results["youtube"] = {"success": True, "id": yt_id,
                                  "url": f"https://youtu.be/{yt_id}"}
            log(f"  ✅ YouTube: https://youtu.be/{yt_id}")

            # Delay entre plataformas para parecer comportamento humano
            human_delay()

        except Exception as e:
            log(f"  ❌ YouTube falhou: {e}")
            results["youtube"] = {"success": False, "error": str(e)}
    else:
        log("  ⏭  YouTube desabilitado (ENABLE_YOUTUBE=false)")

    # ── Facebook Reels ────────────────────────────────────────────────────────
    if ENABLE_FACEBOOK:
        try:
            log("📘 Publicando no Facebook Reels…")
            fb_resp = upload_to_facebook(video_path, title, description)
            fb_id = fb_resp.get("id") or fb_resp.get("video_id", "?")
            results["facebook"] = {"success": True, "id": fb_id}
            log(f"  ✅ Facebook Reel publicado! ID: {fb_id}")

        except EnvironmentError as e:
            log(f"  ⚠️  Facebook não configurado: {e}")
            results["facebook"] = {"success": False, "error": str(e), "skipped": True}
        except Exception as e:
            log(f"  ❌ Facebook falhou: {e}")
            results["facebook"] = {"success": False, "error": str(e)}
    else:
        log("  ⏭  Facebook desabilitado (ENABLE_FACEBOOK=false)")

    return results

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    log("═" * 55)
    log("BOT INICIADO — YouTube Shorts + Facebook Reels v3.0")
    log(f"  YouTube: {'✅ ativo' if ENABLE_YOUTUBE else '⏭  desabilitado'}")
    log(f"  Facebook: {'✅ ativo' if ENABLE_FACEBOOK else '⏭  desabilitado'}")
    log("═" * 55)

    if not DRIVE_FOLDER_ID:
        raise ValueError("DRIVE_FOLDER_ID não configurado.")

    state = load_state()
    service = get_drive_service()

    inbox_id = find_folder_id(service, DRIVE_FOLDER_ID, "inbox")
    if not inbox_id:
        raise ValueError("Pasta 'inbox' não encontrada no Drive.")

    files = list_audio_files_in_folder(service, inbox_id)
    log(f"Áudios no Drive: {len(files)}")

    sync_tracks(state, files)
    save_state(state)

    track = get_next_track(state)
    if not track:
        log("Nenhuma faixa disponível. Encerrando.")
        return

    name = track["name"]
    short_num = track.get("shorts_done", 0) + 1
    styles = detect_styles(name)
    style = detect_style(name)
    base_title = clean_title(name)

    log(f"Processando: {name}")
    log(f"Estilo: {style} | Detectados: {styles} | Short {short_num}/{SHORTS_PER_TRACK}")

    os.makedirs("temp", exist_ok=True)
    audio_path = f"temp/{name}"

    log("Baixando áudio do Drive…")
    download_drive_file(service, track["id"], audio_path)

    try:
        bg = resolve_background(style, name, short_num, styles)
        output_path = build_output_path(base_title, style, short_num)

        log("Gerando vídeo…")
        video_path = create_short(audio_path, bg, output_path, style,
                                  song_name=clean_for_youtube(base_title))
        log(f"Vídeo pronto: {video_path}")

        log("Gerando metadata…")
        title, desc, tags = build_metadata(name, short_num, style, styles)
        log(f"Título: {title}")

        # ── PUBLICAÇÃO SINCRONIZADA ──────────────────────────────────────────
        results = publish_to_all_platforms(video_path, title, desc, tags)

        # ── RESUMO ───────────────────────────────────────────────────────────
        log("─" * 40)
        log("RESULTADO DA PUBLICAÇÃO:")
        any_success = False
        for platform, r in results.items():
            if r.get("skipped"):
                log(f"  {platform}: ⏭  não configurado")
            elif r["success"]:
                url = r.get("url", f"ID: {r.get('id', '?')}")
                log(f"  {platform}: ✅ {url}")
                any_success = True
            else:
                log(f"  {platform}: ❌ {r.get('error', 'erro desconhecido')}")

        if not any_success and not all(r.get("skipped") for r in results.values()):
            raise RuntimeError("Nenhuma plataforma recebeu o vídeo com sucesso.")

        # ── BACKUP ───────────────────────────────────────────────────────────
        try:
            backup_id = find_folder_id(service, DRIVE_FOLDER_ID, "backups")
            if backup_id:
                upload_file_to_drive(service, backup_id, video_path)
                log("Backup salvo no Drive.")
        except Exception as e:
            log(f"Backup falhou (não crítico): {e}")

        # ── ATUALIZA ESTADO ──────────────────────────────────────────────────
        track["shorts_done"] = short_num
        track["done"] = short_num >= SHORTS_PER_TRACK
        state["last_posted_track"] = name
        save_state(state)

        log(f"✅ Short {short_num}/{SHORTS_PER_TRACK} de '{name}' publicado!")
        log("═" * 55)

    finally:
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
        except Exception:
            pass


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"❌ ERRO FATAL: {e}")
        traceback.print_exc()
        raise
