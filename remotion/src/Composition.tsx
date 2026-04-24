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
      bass_hits?: number[];
      beat_intensities?: number[];
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

const splitTitle = (title: string) => {
  const clean = title.trim().toUpperCase();
  const words = clean.split(/\s+/);

  if (words.length <= 2) {
    return [clean, "PHONK ENERGY"];
  }

  const mid = Math.ceil(words.length / 2);
  return [words.slice(0, mid).join(" "), words.slice(mid).join(" ")];
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

  const audioIndex = Math.floor(time * 60);
  const rawAudio = rms[audioIndex] || 0;
  const audioValue = clamp(smooth(rms, audioIndex, 2) * 1.3);

  const recentValues = useMemo(() => {
    const values = rms.slice(Math.max(0, audioIndex - 12), audioIndex + 1);
    return values.length ? values : [0];
  }, [rms, audioIndex]);

  const recentPeak = clamp(Math.max(...recentValues) * 1.45);
  const beatPulse = clamp((rawAudio - audioValue * 0.5) * 5.2);
  const energy = clamp(audioValue * 1.85);
  const bassEnergy = clamp(recentPeak * 1.55);

  const beatNear = beats.some((b) => Math.abs(time - b) < 0.055);
  const bassNear = bassHits.some((b) => Math.abs(time - b) < 0.075);
  const dropNear =
    typeof dropTime === "number"
      ? clamp(1 - Math.abs(time - dropTime) / 1.15)
      : 0;

  const beatHit = beatNear ? 1 : beatPulse;
  const bassHit = bassNear ? 1 : bassEnergy;
  const dropFromEnergy = recentPeak > 0.62 || beatPulse > 0.68 ? 1 : 0;
  const dropHit = Math.max(dropNear, dropFromEnergy);

  const strongestBeat =
    beatIntensities.length > 0
      ? clamp(beatIntensities[Math.floor(time * 2)] || beatHit)
      : beatHit;

  const intensity = clamp(energy * 0.65 + beatHit * 0.22 + bassHit * 0.18 + dropHit * 0.68);

  const shake = dropHit * 14 + bassHit * 6 + beatHit * 3;
  const zoom = 1 + beatHit * 0.014 + bassHit * 0.026 + dropHit * 0.06;
  const logoScale = 1 + beatHit * 0.09 + bassHit * 0.11 + dropHit * 0.23;
  const glow = 44 + energy * 72 + beatHit * 52 + dropHit * 135;
  const rotate = Math.sin(frame * 0.042) * (2.2 + beatHit * 1.3);

  const flashOpacity = clamp(dropHit * 0.46 + beatHit * 0.09);
  const glitch = dropHit > 0.22 || beatHit > 0.62 || strongestBeat > 0.72;
  const chromaShift = glitch ? 5 + dropHit * 18 + beatHit * 6 : 0;

  const cameraX = Math.sin(frame * 0.78) * shake;
  const cameraY = Math.cos(frame * 1.18) * shake;

  const [titleLine1, titleLine2] = splitTitle("DARK PHONK NIGHT DRIVE");

  return (
    <AbsoluteFill
      style={{
        background: "#000",
        overflow: "hidden",
      }}
    >
      {/* VIDEO BASE */}
      <AbsoluteFill
        style={{
          transform: `translate(${cameraX}px, ${cameraY}px) scale(${zoom})`,
          filter: `brightness(${0.78 + intensity * 0.34}) contrast(${
            1.14 + intensity * 0.22
          }) saturate(${1.08 + intensity * 0.48})`,
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

      {/* VINHETA PARA PRENDER O OLHAR NO CENTRO */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(circle at center, rgba(0,0,0,0.04) 0%, rgba(8,0,20,0.32) 45%, rgba(0,0,0,0.86) 100%)",
          opacity: 0.78,
        }}
      />

      {/* COLOR GRADE PHONK */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(135deg, rgba(255,0,86,0.20), rgba(120,0,255,0.18), rgba(0,255,255,0.12))",
          mixBlendMode: "screen",
          opacity: 0.14 + energy * 0.16 + dropHit * 0.18,
        }}
      />

      {/* AURA CENTRAL CONTROLADA */}
      <div
        style={{
          position: "absolute",
          inset: "-10%",
          background:
            "radial-gradient(circle, rgba(255,0,255,0.48), rgba(0,255,255,0.18), transparent 56%)",
          opacity: 0.045 + beatHit * 0.12 + dropHit * 0.28,
          transform: `scale(${1 + beatHit * 0.06 + dropHit * 0.13})`,
        }}
      />

      {/* FLASH DE IMPACTO */}
      <AbsoluteFill
        style={{
          background: "#ffffff",
          mixBlendMode: "screen",
          opacity: flashOpacity,
        }}
      />

      {/* SCANLINES HIPNÓTICAS */}
      <AbsoluteFill
        style={{
          background:
            "repeating-linear-gradient(0deg, rgba(255,255,255,0.05) 0px, rgba(255,255,255,0.05) 1px, transparent 1px, transparent 7px)",
          opacity: 0.08 + beatHit * 0.06 + dropHit * 0.12,
          transform: `translateY(${frame % 7}px)`,
        }}
      />

      {/* LIGHT LEAKS LATERAIS */}
      {[0, 1, 2, 3].map((i) => (
        <div
          key={`leak-${i}`}
          style={{
            position: "absolute",
            left: -560,
            top: -170,
            width: 500,
            height: 1450,
            background:
              i % 2 === 0
                ? "linear-gradient(90deg, transparent, rgba(255,0,255,0.24), transparent)"
                : "linear-gradient(90deg, transparent, rgba(0,255,255,0.20), transparent)",
            transform: `translateX(${
              ((frame * (4.1 + i * 0.72) + i * 530) % 3200) - 380
            }px) rotate(${16 + i * 22}deg)`,
            filter: `blur(${22 + intensity * 18}px)`,
            opacity: 0.28 + beatHit * 0.15 + dropHit * 0.18,
          }}
        />
      ))}

      {/* RINGS NEON - FORTES, MAS NÃO SUJAM O CENTRO */}
      {[760, 610, 470].map((size, i) => {
        const color = i % 2 === 0 ? "#ff00ff" : "#00ffff";
        const spin = frame * (0.52 + i * 0.32) * (i % 2 ? -1 : 1);

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
              boxShadow: `0 0 ${glow * 0.88}px ${color}, inset 0 0 ${
                glow * 0.28
              }px ${color}`,
              transform: `translate(-50%, -50%) rotate(${spin}deg) scale(${
                1 + beatHit * 0.028 + bassHit * 0.038 + dropHit * 0.09
              })`,
              opacity: 0.44 - i * 0.06 + beatHit * 0.13 + dropHit * 0.16,
            }}
          />
        );
      })}

      {/* ONDAS DE DROP */}
      {[0, 1, 2, 3].map((i) => {
        const wave = ((frame + i * 16) % 78) / 78;
        const power = 0.18 + beatHit * 0.26 + dropHit * 0.48;

        return (
          <div
            key={`wave-${i}`}
            style={{
              position: "absolute",
              left: "50%",
              top: "50%",
              width: 320 + wave * 1000,
              height: 320 + wave * 1000,
              borderRadius: "50%",
              border: `2px solid ${i % 2 ? "#00ffff" : "#ff00ff"}`,
              opacity: (1 - wave) * power,
              boxShadow: `0 0 ${35 + dropHit * 70}px ${
                i % 2 ? "#00ffff" : "#ff00ff"
              }`,
              transform: "translate(-50%, -50%)",
            }}
          />
        );
      })}

      {/* PARTÍCULAS - MAIS NAS BORDAS PARA NÃO MATAR FOCO */}
      {[...Array(126)].map((_, i) => {
        const speed = 0.75 + (i % 9) * 0.2 + dropHit * 1.9;
        const y = (frame * speed + i * 47) % 1080;
        const drift = Math.sin(frame * 0.032 + i * 1.6) * (38 + beatHit * 46);
        const baseX = i % 2 === 0 ? i * 21 : 1920 - i * 21;
        const x = (baseX + drift + 1920) % 1920;

        const color =
          i % 4 === 0
            ? "#ff005e"
            : i % 4 === 1
              ? "#00ffff"
              : i % 4 === 2
                ? "#ff00ff"
                : "#8f5cff";

        const size = i % 11 === 0 ? 7 : i % 4 === 0 ? 5 : 3;

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
              opacity: 0.14 + energy * 0.28 + beatHit * 0.18 + dropHit * 0.22,
              boxShadow: `0 0 ${15 + dropHit * 26}px ${color}`,
              transform: `scale(${1 + beatHit * 0.28 + dropHit * 0.6})`,
            }}
          />
        );
      })}

      {/* BARRAS DE ÁUDIO ESQUERDA */}
      {[...Array(34)].map((_, i) => {
        const local =
          rms[Math.max(0, audioIndex - 17 + i)] ||
          audioValue * (0.72 + (i % 5) * 0.08);

        const h =
          28 +
          clamp(local * 1.85) * (165 + dropHit * 225) +
          Math.abs(Math.sin(frame * 0.2 + i * 0.64)) * (30 + beatHit * 48);

        return (
          <div
            key={`bar-l-${i}`}
            style={{
              position: "absolute",
              left: 34 + i * 8,
              top: "50%",
              width: 4,
              height: h,
              borderRadius: 8,
              background: "linear-gradient(180deg, #ff00ff, #ff005e)",
              opacity: 0.24 + energy * 0.28 + beatHit * 0.14,
              transform: `translateY(-50%) scaleY(${1 + dropHit * 0.25})`,
              boxShadow: `0 0 ${12 + glow * 0.1}px #ff00ff`,
            }}
          />
        );
      })}

      {/* BARRAS DE ÁUDIO DIREITA */}
      {[...Array(34)].map((_, i) => {
        const local =
          rms[Math.max(0, audioIndex - 17 + i)] ||
          audioValue * (0.72 + (i % 5) * 0.08);

        const h =
          28 +
          clamp(local * 1.85) * (165 + dropHit * 225) +
          Math.abs(Math.sin(frame * 0.22 + i * 0.72)) * (30 + beatHit * 48);

        return (
          <div
            key={`bar-r-${i}`}
            style={{
              position: "absolute",
              right: 34 + i * 8,
              top: "50%",
              width: 4,
              height: h,
              borderRadius: 8,
              background: "linear-gradient(180deg, #00ffff, #008cff)",
              opacity: 0.24 + energy * 0.28 + beatHit * 0.14,
              transform: `translateY(-50%) scaleY(${1 + dropHit * 0.25})`,
              boxShadow: `0 0 ${12 + glow * 0.1}px #00ffff`,
            }}
          />
        );
      })}

      {/* GLITCH RGB NO LOGO */}
      {glitch && (
        <>
          <img
            src={staticFile("logo.png")}
            style={{
              position: "absolute",
              left: `calc(50% - ${chromaShift}px)`,
              top: "48%",
              width: 505,
              opacity: 0.24 + dropHit * 0.22,
              mixBlendMode: "screen",
              transform: `translate(-50%, -50%) scale(${logoScale}) rotate(${
                rotate - 1.15
              }deg)`,
              filter: `drop-shadow(0 0 ${glow * 0.62}px #ff005e) brightness(1.36)`,
            }}
          />
          <img
            src={staticFile("logo.png")}
            style={{
              position: "absolute",
              left: `calc(50% + ${chromaShift}px)`,
              top: "48%",
              width: 505,
              opacity: 0.22 + dropHit * 0.2,
              mixBlendMode: "screen",
              transform: `translate(-50%, -50%) scale(${logoScale}) rotate(${
                rotate + 1.15
              }deg)`,
              filter: `drop-shadow(0 0 ${glow * 0.62}px #00ffff) brightness(1.32)`,
            }}
          />
        </>
      )}

      {/* LOGO CENTRAL - UM POUCO MAIS ALTO PARA DEIXAR TEXTO EMBAIXO */}
      <img
        src={staticFile("logo.png")}
        style={{
          position: "absolute",
          left: "50%",
          top: "48%",
          width: 500,
          transform: `translate(-50%, -50%) scale(${logoScale}) rotate(${rotate}deg)`,
          filter: `drop-shadow(0 0 ${glow}px #00ffff) drop-shadow(0 0 ${
            glow * 1.45
          }px #ff00ff) brightness(${1.1 + energy * 0.28 + dropHit * 0.38}) contrast(${
            1.12 + beatHit * 0.14
          })`,
          opacity: 0.97,
        }}
      />

      {/* TAG E TÍTULO EMBAIXO - RETENÇÃO SEM COBRIR O CENTRO */}
      <div
        style={{
          position: "absolute",
          left: "50%",
          bottom: "10.5%",
          transform: `translateX(-50%) scale(${1 + beatHit * 0.018 + dropHit * 0.035})`,
          width: "86%",
          textAlign: "center",
        }}
      >
        <div
          style={{
            display: "inline-block",
            color: "#ff4d7a",
            border: "1px solid rgba(255,77,122,0.72)",
            background: "rgba(255,0,94,0.13)",
            padding: "5px 12px",
            borderRadius: 6,
            fontSize: 22,
            fontWeight: 900,
            letterSpacing: 5,
            textShadow: "0 0 12px rgba(255,0,94,0.95)",
            boxShadow: "0 0 18px rgba(255,0,94,0.26)",
            marginBottom: 10,
          }}
        >
          ◈ PHONK MODE ◈
        </div>

        <div
          style={{
            color: "#fff",
            fontSize: 54,
            fontWeight: 1000,
            lineHeight: 1.02,
            letterSpacing: 2.2,
            textTransform: "uppercase",
            textShadow:
              "0 0 10px #ff005e, 0 0 25px rgba(255,0,94,0.92), 0 0 46px rgba(0,255,255,0.42), 2px 2px 0 #000",
            WebkitTextStroke: "1px rgba(0,0,0,0.75)",
          }}
        >
          <span style={{ position: "relative" }}>
            {titleLine1}
            {glitch && (
              <>
                <span
                  style={{
                    position: "absolute",
                    left: -3 - dropHit * 4,
                    top: 0,
                    color: "rgba(255,0,0,0.48)",
                    clipPath: "inset(20% 0 55% 0)",
                  }}
                >
                  {titleLine1}
                </span>
                <span
                  style={{
                    position: "absolute",
                    left: 3 + dropHit * 4,
                    top: 0,
                    color: "rgba(0,255,255,0.38)",
                    clipPath: "inset(55% 0 18% 0)",
                  }}
                >
                  {titleLine1}
                </span>
              </>
            )}
          </span>
          <br />
          <span style={{ color: "#f6f6ff" }}>{titleLine2}</span>
        </div>
      </div>

      {/* BORDA DE ENERGIA */}
      <AbsoluteFill
        style={{
          border: `${2 + dropHit * 4}px solid rgba(0,255,255,${
            0.1 + beatHit * 0.1 + dropHit * 0.22
          })`,
          boxShadow: `inset 0 0 ${44 + glow * 0.45}px rgba(255,0,255,${
            0.1 + dropHit * 0.2
          })`,
          pointerEvents: "none",
        }}
      />

      {/* PROGRESS BAR - RETENÇÃO */}
      <div
        style={{
          position: "absolute",
          left: 0,
          bottom: 0,
          height: 7,
          width: `${progress * 100}%`,
          background: "linear-gradient(90deg, #ff005e, #ff00ff, #00ffff)",
          boxShadow: `0 0 ${18 + beatHit * 18 + dropHit * 32}px #ff005e`,
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 0,
          bottom: 0,
          right: 0,
          height: 7,
          background: "rgba(255,255,255,0.10)",
        }}
      />

      {/* PULSO FINAL PARA LOOP */}
      <AbsoluteFill
        style={{
          background: "#000",
          opacity: progress > 0.935 ? (progress - 0.935) / 0.065 : 0,
        }}
      />
    </AbsoluteFill>
  );
};
