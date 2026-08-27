/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,jsx,mdx}",
    "./components/**/*.{js,jsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: "#0A0C11",
          raised: "#13161F",
          overlay: "#191D29",
          line: "#262B3A",
          muted: "#8891A6",
          soft: "#B7BECC",
          bright: "#F3F1E9",
        },
        paper: {
          DEFAULT: "#EDE6D2",
          raised: "#F5F0E2",
          line: "#C7BB98",
          muted: "#7A7156",
          ink: "#211B10",
        },
        signal: {
          amber: "#D99A3C",
          "amber-ink": "#5C3C13",
          "amber-soft": "#3A2A14",
          green: "#5FA173",
          "green-ink": "#1F4029",
          "green-soft": "#16241C",
          red: "#C1543D",
          "red-ink": "#5A2015",
          "red-soft": "#2E1712",
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
