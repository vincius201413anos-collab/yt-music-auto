"""
main.py — Bot de automação YouTube Shorts
Arquitetura limpa, logs detalhados, tratamento robusto de erros.
"""

import os
import json
import re
import shutil
import random
import time
import traceback
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
from ai_image_generator import generate_image, build_ai_prompt

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO
# ══════════════════════════════════════════════════════════════════════════════

STATE_FILE      = Path("state.json")
SHORTS_PER_TRACK = 3
DRIVE_FOLDER_ID  = os.getenv("DRIVE_FOLDER_ID")

HUMAN_DELAY_MIN = 15
HUMAN_DELAY_MAX = 120

SPOTIFY_LINK = "https://open.spotify.com/intl-pt/artist/1zyM1Pyi4YLAQgrSVRAYEy?si=3fQcRGwSQ8O2vsqq6jOVow"
TIKTOK_LINK  = "https://www.tiktok.com/@darkmrkedit?is_from_webapp=1&sender_device=pc"

AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".opus"}


# ══════════════════════════════════════════════════════════════════════════════
# UTILITÁRIOS
# ══════════════════════════════════════════════════════════════════════════════

def log(msg: str):
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


def human_delay():
    secs = random.randint(HUMAN_DELAY_MIN, HUMAN_DELAY_MAX)
    log(f"Aguardando {secs}s (comportamento humano)…")
    time.sleep(secs)


# ══════════════════════════════════════════════════════════════════════════════
# TÍTULOS VIRAIS
# ══════════════════════════════════════════════════════════════════════════════

STYLE_HOOKS = {
    "rock": [
        "This Hits HARD 🔥", "You Feel This One 🎸",
        "Rock That Goes Crazy 🔥", "This Drop Is Insane 🤯",
        "This One Is Wild ⚡", "Can't Skip This 🎸",
    ],
    "metal": [
        "This Goes INSANE 🔥", "Heavy Drop Warning ⚠️",
        "Metal That Hits HARD 🔥", "Pure Chaos 🤯",
        "This One Is Brutal 😈", "No Skip Zone 🔥",
    ],
    "phonk": [
        "This Feels Illegal 😈", "Night Drive Vibes 🌙",
        "Phonk Energy 🔥", "This One Is Different 😳",
        "You'll Replay This 🔁", "Too Dark, Too Good 🖤",
    ],
    "trap": [
        "This Goes HARD 🔥", "Trap Energy 😈",
        "Luxury Vibes 💎", "You'll Replay This 🔁",
        "Too Clean To Ignore ✨", "This Hits Different 😮",
    ],
    "indie": [
        "You Feel This One 🎧", "Late Night Mood 🌌",
        "This Hits Different 😳", "Emotional Vibes 🌙",
        "This One Stays With You ✨", "Loop This 🔁",
    ],
    "lofi": [
        "Late Night Vibes 🌙", "This Feels Different ✨",
        "You'll Loop This 🔁", "Calm But Addictive 🎧",
        "This Is A Mood ☁️", "Study With This 📚",
    ],
    "electronic": [
        "This Drop Hits HARD 🔥", "Electronic Energy ⚡",
        "You'll Replay This 🔁", "This Is Unreal 🤯",
        "This Sounds Massive 🎧", "Pure Energy ⚡",
    ],
    "cinematic": [
        "This Feels Cinematic 🎬", "You Need To Hear This ✨",
        "This Hits Different 😳", "Pure Atmosphere 🌌",
        "This Sounds Huge 🔥", "Epic From Start 🎬",
    ],
    "funk": [
        "This Hits Different 🔥", "Party Energy ⚡",
        "This One Goes Crazy 🤯", "Don't Skip This 😳",
        "Brazilian Vibes 🔥", "Feel The Groove 🎵",
    ],
    "dark": [
        "Dark Vibes Only 😈", "This Feels Dangerous 🔥",
        "You'll Replay This 🌑", "This Hits Different 😳",
        "Too Dark, Too Good 🖤", "Night Mode 🌙",
    ],
    "pop": [
        "This Is Addictive 🔁", "Don't Skip This 😳",
        "You'll Love This 💫", "Gets Better Every Loop 🔥",
        "Too Clean To Ignore ✨", "This One Slaps 🎵",
    ],
    "default": [
        "This Hits Different 😳", "You'll Replay This 🔁",
        "Don't Skip This 😳", "This Is Addictive 🔥",
        "Gets Better Every Loop 🔥", "This One Slaps 🎵",
    ],
}

ENDINGS = [
    "", "", "",
    " (Best Part 🔥)",
    " (Wait For It 😳)",
    " (Loop Worthy 🔁)",
    " (Too Clean ✨)",
]

FORMATS = [
    "{hook} | {title}{end}",
    "{title} | {hook}",
    "{hook} — {title}{end}",
    "{title} — {hook}",
    "{hook} 🎵 {title}",
]


def generate_viral_title(base_title: str, style: str) -> str:
    title = clean_for_youtube(base_title)
    hooks = STYLE_HOOKS.get(style, STYLE_HOOKS["default"])
    hook  = random.choice(hooks)
    end   = random.choice(ENDINGS)
    fmt   = random.choice(FORMATS)
    result = fmt.format(hook=hook, title=title, end=end)
    return result[:100]


# ══════════════════════════════════════════════════════════════════════════════
# METADATA
# ══════════════════════════════════════════════════════════════════════════════

