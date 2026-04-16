"""
main.py — Bot de automação YouTube Shorts
Claude Opus gera títulos e descrições virais dinamicamente.
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
from ai_image_generator import generate_image, build_ai_prompt

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO
# ══════════════════════════════════════════════════════════════════════════════

STATE_FILE       = Path("state.json")
SHORTS_PER_TRACK = 3
DRIVE_FOLDER_ID  = os.getenv("DRIVE_FOLDER_ID")

HUMAN_DELAY_MIN = 10
HUMAN_DELAY_MAX = 60

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
# TÍTULOS VIRAIS — CLAUDE OPUS
# ══════════════════════════════════════════════════════════════════════════════

# Fallback estático quando a API falha
STYLE_HOOKS = {
    "rock":       ["This Hits HARD 🔥", "You Feel This One 🎸", "Rock That Goes Crazy 🔥", "This Drop Is Insane 🤯", "Can't Skip This 🎸", "This One Is Wild ⚡"],
    "metal":      ["This Goes INSANE 🔥", "Heavy Drop Warning ⚠️", "Metal That Hits HARD 🔥", "Pure Chaos 🤯", "This One Is Brutal 😈", "No Skip Zone 🔥"],
    "phonk":      ["This Feels Illegal 😈", "Night Drive Vibes 🌙", "Phonk Energy 🔥", "This One Is Different 😳", "You'll Replay This 🔁", "Too Dark, Too Good 🖤"],
    "trap":       ["This Goes HARD 🔥", "Trap Energy 😈", "Luxury Vibes 💎", "You'll Replay This 🔁", "Too Clean To Ignore ✨", "This Hits Different 😮"],
    "indie":      ["You Feel This One 🎧", "Late Night Mood 🌌", "This Hits Different 😳", "Emotional Vibes 🌙", "Loop This 🔁", "This One Stays With You ✨"],
    "lofi":       ["Late Night Vibes 🌙", "You'll Loop This 🔁", "Calm But Addictive 🎧", "This Is A Mood ☁️", "Study With This 📚", "This Feels Different ✨"],
    "electronic": ["This Drop Hits HARD 🔥", "Electronic Energy ⚡", "You'll Replay This 🔁", "This Is Unreal 🤯", "This Sounds Massive 🎧", "Pure Energy ⚡"],
    "cinematic":  ["This Feels Cinematic 🎬", "You Need To Hear This ✨", "This Hits Different 😳", "Pure Atmosphere 🌌", "Epic From Start 🎬", "This Sounds Huge 🔥"],
    "funk":       ["This Hits Different 🔥", "Party Energy ⚡", "This One Goes Crazy 🤯", "Don't Skip This 😳", "Brazilian Vibes 🔥", "Feel The Groove 🎵"],
    "dark":       ["Dark Vibes Only 😈", "This Feels Dangerous 🔥", "You'll Replay This 🌑", "This Hits Different 😳", "Too Dark, Too Good 🖤", "Night Mode 🌙"],
    "pop":        ["This Is Addictive 🔁", "Don't Skip This 😳", "You'll Love This 💫", "Gets Better Every Loop 🔥", "Too Clean To Ignore ✨", "This One Slaps 🎵"],
    "default":    ["This Hits Different 😳", "You'll Replay This 🔁", "Don't Skip This 😳", "This Is Addictive 🔥", "Gets Better Every Loop 🔥", "This One Slaps 🎵"],
}

FORMATS = [
    "{hook} | {title}",
    "{title} | {hook}",
    "{hook} — {title}",
    "{title} — {hook}",
    "{hook} 🎵 {title}",
]


def generate_viral_title_opus(
    base_title: str,
    style: str,
    styles: list,
) -> str:
    """
    Usa Claude Opus para gerar título viral único, específico e
    otimizado para o algoritmo do YouTube Shorts.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return _static_title(base_title, style)

    try:
        client = anthropic.Anthropic(api_key=api_key)
        all_styles = ", ".join(styles) if styles else style

        resp = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=120,
            system=(
                "You are a viral YouTube Shorts title expert. "
                "You write short, punchy, emotionally compelling titles "
                "that maximize CTR and retention. "
                "Your titles trigger curiosity, FOMO, and emotional response. "
                "Always include 1-2 relevant emojis. "
                "Never use generic phrases. "
                "Output ONLY the title — no explanation, no quotes."
            ),
            messages=[{
                "role": "user",
                "content": (
                    f"Create a viral YouTube Shorts title for this music:\n"
                    f"Song name: {base_title}\n"
                    f"Music style: {all_styles}\n\n"
                    f"Rules:\n"
                    f"- Max 80 characters\n"
                    f"- Must make people STOP scrolling\n"
                    f"- Reference the specific sound/feeling of {style} music\n"
                    f"- Create curiosity or emotional pull\n"
                    f"- Mix the song name with a viral hook naturally\n"
                    f"- Avoid overused phrases like 'hits different' or 'fire'\n"
                    f"- Use current 2025 YouTube Shorts language"
                ),
            }],
        )

        title = resp.content[0].text.strip().strip('"').strip("'")
        title = title[:100]
        log(f"[Opus] Título gerado: {title}")
        return title

    except Exception as e:
        log(f"[Opus] Falha no título: {e} — usando fallback")
        return _static_title(base_title, style)


