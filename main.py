import json
from pathlib import Path

STATE_FILE = Path("state.json")
SHORTS_PER_TRACK = 3


def load_state():
    if not STATE_FILE.exists():
        raise FileNotFoundError("Arquivo state.json não encontrado.")
    with STATE_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def get_next_track(state):
    for track in state.get("tracks", []):
        if not track.get("done", False):
            return track
    return None


def main():
    print("Bot iniciado...")

    state = load_state()
    track = get_next_track(state)

    if track is None:
        print("Nenhuma música pendente.")
        return

    music_name = track["name"]
    shorts_done = track.get("shorts_done", 0)

    if shorts_done >= SHORTS_PER_TRACK:
        track["done"] = True
        save_state(state)
        print(f"Música {music_name} já concluída. Passando para a próxima.")
        return

    short_number = shorts_done + 1

    print(f"Processando música: {music_name}")
    print(f"Criando short {short_number}/{SHORTS_PER_TRACK}")

    # Aqui depois entra a lógica real:
    # 1. baixar/ler a música
    # 2. gerar clipe
    # 3. renderizar o short
    # 4. postar no YouTube

    track["shorts_done"] = short_number

    if track["shorts_done"] >= SHORTS_PER_TRACK:
        track["done"] = True
        print(f"Finalizado 3/3 para {music_name}. Próxima execução vai para outra música.")
    else:
        print(f"Short {short_number} concluído para {music_name}.")

    save_state(state)
    print("Execução finalizada.")


if __name__ == "__main__":
    main()
