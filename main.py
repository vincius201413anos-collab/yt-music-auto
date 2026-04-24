"""
main.py — Bot de automação YouTube Shorts v4.1
===============================================
CORREÇÃO v4.1:
- NÃO ignora mais músicas com nome duplicado.
- Cada música agora é tratada pelo ID único do Google Drive.
- Resolve o problema de músicas diferentes com nomes iguais/parecidos.
- Mantém o ciclo, estado, upload e títulos do bot.
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


def canonical_track_key(filename: str) -> str:
    """
    Mantido só por compatibilidade com estados antigos.
    A partir da v4.1, a chave principal é o ID do arquivo no Google Drive.
    """
    base = clean_title(filename).lower()
    base = re.sub(r"\s+", " ", base).strip()
    return base


def track_key_from_drive_file(file_obj: dict) -> str:
    """
    Chave REAL da música.

    Antes o bot usava o nome normalizado, então:
    Song.mp3 / Song (1).mp3 / Song.wav
    podiam virar a mesma key.

    Agora usa o ID único do Google Drive.
    Assim, músicas diferentes com nome duplicado serão processadas.
    """
    return str(file_obj.get("id") or canonical_track_key(file_obj.get("name", "")))


def human_delay():
    secs = random.randint(15, 45)
    log(f"Aguardando {secs}s antes do upload...")
    time.sleep(secs)


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

TITLE_TEMPLATES = [
    "DJ darkMark — {title} | {hook}",
    "{hook} — {title} | DJ darkMark",
    "DJ darkMark 🎧 {title} | {hook}",
    "{title} {emoji} {hook} — DJ darkMark",
    "DJ darkMark: {title} | {hook}",
    "{hook} {emoji} {title} — DJ darkMark",
    "DJ darkMark drops: {title} | {hook}",
    "{title} — {hook} | DJ darkMark {emoji}",
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
    "phonk":      "#phonk #darkphonk #phonkmusic #phonkbrasileiro #phonkvibes #djdarkmark #música",
    "trap":       "#trap #trapmusic #808s #trapbeats #undergroundbr #trapvibes #djdarkmark",
    "rock":       "#rock #rockmusic #guitarmusic #hardrock #rockbr #rockalternativo #djdarkmark",
    "metal":      "#metal #heavymetal #metalhead #metalcore #metalbr #músicapesada #djdarkmark",
    "lofi":       "#lofi #lofihiphop #músicaparaestudas #chillvibes #lofibeats #relaxar #djdarkmark",
    "indie":      "#indie #indiemusic #músicaalternativa #indiepop #indierock #djdarkmark",
    "electronic": "#electronic #edm #synthwave #eletrônica #techno #músicaeletrônica #djdarkmark",
    "cinematic":  "#cinematic #músicacinematográfica #epicmusic #trilhasonora #djdarkmark",
    "funk":       "#funk #funkmusic #groove #soul #djdarkmark #músicaboa",
    "dark":       "#dark #músicasombria #gothic #darkwave #atmospheric #djdarkmark",
    "pop":        "#pop #popmusic #djdarkmark #músicanova #hit",
    "default":    "#música #músicanova #underground #djdarkmark #shortsbrasil",
}

UNIVERSAL = "#shorts #youtubeshorts #viral #fyp #trending #musicshorts #djdarkmark #brasil"


def _dhash(text: str) -> int:
    return int(hashlib.md5(text.encode()).hexdigest(), 16)


def build_title(base: str, style: str, short_num: int) -> str:
    emoji = GENRE_EMOJI.get(style, "🎵")

    hook_layers = [
        HOOKS_CURIOSIDADE.get(style, HOOKS_CURIOSIDADE["default"]),
        HOOKS_EMOCIONAL.get(style, HOOKS_EMOCIONAL["default"]),
        HOOKS_IDENTIDADE.get(style, HOOKS_IDENTIDADE["default"]),
    ]

    layer = hook_layers[(short_num - 1) % len(hook_layers)]

    hook_seed = _dhash(f"{base}|hook|{short_num}")
    tmpl_seed = _dhash(f"{base}|tmpl|{short_num}")

    hook     = layer[hook_seed % len(layer)]
    template = TITLE_TEMPLATES[tmpl_seed % len(TITLE_TEMPLATES)]

    title = template.format(hook=hook, title=base, emoji=emoji)

    if "DJ darkMark" not in title and "dj darkmark" not in title.lower():
        title = f"DJ darkMark | {title}"

    return title[:100]


def build_description(base: str, style: str, short_num: int) -> str:
    tags  = STYLE_HASHTAGS.get(style, STYLE_HASHTAGS["default"])
    emoji = GENRE_EMOJI.get(style, "🎵")

    idx = (short_num - 1) % 5

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

        # Só remove duplicata se for exatamente o mesmo ID do Drive.
        # Não remove por nome.
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
    """
    v4.1:
    - Não remove duplicatas por nome.
    - Cada arquivo do Drive entra como faixa única pelo ID.
    - Se tiver 50 músicas com o mesmo nome, mas IDs diferentes, processa as 50.
    """
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


def main():
    log("=" * 55)
    log(f"BOT INICIANDO — {CHANNEL_NAME} | YouTube Shorts + Facebook Reels")
    log(f"  YouTube  : {'ATIVO' if ENABLE_YOUTUBE  else 'DESATIVADO'}")
    log(f"  Facebook : {'ATIVO' if ENABLE_FACEBOOK else 'DESATIVADO'}")
    log(f"  Backup   : {'ATIVO' if DRIVE_BACKUP_FOLDER_ID else 'DESATIVADO'}")
    log(f"  Shorts/faixa: {SHORTS_PER_TRACK}")
    log("=" * 55)

    if not DRIVE_FOLDER_ID:
        raise ValueError("DRIVE_FOLDER_ID não configurado.")

    service  = get_drive_service()
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

    name        = track["name"]
    short_num   = track.get("done", 0) + 1
    title_base  = clean_title(name)

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
        if cached_genre:
            style  = cached_genre
            styles = detect_genre_multi(audio_path)
            log(f"Gênero (cache): {style}")
        else:
            log("Detectando gênero...")
            style  = detect_genre(audio_path)
            styles = detect_genre_multi(audio_path)
            track["genre"] = style
            save_state(state)
            log(f"Gênero: {style} | Secundários: {', '.join(styles[1:] or ['nenhum'])}")

        date       = datetime.utcnow().strftime("%Y-%m-%d")
        output_dir = Path("output") / date / style
        output_dir.mkdir(parents=True, exist_ok=True)
        planned_video_path = str(
            output_dir / f"{date}__{style}__{safe_filename(title_base)}__{track['id']}__s{short_num}.mp4"
        )

        log(f"Gerando background (short {short_num})...")
        bg = resolve_background(style, name, short_num, styles)

        log("Gerando vídeo...")
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

        log(f"Vídeo pronto: {video_path}")

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
        for path in [audio_path, bg]:
            try:
                if path and isinstance(path, str) and os.path.exists(path):
                    if path.startswith("temp/"):
                        os.remove(path)
                        log(f"Temp removido: {path}")
            except Exception:
                pass


if __name__ == "__main__":
    main()
