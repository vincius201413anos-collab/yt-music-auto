"""
audio_to_remotion.py — Audio Data Exporter for Remotion
========================================================
Usa o audio_analysis.py já existente no projeto para gerar
o audio_data.json que o Remotion precisa para sincronizar
os efeitos visuais com a música.

Saída: remotion/public/audio_data.json
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
    logger.warning("librosa não disponível.")

# Importa a análise completa do projeto
try:
    from audio_analysis import full_analysis
    ANALYSIS_OK = True
except ImportError:
    ANALYSIS_OK = False
    logger.warning("audio_analysis não encontrado — usando análise básica.")


def generate_audio_data(
    input_path: str,
    output_path: str = "remotion/public/audio_data.json",
) -> dict:
    """
    Gera audio_data.json com todos os dados de sincronização
    que o Remotion precisa: RMS, beats, kicks, snares, drop, seções.

    Compatível com o audio_analysis.py v2.0 do projeto.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # ── Análise completa via audio_analysis.py ────────────────────
    if ANALYSIS_OK:
        logger.info(f"  [remotion] Analisando: {Path(input_path).name}")
        analysis = full_analysis(input_path)
    else:
        analysis = _basic_analysis(input_path)

    # ── Curva RMS normalizada (usada para pulsar elementos visuais) ─
    rms_curve = _extract_rms(input_path)

    # ── Monta o JSON final ────────────────────────────────────────
    data = {
        # Curva de amplitude frame a frame (principal driver visual)
        "rms": rms_curve,

        # Informações gerais
        "bpm":          analysis.get("bpm", 120.0),
        "duration":     analysis.get("duration", 0.0),
        "song_profile": analysis.get("song_profile", "medium"),

        # Timestamps de eventos (em segundos)
        "beats":       analysis.get("beats", []),
        "bass_hits":   analysis.get("bass_hits", []),
        "snare_hits":  analysis.get("snare_hits", []),
        "hihat_hits":  analysis.get("hihat_hits", []),
        "drop_time":   analysis.get("drop_time", None),

        # Intensidade por beat: "weak" / "medium" / "strong"
        "beat_intensities": analysis.get("beat_intensities", []),

        # Curva de energia suavizada (0.0 a 1.0, 100 pontos)
        "energy_curve": analysis.get("energy_curve", []),

        # Seções da música (intro, buildup, drop, calm, outro)
        "sections": analysis.get("sections", {}),
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(
        f"  [remotion] ✓ audio_data.json gerado → {output_path} "
        f"({len(rms_curve)} pontos RMS | "
        f"beats={len(data['beats'])} | "
        f"kicks={len(data['bass_hits'])} | "
        f"drop={data['drop_time']})"
    )
    print(f"audio_data.json gerado com {len(rms_curve)} pontos")
    return data


def _extract_rms(input_path: str, hop_length: int = 512) -> list:
    """Extrai e normaliza a curva RMS do áudio."""
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
    """Fallback quando audio_analysis.py não está disponível."""
    if not LIBROSA_OK:
        return {"bpm": 120.0, "duration": 0.0, "beats": [], "bass_hits": [],
                "snare_hits": [], "hihat_hits": [], "drop_time": None,
                "beat_intensities": [], "energy_curve": [], "sections": {},
                "song_profile": "medium"}
    try:
        y, sr = librosa.load(input_path, mono=True)
        duration = float(librosa.get_duration(y=y, sr=sr))
        tempo, frames = librosa.beat.beat_track(y=y, sr=sr)
        bpm = float(np.ravel(tempo)[0]) if hasattr(tempo, "__len__") else float(tempo)
        beats = [float(t) for t in librosa.frames_to_time(frames, sr=sr)]
        return {
            "bpm": round(bpm, 1), "duration": duration,
            "beats": beats, "bass_hits": [], "snare_hits": [],
            "hihat_hits": [], "drop_time": None, "beat_intensities": [],
            "energy_curve": [], "sections": {}, "song_profile": "medium",
        }
    except Exception as e:
        logger.warning(f"_basic_analysis: {e}")
        return {"bpm": 120.0, "duration": 0.0, "beats": [], "bass_hits": [],
                "snare_hits": [], "hihat_hits": [], "drop_time": None,
                "beat_intensities": [], "energy_curve": [], "sections": {},
                "song_profile": "medium"}


# ── CLI: python audio_to_remotion.py <audio_path> ─────────────────
if __name__ == "__main__":
    import sys
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)-8s %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )

    if len(sys.argv) < 2:
        print("Uso: python audio_to_remotion.py <caminho_do_audio> [saida.json]")
        sys.exit(1)

    audio = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else "remotion/public/audio_data.json"

    generate_audio_data(audio, output)
