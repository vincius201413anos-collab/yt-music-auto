"""
genre_detector.py — Detecção automática de gênero musical por análise acústica.

Analisa o áudio usando librosa para extrair características acústicas reais
(BPM, energia, espectro, graves, etc.) e usa Claude como árbitro final.

Fluxo:
    1. Extrai features acústicas com librosa
    2. Aplica regras heurísticas para candidatos iniciais
    3. Claude recebe os dados e decide o gênero final
    4. Fallback: nome do arquivo (keywords) se tudo falhar
"""

import os
import math
import json
import re
from pathlib import Path

# ══════════════════════════════════════════════════════════════════════
# IMPORTS COM FALLBACK GRACIOSO
# ══════════════════════════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════════════════════════
# GÊNEROS SUPORTADOS (devem bater com edit_profiles.py)
# ══════════════════════════════════════════════════════════════════════

SUPPORTED_GENRES = [
    "phonk", "trap", "rock", "metal", "electronic",
    "cinematic", "lofi", "indie", "pop", "funk", "dark", "default"
]

# ══════════════════════════════════════════════════════════════════════
# KEYWORDS NO NOME DO ARQUIVO (fallback)
# ══════════════════════════════════════════════════════════════════════

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
    "metal", "rock", "phonk", "trap", "electronic",
    "cinematic", "dark", "indie", "lofi", "pop", "funk"
]


# ══════════════════════════════════════════════════════════════════════
# EXTRAÇÃO DE FEATURES ACÚSTICAS
# ══════════════════════════════════════════════════════════════════════

