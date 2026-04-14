import os
import json
import requests
from pathlib import Path

STATE_FILE = Path("state.json")
SHORTS_PER_TRACK = 3

DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")


def load_state():
    if not STATE_FILE.exists():
        return {"tracks": []}

    with STATE_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def get_next_track(state):
    for track in state["tracks"]:
        if not track["done"]:
            return track
    return None


def scan_drive_folder():
    print("Escaneando Google Drive...")

    # Aqui ainda simulamos leitura
    # depois vamos usar API real

    fake_files = [
        "musica1.mp3",
        "musica2.mp3"
    ]

    return fake_files


def sync_tracks(state, drive_files):
    existing = [t["name"] for t in state["tracks"]]

    for file in drive_files:
        if file not in existing:
            print(f"Nova música detectada: {file}")

            state["tracks"].append({
                "name": file,
                "shorts_done": 0,
                "done": False
            })


def main():
    print("Bot iniciado...")

    if not DRIVE_FOLDER_ID:
        raise ValueError("Drive folder ID não encontrado")

    print("Drive folder ID carregado")

    state = load_state()

    drive_files = scan_drive_folder()

    sync_tracks(state, drive_files)

    track = get_next_track(state)

    if not track:
        print("Nenhuma música pendente")
        return

    name = track["name"]
    shorts_done = track["shorts_done"]

    if shorts_done >= SHORTS_PER_TRACK:
        track["done"] = True
        save_state(state)
        return

    short_number = shorts_done + 1

    print(f"Processando: {name}")
    print(f"Criando short {short_number}/3")

    # Aqui depois entra geração de vídeo

    track["shorts_done"] = short_number

    if track["shorts_done"] >= SHORTS_PER_TRACK:
        track["done"] = True
        print("Música finalizada")

    save_state(state)

    print("Execução finalizada")


if __name__ == "__main__":
    main()
