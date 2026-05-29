/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        soc: {
          bg:          "#0a0a0a",
          surface:     "#0d1117",
          card:        "#161b22",
          border:      "#21262d",
          green:       "#00ff41",
          "green-dim": "#00cc33",
          red:         "#ff0040",
          "red-dim":   "#cc0033",
          amber:       "#f59e0b",
          blue:        "#58a6ff",
          muted:       "#8b949e",
          text:        "#c9d1d9",
          "text-dim":  "#6e7681",
        },
      },
      fontFamily: {
        mono: ["'JetBrains Mono'", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        "glow-green": "0 0 8px rgba(0,255,65,0.35)",
        "glow-red":   "0 0 8px rgba(255,0,64,0.35)",
        "glow-amber": "0 0 8px rgba(245,158,11,0.35)",
      },
      keyframes: {
        blink: {
          "0%,100%": { opacity: "1" },
          "50%":     { opacity: "0" },
        },
      },
      animation: {
        blink: "blink 1s step-end infinite",
      },
    },
  },
  plugins: [],
}