def _static_title(base_title: str, style: str) -> str:
    """Título estático de alta qualidade."""
    clean = clean_for_youtube(base_title)
    hooks = STYLE_HOOKS.get(style, STYLE_HOOKS["default"])
    hook  = random.choice(hooks)
    fmt   = random.choice(FORMATS)
    return fmt.format(hook=hook, title=clean)[:100]


# ══════════════════════════════════════════════════════════════════════════════
# METADATA — CLAUDE OPUS
# ══════════════════════════════════════════════════════════════════════════════

# Hashtags por estilo — curadas para máximo alcance
STYLE_HASHTAGS = {
    "electronic": "#electronic #edm #electronicmusic #synthwave #clubmusic #rave #dancemusic #techno #trance #futuremusic",
    "phonk":      "#phonk #phonkmusic #darkphonk #phonkedit #drift #phonkvibes #russiaphonk #phonkrap #aggressive #phonktiktok",
    "trap":       "#trap #trapmusic #trapbeats #hiphop #traprap #hardtrap #banger #trapart #drip #trapgang",
    "rock":       "#rock #rockmusic #hardrock #guitarmusic #livemusic #rockband #alternative #grunge #rockguitar #indierock",
    "metal":      "#metal #metalmusic #heavymetal #deathmetal #metalhead #extrememetal #progressivemetal #metalcore #djent",
    "indie":      "#indie #indiemusic #indierock #alternativemusic #indievibes #bedroom #emotionalmusic #sadmusic",
    "lofi":       "#lofi #lofihiphop #lofichill #studymusic #relaxingmusic #chillvibes #lofibeats #lofimusic #chill",
    "cinematic":  "#cinematic #cinematicmusic #epicmusic #orchestral #filmmusic #cinemamusic #dramatic #epicorchestralmmusic",
    "funk":       "#funk #funkmusic #groove #brazilianmusic #soulmusic #funkychill #groovemusic #partytime",
    "dark":       "#dark #darkmusic #darkvibes #darkambient #haunting #mysterious #darkness #darkwave #gothic",
    "pop":        "#pop #popmusic #popvibes #newmusic #chart #top40 #popbanger #hitmusic #mainstream",
    "default":    "#music #newmusic #viralmusic #musiclover #underground #musicshorts #indiemúsic",
}

UNIVERSAL_TAGS = "#shorts #youtubeshorts #viral #fyp #foryou #trending #musicshorts"


