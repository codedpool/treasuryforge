/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,jsx,mdx}",
    "./components/**/*.{js,jsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Every value below is sampled from harness3.png (the lake-at-dusk
        // hero art): ink is the deep navy of the sky and its reflection in
        // the water; paper is the sunlit cumulus/cabin cream; signal takes
        // its three hues from the maple-red trees, the blue-green trees,
        // and the warm gold light on the clouds and cabin windows.
        ink: {
          DEFAULT: "#14324B",
          raised: "#1C3E5A",
          overlay: "#24496B",
          line: "#35597A",
          muted: "#8FA7BC",
          soft: "#C7D6E1",
          bright: "#F6EEDD",
        },
        paper: {
          DEFAULT: "#F3EAD6",
          raised: "#FAF5E9",
          line: "#DCC9A0",
          muted: "#6E5E42",
          ink: "#1C3348",
        },
        signal: {
          amber: "#C6923F",
          "amber-ink": "#6B4A17",
          "amber-soft": "#3A2E17",
          green: "#4C7A68",
          "green-ink": "#1F3D33",
          "green-soft": "#1B2E27",
          red: "#B24734",
          "red-ink": "#6B2418",
          "red-soft": "#3A1D15",
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "Georgia", "serif"],
        body: ["var(--font-body)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      letterSpacing: {
        wideish: "0.04em",
        stamp: "0.14em",
      },
      keyframes: {
        "stamp-land": {
          "0%": { transform: "scale(1.6) rotate(var(--stamp-rot, -4deg))", opacity: "0" },
          "55%": { transform: "scale(0.94) rotate(var(--stamp-rot, -4deg))", opacity: "1" },
          "72%": { transform: "scale(1.04) rotate(var(--stamp-rot, -4deg))" },
          "100%": { transform: "scale(1) rotate(var(--stamp-rot, -4deg))", opacity: "1" },
        },
        "fade-up": {
          "0%": { transform: "translateY(10px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        "ticker-blink": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.35" },
        },
      },
      animation: {
        "stamp-land": "stamp-land 480ms cubic-bezier(.2,1.6,.4,1) both",
        "fade-up": "fade-up 500ms ease-out both",
        "ticker-blink": "ticker-blink 1.6s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
