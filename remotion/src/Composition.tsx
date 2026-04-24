import { useEffect, useMemo, useState } from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  staticFile,
  useVideoConfig,
  Video,
} from "remotion";

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════
type AudioPayload =
  | number[]
  | {
      rms?: number[];
      audio_data?: number[];
      beats?: number[];
      bass_hits?: number[];
      beat_intensities?: number[];
      drop_time?: number | null;
      duration?: number;
      bpm?: number;
      title?: string;
      style?: string;
    };

// ══════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════
const clamp = (v: number, min = 0, max = 1) => Math.max(min, Math.min(max, v));

const smooth = (arr: number[], index: number, radius = 2) => {
  if (!arr.length) return 0;
  let total = 0, count = 0;
  for (let i = -radius; i <= radius; i++) {
    const v = arr[index + i];
    if (typeof v === "number" && Number.isFinite(v)) { total += v; count++; }
  }
  return count ? total / count : 0;
};

const splitTitle = (title: string) => {
  const clean = title.trim().toUpperCase().replace(/_/g, " ");
  const words = clean.split(/\s+/);
  if (words.length <= 2) return [clean, ""];
  const mid = Math.ceil(words.length / 2);
  return [words.slice(0, mid).join(" "), words.slice(mid).join(" ")];
};

const GENRE_TAGS: Record<string, string> = {
  phonk: "◈ PHONK MODE ◈",
  trap: "◈ TRAP ENERGY ◈",
  dark: "◈ DARK VIBES ◈",
  electronic: "◈ ELECTRONIC ◈",
  lofi: "◈ LO-FI CHILL ◈",
  metal: "◈ METAL RAGE ◈",
  rock: "◈ ROCK ENERGY ◈",
  indie: "◈ INDIE SOUL ◈",
  cinematic: "◈ CINEMATIC ◈",
  funk: "◈ FUNK GROOVE ◈",
  default: "◈ DARKMARK ◈",
};

const GENRE_COLORS: Record<string, { primary: string; secondary: string; accent: string }> = {
  phonk:      { primary: "#8B00FF", secondary: "#00FFEE", accent: "#FF003C" },
  trap:       { primary: "#00CCFF", secondary: "#FF00FF", accent: "#00FFEE" },
  dark:       { primary: "#6600CC", secondary: "#9900FF", accent: "#FF003C" },
  electronic: { primary: "#00FFEE", secondary: "#00CCFF", accent: "#FF00FF" },
  metal:      { primary: "#FF5500", secondary: "#FF003C", accent: "#CC00FF" },
  rock:       { primary: "#FF8800", secondary: "#FF003C", accent: "#CC00FF" },
  lofi:       { primary: "#FFAA44", secondary: "#FF7700", accent: "#CC44FF" },
  indie:      { primary: "#FFDD88", secondary: "#FF8800", accent: "#CC44FF" },
  cinematic:  { primary: "#FFBB44", secondary: "#FF8800", accent: "#CC00FF" },
  funk:       { primary: "#FF8800", secondary: "#FF4400", accent: "#CC00FF" },
  default:    { primary: "#8B00FF", secondary: "#00FFEE", accent: "#FF003C" },
};

