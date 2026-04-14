import os
import json
from pathlib import Path
from drive_service import get_drive_service, find_folder_id, list_mp3_files_in_folder

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
        if not track.get("done", False):
            return track
    return None


def scan_drive_folder():
    print("Escaneando Google Drive...")

    service = get_drive_service()

    inbox_folder_id = find_folder_id(service, DRIVE_FOLDER_ID, "inbox")
    if not inbox_folder_id:
        raise ValueError("Pasta 'inbox' não encontrada dentro da pasta principal do Drive.")

    mp3_files = list_mp3_files_in_folder(service, inbox_folder_id)

    names = [file["name"] for file in mp3_files]
    print(f"Músicas encontradas no inbox: {names}")

    return names


def sync_tracks(state, drive_files):
    existing_names = [track["name"] for track in state["tracks"]]

    for file_name in drive_files:
        if file_name not in existing_names:
            print(f"Nova música detectada: {file_name}")
            state["tracks"].append({
                "name": file_name,
                "shorts_done": 0,
                "done": False
            })


def main():
    print("Bot iniciado")

    if not DRIVE_FOLDER_ID:
        raise ValueError("Drive folder ID não encontrado")

    print("Drive folder ID carregado")

    state = load_state()
    drive_files = scan_drive_folder()
    sync_tracks(state, drive_files)

    track = get_next_track(state)

    if not track:
        print("Nenhuma música pendente")
        save_state(state)
        return

    name = track["name"]
    shorts_done = track.get("shorts_done", 0)

    if shorts_done >= SHORTS_PER_TRACK:
        track["done"] = True
        save_state(state)
        print(f"Música {name} já estava concluída")
        return

    short_number = shorts_done + 1

    print(f"Processando: {name}")
    print(f"Criando short {short_number}/{SHORTS_PER_TRACK}")

    track["shorts_done"] = short_number

    if track["shorts_done"] >= SHORTS_PER_TRACK:
        track["done"] = True
        print("Música finalizada")

    save_state(state)
    print("Execução finalizada")


if __name__ == "__main__":
    main()
