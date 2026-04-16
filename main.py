"""
main.py — Bot de automação YouTube Shorts
Versão melhorada com:
- lock de state.json
- limpeza segura de temporários
- singleton do cliente Anthropic
- títulos mais específicos
- imagem IA priorizada em todos os vídeos
"""

from __future__ import annotations

import json
import os
import random
import re
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

import anthropic

from drive_service import (
    download_drive_file,
    find_folder_id,
    get_drive_service,
    list_audio_files_in_folder,
    upload_file_to_drive,
)
from background_selector import detect_style, detect_styles, get_random_background
from video_generator import create_short
from youtube_service import upload_video
from ai_image_generator import build_ai_prompt, generate_image

try:
    import fcntl
except ImportError:  # Windows fallback
    fcntl = None


# ══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════════════

STATE_FILE = Path("state.json")
SHORTS_PER_TRACK = 5
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")

HUMAN_DELAY_MIN = 10
HUMAN_DELAY_MAX = 60

SPOTIFY_LINK = "https://open.spotify.com/intl-pt/artist/1zyM1Pyi4YLAQgrSVRAYEy?si=3fQcRGwSQ8O2vsqq6jOVow"
TIKTOK_LINK = "https://www.tiktok.com/@darkmrkedit?is_from_webapp=1&sender_device=pc"

AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".opus"}

_ANTHROPIC_CLIENT: anthropic.Anthropic | None = None


# ══════════════════════════════════════════════════════════════════════════════
# UTILS
# ══════════════════════════════════════════════════════════════════════════════

def get_anthropic_model() -> str:
    return os.getenv("ANTHROPIC_MODEL", "claude-opus-4-7")


def get_anthropic_client() -> anthropic.Anthropic | None:
    global _ANTHROPIC_CLIENT
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    if _ANTHROPIC_CLIENT is None:
        _ANTHROPIC_CLIENT = anthropic.Anthropic(api_key=api_key)
    return _ANTHROPIC_CLIENT


