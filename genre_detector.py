"""
genre_detector.py — Detecção automática de gênero musical.

Ajustado para o canal DjDarkMark:
- prioridade maior para phonk / trap / dark / electronic
- fallback robusto
- correção para retorno de BPM do librosa
- menos chance de classificar errado música underground
"""

import os
import json
import re
from pathlib import Path

try:
    import librosa
    import numpy as np
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    print("[genre_detector] librosa não instalado — usando apenas nome + Claude.")

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("[genre_detector] anthropic não instalado — usando apenas heurísticas.")

SUPPORTED_GENRES = [
    "phonk", "trap", "rock", "metal", "electronic",
    "cinematic", "lofi", "indie", "pop", "funk", "dark", "default"
]

# Ordem alinhada ao teu canal
CHANNEL_PRIORITY = [
    "phonk", "trap", "dark", "electronic",
    "indie", "rock", "lofi", "cinematic", "pop", "funk", "metal"
]

FILENAME_KEYWORDS = {
    "phonk":      ["phonk", "drift", "cowbell", "dark phonk"],
    "trap":       ["trap", "808", "rage", "drill"],
    "lofi":       ["lofi", "lo-fi", "chill", "sad", "study", "relax"],
    "cinematic":  ["cinematic", "epic", "ambient", "orchestral", "ost", "score"],
    "rock":       ["rock", "guitar", "grunge", "alternative", "punk"],
    "metal":      ["metal", "metalcore", "deathcore", "hardcore", "djent", "breakdown"],
    "indie":      ["indie", "dream", "shoegaze", "bedroom", "alt"],
    "pop":        ["pop", "commercial", "mainstream", "radio"],
    "funk":       ["funk", "mandela", "bruxaria", "groove", "soul"],
    "electronic": ["edm", "electronic", "house", "techno", "trance", "dubstep", "dnb", "bass"],
    "dark":       ["dark", "gothic", "witch", "sinister", "occult"],
}

FILENAME_PRIORITY = [
    "phonk", "trap", "dark", "electronic",
    "metal", "rock", "indie", "lofi", "cinematic", "pop", "funk"
]


def _safe_scalar(value) -> float:
    """
    Converte escalar/array/lista do librosa para float sem quebrar.
    """
    try:
        if isinstance(value, (list, tuple)):
            return float(value[0])
        if hasattr(value, "ndim"):
            if value.ndim == 0:
                return float(value)
            flat = np.ravel(value)
            return float(flat[0]) if len(flat) else 0.0
        return float(value)
    except Exception:
        return 0.0


