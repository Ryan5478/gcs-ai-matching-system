/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  "#eef4ff", 100: "#dbe6ff", 500: "#3b6ef5",
          600: "#2554d6", 700: "#1c42ab", 900: "#0d1f4d",
        },
        neon: {
          indigo: "#6366f1",
          purple: "#a855f7",
          cyan:   "#22d3ee",
          pink:   "#ec4899",
          teal:   "#14b8a6",
        },
        void: {
          900: "#06060f",
          800: "#0a0a18",
          700: "#0f0f22",
          600: "#14142e",
          500: "#1a1a3a",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      animation: {
        "gradient-shift": "gradient-shift 8s ease infinite",
        "shimmer":        "shimmer 3s linear infinite",
        "glow-pulse":     "glow-pulse 2.5s ease-in-out infinite",
        "scanline":       "scanline 6s linear infinite",
        "float":          "float 6s ease-in-out infinite",
        "fade-in-up":     "fade-in-up 0.6s ease-out both",
        "orb-drift":      "orb-drift 18s ease-in-out infinite",
        "spin-slow":      "spin 8s linear infinite",
        "pulse-ring":     "pulse-ring 2s ease-out infinite",
      },
      keyframes: {
        "gradient-shift": {
          "0%, 100%": { "background-position": "0% 50%" },
          "50%":      { "background-position": "100% 50%" },
        },
        shimmer: {
          "0%":   { "background-position": "-1000px 0" },
          "100%": { "background-position": "1000px 0" },
        },
        "glow-pulse": {
          "0%, 100%": { "box-shadow": "0 0 20px rgba(99,102,241,0.25), 0 0 40px rgba(168,85,247,0.15)" },
          "50%":      { "box-shadow": "0 0 40px rgba(99,102,241,0.55), 0 0 80px rgba(168,85,247,0.35)" },
        },
        scanline: {
          "0%":   { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100vh)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%":      { transform: "translateY(-8px)" },
        },
        "fade-in-up": {
          "0%":   { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "orb-drift": {
          "0%, 100%": { transform: "translate(0, 0) scale(1)" },
          "33%":      { transform: "translate(80px, -60px) scale(1.1)" },
          "66%":      { transform: "translate(-60px, 40px) scale(0.95)" },
        },
        "pulse-ring": {
          "0%":   { transform: "scale(0.9)", opacity: "1" },
          "100%": { transform: "scale(1.6)", opacity: "0" },
        },
      },
      backdropBlur: { xs: "2px" },
    },
  },
  plugins: [],
};
