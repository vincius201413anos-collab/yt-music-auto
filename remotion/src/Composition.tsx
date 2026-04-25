import { useEffect, useState } from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  staticFile,
  useVideoConfig,
  Img,
} from "remotion";

const clamp = (v: number, min = 0, max = 1) =>
  Math.max(min, Math.min(max, v));

const smooth = (arr: number[], index: number, radius = 5) => {
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

type AudioPayload =
  | number[]
  | {
      rms?: number[];
      audio_data?: number[];
      beats?: number[];
      bass_hits?: number[];
      bpm?: number;
      drop_time?: number | null;
    };

export const MyComposition = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames, width, height } = useVideoConfig();

  const [rms, setRms] = useState<number[]>([]);
  const [beats, setBeats] = useState<number[]>([]);
  const [bassHits, setBassHits] = useState<number[]>([]);
  const [bpm, setBpm] = useState(128);
  const [dropTime, setDropTime] = useState<number | null>(null);

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

        if (typeof data.bpm === "number" && Number.isFinite(data.bpm)) {
          setBpm(data.bpm);
        }

        setDropTime(typeof data.drop_time === "number" ? data.drop_time : null);
      })
      .catch(() => {});
  }, []);

  const time = frame / fps;
  const duration = durationInFrames / fps;
  const audioIndex = Math.floor(time * 60);

  // Energia geral / grave
  const rawEnergy = smooth(rms, audioIndex, 5);
  const energy = clamp(rawEnergy * 2.35, 0, 1);
  const bassEnergy = clamp(smooth(rms, audioIndex, 8) * 2.7, 0, 1);

  // BPM seguro
  const safeBpm = Math.max(60, Math.min(190, bpm || 128));
  const beatInterval = Math.max(1, fps * (60 / safeBpm));
  const beatPhase = (frame % beatInterval) / beatInterval;

  // Corrigido: 0 até 1, nunca negativo
  const bpmPulse = (Math.sin(beatPhase * Math.PI * 2) + 1) / 2;

  // Usa beats reais quando existirem
  const beatNear = beats.some((b) => Math.abs(time - b) < 0.055);
  const bassNear = bassHits.some((b) => Math.abs(time - b) < 0.075);

  const beatPulse = clamp(Math.max(bpmPulse * 0.75, beatNear ? 1 : 0));
  const bassPulse = clamp(Math.max(bassEnergy, bassNear ? 1 : 0));

  // Drop
  const drop = dropTime ?? duration * 0.42;
  const dropDist = Math.abs(time - drop);
  const dropImpact = clamp(1 - dropDist / 0.8, 0, 1);
  const hardDrop = clamp(1 - dropDist / 0.22, 0, 1);

  // Fade suave
  const fadeIn = clamp(time / 0.6);
  const fadeOut = clamp(1 - (time - (duration - 0.9)) / 0.9);
  const masterOpacity = Math.min(fadeIn, fadeOut);

  // Animações otimizadas
  const logoScale =
    0.95 +
    beatPulse * 0.08 +
    bassPulse * 0.14 +
    energy * 0.12 +
    dropImpact * 0.38;

  const logoRotation =
    Math.sin(frame * 0.018) * 0.8 +
    beatPulse * 2.4 +
    hardDrop * Math.sin(frame * 0.75) * 7;

  const glowIntensity =
    24 +
    energy * 48 +
    bassPulse * 34 +
    dropImpact * 95 +
    hardDrop * 50;

  const ringSize =
    Math.min(width, height) * 0.46 +
    beatPulse * 46 +
    energy * 76 +
    dropImpact * 145;

  const shake = hardDrop * 10 + bassPulse * 1.8;
  const shakeX = Math.sin(frame * 1.13) * shake;
  const shakeY = Math.cos(frame * 0.91) * shake;

  const cx = width / 2;
  const cy = height / 2;

  return (
    <AbsoluteFill
      style={{
        background: "#0a001f",
        overflow: "hidden",
        opacity: masterOpacity,
      }}
    >
      {/* === FUNDO CYBERPUNK === */}
      <Img
        src={staticFile("background.png")}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `translate(${shakeX}px, ${shakeY}px) scale(${
            1.035 + energy * 0.035 + dropImpact * 0.025
          })`,
          filter: `brightness(${0.72 + energy * 0.18}) contrast(1.12) saturate(${
            1.08 + energy * 0.2
          })`,
        }}
      />

      {/* === OVERLAY DARK + NEON === */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(circle at center, transparent 34%, rgba(10,0,40,0.62) 66%, rgba(0,0,0,0.92) 100%)",
        }}
      />

      {/* === AMBIENTE NEON SUAVE === */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(circle at 50% 46%, rgba(195,0,255,0.18) 0%, rgba(0,240,255,0.08) 35%, transparent 68%)",
          mixBlendMode: "screen",
          opacity: 0.32 + energy * 0.18 + dropImpact * 0.25,
        }}
      />

      {/* === FLASH NO DROP === */}
      {dropImpact > 0.18 && (
        <AbsoluteFill
          style={{
            background:
              "radial-gradient(circle at center, rgba(255,255,255,0.95) 0%, rgba(0,240,255,0.45) 22%, transparent 62%)",
            opacity: dropImpact * 0.38,
            mixBlendMode: "screen",
          }}
        />
      )}

      {/* === AURA DO LOGO LEVE === */}
      <Img
        src={staticFile("logo_darkmark.png")}
        style={{
          position: "absolute",
          left: cx,
          top: cy,
          width: 500 * logoScale,
          transform: "translate(-50%, -50%)",
          filter: `blur(${7 + energy * 7 + dropImpact * 11}px) brightness(2.35)`,
          opacity: 0.18 + bassPulse * 0.05 + dropImpact * 0.18,
          mixBlendMode: "screen",
          pointerEvents: "none",
        }}
      />

      {/* === RING PRINCIPAL === */}
      <div
        style={{
          position: "absolute",
          left: cx,
          top: cy,
          width: ringSize,
          height: ringSize,
          borderRadius: "50%",
          border: `${1.8 + bassPulse * 1.1 + hardDrop * 3}px solid #c300ff`,
          transform: `translate(-50%, -50%) rotate(${frame * 0.12}deg)`,
          opacity: 0.36 + beatPulse * 0.22 + dropImpact * 0.25,
          boxShadow: `0 0 ${glowIntensity * 0.72}px #c300ff, inset 0 0 ${
            glowIntensity * 0.26
          }px #00f0ff`,
          zIndex: 4,
        }}
      />

      {/* === RING SECUNDÁRIO CIANO === */}
      <div
        style={{
          position: "absolute",
          left: cx,
          top: cy,
          width: ringSize * 0.84 + beatPulse * 26,
          height: ringSize * 0.84 + beatPulse * 26,
          borderRadius: "50%",
          border: "1.4px solid #00f0ff",
          transform: `translate(-50%, -50%) rotate(${-frame * 0.16}deg)`,
          opacity: 0.22 + bassPulse * 0.16 + dropImpact * 0.22,
          boxShadow: `0 0 ${glowIntensity * 0.45}px #00f0ff`,
          zIndex: 4,
        }}
      />

      {/* === LOGO PRINCIPAL === */}
      <Img
        src={staticFile("logo_darkmark.png")}
        style={{
          position: "absolute",
          left: cx,
          top: cy,
          width: Math.min(width, height) * 0.39,
          transform: `translate(-50%, -50%) scale(${logoScale}) rotate(${logoRotation}deg)`,
          filter: `
            drop-shadow(0 0 ${glowIntensity * 0.75}px #c300ff)
            drop-shadow(0 0 ${glowIntensity * 0.5}px #00f0ff)
            brightness(${1.05 + energy * 0.18 + hardDrop * 0.24})
            contrast(${1.08 + beatPulse * 0.08})
          `,
          zIndex: 10,
          pointerEvents: "none",
        }}
      />

      {/* === IMPACT WAVE NO BEAT/DROP === */}
      {(beatPulse > 0.72 || bassPulse > 0.62 || dropImpact > 0.2) && (
        <div
          style={{
            position: "absolute",
            left: cx,
            top: cy,
            width: ringSize + dropImpact * 190,
            height: ringSize + dropImpact * 190,
            borderRadius: "50%",
            border: `${1 + hardDrop * 2}px solid #00f0ff`,
            transform: "translate(-50%, -50%)",
            opacity: (0.18 + bassPulse * 0.14 + dropImpact * 0.28) * (1 - beatPhase * 0.5),
            boxShadow: `0 0 ${glowIntensity * 0.38}px #00f0ff`,
            zIndex: 3,
          }}
        />
      )}

      {/* === VINHETA FINAL === */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(circle, transparent 48%, rgba(0,0,0,0.78) 100%)",
          opacity: 0.72,
          pointerEvents: "none",
        }}
      />

      {/* === FADE FINAL === */}
      <AbsoluteFill
        style={{
          background: "#000",
          opacity: time > duration - 0.9 ? clamp((time - (duration - 0.9)) / 0.9) : 0,
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
};

export default MyComposition;
