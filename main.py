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

# ── 1 short por música por execução ──────────────────────────────────
SHORTS_PER_TRACK = int(os.getenv("SHORTS_PER_TRACK", "1"))

DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")
DRIVE_BACKUP_FOLDER_ID = os.getenv("DRIVE_BACKUP_FOLDER_ID", "").strip()

SPOTIFY_LINK = "https://open.spotify.com/intl-pt/artist/1zyM1Pyi4YLAQgrSVRAYEy"
TIKTOK_LINK = "https://www.tiktok.com/@darkmrkedit"

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
    log(f"Aguardando {secs}s antes do proximo upload...")
    time.sleep(secs)


# ══════════════════════════════════════════════════════════════════════
# SISTEMA DE TÍTULOS V2 — Mais impactantes, variados, anti-shadowban
# ══════════════════════════════════════════════════════════════════════

TITLE_BANK = {
    "phonk": [
        # Grupo 1 — Discovery hook
        [
            "{base} — você achou antes de explodir 🌑",
            "essa é diferente. {base} 🖤",
            "{base} | o underground te encontrou 📲",
            "salva isso. {base} 🌙",
            "{base} — alguns sons não pertencem à luz do dia 🕒",
            "o algoritmo finalmente acertou 🌑 | {base}",
        ],
        # Grupo 2 — Emotional reaction
        [
            "não estava pronto pra {base} 😳",
            "{base} — repeti mais vezes do que admito 🔁",
            "coloquei às 3am e perdi a noção do tempo | {base} 🌙",
            "{base} | primeiros 10 segundos. acabou. 🎧",
            "esse me pegou | {base} 🖤",
            "{base} — não esperava sentir isso 😮",
        ],
        # Grupo 3 — Challenge
        [
            "tenta não sentir {base} 😈",
            "{base} | me diz que você não vai voltar nisso 🔁",
            "uma vez e você entende | {base} 🌑",
            "{base} — primeira escuta muda algo 😈",
            "escuta uma vez. só uma. | {base} 🎧",
            "{base} | se você entende, você entende 🖤",
        ],
        # Grupo 4 — Vibe/Mood
        [
            "{base} — estacionamento vazio às 3am 🌑",
            "o som de dirigir sem destino à meia-noite | {base} 🚗",
            "{base} | energia escura, sem explicação necessária 🖤",
            "é assim que foco soa | {base} 😤",
            "{base} — frio, calculado, diferente 🌙",
            "música pra dirigir à noite | {base} 🌑",
        ],
        # Grupo 5 — Minimal
        [
            "{base} 🌑",
            "{base} | fala por si mesmo 🖤",
            "só ouve. {base} 🎧",
            "{base} — sem palavras 🌙",
            "🖤 {base}",
            "{base} | você já sabe 😈",
        ],
    ],
    "trap": [
        [
            "{base} — antes de chegar em todo lugar 📈",
            "as ruas sabem | {base} 🏙️",
            "{base} | achei isso e não consegui parar 💎",
            "ninguém tá falando disso ainda | {base} 🤫",
            "{base} — essa é diferente 👑",
            "underground certificado | {base} 🔒",
        ],
        [
            "o bass de {base} bateu diferente 🔊",
            "{base} | minha caixa não tava pronta 💀",
            "pulei tudo depois de ouvir {base} 🔁",
            "{base} — o drop veio cedo e eu não estava pronto 😮",
            "esse 808 | {base} 🥁",
            "{base} | repeti o drop seis vezes 🔊",
        ],
        [
            "coloca {base} e vê quem para pra olhar 👀",
            "{base} | me fala que não sentiu 😤",
            "acha um motivo pra tirar isso. espero | {base} 🕐",
            "{base} — uma vez e você entende 💎",
            "tenta não balançar com {base} 🔊",
            "{base} | se você pulou tá perdendo 👑",
        ],
        [
            "{base} — é assim que confiança soa 👑",
            "áudio de luxo | {base} 💸",
            "{base} | nem todo mundo tem gosto. você tem. 🖤",
            "limpo, caro, diferente | {base} 💎",
            "{base} — o padrão acabou de mudar 📈",
            "vibe de cobertura | {base} 🏙️",
        ],
        [
            "{base} 💎",
            "🏙️ {base}",
            "{base} | fala por si mesmo 👑",
            "só coloca | {base} 🔊",
            "{base} — confia 💸",
            "👑 {base}",
        ],
    ],
    "rock": [
        [
            "{base} — esse riff não pede licença 🎸",
            "rock ainda tem muito a dizer | {base} ⚡",
            "{base} | achei à 1am, sem arrependimento 🌙",
            "essa banda deveria estar no topo | {base} 🎪",
            "{base} — a volta da guitarra de verdade 🎸",
            "o que você tava procurando | {base} ⚡",
        ],
        [
            "o primeiro riff de {base} me parou 🎸",
            "{base} | fiz headbang sozinho no carro 🤘",
            "não devia ser tão bom | {base} 😤",
            "{base} — a ponte me pegou 🎸",
            "parei tudo pra achar isso | {base} 🔍",
            "{base} | o solo bateu diferente ⚡",
        ],
        [
            "não mexer durante o solo. impossível | {base} 🎸",
            "{base} | me fala que não merece mais alto 📢",
            "escuta sem air guitar. aposta | {base} 🤘",
            "{base} — acha um skip. não vai achar ⏭️",
            "volume máximo. agora. | {base} 🔊",
            "{base} | tenta não sentir essa ⚡",
        ],
        [
            "{base} — feita pra palcos que ainda não existem ⚡",
            "energia pura | {base} 🔥",
            "{base} | é assim que real soa 🎸",
            "a energia disso | {base} ⚡",
            "{base} — cru e real 🎸",
            "isso é rock | {base} 🤘",
        ],
        [
            "{base} 🎸",
            "⚡ {base}",
            "{base} | toca alto 🔊",
            "🤘 {base}",
            "{base} — volume máximo ⚡",
            "só aumenta | {base} 🎸",
        ],
    ],
    "metal": [
        [
            "{base} — o underground não quer que você ache isso 🔒",
            "pesado demais pra maioria. não pra você | {base} 🌑",
            "{base} | isso existe e pouca gente sabe 🤘",
            "os heads sabem | {base} ⚠️",
            "{base} — enterrado no algoritmo por um motivo 📉",
            "essa banda é boa demais pra tanto silêncio | {base} 🌑",
        ],
        [
            "o breakdown de {base} bateu fisicamente 💀",
            "{base} | meus vizinhos se mudaram por causa disso 😈",
            "não consegui processar na primeira vez | {base} 🔁",
            "{base} — precisei parar depois do drop 🤯",
            "isso mudou o que eu achava possível | {base} ⚡",
            "{base} | não estava pronto 💀",
        ],
        [
            "volume máximo ou nem toca | {base} 🔊",
            "{base} | acha algo mais pesado. te desafio ⚔️",
            "sobrevive ao breakdown | {base} 🤘",
            "{base} — comprometimento total, dano total 🔊",
            "não desvia o olhar | {base} 😈",
            "{base} | não é pra todo mundo. talvez pra você ⚠️",
        ],
        [
            "{base} — isso não é música. é uma força. ⚠️",
            "peso puro | {base} 🌑",
            "{base} | a pesadez que você pediu ao universo 🔥",
            "não é pra ambiente quieto | {base} 🔊",
            "{base} — transcende gênero ⚡",
            "antigo e brutal | {base} 🌑",
        ],
        [
            "{base} ⚠️",
            "🌑 {base}",
            "{base} | se você sabe, você sabe 🤘",
            "só experimenta | {base} ⚔️",
            "{base} — sem palavras 💀",
            "⚡ {base}",
        ],
    ],
    "lofi": [
        [
            "{base} — algumas músicas chegam na hora certa ⏱️",
            "essa joia lofi merecia mais | {base} 💎",
            "{base} | o algoritmo finalmente fez algo certo 🙏",
            "a que toca no café | {base} ☕",
            "{base} — mereceu mais do que recebeu 🕊️",
            "achei tarde. melhor do que nunca | {base} 🌙",
        ],
        [
            "parei tudo pra existir dentro de {base} 😮",
            "{base} | primeiros 10 segundos e desacelerou tudo 🌿",
            "essa fez o barulho na minha cabeça parar | {base} 🧠",
            "{base} — sem querer fiquei acordado com isso ligado 🌙",
            "esqueci que tinha lista de tarefas | {base} 📋",
            "{base} | essa me tirou do buraco 🎧",
        ],
        [
            "tenta escutar sem se perder | {base} 💭",
            "{base} | um loop e me diz que não tá mais calmo 🧘",
            "acha companhia melhor pra estudar. espero | {base} 📚",
            "{base} — tenta não sentir nada. impossível 🎧",
            "escuta uma vez e não salva | {base} 🔁",
            "{base} | só coloca e respira ☁️",
        ],
        [
            "{base} — é assim que as 3am soam quando tá okay 🌙",
            "a trilha dos seus pensamentos não lidos | {base} 📖",
            "{base} | paz que você não sabia que precisava ☁️",
            "o som de um suspiro depois de um dia longo | {base} 🌙",
            "{base} — quieto e real 🌿",
            "isso segura sua mão sem pedir | {base} 🎧",
        ],
        [
            "{base} 🌙",
            "☁️ {base}",
            "{base} | sentimentos de madrugada 🎧",
            "só {base} 🌿",
            "{base} — estação aconchego 🌙",
            "🎧 {base}",
        ],
    ],
    "indie": [
        [
            "{base} — antes de todo mundo descobrir 🔮",
            "alguns artistas merecem mais salas | {base} 🎪",
            "{base} | ouvi uma vez e contei pra todo mundo 📣",
            "a internet acha tudo eventualmente | {base} 🌐",
            "{base} — escondido porque é real 💎",
            "chegando cedo nessa | {base} 📌",
        ],
        [
            "primeiro verso de {base} e parei de rolar 🛑",
            "{base} | repeti a ponte seis vezes 🔁",
            "essa disse o que eu não achava palavras | {base} 💬",
            "{base} — adicionei antes de terminar ⚡",
            "não conheço essa banda ainda mas vou conhecer | {base} 🔍",
            "{base} | não esperava sentir algo 😮",
        ],
        [
            "tenta explicar por que {base} pesa assim 🤔",
            "{base} | finge que não ficou com você 🎶",
            "não adiciona isso numa playlist. aposta | {base} 📌",
            "{base} — a ponte. só isso. esse é o post 😤",
            "acha o momento que parou de ouvir | {base} 🎧",
            "{base} | uma escuta. só uma 🌅",
        ],
        [
            "{base} — soa como como nostalgia se sente 🌅",
            "música que te faz saudade de algo sem nome | {base} 🌙",
            "{base} | o sentimento, não só a música 🌿",
            "seu coração precisava disso | {base} 💙",
            "{base} — escrita pra quem sentiu antes das palavras 📝",
            "esse é o sentimento | {base} 🌅",
        ],
        [
            "{base} 🌅",
            "🌿 {base}",
            "{base} | só sente 💙",
            "🎶 {base}",
            "{base} — ainda pensando 🌙",
            "só {base} 🌅",
        ],
    ],
    "electronic": [
        [
            "{base} — antes de encher todo palco de festival 🌍",
            "produtores tão anotando | {base} 📝",
            "{base} | o ID que você tava procurando 🔍",
            "underground até não ser. olha só | {base} 👀",
            "{base} — esse produtor vai estar em todo lugar 🚀",
            "chegando cedo em {base} | lembra disso 📌",
        ],
        [
            "o drop de {base} chegou quando eu não tava pronto 💀",
            "{base} | fiquei andando pelo apartamento à meia-noite 🌙",
            "ouvi num set uma vez e fiquei semanas procurando | {base} 🔍",
            "{base} — é por isso que não durmo antes de festival 🎉",
            "meu corpo se moveu antes do meu cérebro | {base} 🕺",
            "{base} | o drop bateu diferente 🔊",
        ],
        [
            "fica parado no drop. impossível | {base} 🕺",
            "{base} | acha um drop mais pesado. vai lá 🔎",
            "volume máximo, quarto escuro | {base} 🔊",
            "{base} — não sente o bass no peito. impossível 🫀",
            "escuta sem querer estar numa multidão | {base} 🏟️",
            "{base} | tenta não mexer. impossível 🕺",
        ],
        [
            "{base} — esse drop existe em outra dimensão 🌀",
            "feito pra caixas que conseguem aguentar | {base} 🔊",
            "{base} | energia máxima, sem explicação necessária ⚡",
            "algumas frequências foram feitas pra estádios | {base} 🏟️",
            "{base} — o futuro já soa assim 🚀",
            "é assim que o drop se sente | {base} ⚡",
        ],
        [
            "{base} ⚡",
            "🌀 {base}",
            "{base} | o drop 🔊",
            "🚀 {base}",
            "{base} — só coloca ⚡",
            "aumenta | {base} 🔊",
        ],
    ],
    "dark": [
        [
            "{base} — isso existia antes de você achar 🕯️",
            "nem tudo que é bom fica famoso | {base} 🌑",
            "{base} | os quietos chegam mais fundo 🖤",
            "escondido pra quem estava pronto | {base} 🌌",
            "{base} — algumas músicas vivem nas margens 🔍",
            "essa te achou por um motivo | {base} 🕯️",
        ],
        [
            "{base} me parou completamente 🕯️",
            "não sei o que isso me fez sentir mas foi real | {base} 😶",
            "{base} — ficou na minha cabeça por três dias 💭",
            "ouvi quatro vezes tentando entender | {base} 🔁",
            "{base} | isso reconfigura algo 🧠",
            "só fiquei um tempo com {base} 🌑",
        ],
        [
            "ouve sozinho à noite | {base} 🌑",
            "{base} | explica o sentimento. impossível 🖤",
            "tenta pular antes do fim. não vai | {base} 🎧",
            "{base} — acha a palavra pra o que isso te faz sentir 📖",
            "descreve pra alguém. olha eles não entenderem | {base} 🌌",
            "{base} | só fica nisso 🕯️",
        ],
        [
            "{base} — algumas músicas só fazem sentido depois da meia-noite 🌑",
            "bonito de um jeito que dói | {base} 🖤",
            "{base} | essa melodia não foi feita pra luz do dia 🕯️",
            "escuridão com pulso | {base} 🌑",
            "{base} — o som de algo vasto e quieto 🌌",
            "não é pra todo mundo | {base} 🖤",
        ],
        [
            "{base} 🖤",
            "🌑 {base}",
            "{base} | meia-noite 🕯️",
            "só {base} 🌌",
            "{base} — você vai entender 🖤",
            "🕯️ {base}",
        ],
    ],
    "cinematic": [
        [
            "{base} — essa trilha merece um filme à altura 🎬",
            "música cinematográfica que não precisa de tela | {base} 🎥",
            "{base} | achei às 2am e não consegui parar 🌙",
            "o compositor que ninguém fala ainda | {base} 🎼",
            "{base} — existia em silêncio. agora você sabe 🌅",
            "chegando cedo em {base} | olha o que vai acontecer 📌",
        ],
        [
            "parei de me mover e deixei {base} tocar 🎬",
            "{base} | o build é quase injusto 🌊",
            "bateu mais forte que qualquer filme esse ano | {base} 🎥",
            "{base} — precisei de um momento depois que terminou 😶",
            "isso desbloqueou algo | {base} 🌅",
            "{base} | não estava pronto pro clímax 🎻",
        ],
        [
            "ouve sem fechar os olhos. impossível | {base} 🎬",
            "{base} | tenta não imaginar uma cena inteira 🎥",
            "não sente nada no clímax. impossível | {base} 🌊",
            "{base} — não se perde nisso. aviso 🌌",
            "me diz que isso não é cinematográfico | {base} 🎻",
            "{base} | uma escuta. sério 🎬",
        ],
        [
            "{base} — soa como a cena que cortaram por boa demais 🎬",
            "feita pra um filme que ainda não foi feito | {base} 🎥",
            "{base} | te faz sentir o protagonista 🌅",
            "a trilha que sua vida não sabia que precisava | {base} 🎻",
            "{base} — expande qualquer ambiente que você estiver 🌌",
            "épico desde o primeiro segundo | {base} 🎬",
        ],
        [
            "{base} 🎬",
            "🎻 {base}",
            "{base} | só experimenta 🌌",
            "🌅 {base}",
            "{base} — sem palavras 🎥",
            "só {base} 🎬",
        ],
    ],
    "funk": [
        [
            "{base} — funk brasileiro antes do mundo descobrir 🇧🇷",
            "esse groove estava escondido | {base} 🕵️",
            "{base} | o achado que muda sua playlist 📌",
            "som underground, energia de mainstream | {base} 🚀",
            "{base} — bom demais pra tanto silêncio 🎼",
            "chegando cedo em {base} | confia 📌",
        ],
        [
            "eu tava sentado. palavra-chave: tava | {base} 🕺",
            "{base} | ninguém me avisou do baixo 🎸",
            "o groove chegou e perdi a noção do tempo | {base} 🕐",
            "{base} — repeti duas vezes antes de acreditar 🔁",
            "isso quebrou meu foco imediatamente | {base} 😤",
            "{base} | não esperava isso 🕺",
        ],
        [
            "fica parado no baixo. impossível | {base} 🕺",
            "{base} | não balança a cabeça. impossível 🎵",
            "uma vez sem dançar. aposta | {base} 💃",
            "{base} — acha um groove mais limpo. espero 🎸",
            "tenta escutar sem sorrir | {base} 😁",
            "{base} | só tenta 🕺",
        ],
        [
            "{base} — seu corpo já sabe o que fazer 🕺",
            "groove que toma conta | {base} 🎵",
            "{base} | é assim que fim de semana soa 🔥",
            "energia pura, sem explicação | {base} 🇧🇷",
            "{base} — do tipo que move móveis 🕺",
            "isso se sente vivo | {base} 🔥",
        ],
        [
            "{base} 🕺",
            "🔥 {base}",
            "{base} | só se move 🎵",
            "💃 {base}",
            "{base} — você vai entender 🕺",
            "🇧🇷 {base}",
        ],
    ],
    "pop": [
        [
            "{base} — antes de estar em toda playlist 📈",
            "pop ainda surpreende | {base} 🎵",
            "{base} | chegando cedo nessa. lembra 📌",
            "a música que vai ser inescapável | {base} 🌍",
            "{base} — esse artista vai ser famoso 🚀",
            "peguei antes de explodir | {base} 📌",
        ],
        [
            "não esperava {base} pesar tanto 😮",
            "{base} | o refrão chegou e voltei pro começo 🔁",
            "fiquei cantando {base} horas depois 🎵",
            "{base} — pulei uma vez. voltei imediatamente 🔁",
            "é isso que chiclete significa | {base} 🎧",
            "{base} | viciante desde o segundo um 🔁",
        ],
        [
            "tenta tirar {base} da cabeça 🧠",
            "{base} | pula antes do hook. impossível ⏭️",
            "acha refrão mais limpo esse ano | {base} 🔎",
            "{base} — não fica cantando o dia todo. impossível 🎵",
            "escuta uma vez e não adiciona | {base} 📌",
            "{base} | tenta esquecer 🧠",
        ],
        [
            "{base} — viciante antes do refrão até cair 🔁",
            "feita pra ficar na cabeça | {base} 🧠",
            "{base} | limpa e impossível de pular 💫",
            "o hook que estraga tudo que vem depois | {base} 🎵",
            "{base} — é por isso que pop ainda importa 🎵",
            "pop genuinamente bom | {base} 💫",
        ],
        [
            "{base} 🎵",
            "💫 {base}",
            "{base} | confia 🔁",
            "🎵 {base}",
            "{base} — você vai ver 📈",
            "só {base} 💫",
        ],
    ],
    "default": [
        [
            "{base} — achado antes de explodir 🔮",
            "chegando cedo nessa | {base} 📌",
            "{base} | algumas coisas chegam antes da hora 🌱",
            "o achado que você vai contar pra todo mundo | {base} 📣",
            "{base} — essa cresce 🌱",
            "você achou isso. isso significa algo | {base} 📌",
        ],
        [
            "primeiros 15 segundos de {base} e acabou 🎧",
            "{base} | não consegui pular nem tentando 🔁",
            "bateu como se fosse feita pra mim | {base} 🎵",
            "{base} — parei pra descobrir quem fez 🔍",
            "mudou a energia do meu dia inteiro | {base} 🔁",
            "{base} | não esperava isso 🎧",
        ],
        [
            "uma vez e finge que não vai voltar | {base} 🔁",
            "{base} | acha um motivo pra tirar da playlist 🔎",
            "pula isso. vê o que acontece | {base} ⏭️",
            "{base} — escuta sem melhorar o humor. impossível 😌",
            "argumenta que isso não pertence nos favoritos | {base} 💎",
            "{base} | só tenta pular 🔁",
        ],
        [
            "{base} — os reais reconhecem qualidade na hora 💎",
            "essa merece seu melhor fone | {base} 🎧",
            "{base} | a adição de playlist que você não planejou 🎵",
            "alguns sons funcionam na hora | {base} 🎧",
            "{base} — não precisa de apresentação 🎵",
            "magnético desde o começo | {base} 💎",
        ],
        [
            "{base} 🎵",
            "🎧 {base}",
            "{base} | só ouve 💎",
            "🎶 {base}",
            "{base} — confia 🎵",
            "só {base} 🎧",
        ],
    ],
}

