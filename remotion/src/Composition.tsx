import { useEffect, useState } from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  staticFile,
  useVideoConfig,
  Video,
} from "remotion";

/**
 * Composition.tsx — v11 DARK PROFESSIONAL
 * ----------------------------------------
 * Estilo: canal de phonk/trap/electronic profissional.
 * Referência: visual escuro, logo central como foco único,
 * glow neon reativo ao beat, fundo quase invisível.
 *
 * O que foi REMOVIDO vs v10:
 * - 72 partículas flutuantes (pesado + poluído)
 * - 8 orbit dots
 * - 6 rings simultâneos → agora 1 ring limpo
 * - Starburst (spikes)
 * - Scanlines
 * - Color wash excessivo
 * - Camera shake agressivo
 * - Glitch RGB triplo → agora glitch sutil 1 camada
 *
 * O que ficou / melhorou:
 * - Logo como protagonista absoluto
 * - 1 ring neon reativo ao beat
 * - Glow difuso de fundo (aura)
 * - Impact wave limpo no drop
 * - Vinheta forte mantendo o fundo escuro
 * - Texto mínimo e elegante
 * - Borda neon respirando
 * - Performance: ~80% menos elementos no DOM
 */

type AudioPayload =
  | number[]
  | {
      rms?: number[];
      audio_data?: number[];
      beats?: number[];
      bass_hits?: number[];
      snare_hits?: number[];
      beat_intensities?: number[];
      drop_time?: number | null;
      duration?: number;
      bpm?: number;
      title?: string;
      style?: string;
    };

const clamp = (v: number, min = 0, max = 1) =>
  Math.max(min, Math.min(max, v));

const smooth = (arr: number[], index: number, radius = 3) => {
  if (!arr.length) return 0;
  let total = 0;
  let count = 0;
  for (let i = -radius; i <= radius; i++) {
    const v = arr[index + i];
    if (typeof v === "number" && Number.isFinite(v)) {
      total += v;
      count++;
    }
  }
  return count ? total / count : 0;
};

const splitTitle = (title: string) => {
  const clean = (title || "DJ DARKMARK")
    .trim()
    .toUpperCase()
    .replace(/_/g, " ");
  const words = clean.split(/\s+/).filter(Boolean);
  if (words.length <= 2) return [clean, ""];
  const mid = Math.ceil(words.length / 2);
  return [words.slice(0, mid).join(" "), words.slice(mid).join(" ")];
};

const GENRE_TAGS: Record<string, string> = {
  phonk:      "PHONK",
  trap:       "TRAP",
  dark:       "DARK",
  electronic: "ELECTRONIC",
  lofi:       "LO-FI",
  metal:      "METAL",
  rock:       "ROCK",
  indie:      "INDIE",
  cinematic:  "CINEMATIC",
  funk:       "FUNK",
  default:    "DJ DARKMARK",
};

// Paleta contida — neon só onde precisa
const GENRE_COLORS: Record<
  string,
  { primary: string; secondary: string; accent: string }
> = {
  phonk:      { primary: "#7B00FF", secondary: "#00EEFF", accent: "#CC00FF" },
  trap:       { primary: "#0099FF", secondary: "#00EEFF", accent: "#FF00CC" },
  dark:       { primary: "#5500BB", secondary: "#8800FF", accent: "#FF0033" },
  electronic: { primary: "#00EEFF", secondary: "#0099FF", accent: "#CC00FF" },
  metal:      { primary: "#FF4400", secondary: "#FF0033", accent: "#AA00FF" },
  rock:       { primary: "#FF6600", secondary: "#FF0033", accent: "#AA00FF" },
  lofi:       { primary: "#FF9933", secondary: "#FF6600", accent: "#BB33FF" },
  indie:      { primary: "#FFCC66", secondary: "#FF7700", accent: "#BB33FF" },
  cinematic:  { primary: "#FFAA33", secondary: "#FF6600", accent: "#AA00FF" },
  funk:       { primary: "#FF6600", secondary: "#FF3300", accent: "#AA00FF" },
  default:    { primary: "#7B00FF", secondary: "#00EEFF", accent: "#CC00FF" },
};