def extract_acoustic_features(audio_path: str) -> dict | None:
    if not LIBROSA_AVAILABLE:
        return None

    try:
        y, sr = librosa.load(audio_path, duration=90, mono=True)

        # BPM
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm = _safe_scalar(tempo)

        # Energia RMS
        rms = librosa.feature.rms(y=y)
        avg_energy = float(np.mean(rms))
        energy_var = float(np.var(rms))

        # Brilho
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        avg_centroid = float(np.mean(centroid))

        rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
        avg_rolloff = float(np.mean(rolloff))

        # ZCR
        zcr = librosa.feature.zero_crossing_rate(y)
        avg_zcr = float(np.mean(zcr))

        # Harmonia
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_std = float(np.std(chroma))
        chroma_mean = float(np.mean(chroma))

        # MFCC
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_means = [float(np.mean(mfcc[i])) for i in range(13)]

        # Bandas
        stft = np.abs(librosa.stft(y))
        freqs = librosa.fft_frequencies(sr=sr)

        sub_bass_mask = (freqs >= 20) & (freqs <= 80)
        bass_mask = (freqs >= 80) & (freqs <= 250)
        mid_mask = (freqs >= 250) & (freqs <= 4000)
        high_mask = (freqs >= 4000) & (freqs <= 20000)

        total_energy = float(np.mean(stft)) + 1e-9
        sub_bass_ratio = float(np.mean(stft[sub_bass_mask])) / total_energy if np.any(sub_bass_mask) else 0.0
        bass_ratio = float(np.mean(stft[bass_mask])) / total_energy if np.any(bass_mask) else 0.0
        mid_ratio = float(np.mean(stft[mid_mask])) / total_energy if np.any(mid_mask) else 0.0
        high_ratio = float(np.mean(stft[high_mask])) / total_energy if np.any(high_mask) else 0.0

        # Onset
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        onset_mean = float(np.mean(onset_env))
        onset_max = float(np.max(onset_env))

        duration = float(librosa.get_duration(y=y, sr=sr))

        return {
            "bpm": round(bpm, 1),
            "avg_energy": round(avg_energy, 5),
            "energy_var": round(energy_var, 8),
            "avg_centroid": round(avg_centroid, 1),
            "avg_rolloff": round(avg_rolloff, 1),
            "avg_zcr": round(avg_zcr, 5),
            "chroma_std": round(chroma_std, 4),
            "chroma_mean": round(chroma_mean, 4),
            "mfcc_1": round(mfcc_means[0], 2),
            "mfcc_2": round(mfcc_means[1], 2),
            "mfcc_3": round(mfcc_means[2], 2),
            "sub_bass_ratio": round(sub_bass_ratio, 4),
            "bass_ratio": round(bass_ratio, 4),
            "mid_ratio": round(mid_ratio, 4),
            "high_ratio": round(high_ratio, 4),
            "onset_mean": round(onset_mean, 4),
            "onset_max": round(onset_max, 4),
            "duration_s": round(duration, 1),
        }

    except Exception as e:
        print(f"[genre_detector] Erro ao extrair features: {e}")
        return None


def heuristic_scores(features: dict) -> dict:
    if not features:
        return {g: 0.0 for g in SUPPORTED_GENRES}

    bpm = features["bpm"]
    energy = features["avg_energy"]
    centroid = features["avg_centroid"]
    sub_bass = features["sub_bass_ratio"]
    bass = features["bass_ratio"]
    mid = features["mid_ratio"]
    high = features["high_ratio"]
    zcr = features["avg_zcr"]
    onset_mean = features["onset_mean"]
    chroma_std = features["chroma_std"]
    energy_var = features["energy_var"]

    scores = {g: 0.0 for g in SUPPORTED_GENRES}

    # METAL
    if bpm > 150:            scores["metal"] += 1.8
    if bpm > 180:            scores["metal"] += 1.2
    if energy > 0.12:        scores["metal"] += 1.4
    if zcr > 0.12:           scores["metal"] += 1.8
    if mid > 0.35:           scores["metal"] += 1.2
    if high > 0.15:          scores["metal"] += 0.8

    # ROCK
    if 100 < bpm <= 180:     scores["rock"] += 1.2
    if energy > 0.08:        scores["rock"] += 1.0
    if zcr > 0.08:           scores["rock"] += 1.2
    if mid > 0.28:           scores["rock"] += 1.2
    if chroma_std > 0.18:    scores["rock"] += 1.0

    # PHONK
    if 128 <= bpm <= 170:    scores["phonk"] += 2.2
    if sub_bass > 0.06:      scores["phonk"] += 2.6
    if bass > 0.20:          scores["phonk"] += 1.6
    if energy > 0.06:        scores["phonk"] += 1.0
    if onset_mean > 2.0:     scores["phonk"] += 1.0
    if centroid < 2800:      scores["phonk"] += 0.5

    # TRAP
    if 120 <= bpm <= 170:    scores["trap"] += 1.8
    if sub_bass > 0.05:      scores["trap"] += 2.0
    if high > 0.12:          scores["trap"] += 1.4
    if energy > 0.05:        scores["trap"] += 0.8
    if mid > 0.22:           scores["trap"] += 0.4

    # ELECTRONIC
    if 118 <= bpm <= 150:    scores["electronic"] += 1.4
    if centroid > 3000:      scores["electronic"] += 1.8
    if high > 0.18:          scores["electronic"] += 1.8
    if energy_var > 1e-5:    scores["electronic"] += 1.2

    # LOFI
    if bpm < 90:             scores["lofi"] += 2.0
    if energy < 0.04:        scores["lofi"] += 1.8
    if centroid < 2000:      scores["lofi"] += 1.2
    if energy_var < 1e-6:    scores["lofi"] += 1.2

    # CINEMATIC
    if energy_var > 5e-5:    scores["cinematic"] += 1.8
    if chroma_std > 0.20:    scores["cinematic"] += 1.8
    if bpm < 100:            scores["cinematic"] += 0.8
    if mid < 0.20:           scores["cinematic"] += 0.8

    # INDIE
    if 80 <= bpm <= 130:     scores["indie"] += 1.0
    if energy < 0.07:        scores["indie"] += 1.2
    if chroma_std > 0.15:    scores["indie"] += 1.2
    if zcr < 0.08:           scores["indie"] += 0.8

    # POP
    if 100 <= bpm <= 130:    scores["pop"] += 1.2
    if centroid > 2500:      scores["pop"] += 1.2
    if energy > 0.06:        scores["pop"] += 0.8
    if chroma_std < 0.16:    scores["pop"] += 0.8

    # FUNK
    if 90 <= bpm <= 130:     scores["funk"] += 1.2
    if bass > 0.18:          scores["funk"] += 1.8
    if onset_mean > 1.5:     scores["funk"] += 1.2
    if mid > 0.25:           scores["funk"] += 0.8

    # DARK
    if bpm < 125:            scores["dark"] += 1.0
    if energy < 0.07:        scores["dark"] += 1.2
    if centroid < 2300:      scores["dark"] += 1.4
    if chroma_std < 0.12:    scores["dark"] += 1.4
    if sub_bass > 0.04:      scores["dark"] += 0.5

    return scores