def extract_acoustic_features(audio_path: str) -> dict | None:
    """
    Extrai características acústicas do áudio usando librosa.
    Retorna dict com métricas numéricas, ou None se falhar.
    """
    if not LIBROSA_AVAILABLE:
        return None

    try:
        # Carrega apenas os primeiros 90s para agilizar (suficiente para gênero)
        y, sr = librosa.load(audio_path, duration=90, mono=True)

        # ── BPM ──────────────────────────────────────────────────────
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm = float(tempo)

        # ── ENERGIA RMS ──────────────────────────────────────────────
        rms = librosa.feature.rms(y=y)
        avg_energy = float(np.mean(rms))
        energy_var = float(np.var(rms))   # variância = dinâmica

        # ── SPECTRAL CENTROID (brilho do som) ────────────────────────
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        avg_centroid = float(np.mean(centroid))

        # ── SPECTRAL ROLLOFF (quanto de energia está nas altas freq.) ─
        rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
        avg_rolloff = float(np.mean(rolloff))

        # ── ZERO CROSSING RATE (quanto de ruído/noise) ───────────────
        zcr = librosa.feature.zero_crossing_rate(y)
        avg_zcr = float(np.mean(zcr))

        # ── CHROMA (tonalidade / harmonia) ───────────────────────────
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_std = float(np.std(chroma))      # variação harmônica
        chroma_mean = float(np.mean(chroma))

        # ── MFCC (timbre) ────────────────────────────────────────────
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_means = [float(np.mean(mfcc[i])) for i in range(13)]

        # ── SUB-BASS ENERGY (20-80 Hz) ───────────────────────────────
        stft = np.abs(librosa.stft(y))
        freqs = librosa.fft_frequencies(sr=sr)
        sub_bass_mask = (freqs >= 20) & (freqs <= 80)
        bass_mask     = (freqs >= 80) & (freqs <= 250)
        mid_mask      = (freqs >= 250) & (freqs <= 4000)
        high_mask     = (freqs >= 4000) & (freqs <= 20000)

        total_energy = float(np.mean(stft)) + 1e-9
        sub_bass_ratio = float(np.mean(stft[sub_bass_mask])) / total_energy
        bass_ratio     = float(np.mean(stft[bass_mask]))     / total_energy
        mid_ratio      = float(np.mean(stft[mid_mask]))      / total_energy
        high_ratio     = float(np.mean(stft[high_mask]))     / total_energy

        # ── ONSET STRENGTH (densidade de batidas) ────────────────────
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        onset_mean = float(np.mean(onset_env))
        onset_max  = float(np.max(onset_env))

        # ── DURAÇÃO ──────────────────────────────────────────────────
        duration = float(librosa.get_duration(y=y, sr=sr))

        return {
            "bpm":           round(bpm, 1),
            "avg_energy":    round(avg_energy, 5),
            "energy_var":    round(energy_var, 8),
            "avg_centroid":  round(avg_centroid, 1),
            "avg_rolloff":   round(avg_rolloff, 1),
            "avg_zcr":       round(avg_zcr, 5),
            "chroma_std":    round(chroma_std, 4),
            "chroma_mean":   round(chroma_mean, 4),
            "mfcc_1":        round(mfcc_means[0], 2),
            "mfcc_2":        round(mfcc_means[1], 2),
            "mfcc_3":        round(mfcc_means[2], 2),
            "sub_bass_ratio": round(sub_bass_ratio, 4),
            "bass_ratio":    round(bass_ratio, 4),
            "mid_ratio":     round(mid_ratio, 4),
            "high_ratio":    round(high_ratio, 4),
            "onset_mean":    round(onset_mean, 4),
            "onset_max":     round(onset_max, 4),
            "duration_s":    round(duration, 1),
        }

    except Exception as e:
        print(f"[genre_detector] Erro ao extrair features: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════
# HEURÍSTICAS LOCAIS (candidatos antes do Claude)
# ══════════════════════════════════════════════════════════════════════

def heuristic_genre(features: dict) -> str:
    """
    Aplica regras baseadas em características acústicas conhecidas
    para chegar a um candidato inicial de gênero.
    """
    if not features:
        return "default"

    bpm           = features["bpm"]
    energy        = features["avg_energy"]
    centroid      = features["avg_centroid"]
    sub_bass      = features["sub_bass_ratio"]
    bass          = features["bass_ratio"]
    mid           = features["mid_ratio"]
    high          = features["high_ratio"]
    zcr           = features["avg_zcr"]
    onset_mean    = features["onset_mean"]
    chroma_std    = features["chroma_std"]
    energy_var    = features["energy_var"]

    scores = {g: 0.0 for g in SUPPORTED_GENRES}

    # ── METAL ────────────────────────────────────────────────────────
    # BPM alto, muita energia, muito médio, ZCR alto (distorção)
    if bpm > 150:            scores["metal"] += 2.0
    if bpm > 180:            scores["metal"] += 1.5
    if energy > 0.12:        scores["metal"] += 1.5
    if zcr > 0.12:           scores["metal"] += 2.0   # distorção de guitarra
    if mid > 0.35:           scores["metal"] += 1.5
    if high > 0.15:          scores["metal"] += 1.0

    # ── ROCK ─────────────────────────────────────────────────────────
    if 100 < bpm <= 180:     scores["rock"] += 1.5
    if energy > 0.08:        scores["rock"] += 1.0
    if zcr > 0.08:           scores["rock"] += 1.5
    if mid > 0.28:           scores["rock"] += 1.5
    if chroma_std > 0.18:    scores["rock"] += 1.0   # variação harmônica = acordes

    # ── PHONK ────────────────────────────────────────────────────────
    # BPM 130-160, muito sub-bass/808, energia moderada-alta
    if 128 <= bpm <= 165:    scores["phonk"] += 2.0
    if sub_bass > 0.06:      scores["phonk"] += 2.5
    if bass > 0.20:          scores["phonk"] += 1.5
    if energy > 0.06:        scores["phonk"] += 1.0
    if onset_mean > 2.0:     scores["phonk"] += 1.0

    # ── TRAP ─────────────────────────────────────────────────────────
    # BPM 120-170 (com hi-hats rápidos), 808s pesados
    if 120 <= bpm <= 170:    scores["trap"] += 1.5
    if sub_bass > 0.05:      scores["trap"] += 2.0
    if high > 0.12:          scores["trap"] += 1.5   # hi-hats
    if energy > 0.05:        scores["trap"] += 1.0

    # ── ELECTRONIC ───────────────────────────────────────────────────
    # BPM 120-145, centroid alto (sintetizadores), muito agudo
    if 120 <= bpm <= 145:    scores["electronic"] += 1.5
    if centroid > 3000:      scores["electronic"] += 2.0
    if high > 0.18:          scores["electronic"] += 2.0
    if energy_var > 1e-5:    scores["electronic"] += 1.5  # drops = muita variação

    # ── LOFI ─────────────────────────────────────────────────────────
    # BPM baixo, energia baixa, pouca variação, centroid baixo
    if bpm < 90:             scores["lofi"] += 2.5
    if energy < 0.04:        scores["lofi"] += 2.0
    if centroid < 2000:      scores["lofi"] += 1.5
    if energy_var < 1e-6:    scores["lofi"] += 1.5   # som constante = lofi

    # ── CINEMATIC ────────────────────────────────────────────────────
    # BPM variável, energia com grandes variações, muito grave+agudo
    if energy_var > 5e-5:    scores["cinematic"] += 2.0  # dinâmica orquestral
    if chroma_std > 0.20:    scores["cinematic"] += 2.0  # progressão harmônica rica
    if bpm < 100:            scores["cinematic"] += 1.0
    if mid < 0.20:           scores["cinematic"] += 1.0  # menos médio = mais épico

    # ── INDIE ────────────────────────────────────────────────────────
    if 80 <= bpm <= 130:     scores["indie"] += 1.0
    if energy < 0.07:        scores["indie"] += 1.5
    if chroma_std > 0.15:    scores["indie"] += 1.5
    if zcr < 0.08:           scores["indie"] += 1.0   # sem distorção pesada

    # ── POP ──────────────────────────────────────────────────────────
    if 100 <= bpm <= 130:    scores["pop"] += 1.5
    if centroid > 2500:      scores["pop"] += 1.5
    if energy > 0.06:        scores["pop"] += 1.0
    if chroma_std < 0.16:    scores["pop"] += 1.0   # harmonia simples

    # ── FUNK ─────────────────────────────────────────────────────────
    if 90 <= bpm <= 130:     scores["funk"] += 1.5
    if bass > 0.18:          scores["funk"] += 2.0
    if onset_mean > 1.5:     scores["funk"] += 1.5  # groove denso
    if mid > 0.25:           scores["funk"] += 1.0

    # ── DARK ─────────────────────────────────────────────────────────
    if bpm < 120:            scores["dark"] += 1.0
    if energy < 0.06:        scores["dark"] += 1.5
    if centroid < 2200:      scores["dark"] += 1.5
    if chroma_std < 0.12:    scores["dark"] += 1.5  # harmonia fria/estática

    # Remove default da competição por score
    scores.pop("default", None)

    best = max(scores, key=lambda g: scores[g])
    best_score = scores[best]

    if best_score < 2.0:
        return "default"

    return best


# ══════════════════════════════════════════════════════════════════════
# CLASSIFICAÇÃO VIA CLAUDE
# ══════════════════════════════════════════════════════════════════════

def claude_classify_genre(
    filename: str,
    features: dict | None,
    heuristic_candidate: str,
) -> str:
    """
    Usa Claude para classificar o gênero com base nas features acústicas
    e no candidato heurístico. Retorna gênero final como string.
    """
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
Características acústicas extraídas do áudio:
- BPM: {features['bpm']}
- Energia média (RMS): {features['avg_energy']}
- Variação de energia: {features['energy_var']}
- Centroid espectral (brilho): {features['avg_centroid']} Hz
- Rolloff espectral: {features['avg_rolloff']} Hz
- Zero Crossing Rate: {features['avg_zcr']}
- Sub-bass ratio (20-80 Hz): {features['sub_bass_ratio']}
- Bass ratio (80-250 Hz): {features['bass_ratio']}
- Mid ratio (250-4000 Hz): {features['mid_ratio']}
- High ratio (4000+ Hz): {features['high_ratio']}
- Onset strength médio: {features['onset_mean']}
- Variação harmônica (chroma std): {features['chroma_std']}
- Duração: {features['duration_s']}s
"""
        else:
            features_text = "Análise acústica não disponível."

        resp = client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-opus-4-7"),
            max_tokens=60,
            system=(
                "You are an expert music genre classifier. "
                "You receive acoustic features extracted from an audio file "
                "and must classify it into exactly one genre. "
                "Reply with ONLY the genre name, nothing else. "
                f"Choose from: {', '.join(SUPPORTED_GENRES)}"
            ),
            messages=[{
                "role": "user",
                "content": (
                    f"File name: {filename}\n"
                    f"Heuristic candidate: {heuristic_candidate}\n"
                    f"{features_text}\n"
                    f"Based on these acoustic features, what is the most accurate genre? "
                    f"Reply with ONLY one word from: {', '.join(SUPPORTED_GENRES)}"
                ),
            }],
        )

        raw = resp.content[0].text.strip().lower()
        # Garante que a resposta é um gênero válido
        for g in SUPPORTED_GENRES:
            if g in raw:
                print(f"[genre_detector] Claude classificou: {g}")
                return g

        print(f"[genre_detector] Claude retornou '{raw}' — usando heurística: {heuristic_candidate}")
        return heuristic_candidate

    except Exception as e:
        print(f"[genre_detector] Erro no Claude: {e} — usando heurística: {heuristic_candidate}")
        return heuristic_candidate


# ══════════════════════════════════════════════════════════════════════
# FALLBACK: NOME DO ARQUIVO
# ══════════════════════════════════════════════════════════════════════

def detect_genre_from_filename(filename: str) -> str:
    """Detecta gênero por keywords no nome do arquivo (fallback)."""
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


# ══════════════════════════════════════════════════════════════════════
# FUNÇÃO PRINCIPAL
# ══════════════════════════════════════════════════════════════════════

def detect_genre(audio_path: str) -> str:
    """
    Detecta o gênero musical de um arquivo de áudio.

    Prioridade:
        1. Análise acústica (librosa) + Claude
        2. Heurísticas acústicas sozinhas
        3. Nome do arquivo (keywords)
        4. "default"

    Args:
        audio_path: Caminho para o arquivo de áudio (.mp3, .wav, etc.)

    Returns:
        str: gênero detectado (ex: "phonk", "trap", "rock", ...)
    """
    filename = Path(audio_path).name
    print(f"[genre_detector] Analisando: {filename}")

    # ── 1. Extrai features acústicas ─────────────────────────────────
    features = None
    if LIBROSA_AVAILABLE and os.path.exists(audio_path):
        print("[genre_detector] Extraindo features acústicas...")
        features = extract_acoustic_features(audio_path)
        if features:
            print(f"[genre_detector] BPM={features['bpm']} | "
                  f"Energia={features['avg_energy']:.4f} | "
                  f"Sub-bass={features['sub_bass_ratio']:.4f} | "
                  f"Centroid={features['avg_centroid']:.0f}Hz")

    # ── 2. Heurísticas ───────────────────────────────────────────────
    heuristic = heuristic_genre(features) if features else "default"
    print(f"[genre_detector] Heurística: {heuristic}")

    # ── 3. Nome do arquivo como dica adicional ───────────────────────
    filename_hint = detect_genre_from_filename(filename)
    if filename_hint != "default":
        print(f"[genre_detector] Dica do nome do arquivo: {filename_hint}")
        # Se nome confirma heurística, mais confiança
        if filename_hint == heuristic:
            print(f"[genre_detector] Nome confirma heurística → {heuristic}")
            return heuristic

    # ── 4. Claude como árbitro final ─────────────────────────────────
    if ANTHROPIC_AVAILABLE and features:
        # Passa a dica do nome pro Claude como contexto adicional
        enhanced_filename = filename
        if filename_hint != "default":
            enhanced_filename = f"{filename} [hint: {filename_hint}]"

        final_genre = claude_classify_genre(enhanced_filename, features, heuristic)
        print(f"[genre_detector] Gênero final (Claude): {final_genre}")
        return final_genre

    # ── 5. Fallback: heurística ou nome ──────────────────────────────
    if heuristic != "default":
        print(f"[genre_detector] Usando heurística: {heuristic}")
        return heuristic

    if filename_hint != "default":
        print(f"[genre_detector] Usando nome do arquivo: {filename_hint}")
        return filename_hint

    print("[genre_detector] Nenhum gênero detectado — usando default")
    return "default"


def detect_genre_multi(audio_path: str) -> list[str]:
    """
    Retorna lista de gêneros detectados (principal + secundários possíveis).
    Útil para metadata/tags.
    """
    primary = detect_genre(audio_path)

    # Gêneros relacionados por afinidade
    related = {
        "phonk":      ["dark", "trap"],
        "trap":       ["phonk", "dark"],
        "rock":       ["indie", "metal"],
        "metal":      ["rock", "dark"],
        "electronic": ["pop", "cinematic"],
        "cinematic":  ["electronic", "dark"],
        "lofi":       ["indie", "cinematic"],
        "indie":      ["rock", "lofi"],
        "pop":        ["electronic", "indie"],
        "funk":       ["pop", "electronic"],
        "dark":       ["phonk", "cinematic"],
        "default":    [],
    }

    secondary = related.get(primary, [])
    return [primary] + secondary


# ══════════════════════════════════════════════════════════════════════
# DEBUG / STANDALONE
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python genre_detector.py <caminho_do_audio>")
        sys.exit(1)

    path = sys.argv[1]
    print(f"\n{'='*50}")
    print(f"Analisando: {path}")
    print(f"{'='*50}")

    genre = detect_genre(path)
    genres = detect_genre_multi(path)

    print(f"\n✅ Gênero principal: {genre}")
    print(f"📋 Gêneros (com secundários): {genres}")