def build_metadata(filename: str, short_num: int, style: str, styles: list):
    base  = clean_title(filename)
    clean = clean_for_youtube(base)
    title = generate_viral_title(clean, style)

    desc = (
        f"{clean}\n\n"
        f"🎵 Style: {style.title()} | {', '.join(s.title() for s in styles)}\n\n"
        f"🎧 Spotify:\n{SPOTIFY_LINK}\n\n"
        f"📲 TikTok:\n{TIKTOK_LINK}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"#music #shorts #youtubeshorts #{style} #viral #newmusic #edit"
    )

    tags = list({
        "music", "shorts", "youtube shorts", "viral music",
        "new music", "music video", style, f"{style} music",
        clean.lower(),
        *[s for s in styles],
        *[f"{s} music" for s in styles],
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
            state["tracks"].append({
                "id": f["id"], "name": f["name"],
                "shorts_done": 0, "done": False, "is_new": True,
            })
        else:
            tr = existing[f["name"]]
            tr["id"] = f["id"]

    drive_names = {f["name"] for f in drive_files}
    state["tracks"] = [t for t in state["tracks"] if t["name"] in drive_names]

    n = len(state["tracks"])
    state["queue_index"] = state["queue_index"] % n if n else 0


def get_next_track(state: dict):
    tracks = state["tracks"]
    if not tracks:
        return None

    last = state.get("last_posted_track")

    # novas músicas têm prioridade
    new = [t for t in tracks if t.get("is_new")]
    if new:
        chosen = next((t for t in new if t["name"] != last), new[0])
        chosen["is_new"] = False
        return chosen

    # fila circular — pula done e evita repetir a última
    idx   = state.get("queue_index", 0) % len(tracks)
    avail = []
    for i in range(len(tracks)):
        t = tracks[(idx + i) % len(tracks)]
        if t.get("shorts_done", 0) < SHORTS_PER_TRACK:
            avail.append(((idx + i) % len(tracks), t))

    if not avail:
        # reset geral quando todas estão done
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

def resolve_background(style: str, filename: str, short_num: int, styles: list) -> str:
    try:
        bg = get_random_background(style, filename)
        if bg and not str(bg).startswith("__AUTO"):
            log(f"Background local: {bg}")
            return bg
    except Exception as e:
        log(f"Falha ao buscar background local: {e}")

    os.makedirs("temp", exist_ok=True)
    prompt = build_ai_prompt(style, filename, styles)
    log(f"Gerando imagem IA: {prompt[:120]}…")

    img = generate_image(prompt)
    if img and os.path.exists(img):
        dest = f"temp/{Path(filename).stem}_{short_num}.png"
        shutil.copy2(img, dest)
        log(f"Imagem IA salva: {dest}")
        return dest

    fallback = "assets/backgrounds/default.jpg"
    if os.path.exists(fallback):
        log("Usando fallback default.jpg")
        return fallback

    raise FileNotFoundError("Nenhum background disponível e fallback não existe.")


def build_output_path(base_title: str, style: str, short_num: int) -> str:
    date   = datetime.utcnow().strftime("%Y-%m-%d")
    folder = Path("output") / date / style
    folder.mkdir(parents=True, exist_ok=True)
    name   = f"{date}__{style}__{safe_filename(base_title)}__s{short_num}.mp4"
    return str(folder / name)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    log("═" * 50)
    log("BOT INICIADO")
    log("═" * 50)

    if not DRIVE_FOLDER_ID:
        raise ValueError("DRIVE_FOLDER_ID não configurado.")

    state   = load_state()
    service = get_drive_service()

    inbox_id = find_folder_id(service, DRIVE_FOLDER_ID, "inbox")
    if not inbox_id:
        raise ValueError("Pasta 'inbox' não encontrada no Drive.")

    files = list_audio_files_in_folder(service, inbox_id)
    log(f"Áudios no Drive: {len(files)}")
    for f in files:
        log(f"  • {f['name']}")

    sync_tracks(state, files)
    save_state(state)

    track = get_next_track(state)
    if not track:
        log("Nenhuma faixa disponível. Encerrando.")
        return

    name       = track["name"]
    short_num  = track.get("shorts_done", 0) + 1
    styles     = detect_styles(name)
    style      = detect_style(name)
    base_title = clean_title(name)

    log(f"Processando: {name}")
    log(f"Estilo: {style} | Estilos: {styles}")
    log(f"Short {short_num}/{SHORTS_PER_TRACK}")

    os.makedirs("temp", exist_ok=True)
    audio_path = f"temp/{name}"

    log("Baixando áudio…")
    download_drive_file(service, track["id"], audio_path)
    log("Download concluído.")

    bg          = resolve_background(style, name, short_num, styles)
    output_path = build_output_path(base_title, style, short_num)

    log("Gerando vídeo…")
    video_path = create_short(audio_path, bg, output_path, style)
    log(f"Vídeo: {video_path}")

    title, desc, tags = build_metadata(name, short_num, style, styles)
    log(f"Título: {title}")

    human_delay()

    log("Fazendo upload no YouTube…")
    response = upload_video(video_path, title, desc, tags, "public")
    video_id = response.get("id", "?") if isinstance(response, dict) else "?"
    log(f"Publicado! https://youtu.be/{video_id}")

    # backup no Drive (opcional)
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

    # atualiza estado
    track["shorts_done"] = short_num
    track["done"]        = short_num >= SHORTS_PER_TRACK
    state["last_posted_track"] = name
    save_state(state)

    # limpa temp
    try:
        if os.path.exists(audio_path):
            os.remove(audio_path)
    except Exception:
        pass

    log(f"✅ Concluído: {name} (short {short_num}/{SHORTS_PER_TRACK})")
    log("═" * 50)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"❌ ERRO: {e}")
        traceback.print_exc()
        raise
