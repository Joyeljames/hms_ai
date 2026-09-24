import { useEffect, useState } from "react";

export default function Splash({ onDone }) {
  const [stage, setStage] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setStage(1), 200),   // logo
      setTimeout(() => setStage(2), 900),   // title
      setTimeout(() => setStage(3), 1600),  // subtitle
      setTimeout(() => setStage(4), 2600),  // fade out
      setTimeout(() => onDone(), 3200),     // done
    ];
    return () => timers.forEach(clearTimeout);
  }, [onDone]);

  return (
    <div
      onClick={onDone}
      className={`fixed inset-0 z-50 flex cursor-pointer flex-col items-center justify-center bg-white transition-opacity duration-600 ${
        stage >= 4 ? "opacity-0" : "opacity-100"
      }`}
    >
      {/* PULSE RING + LOGO */}
      <div className="relative mb-8">
        <span
          className={`absolute inset-0 rounded-3xl bg-gray-900/10 transition-all duration-1000 ${
            stage >= 1 ? "scale-[1.8] opacity-0" : "scale-100 opacity-100"
          }`}
        />
        <div
          className={`relative flex h-20 w-20 items-center justify-center rounded-3xl bg-gray-900 transition-all duration-700 ${
            stage >= 1
              ? "scale-100 rotate-0 opacity-100"
              : "scale-50 -rotate-12 opacity-0"
          }`}
        >
          <Cross />
        </div>
      </div>

          {/* TITLE */}
      <h1
        className={`mb-1 text-center text-3xl font-semibold tracking-tight text-gray-900 transition-all duration-700 md:text-4xl ${
          stage >= 2 ? "translate-y-0 opacity-100" : "translate-y-4 opacity-0"
        }`}
      >
        Joyel's <span className="text-gray-400">AI</span>
      </h1>

      {/* LINE */}
      <div
        className={`my-3 h-px bg-gray-900 transition-all duration-700 ${
          stage >= 2 ? "w-28 opacity-100" : "w-0 opacity-0"
        }`}
      />

      {/* SUBTITLE */}
      <p
        className={`max-w-xs text-center text-base text-gray-600 transition-all duration-700 md:text-lg ${
          stage >= 3 ? "translate-y-0 opacity-100" : "translate-y-3 opacity-0"
        }`}
      >
        AI powered software for HMS
      </p>

      
      {/* FOOTER */}
      <div
        className={`absolute bottom-10 text-center transition-opacity duration-700 ${
          stage >= 3 ? "opacity-100" : "opacity-0"
        }`}
      >
        <p className="text-xs tracking-widest text-gray-400 uppercase">
          Built in Nagercoil
        </p>
      </div>
    </div>
  );
}

function Cross() {
  return (
    <svg width="34" height="34" viewBox="0 0 24 24" fill="none">
      <path
        d="M10 3h4v7h7v4h-7v7h-4v-7H3v-4h7V3z"
        fill="white"
        className="animate-[draw_0.8s_ease-out]"
      />
    </svg>
  );
}