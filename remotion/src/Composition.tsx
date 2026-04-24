import { useEffect, useMemo, useState } from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  staticFile,
  useVideoConfig,
  Video,
} from "remotion";

type AudioPayload =
  | number[]
  | {
      rms?: number[];
      audio_data?: number[];
      beats?: number[];
      beat_intensities?: number[];
      bass_hits?: number[];
      drop_time?: number | null;
      duration?: number;
      bpm?: number;
    };

const clamp = (value: number, min = 0, max = 1) => {
  return Math.max(min, Math.min(max, value));
};

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

export const MyComposition = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const [rms, setRms] = useState<number[]>([]);
  const [beats, setBeats] = useState<number[]>([]);
  const [bassHits, setBassHits] = useState<number[]>([]);
  const [beatIntensities, setBeatIntensities] = useState<number[]>([]);
  const [dropTime, setDropTime] = useState<number | null>(null);

  useEffect(() => {
    fetch(staticFile("audio_data.json"))
      .then((res) => res.json())
      .then((data: AudioPayload) => {
        if (Array.isArray(data)) {
          setRms(data);
          setBeats([]);
          setBassHits([]);
          setBeatIntensities([]);
          setDropTime(null);
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
        setBeatIntensities(
          Array.isArray(data.beat_intensities) ? data.beat_intensities : []
        );
        setDropTime(typeof data.drop_time === "number" ? data.drop_time : null);
      })
      .catch(() => {
        setRms([]);
        setBeats([]);
        setBassHits([]);
        setBeatIntensities([]);
        setDropTime(null);
      });
  }, []);

  const time = frame / fps;
  const progress = frame / Math.max(1, durationInFrames - 1);

  // Seu audio_data.json costuma ter 60 pontos por segundo.
  const audioIndex = Math.floor(time * 60);
  const rawAudio = rms[audioIndex] || 0;
  const audioValue = clamp(smooth(rms, audioIndex, 2) * 1.25);

  const lastValues = useMemo(() => {
    const values = rms.slice(Math.max(0, audioIndex - 10), audioIndex + 1);
    return values.length ? values : [0];
  }, [rms, audioIndex]);

  const recentPeak = clamp(Math.max(...lastValues) * 1.35);
  const beatPulse = clamp((rawAudio - audioValue * 0.55) * 4.5);
  const energy = clamp(audioValue * 1.75);
  const bass = clamp(recentPeak * 1.55);
  const dropFromEnergy = recentPeak > 0.58 || beatPulse > 0.62 ? 1 : 0;

  const beatNear = beats.some((b) => Math.abs(time - b) < 0.055);
  const bassNear = bassHits.some((b) => Math.abs(time - b) < 0.075);
  const dropNear =
    typeof dropTime === "number" ? Math.max(0, 1 - Math.abs(time - dropTime) / 1.2) : 0;

  const beatHit = beatNear ? 1 : beatPulse;
  const bassHit = bassNear ? 1 : bass;
  const dropHit = Math.max(dropFromEnergy, dropNear);

  const strongestBeat =
    beatIntensities.length > 0
      ? clamp(beatIntensities[Math.floor((frame / fps) * 2)] || beatHit)
      : beatHit;

  const introBuild = clamp(progress * 2.2);
  const intensity = clamp(energy * 0.7 + beatHit * 0.2 + dropHit * 0.7);
  const flashOpacity = clamp(dropHit * 0.58 + beatHit * 0.13);
  const shake = dropHit * 18 + bassHit * 8 + beatHit * 4;
  const zoom = 1 + beatHit * 0.018 + bassHit * 0.026 + dropHit * 0.07;
  const logoScale = 1 + beatHit * 0.1 + bassHit * 0.13 + dropHit * 0.26;
  const glow = 42 + energy * 70 + beatHit * 55 + dropHit * 145;
  const rotate = Math.sin(frame * 0.045) * (2.5 + beatHit * 1.8);
  const glitch = dropHit > 0.2 || beatHit > 0.55;
  const chromaShift = glitch ? 8 + dropHit * 18 + beatHit * 7 : 0;

  const cameraX = Math.sin(frame * 0.82) * shake;
  const cameraY = Math.cos(frame * 1.14) * shake;

  return (
    <AbsoluteFill
      style={{
        background: "#000",
        overflow: "hidden",
      }}
    >
      {/* VÍDEO BASE GERADO PELO FFMPEG */}
      <AbsoluteFill
        style={{
          transform: `translate(${cameraX}px, ${cameraY}px) scale(${zoom})`,
          filter: `brightness(${0.78 + intensity * 0.35}) contrast(${
            1.12 + intensity * 0.23
          }) saturate(${1.05 + intensity * 0.45})`,
        }}
      >
        <Video
          src={staticFile("input.mp4")}
          style={{
            position: "absolute",
            inset: 0,
            width: "100%",
            height: "100%",
            objectFit: "cover",
          }}
        />
      </AbsoluteFill>

      {/* VINHETA CINEMÁTICA */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(circle at center, rgba(0,0,0,0.03) 0%, rgba(8,0,22,0.34) 42%, rgba(0,0,0,0.82) 100%)",
          opacity: 0.78,
        }}
      />

      {/* COLOR WASH REATIVO */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(135deg, rgba(255,0,94,0.18), rgba(120,0,255,0.18), rgba(0,255,255,0.13))",
          mixBlendMode: "screen",
          opacity: 0.18 + energy * 0.18 + dropHit * 0.22,
        }}
      />

      {/* AURA CENTRAL */}
      <div
        style={{
          position: "absolute",
          inset: "-10%",
          background:
            "radial-gradient(circle, rgba(255,0,255,0.60), rgba(0,255,255,0.22), transparent 58%)",
          opacity: 0.06 + beatHit * 0.15 + dropHit * 0.36,
          transform: `scale(${1 + beatHit * 0.08 + dropHit * 0.16})`,
        }}
      />

      {/* FLASH NO DROP / BEAT */}
      <AbsoluteFill
        style={{
          background: "#ffffff",
          mixBlendMode: "screen",
          opacity: flashOpacity,
        }}
      />

      {/* SCANLINES */}
      <AbsoluteFill
        style={{
          background:
            "repeating-linear-gradient(0deg, rgba(255,255,255,0.055) 0px, rgba(255,255,255,0.055) 1px, transparent 1px, transparent 7px)",
          opacity: 0.09 + beatHit * 0.08 + dropHit * 0.16,
          transform: `translateY(${frame % 7}px)`,
        }}
      />

      {/* LIGHT LEAKS */}
      {[0, 1, 2, 3].map((i) => (
        <div
          key={`leak-${i}`}
          style={{
            position: "absolute",
            left: -500,
            top: -140,
            width: 520,
            height: 1420,
            background:
              i % 2 === 0
                ? "linear-gradient(90deg, transparent, rgba(255,0,255,0.25), transparent)"
                : "linear-gradient(90deg, transparent, rgba(0,255,255,0.22), transparent)",
            transform: `translateX(${
              ((frame * (4.4 + i * 0.75) + i * 520) % 3100) - 450
            }px) rotate(${16 + i * 22}deg)`,
            filter: `blur(${20 + intensity * 22}px)`,
            opacity: 0.38 + beatHit * 0.18 + dropHit * 0.22,
          }}
        />
      ))}

      {/* RINGS NEON COM PULSO */}
      {[780, 625, 485, 340].map((size, i) => {
        const color = i % 2 === 0 ? "#ff00ff" : "#00ffff";
        const spin = frame * (0.55 + i * 0.32) * (i % 2 ? -1 : 1);

        return (
          <div
            key={`ring-${i}`}
            style={{
              position: "absolute",
              left: "50%",
              top: "50%",
              width: size,
              height: size,
              borderRadius: "50%",
              border: `${Math.max(1, 4 - i)}px solid ${color}`,
              boxShadow: `0 0 ${glow}px ${color}, inset 0 0 ${
                glow * 0.38
              }px ${color}`,
              transform: `translate(-50%, -50%) rotate(${spin}deg) scale(${
                1 + beatHit * 0.035 + bassHit * 0.045 + dropHit * 0.12
              })`,
              opacity: 0.58 - i * 0.07 + beatHit * 0.16 + dropHit * 0.2,
              filter: `blur(${i === 3 ? 0.2 : 0}px)`,
            }}
          />
        );
      })}

      {/* ONDAS DE IMPACTO */}
      {[0, 1, 2, 3, 4].map((i) => {
        const wave = ((frame + i * 14) % 74) / 74;
        const power = 0.22 + beatHit * 0.34 + dropHit * 0.55;

        return (
          <div
            key={`wave-${i}`}
            style={{
              position: "absolute",
              left: "50%",
              top: "50%",
              width: 300 + wave * 1050,
              height: 300 + wave * 1050,
              borderRadius: "50%",
              border: `2px solid ${i % 2 ? "#00ffff" : "#ff00ff"}`,
              opacity: (1 - wave) * power,
              boxShadow: `0 0 ${35 + dropHit * 80}px ${
                i % 2 ? "#00ffff" : "#ff00ff"
              }`,
              transform: "translate(-50%, -50%)",
            }}
          />
        );
      })}

      {/* PARTÍCULAS */}
      {[...Array(140)].map((_, i) => {
        const speed = 0.85 + (i % 9) * 0.22 + dropHit * 2.2;
        const y = (frame * speed + i * 47) % 1080;
        const drift = Math.sin(frame * 0.035 + i * 1.7) * (42 + beatHit * 56);
        const x = (i * 131 + drift) % 1920;
        const color =
          i % 4 === 0
            ? "#ff005e"
            : i % 4 === 1
              ? "#00ffff"
              : i % 4 === 2
                ? "#ff00ff"
                : "#8f5cff";

        const size = i % 9 === 0 ? 7 : i % 4 === 0 ? 5 : 3;

        return (
          <div
            key={`p-${i}`}
            style={{
              position: "absolute",
              left: x,
              top: y,
              width: size + dropHit * 2,
              height: size + dropHit * 2,
              borderRadius: "50%",
              background: color,
              opacity: 0.18 + energy * 0.32 + beatHit * 0.22 + dropHit * 0.25,
              boxShadow: `0 0 ${16 + dropHit * 30}px ${color}`,
              transform: `scale(${1 + beatHit * 0.35 + dropHit * 0.7})`,
            }}
          />
        );
      })}

      {/* BARRAS DE ÁUDIO ESQUERDA */}
      {[...Array(36)].map((_, i) => {
        const local =
          rms[Math.max(0, audioIndex - 18 + i)] || audioValue * (0.75 + (i % 5) * 0.08);
        const h =
          32 +
          clamp(local * 1.8) * (190 + dropHit * 250) +
          Math.abs(Math.sin(frame * 0.2 + i * 0.64)) * (38 + beatHit * 58);

        return (
          <div
            key={`bar-l-${i}`}
            style={{
              position: "absolute",
              left: 42 + i * 9,
              top: "50%",
              width: 4,
              height: h,
              borderRadius: 8,
              background: "linear-gradient(180deg, #ff00ff, #ff005e)",
              opacity: 0.34 + energy * 0.32 + beatHit * 0.18,
              transform: `translateY(-50%) scaleY(${1 + dropHit * 0.32})`,
              boxShadow: `0 0 ${14 + glow * 0.14}px #ff00ff`,
            }}
          />
        );
      })}

      {/* BARRAS DE ÁUDIO DIREITA */}
      {[...Array(36)].map((_, i) => {
        const local =
          rms[Math.max(0, audioIndex - 18 + i)] || audioValue * (0.75 + (i % 5) * 0.08);
        const h =
          32 +
          clamp(local * 1.8) * (190 + dropHit * 250) +
          Math.abs(Math.sin(frame * 0.22 + i * 0.72)) * (38 + beatHit * 58);

        return (
          <div
            key={`bar-r-${i}`}
            style={{
              position: "absolute",
              right: 42 + i * 9,
              top: "50%",
              width: 4,
              height: h,
              borderRadius: 8,
              background: "linear-gradient(180deg, #00ffff, #008cff)",
              opacity: 0.34 + energy * 0.32 + beatHit * 0.18,
              transform: `translateY(-50%) scaleY(${1 + dropHit * 0.32})`,
              boxShadow: `0 0 ${14 + glow * 0.14}px #00ffff`,
            }}
          />
        );
      })}

      {/* GLITCH RGB NO DROP */}
      {glitch && (
        <>
          <img
            src={staticFile("logo.png")}
            style={{
              position: "absolute",
              left: `calc(50% - ${chromaShift}px)`,
              top: "50%",
              width: 565,
              opacity: 0.32 + dropHit * 0.25,
              mixBlendMode: "screen",
              transform: `translate(-50%, -50%) scale(${logoScale}) rotate(${
                rotate - 1.2
              }deg)`,
              filter: `drop-shadow(0 0 ${glow * 0.7}px #ff005e) brightness(1.4)`,
            }}
          />
          <img
            src={staticFile("logo.png")}
            style={{
              position: "absolute",
              left: `calc(50% + ${chromaShift}px)`,
              top: "50%",
              width: 565,
              opacity: 0.28 + dropHit * 0.22,
              mixBlendMode: "screen",
              transform: `translate(-50%, -50%) scale(${logoScale}) rotate(${
                rotate + 1.2
              }deg)`,
              filter: `drop-shadow(0 0 ${glow * 0.7}px #00ffff) brightness(1.35)`,
            }}
          />
        </>
      )}

      {/* LOGO / ÍCONE PRINCIPAL REATIVO */}
      <img
        src={staticFile("logo.png")}
        style={{
          position: "absolute",
          left: "50%",
          top: "50%",
          width: 555,
          transform: `translate(-50%, -50%) scale(${logoScale}) rotate(${rotate}deg)`,
          filter: `drop-shadow(0 0 ${glow}px #00ffff) drop-shadow(0 0 ${
            glow * 1.55
          }px #ff00ff) brightness(${1.08 + energy * 0.32 + dropHit * 0.42}) contrast(${
            1.12 + beatHit * 0.16
          })`,
          opacity: 0.96,
        }}
      />

      {/* BORDAS DE ENERGIA */}
      <AbsoluteFill
        style={{
          border: `${2 + dropHit * 5}px solid rgba(0,255,255,${
            0.12 + beatHit * 0.12 + dropHit * 0.25
          })`,
          boxShadow: `inset 0 0 ${45 + glow * 0.55}px rgba(255,0,255,${
            0.12 + dropHit * 0.23
          })`,
        }}
      />

      {/* ESCURECIMENTO SUAVE PARA FINAL NÃO FICAR SECO */}
      <AbsoluteFill
        style={{
          background: "#000",
          opacity: progress > 0.92 ? (progress - 0.92) / 0.08 : 0,
        }}
      />
    </AbsoluteFill>
  );
};
