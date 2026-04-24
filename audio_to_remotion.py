"""
audio_to_remotion.py — Audio Data Exporter for Remotion
========================================================
Usa o audio_analysis.py do projeto para gerar
remotion/public/audio_data.json com todos os dados
de sincronização: RMS, beats, kicks, snares, drop, seções.
"""

import json
import os
import logging
from pathlib import Path

logger = logging.getLogger("audio_to_remotion")

try:
    import numpy as np
    import librosa
    LIBROSA_OK = True
except ImportError:
    LIBROSA_OK = False

try:
    from audio_analysis import full_analysis
    ANALYSIS_OK = True
except ImportError:
    ANALYSIS_OK = False


def generate_audio_data(
    input_path: str,
    output_path: str = "remotion/public/audio_data.json",
) -> dict:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if ANALYSIS_OK:
        analysis = full_analysis(input_path)
    else:
        analysis = _basic_analysis(input_path)

    rms_curve = _extract_rms(input_path)

    data = {
        "rms":              rms_curve,
        "bpm":              analysis.get("bpm", 120.0),
        "duration":         analysis.get("duration", 0.0),
        "song_profile":     analysis.get("song_profile", "medium"),
        "beats":            analysis.get("beats", []),
        "bass_hits":        analysis.get("bass_hits", []),
        "snare_hits":       analysis.get("snare_hits", []),
        "hihat_hits":       analysis.get("hihat_hits", []),
        "drop_time":        analysis.get("drop_time", None),
        "beat_intensities": analysis.get("beat_intensities", []),
        "energy_curve":     analysis.get("energy_curve", []),
        "sections":         analysis.get("sections", {}),
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"audio_data.json gerado com {len(rms_curve)} pontos RMS")
    return data


def _extract_rms(input_path: str, hop_length: int = 512) -> list:
    if not LIBROSA_OK:
        return []
    try:
        y, sr = librosa.load(input_path, mono=True)
        rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
        max_val = float(np.max(rms)) if np.max(rms) != 0 else 1.0
        return [round(float(v) / max_val, 6) for v in rms]
    except Exception as e:
        logger.warning(f"_extract_rms: {e}")
        return []


def _basic_analysis(input_path: str) -> dict:
    empty = {
        "bpm": 120.0, "duration": 0.0, "beats": [],
        "bass_hits": [], "snare_hits": [], "hihat_hits": [],
        "drop_time": None, "beat_intensities": [],
        "energy_curve": [], "sections": {}, "song_profile": "medium",
    }
    if not LIBROSA_OK:
        return empty
    try:
        y, sr    = librosa.load(input_path, mono=True)
        duration = float(librosa.get_duration(y=y, sr=sr))
        tempo, frames = librosa.beat.beat_track(y=y, sr=sr)
        bpm   = float(np.ravel(tempo)[0]) if hasattr(tempo, "__len__") else float(tempo)
        beats = [float(t) for t in librosa.frames_to_time(frames, sr=sr)]
        return {**empty, "bpm": round(bpm, 1), "duration": duration, "beats": beats}
    except Exception as e:
        logger.warning(f"_basic_analysis: {e}")
        return empty


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")

    if len(sys.argv) < 2:
        print("Uso: python audio_to_remotion.py <audio> [saida.json]")
        sys.exit(1)

    audio  = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else "remotion/public/audio_data.json"
    generate_audio_data(audio, output)