def heuristic_genre(features: dict) -> str:
    scores = heuristic_scores(features)
    scores.pop("default", None)

    # bias do canal: em dúvida, prefere phonk/trap/dark/electronic
    for g, bonus in {
        "phonk": 0.18,
        "trap": 0.14,
        "dark": 0.10,
        "electronic": 0.06,
    }.items():
        if g in scores:
            scores[g] += bonus

    best = max(scores, key=lambda g: scores[g])
    if scores[best] < 2.0:
        return "default"
    return best


def claude_classify_genre(filename: str, features: dict | None, heuristic_candidate: str) -> str:
    if not ANTHROPIC_AVAILABLE:
        return heuristic_candidate

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return heuristic_candidate

    try:
        client = anthropic.Anthropic(api_key=api_key)

        features_text = ""
        if features:
            features_text = f"""
Características acústicas:
- BPM: {features['bpm']}
- Energia média: {features['avg_energy']}
- Variação de energia: {features['energy_var']}
- Spectral centroid: {features['avg_centroid']} Hz
- Spectral rolloff: {features['avg_rolloff']} Hz
- ZCR: {features['avg_zcr']}
- Sub-bass ratio: {features['sub_bass_ratio']}
- Bass ratio: {features['bass_ratio']}
- Mid ratio: {features['mid_ratio']}
- High ratio: {features['high_ratio']}
- Onset mean: {features['onset_mean']}
- Chroma std: {features['chroma_std']}
- Duration: {features['duration_s']}s
"""
        else:
            features_text = "Análise acústica não disponível."

        resp = client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-opus-4-7"),
            max_tokens=60,
            system=(
                "You are an expert music genre classifier. "
                "Classify the track into exactly one of these genres only: "
                f"{', '.join(SUPPORTED_GENRES)}. "
                "Reply with only the genre name."
            ),
            messages=[{
                "role": "user",
                "content": (
                    f"Filename: {filename}\n"
                    f"Heuristic candidate: {heuristic_candidate}\n"
                    f"{features_text}\n"
                    f"Choose exactly one genre from: {', '.join(SUPPORTED_GENRES)}"
                ),
            }],
        )

        raw = resp.content[0].text.strip().lower()
        for g in SUPPORTED_GENRES:
            if g in raw:
                print(f"[genre_detector] Claude classificou: {g}")
                return g

        print(f"[genre_detector] Claude retornou '{raw}' — usando heurística: {heuristic_candidate}")
        return heuristic_candidate

    except Exception as e:
        print(f"[genre_detector] Erro no Claude: {e} — usando heurística: {heuristic_candidate}")
        return heuristic_candidate


