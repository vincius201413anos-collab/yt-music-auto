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

  // Energia forçada: mesmo música fraca fica viva.
  const rawEnergy = smooth(rms, audioIndex, 5);
  const energy = clamp(rawEnergy * 4.15, 0.22, 1);
  const bassEnergy = clamp(smooth(rms, audioIndex, 8) * 4.4, 0.16, 1);

  const safeBpm = Math.max(60, Math.min(190, bpm || 128));
  const beatInterval = Math.max(1, fps * (60 / safeBpm));
  const beatPhase = (frame % beatInterval) / beatInterval;

  const bpmPulse = (Math.sin(beatPhase * Math.PI * 2) + 1) / 2;
  const beatNear = beats.some((b) => Math.abs(time - b) < 0.065);
  const bassNear = bassHits.some((b) => Math.abs(time - b) < 0.085);

  const beatPulse = clamp(Math.max(bpmPulse * 0.9, beatNear ? 1 : 0), 0.18, 1);
  const bassPulse = clamp(Math.max(bassEnergy, bassNear ? 1 : 0), 0.16, 1);

  // Drop mais agressivo.
  const drop = dropTime ?? duration * 0.42;
  const dropDist = Math.abs(time - drop);
  const dropImpact = clamp(1 - dropDist / 0.55, 0, 1);
  const hardDrop = clamp(1 - dropDist / 0.18, 0, 1);

  const fadeIn = clamp(time / 0.45);
  const fadeOut = clamp(1 - (time - (duration - 0.75)) / 0.75);
  const masterOpacity = Math.min(fadeIn, fadeOut);

  // Visual parecido com a imagem de prévia: logo grande, ring neon, glow pesado.
  const logoScale =
    1.02 +
    beatPulse * 0.12 +
    bassPulse * 0.18 +
    energy * 0.18 +
    dropImpact * 0.52;

  const logoRotation =
    Math.sin(frame * 0.022) * 1.2 +
    beatPulse * 4.2 +
    hardDrop * Math.sin(frame * 0.92) * 13;

  const glowIntensity =
    75 +
    energy * 145 +
    bassPulse * 95 +
    dropImpact * 260 +
    hardDrop * 130;

  const ringSize =
    Math.min(width, height) * 0.58 +
    beatPulse * 82 +
    energy * 110 +
    dropImpact * 235;

  const shake = hardDrop * 25 + bassPulse * 3.5;
  const shakeX = Math.sin(frame * 1.33) * shake;
  const shakeY = Math.cos(frame * 1.08) * shake;

  const cx = width / 2;
  const cy = height / 2;

  const particleOpacity = clamp(0.22 + energy * 0.28 + dropImpact * 0.45, 0, 0.85);
  const scanOpacity = clamp(0.08 + bassPulse * 0.08 + dropImpact * 0.13, 0, 0.28);

  return (
    <AbsoluteFill
      style={{
        background: "#050010",
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
            1.055 + energy * 0.052 + dropImpact * 0.045
          })`,
          filter: `brightness(${0.78 + energy * 0.26 + hardDrop * 0.18}) contrast(${
            1.18 + energy * 0.18
          }) saturate(${1.22 + energy * 0.45 + dropImpact * 0.35})`,
        }}
      />

      {/* === ESCURECE BORDAS E PUXA FOCO PRA LOGO === */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(circle at center, transparent 24%, rgba(18,0,48,0.50) 58%, rgba(0,0,0,0.94) 100%)",
        }}
      />

      {/* === NEON ATMOSFERA CENTRAL === */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(circle at 50% 49%, rgba(255,0,255,0.32) 0%, rgba(0,240,255,0.18) 30%, rgba(80,0,255,0.10) 52%, transparent 72%)",
          mixBlendMode: "screen",
          opacity: 0.55 + energy * 0.22 + dropImpact * 0.28,
        }}
      />

      {/* === SCANLINES CYBERPUNK === */}
      <AbsoluteFill
        style={{
          background:
            "repeating-linear-gradient(to bottom, transparent 0px, transparent 5px, rgba(0,240,255,0.12) 5px, rgba(0,240,255,0.12) 6px)",
          opacity: scanOpacity,
          mixBlendMode: "screen",
          pointerEvents: "none",
        }}
      />

      {/* === PARTÍCULAS / FAÍSCAS SIMULADAS === */}
      <AbsoluteFill
        style={{
          background: `
            radial-gradient(circle at ${50 + Math.sin(frame * 0.07) * 22}% ${38 + Math.cos(frame * 0.05) * 18}%, rgba(255,0,255,0.95) 0px, transparent 2px),
            radial-gradient(circle at ${38 + Math.cos(frame * 0.09) * 25}% ${57 + Math.sin(frame * 0.06) * 20}%, rgba(0,240,255,0.95) 0px, transparent 2px),
            radial-gradient(circle at ${62 + Math.sin(frame * 0.11) * 24}% ${64 + Math.cos(frame * 0.08) * 16}%, rgba(255,255,255,0.85) 0px, transparent 2px),
            repeating-radial-gradient(circle at center, rgba(255,0,255,0.18) 0px, rgba(255,0,255,0.18) 1px, transparent 2px, transparent 38px)
          `,
          opacity: particleOpacity,
          mixBlendMode: "screen",
          transform: `scale(${1 + beatPulse * 0.06 + dropImpact * 0.18}) rotate(${frame * 0.05}deg)`,
          pointerEvents: "none",
        }}
      />

      {/* === LINHAS DE ENERGIA SAINDO DO LOGO === */}
      {(beatPulse > 0.55 || dropImpact > 0.12) && (
        <AbsoluteFill
          style={{
            background:
              "conic-gradient(from 0deg at 50% 50%, transparent 0deg, rgba(255,0,255,0.55) 7deg, transparent 12deg, transparent 40deg, rgba(0,240,255,0.55) 48deg, transparent 55deg, transparent 92deg, rgba(255,255,255,0.36) 98deg, transparent 103deg, transparent 145deg, rgba(255,0,255,0.50) 153deg, transparent 160deg, transparent 220deg, rgba(0,240,255,0.42) 228deg, transparent 236deg, transparent 360deg)",
            opacity: (0.16 + beatPulse * 0.16 + dropImpact * 0.42),
            mixBlendMode: "screen",
            filter: `blur(${0.6 + dropImpact * 1.4}px)`,
            transform: `scale(${0.92 + beatPulse * 0.08 + dropImpact * 0.2}) rotate(${frame * 0.6}deg)`,
            pointerEvents: "none",
          }}
        />
      )}

      {/* === FLASH BRANCO/CYAN NO DROP === */}
      {dropImpact > 0.12 && (
        <AbsoluteFill
          style={{
            background:
              "radial-gradient(circle at center, rgba(255,255,255,1) 0%, rgba(0,240,255,0.62) 18%, rgba(255,0,255,0.32) 34%, transparent 66%)",
            opacity: dropImpact * 0.58,
            mixBlendMode: "screen",
            pointerEvents: "none",
          }}
        />
      )}

      {/* === AURA GRANDE DO LOGO === */}
      <Img
        src={staticFile("logo_darkmark.png")}
        style={{
          position: "absolute",
          left: cx,
          top: cy,
          width: Math.min(width, height) * 0.72 * logoScale,
          transform: "translate(-50%, -50%)",
          filter: `blur(${14 + energy * 16 + dropImpact * 24}px) brightness(3.35) saturate(1.4)`,
          opacity: 0.32 + bassPulse * 0.08 + dropImpact * 0.32,
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
          border: `${3.2 + bassPulse * 1.8 + hardDrop * 6}px solid #ff00ff`,
          transform: `translate(-50%, -50%) rotate(${frame * 0.18}deg)`,
          opacity: 0.62 + beatPulse * 0.18 + dropImpact * 0.18,
          boxShadow: `
            0 0 ${glowIntensity * 0.72}px #ff00ff,
            0 0 ${glowIntensity * 0.32}px #00f0ff,
            inset 0 0 ${glowIntensity * 0.30}px #00f0ff
          `,
          zIndex: 4,
        }}
      />

      {/* === RING CIANO SECUNDÁRIO === */}
      <div
        style={{
          position: "absolute",
          left: cx,
          top: cy,
          width: ringSize * 0.82 + beatPulse * 44,
          height: ringSize * 0.82 + beatPulse * 44,
          borderRadius: "50%",
          border: `${1.8 + hardDrop * 2.2}px solid #00f0ff`,
          transform: `translate(-50%, -50%) rotate(${-frame * 0.24}deg)`,
          opacity: 0.35 + bassPulse * 0.18 + dropImpact * 0.32,
          boxShadow: `0 0 ${glowIntensity * 0.55}px #00f0ff`,
          zIndex: 5,
        }}
      />

      {/* === IMPACT WAVE EXPANDINDO === */}
      {(beatPulse > 0.62 || bassPulse > 0.55 || dropImpact > 0.14) && (
        <div
          style={{
            position: "absolute",
            left: cx,
            top: cy,
            width: ringSize + beatPulse * 110 + dropImpact * 250,
            height: ringSize + beatPulse * 110 + dropImpact * 250,
            borderRadius: "50%",
            border: `${1.5 + hardDrop * 2.8}px solid #ffffff`,
            transform: "translate(-50%, -50%)",
            opacity: (0.18 + bassPulse * 0.18 + dropImpact * 0.34) * (1 - beatPhase * 0.42),
            boxShadow: `0 0 ${glowIntensity * 0.45}px #ffffff`,
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
          width: Math.min(width, height) * 0.44,
          transform: `translate(-50%, -50%) scale(${logoScale}) rotate(${logoRotation}deg)`,
          filter: `
            drop-shadow(0 0 ${glowIntensity * 0.92}px #ff00ff)
            drop-shadow(0 0 ${glowIntensity * 0.72}px #00f0ff)
            drop-shadow(0 0 ${glowIntensity * 0.26}px #ffffff)
            brightness(${1.22 + energy * 0.28 + hardDrop * 0.40})
            contrast(${1.18 + beatPulse * 0.14})
          `,
          zIndex: 10,
          pointerEvents: "none",
        }}
      />

      {/* === GLITCH/CHROMA NO DROP === */}
      {dropImpact > 0.28 && (
        <>
          <Img
            src={staticFile("logo_darkmark.png")}
            style={{
              position: "absolute",
              left: cx - 7 * dropImpact,
              top: cy,
              width: Math.min(width, height) * 0.44,
              transform: `translate(-50%, -50%) scale(${logoScale}) rotate(${logoRotation}deg)`,
              opacity: dropImpact * 0.18,
              filter: "drop-shadow(0 0 45px #ff003c)",
              zIndex: 9,
              pointerEvents: "none",
            }}
          />
          <Img
            src={staticFile("logo_darkmark.png")}
            style={{
              position: "absolute",
              left: cx + 7 * dropImpact,
              top: cy,
              width: Math.min(width, height) * 0.44,
              transform: `translate(-50%, -50%) scale(${logoScale}) rotate(${logoRotation}deg)`,
              opacity: dropImpact * 0.18,
              filter: "drop-shadow(0 0 45px #00f0ff)",
              zIndex: 9,
              pointerEvents: "none",
            }}
          />
        </>
      )}

      {/* === VINHETA PESADA === */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(circle, transparent 44%, rgba(0,0,0,0.82) 100%)",
          opacity: 0.78,
          pointerEvents: "none",
          zIndex: 20,
        }}
      />

      {/* === FADE FINAL LIMPO === */}
      <AbsoluteFill
        style={{
          background: "#000",
          opacity: time > duration - 0.75 ? clamp((time - (duration - 0.75)) / 0.75) : 0,
          pointerEvents: "none",
          zIndex: 30,
        }}
      />
    </AbsoluteFill>
  );
};

export default MyComposition;
