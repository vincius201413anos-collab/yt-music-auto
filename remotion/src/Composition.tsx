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
      beats?: number[];
      bass_hits?: number[];
      drop_time?: number | null;
    };

const clamp = (v: number, min = 0, max = 1) =>
  Math.max(min, Math.min(max, v));

export const MyComposition = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const [rms, setRms] = useState<number[]>([]);
  const [beats, setBeats] = useState<number[]>([]);
  const [bassHits, setBassHits] = useState<number[]>([]);
  const [dropTime, setDropTime] = useState<number | null>(null);

  useEffect(() => {
    fetch(staticFile("audio_data.json"))
      .then((r) => r.json())
      .then((data: AudioPayload) => {
        if (Array.isArray(data)) {
          setRms(data);
          return;
        }
        setRms(data.rms || []);
        setBeats(data.beats || []);
        setBassHits(data.bass_hits || []);
        setDropTime(data.drop_time ?? null);
      });
  }, []);

  const time = frame / fps;
  const progress = frame / durationInFrames;

  const index = Math.floor(time * 60);
  const val = rms[index] || 0;

  const beat = beats.some((b) => Math.abs(time - b) < 0.05) ? 1 : 0;
  const bass = bassHits.some((b) => Math.abs(time - b) < 0.06) ? 1 : 0;
  const drop =
    dropTime !== null ? Math.max(0, 1 - Math.abs(time - dropTime)) : 0;

  const energy = clamp(val * 2);
  const zoom = 1 + beat * 0.02 + drop * 0.06;
  const glow = 30 + energy * 80 + drop * 120;
  const logoScale = 1 + beat * 0.12 + drop * 0.25;

  return (
    <AbsoluteFill style={{ background: "#000" }}>
      {/* VIDEO */}
      <AbsoluteFill
        style={{
          transform: `scale(${zoom})`,
          filter: `brightness(${0.8 + energy * 0.4}) contrast(1.2)`,
        }}
      >
        <Video
          src={staticFile("input.mp4")}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </AbsoluteFill>

      {/* VIGNETTE */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(circle, transparent 50%, rgba(0,0,0,0.8) 100%)",
        }}
      />

      {/* FLASH DROP */}
      <AbsoluteFill
        style={{
          background: "#fff",
          opacity: drop * 0.5 + beat * 0.1,
          mixBlendMode: "screen",
        }}
      />

      {/* LOGO CENTRAL */}
      <img
        src={staticFile("logo.png")}
        style={{
          position: "absolute",
          left: "50%",
          top: "50%",
          width: 520,
          transform: `translate(-50%, -50%) scale(${logoScale})`,
          filter: `drop-shadow(0 0 ${glow}px #ff00ff)`,
        }}
      />

      {/* SCANLINES (HIPNÓTICO) */}
      <AbsoluteFill
        style={{
          background:
            "repeating-linear-gradient(0deg, transparent, transparent 3px, rgba(255,255,255,0.05) 3px, rgba(255,255,255,0.05) 4px)",
          opacity: 0.15,
        }}
      />

      {/* 🔥 TÍTULO EMBAIXO (CORRIGIDO) */}
      <div
        style={{
          position: "absolute",
          bottom: "14%",
          left: "50%",
          transform: "translateX(-50%)",
          textAlign: "center",
          color: "#fff",
          fontSize: 48,
          fontWeight: 900,
          textShadow:
            "0 0 10px #ff005e, 0 0 30px #ff005e, 1px 1px 0 #000",
          lineHeight: 1.2,
          letterSpacing: "2px",
          maxWidth: "80%",
        }}
      >
        NIGHT DRIVE<br />PHONK ENERGY
      </div>

      {/* 🎯 PROGRESS BAR (VÍCIO) */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          height: 6,
          width: `${progress * 100}%`,
          background: "linear-gradient(90deg,#ff005e,#ff4d88)",
          boxShadow: "0 0 10px #ff005e",
        }}
      />

      {/* FADE FINAL */}
      <AbsoluteFill
        style={{
          background: "#000",
          opacity: progress > 0.92 ? (progress - 0.92) / 0.08 : 0,
        }}
      />
    </AbsoluteFill>
  );
};