def detect_genre_from_filename(filename: str) -> str:
    name = Path(filename).stem.lower()
    found = []
    for genre, keywords in FILENAME_KEYWORDS.items():
        for kw in keywords:
            if kw in name:
                found.append(genre)
                break

    if not found:
        return "default"

    for priority_genre in FILENAME_PRIORITY:
        if priority_genre in found:
            return priority_genre

    return found[0]


def detect_genre(audio_path: str) -> str:
    filename = Path(audio_path).name
    print(f"[genre_detector] Analisando: {filename}")

    features = None
    if LIBROSA_AVAILABLE and os.path.exists(audio_path):
        print("[genre_detector] Extraindo features acústicas...")
        features = extract_acoustic_features(audio_path)
        if features:
            print(
                f"[genre_detector] BPM={features['bpm']} | "
                f"Energia={features['avg_energy']:.4f} | "
                f"Sub-bass={features['sub_bass_ratio']:.4f} | "
                f"Centroid={features['avg_centroid']:.0f}Hz"
            )

    heuristic = heuristic_genre(features) if features else "default"
    print(f"[genre_detector] Heurística: {heuristic}")

    filename_hint = detect_genre_from_filename(filename)
    if filename_hint != "default":
        print(f"[genre_detector] Dica do nome do arquivo: {filename_hint}")
        if filename_hint == heuristic:
            print(f"[genre_detector] Nome confirma heurística → {heuristic}")
            return heuristic

    if ANTHROPIC_AVAILABLE and features:
        enhanced_filename = filename
        if filename_hint != "default":
            enhanced_filename = f"{filename} [hint: {filename_hint}]"

        final_genre = claude_classify_genre(enhanced_filename, features, heuristic)
        print(f"[genre_detector] Gênero final (Claude): {final_genre}")
        return final_genre

    if heuristic != "default":
        print(f"[genre_detector] Usando heurística: {heuristic}")
        return heuristic

    if filename_hint != "default":
        print(f"[genre_detector] Usando nome do arquivo: {filename_hint}")
        return filename_hint

    print("[genre_detector] Nenhum gênero detectado — usando default")
    return "default"


def detect_genre_multi(audio_path: str) -> list[str]:
    primary = detect_genre(audio_path)

    related = {
        "phonk":      ["dark", "trap"],
        "trap":       ["phonk", "dark"],
        "dark":       ["phonk", "trap"],
        "electronic": ["trap", "dark"],
        "rock":       ["indie", "dark"],
        "metal":      ["dark", "rock"],
        "cinematic":  ["dark", "electronic"],
        "lofi":       ["indie", "cinematic"],
        "indie":      ["dark", "lofi"],
        "pop":        ["electronic", "indie"],
        "funk":       ["electronic", "pop"],
        "default":    ["dark", "trap"],
    }

    secondary = related.get(primary, [])
    return [primary] + secondary


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python genre_detector.py <caminho_do_audio>")
        raise SystemExit(1)

    path = sys.argv[1]
    print(f"\n{'=' * 50}")
    print(f"Analisando: {path}")
    print(f"{'=' * 50}")

    genre = detect_genre(path)
    genres = detect_genre_multi(path)

    print(f"\n✅ Gênero principal: {genre}")
    print(f"📋 Gêneros (com secundários): {genres}")