def log(msg: str) -> None:
    ts = datetime.utcnow().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def clean_title(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(r"\[[^\]]*\]", "", name)
    name = re.sub(r"\{[^\}]*\}", "", name)
    name = re.sub(r"\([^\)]*\)", "", name)
    name = re.sub(r"[_\-]+", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name.title()


def clean_for_youtube(title: str) -> str:
    title = re.sub(r"\(\d+\)", "", title)
    title = re.sub(r"\bshort\s*\d*\b", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\bversion\s*\d*\b", "", title, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", title).strip(" -_|")


def safe_filename(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s\-]", "", text)
    text = re.sub(r"\s+", "_", text)
    return text[:60]


def human_delay() -> None:
    secs = random.randint(HUMAN_DELAY_MIN, HUMAN_DELAY_MAX)
    log(f"Aguardando {secs}s (comportamento humano)…")
    time.sleep(secs)


# ══════════════════════════════════════════════════════════════════════════════
# TÍTULOS / DESCRIÇÕES
# ══════════════════════════════════════════════════════════════════════════════

STYLE_HOOKS: dict[str, list[str]] = {
    "rock": [
        "You won't skip this 🎸",
        "This guitar lead is wild ⚡",
        "That riff carries the whole short 🔥",
        "Rock fans will replay this 🎧",
    ],
    "metal": [
        "This drop turns brutal fast 😈",
        "Metal fans, stay for the hit ⚠️",
        "That breakdown came out of nowhere 🤯",
        "Pure heavy energy from start 🔥",
    ],
    "phonk": [
        "Night drive energy unlocked 🌙",
        "This one feels illegal 😈",
        "That drift vibe is too clean 🚗",
        "Play this after midnight 🖤",
    ],
    "trap": [
        "This beat enters different 💎",
        "That switch-up is too clean ✨",
        "Trap fans will replay this 🔁",
        "Luxury vibe with a hard drop 😮",
    ],
    "indie": [
        "Late-night mood in one short 🌌",
        "This melody lingers after the end ✨",
        "Indie fans, wait for the feeling 🎧",
        "Soft vibe, strong replay value 🌙",
    ],
    "lofi": [
        "Perfect for tonight’s mood 🌙",
        "Study with this one 📚",
        "This loop feels too peaceful ☁️",
        "That cozy vibe hits instantly 🎧",
    ],
    "electronic": [
        "Wait for the synth drop ⚡",
        "Electronic fans, don’t skip this 🔥",
        "That build-up pays off hard 🎛️",
        "This one was made for replay 🔁",
    ],
    "cinematic": [
        "This feels bigger than a short 🎬",
        "That atmosphere is unreal 🌌",
        "Wait for the emotional lift ✨",
        "This one sounds like a trailer 🔥",
    ],
    "funk": [
        "This groove catches fast 🎵",
        "Party energy in one short ⚡",
        "That bounce is too addictive 🔥",
        "Brazilian vibe done right 🇧🇷",
    ],
    "dark": [
        "This mood gets under your skin 🌑",
        "Dark vibe done right 🖤",
        "Play this when the lights are low 🌙",
        "That atmosphere pulls you in 😈",
    ],
    "pop": [
        "This chorus sticks instantly 💫",
        "Too catchy to skip ✨",
        "That pop glow is addictive 🔁",
        "This one lands fast 🎵",
    ],
    "default": [
        "You’ll want another replay 🔁",
        "This one catches fast 🎧",
        "Don’t skip the payoff ✨",
        "Short, but hard to forget 🔥",
    ],
}

TITLE_PATTERNS = {
    1: [
        "{hook} | {title}",
        "{title} | {hook}",
    ],
    2: [
        "Would you replay this? 🎧 | {title}",
        "{title} | Hear the switch-up 😮",
    ],
    3: [
        "Wait for the drop ⚡ | {title}",
        "{title} | This part hits hardest 🔥",
    ],
    4: [
        "This mood stays with you 🌙 | {title}",
        "{title} | Not your average short ✨",
    ],
    5: [
        "One more replay won’t hurt 🔁 | {title}",
        "{title} | This deserves headphones 🎧",
    ],
}


def _fallback_title(base_title: str, style: str, short_num: int) -> str:
    clean = clean_for_youtube(base_title)
    hooks = STYLE_HOOKS.get(style, STYLE_HOOKS["default"])
    hook = random.choice(hooks)
    formats = TITLE_PATTERNS.get(short_num, TITLE_PATTERNS[1])
    fmt = random.choice(formats)
    return fmt.format(hook=hook, title=clean)[:100]


def generate_viral_title(
    base_title: str,
    style: str,
    styles: list[str],
    short_num: int,
) -> str:
    client = get_anthropic_client()
    if client is None:
        return _fallback_title(base_title, style, short_num)

    all_styles = ", ".join(styles) if styles else style
    try:
        resp = client.messages.create(
            model=get_anthropic_model(),
            max_tokens=120,
            system=(
                "You are a viral YouTube Shorts title expert. "
                "Write short, punchy, specific music titles that maximize CTR. "
                "Avoid stale phrases like 'hits different', 'goes hard', or generic clickbait. "
                "Output only the title."
            ),
            messages=[{
                "role": "user",
                "content": (
                    f"Create a YouTube Shorts title for:\n"
                    f"Song: {base_title}\n"
                    f"Style: {all_styles}\n"
                    f"Variation number: {short_num} of 5\n\n"
                    f"Rules:\n"
                    f"- Max 80 characters\n"
                    f"- Use 1-2 emojis max\n"
                    f"- Be specific to the mood/genre\n"
                    f"- Make it feel fresh and replayable\n"
                    f"- Do not use overused phrases\n"
                    f"- Variation intent:\n"
                    f"  1 = direct hook\n"
                    f"  2 = curiosity/question\n"
                    f"  3 = drop/payoff\n"
                    f"  4 = emotional/mood\n"
                    f"  5 = replay/headphones CTA"
                ),
            }],
        )
        title = resp.content[0].text.strip().strip('"').strip("'")
        title = title[:100]
        log(f"[Claude] Título gerado: {title}")
        return title
    except Exception as e:
        log(f"[Claude] Falha no título: {e} — usando fallback")
        return _fallback_title(base_title, style, short_num)


STYLE_HASHTAGS: dict[str, str] = {
    "electronic": "#electronic #edm #electronicmusic #synthwave #clubmusic #rave #dancemusic #techno #trance #futuremusic",
    "phonk": "#phonk #phonkmusic #darkphonk #phonkedit #drift #phonkvibes #phonkrap #aggressive #nightdrive",
    "trap": "#trap #trapmusic #trapbeats #hiphop #traprap #hardtrap #banger #drip #trapvibes",
    "rock": "#rock #rockmusic #hardrock #guitarmusic #rockband #alternative #grunge #rockguitar",
    "metal": "#metal #metalmusic #heavymetal #metalhead #metalcore #djent #breakdown",
    "indie": "#indie #indiemusic #indierock #alternativemusic #indievibes #bedroompop #emotionalmusic",
    "lofi": "#lofi #lofihiphop #lofichill #studymusic #relaxingmusic #chillvibes #lofibeats",
    "cinematic": "#cinematic #cinematicmusic #epicmusic #orchestral #filmmusic #dramaticmusic",
    "funk": "#funk #funkmusic #groove #brazilianmusic #partytime #dancevibes",
    "dark": "#dark #darkmusic #darkvibes #darkambient #darkwave #gothic",
    "pop": "#pop #popmusic #popvibes #newmusic #hitmusic #catchy",
    "default": "#music #newmusic #viralmusic #musiclover #musicshorts",
}

UNIVERSAL_TAGS = "#shorts #youtubeshorts #viral #fyp #foryou #trending #musicshorts"


def _fallback_description(base_title: str, style: str, styles: list[str], short_num: int) -> str:
    clean = clean_for_youtube(base_title)
    style_tags = STYLE_HASHTAGS.get(style, STYLE_HASHTAGS["default"])
    all_styles = " | ".join(s.title() for s in styles) if styles else style.title()

    mood_lines = {
        1: "Immediate hook and strong visual mood.",
        2: "A replayable moment with a clean emotional pull.",
        3: "Built for the payoff, drop, and retention moment.",
        4: "Focused on atmosphere, feeling, and replay value.",
        5: "A variation made to test click-through and repeat plays.",
    }
    mood = mood_lines.get(short_num, mood_lines[1])

    return (
        f"🎵 {clean}\n\n"
        f"Style: {all_styles}\n"
        f"Mood: {mood}\n\n"
        f"🎧 Full track on Spotify:\n{SPOTIFY_LINK}\n\n"
        f"📲 Follow on TikTok for more:\n{TIKTOK_LINK}\n\n"
        f"🔔 Subscribe for daily music drops\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{style_tags}\n"
        f"{UNIVERSAL_TAGS}"
    )


def build_description(
    base_title: str,
    style: str,
    styles: list[str],
    short_num: int,
) -> str:
    client = get_anthropic_client()
    if client is None:
        return _fallback_description(base_title, style, styles, short_num)

    all_styles = ", ".join(styles) if styles else style
    try:
        resp = client.messages.create(
            model=get_anthropic_model(),
            max_tokens=350,
            system=(
                "You are a YouTube SEO expert for music Shorts. "
                "Write short, human, search-friendly descriptions."
            ),
            messages=[{
                "role": "user",
                "content": (
                    f"Write a YouTube Shorts description for:\n"
                    f"Song: {base_title}\n"
                    f"Style: {all_styles}\n"
                    f"Variation: {short_num} of 5\n\n"
                    f"Include:\n"
                    f"- a 1-2 sentence hook\n"
                    f"- a short mood/SEO phrase for searchability\n"
                    f"- Spotify placeholder [SPOTIFY]\n"
                    f"- TikTok placeholder [TIKTOK]\n"
                    f"- CTA to subscribe\n"
                    f"- relevant hashtags\n"
                    f"Keep it under 250 words."
                ),
            }],
        )
        desc = resp.content[0].text.strip()
        desc = desc.replace("[SPOTIFY]", SPOTIFY_LINK)
        desc = desc.replace("[TIKTOK]", TIKTOK_LINK)
        return desc[:4500]
    except Exception as e:
        log(f"[Claude] Falha na descrição: {e} — usando fallback")
        return _fallback_description(base_title, style, styles, short_num)


def build_metadata(
    filename: str,
    short_num: int,
    style: str,
    styles: list[str],
) -> tuple[str, str, list[str]]:
    base = clean_title(filename)
    clean = clean_for_youtube(base)

    title = generate_viral_title(clean, style, styles, short_num)
    desc = build_description(clean, style, styles, short_num)

    tags = list({
        "music",
        "shorts",
        "youtube shorts",
        "viral music",
        "new music",
        "music video",
        style,
        f"{style} music",
        clean.lower(),
        *styles,
        *[f"{s} music" for s in styles],
        "independent music",
        "underground music",
        "new artist",
        "anime aesthetic",
        "music aesthetic",
        "visual edit",
    })
    return title, desc, tags[:500]


# ══════════════════════════════════════════════════════════════════════════════
# ESTADO
# ══════════════════════════════════════════════════════════════════════════════

def load_state() -> dict[str, Any]:
    if not STATE_FILE.exists():
        return {"tracks": [], "queue_index": 0, "last_posted_track": None}

    with STATE_FILE.open("r", encoding="utf-8") as f:
        if fcntl:
            fcntl.flock(f, fcntl.LOCK_SH)
        try:
            state = json.load(f)
        finally:
            if fcntl:
                fcntl.flock(f, fcntl.LOCK_UN)

    state.setdefault("tracks", [])
    state.setdefault("queue_index", 0)
    state.setdefault("last_posted_track", None)

    for track in state["tracks"]:
        track.setdefault("shorts_done", 0)
        track.setdefault("done", False)
        track.setdefault("is_new", False)

    return state


def save_state(state: dict[str, Any]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with STATE_FILE.open("w", encoding="utf-8") as f:
        if fcntl:
            fcntl.flock(f, fcntl.LOCK_EX)
        try:
            json.dump(state, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        finally:
            if fcntl:
                fcntl.flock(f, fcntl.LOCK_UN)


def sync_tracks(state: dict[str, Any], drive_files: list[dict[str, str]]) -> None:
    existing = {track["name"]: track for track in state["tracks"]}

    for file_item in drive_files:
        if file_item["name"] not in existing:
            log(f"Nova música: {file_item['name']}")
            state["tracks"].append({
                "id": file_item["id"],
                "name": file_item["name"],
                "shorts_done": 0,
                "done": False,
                "is_new": True,
            })
        else:
            existing[file_item["name"]]["id"] = file_item["id"]

    drive_names = {f["name"] for f in drive_files}
    state["tracks"] = [track for track in state["tracks"] if track["name"] in drive_names]

    total = len(state["tracks"])
    state["queue_index"] = state["queue_index"] % total if total else 0


def get_next_track(state: dict[str, Any]) -> dict[str, Any] | None:
    tracks = state["tracks"]
    if not tracks:
        return None

    last = state.get("last_posted_track")

    new_tracks = [t for t in tracks if t.get("is_new")]
    if new_tracks:
        chosen = next((t for t in new_tracks if t["name"] != last), new_tracks[0])
        chosen["is_new"] = False
        return chosen

    idx = state.get("queue_index", 0) % len(tracks)
    available: list[tuple[int, dict[str, Any]]] = []
    for i in range(len(tracks)):
        track = tracks[(idx + i) % len(tracks)]
        if track.get("shorts_done", 0) < SHORTS_PER_TRACK:
            available.append(((idx + i) % len(tracks), track))

    if not available:
        log("Todas as músicas completadas — resetando fila.")
        for track in tracks:
            track["shorts_done"] = 0
            track["done"] = False
        available = list(enumerate(tracks))

    for i, track in available:
        if track["name"] != last:
            state["queue_index"] = (i + 1) % len(tracks)
            return track

    i, track = available[0]
    state["queue_index"] = (i + 1) % len(tracks)
    return track


# ══════════════════════════════════════════════════════════════════════════════
# BACKGROUND
# ══════════════════════════════════════════════════════════════════════════════

def resolve_background(
    style: str,
    filename: str,
    short_num: int,
    styles: list[str],
) -> str:
    """
    IA primeiro: garante visual com personagem feminina.
    Fallback local só se a geração falhar.
    """
    os.makedirs("temp", exist_ok=True)

    prompt = build_ai_prompt(style, filename, styles, short_num=short_num)
    log("Gerando imagem IA focada em personagem feminina estilizada…")
    log(f"Prompt: {prompt[:140]}...")

    dest = f"temp/{Path(filename).stem}_{short_num}.png"
    image_path = generate_image(prompt, output_path=dest)
    if image_path and os.path.exists(image_path):
        log(f"Imagem IA salva: {image_path}")
        return image_path

    try:
        bg = get_random_background(style, filename)
        if bg and not str(bg).startswith("__AUTO"):
            log(f"Fallback background local: {bg}")
            return bg
    except Exception as e:
        log(f"Fallback local falhou: {e}")

    fallback = "assets/backgrounds/default.jpg"
    if os.path.exists(fallback):
        log("Usando fallback default.jpg")
        return fallback

    raise FileNotFoundError("Nenhum background disponível.")


def build_output_path(base_title: str, style: str, short_num: int) -> str:
    date = datetime.utcnow().strftime("%Y-%m-%d")
    folder = Path("output") / date / style
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{date}__{style}__{safe_filename(base_title)}__s{short_num}.mp4"
    return str(folder / name)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    log("═" * 50)
    log("BOT INICIADO — Premium Girl Visual Edition")
    log("═" * 50)

    if not DRIVE_FOLDER_ID:
        raise ValueError("DRIVE_FOLDER_ID não configurado.")

    state = load_state()
    service = get_drive_service()

    inbox_id = find_folder_id(service, DRIVE_FOLDER_ID, "inbox")
    if not inbox_id:
        raise ValueError("Pasta 'inbox' não encontrada no Drive.")

    files = list_audio_files_in_folder(service, inbox_id)
    log(f"Áudios no Drive: {len(files)}")
    for file_item in files:
        log(f"  • {file_item['name']}")

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
    log(f"Estilo: {style} | Estilos: {styles}")
    log(f"Short {short_num}/{SHORTS_PER_TRACK}")

    os.makedirs("temp", exist_ok=True)
    audio_path = f"temp/{name}"

    try:
        log("Baixando áudio…")
        download_drive_file(service, track["id"], audio_path)
        log("Download concluído.")

        bg = resolve_background(style, name, short_num, styles)
        output_path = build_output_path(base_title, style, short_num)

        log("Gerando vídeo com overlays de retenção…")
        video_path = create_short(
            audio_path,
            bg,
            output_path,
            style,
            song_name=clean_for_youtube(base_title),
        )
        log(f"Vídeo: {video_path}")

        log("Gerando metadata viral com Claude…")
        title, desc, tags = build_metadata(name, short_num, style, styles)
        log(f"Título: {title}")

        human_delay()

        log("Fazendo upload no YouTube…")
        response = upload_video(video_path, title, desc, tags, "public")
        video_id = response.get("id", "?") if isinstance(response, dict) else "?"
        log(f"Publicado! https://youtu.be/{video_id}")

        try:
            backup_id = find_folder_id(service, DRIVE_FOLDER_ID, "backups")
            if backup_id:
                log("Salvando backup no Drive…")
                upload_file_to_drive(service, backup_id, video_path)
                log("Backup salvo.")
            else:
                log("Pasta 'backups' não encontrada — pulando.")
        except Exception as e:
            log(f"Backup falhou (não crítico): {e}")

        track["shorts_done"] = short_num
        track["done"] = short_num >= SHORTS_PER_TRACK
        state["last_posted_track"] = name
        save_state(state)

        log(f"✅ Concluído: {name} (short {short_num}/{SHORTS_PER_TRACK})")
        log(f"   YouTube: https://youtu.be/{video_id}")
        log("═" * 50)

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
        log(f"❌ ERRO: {e}")
        traceback.print_exc()
        raise