def build_description_opus(
    base_title: str,
    style: str,
    styles: list,
) -> str:
    """
    Usa Claude Opus para criar descrição otimizada para SEO e conversão.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return _static_description(base_title, style, styles)

    try:
        client = anthropic.Anthropic(api_key=api_key)
        all_styles = ", ".join(styles) if styles else style

        resp = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=400,
            system=(
                "You are a YouTube SEO expert specializing in music channels. "
                "You write compelling, keyword-rich video descriptions that "
                "maximize watch time and drive channel subscribers. "
                "Always write in a way that connects with music fans emotionally."
            ),
            messages=[{
                "role": "user",
                "content": (
                    f"Write a YouTube Shorts description for:\n"
                    f"Song: {base_title}\n"
                    f"Style: {all_styles}\n\n"
                    f"Include:\n"
                    f"1. Short emotional hook (1-2 sentences about the feeling)\n"
                    f"2. Spotify link placeholder: [SPOTIFY]\n"
                    f"3. TikTok link placeholder: [TIKTOK]\n"
                    f"4. Brief call to action to subscribe\n"
                    f"5. Relevant hashtags for {style} music\n\n"
                    f"Keep it under 300 words. Make it feel human, not corporate."
                ),
            }],
        )

        desc = resp.content[0].text.strip()
        desc = desc.replace("[SPOTIFY]", SPOTIFY_LINK)
        desc = desc.replace("[TIKTOK]", TIKTOK_LINK)
        return desc[:4500]

    except Exception as e:
        log(f"[Opus] Falha na descrição: {e} — usando fallback")
        return _static_description(base_title, style, styles)


def _static_description(base_title: str, style: str, styles: list) -> str:
    """Descrição estática de alta qualidade."""
    clean = clean_for_youtube(base_title)
    style_tags = STYLE_HASHTAGS.get(style, STYLE_HASHTAGS["default"])
    all_styles  = " | ".join(s.title() for s in styles) if styles else style.title()

    return (
        f"🎵 {clean}\n\n"
        f"Style: {all_styles}\n\n"
        f"🎧 Full track on Spotify:\n{SPOTIFY_LINK}\n\n"
        f"📲 Follow on TikTok for more:\n{TIKTOK_LINK}\n\n"
        f"🔔 Subscribe for daily music drops\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{style_tags}\n"
        f"{UNIVERSAL_TAGS}"
    )


def build_metadata(filename: str, short_num: int, style: str, styles: list):
    """Monta título, descrição e tags otimizados."""
    base  = clean_title(filename)
    clean = clean_for_youtube(base)

    title = generate_viral_title_opus(clean, style, styles)
    desc  = build_description_opus(clean, style, styles)

    tags = list({
        "music", "shorts", "youtube shorts", "viral music",
        "new music", "music video", style, f"{style} music",
        clean.lower(),
        *[s for s in styles],
        *[f"{s} music" for s in styles],
        "independent music", "underground music", "new artist",
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

    drive_names     = {f["name"] for f in drive_files}
    state["tracks"] = [t for t in state["tracks"] if t["name"] in drive_names]

    n = len(state["tracks"])
    state["queue_index"] = state["queue_index"] % n if n else 0


def get_next_track(state: dict):
    tracks = state["tracks"]
    if not tracks:
        return None

    last = state.get("last_posted_track")

    # Novas músicas têm prioridade absoluta
    new = [t for t in tracks if t.get("is_new")]
    if new:
        chosen = next((t for t in new if t["name"] != last), new[0])
        chosen["is_new"] = False
        return chosen

    # Fila circular — pula done e evita repetir a última
    idx   = state.get("queue_index", 0) % len(tracks)
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

def resolve_background(style: str, filename: str, short_num: int, styles: list) -> str:
    # 1. Tenta background local primeiro
    try:
        bg = get_random_background(style, filename)
        if bg and not str(bg).startswith("__AUTO"):
            log(f"Background local: {bg}")
            return bg
    except Exception as e:
        log(f"Background local falhou: {e}")

    # 2. Gera imagem IA — Claude Opus cria o prompt
    os.makedirs("temp", exist_ok=True)
    prompt = build_ai_prompt(style, filename, styles)
    log(f"Gerando imagem IA (Opus+Flux)…")
    log(f"Prompt: {prompt[:120]}…")

    dest = f"temp/{Path(filename).stem}_{short_num}.png"
    img  = generate_image(prompt, output_path=dest)
    if img and os.path.exists(img):
        log(f"Imagem IA salva: {img}")
        return img

    # 3. Fallback final
    fallback = "assets/backgrounds/default.jpg"
    if os.path.exists(fallback):
        log("Usando fallback default.jpg")
        return fallback

    raise FileNotFoundError("Nenhum background disponível.")


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
    log("BOT INICIADO — Claude Opus Edition")
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

    log("Gerando vídeo com overlays de retenção…")
    # Passa song_name explicitamente para os overlays
    video_path = create_short(
        audio_path, bg, output_path, style,
        song_name=clean_for_youtube(base_title),
    )
    log(f"Vídeo: {video_path}")

    # Gera metadata com Claude Opus
    log("Gerando metadata viral com Opus…")
    title, desc, tags = build_metadata(name, short_num, style, styles)
    log(f"Título: {title}")

    human_delay()

    log("Fazendo upload no YouTube…")
    response = upload_video(video_path, title, desc, tags, "public")
    video_id = response.get("id", "?") if isinstance(response, dict) else "?"
    log(f"Publicado! https://youtu.be/{video_id}")

    # Backup no Drive
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

    # Atualiza estado
    track["shorts_done"] = short_num
    track["done"]        = short_num >= SHORTS_PER_TRACK
    state["last_posted_track"] = name
    save_state(state)

    # Limpa temp
    try:
        if os.path.exists(audio_path):
            os.remove(audio_path)
    except Exception:
        pass

    log(f"✅ Concluído: {name} (short {short_num}/{SHORTS_PER_TRACK})")
    log(f"   YouTube: https://youtu.be/{video_id}")
    log("═" * 50)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"❌ ERRO: {e}")
        traceback.print_exc()
        raise
