import { useEffect, useMemo, useState } from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  staticFile,
  useVideoConfig,
  Video,
} from "remotion";

/**
 * Composition.tsx — v10 FINAL ABSURDA VIRAL
 * -----------------------------------------
 * Foco: padrão viral/hipnótico estilo Shorts grandes.
 * - Poucos elementos, impacto alto.
 * - Build controlado.
 * - Drop explosivo.
 * - Logo como foco principal.
 * - Fundo cyberpunk aparece mais.
 * - Sem progress bar.
 * - Sem Math.random no render.
 * - Otimizado para 1080x1920.
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

const clamp = (v: number, min = 0, max = 1) => Math.max(min, Math.min(max, v));

const smooth = (arr: number[], index: number, radius = 2) => {
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
  const clean = (title || "DJ DARKMARK").trim().toUpperCase().replace(/_/g, " ");
  const words = clean.split(/\s+/).filter(Boolean);

  if (words.length <= 2) {
    return [clean, ""];
  }

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
  default: "◈ DJ DARKMARK ◈",
};

const GENRE_COLORS: Record<
  string,
  { primary: string; secondary: string; accent: string; deep: string }
> = {
  phonk: { primary: "#8B00FF", secondary: "#00FFEE", accent: "#FF003C", deep: "#030006" },
  trap: { primary: "#00CCFF", secondary: "#FF00FF", accent: "#00FFEE", deep: "#020511" },
  dark: { primary: "#6600CC", secondary: "#9900FF", accent: "#FF003C", deep: "#020004" },
  electronic: { primary: "#00FFEE", secondary: "#00CCFF", accent: "#FF00FF", deep: "#000912" },
  metal: { primary: "#FF5500", secondary: "#FF003C", accent: "#CC00FF", deep: "#100300" },
  rock: { primary: "#FF8800", secondary: "#FF003C", accent: "#CC00FF", deep: "#100500" },
  lofi: { primary: "#FFAA44", secondary: "#FF7700", accent: "#CC44FF", deep: "#100800" },
  indie: { primary: "#FFDD88", secondary: "#FF8800", accent: "#CC44FF", deep: "#100800" },
  cinematic: { primary: "#FFBB44", secondary: "#FF8800", accent: "#CC00FF", deep: "#100700" },
  funk: { primary: "#FF8800", secondary: "#FF4400", accent: "#CC00FF", deep: "#100500" },
  default: { primary: "#8B00FF", secondary: "#00FFEE", accent: "#FF003C", deep: "#030006" },
};

export const MyComposition = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames, width, height } = useVideoConfig();

  const [rms, setRms] = useState<number[]>([]);
  const [beats, setBeats] = useState<number[]>([]);
  const [bassHits, setBassHits] = useState<number[]>([]);
  const [snareHits, setSnareHits] = useState<number[]>([]);
  const [beatIntensities, setBeatIntensities] = useState<number[]>([]);
  const [dropTime, setDropTime] = useState<number | null>(null);
  const [songTitle, setSongTitle] = useState("DJ darkMark");
  const [songStyle, setSongStyle] = useState("phonk");

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
        setBeatIntensities(Array.isArray(data.beat_intensities) ? data.beat_intensities : []);
        setDropTime(typeof data.drop_time === "number" ? data.drop_time : null);

        if (typeof data.title === "string" && data.title.trim()) setSongTitle(data.title);
        if (typeof data.style === "string" && data.style.trim()) setSongStyle(data.style);
      })
      .catch(() => {});
  }, []);

  const time = frame / fps;
  const progress = frame / Math.max(1, durationInFrames - 1);

  const cx = width / 2;
  const cy = height * 0.445;
  const minDim = Math.min(width, height);

  const audioIndex = Math.floor(time * 60);
  const rawAudio = rms[audioIndex] || 0;
  const audioValue = clamp(smooth(rms, audioIndex, 3) * 1.55);

  const recentValues = useMemo(() => {
    const values = rms.slice(Math.max(0, audioIndex - 10), audioIndex + 1);
    return values.length ? values : [0];
  }, [rms, audioIndex]);

  const recentPeak = clamp(Math.max(...recentValues) * 1.75);
  const beatPulse = clamp((rawAudio - audioValue * 0.34) * 7.4);
  const energy = clamp(audioValue * 2.25);
  const bassEnergy = clamp(recentPeak * 1.85);

  const beatNear = beats.some((b) => Math.abs(time - b) < 0.055);
  const bassNear = bassHits.some((b) => Math.abs(time - b) < 0.085);
  const snareNear = snareHits.some((s) => Math.abs(time - s) < 0.055);

  const detectedDrop =
    typeof dropTime === "number" ? dropTime : durationInFrames / fps * 0.42;

  const dropNear = clamp(1 - Math.abs(time - detectedDrop) / 1.35);
  const hardDrop = clamp(1 - Math.abs(time - detectedDrop) / 0.22);

  const intensityIndex = Math.floor(time * 2);
  const beatIntensity = clamp(beatIntensities[intensityIndex] || 0);

  const beatHit = Math.max(beatNear ? 1 : 0, beatPulse, beatIntensity * 0.68);
  const bassHit = Math.max(bassNear ? 1 : 0, bassEnergy);
  const snareHit = snareNear ? 1 : 0;

  const dropFromEnergy = recentPeak > 0.53 || beatPulse > 0.64 ? recentPeak : 0;
  const dropHit = Math.max(dropNear, dropFromEnergy * 0.72);

  // 0-12% = hook limpo; 12-40% = build; 40%+ = energia controlada.
  const hookPhase = frame < fps * 2.0 ? 1 - frame / (fps * 2.0) : 0;
  const buildPhase = clamp((progress - 0.10) / 0.35);
  const afterDropPhase = progress > 0.42 ? 1 : 0;

  const intensity = clamp(
    energy * 0.52 +
      beatHit * 0.18 +
      bassHit * 0.22 +
      dropHit * 0.70 +
      afterDropPhase * 0.10
  );

  const controlledChaos = clamp(
    hardDrop * 1.0 +
      dropHit * 0.34 +
      bassHit * 0.18 +
      snareHit * 0.12
  );

  const cameraShake = controlledChaos * 22 + bassHit * 4;
  const zoom = 1 + buildPhase * 0.045 + beatHit * 0.010 + bassHit * 0.020 + hardDrop * 0.155;
  const logoScale = 1 + beatHit * 0.085 + bassHit * 0.16 + hardDrop * 0.48 + dropHit * 0.08;
  const logoRotate = Math.sin(frame * 0.025) * (1.5 + beatHit * 1.2) + hardDrop * Math.sin(frame * 0.8) * 4;

  const glow = 48 + energy * 88 + bassHit * 60 + dropHit * 120 + hardDrop * 210;
  const flashOpacity = clamp(hardDrop * 0.88 + dropHit * 0.18 + hookPhase * 0.18);

  const glitch = hardDrop > 0.08 || bassHit > 0.66;
  const chromaShift = glitch ? 3 + bassHit * 10 + hardDrop * 30 : 0;

  const cameraX = Math.sin(frame * 0.84) * cameraShake;
  const cameraY = Math.cos(frame * 1.18) * cameraShake;

  const colors = GENRE_COLORS[songStyle] || GENRE_COLORS.default;
  const { primary: C1, secondary: C2, accent: C3, deep } = colors;
  const genreTag = GENRE_TAGS[songStyle] || GENRE_TAGS.default;
  const [titleLine1, titleLine2] = splitTitle(songTitle);

  const particles = useMemo(
    () =>
      Array.from({ length: 72 }, (_, i) => ({
        id: i,
        baseX: (i * 73) % width,
        seed: i * 1.771,
        speed: 0.54 + (i % 7) * 0.18,
        size: i % 13 === 0 ? 7 : i % 5 === 0 ? 5 : 3,
        colorIndex: i % 5,
      })),
    [width]
  );

  const orbitDots = useMemo(
    () =>
      Array.from({ length: 8 }, (_, i) => ({
        id: i,
        baseAngle: (i / 8) * Math.PI * 2,
        orbitRadius: i < 4 ? minDim * 0.25 : minDim * 0.36,
        size: i < 4 ? 18 : 13,
        speed: i < 4 ? 0.027 : 0.018,
        dir: i % 2 ? 1 : -1,
        colorIndex: i % 3,
      })),
    [minDim]
  );

  return (
    <AbsoluteFill style={{ background: deep, overflow: "hidden" }}>
      {/* BASE VIDEO — o fundo importa */}
      <AbsoluteFill
        style={{
          transform: `translate(${cameraX}px, ${cameraY}px) scale(${zoom})`,
          filter: `brightness(${0.66 + intensity * 0.34}) contrast(${
            1.18 + intensity * 0.28
          }) saturate(${1.08 + intensity * 0.58})`,
        }}
      >
        <Video
          src={staticFile("input.mp4")}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
          }}
        />
      </AbsoluteFill>

      {/* VIGNETTE — foco central */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse 70% 58% at 50% 43%, transparent 0%, rgba(0,0,0,0.14) 35%, rgba(0,0,0,0.70) 76%, rgba(0,0,0,0.97) 100%)`,
        }}
      />

      {/* COLOR WASH — menor, pra não matar o fundo */}
      <AbsoluteFill
        style={{
          background: `linear-gradient(145deg, ${C3}22 0%, ${C1}26 52%, ${C2}18 100%)`,
          mixBlendMode: "screen",
          opacity: 0.10 + energy * 0.13 + dropHit * 0.18,
        }}
      />

      {/* FLASH DO DROP */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at 50% 44%, rgba(255,255,255,${
            flashOpacity * 0.92
          }) 0%, ${C3}AA 18%, ${C1}55 42%, transparent 74%)`,
          opacity: flashOpacity,
          mixBlendMode: "screen",
        }}
      />

      {/* TÚNEL HIPNÓTICO — 6 rings, mais limpo */}
      {[...Array(6)].map((_, i) => {
        const baseSize = minDim * 0.28 + i * minDim * 0.23;
        const size = baseSize * (1 + buildPhase * 0.05 + bassHit * 0.08 + hardDrop * 0.42);
        const dir = i % 2 ? 1 : -1;
        const spd = (0.62 - i * 0.055) * dir * 0.32;
        const col = [C1, C2, C3][i % 3];
        const opacity = Math.max(0.035, 0.48 - i * 0.05 + beatHit * 0.10 + hardDrop * 0.28);

        return (
          <div
            key={`ring-${i}`}
            style={{
              position: "absolute",
              left: cx,
              top: cy,
              width: size,
              height: size,
              borderRadius: "50%",
              border: `${Math.max(1, 3.2 - i * 0.32)}px solid ${col}`,
              boxShadow: `0 0 ${glow * (0.95 - i * 0.09)}px ${col}`,
              opacity,
              transform: `translate(-50%, -50%) rotate(${frame * spd}deg)`,
            }}
          />
        );
      })}

      {/* STARBURST — só quando precisa */}
      {dropHit > 0.12 &&
        [...Array(8)].map((_, i) => {
          const angle = (i / 8) * 360 + frame * 0.08;
          const length = minDim * 0.13 + bassHit * 45 + hardDrop * 250;
          const col = [C1, C2, C3][i % 3];

          return (
            <div
              key={`spike-${i}`}
              style={{
                position: "absolute",
                left: cx,
                top: cy,
                width: 2 + hardDrop * 4,
                height: length,
                background: `linear-gradient(180deg, ${col}, transparent)`,
                boxShadow: `0 0 ${14 + glow * 0.12}px ${col}`,
                transformOrigin: "50% 0%",
                transform: `translateX(-50%) rotate(${angle}deg)`,
                opacity: hardDrop * 0.85 + dropHit * 0.25,
              }}
            />
          );
        })}

      {/* IMPACT WAVES — limpo */}
      {[...Array(3)].map((_, i) => {
        const wave = ((frame + i * 18) % 80) / 80;
        const power = 0.06 + beatHit * 0.12 + bassHit * 0.16 + hardDrop * 0.70;
        const col = [C1, C2, C3][i % 3];

        return (
          <div
            key={`wave-${i}`}
            style={{
              position: "absolute",
              left: cx,
              top: cy,
              width: minDim * 0.32 + wave * minDim * 1.20,
              height: minDim * 0.32 + wave * minDim * 1.20,
              borderRadius: "50%",
              border: `${1.2 + hardDrop * 3}px solid ${col}`,
              opacity: (1 - wave) * power,
              boxShadow: `0 0 ${34 + hardDrop * 110}px ${col}`,
              transform: "translate(-50%, -50%)",
            }}
          />
        );
      })}

      {/* ORBIT DOTS — poucos, mais premium */}
      {orbitDots.map((p) => {
        const angle = frame * p.speed * p.dir + p.baseAngle;
        const pulse = 1 + beatHit * 0.18 + hardDrop * 0.82;
        const orbitX = Math.cos(angle) * p.orbitRadius * pulse;
        const orbitY = Math.sin(angle) * p.orbitRadius * pulse;
        const col = [C1, C2, C3][p.colorIndex];
        const size = p.size + bassHit * 6 + hardDrop * 18;

        return (
          <div
            key={`orbit-${p.id}`}
            style={{
              position: "absolute",
              left: cx,
              top: cy,
              width: size,
              height: size,
              borderRadius: "50%",
              background: col,
              boxShadow: `0 0 ${22 + glow * 0.15}px ${col}, 0 0 ${45 + glow * 0.22}px ${col}55`,
              transform: `translate(calc(-50% + ${orbitX}px), calc(-50% + ${orbitY}px)) scale(${
                1 + beatHit * 0.24 + hardDrop * 0.82
              })`,
              opacity: 0.62 + beatHit * 0.16 + hardDrop * 0.32,
            }}
          />
        );
      })}

      {/* GLOW DIFUSO DO LOGO */}
      <img
        src={staticFile("logo.png")}
        style={{
          position: "absolute",
          left: cx,
          top: cy,
          width: minDim * 0.72 * logoScale,
          height: "auto",
          filter: `blur(${10 + bassHit * 14 + hardDrop * 30}px) brightness(3.6)`,
          opacity: 0.16 + bassHit * 0.10 + hardDrop * 0.30,
          mixBlendMode: "screen",
          transform: `translate(-50%, -50%)`,
        }}
      />

      {/* RGB GLITCH DO LOGO */}
      {glitch && (
        <>
          <img
            src={staticFile("logo.png")}
            style={{
              position: "absolute",
              left: cx - chromaShift,
              top: cy,
              width: minDim * 0.49,
              opacity: 0.22 + hardDrop * 0.28,
              mixBlendMode: "screen",
              transform: `translate(-50%, -50%) scale(${logoScale * 1.035}) rotate(${
                logoRotate - 1.4
              }deg)`,
              filter: `drop-shadow(0 0 ${glow * 0.62}px ${C3}) brightness(1.55)`,
            }}
          />
          <img
            src={staticFile("logo.png")}
            style={{
              position: "absolute",
              left: cx + chromaShift,
              top: cy,
              width: minDim * 0.49,
              opacity: 0.20 + hardDrop * 0.24,
              mixBlendMode: "screen",
              transform: `translate(-50%, -50%) scale(${logoScale * 1.035}) rotate(${
                logoRotate + 1.4
              }deg)`,
              filter: `drop-shadow(0 0 ${glow * 0.62}px ${C2}) brightness(1.5)`,
            }}
          />
        </>
      )}

      {/* LOGO PRINCIPAL — foco absoluto */}
      <img
        src={staticFile("logo.png")}
        style={{
          position: "absolute",
          left: cx,
          top: cy,
          width: minDim * 0.49,
          transform: `translate(-50%, -50%) scale(${logoScale}) rotate(${logoRotate}deg)`,
          filter: `
            drop-shadow(0 0 ${glow}px ${C2})
            drop-shadow(0 0 ${glow * 1.35}px ${C1})
            drop-shadow(0 0 ${glow * 0.65}px ${C3})
            brightness(${1.08 + energy * 0.25 + hardDrop * 0.55})
            contrast(${1.15 + beatHit * 0.16})
          `,
          opacity: 0.99,
        }}
      />

      {/* PARTICLES — controlado */}
      {particles.map((p) => {
        const y = (frame * p.speed + p.id * 43) % height;
        const drift = Math.sin(frame * 0.024 + p.seed) * (30 + beatHit * 34 + hardDrop * 80);
        const x = (p.baseX + drift + width) % width;
        const col = [C1, C2, C3, "#ffffff", C1][p.colorIndex];

        return (
          <div
            key={`particle-${p.id}`}
            style={{
              position: "absolute",
              left: x,
              top: y,
              width: p.size + hardDrop * 2.8,
              height: p.size + hardDrop * 2.8,
              borderRadius: "50%",
              background: col,
              opacity: 0.09 + energy * 0.22 + beatHit * 0.10 + hardDrop * 0.36,
              boxShadow: `0 0 ${14 + hardDrop * 34}px ${col}`,
              transform: `scale(${1 + beatHit * 0.22 + hardDrop * 0.72})`,
            }}
          />
        );
      })}

      {/* SCANLINES — sutil */}
      <AbsoluteFill
        style={{
          background:
            "repeating-linear-gradient(0deg, rgba(255,255,255,0.040) 0px, rgba(255,255,255,0.040) 1px, transparent 1px, transparent 7px)",
          opacity: 0.05 + beatHit * 0.04 + hardDrop * 0.12,
          transform: `translateY(${frame % 7}px)`,
          mixBlendMode: "screen",
        }}
      />

      {/* TEXT SAFE ZONE — menor que antes */}
      <div
        style={{
          position: "absolute",
          left: "50%",
          bottom: height * 0.060,
          transform: `translateX(-50%) scale(${1 + beatHit * 0.012 + hardDrop * 0.025})`,
          width: "84%",
          textAlign: "center",
          zIndex: 10,
          opacity: 0.92,
        }}
      >
        <div
          style={{
            display: "inline-block",
            color: C3,
            border: `1px solid ${C3}99`,
            background: `${C3}18`,
            padding: "4px 12px",
            borderRadius: 6,
            fontSize: 18,
            fontWeight: 900,
            letterSpacing: 4,
            textShadow: `0 0 12px ${C3}`,
            boxShadow: `0 0 ${14 + beatHit * 10}px ${C3}40`,
            marginBottom: 8,
          }}
        >
          {genreTag}
        </div>

        <div
          style={{
            color: "#fff",
            fontSize: 44,
            fontWeight: 1000,
            lineHeight: 1.02,
            letterSpacing: 2,
            textTransform: "uppercase",
            textShadow: `0 0 10px ${C3}, 0 0 24px ${C3}cc, 0 0 48px ${C2}60, 2px 2px 0 #000`,
            WebkitTextStroke: "1px rgba(0,0,0,0.85)",
            position: "relative",
          }}
        >
          {titleLine1}
        </div>

        {titleLine2 && (
          <div
            style={{
              color: "#f0f0ff",
              fontSize: 42,
              fontWeight: 900,
              lineHeight: 1.02,
              letterSpacing: 1.8,
              textTransform: "uppercase",
              textShadow: `0 0 9px ${C1}, 0 0 20px ${C1}cc, 2px 2px 0 #000`,
              WebkitTextStroke: "1px rgba(0,0,0,0.80)",
            }}
          >
            {titleLine2}
          </div>
        )}
      </div>

      {/* BORDA NEON — só respira, não domina */}
      <AbsoluteFill
        style={{
          border: `${2 + hardDrop * 5}px solid ${C2}${Math.floor(
            (0.08 + beatHit * 0.08 + hardDrop * 0.32) * 255
          )
            .toString(16)
            .padStart(2, "0")}`,
          boxShadow: `inset 0 0 ${42 + glow * 0.35}px ${C1}${Math.floor(
            (0.08 + hardDrop * 0.24) * 255
          )
            .toString(16)
            .padStart(2, "0")}`,
          pointerEvents: "none",
        }}
      />

      {/* LOOP FINAL — volta pro escuro, sem progress bar */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at 50% 44%, ${C2}${Math.floor(
            clamp((progress > 0.94 ? (progress - 0.94) / 0.06 : 0) * 95)
          )
            .toString(16)
            .padStart(2, "0")} 0%, transparent 62%)`,
          opacity: progress > 0.94 ? (progress - 0.94) / 0.06 : 0,
          mixBlendMode: "screen",
        }}
      />

      <AbsoluteFill
        style={{
          background: "#000",
          opacity: progress > 0.987 ? (progress - 0.987) / 0.013 : 0,
        }}
      />
    </AbsoluteFill>
  );
};

export default MyComposition;
