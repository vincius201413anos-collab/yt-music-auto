import { Composition } from "remotion";
import { MyComposition } from "./Composition";

export const RemotionRoot = () => {
  return (
    <>
      <Composition
        id="MyComposition"
        component={MyComposition}
        durationInFrames={1800} // 60 segundos (30fps)
        fps={30}
        width={1080}
        height={1920}
      />
    </>
  );
};
