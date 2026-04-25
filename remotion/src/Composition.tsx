import { useEffect, useState } from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  staticFile,
  useVideoConfig,
  Img,
  Video,
} from "remotion";

const clamp = (v: number, min = 0, max = 1) =>
  Math.max(min, Math.min(max, v));

const smooth = (arr: number[], index: number, radius = 4) => {
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

  // Reativo, mas leve para GitHub Actions.
  const rawEnergy = smooth(rms, audioIndex, 4);
  const energy = clamp(rawEnergy * 3.8, 0.18, 1);
  const bassEnergy = clamp(smooth(rms, audioIndex, 6) * 4.2, 0.12, 1);

  const safeBpm = Math.max(60, Math.min(190, bpm || 128));
  const beatInterval = Math.max(1, fps * (60 / safeBpm));
  const beatPhase = (frame % beatInterval) / beatInterval;

  const bpmPulse = (Math.sin(beatPhase * Math.PI * 2) + 1) / 2;
  const beatNear = beats.some((b) => Math.abs(time - b) < 0.065);
  const bassNear = bassHits.some((b) => Math.abs(time - b) < 0.085);

  const beatPulse = clamp(Math.max(bpmPulse * 0.85, beatNear ? 1 : 0), 0.14, 1);
  const bassPulse = clamp(Math.max(bassEnergy, bassNear ? 1 : 0), 0.12, 1);

  const drop = dropTime ?? duration * 0.42;
  const dropDist = Math.abs(time - drop);
  const dropImpact = clamp(1 - dropDist / 0.55, 0, 1);
  const hardDrop = clamp(1 - dropDist / 0.18, 0, 1);

  const fadeIn = clamp(time / 0.4);
  const fadeOut = clamp(1 - (time - (duration - 0.7)) / 0.7);
  const masterOpacity = Math.min(fadeIn, fadeOut);

  const logoScale =
    0.96 +
    beatPulse * 0.07 +
    bassPulse * 0.12 +
    energy * 0.09 +
    dropImpact * 0.28;

  const logoRotation =
    Math.sin(frame * 0.018) * 0.8 +
    beatPulse * 1.5 +
    hardDrop * Math.sin(frame * 0.65) * 5;

  const glowIntensity =
    32 +
    energy * 55 +
    bassPulse * 38 +
    dropImpact * 95 +
    hardDrop * 42;

  const ringSize =
    Math.min(width, height) * 0.46 +
    beatPulse * 36 +
    energy * 52 +
    dropImpact * 95;

  // Shake reduzido: mantém impacto sem travar render.
  const shake = hardDrop * 7 + bassPulse * 1.2;
  const shakeX = Math.sin(frame * 0.9) * shake;
  const shakeY = Math.cos(frame * 0.8) * shake;

  const cx = width / 2;
  const cy = height / 2;

  const scanOpacity = clamp(0.04 + bassPulse * 0.05 + dropImpact * 0.08, 0, 0.18);

  return (
    <AbsoluteFill
      style={{
        background: "#050010",
        overflow: "hidden",
        opacity: masterOpacity,
      }}
    >
      {/* === VIDEO BASE FFmpeg === */}
      <AbsoluteFill
        style={{
          transform: `translate(${shakeX}px, ${shakeY}px) scale(${
            1.035 + energy * 0.025 + dropImpact * 0.018
          })`,
          filter: `brightness(${0.82 + energy * 0.18 + hardDrop * 0.12}) contrast(${
            1.1 + energy * 0.12
          }) saturate(${1.12 + energy * 0.28 + dropImpact * 0.2})`,
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

      {/* === VINHETA / FOCO CENTRAL === */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(circle at center, transparent 30%, rgba(18,0,48,0.42) 62%, rgba(0,0,0,0.86) 100%)",
          pointerEvents: "none",
        }}
      />

      {/* === GLOW CENTRAL LEVE === */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(circle at 50% 50%, rgba(255,0,255,0.22) 0%, rgba(0,240,255,0.12) 30%, transparent 68%)",
          mixBlendMode: "screen",
          opacity: 0.38 + energy * 0.14 + dropImpact * 0.18,
          pointerEvents: "none",
        }}
      />

      {/* === SCANLINES LEVES === */}
      <AbsoluteFill
        style={{
          background:
            "repeating-linear-gradient(to bottom, transparent 0px, transparent 6px, rgba(0,240,255,0.10) 6px, rgba(0,240,255,0.10) 7px)",
          opacity: scanOpacity,
          mixBlendMode: "screen",
          pointerEvents: "none",
        }}
      />

      {/* === FLASH NO DROP === */}
      {dropImpact > 0.18 && (
        <AbsoluteFill
          style={{
            background:
              "radial-gradient(circle at center, rgba(255,255,255,0.85) 0%, rgba(0,240,255,0.35) 22%, transparent 62%)",
            opacity: dropImpact * 0.32,
            mixBlendMode: "screen",
            pointerEvents: "none",
          }}
        />
      )}

      {/* === AURA DO LOGO OTIMIZADA === */}
      <Img
        src={staticFile("logo_darkmark.png")}
        style={{
          position: "absolute",
          left: cx,
          top: cy,
          width: Math.min(width, height) * 0.55 * logoScale,
          transform: "translate(-50%, -50%)",
          filter: `blur(${6 + energy * 5 + dropImpact * 7}px) brightness(2.4)`,
          opacity: 0.22 + bassPulse * 0.05 + dropImpact * 0.16,
          mixBlendMode: "screen",
          pointerEvents: "none",
          zIndex: 2,
        }}
      />

      {/* === RING MAGENTA PRINCIPAL === */}
      <div
        style={{
          position: "absolute",
          left: cx,
          top: cy,
          width: ringSize,
          height: ringSize,
          borderRadius: "50%",
          border: `${2 + bassPulse * 0.8 + hardDrop * 2.4}px solid #ff00ff`,
          transform: `translate(-50%, -50%) rotate(${frame * 0.08}deg)`,
          opacity: 0.42 + beatPulse * 0.18 + dropImpact * 0.14,
          boxShadow: `0 0 ${glowIntensity * 0.58}px #ff00ff`,
          zIndex: 4,
        }}
      />

      {/* === RING CIANO LEVE === */}
      <div
        style={{
          position: "absolute",
          left: cx,
          top: cy,
          width: ringSize * 0.84 + beatPulse * 24,
          height: ringSize * 0.84 + beatPulse * 24,
          borderRadius: "50%",
          border: `${1.2 + hardDrop * 1.2}px solid #00f0ff`,
          transform: `translate(-50%, -50%) rotate(${-frame * 0.11}deg)`,
          opacity: 0.22 + bassPulse * 0.12 + dropImpact * 0.18,
          boxShadow: `0 0 ${glowIntensity * 0.32}px #00f0ff`,
          zIndex: 5,
        }}
      />

      {/* === WAVE DE IMPACTO LEVE === */}
      {(beatPulse > 0.72 || bassPulse > 0.62 || dropImpact > 0.2) && (
        <div
          style={{
            position: "absolute",
            left: cx,
            top: cy,
            width: ringSize + beatPulse * 55 + dropImpact * 120,
            height: ringSize + beatPulse * 55 + dropImpact * 120,
            borderRadius: "50%",
            border: `${1 + hardDrop * 1.6}px solid rgba(255,255,255,0.75)`,
            transform: "translate(-50%, -50%)",
            opacity: (0.12 + bassPulse * 0.1 + dropImpact * 0.18) * (1 - beatPhase * 0.38),
            boxShadow: `0 0 ${glowIntensity * 0.22}px #ffffff`,
            mixBlendMode: "screen",
            zIndex: 3,
          }}
        />
      )}

      {/* === LOGO PRINCIPAL === */}
      <Img
        src={staticFile("logo_darkmark.png")}
        style={{
          position: "absolute",
          left: cx,
          top: cy,
          width: Math.min(width, height) * 0.36,
          transform: `translate(-50%, -50%) scale(${logoScale}) rotate(${logoRotation}deg)`,
          filter: `
            drop-shadow(0 0 ${glowIntensity * 0.42}px #ff00ff)
            drop-shadow(0 0 ${glowIntensity * 0.28}px #00f0ff)
            brightness(${1.08 + energy * 0.14 + hardDrop * 0.18})
            contrast(${1.08 + beatPulse * 0.06})
          `,
          zIndex: 10,
          pointerEvents: "none",
        }}
      />

      {/* === VINHETA FINAL === */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(circle, transparent 48%, rgba(0,0,0,0.72) 100%)",
          opacity: 0.68,
          pointerEvents: "none",
          zIndex: 20,
        }}
      />

      {/* === FADE FINAL === */}
      <AbsoluteFill
        style={{
          background: "#000",
          opacity: time > duration - 0.7 ? clamp((time - (duration - 0.7)) / 0.7) : 0,
          pointerEvents: "none",
          zIndex: 30,
        }}
      />
    </AbsoluteFill>
  );
};

export default MyComposition;
