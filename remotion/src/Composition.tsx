import { useEffect, useState } from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  staticFile,
  useVideoConfig,
  Video,
} from "remotion";

export const MyComposition = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const [audioData, setAudioData] = useState<number[]>([]);

  useEffect(() => {
    fetch(staticFile("audio_data.json"))
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setAudioData(data);
        } else if (Array.isArray(data.rms)) {
          setAudioData(data.rms);
        } else if (Array.isArray(data.audio_data)) {
          setAudioData(data.audio_data);
        } else {
          setAudioData([]);
        }
      })
      .catch(() => setAudioData([]));
  }, []);

  const audioIndex = Math.floor((frame / fps) * 60);
  const audioValue = audioData[audioIndex] || 0;

  const beat = Math.min(1, audioValue * 1.6);
  const bass = Math.min(1, audioValue * 1.2);
  const drop = audioValue > 0.62 ? 1 : 0;

  const shake = drop ? 10 : bass * 3;
  const scale = 1 + beat * 0.08 + bass * 0.08 + drop * 0.22;
  const glow = 55 + beat * 35 + bass * 45 + drop * 90;
  const rotate = Math.sin(frame * 0.045) * 3;

  return (
    <AbsoluteFill
      style={{
        background: "#000",
        overflow: "hidden",
      }}
    >
      {/* VÍDEO BASE GERADO PELO FFMPEG */}
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

      {/* CAMADA ESCURA PARA O LOGO/EFEITOS FICAREM MAIS BONITOS */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(circle at center, rgba(36,0,47,0.30) 0%, rgba(7,0,16,0.45) 45%, rgba(0,0,0,0.35) 100%)",
          transform: `translate(${Math.sin(frame) * shake}px, ${
            Math.cos(frame * 1.3) * shake
          }px)`,
        }}
      />

      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(circle, rgba(255,0,255,0.65), rgba(0,255,255,0.22), transparent 62%)",
          opacity: 0.04 + beat * 0.08 + drop * 0.35,
        }}
      />

      {[0, 1, 2].map((i) => (
        <div
          key={`leak-${i}`}
          style={{
            position: "absolute",
            width: 500,
            height: 1200,
            background:
              i % 2 === 0
                ? "linear-gradient(90deg, transparent, rgba(255,0,255,0.18), transparent)"
                : "linear-gradient(90deg, transparent, rgba(0,255,255,0.16), transparent)",
            transform: `translateX(${
              ((frame * (3 + i) + i * 500) % 2600) - 1300
            }px) rotate(${20 + i * 18}deg)`,
            filter: "blur(25px)",
            opacity: 0.5,
          }}
        />
      ))}

      {[720, 600, 500].map((size, i) => {
        const color = i % 2 === 0 ? "#ff00ff" : "#00ffff";

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
              border: `${4 - i}px solid ${color}`,
              boxShadow: `0 0 ${glow}px ${color}, inset 0 0 ${
                glow * 0.45
              }px ${color}`,
              transform: `translate(-50%, -50%) rotate(${
                frame * (0.6 + i * 0.35)
              }deg) scale(${1 + beat * 0.025 + drop * 0.08})`,
              opacity: 0.75 - i * 0.12,
            }}
          />
        );
      })}

      {[0, 1, 2, 3].map((i) => {
        const wave = ((frame + i * 18) % 90) / 90;

        return (
          <div
            key={`wave-${i}`}
            style={{
              position: "absolute",
              left: "50%",
              top: "50%",
              width: 430 + wave * 700,
              height: 430 + wave * 700,
              borderRadius: "50%",
              border: `2px solid ${i % 2 ? "#00ffff" : "#ff00ff"}`,
              opacity: (1 - wave) * (0.35 + drop * 0.35),
              boxShadow: `0 0 ${40 + drop * 50}px ${
                i % 2 ? "#00ffff" : "#ff00ff"
              }`,
              transform: "translate(-50%, -50%)",
            }}
          />
        );
      })}

      {[...Array(95)].map((_, i) => {
        const speed = 0.7 + (i % 7) * 0.16;
        const y = (frame * speed + i * 53) % 1080;
        const x = (i * 137 + Math.sin(frame * 0.03 + i) * 60) % 1920;
        const color =
          i % 3 === 0 ? "#ff00ff" : i % 3 === 1 ? "#00ffff" : "#9b5cff";

        return (
          <div
            key={`p-${i}`}
            style={{
              position: "absolute",
              left: x,
              top: y,
              width: i % 4 === 0 ? 6 : 3,
              height: i % 4 === 0 ? 6 : 3,
              borderRadius: "50%",
              background: color,
              opacity: 0.25 + beat * 0.35 + drop * 0.25,
              boxShadow: `0 0 22px ${color}`,
            }}
          />
        );
      })}

      {[...Array(32)].map((_, i) => {
        const h =
          35 +
          audioValue * (180 + drop * 220) +
          Math.abs(Math.sin(frame * 0.18 + i * 0.7)) * 80;

        return (
          <div
            key={`bar-l-${i}`}
            style={{
              position: "absolute",
              left: 60 + i * 10,
              top: "50%",
              width: 5,
              height: h,
              background: "#ff00ff",
              opacity: 0.55,
              transform: "translateY(-50%)",
              boxShadow: "0 0 18px #ff00ff",
            }}
          />
        );
      })}

      {[...Array(32)].map((_, i) => {
        const h =
          35 +
          audioValue * (180 + drop * 220) +
          Math.abs(Math.sin(frame * 0.2 + i * 0.9)) * 80;

        return (
          <div
            key={`bar-r-${i}`}
            style={{
              position: "absolute",
              right: 60 + i * 10,
              top: "50%",
              width: 5,
              height: h,
              background: "#00ffff",
              opacity: 0.55,
              transform: "translateY(-50%)",
              boxShadow: "0 0 18px #00ffff",
            }}
          />
        );
      })}

      {/* LOGO / ÍCONE REATIVO */}
      <img
        src={staticFile("logo.png")}
        style={{
          position: "absolute",
          left: "50%",
          top: "50%",
          width: 560,
          transform: `translate(-50%, -50%) scale(${scale}) rotate(${rotate}deg)`,
          filter: `drop-shadow(0 0 ${glow}px #00ffff) drop-shadow(0 0 ${
            glow * 1.7
          }px #ff00ff) brightness(${
            1.15 + beat * 0.35 + drop * 0.3
          }) contrast(1.16)`,
        }}
      />
    </AbsoluteFill>
  );
};