export const MyComposition = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames, width, height } = useVideoConfig();

  const [rms, setRms]                         = useState<number[]>([]);
  const [beats, setBeats]                     = useState<number[]>([]);
  const [bassHits, setBassHits]               = useState<number[]>([]);
  const [snareHits, setSnareHits]             = useState<number[]>([]);
  const [beatIntensities, setBeatIntensities] = useState<number[]>([]);
  const [dropTime, setDropTime]               = useState<number | null>(null);
  const [songTitle, setSongTitle]             = useState("DJ darkMark");
  const [songStyle, setSongStyle]             = useState("phonk");

  useEffect(() => {
    fetch(staticFile("audio_data.json"))
      .then((r) => r.json())
      .then((data: AudioPayload) => {
        if (Array.isArray(data)) {
          setRms(data);
          return;
        }
        setRms(
          Array.isArray(data.rms)
            ? data.rms
            : Array.isArray(data.audio_data)
              ? data.audio_data
              : []
        );
        setBeats(Array.isArray(data.beats) ? data.beats : []);
        setBassHits(Array.isArray(data.bass_hits) ? data.bass_hits : []);
        setSnareHits(Array.isArray(data.snare_hits) ? data.snare_hits : []);
        setBeatIntensities(
          Array.isArray(data.beat_intensities) ? data.beat_intensities : []
        );
        setDropTime(
          typeof data.drop_time === "number" ? data.drop_time : null
        );
        if (typeof data.title === "string" && data.title.trim())
          setSongTitle(data.title);
        if (typeof data.style === "string" && data.style.trim())
          setSongStyle(data.style);
      })
      .catch(() => {});
  }, []);

  // ── Tempo e progresso ──────────────────────────────────────────────────────
  const time     = frame / fps;
  const progress = frame / Math.max(1, durationInFrames - 1);

  const cx     = width / 2;
  const cy     = height * 0.44;
  const minDim = Math.min(width, height);

  // ── Áudio ──────────────────────────────────────────────────────────────────
  const audioIndex = Math.floor(time * 60);
  const rawAudio   = rms[audioIndex] || 0;
  const audioSmooth = clamp(smooth(rms, audioIndex, 3) * 1.4);

  const beatPulse  = clamp((rawAudio - audioSmooth * 0.4) * 6.5);
  const energy     = clamp(audioSmooth * 2.0);
  const bassEnergy = clamp(
    Math.max(...(rms.slice(Math.max(0, audioIndex - 8), audioIndex + 1).length
      ? rms.slice(Math.max(0, audioIndex - 8), audioIndex + 1)
      : [0])) * 1.6
  );

  const beatNear  = beats.some((b) => Math.abs(time - b) < 0.05);
  const bassNear  = bassHits.some((b) => Math.abs(time - b) < 0.08);
  const snareNear = snareHits.some((s) => Math.abs(time - s) < 0.05);

  const detectedDrop =
    typeof dropTime === "number"
      ? dropTime
      : (durationInFrames / fps) * 0.42;

  const dropNear = clamp(1 - Math.abs(time - detectedDrop) / 1.2);
  const hardDrop = clamp(1 - Math.abs(time - detectedDrop) / 0.18);

  const intensityIdx  = Math.floor(time * 2);
  const beatIntensity = clamp(beatIntensities[intensityIdx] || 0);

  const beatHit  = Math.max(beatNear ? 1 : 0, beatPulse, beatIntensity * 0.6);
  const bassHit  = Math.max(bassNear ? 1 : 0, bassEnergy);
  const snareHit = snareNear ? 1 : 0;
  const dropHit  = Math.max(
    dropNear,
    bassEnergy > 0.5 ? bassEnergy * 0.6 : 0
  );

  // ── Fases ──────────────────────────────────────────────────────────────────
  // Fade-in nos primeiros 0.8s
  const fadeIn  = clamp(time / 0.8);
  // Fade-out nos últimos 1s
  const fadeOut = clamp(1 - (time - (durationInFrames / fps - 1.0)) / 1.0);
  const masterOpacity = Math.min(fadeIn, fadeOut);

  // ── Efeitos visuais ────────────────────────────────────────────────────────
  // Zoom contido — só respira levemente
  const zoom = 1 + beatHit * 0.008 + bassHit * 0.015 + hardDrop * 0.08;

  // Câmera: só treme no hard drop, sutil
  const shake  = hardDrop * 10 + bassHit * 2.5;
  const shakeX = Math.sin(frame * 1.1) * shake;
  const shakeY = Math.cos(frame * 0.9) * shake;

  // Logo: escala reativa ao beat
  const logoScale =
    1 + beatHit * 0.06 + bassHit * 0.12 + hardDrop * 0.32 + dropHit * 0.05;

  // Rotação mínima — profissional, não cartoon
  const logoRotate =
    Math.sin(frame * 0.018) * 0.8 +
    hardDrop * Math.sin(frame * 0.7) * 2.5;

  // Glow: base baixa, explode no beat
  const glowBase = 20 + energy * 40 + bassHit * 30 + dropHit * 70 + hardDrop * 140;

  // Flash branco no hard drop — rápido e limpo
  const flashOpacity = clamp(hardDrop * 0.65 + snareHit * 0.15);

  // Glitch: só no hard drop, 1 camada
  const glitchActive = hardDrop > 0.12 || bassHit > 0.72;
  const chromaShift  = glitchActive ? 2 + bassHit * 6 + hardDrop * 18 : 0;

  // Brightness do fundo: começa escuro, sobe levemente no drop
  const bgBrightness = 0.55 + energy * 0.18 + dropHit * 0.15;

  const colors = GENRE_COLORS[songStyle] ?? GENRE_COLORS.default;
  const { primary: C1, secondary: C2, accent: C3 } = colors;
  const genreTag   = GENRE_TAGS[songStyle] ?? GENRE_TAGS.default;
  const [line1, line2] = splitTitle(songTitle);

  // Ring size: pulsa no beat
  const ringSize =
    minDim * 0.36 * (1 + beatHit * 0.06 + bassHit * 0.12 + hardDrop * 0.35);

  // Impact wave: frame relativo ao beat/drop
  const waveProgress = ((frame * 1.4) % 80) / 80;
  const wavePower    = clamp(beatHit * 0.5 + bassHit * 0.6 + hardDrop * 1.2);

  return (
    <AbsoluteFill
      style={{
        background: "#050005",
        overflow: "hidden",
        opacity: masterOpacity,
      }}
    >
      {/* ── FUNDO (vídeo base) ─────────────────────────────────────────────── */}
      <AbsoluteFill
        style={{
          transform: `translate(${shakeX}px, ${shakeY}px) scale(${zoom * 1.04})`,
          filter: `brightness(${bgBrightness}) contrast(1.15) saturate(${0.9 + energy * 0.35})`,
        }}
      >
        <Video
          src={staticFile("input.mp4")}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </AbsoluteFill>

      {/* ── VINHETA PESADA — mantém tudo escuro ───────────────────────────── */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse 60% 52% at 50% 42%, transparent 0%, rgba(0,0,0,0.25) 30%, rgba(0,0,0,0.82) 68%, rgba(0,0,0,0.97) 100%)",
        }}
      />

      {/* ── COR DE AMBIENTE — muito sutil ─────────────────────────────────── */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse 55% 45% at 50% 42%, ${C1}30 0%, transparent 70%)`,
          mixBlendMode: "screen",
          opacity: 0.08 + energy * 0.10 + dropHit * 0.14,
        }}
      />

      {/* ── FLASH DO DROP ─────────────────────────────────────────────────── */}
      {flashOpacity > 0.01 && (
        <AbsoluteFill
          style={{
            background: `radial-gradient(circle at 50% 42%, rgba(255,255,255,${
              flashOpacity * 0.7
            }) 0%, ${C1}88 22%, transparent 60%)`,
            opacity: flashOpacity,
            mixBlendMode: "screen",
          }}
        />
      )}

      {/* ── AURA DIFUSA DO LOGO ────────────────────────────────────────────── */}
      <img
        src={staticFile("logo.png")}
        style={{
          position: "absolute",
          left: cx,
          top: cy,
          width: minDim * 0.65 * logoScale,
          height: "auto",
          filter: `blur(${16 + bassHit * 18 + hardDrop * 36}px) brightness(3.5)`,
          opacity: 0.12 + bassHit * 0.08 + hardDrop * 0.22,
          mixBlendMode: "screen",
          transform: "translate(-50%, -50%)",
          pointerEvents: "none",
        }}
      />

      {/* ── RING NEON — 1 único, reativo ──────────────────────────────────── */}
      <div
        style={{
          position: "absolute",
          left: cx,
          top: cy,
          width: ringSize,
          height: ringSize,
          borderRadius: "50%",
          border: `${1.5 + bassHit * 2 + hardDrop * 5}px solid ${C1}`,
          boxShadow: `0 0 ${glowBase}px ${C1}, 0 0 ${glowBase * 0.5}px ${C2}`,
          opacity: 0.55 + beatHit * 0.25 + hardDrop * 0.35,
          transform: `translate(-50%, -50%) rotate(${frame * 0.22}deg)`,
        }}
      />

      {/* ── IMPACT WAVE — limpa, só quando há energia ─────────────────────── */}
      {wavePower > 0.05 && (
        <div
          style={{
            position: "absolute",
            left: cx,
            top: cy,
            width:  minDim * 0.28 + waveProgress * minDim * 1.1,
            height: minDim * 0.28 + waveProgress * minDim * 1.1,
            borderRadius: "50%",
            border: `${1 + hardDrop * 2}px solid ${C2}`,
            opacity: (1 - waveProgress) * wavePower * 0.7,
            boxShadow: `0 0 ${20 + hardDrop * 60}px ${C2}`,
            transform: "translate(-50%, -50%)",
          }}
        />
      )}

      {/* ── GLITCH — 1 camada, sutil ──────────────────────────────────────── */}
      {glitchActive && chromaShift > 0 && (
        <img
          src={staticFile("logo.png")}
          style={{
            position: "absolute",
            left: cx - chromaShift,
            top: cy,
            width: minDim * 0.46,
            height: "auto",
            opacity: 0.15 + hardDrop * 0.18,
            mixBlendMode: "screen",
            transform: `translate(-50%, -50%) scale(${logoScale * 1.02}) rotate(${
              logoRotate - 1
            }deg)`,
            filter: `drop-shadow(0 0 ${glowBase * 0.4}px ${C3}) brightness(1.4)`,
            pointerEvents: "none",
          }}
        />
      )}

      {/* ── LOGO PRINCIPAL ────────────────────────────────────────────────── */}
      <img
        src={staticFile("logo.png")}
        style={{
          position: "absolute",
          left: cx,
          top: cy,
          width: minDim * 0.46,
          height: "auto",
          transform: `translate(-50%, -50%) scale(${logoScale}) rotate(${logoRotate}deg)`,
          filter: `
            drop-shadow(0 0 ${glowBase}px ${C1})
            drop-shadow(0 0 ${glowBase * 1.2}px ${C2})
            brightness(${1.05 + energy * 0.2 + hardDrop * 0.45})
            contrast(${1.1 + beatHit * 0.12})
          `,
          opacity: 0.98,
          pointerEvents: "none",
        }}
      />

      {/* ── TEXTO INFERIOR — minimalista ──────────────────────────────────── */}
      <div
        style={{
          position: "absolute",
          left: "50%",
          bottom: height * 0.055,
          transform: `translateX(-50%) scale(${1 + beatHit * 0.008 + hardDrop * 0.016})`,
          width: "80%",
          textAlign: "center",
          zIndex: 10,
        }}
      >
        {/* Tag de gênero — pequena, elegante */}
        <div
          style={{
            display: "inline-block",
            color: C2,
            border: `1px solid ${C2}66`,
            background: `${C2}12`,
            padding: "3px 10px",
            borderRadius: 4,
            fontSize: 15,
            fontWeight: 800,
            letterSpacing: 5,
            textShadow: `0 0 10px ${C2}`,
            marginBottom: 7,
            opacity: 0.88,
          }}
        >
          {genreTag}
        </div>

        {/* Título linha 1 */}
        <div
          style={{
            color: "#ffffff",
            fontSize: 42,
            fontWeight: 900,
            lineHeight: 1.05,
            letterSpacing: 1.5,
            textTransform: "uppercase",
            textShadow: `0 0 8px ${C1}, 0 0 20px ${C1}aa, 2px 2px 0 #000`,
            WebkitTextStroke: "1px rgba(0,0,0,0.8)",
          }}
        >
          {line1}
        </div>

        {/* Título linha 2 */}
        {line2 && (
          <div
            style={{
              color: "#e8e8ff",
              fontSize: 40,
              fontWeight: 800,
              lineHeight: 1.05,
              letterSpacing: 1.2,
              textTransform: "uppercase",
              textShadow: `0 0 7px ${C2}, 0 0 18px ${C2}aa, 2px 2px 0 #000`,
              WebkitTextStroke: "1px rgba(0,0,0,0.75)",
            }}
          >
            {line2}
          </div>
        )}
      </div>

      {/* ── BORDA NEON — respira, não domina ──────────────────────────────── */}
      <AbsoluteFill
        style={{
          border: `${1.5 + hardDrop * 3}px solid ${C1}${Math.floor(
            clamp(0.06 + beatHit * 0.07 + hardDrop * 0.28) * 255
          )
            .toString(16)
            .padStart(2, "0")}`,
          boxShadow: `inset 0 0 ${30 + glowBase * 0.25}px ${C1}${Math.floor(
            clamp(0.05 + hardDrop * 0.18) * 255
          )
            .toString(16)
            .padStart(2, "0")}`,
          pointerEvents: "none",
        }}
      />

      {/* ── FADE FINAL ────────────────────────────────────────────────────── */}
      <AbsoluteFill
        style={{
          background: "#000",
          opacity: progress > 0.97 ? (progress - 0.97) / 0.03 : 0,
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
};

export default MyComposition;
