""
genre_detector.py — Detecção automática de gênero musical v2.0 FINAL
====================================================================
Objetivo:
- Parar de chamar tudo de phonk.
- Separar melhor phonk / trap / electronic / dark.
- Usar nome do arquivo como pista, mas sem dominar quando a análise acústica contradiz.
- Evitar cache ruim: este arquivo sempre retorna gênero mais confiável possível.
- Compatível com detect_genre(...) e detect_genre_multi(...).
"""

from __future__ import annotations

import os
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

# Ordem de desempate. Phonk NÃO fica mais sempre acima de tudo.
TIE_PRIORITY = [
    "trap", "electronic", "phonk", "dark",
    "lofi", "indie", "rock", "metal", "cinematic", "funk", "pop"
]

FILENAME_KEYWORDS = {
    "phonk": [
        "phonk", "drift phonk", "cowbell", "memphis", "sigma phonk",
        "brazilian phonk", "dark phonk", "phonkwave"
    ],
    "trap": [
        "trap", "808", "rage", "drill", "pluggnb", "jerk", "opium",
        "carti", "ken carson", "yeat", "future type", "hard trap"
    ],
    "electronic": [
        "edm", "electronic", "house", "techno", "trance", "dubstep",
        "dnb", "drum and bass", "bass house", "synthwave", "electro",
        "rave", "dance", "hyperpop", "hardstyle", "club"
    ],
    "dark": [
        "dark", "gothic", "witch", "sinister", "occult", "shadow",
        "madrugada", "nightmare", "ghost", "phantom"
    ],
    "lofi": [
        "lofi", "lo-fi", "chill", "sad", "study", "relax", "sleep",
        "rain", "alone"
    ],
    "cinematic": [
        "cinematic", "epic", "ambient", "orchestral", "ost", "score",
        "trailer", "film"
    ],
    "rock": [
        "rock", "guitar", "grunge", "alternative", "punk", "riff"
    ],
    "metal": [
        "metal", "metalcore", "deathcore", "hardcore", "djent",
        "breakdown", "heavy"
    ],
    "indie": [
        "indie", "dream", "shoegaze", "bedroom", "alt"
    ],
    "pop": [
        "pop", "commercial", "mainstream", "radio"
    ],
    "funk": [
        "funk", "mandela", "bruxaria", "groove", "soul"
    ],
}

# Quando o nome contém uma dessas palavras, ela tem peso forte.
STRONG_FILENAME_HINTS = {"phonk", "trap", "electronic", "dark", "lofi", "rock", "metal", "funk"}


def _safe_scalar(value) -> float:
    try:
        if isinstance(value, (list, tuple)):
            return float(value[0]) if value else 0.0
        if hasattr(value, "ndim"):
            if value.ndim == 0:
                return float(value)
            flat = np.ravel(value)
            return float(flat[0]) if len(flat) else 0.0
        return float(value)
    except Exception:
        return 0.0


def _normalize_bpm(bpm: float) -> float:
    """
    Librosa às vezes retorna BPM dobrado/metade. Mantém o valor musical mais útil.
    Ex:
    83 pode ser trap/phonk em halftime, mas também equivale a 166.
    """
    bpm = float(bpm or 0.0)
    if bpm <= 0:
        return 0.0
    if bpm < 70:
        return bpm * 2
    if bpm > 190:
        return bpm / 2
    return bpm


def _halftime_bpm(bpm: float) -> float:
    if bpm >= 120:
        return bpm / 2
    return bpm


def extract_acoustic_features(audio_path: str) -> dict | None:
    if not LIBROSA_AVAILABLE:
        return None

    try:
        y, sr = librosa.load(audio_path, duration=90, mono=True)

        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm_raw = _safe_scalar(tempo)
        bpm = _normalize_bpm(bpm_raw)
        bpm_half = _halftime_bpm(bpm)

        rms = librosa.feature.rms(y=y)
        avg_energy = float(np.mean(rms))
        energy_var = float(np.var(rms))

        centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        avg_centroid = float(np.mean(centroid))

        rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
        avg_rolloff = float(np.mean(rolloff))

        zcr = librosa.feature.zero_crossing_rate(y)
        avg_zcr = float(np.mean(zcr))

        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_std = float(np.std(chroma))
        chroma_mean = float(np.mean(chroma))

        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_means = [float(np.mean(mfcc[i])) for i in range(13)]

        stft = np.abs(librosa.stft(y))
        freqs = librosa.fft_frequencies(sr=sr)

        def band_ratio(low: int, high: int) -> float:
            mask = (freqs >= low) & (freqs <= high)
            total = float(np.mean(stft)) + 1e-9
            return float(np.mean(stft[mask])) / total if np.any(mask) else 0.0

        sub_bass_ratio = band_ratio(20, 80)
        bass_ratio = band_ratio(80, 250)
        low_mid_ratio = band_ratio(250, 800)
        mid_ratio = band_ratio(250, 4000)
        high_ratio = band_ratio(4000, 20000)

        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        onset_mean = float(np.mean(onset_env))
        onset_max = float(np.max(onset_env))
        onset_std = float(np.std(onset_env))

        # Percentual de transientes fortes: ajuda a separar eletrônica/trap/phonk.
        onset_threshold = np.percentile(onset_env, 80) if len(onset_env) else 0
        onset_density = float(np.mean(onset_env > onset_threshold)) if len(onset_env) else 0.0

        duration = float(librosa.get_duration(y=y, sr=sr))

        return {
            "bpm_raw": round(bpm_raw, 1),
            "bpm": round(bpm, 1),
            "bpm_half": round(bpm_half, 1),
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
            "low_mid_ratio": round(low_mid_ratio, 4),
            "mid_ratio": round(mid_ratio, 4),
            "high_ratio": round(high_ratio, 4),
            "onset_mean": round(onset_mean, 4),
            "onset_max": round(onset_max, 4),
            "onset_std": round(onset_std, 4),
            "onset_density": round(onset_density, 4),
            "duration_s": round(duration, 1),
        }

    except Exception as e:
        print(f"[genre_detector] Erro ao extrair features: {e}")
        return None


def filename_scores(filename: str) -> dict[str, float]:
    name = Path(filename).stem.lower()
    name = re.sub(r"[_\-]+", " ", name)
    scores = {g: 0.0 for g in SUPPORTED_GENRES}

    for genre, keywords in FILENAME_KEYWORDS.items():
        for kw in keywords:
            if kw in name:
                # Palavra explícita vale bastante, mas não decide tudo sozinha.
                scores[genre] += 2.4 if genre in STRONG_FILENAME_HINTS else 1.4
                if kw == genre:
                    scores[genre] += 0.6

    return scores


def detect_genre_from_filename(filename: str) -> str:
    scores = filename_scores(filename)
    scores.pop("default", None)
    best = max(scores, key=lambda g: scores[g])
    return best if scores[best] > 0 else "default"


def heuristic_scores(features: dict | None, filename: str = "") -> dict[str, float]:
    scores = {g: 0.0 for g in SUPPORTED_GENRES}

    if filename:
        fs = filename_scores(filename)
        for g, v in fs.items():
            scores[g] += v

    if not features:
        return scores

    bpm = features["bpm"]
    bpm_half = features.get("bpm_half", bpm / 2 if bpm else 0)
    energy = features["avg_energy"]
    centroid = features["avg_centroid"]
    rolloff = features["avg_rolloff"]
    sub_bass = features["sub_bass_ratio"]
    bass = features["bass_ratio"]
    low_mid = features.get("low_mid_ratio", 0.0)
    mid = features["mid_ratio"]
    high = features["high_ratio"]
    zcr = features["avg_zcr"]
    onset_mean = features["onset_mean"]
    onset_std = features.get("onset_std", 0.0)
    energy_var = features["energy_var"]
    chroma_std = features["chroma_std"]

    # PHONK: normalmente dark/drift, muito sub/bass, médio brilho, 120-170 ou halftime 60-90.
    # Antes ele ganhava fácil demais; agora precisa de low-end + clima escuro.
    if 125 <= bpm <= 175 or 62 <= bpm_half <= 88:
        scores["phonk"] += 1.5
    if sub_bass > 0.07:
        scores["phonk"] += 1.6
    if bass > 0.24:
        scores["phonk"] += 1.1
    if 1800 <= centroid <= 3400:
        scores["phonk"] += 0.9
    if high < 0.16:
        scores["phonk"] += 0.6
    if energy > 0.055:
        scores["phonk"] += 0.5
    if onset_mean > 1.4:
        scores["phonk"] += 0.4

    # TRAP: 808/sub forte + hi-hat/brilho maior que phonk + halftime comum.
    if 120 <= bpm <= 175 or 60 <= bpm_half <= 88:
        scores["trap"] += 1.6
    if sub_bass > 0.055:
        scores["trap"] += 1.4
    if high > 0.12:
        scores["trap"] += 1.5
    if centroid > 2400:
        scores["trap"] += 0.8
    if bass > 0.18:
        scores["trap"] += 0.6
    if onset_std > 1.1:
        scores["trap"] += 0.6

    # ELECTRONIC: brilho, transientes regulares, energia/variação e BPM de club.
    if 118 <= bpm <= 150:
        scores["electronic"] += 1.8
    if 126 <= bpm <= 140:
        scores["electronic"] += 0.8
    if centroid > 3000:
        scores["electronic"] += 1.8
    if rolloff > 5500:
        scores["electronic"] += 0.8
    if high > 0.17:
        scores["electronic"] += 1.6
    if energy_var > 1e-5:
        scores["electronic"] += 1.1
    if onset_mean > 1.8:
        scores["electronic"] += 0.7

    # DARK: clima escuro, menos brilho, menos energia. Pode coexistir como secundário.
    if energy < 0.075:
        scores["dark"] += 1.2
    if centroid < 2400:
        scores["dark"] += 1.2
    if high < 0.10:
        scores["dark"] += 0.9
    if chroma_std < 0.13:
        scores["dark"] += 0.8
    if sub_bass > 0.04:
        scores["dark"] += 0.4

    # LOFI
    if bpm < 95:
        scores["lofi"] += 1.8
    if energy < 0.045:
        scores["lofi"] += 1.5
    if centroid < 2100:
        scores["lofi"] += 1.0
    if high < 0.09:
        scores["lofi"] += 0.8
    if energy_var < 1e-6:
        scores["lofi"] += 0.8

    # ROCK / METAL
    if 100 < bpm <= 180:
        scores["rock"] += 0.8
    if energy > 0.085:
        scores["rock"] += 0.8
    if zcr > 0.08:
        scores["rock"] += 1.1
    if mid > 0.28:
        scores["rock"] += 0.9
    if chroma_std > 0.18:
        scores["rock"] += 0.8

    if bpm > 150:
        scores["metal"] += 1.2
    if bpm > 180:
        scores["metal"] += 0.8
    if energy > 0.12:
        scores["metal"] += 1.0
    if zcr > 0.12:
        scores["metal"] += 1.6
    if mid > 0.35:
        scores["metal"] += 1.0
    if high > 0.15:
        scores["metal"] += 0.7

    # CINEMATIC / INDIE / POP / FUNK
    if energy_var > 5e-5:
        scores["cinematic"] += 1.2
    if chroma_std > 0.22:
        scores["cinematic"] += 1.2
    if bpm < 100:
        scores["cinematic"] += 0.5

    if 80 <= bpm <= 130:
        scores["indie"] += 0.8
    if energy < 0.07:
        scores["indie"] += 0.8
    if chroma_std > 0.15:
        scores["indie"] += 0.8
    if zcr < 0.08:
        scores["indie"] += 0.5

    if 95 <= bpm <= 135:
        scores["pop"] += 0.8
    if centroid > 2500:
        scores["pop"] += 0.8
    if energy > 0.06:
        scores["pop"] += 0.5
    if chroma_std < 0.16:
        scores["pop"] += 0.5

    if 90 <= bpm <= 135:
        scores["funk"] += 0.8
    if bass > 0.18:
        scores["funk"] += 1.0
    if onset_mean > 1.5:
        scores["funk"] += 0.8
    if low_mid > 0.25:
        scores["funk"] += 0.4

    # Penalidades para evitar phonk falso.
    # Se tem muito brilho/high, tende mais trap/electronic.
    if high > 0.18 and centroid > 3000:
        scores["phonk"] -= 1.1
        scores["electronic"] += 0.7
    if high > 0.15 and sub_bass > 0.05:
        scores["trap"] += 0.7
        scores["phonk"] -= 0.4
    # Se o BPM é bem de house/techno e tem brilho, evita phonk.
    if 124 <= bpm <= 140 and centroid > 3100 and high > 0.16:
        scores["phonk"] -= 1.2
        scores["electronic"] += 1.0
    # Se está escuro/lento mas sem low-end forte, não força phonk.
    if sub_bass < 0.045 and bass < 0.18:
        scores["phonk"] -= 0.8

    return scores


def _best_from_scores(scores: dict[str, float]) -> tuple[str, float, dict[str, float]]:
    clean = {g: float(v) for g, v in scores.items() if g != "default"}
    ordered = sorted(
        clean.items(),
        key=lambda kv: (kv[1], -TIE_PRIORITY.index(kv[0]) if kv[0] in TIE_PRIORITY else -999),
        reverse=True,
    )
    if not ordered:
        return "default", 0.0, clean
    return ordered[0][0], ordered[0][1], clean


def heuristic_genre(features: dict | None, filename: str = "") -> str:
    scores = heuristic_scores(features, filename)
    best, score, _ = _best_from_scores(scores)
    if score < 2.0:
        return "default"
    return best


def _score_summary(scores: dict[str, float], limit: int = 5) -> str:
    items = sorted(
        [(g, v) for g, v in scores.items() if g != "default"],
        key=lambda kv: kv[1],
        reverse=True,
    )[:limit]
    return ", ".join(f"{g}={v:.2f}" for g, v in items)


def claude_classify_genre(filename: str, features: dict | None, heuristic_candidate: str, scores: dict[str, float]) -> str:
    if not ANTHROPIC_AVAILABLE:
        return heuristic_candidate

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return heuristic_candidate

    try:
        client = anthropic.Anthropic(api_key=api_key)

        if features:
            features_text = f"""