STYLE_HASHTAGS = {
    "phonk":      "#phonk #darkphonk #phonkmusic #phonkdrift #phonkvibes #phonkedit #phonkcar",
    "trap":       "#trap #trapmusic #808s #trapbeats #undergroundhiphop #trapvibes #newmusic",
    "rock":       "#rock #rockmusic #guitarmusic #hardrock #alternative #alternativerock #newrock",
    "metal":      "#metal #heavymetal #metalhead #metalcore #extrememetal #newmetal #heavymusic",
    "lofi":       "#lofi #lofihiphop #studymusic #chillvibes #lofibeats #relaxingmusic #lofichill",
    "indie":      "#indie #indiemusic #alternativemusic #indiepop #indierock #emotionalmusic #indievibes",
    "electronic": "#electronic #edm #synthwave #electronicmusic #techno #dancemusic #festivalmusic",
    "cinematic":  "#cinematic #cinematicmusic #epicmusic #orchestral #filmmusic #epicorchestral #dramatic",
    "funk":       "#funk #funkmusic #groove #brazilianmusic #soulmusic #funkychill #groovemusic",
    "dark":       "#dark #darkmusic #gothic #darkambient #darkwave #atmospheric #hauntingmusic",
    "pop":        "#pop #popmusic #popvibes #newmusic #chart #top40 #hitmusic",
    "default":    "#music #newmusic #viralmusic #underground #musiclover #musicdiscovery #hiddengems",
}

