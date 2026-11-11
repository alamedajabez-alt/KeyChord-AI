/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: { 950: "#0a0b10", 900: "#10121a", 800: "#171a25", 700: "#212535", 600: "#2e3347" },
        accent: { DEFAULT: "#7c6cff", soft: "#a79bff", dim: "#4c3fd1" },
        ok: "#34d399",
        warn: "#fbbf24",
        bad: "#f87171",
      },
      fontFamily: {
        sans: ['"Inter"', "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      fontSize: {
        display: ["clamp(2.25rem, 5vw, 3.75rem)", { lineHeight: "1.05", letterSpacing: "-0.02em" }],
      },
      boxShadow: { glow: "0 0 0 1px rgba(124,108,255,.35), 0 8px 30px -8px rgba(124,108,255,.35)" },
    },
  },
  plugins: [],
};