Características acústicas:
- BPM raw: {features.get('bpm_raw')}
- BPM normalizado: {features['bpm']}
- BPM halftime: {features.get('bpm_half')}
- Energia média: {features['avg_energy']}
- Variação de energia: {features['energy_var']}
- Spectral centroid: {features['avg_centroid']} Hz
- Spectral rolloff: {features['avg_rolloff']} Hz
- ZCR: {features['avg_zcr']}
- Sub-bass ratio: {features['sub_bass_ratio']}
- Bass ratio: {features['bass_ratio']}
- Low-mid ratio: {features.get('low_mid_ratio')}
- Mid ratio: {features['mid_ratio']}
- High ratio: {features['high_ratio']}
- Onset mean: {features['onset_mean']}
- Onset std: {features.get('onset_std')}
- Chroma std: {features['chroma_std']}
- Duration: {features['duration_s']}s
- Heuristic scores: {_score_summary(scores, 8)}
"""
        else:
            features_text = "Análise acústica não disponível."

        resp = client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-opus-4-7"),
            max_tokens=40,
            temperature=0,
            system=(
                "You are an expert music genre classifier. "
                "Classify the track into exactly one of these genres only: "
                f"{', '.join(SUPPORTED_GENRES)}. "
                "Do not overuse phonk. Use phonk only when it clearly has phonk/drift/cowbell/dark phonk traits. "
                "Trap usually has 808/sub bass and hi-hats. Electronic usually has bright synths, club BPM, and high spectral centroid. "
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
            if re.fullmatch(rf".*\b{re.escape(g)}\b.*", raw):
                print(f"[genre_detector] Claude classificou: {g}")
                return g

        print(f"[genre_detector] Claude retornou '{raw}' — usando heurística: {heuristic_candidate}")
        return heuristic_candidate

    except Exception as e:
        print(f"[genre_detector] Erro no Claude: {e} — usando heurística: {heuristic_candidate}")
        return heuristic_candidate


def _final_guardrails(final_genre: str, heuristic: str, filename_hint: str, features: dict | None, scores: dict[str, float]) -> str:
    """
    Impede resultado claramente zoado, principalmente phonk falso.
    """
    if not features:
        return final_genre

    high = features["high_ratio"]
    centroid = features["avg_centroid"]
    sub_bass = features["sub_bass_ratio"]
    bpm = features["bpm"]

    # Se Claude/heurística devolver phonk, mas o áudio parece bem eletrônico/trap, corrige.
    if final_genre == "phonk":
        electronic_score = scores.get("electronic", 0.0)
        trap_score = scores.get("trap", 0.0)
        phonk_score = scores.get("phonk", 0.0)

        if filename_hint in {"trap", "electronic"} and scores.get(filename_hint, 0.0) >= phonk_score - 0.5:
            print(f"[genre_detector] Guardrail: phonk -> {filename_hint} por nome + score próximo")
            return filename_hint

        if 124 <= bpm <= 140 and centroid > 3100 and high > 0.16 and electronic_score >= phonk_score - 0.8:
            print("[genre_detector] Guardrail: phonk -> electronic por BPM/brilho")
            return "electronic"

        if high > 0.15 and sub_bass > 0.05 and trap_score >= phonk_score - 0.5:
            print("[genre_detector] Guardrail: phonk -> trap por sub/hi-hat")
            return "trap"

    return final_genre


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
                f"High={features['high_ratio']:.4f} | "
                f"Centroid={features['avg_centroid']:.0f}Hz"
            )

    filename_hint = detect_genre_from_filename(filename)
    if filename_hint != "default":
        print(f"[genre_detector] Dica do nome do arquivo: {filename_hint}")

    scores = heuristic_scores(features, filename)
    print(f"[genre_detector] Scores: {_score_summary(scores)}")

    heuristic = heuristic_genre(features, filename)
    print(f"[genre_detector] Heurística: {heuristic}")

    final_genre = heuristic

    # Se não tem análise boa, o nome manda.
    if not features and filename_hint != "default":
        final_genre = filename_hint

    # Claude decide quando disponível, mas com guardrails depois.
    elif ANTHROPIC_AVAILABLE and features:
        enhanced_filename = filename
        if filename_hint != "default":
            enhanced_filename = f"{filename} [filename_hint: {filename_hint}]"

        final_genre = claude_classify_genre(enhanced_filename, features, heuristic, scores)

    elif heuristic == "default" and filename_hint != "default":
        final_genre = filename_hint

    final_genre = _final_guardrails(final_genre, heuristic, filename_hint, features, scores)

    if final_genre not in SUPPORTED_GENRES:
        final_genre = "default"

    print(f"[genre_detector] Gênero final: {final_genre}")
    return final_genre


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
