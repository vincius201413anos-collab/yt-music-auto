"""
main.py — Bot de automação YouTube Shorts
Versão 2.0 — Visual cinematográfico + títulos únicos + modelo corrigido.
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
)
from background_selector import detect_style, detect_styles, get_random_background
from video_generator import create_short
from youtube_service import upload_video
from ai_image_generator import generate_image, build_ai_prompt

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO
# ══════════════════════════════════════════════════════════════════════════════

STATE_FILE = Path("state.json")
SHORTS_PER_TRACK = 5
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")
HUMAN_DELAY_MIN = 10
HUMAN_DELAY_MAX = 60
SPOTIFY_LINK = "https://open.spotify.com/intl-pt/artist/1zyM1Pyi4YLAQgrSVRAYEy?si=3fQcRGwSQ8O2vsqq6jOVow"
TIKTOK_LINK = "https://www.tiktok.com/@darkmrkedit?is_from_webapp=1&sender_device=pc"
AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".opus"}

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

TITLE_FORMATS_BY_POSITION = {
    1: "{hook} | {title}",
    2: "{title} | {hook}",
    3: "You need to hear this 🎧 {title}",
    4: "{hook} — {title}",
    5: "Play this at {time} 🌙 {title}",
}

STYLE_TIME_CONTEXT = {
    "lofi": "3am",
    "indie": "sunset",
    "rock": "full volume",
    "metal": "midnight",
    "phonk": "night drive",
    "trap": "the top",
    "electronic": "the drop",
    "dark": "2am",
    "pop": "max volume",
    "funk": "the party",
    "cinematic": "the moment",
    "default": "midnight",
}

STYLE_HOOKS = {
    "rock": [
        "Your speakers won't forgive you 🎸",
        "This guitar hit different tonight 🔥",
        "Can't skip, won't skip 🎸",
        "This one goes to 11 ⚡",
        "Your playlist needed this 🔥",
    ],
    "metal": [
        "This drop is unreal 😈",
        "Not for the faint-hearted 🔥",
        "Your ears aren't ready 🖤",
        "Warning: extremely heavy ⚠️",
        "This hits like a freight train 😈",
    ],
    "phonk": [
        "Save this for the night drive 🌙",
        "Your city needs this energy 😈",
        "The underground found a new anthem 🔥",
        "This doesn't belong on a playlist 😳",
        "Night mode: activated 🖤",
    ],
    "trap": [
        "This one built different 💎",
        "Your headphones deserved this 👑",
        "That baseline just walked in 🔥",
        "Luxury frequency unlocked 💎",
        "Certified banger, no debate 🏆",
    ],
    "indie": [
        "You'll replay this all week 🎧",
        "Someone left this feeling in a song 🌙",
        "Your next favorite song 🎵",
        "This one stays with you 🌅",
        "The feeling you couldn't name 🎧",
    ],
    "lofi": [
        "Sleep to this tonight 🌙",
        "Your study playlist found its anchor 📚",
        "3am and this is perfect ☁️",
        "Quiet enough to think, beautiful enough to feel 🌙",
        "This is what calm sounds like 🎧",
    ],
    "electronic": [
        "That drop will break your brain 🤯",
        "The festival you never attended ⚡",
        "Your ears are about to time travel 🚀",
        "This frequency doesn't exist yet ⚡",
        "The drop you won't see coming 🤯",
    ],
    "cinematic": [
        "This sounds like a movie scene 🎬",
        "Your moment has a soundtrack now 🎬",
        "The feeling before something changes 🌌",
        "This exists to give you chills 🎬",
        "Goosebumps loading… 🌌",
    ],
    "funk": [
        "Your body already knows this one 🕺",
        "Play this and watch the room change 🔥",
        "This groove is criminal 🎵",
        "You weren't ready for this 🕺",
        "Dance whether you want to or not 🔥",
    ],
    "dark": [
        "This found you at the right moment 🌑",
        "Beautiful and haunting 🖤",
        "Some songs carry entire nights 🌙",
        "Your soul needed this 🌑",
        "The darkness has a melody 🖤",
    ],
    "pop": [
        "This one's going on every playlist 🌟",
        "Warning: extremely catchy ✨",
        "You'll sing this all week 💫",
        "Certified earworm — you've been warned ✨",
        "The song you didn't know you needed 🌸",
    ],
    "default": [
        "Your playlist needed this upgrade 🎵",
        "You won't regret pressing play 🎧",
        "This is the one 🔥",
        "Found: your new favorite 🎵",
        "Don't say we didn't warn you 🎧",
    ],
}


def generate_viral_title(
    base_title: str,
    style: str,
    styles: list[str],
    short_num: int = 1,
) -> str:
    client = get_anthropic_client()
    if client:
        try:
            return _claude_title(client, base_title, style, styles, short_num)
        except Exception as e:
            log(f"[Claude] Falha no título: {e} — usando fallback")
    return _static_title(base_title, style, short_num)


def _claude_title(
    client: anthropic.Anthropic,
    base_title: str,
    style: str,
    styles: list[str],
    short_num: int,
) -> str:
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
            "You write viral YouTube Shorts titles for a music channel. "
            "Your titles are punchy, emotionally resonant, and make people stop scrolling. "
            "Each title must feel fresh and specific to the genre — never generic. "
            "Include 1-2 relevant emojis. "
            "Output ONLY the title — no explanation, no quotes."
        ),
        messages=[{
            "role": "user",
            "content": (
                f"Write a YouTube Shorts title for:\n"
                f"Song: {base_title}\n"
                f"Genre: {all_styles}\n"
                f"Title strategy: {position_hint}\n\n"
                f"Rules:\n"
                f"- Max 80 characters\n"
                f"- Specific to {style} music culture and audience\n"
                f"- Creates emotional pull or curiosity\n"
                f"- Sounds human, not AI-generated\n"
                f"- Avoid: 'hits different', 'fire', 'banger', 'slaps' (overused)\n"
                f"- Use current 2025 YouTube Shorts language"
            ),
        }],
    )
    title = resp.content[0].text.strip().strip('"').strip("'")
    log(f"[Claude] Título gerado: {title}")
    return title[:100]


def _static_title(base_title: str, style: str, short_num: int) -> str:
    clean = clean_for_youtube(base_title)
    hooks = STYLE_HOOKS.get(style, STYLE_HOOKS["default"])
    hook = hooks[(short_num - 1) % len(hooks)]
    time_ctx = STYLE_TIME_CONTEXT.get(style, "midnight")
    fmt = TITLE_FORMATS_BY_POSITION.get(short_num, "{hook} | {title}")
    return fmt.format(hook=hook, title=clean, time=time_ctx)[:100]


# ══════════════════════════════════════════════════════════════════════════════
# METADATA
# ══════════════════════════════════════════════════════════════════════════════

STYLE_HASHTAGS = {
    "electronic": "#electronic #edm #electronicmusic #synthwave #clubmusic #rave #dancemusic #techno #trance #futuremusic",
    "phonk": "#phonk #phonkmusic #darkphonk #phonkedit #drift #phonkvibes #russiaphonk #phonkrap #aggressive #phonktiktok",
    "trap": "#trap #trapmusic #trapbeats #hiphop #traprap #hardtrap #banger #trapart #drip #trapgang",
    "rock": "#rock #rockmusic #hardrock #guitarmusic #livemusic #rockband #alternative #grunge #rockguitar #indierock",
    "metal": "#metal #metalmusic #heavymetal #deathmetal #metalhead #extrememetal #progressivemetal #metalcore #djent",
    "indie": "#indie #indiemusic #indierock #alternativemusic #indievibes #bedroom #emotionalmusic #sadmusic",
    "lofi": "#lofi #lofihiphop #lofichill #studymusic #relaxingmusic #chillvibes #lofibeats #lofimusic #chill",
    "cinematic": "#cinematic #cinematicmusic #epicmusic #orchestral #filmmusic #cinemamusic #dramatic #epicorchestralmusic",
    "funk": "#funk #funkmusic #groove #brazilianmusic #soulmusic #funkychill #groovemusic #partytime",
    "dark": "#dark #darkmusic #darkvibes #darkambient #haunting #mysterious #darkness #darkwave #gothic",
    "pop": "#pop #popmusic #popvibes #newmusic #chart #top40 #popbanger #hitmusic #mainstream",
    "sertanejo": "#sertanejo #sertanejouniversitario #musicasertaneja #sertanejoromantic #brasil #musicabrasileira",
    "mpb": "#mpb #musicapopularbrasileira #bossanova #brasil #musicabrasileira #jazz #acoustic",
    "default": "#music #newmusic #viralmusic #musiclover #underground #musicshorts #indiemusic",
}

UNIVERSAL_TAGS = "#shorts #youtubeshorts #viral #fyp #foryou #trending #musicshorts"


def build_description(
    base_title: str,
    style: str,
    styles: list[str],
) -> str:
    client = get_anthropic_client()
    if client:
        try:
            return _claude_description(client, base_title, style, styles)
        except Exception as e:
            log(f"[Claude] Falha na descrição: {e} — usando fallback")
    return _static_description(base_title, style, styles)


def _claude_description(
    client: anthropic.Anthropic,
    base_title: str,
    style: str,
    styles: list[str],
) -> str:
    all_styles = ", ".join(styles) if styles else style
    resp = client.messages.create(
        model=get_anthropic_model(),
        max_tokens=400,
        system=(
            "You are a YouTube SEO expert for music channels. "
            "You write compelling, keyword-rich descriptions that feel human. "
            "Connect with fans emotionally. Drive subscriptions and Spotify streams."
        ),
        messages=[{
            "role": "user",
            "content": (
                f"Write a YouTube Shorts description for:\n"
                f"Song: {base_title}\n"
                f"Style: {all_styles}\n\n"
                f"Include:\n"
                f"1. Emotional hook (1-2 sentences about the feeling of {style} music)\n"
                f"2. Spotify link placeholder: [SPOTIFY]\n"
                f"3. TikTok link placeholder: [TIKTOK]\n"
                f"4. Brief call to subscribe\n"
                f"5. Hashtags for {style}\n\n"
                f"Under 300 words. Feels human, not corporate."
            ),
        }],
    )
    desc = resp.content[0].text.strip()
    desc = desc.replace("[SPOTIFY]", SPOTIFY_LINK)
    desc = desc.replace("[TIKTOK]", TIKTOK_LINK)
    return desc[:4500]


def _static_description(base_title: str, style: str, styles: list[str]) -> str:
    clean = clean_for_youtube(base_title)
    style_tags = STYLE_HASHTAGS.get(style, STYLE_HASHTAGS["default"])
    all_styles = " | ".join(s.title() for s in styles) if styles else style.title()
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


def build_metadata(
    filename: str,
    short_num: int,
    style: str,
    styles: list[str],
) -> tuple[str, str, list[str]]:
    base = clean_title(filename)
    clean = clean_for_youtube(base)
    title = generate_viral_title(clean, style, styles, short_num)
    desc = build_description(clean, style, styles)
    tags = list({
        "music", "shorts", "youtube shorts", "viral music",
        "new music", "music video", style, f"{style} music",
        clean.lower(),
        *[s for s in styles],
        *[f"{s} music" for s in styles],
        "independent music", "underground music", "new artist",
        "anime aesthetic", "music aesthetic", "visual edit",
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
                "id": f["id"],
                "name": f["name"],
                "shorts_done": 0,
                "done": False,
                "is_new": True,
            })
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
# BACKGROUND — IA SEMPRE PRIMEIRO
# ══════════════════════════════════════════════════════════════════════════════

def resolve_background(
    style: str,
    filename: str,
    short_num: int,
    styles: list[str],
) -> str:
    os.makedirs("temp", exist_ok=True)

    prompt = build_ai_prompt(style, filename, styles, short_num=short_num)
    log(f"Gerando imagem IA — gênero: {style}, variação {short_num}")
    log(f"Prompt: {prompt[:120]}...")

    dest = f"temp/{Path(filename).stem}_{short_num}.png"
    img = generate_image(prompt, output_path=dest)
    if img and os.path.exists(img):
        log(f"Imagem IA salva: {img}")
        return img

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

def main():
    log("═" * 50)
    log("BOT INICIADO — Cinematic Girl Visual Edition v2.0")
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
    for f in files:
        log(f"  • {f['name']}")

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
    log(f"Estilo: {style} | Estilos detectados: {styles}")
    log(f"Short {short_num}/{SHORTS_PER_TRACK}")

    os.makedirs("temp", exist_ok=True)
    audio_path = f"temp/{name}"

    log("Baixando áudio…")
    download_drive_file(service, track["id"], audio_path)
    log("Download concluído.")

    video_path = None
    bg = None

    try:
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

        # BACKUP DESATIVADO POR ENQUANTO
        # Não salva mais no Drive nem no GitHub storage

        track["shorts_done"] = short_num
        track["done"] = short_num >= SHORTS_PER_TRACK
        state["last_posted_track"] = name
        save_state(state)

        log(f"✅ Concluído: {name} (short {short_num}/{SHORTS_PER_TRACK})")
        log(f"   YouTube: https://youtu.be/{video_id}")

    finally:
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
                log(f"Áudio temporário removido: {audio_path}")
        except Exception as e:
            log(f"Falha ao remover áudio temporário: {e}")

        try:
            if video_path and os.path.exists(video_path):
                os.remove(video_path)
                log(f"Vídeo temporário removido: {video_path}")
        except Exception as e:
            log(f"Falha ao remover vídeo temporário: {e}")

        try:
            if bg and str(bg).startswith("temp/") and os.path.exists(bg):
                os.remove(bg)
                log(f"Imagem temporária removida: {bg}")
        except Exception as e:
            log(f"Falha ao remover imagem temporária: {e}")

    log("═" * 50)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"❌ ERRO: {e}")
        traceback.print_exc()
        raise
