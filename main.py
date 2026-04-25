"""
main.py — DJ DARK MARK YouTube Shorts Bot v7.1 FINAL MERGE
=========================================================
Merge v7 (audio_analysis real, beat sync) + v4.6 (títulos, gênero, GitHub safe).

MELHORIAS DESTA VERSÃO:
- Títulos incluem o nome real da música (fix v4.6).
- Gênero rechecado por padrão (evita phonk errado no state.json).
- Correção de gênero por nome do arquivo e estilos secundários.
- audio_analysis.py Elite v2.1: snare/hihat/seções/perfil/curva de energia.
- Remotion desligado por padrão no GitHub Actions (anti-trava).
- Backup no Drive quando DRIVE_BACKUP_FOLDER_ID existir.
- Suporte a Facebook Reels (ENABLE_FACEBOOK=true).

GARANTIAS GITHUB ACTIONS FREE:
- Sem Remotion por padrão (trava o runner).
- FFmpeg com timeout configurável.
- librosa/scipy opcionais — fallback automático.
- Limpeza agressiva de temp no finally.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import shutil
import signal
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from drive_service import (
    get_drive_service,
    find_folder_id,
    list_audio_files_in_folder,
    download_drive_file,
    upload_file_to_drive,
    download_assets_from_drive,
)
from background_selector import get_random_background
from genre_detector import detect_genre, detect_genre_multi
from video_generator import create_short
from youtube_service import upload_video
from facebook_service import upload_to_facebook
from ai_image_generator import generate_image, build_ai_prompt


STATE_FILE = Path("state.json")

SHORTS_PER_TRACK = int(os.getenv("SHORTS_PER_TRACK", "1"))
RECHECK_GENRE_EACH_RUN = os.getenv("RECHECK_GENRE_EACH_RUN", "true").lower() == "true"

DRIVE_FOLDER_ID        = os.getenv("DRIVE_FOLDER_ID")
DRIVE_BACKUP_FOLDER_ID = os.getenv("DRIVE_BACKUP_FOLDER_ID", "").strip()

SPOTIFY_LINK  = os.getenv("SPOTIFY_LINK", "https://open.spotify.com/intl-pt/artist/1zyM1Pyi4YLAQgrSVRAYEy")
TIKTOK_LINK   = os.getenv("TIKTOK_LINK", "https://www.tiktok.com/@darkmrkedit")
CHANNEL_NAME  = os.getenv("CHANNEL_NAME", "DJ darkMark")

ENABLE_YOUTUBE  = os.getenv("ENABLE_YOUTUBE",  "true").lower()  == "true"
ENABLE_FACEBOOK = os.getenv("ENABLE_FACEBOOK", "false").lower() == "true"

ENABLE_REMOTION       = os.getenv("ENABLE_REMOTION", "true").lower() == "true"
RUNNING_IN_GITHUB     = os.getenv("GITHUB_ACTIONS", "").lower() == "true"
FORCE_REMOTION_GITHUB = os.getenv("FORCE_REMOTION_GITHUB", "false").lower() == "true"

# Anti-trava: no GitHub Actions, Remotion/Chromium trava o job por padrão.
if RUNNING_IN_GITHUB and ENABLE_REMOTION and not FORCE_REMOTION_GITHUB:
    ENABLE_REMOTION = False

REMOTION_COMPOSITION_ID      = os.getenv("REMOTION_COMPOSITION_ID", "MyComposition")
REMOTION_ENTRY               = os.getenv("REMOTION_ENTRY", "index.ts")
REMOTION_CONCURRENCY         = int(os.getenv("REMOTION_CONCURRENCY", "1"))
REMOTION_SCALE               = os.getenv("REMOTION_SCALE", "0.6")
REMOTION_CRF                 = os.getenv("REMOTION_CRF", "28")
REMOTION_TIMEOUT_MS          = os.getenv("REMOTION_TIMEOUT_MS", "300000")
REMOTION_SUBPROCESS_TIMEOUT  = int(os.getenv("REMOTION_SUBPROCESS_TIMEOUT", os.getenv("REMOTION_TIMEOUT", "300")))


# ══════════════════════════════════════════════════════════════════════
# LOG
# ══════════════════════════════════════════════════════════════════════

def log(msg: str):
    print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] {msg}")


# ══════════════════════════════════════════════════════════════════════
# UTILITÁRIOS DE TEXTO
# ══════════════════════════════════════════════════════════════════════

def clean_title(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(r"\[[^\]]*\]|\{[^\}]*\}|\([^\)]*\)", "", name)
    name = re.sub(r"[_\-]+", " ", name)
    return re.sub(r"\s+", " ", name).strip().title()


def safe_filename(text: str) -> str:
    text = re.sub(r"[^\w\s\-]", "", text.lower())
    return re.sub(r"\s+", "_", text)[:60]


def canonical_track_key(filename: str) -> str:
    base = clean_title(filename).lower()
    return re.sub(r"\s+", " ", base).strip()


def track_key_from_drive_file(file_obj: dict) -> str:
    return str(file_obj.get("id") or canonical_track_key(file_obj.get("name", "")))


def human_delay():
    secs = random.randint(15, 45)
    log(f"Aguardando {secs}s antes do upload...")
    time.sleep(secs)


# ══════════════════════════════════════════════════════════════════════
# CORREÇÃO DE GÊNERO
# ══════════════════════════════════════════════════════════════════════

def normalize_detected_style(style: str, styles: list, filename: str) -> str:
    """
    Correção leve para não rotular tudo como phonk.
    A detecção principal continua no genre_detector.py.
    Aqui limpamos casos óbvios pelo nome do arquivo e gêneros secundários.
    """
    base = clean_title(filename).lower()
    secondary = [str(s).lower() for s in (styles or [])]

    electronic_words = [
        "electronic", "eletronic", "edm", "techno", "house", "rave", "synth",
        "synthwave", "dubstep", "future", "cyber", "laser", "club", "dance"
    ]
    trap_words = [
        "trap", "808", "drill", "street", "gang", "plug", "rage", "carti",
        "atl", "hood", "luxury", "flex"
    ]
    phonk_words = [
        "phonk", "drift", "cowbell", "memphis", "murder", "ghostface"
    ]

    if any(w in base for w in electronic_words):
        return "electronic"
    if any(w in base for w in trap_words):
        return "trap"
    if any(w in base for w in phonk_words):
        return "phonk"

    if style == "phonk":
        if "electronic" in secondary or "edm" in secondary or "dubstep" in secondary:
            return "electronic"
        if "trap" in secondary and "dark" not in secondary:
            return "trap"

    return style or "default"


# ══════════════════════════════════════════════════════════════════════
# HOOKS E TÍTULOS
# ══════════════════════════════════════════════════════════════════════

def _dhash(text: str) -> int:
    return int(hashlib.md5(text.encode()).hexdigest(), 16)


HOOKS_CURIOSIDADE = {
    "phonk": [
        "você não tava preparado pra isso",
        "enterraram essa aqui de propósito",
        "não existe no rádio por um motivo",
        "essa frequência não é pra todo mundo",
        "o underground não quer que você ache isso",
        "achei às 3 da manhã e não me arrependo",
        "essa batida não pede licença",
    ],
    "trap": [
        "ninguém tá falando disso ainda",
        "as ruas já sabem",
        "limpo demais pra continuar underground",
        "antes de chegar pra todo mundo",
        "esse produtor vai ser grande",
        "isso chega no topo sem pedir permissão",
        "cedo demais pra ignorar",
    ],
    "rock": [
        "esse riff não pede licença",
        "nos primeiros 3 segundos eu sabia",
        "a guitarra voltou e veio com raiva",
        "não devia ser tão boa em 2024",
        "essa banda merece estádios",
        "volume no máximo ou não vale",
        "rock não morreu ele só mudou de endereço",
    ],
    "metal": [
        "pesado demais pra maioria. você não é a maioria.",
        "o underground não quer que você ache isso",
        "sobreviva ao breakdown",
        "isso transcende gênero nesse ponto",
        "antigo e brutal e não consigo parar",
        "pesos assim são raros",
        "essa não é pra ouvir no fone no ônibus",
    ],
    "lofi": [
        "o barulho na minha cabeça parou com essa",
        "esqueci que tinha lista de tarefas",
        "essa segura sua mão sem pedir",
        "foco desbloqueado. não pergunte como.",
        "3 da manhã e finalmente quieto",
        "essa não é pra fundo de vídeo. é protagonista.",
        "estudei 4 horas sem perceber",
    ],
    "indie": [
        "disse o que eu não achava palavras",
        "soa como nostalgia que ainda não dói",
        "achei antes de todo mundo e sou protetor",
        "não consigo explicar por que bate. só bate.",
        "uma escuta e eu sabia que ia voltar",
        "honesta de um jeito que música raramente é",
        "essa artista merece muito mais gente",
    ],
    "electronic": [
        "o drop bateu antes do meu cérebro processar",
        "feito pra palcos que ainda não existem",
        "essa frequência pertence a estádios",
        "achei o ID que eu tava procurando",
        "produtor no topo em breve",
        "isso vai dominar festival",
        "cedo nesse artista e ficando",
    ],
    "dark": [
        "faz sentido só depois da meia-noite",
        "bonita de um jeito que não tem nome",
        "essa melodia não foi feita pra luz do dia",
        "tenta pular antes do fim. você não vai.",
        "beleza que assusta um pouco",
        "alguns sons foram enterrados por um motivo",
        "essa fica na cabeça por dias",
    ],
    "cinematic": [
        "pausei tudo. só ouvi.",
        "a construção é quase injusta",
        "te faz sentir protagonista",
        "mais pesado que qualquer trilha esse ano",
        "precisa de um filme digno dela",
        "essa compositor ninguém conhece ainda",
        "primeira nota e eu já era",
    ],
    "funk": [
        "não consegui ficar parado",
        "o groove tomou conta antes de eu concordar",
        "coisa mais limpa que achei essa semana",
        "tenta não se mexer. impossível.",
        "groove puro sem explicação necessária",
        "essa faz qualquer dia virar sexta",
        "baixo chegou antes de eu estar pronto",
    ],
    "default": [
        "o algoritmo finalmente acertou",
        "achei antes de explodir",
        "não consegue pular essa",
        "boa demais pra estar tão escondida",
        "uma escuta muda tudo",
        "isso vai crescer muito",
        "cedo nessa aqui",
    ],
}

HOOKS_EMOCIONAL = {
    "phonk": [
        "3 da manhã e não para de repetir",
        "lado sombrio do underground achado",
        "energia meia-noite chegou sem avisar",
        "obcecado em 10 segundos",
        "essa entrou em mim",
        "batida das 3h da manhã no carro",
        "perfeita pra dirigir no escuro",
    ],
    "trap": [
        "cedo nessa e não para",
        "luxo soa como isso aqui",
        "era isso que tava faltando na playlist",
        "o 808 que eu precisava sem saber",
        "isso elevou meu dia na hora",
        "qualidade que você sente antes de entender",
        "toca de novo automaticamente",
    ],
    "rock": [
        "coloca pra tocar já",
        "volume no máximo ou não vale",
        "achei às 1h da manhã e ainda tô aqui",
        "cada escuta mais pesada que a anterior",
        "sem skip possível nem se eu quisesse",
        "essa vai ficar comigo por semanas",
        "pele arrepiada do início ao fim",
    ],
    "metal": [
        "volume total ou não vale",
        "não é pra salas quietas",
        "as cabeças já sabem",
        "peso sonic que você sente no peito",
        "o breakdown bate físico",
        "essa não deixa você parado",
        "intensidade que você precisava",
    ],
    "lofi": [
        "companhia perfeita pra 3 da manhã",
        "desacelera tudo assim",
        "paz que eu não sabia que precisava",
        "melhor sessão de estudo da minha vida",
        "fica em loop a noite toda",
        "essa abraça sem pedir nada",
        "silêncio interno finalmente",
    ],
    "indie": [
        "merece salas maiores e mais tempo",
        "honesta de um jeito que música raramente é",
        "adicionei antes de terminar",
        "a ponte. é a resenha completa.",
        "cedo nesse artista e ficando",
        "essa vai envelhecer muito bem",
        "uma escuta e é permanente",
    ],
    "electronic": [
        "volume máximo sala escura e só isso",
        "não consigo ficar quieto no drop",
        "meu corpo moveu antes de eu decidir",
        "o futuro já soa assim",
        "cedo nesse produtor",
        "esse set ia destruir qualquer festival",
        "frequência que você sente antes de ouvir",
    ],
    "dark": [
        "3 dias na minha cabeça agora",
        "não é pra todo mundo e esse é o ponto",
        "escuridão com pulso é raro",
        "bonita de um jeito que incomoda um pouco",
        "achei escondida nas margens",
        "essa fica",
        "beleza que você não deveria conseguir explicar",
    ],
    "cinematic": [
        "olhos fechados. imediatamente.",
        "épica desde o primeiro segundo",
        "a cena que cortaram por ser boa demais",
        "uma escuta. sério.",
        "compositor que ninguém fala ainda",
        "essa merecia Oscar de trilha",
        "arrepio garantido",
    ],
    "funk": [
        "energia de fim de semana qualquer dia",
        "repeti duas vezes antes de acreditar",
        "seu corpo já sabe o que fazer",
        "isso parece genuinamente vivo",
        "baixo bateu antes de eu estar pronto",
        "sorriso involuntário garantido",
        "essa faz bem",
    ],
    "default": [
        "cedo nessa aqui",
        "sua playlist precisava disso",
        "achei de madrugada",
        "obcecado em 10 segundos",
        "confia em mim nessa",
        "isso vai crescer",
        "uma escuta e você volta",
    ],
}

HOOKS_IDENTIDADE = {
    "phonk": [
        "não é pra todo mundo • você encontrou de qualquer forma",
        "underground certificado",
        "música das sombras",
        "quem conhece, conhece",
        "phonk pra quem ouve no escuro",
        "certificado pesado",
        "os que sabem já sabem",
    ],
    "trap": [
        "underground certificado",
        "direto do underground",
        "pra quem reconhece qualidade",
        "certificado",
        "quem presta atenção já sabe",
        "essa vai chegar grande",
        "você foi cedo nessa",
    ],
    "rock": [
        "sem mainstream necessário",
        "pra quem ainda coloca no volume",
        "guitarra de verdade ainda existe",
        "o rock que não morreu",
        "certificado alto",
        "pra quem aguenta o tranco",
        "sem rádio necessário",
    ],
    "metal": [
        "pra quem aguenta",
        "underground aprovado",
        "certificado pesado",
        "pra quem precisa do peso",
        "certificado brutal",
        "você achou isso por algum motivo",
        "não é pra todo mundo",
    ],
    "lofi": [
        "pra quem estuda em silêncio",
        "certificado chill",
        "lofi pra quem sente de verdade",
        "os que ouvem às 3 da manhã",
        "certificado quieto",
        "pra quem precisa desacelerar",
        "fones de ouvido e paz",
    ],
    "indie": [
        "pra quem presta atenção",
        "os ouvintes cedo sabem",
        "joia escondida certificada",
        "underground antes de virar mainstream",
        "quem acha primeiro cuida",
        "certificado autêntico",
        "pra quem gosta de gente real",
    ],
    "electronic": [
        "ouvinte cedo certificado",
        "pra quem tá na pista antes da música",
        "certificado eletrônico",
        "rave certificado",
        "pra quem sente frequências",
        "você tá cedo nessa",
        "os que chegam antes do drop",
    ],
    "dark": [
        "não é pra luz do dia",
        "certificado sombrio",
        "os que ouvem sozinhos à noite",
        "underground e ficando lá",
        "pra quem entende",
        "beleza estranha certificada",
        "não é pra todo mundo",
    ],
    "cinematic": [
        "pra quem ouve de olhos fechados",
        "certificado épico",
        "energia de trilha sonora",
        "pra quem sente música como história",
        "cinematográfico certificado",
        "pra quem precisa da grandiosidade",
        "trilha sem filme",
    ],
    "funk": [
        "groove certificado",
        "pra quem não fica parado",
        "o povo que sabe dançar",
        "certificado groove",
        "pra quem sente antes de ouvir",
        "alegria certificada",
        "pra quem precisa de energia",
    ],
    "default": [
        "underground certificado",
        "ouvinte cedo",
        "pra quem presta atenção",
        "achado antes de explodir",
        "os bons sempre se escondem primeiro",
        "você foi cedo",
        "certificado",
    ],
}

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

GENRE_PREFIXES = {
    "phonk":      ["Phonk Music 😈", "🖤 Phonk Music", "Dark Phonk 🌑", "Phonk Vibes 😈", "💀 Phonk Music", "Phonk Mode 🖤", "Drift Phonk 😈"],
    "trap":       ["Trap Music 🔥", "💎 Trap Music", "Hard Trap 🔥", "Trap Banger 💎", "🔥 Trap Vibes", "Trap Mode 😤", "Street Trap 🔥"],
    "electronic": ["Electronic Music ⚡", "⚡ Electronic", "EDM Energy 🔥", "Electronic Drop ⚡", "🎛️ Electronic", "Synth Wave ⚡", "Electronic Banger ⚡"],
    "rock":       ["Rock Music 🎸", "🔥 Rock Music", "Hard Rock 🎸", "Rock Vibes ⚡", "🎸 Rock Energy", "Rock Banger 🔥", "Electric Rock 🎸"],
    "metal":      ["Metal Music 🤘", "🔥 Heavy Metal", "Metal Rage 🤘", "Heavy Metal 💀", "🤘 Metal Vibes", "Death Metal 🔥", "Metal Energy 🤘"],
    "indie":      ["Indie Music 🌙", "✨ Indie Vibes", "Indie Dream 🌙", "Indie Mood ✨", "🎧 Indie Music", "Indie Soul 🌙", "Bedroom Indie ✨"],
    "lofi":       ["Lo-Fi Music 🌙", "☁️ Lo-Fi Vibes", "Lo-Fi Chill 🎧", "Lofi Mood 🌙", "🎧 Lo-Fi Music", "Chill Lofi ☁️", "Late Night Lofi 🌙"],
    "cinematic":  ["Cinematic Music 🎬", "🎬 Epic Music", "Cinematic Drop 🎬", "Epic Cinematic ✨", "🌌 Cinematic", "Film Score Energy 🎬", "Cinematic Vibes 🌌"],
    "funk":       ["Funk Music 🎵", "🔥 Funk Vibes", "Groove Music 🎵", "Funk Energy ⚡", "🎵 Funk Mode", "Brazilian Funk 🔥", "Funk Banger 🎵"],
    "dark":       ["Dark Music 🌑", "🖤 Dark Vibes", "Dark Ambient 🌑", "Dark Energy 😈", "💀 Dark Music", "Dark Mode 🌑", "Shadow Music 🖤"],
    "pop":        ["Pop Music 💫", "✨ Pop Vibes", "Pop Banger 🔥", "Pop Energy 💫", "🎵 Pop Music", "Pop Hit ✨", "Pop Mood 💫"],
    "default":    ["Music 🎵", "🔥 New Music", "Music Vibes 🎧", "🎧 Underground", "New Music 🔥"],
}

TITLE_SEPARATORS = [" — ", " | ", " · ", " ✦ ", " » ", " ▸ "]

TITLE_TEMPLATES = [
    "{base} — {genre_prefix}{sep}{hook} | DJ darkMark",
    "{base} | {genre_prefix}{sep}{hook} — DJ darkMark",
    "{base} · DJ darkMark{sep}{hook}",
    "{base} {emoji} — {genre_prefix} | DJ darkMark",
    "{genre_prefix}{sep}{base} — DJ darkMark",
    "{base} — DJ darkMark{sep}{hook}",
    "{base} | DJ darkMark 🎧 {genre_prefix}",
    "{base} · {hook} — DJ darkMark {emoji}",
]


def build_title(base: str, style: str, short_num: int) -> str:
    emoji = GENRE_EMOJI.get(style, "🎵")
    prefix_pool = GENRE_PREFIXES.get(style, GENRE_PREFIXES["default"])
    prefix_seed = _dhash(f"{base}|prefix|{short_num}")
    genre_prefix = prefix_pool[prefix_seed % len(prefix_pool)]
    sep_seed = _dhash(f"{base}|sep|{short_num}")
    sep = TITLE_SEPARATORS[sep_seed % len(TITLE_SEPARATORS)]
    hook_layers = [
        HOOKS_CURIOSIDADE.get(style, HOOKS_CURIOSIDADE["default"]),
        HOOKS_EMOCIONAL.get(style, HOOKS_EMOCIONAL["default"]),
        HOOKS_IDENTIDADE.get(style, HOOKS_IDENTIDADE["default"]),
    ]
    layer = hook_layers[(short_num - 1) % len(hook_layers)]
    hook_seed = _dhash(f"{base}|hook|{short_num}")
    hook = layer[hook_seed % len(layer)]
    tmpl_seed = _dhash(f"{base}|tmpl|{short_num}")
    template = TITLE_TEMPLATES[tmpl_seed % len(TITLE_TEMPLATES)]
    title = template.format(
        base=base,
        genre_prefix=genre_prefix,
        sep=sep,
        hook=hook,
        emoji=emoji,
    )
    # Garante que o nome da música nunca suma
    if base.lower() not in title.lower():
        title = f"{base} — {title}"
    return title[:100]


STYLE_HASHTAGS = {
    "phonk":      "#phonk #darkphonk #phonkmusic #phonkbrasileiro #phonkvibes #djdarkmark #música",
    "trap":       "#trap #trapmusic #808s #trapbeats #undergroundbr #trapvibes #djdarkmark",
    "rock":       "#rock #rockmusic #guitarmusic #hardrock #rockbr #rockalternativo #djdarkmark",
    "metal":      "#metal #heavymetal #metalhead #metalcore #metalbr #músicapesada #djdarkmark",
    "lofi":       "#lofi #lofihiphop #músicaparaestudar #chillvibes #lofibeats #relaxar #djdarkmark",
    "indie":      "#indie #indiemusic #músicaalternativa #indiepop #indierock #djdarkmark",
    "electronic": "#electronic #edm #synthwave #eletrônica #techno #músicaeletrônica #djdarkmark",
    "cinematic":  "#cinematic #músicacinematográfica #epicmusic #trilhasonora #djdarkmark",
    "funk":       "#funk #funkmusic #groove #soul #djdarkmark #músicaboa",
    "dark":       "#dark #músicasombria #gothic #darkwave #atmospheric #djdarkmark",
    "pop":        "#pop #popmusic #djdarkmark #músicanova #hit",
    "default":    "#música #músicanova #underground #djdarkmark #shortsbrasil",
}

UNIVERSAL = "#shorts #youtubeshorts #viral #fyp #trending #musicshorts #djdarkmark #brasil"


def build_description(base: str, style: str, short_num: int) -> str:
    tags  = STYLE_HASHTAGS.get(style, STYLE_HASHTAGS["default"])
    emoji = GENRE_EMOJI.get(style, "🎵")
    idx   = (short_num - 1) % 5

    openers = [
        f"{emoji} {base}\n\nEssa aqui chegou no momento certo.\nDJ darkMark traz o melhor do underground todo dia — antes de chegar pra todo mundo.",
        f"{emoji} {base} — DJ darkMark\n\nAlgumas músicas merecem mais ouvidos. Achei pra você não precisar procurar.",
        f"{emoji} {base}\n\nO algoritmo enterrou essa. DJ darkMark desenterrou. Drops diários de música underground.",
        f"{emoji} {base} — DJ darkMark\n\nNem tudo que é bom viraliza. DJ darkMark garante que você ache de qualquer forma.",
        f"{emoji} {base}\n\nCedo nessa. DJ darkMark — música nova todo dia, essa que você não ia achar no rádio.",
    ]
    ctas = [
        "Inscreva-se no DJ darkMark pra não perder nenhum drop.",
        "Siga o DJ darkMark — música nova todo dia sem falta.",
        "Curte se essa merecia mais plays.",
        "Salva essa. Você vai querer ela de volta.",
        "Comenta se bateu do jeito certo.",
    ]
    spotify_lines = [
        f"🎧 Música completa:\n{SPOTIFY_LINK}",
        f"🎵 Ouça na íntegra:\n{SPOTIFY_LINK}",
        f"🔊 Versão completa:\n{SPOTIFY_LINK}",
        f"📻 No Spotify:\n{SPOTIFY_LINK}",
        f"🎧 Ouve aqui:\n{SPOTIFY_LINK}",
    ]
    return (
        f"{openers[idx]}\n\n"
        f"{ctas[idx]}\n\n"
        f"{spotify_lines[idx]}\n\n"
        f"📲 TikTok:\n{TIKTOK_LINK}\n\n"
        f"{tags}\n{UNIVERSAL}"
    )


# ══════════════════════════════════════════════════════════════════════
# STATE
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
    normalized_tracks = []
    seen_ids = set()
    for t in state["tracks"]:
        t.setdefault("done", 0)
        t.setdefault("is_new", False)
        t.setdefault("genre", None)
        drive_id = t.get("id")
        if drive_id:
            t["key"] = str(drive_id)
        else:
            t.setdefault("key", canonical_track_key(t["name"]))
        unique_id = t.get("id") or t.get("key")
        if unique_id in seen_ids:
            continue
        seen_ids.add(unique_id)
        normalized_tracks.append(t)
    state["tracks"] = normalized_tracks
    n = len(state["tracks"])
    state["alpha_index"] = state.get("alpha_index", 0) % n if n else 0
    return state


def save_state(state: dict):
    tmp = STATE_FILE.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    tmp.replace(STATE_FILE)


def sync_tracks(state: dict, files: list):
    drive_files = []
    for f in files:
        key = track_key_from_drive_file(f)
        name_key = canonical_track_key(f["name"])
        drive_files.append({
            "id": f["id"],
            "name": f["name"],
            "key": key,
            "name_key": name_key,
        })
    existing = {}
    for t in state["tracks"]:
        if t.get("id"):
            existing[str(t["id"])] = t
        else:
            existing[t.get("key", canonical_track_key(t["name"]))] = t
    new_tracks = []
    for f in drive_files:
        key = f["key"]
        if key not in existing:
            log(f"Nova faixa: {f['name']}")
            track = {
                "id": f["id"],
                "name": f["name"],
                "key": key,
                "name_key": f["name_key"],
                "done": 0,
                "is_new": True,
                "genre": None,
            }
            existing[key] = track
            new_tracks.append(track)
        else:
            track = existing[key]
            track["id"] = f["id"]
            track["name"] = f["name"]
            track["key"] = key
            track["name_key"] = f["name_key"]
            track.setdefault("done", 0)
            track.setdefault("is_new", False)
            track.setdefault("genre", None)
    ordered_tracks = []
    for f in drive_files:
        track = existing.get(f["key"])
        if track:
            ordered_tracks.append(track)
    state["tracks"] = ordered_tracks
    n = len(state["tracks"])
    if n == 0:
        state["alpha_index"] = 0
        return
    if new_tracks:
        state["alpha_index"] = 0
    else:
        state["alpha_index"] = state.get("alpha_index", 0) % n


def get_next_track(state: dict) -> dict | None:
    tracks = state["tracks"]
    if not tracks:
        return None
    new_tracks = [t for t in tracks if t.get("is_new") and t.get("done", 0) < SHORTS_PER_TRACK]
    if new_tracks:
        chosen = new_tracks[0]
        log(f"Prioridade: nova faixa — {chosen['name']}")
        chosen["is_new"] = False
        state["alpha_index"] = 0
        return chosen
    n = len(tracks)
    idx = state.get("alpha_index", 0) % n
    for i in range(n):
        pos = (idx + i) % n
        t = tracks[pos]
        if t.get("done", 0) < SHORTS_PER_TRACK:
            state["alpha_index"] = (pos + 1) % n
            return t
    log("Ciclo completo — resetando contadores e voltando ao topo da inbox.")
    for t in tracks:
        t["done"] = 0
        t["is_new"] = False
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
            log(f"Imagem AI gerada: {img}")
            return img
    except Exception as e:
        log(f"Imagem AI falhou, tentando fallback local: {e}")
    try:
        bg = get_random_background(style, filename)
        if bg and not str(bg).startswith("__AUTO"):
            log(f"Usando background local: {bg}")
            return bg
    except Exception as e:
        log(f"Background local falhou: {e}")
    fallback = "assets/backgrounds/default.jpg"
    if os.path.exists(fallback):
        log("Usando background padrão de fallback")
        return fallback
    raise FileNotFoundError("Nenhum background disponível.")


# ══════════════════════════════════════════════════════════════════════
# REMOTION (desativado por padrão no GitHub Actions)
# ══════════════════════════════════════════════════════════════════════

def run_process_kill_tree(cmd: list[str], cwd: str, timeout: int) -> subprocess.CompletedProcess:
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            time.sleep(2)
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGKILL)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        raise subprocess.TimeoutExpired(cmd, timeout, output=exc.output, stderr=exc.stderr)
    result = subprocess.CompletedProcess(cmd, proc.returncode, stdout, stderr)
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd, output=stdout, stderr=stderr)
    return result


def run_remotion_overlay(
    base_video_path: str,
    output_path: str,
    audio_data_path: str | None = None,
    logo_path: str | None = None,
    style: str = "default",
    song_name: str = "",
) -> str:
    if not ENABLE_REMOTION:
        log("Remotion desativado — usando vídeo base.")
        return base_video_path

    base_video_abs = Path(base_video_path).resolve()
    output_abs     = Path(output_path).resolve()

    if not base_video_abs.exists():
        log(f"ERRO: Vídeo base não encontrado: {base_video_abs}")
        return base_video_path

    remotion_dir = Path("remotion").resolve()
    if not remotion_dir.exists():
        log("Pasta remotion não encontrada — usando vídeo base.")
        return base_video_path

    public_dir = remotion_dir / "public"
    public_dir.mkdir(parents=True, exist_ok=True)

    # Copia vídeo base
    input_video_dest = public_dir / "input.mp4"
    shutil.copy(str(base_video_abs), str(input_video_dest))
    log(f"✅ Vídeo base copiado para Remotion: {input_video_dest}")

    # Copia audio_data.json
    audio_dest  = public_dir / "audio_data.json"
    copied_audio = False
    possible_audio_paths = []
    if audio_data_path:
        possible_audio_paths.append(Path(audio_data_path))
    possible_audio_paths.extend([
        Path("temp/audio_data.json"),
        Path("audio_data.json"),
        Path("remotion/public/audio_data.json"),
    ])
    for candidate in possible_audio_paths:
        try:
            if candidate and candidate.exists() and candidate.stat().st_size > 5:
                if candidate.resolve() != audio_dest.resolve():
                    shutil.copy(str(candidate), str(audio_dest))
                copied_audio = True
                log(f"✅ audio_data.json copiado: {candidate} -> {audio_dest}")
                break
        except Exception:
            pass
    if not copied_audio:
        audio_dest.write_text("[]", encoding="utf-8")
        log("audio_data.json não encontrado — fallback vazio.")

    # Copia logo
    copied_logo = False
    possible_logo_paths = [
        Path("assets/logo_darkmark.png"),
        Path("assets/logo.png"),
    ]
    if logo_path:
        possible_logo_paths.insert(0, Path(logo_path))
    for candidate in possible_logo_paths:
        try:
            if candidate and candidate.exists() and candidate.stat().st_size > 0:
                for dest_name in ("logo.png", "logo_darkmark.png"):
                    dest = public_dir / dest_name
                    if candidate.resolve() != dest.resolve():
                        shutil.copy(str(candidate), str(dest))
                copied_logo = True
                log(f"🔥 LOGO: {candidate}")
                break
        except Exception:
            pass
    if not copied_logo:
        log("Logo não encontrada — ícone não vai aparecer no Remotion.")

    # Valida entry
    entry_env      = str(REMOTION_ENTRY).replace("\\", "/").strip()
    entry_for_cli  = entry_env.replace("remotion/", "", 1) if entry_env.startswith("remotion/") else entry_env
    entry_path     = remotion_dir / entry_for_cli

    if not entry_path.exists():
        log(f"Entry do Remotion não encontrado: {entry_path} — usando vídeo base.")
        return base_video_path
    if not (remotion_dir / "package.json").exists():
        log("remotion/package.json não encontrado — usando vídeo base.")
        return base_video_path

    output_abs.parent.mkdir(parents=True, exist_ok=True)
    if output_abs.exists():
        try:
            output_abs.unlink()
        except Exception:
            pass

    cmd = [
        "npx", "remotion", "render",
        entry_for_cli,
        REMOTION_COMPOSITION_ID,
        str(output_abs),
        "--overwrite",
        "--concurrency", str(REMOTION_CONCURRENCY),
        "--timeout", REMOTION_TIMEOUT_MS,
        "--scale", REMOTION_SCALE,
        "--crf", REMOTION_CRF,
        "--gl=swiftshader",
    ]

    log(f"▶ Iniciando render Remotion (concurrency={REMOTION_CONCURRENCY}, gl=swiftshader)...")

    try:
        result = run_process_kill_tree(cmd, cwd=str(remotion_dir), timeout=REMOTION_SUBPROCESS_TIMEOUT)
        if result.stdout and result.stdout.strip():
            tail = result.stdout.strip().splitlines()[-20:]
            log("Remotion stdout (tail):\n" + "\n".join(tail))
        if result.stderr and result.stderr.strip():
            tail = result.stderr.strip().splitlines()[-10:]
            log("Remotion stderr (tail):\n" + "\n".join(tail))
        log("✅ Remotion finalizado com sucesso!")
    except FileNotFoundError:
        log("npx não encontrado — Node/Remotion não instalado. Usando vídeo base.")
        return base_video_path
    except subprocess.TimeoutExpired:
        log(f"❌ Remotion passou do limite ({REMOTION_SUBPROCESS_TIMEOUT}s) — usando vídeo base.")
        return base_video_path
    except subprocess.CalledProcessError as e:
        log(f"❌ Remotion falhou com código {e.returncode}. Usando vídeo base.")
        return base_video_path
    except Exception as e:
        log(f"❌ Remotion falhou: {e} — usando vídeo base.")
        return base_video_path

    if output_abs.exists() and output_abs.stat().st_size > 100_000:
        log(f"✅ Vídeo FINAL do Remotion pronto: {output_abs}")
        return str(output_abs)

    log("⚠️ Remotion não gerou arquivo válido — usando vídeo base.")
    return base_video_path


def choose_upload_video(base_video_path: str, remotion_video_path: str) -> str:
    remotion_abs = Path(remotion_video_path).resolve()
    if remotion_abs.exists() and remotion_abs.stat().st_size > 100_000:
        log(f"OK: usando vídeo FINAL do Remotion: {remotion_abs}")
        return str(remotion_abs)
    log("ATENÇÃO: Remotion não gerou arquivo válido — fallback para vídeo base.")
    return str(Path(base_video_path).resolve())


# ══════════════════════════════════════════════════════════════════════
# UPLOAD
# ══════════════════════════════════════════════════════════════════════

def publish(video_path: str, title: str, description: str) -> dict:
    results = {}
    if ENABLE_YOUTUBE:
        try:
            log("Fazendo upload pro YouTube...")
            res   = upload_video(video_path, title, description, [], "public")
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
            log("Fazendo upload pro Facebook Reels...")
            res   = upload_to_facebook(video_path, title, description)
            fb_id = res.get("id") or res.get("video_id", "?")
            log(f"  Facebook OK -> ID: {fb_id}")
            results["facebook"] = {"ok": True, "id": fb_id}
        except EnvironmentError as e:
            log(f"  Facebook não configurado: {e}")
            results["facebook"] = {"ok": False, "skipped": True}
        except Exception as e:
            log(f"  Facebook ERRO: {e}")
            results["facebook"] = {"ok": False, "error": str(e)}
    else:
        results["facebook"] = {"ok": False, "skipped": True}

    return results


# ══════════════════════════════════════════════════════════════════════
# CLEANUP
# ══════════════════════════════════════════════════════════════════════

def _cleanup_temp(*paths):
    for path in paths:
        try:
            if path and isinstance(path, str) and os.path.exists(path):
                if path.startswith("temp/") or "/temp/" in path:
                    os.remove(path)
                    log(f"Temp removido: {path}")
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════

def main():
    log("=" * 55)
    log(f"BOT INICIANDO — {CHANNEL_NAME} | YouTube Shorts + Facebook Reels")
    log(f"  YouTube  : {'ATIVO' if ENABLE_YOUTUBE  else 'DESATIVADO'}")
    log(f"  Facebook : {'ATIVO' if ENABLE_FACEBOOK else 'DESATIVADO'}")
    log(f"  Backup   : {'ATIVO' if DRIVE_BACKUP_FOLDER_ID else 'DESATIVADO'}")
    log(f"  Remotion : {'ATIVO' if ENABLE_REMOTION else 'DESATIVADO'}")
    if RUNNING_IN_GITHUB and not ENABLE_REMOTION:
        log("  Modo seguro GitHub: Remotion pulado para evitar travamento.")
    log(f"  Shorts/faixa: {SHORTS_PER_TRACK}")
    log("=" * 55)

    if not DRIVE_FOLDER_ID:
        raise ValueError("DRIVE_FOLDER_ID não configurado.")

    service = get_drive_service()

    log("Sincronizando assets (logo/efeitos) do Drive...")
    assets_result = download_assets_from_drive(service, DRIVE_FOLDER_ID)
    logo_path = assets_result.get("logo_path")

    if logo_path:
        log(f"Logo pronta: {logo_path}")
    else:
        log("Logo não encontrada — continuando sem logo.")

    if assets_result.get("effects"):
        log(f"Efeitos carregados: {list(assets_result['effects'].keys())}")
    else:
        log("Nenhum efeito encontrado — continuando sem efeitos.")

    inbox_id = find_folder_id(service, DRIVE_FOLDER_ID, "inbox")
    if not inbox_id:
        raise ValueError("Pasta 'inbox' não encontrada no Drive.")

    files = list_audio_files_in_folder(service, inbox_id)
    log(f"Arquivos de áudio encontrados no Drive: {len(files)}")

    state = load_state()
    sync_tracks(state, files)
    save_state(state)

    if not state["tracks"]:
        log("Nenhuma faixa pra processar. Encerrando.")
        return

    track = get_next_track(state)
    if not track:
        log("Nenhuma faixa disponível.")
        return

    name       = track["name"]
    short_num  = track.get("done", 0) + 1
    title_base = clean_title(name)

    log(f"Faixa   : {name}")
    log(f"Short   : {short_num}/{SHORTS_PER_TRACK}")

    os.makedirs("temp", exist_ok=True)
    audio_path = f"temp/{track['id']}_{safe_filename(name)}"

    bg             = None
    style          = "default"
    styles         = ["default"]
    thumbnail_path = None

    try:
        log("Baixando áudio do Drive...")
        download_drive_file(service, track["id"], audio_path)
        log("Download completo.")

        cached_genre = track.get("genre")
        if cached_genre and not RECHECK_GENRE_EACH_RUN:
            style = cached_genre
            styles = detect_genre_multi(audio_path)
            corrected_style = normalize_detected_style(style, styles, name)
            if corrected_style != style:
                log(f"Gênero corrigido por contexto: {style} -> {corrected_style}")
                style = corrected_style
                track["genre"] = style
                save_state(state)
            else:
                log(f"Gênero (cache): {style}")
        else:
            log("Detectando gênero...")
            raw_style = detect_genre(audio_path)
            styles = detect_genre_multi(audio_path)
            style = normalize_detected_style(raw_style, styles, name)
            if style != raw_style:
                log(f"Gênero ajustado: {raw_style} -> {style}")
            track["genre"] = style
            save_state(state)
            log(f"Gênero: {style} | Secundários: {', '.join(styles[1:] or ['nenhum'])}")

        date       = datetime.utcnow().strftime("%Y-%m-%d")
        output_dir = Path("output") / date / style
        output_dir.mkdir(parents=True, exist_ok=True)

        base_video_path = str(
            output_dir / f"{date}__{style}__{safe_filename(title_base)}__{track['id']}__s{short_num}__base.mp4"
        )
        final_video_path = str(
            output_dir / f"{date}__{style}__{safe_filename(title_base)}__{track['id']}__s{short_num}__remotion.mp4"
        )

        log(f"Gerando background (short {short_num})...")
        bg = resolve_background(style, name, short_num, styles)

        log("Gerando vídeo base com FFmpeg...")
        render_result = create_short(
            audio_path,
            bg,
            base_video_path,
            style,
            song_name=title_base,
        )

        if isinstance(render_result, dict):
            video_base_ready = render_result["output_path"]
            thumbnail_path   = render_result.get("thumbnail_path")
            audio_data_path  = render_result.get("audio_data_path") or render_result.get("audio_json_path")
        else:
            video_base_ready = render_result
            thumbnail_path   = None
            audio_data_path  = None

        # Resolve audio_data.json
        if not audio_data_path:
            for candidate in [
                Path("temp/audio_data.json"),
                Path("audio_data.json"),
                Path("remotion/public/audio_data.json"),
            ]:
                if candidate.exists() and candidate.stat().st_size > 5:
                    audio_data_path = str(candidate)
                    break

        if audio_data_path:
            log(f"Audio data para Remotion: {audio_data_path}")
        else:
            log("Audio data não encontrado — efeitos menos sincronizados.")

        log(f"Vídeo base pronto: {video_base_ready}")

        # Remotion overlay (desativado por padrão no GitHub)
        run_remotion_overlay(
            base_video_path=video_base_ready,
            output_path=final_video_path,
            audio_data_path=audio_data_path,
            logo_path=logo_path,
            style=style,
            song_name=title_base,
        )

        video_path = choose_upload_video(
            base_video_path=video_base_ready,
            remotion_video_path=final_video_path,
        )

        log(f"Vídeo que será enviado: {video_path}")

        title       = build_title(title_base, style, short_num)
        description = build_description(title_base, style, short_num)
        log(f"Título  : {title}")

        results = publish(video_path, title, description)

        if DRIVE_BACKUP_FOLDER_ID:
            try:
                log("Salvando backup no Drive...")
                upload_file_to_drive(service, DRIVE_BACKUP_FOLDER_ID, video_path)
                log("  Backup salvo.")
            except Exception as e:
                log(f"  Backup falhou (não crítico): {e}")

        any_ok      = any(r.get("ok") for r in results.values())
        all_skipped = all(r.get("skipped") for r in results.values())

        if not any_ok and not all_skipped:
            raise RuntimeError("Nenhuma plataforma recebeu o vídeo com sucesso.")

        track["done"] = short_num
        save_state(state)

        log("=" * 55)
        log(f"CONCLUÍDO — {name} (short {short_num}/{SHORTS_PER_TRACK})")
        log("=" * 55)

    finally:
        _cleanup_temp(audio_path, bg)


if __name__ == "__main__":
    main()
