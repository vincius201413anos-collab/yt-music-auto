import { useEffect, useState } from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  staticFile,
  useVideoConfig,
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
    if (typeof v === "number") {
      total += v;
      count++;
    }
  }
  return count ? total / count : 0;
};

export const MyComposition = () => {
  const frame = useCurrentFrame();
  const { fps, width, height, durationInFrames } = useVideoConfig();

  const [rms, setRms] = useState<number[]>([]);
  const [bpm, setBpm] = useState(120);
  const [dropTime, setDropTime] = useState<number | null>(null);

  useEffect(() => {
    fetch(staticFile("audio_data.json"))
      .then((r) => r.json())
      .then((data) => {
        setRms(data.rms || data.audio_data || []);
        setBpm(data.bpm || 120);
        setDropTime(data.drop_time ?? null);
      });
  }, []);

  const time = frame / fps;
  const audioIndex = Math.floor(time * 60);

  const energy = clamp(smooth(rms, audioIndex, 4) * 1.6);

  // 🔥 SINCRONIZAÇÃO REAL COM BPM
  const beatInterval = fps * (60 / bpm);
  const beatPhase = (frame % beatInterval) / beatInterval;

  const beatPulse = Math.sin(beatPhase * Math.PI);

  // 💀 DETECTA DROP
  const drop = dropTime ?? durationInFrames / fps * 0.4;
  const dropDist = Math.abs(time - drop);
  const dropImpact = clamp(1 - dropDist / 0.5);

  // 🔥 ANIMAÇÃO DO LOGO (NÍVEL VIRAL)
  const scale =
    1 +
    beatPulse * 0.08 +
    energy * 0.15 +
    dropImpact * 0.4;

  const rotation =
    Math.sin(frame * 0.02) * 1 +
    dropImpact * Math.sin(frame * 0.6) * 4;

  const glow =
    20 +
    energy * 40 +
    dropImpact * 120;

  const shake = dropImpact * 15;

  const cx = width / 2;
  const cy = height / 2;

  return (
    <AbsoluteFill style={{ background: "#050005" }}>
      
      {/* 🎬 VIDEO FUNDO */}
      <AbsoluteFill
        style={{
          transform: `scale(${1.05 + energy * 0.03}) translate(${Math.sin(frame)*shake}px, ${Math.cos(frame)*shake}px)`
        }}
      >
        <Video
          src={staticFile("input.mp4")}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </AbsoluteFill>

      {/* 🌌 VIGNETTE */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(circle, transparent 30%, rgba(0,0,0,0.85) 100%)",
        }}
      />

      {/* 💥 FLASH NO DROP */}
      {dropImpact > 0.1 && (
        <AbsoluteFill
          style={{
            background: "white",
            opacity: dropImpact * 0.4,
            mixBlendMode: "screen",
          }}
        />
      )}

      {/* 🔮 AURA */}
      <img
        src={staticFile("logo_darkmark.png")}
        style={{
          position: "absolute",
          left: cx,
          top: cy,
          width: 500 * scale,
          transform: "translate(-50%, -50%)",
          filter: `blur(${8 + energy * 12 + dropImpact * 25}px) brightness(3)`,
          opacity: 0.2,
        }}
      />

      {/* 🔥 LOGO PRINCIPAL */}
      <img
        src={staticFile("logo_darkmark.png")}
        style={{
          position: "absolute",
          left: cx,
          top: cy,
          width: 420,
          transform: `translate(-50%, -50%) scale(${scale}) rotate(${rotation}deg)`,
          filter: `
            drop-shadow(0 0 ${glow}px #7B00FF)
            drop-shadow(0 0 ${glow * 1.2}px #00EEFF)
          `,
        }}
      />

      {/* 💣 RING REATIVO */}
      <div
        style={{
          position: "absolute",
          left: cx,
          top: cy,
          width: 500 + beatPulse * 50 + dropImpact * 200,
          height: 500 + beatPulse * 50 + dropImpact * 200,
          borderRadius: "50%",
          border: `${2 + dropImpact * 4}px solid #7B00FF`,
          transform: "translate(-50%, -50%)",
          opacity: 0.5 + beatPulse * 0.3,
          boxShadow: `0 0 ${glow}px #7B00FF`,
        }}
      />

      {/* 🎯 ZOOM FINAL */}
      <AbsoluteFill
        style={{
          background: "#000",
          opacity: time > (durationInFrames / fps - 1)
            ? (time - (durationInFrames / fps - 1))
            : 0,
        }}
      />
    </AbsoluteFill>
  );
};

export default MyComposition;