UNIVERSAL = "#shorts #youtubeshorts #viral #fyp #trending #musicshorts #shortsvideo"


def build_title(base: str, style: str, short_num: int) -> str:
    bank = TITLE_BANK.get(style, TITLE_BANK["default"])
    group_idx = (short_num - 1) % len(bank)
    group = bank[group_idx]

    import hashlib
    seed = int(hashlib.md5(f"{base}|{short_num}|v2".encode()).hexdigest(), 16) % len(group)
    template = group[seed]
    title = template.format(base=base)
    return title[:100]


def build_description(base: str, style: str, short_num: int) -> str:
    tags = STYLE_HASHTAGS.get(style, STYLE_HASHTAGS["default"])
    ctas = [
        "Inscreva-se se quiser mais achados como esse.",
        "Comenta se essa chegou do jeito certo.",
        "Salva pra depois — você vai querer de volta.",
        "Segue pra upload diário de música underground.",
        "Like se essa merecia mais do que recebeu.",
    ]
    cta = ctas[(short_num - 1) % len(ctas)]
    spotify_lines = [
        f"🎧 Track completa no Spotify:\n{SPOTIFY_LINK}",
        f"🎵 Ouve em todo lugar:\n{SPOTIFY_LINK}",
        f"🎧 Stream aqui:\n{SPOTIFY_LINK}",
        f"🔊 Versão completa no Spotify:\n{SPOTIFY_LINK}",
        f"📻 No Spotify agora:\n{SPOTIFY_LINK}",
    ]
    spotify_line = spotify_lines[(short_num - 1) % len(spotify_lines)]
    return (
        f"🎵 {base}\n\n"
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
            log(f"Nova musica: {f['name']}")
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

    # Prioridade: músicas novas com 0 shorts
    new_tracks = [t for t in tracks if t.get("is_new") and t.get("done", 0) == 0]
    if new_tracks:
        chosen = new_tracks[0]
        log(f"Prioridade para nova musica: {chosen['name']}")
        chosen["is_new"] = False
        return chosen

    n = len(tracks)
    idx = state.get("alpha_index", 0) % n

    for i in range(n):
        t = tracks[(idx + i) % n]
        if t.get("done", 0) < SHORTS_PER_TRACK:
            state["alpha_index"] = (idx + i + 1) % n
            return t

    log("Rodada completa — resetando todos os contadores.")
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
            log(f"Imagem IA gerada com sucesso: {img}")
            return img
    except Exception as e:
        log(f"IA falhou, tentando fallback local: {e}")

    try:
        bg = get_random_background(style, filename)
        if bg and not str(bg).startswith("__AUTO"):
            log(f"Usando background local: {bg}")
            return bg
    except Exception as e:
        log(f"Background local falhou: {e}")

    fallback = "assets/backgrounds/default.jpg"
    if os.path.exists(fallback):
        log("Usando background fallback padrao")
        return fallback

    raise FileNotFoundError("Nenhum background disponivel (IA, local e fallback falharam).")


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
    log("=" * 55)
    log("BOT INICIANDO — YouTube Shorts + Facebook Reels")
    log(f"  YouTube  : {'ATIVO' if ENABLE_YOUTUBE else 'DESABILITADO'}")
    log(f"  Facebook : {'ATIVO' if ENABLE_FACEBOOK else 'DESABILITADO'}")
    log(f"  Backup   : {'ATIVO' if DRIVE_BACKUP_FOLDER_ID else 'DESABILITADO'}")
    log(f"  Shorts/track: {SHORTS_PER_TRACK}")
    log("=" * 55)

    if not DRIVE_FOLDER_ID:
        raise ValueError("DRIVE_FOLDER_ID nao configurado nas variaveis de ambiente.")

    service = get_drive_service()
    inbox_id = find_folder_id(service, DRIVE_FOLDER_ID, "inbox")
    if not inbox_id:
        raise ValueError("Pasta 'inbox' nao encontrada no Drive.")

    files = list_audio_files_in_folder(service, inbox_id)
    log(f"Audios encontrados no Drive: {len(files)}")

    state = load_state()
    sync_tracks(state, files)
    save_state(state)

    if not state["tracks"]:
        log("Sem musicas para processar. Encerrando.")
        return

    track = get_next_track(state)
    if not track:
        log("Nenhuma faixa disponivel para processar.")
        return

    name = track["name"]
    short_num = track.get("done", 0) + 1
    title_base = clean_title(name)

    log(f"Musica  : {name}")
    log(f"Short   : {short_num}/{SHORTS_PER_TRACK}")

    os.makedirs("temp", exist_ok=True)
    audio_path = f"temp/{name}"

    bg = None
    style = "default"
    styles = ["default"]
    thumbnail_path = None

    try:
        log("Baixando audio do Drive...")
        download_drive_file(service, track["id"], audio_path)
        log("Download concluido.")

        cached_genre = track.get("genre")
        if cached_genre:
            style = cached_genre
            styles = detect_genre_multi(audio_path)
            log(f"Genero (cache): {style}")
        else:
            log("Detectando genero por analise acustica...")
            style = detect_genre(audio_path)
            styles = detect_genre_multi(audio_path)
            track["genre"] = style
            save_state(state)
            log(f"Genero detectado: {style} | Secundarios: {', '.join(styles[1:] or ['nenhum'])}")

        date = datetime.utcnow().strftime("%Y-%m-%d")
        output_dir = Path("output") / date / style
        output_dir.mkdir(parents=True, exist_ok=True)
        planned_video_path = str(
            output_dir / f"{date}__{style}__{safe_filename(title_base)}__s{short_num}.mp4"
        )

        log(f"Gerando background (short {short_num})...")
        bg = resolve_background(style, name, short_num, styles)

        log("Gerando video...")
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

        log(f"Video pronto: {video_path}")
        if thumbnail_path:
            log(f"Thumbnail pronta: {thumbnail_path}")

        title = build_title(title_base, style, short_num)
        description = build_description(title_base, style, short_num)
        log(f"Titulo  : {title}")

        results = publish(video_path, title, description)

        if DRIVE_BACKUP_FOLDER_ID:
            try:
                log("Salvando backup no Drive...")
                upload_file_to_drive(service, DRIVE_BACKUP_FOLDER_ID, video_path)
                log("  Backup salvo com sucesso.")
            except Exception as e:
                log(f"  Backup falhou (nao critico): {e}")
        else:
            log("  Backup desabilitado (DRIVE_BACKUP_FOLDER_ID nao configurado).")

        any_ok = any(r.get("ok") for r in results.values())
        all_skipped = all(r.get("skipped") for r in results.values())

        if not any_ok and not all_skipped:
            raise RuntimeError("Nenhuma plataforma recebeu o video com sucesso.")

        track["done"] = short_num
        save_state(state)

        log("=" * 55)
        log(f"CONCLUIDO — {name} (short {short_num}/{SHORTS_PER_TRACK})")
        log("=" * 55)

    finally:
        for path in [audio_path, bg]:
            try:
                if path and isinstance(path, str) and os.path.exists(path):
                    if path.startswith("temp/"):
                        os.remove(path)
                        log(f"Temporario removido: {path}")
            except Exception:
                pass


if __name__ == "__main__":
    main()