// ══════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPAL
// ══════════════════════════════════════════════════════════════
export const MyComposition = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // ── Estado de áudio ────────────────────────────────────────
  const [rms, setRms] = useState<number[]>([]);
  const [beats, setBeats] = useState<number[]>([]);
  const [bassHits, setBassHits] = useState<number[]>([]);
  const [beatIntensities, setBeatIntensities] = useState<number[]>([]);
  const [dropTime, setDropTime] = useState<number | null>(null);
  const [songTitle, setSongTitle] = useState<string>("DJ darkMark");
  const [songStyle, setSongStyle] = useState<string>("phonk");

  useEffect(() => {
    fetch(staticFile("audio_data.json"))
      .then((r) => r.json())
      .then((data: AudioPayload) => {
        if (Array.isArray(data)) { setRms(data); return; }
        setRms(Array.isArray(data.rms) ? data.rms : Array.isArray(data.audio_data) ? data.audio_data : []);
        setBeats(Array.isArray(data.beats) ? data.beats : []);
        setBassHits(Array.isArray(data.bass_hits) ? data.bass_hits : []);
        setBeatIntensities(Array.isArray(data.beat_intensities) ? data.beat_intensities : []);
        setDropTime(typeof data.drop_time === "number" ? data.drop_time : null);
        if (typeof data.title === "string" && data.title) setSongTitle(data.title);
        if (typeof data.style === "string" && data.style) setSongStyle(data.style);
      })
      .catch(() => {});
  }, []);

  // ── Tempo e progresso ──────────────────────────────────────
  const time = frame / fps;
  const progress = frame / Math.max(1, durationInFrames - 1);

  // ── Extração de energia do áudio ───────────────────────────
  const audioIndex = Math.floor(time * 60);
  const rawAudio = rms[audioIndex] || 0;
  const audioValue = clamp(smooth(rms, audioIndex, 3) * 1.5);

  const recentValues = useMemo(() => {
    const values = rms.slice(Math.max(0, audioIndex - 8), audioIndex + 1);
    return values.length ? values : [0];
  }, [rms, audioIndex]);

  const recentPeak = clamp(Math.max(...recentValues) * 1.7);
  const beatPulse  = clamp((rawAudio - audioValue * 0.35) * 7.0);
  const energy     = clamp(audioValue * 2.4);
  const bassEnergy = clamp(recentPeak * 1.9);

  // ── Detecção de eventos ────────────────────────────────────
  const beatNear = beats.some((b) => Math.abs(time - b) < 0.07);
  const bassNear = bassHits.some((b) => Math.abs(time - b) < 0.10);
  const dropNear = typeof dropTime === "number"
    ? clamp(1 - Math.abs(time - dropTime) / 1.5)
    : 0;

  const beatHit = beatNear ? 1 : beatPulse;
  const bassHit = bassNear ? 1 : bassEnergy;
  const dropFromEnergy = recentPeak > 0.52 || beatPulse > 0.62 ? recentPeak : 0;
  const dropHit = Math.max(dropNear, dropFromEnergy * 0.7);

  const intensity = clamp(energy * 0.65 + beatHit * 0.24 + bassHit * 0.22 + dropHit * 0.78);

  // ── Parâmetros visuais ─────────────────────────────────────
  const shake     = dropHit * 28 + bassHit * 13 + beatHit * 5;
  const zoom      = 1 + beatHit * 0.022 + bassHit * 0.038 + dropHit * 0.092;
  const logoScale = 1 + beatHit * 0.14 + bassHit * 0.22 + dropHit * 0.56;
  const logoRotate = Math.sin(frame * 0.038) * (3.2 + beatHit * 2.4) + frame * 0.005;
  const ringScale = 1 + beatHit * 0.10 + bassHit * 0.16 + dropHit * 0.42;
  const glow      = 70 + energy * 120 + beatHit * 100 + dropHit * 240;

  const flashOpacity  = clamp(dropHit * 0.82 + beatHit * 0.16 + bassHit * 0.12);
  const glitch        = dropHit > 0.16 || beatHit > 0.52 || bassHit > 0.58;
  const chromaShift   = bassHit > 0.20 ? 4 + bassHit * 16 + dropHit * 36 : 0;

  const cameraX = Math.sin(frame * 0.84) * shake;
  const cameraY = Math.cos(frame * 1.26) * shake;

  // ── Cores por gênero ───────────────────────────────────────
  const colors = GENRE_COLORS[songStyle] || GENRE_COLORS.default;
  const { primary: C1, secondary: C2, accent: C3 } = colors;
  const genreTag = GENRE_TAGS[songStyle] || GENRE_TAGS.default;
  const [titleLine1, titleLine2] = splitTitle(songTitle);

  // ══════════════════════════════════════════════════════════
  // RENDER
  // ══════════════════════════════════════════════════════════
  return (
    <AbsoluteFill style={{ background: "#000", overflow: "hidden" }}>

      {/* ── 1. VÍDEO BASE COM CÂMERA REATIVA ─────────────────── */}
      <AbsoluteFill style={{
        transform: `translate(${cameraX}px, ${cameraY}px) scale(${zoom})`,
        filter: `brightness(${0.68 + intensity * 0.42}) contrast(${1.22 + intensity * 0.30}) saturate(${1.15 + intensity * 0.60})`,
      }}>
        <Video
          src={staticFile("input.mp4")}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </AbsoluteFill>

      {/* ── 2. VINHETA CINEMATOGRÁFICA PESADA ────────────────── */}
      <AbsoluteFill style={{
        background: "radial-gradient(ellipse 70% 75% at 50% 48%, rgba(0,0,0,0) 0%, rgba(0,0,0,0.20) 30%, rgba(0,0,0,0.72) 62%, rgba(0,0,0,0.97) 100%)",
      }} />

      {/* ── 3. COLOR GRADE NEON REATIVO ───────────────────────── */}
      <AbsoluteFill style={{
        background: `linear-gradient(145deg, ${C3}30 0%, ${C1}28 50%, ${C2}20 100%)`,
        mixBlendMode: "screen",
        opacity: 0.18 + energy * 0.20 + dropHit * 0.26,
      }} />

      {/* ── 4. AURA DE FUMAÇA DO LOGO ────────────────────────── */}
      <div style={{
        position: "absolute",
        left: "50%",
        top: "48%",
        width: 800 + bassHit * 250 + dropHit * 450,
        height: 800 + bassHit * 250 + dropHit * 450,
        borderRadius: "50%",
        background: `radial-gradient(circle, ${C1}55 0%, ${C3}25 28%, ${C2}18 48%, transparent 72%)`,
        transform: `translate(-50%, -50%) scale(${1 + beatHit * 0.10 + dropHit * 0.28})`,
        filter: `blur(${30 + dropHit * 50}px)`,
        opacity: 0.55 + bassHit * 0.25 + dropHit * 0.35,
      }} />

      {/* ── 5. ANÉIS EXTERNOS ROTATIVOS (TÚNEL HIPNÓTICO) ────── */}
      {[0,1,2,3,4,5,6,7,8].map((i) => {
        const baseSize = 240 + i * 135;
        const size = baseSize * ringScale + dropHit * 80;
        const dir  = i % 2 ? 1 : -1;
        const spd  = (0.85 - i * 0.085) * dir * 0.38;
        const ringColors = [C1, C2, C3, C1, C2, C3, C1, C2, C3];
        const col  = ringColors[i];
        const bw   = Math.max(0.8, 3.5 - i * 0.32);

        return (
          <div key={`ring-${i}`} style={{
            position: "absolute",
            left: "50%",
            top: "48%",
            width: size,
            height: size,
            borderRadius: "50%",
            border: `${bw}px solid ${col}`,
            boxShadow: `0 0 ${glow * (1 - i * 0.09)}px ${col}, inset 0 0 ${glow * 0.18}px ${col}`,
            transform: `translate(-50%, -50%) rotate(${frame * spd}deg)`,
            opacity: Math.max(0.05, (0.62 - i * 0.055) + beatHit * 0.18 + dropHit * 0.24),
          }} />
        );
      })}

      {/* ── 6. RAIOS/SPIKES AO REDOR DO LOGO (STARBURST) ──────── */}
      {[...Array(12)].map((_, i) => {
        const angle = (i / 12) * 360 + frame * 0.18 + beatHit * 8;
        const length = 180 + beatHit * 80 + bassHit * 60 + dropHit * 200;
        const width  = 2 + beatHit * 1.5 + dropHit * 3;
        const col = i % 3 === 0 ? C1 : i % 3 === 1 ? C2 : C3;

        return (
          <div key={`spike-${i}`} style={{
            position: "absolute",
            left: "50%",
            top: "48%",
            width: width,
            height: length,
            background: `linear-gradient(180deg, ${col}ff, ${col}00)`,
            boxShadow: `0 0 ${14 + glow * 0.12}px ${col}`,
            transformOrigin: "50% 0%",
            transform: `translateX(-50%) rotate(${angle}deg)`,
            opacity: 0.5 + beatHit * 0.3 + bassHit * 0.15 + dropHit * 0.4,
          }} />
        );
      })}

      {/* ── 7. ONDAS DE IMPACTO ───────────────────────────────── */}
      {[0,1,2,3,4,5].map((i) => {
        const wave  = ((frame + i * 13) % 72) / 72;
        const power = 0.12 + beatHit * 0.30 + bassHit * 0.24 + dropHit * 0.60;
        const col   = i % 3 === 0 ? C1 : i % 3 === 1 ? C2 : C3;

        return (
          <div key={`wave-${i}`} style={{
            position: "absolute",
            left: "50%",
            top: "48%",
            width: 260 + wave * 1300,
            height: 260 + wave * 1300,
            borderRadius: "50%",
            border: `${1.5 + dropHit * 2}px solid ${col}`,
            opacity: (1 - wave) * power,
            boxShadow: `0 0 ${45 + dropHit * 100}px ${col}`,
            transform: "translate(-50%, -50%)",
          }} />
        );
      })}

      {/* ── 8. ELEMENTOS ORBITANDO O LOGO ─────────────────────── */}
      {[...Array(10)].map((_, i) => {
        const isInner   = i < 5;
        const orbitR    = isInner ? 290 : 420;
        const speed     = isInner ? 0.030 : 0.020;
        const dir       = i % 2 ? 1 : -1;
        const phase     = (i / 10) * Math.PI * 2;
        const angle     = frame * speed * dir + phase;
        const pulse     = 1 + beatHit * 0.35 + dropHit * 0.75;
        const orbitX    = Math.cos(angle) * orbitR * pulse;
        const orbitY    = Math.sin(angle) * orbitR * pulse;
        const col       = i % 3 === 0 ? C1 : i % 3 === 1 ? C2 : C3;
        const size      = (isInner ? 20 : 15) + beatHit * 12 + dropHit * 18;

        return (
          <div key={`orbit-${i}`} style={{
            position: "absolute",
            left: "50%",
            top: "48%",
            width: size,
            height: size,
            borderRadius: "50%",
            background: col,
            boxShadow: `0 0 ${28 + glow * 0.20}px ${col}, 0 0 ${55 + glow * 0.40}px ${col}40`,
            transform: `translate(calc(-50% + ${orbitX}px), calc(-50% + ${orbitY}px)) scale(${1 + beatHit * 0.55 + dropHit * 1.1})`,
            opacity: 0.75 + beatHit * 0.25 + dropHit * 0.3,
          }} />
        );
      })}

      {/* ── 9. GLITCH RGB DO LOGO ─────────────────────────────── */}
      {glitch && chromaShift > 0 && (<>
        <img src={staticFile("logo.png")} style={{
          position: "absolute",
          left: `calc(50% - ${chromaShift}px)`,
          top: "48%",
          width: 530,
          opacity: 0.32 + dropHit * 0.28,
          mixBlendMode: "screen",
          transform: `translate(-50%, -50%) scale(${logoScale * 1.03}) rotate(${logoRotate - 1.8}deg)`,
          filter: `drop-shadow(0 0 ${glow * 0.75}px ${C3}) brightness(1.6)`,
        }} />
        <img src={staticFile("logo.png")} style={{
          position: "absolute",
          left: `calc(50% + ${chromaShift}px)`,
          top: "48%",
          width: 530,
          opacity: 0.28 + dropHit * 0.24,
          mixBlendMode: "screen",
          transform: `translate(-50%, -50%) scale(${logoScale * 1.03}) rotate(${logoRotate + 1.8}deg)`,
          filter: `drop-shadow(0 0 ${glow * 0.75}px ${C2}) brightness(1.5)`,
        }} />
      </>)}

      {/* ── 10. LOGO PRINCIPAL ────────────────────────────────── */}
      <img src={staticFile("logo.png")} style={{
        position: "absolute",
        left: "50%",
        top: "48%",
        width: 540,
        transform: `translate(-50%, -50%) scale(${logoScale}) rotate(${logoRotate}deg)`,
        filter: `
          drop-shadow(0 0 ${glow}px ${C2})
          drop-shadow(0 0 ${glow * 1.7}px ${C1})
          drop-shadow(0 0 ${glow * 0.8}px ${C3})
          brightness(${1.08 + energy * 0.35 + dropHit * 0.50})
          contrast(${1.18 + beatHit * 0.20})
        `,
        opacity: 0.98,
      }} />

      {/* ── 11. FLASH DE IMPACTO (DROP/BASS) ─────────────────── */}
      <AbsoluteFill style={{
        background: `radial-gradient(circle at 50% 48%, rgba(255,255,255,${flashOpacity * 0.85}) 0%, ${C1}${Math.floor(flashOpacity * 200).toString(16).padStart(2,"0")} 35%, transparent 72%)`,
      }} />

      {/* ── 12. LIGHT LEAKS ───────────────────────────────────── */}
      {[0,1,2,3,4].map((i) => {
        const lc = [C1, C2, C3, C1, C2][i];
        return (
          <div key={`leak-${i}`} style={{
            position: "absolute",
            left: -620,
            top: -220,
            width: 560,
            height: 1700,
            background: `linear-gradient(90deg, transparent, ${lc}30, transparent)`,
            transform: `translateX(${((frame * (4.8 + i * 0.85) + i * 600) % 3800) - 480}px) rotate(${16 + i * 22}deg)`,
            filter: `blur(${32 + intensity * 25}px)`,
            opacity: 0.35 + beatHit * 0.20 + dropHit * 0.25,
          }} />
        );
      })}

      {/* ── 13. SCANLINES ─────────────────────────────────────── */}
      <AbsoluteFill style={{
        background: "repeating-linear-gradient(0deg, rgba(255,255,255,0.042) 0px, rgba(255,255,255,0.042) 1px, transparent 1px, transparent 6px)",
        opacity: 0.09 + beatHit * 0.08 + dropHit * 0.18,
        transform: `translateY(${frame % 6}px)`,
      }} />

      {/* ── 14. PARTÍCULAS (180 unidades) ────────────────────── */}
      {[...Array(180)].map((_, i) => {
        const speed = 0.80 + (i % 10) * 0.20 + dropHit * 2.4;
        const y     = (frame * speed + i * 43) % 1080;
        const drift = Math.sin(frame * 0.026 + i * 1.85) * (44 + beatHit * 58);
        const baseX = i % 3 === 0 ? i * 13 : i % 3 === 1 ? 1920 - i * 13 : 540 + Math.cos(i * 0.8) * 220;
        const x     = (baseX + drift + 1920) % 1920;
        const pc    = [C1, C2, C3, "#ffffff", C1][i % 5];
        const size  = i % 12 === 0 ? 9 : i % 5 === 0 ? 5 : 3;

        return (
          <div key={`p-${i}`} style={{
            position: "absolute",
            left: x,
            top: y,
            width: size + dropHit * 3.5,
            height: size + dropHit * 3.5,
            borderRadius: "50%",
            background: pc,
            opacity: 0.14 + energy * 0.35 + beatHit * 0.24 + dropHit * 0.30,
            boxShadow: `0 0 ${20 + dropHit * 35}px ${pc}`,
            transform: `scale(${1 + beatHit * 0.38 + dropHit * 0.80})`,
          }} />
        );
      })}

      {/* ── 15. BARRAS VISUALIZADOR ESQUERDA ─────────────────── */}
      {[...Array(42)].map((_, i) => {
        const local = rms[Math.max(0, audioIndex - 21 + i)] || audioValue * (0.68 + (i % 6) * 0.08);
        const h = 30 + clamp(local * 2.2) * (195 + dropHit * 280) + Math.abs(Math.sin(frame * 0.24 + i * 0.72)) * (38 + beatHit * 60);
        return (
          <div key={`bl-${i}`} style={{
            position: "absolute",
            left: 28 + i * 7,
            top: "50%",
            width: 5,
            height: h,
            borderRadius: 10,
            background: `linear-gradient(180deg, ${C1}, ${C3}, ${C1}44)`,
            opacity: 0.28 + energy * 0.34 + beatHit * 0.20,
            transform: `translateY(-50%) scaleY(${1 + dropHit * 0.35})`,
            boxShadow: `0 0 ${14 + glow * 0.11}px ${C1}`,
          }} />
        );
      })}

      {/* ── 16. BARRAS VISUALIZADOR DIREITA ──────────────────── */}
      {[...Array(42)].map((_, i) => {
        const local = rms[Math.max(0, audioIndex - 21 + i)] || audioValue * (0.68 + (i % 6) * 0.08);
        const h = 30 + clamp(local * 2.2) * (195 + dropHit * 280) + Math.abs(Math.sin(frame * 0.26 + i * 0.78)) * (38 + beatHit * 60);
        return (
          <div key={`br-${i}`} style={{
            position: "absolute",
            right: 28 + i * 7,
            top: "50%",
            width: 5,
            height: h,
            borderRadius: 10,
            background: `linear-gradient(180deg, ${C2}, ${C1}, ${C2}44)`,
            opacity: 0.28 + energy * 0.34 + beatHit * 0.20,
            transform: `translateY(-50%) scaleY(${1 + dropHit * 0.35})`,
            boxShadow: `0 0 ${14 + glow * 0.11}px ${C2}`,
          }} />
        );
      })}

      {/* ── 17. TEXTO: TAG + TÍTULO (PARTE INFERIOR) ─────────── */}
      <div style={{
        position: "absolute",
        left: "50%",
        bottom: "9%",
        transform: `translateX(-50%) scale(${1 + beatHit * 0.020 + dropHit * 0.040})`,
        width: "82%",
        textAlign: "center",
        zIndex: 10,
      }}>
        {/* Tag de gênero */}
        <div style={{
          display: "inline-block",
          color: C3,
          border: `1px solid ${C3}BB`,
          background: `${C3}20`,
          padding: "5px 14px",
          borderRadius: 6,
          fontSize: 21,
          fontWeight: 900,
          letterSpacing: 5,
          textShadow: `0 0 14px ${C3}`,
          boxShadow: `0 0 ${18 + beatHit * 14}px ${C3}45`,
          marginBottom: 10,
        }}>
          {genreTag}
        </div>

        {/* Linha 1 do título */}
        {titleLine1 && (
          <div style={{
            color: "#fff",
            fontSize: 52,
            fontWeight: 1000,
            lineHeight: 1.04,
            letterSpacing: 2.5,
            textTransform: "uppercase",
            textShadow: `0 0 12px ${C3}, 0 0 30px ${C3}ee, 0 0 58px ${C2}70, 2px 2px 0 #000`,
            WebkitTextStroke: "1px rgba(0,0,0,0.85)",
            position: "relative",
          }}>
            {titleLine1}
            {/* Glitch do título */}
            {glitch && (<>
              <span style={{
                position: "absolute", left: -(2 + dropHit * 5), top: 0,
                color: `${C3}70`, clipPath: "inset(18% 0 58% 0)",
              }}>{titleLine1}</span>
              <span style={{
                position: "absolute", left: 2 + dropHit * 5, top: 0,
                color: `${C2}55`, clipPath: "inset(55% 0 16% 0)",
              }}>{titleLine1}</span>
            </>)}
          </div>
        )}

        {/* Linha 2 do título */}
        {titleLine2 && (
          <div style={{
            color: "#f0f0ff",
            fontSize: 50,
            fontWeight: 900,
            lineHeight: 1.04,
            letterSpacing: 2,
            textTransform: "uppercase",
            textShadow: `0 0 10px ${C1}, 0 0 25px ${C1}cc, 2px 2px 0 #000`,
            WebkitTextStroke: "1px rgba(0,0,0,0.80)",
          }}>
            {titleLine2}
          </div>
        )}
      </div>

      {/* ── 18. BORDA NEON ────────────────────────────────────── */}
      <AbsoluteFill style={{
        border: `${2 + dropHit * 5}px solid ${C2}${Math.floor((0.12 + beatHit * 0.14 + dropHit * 0.30) * 255).toString(16).padStart(2,"0")}`,
        boxShadow: `inset 0 0 ${60 + glow * 0.55}px ${C1}${Math.floor((0.12 + dropHit * 0.26) * 255).toString(16).padStart(2,"0")}`,
        pointerEvents: "none",
      }} />

      {/* ── 19. PROGRESS BAR COM NEON ────────────────────────── */}
      <div style={{
        position: "absolute", left: 0, bottom: 0,
        height: 8, width: `${progress * 100}%`,
        background: `linear-gradient(90deg, ${C3}, ${C1}, ${C2})`,
        boxShadow: `0 0 ${24 + beatHit * 24 + dropHit * 45}px ${C3}`,
      }} />
      <div style={{
        position: "absolute", left: 0, bottom: 0, right: 0,
        height: 8, background: "rgba(255,255,255,0.07)",
      }} />

      {/* ── 20. FADE FINAL PARA LOOP ──────────────────────────── */}
      <AbsoluteFill style={{
        background: "#000",
        opacity: progress > 0.93 ? (progress - 0.93) / 0.07 : 0,
      }} />

    </AbsoluteFill>
  );
};
