/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#090B0A", fg: "#F4F4F5", muted: "#121613", mutedfg: "#8E9991", line: "#28312A",
        accent: { DEFAULT: "#1ED760", soft: "#1ED760", dim: "#1ED760" },
        // legacy aliases for untouched files (src/src/*)
        ink: { 950: "#0E0F11", 900: "#0E0F11", 800: "#17191C", 700: "#2A2D31", 600: "#2A2D31" },
        ok: "#B89B6A", warn: "#EFE8DC", bad: "#EFE8DC",
      },
      fontFamily: { sans: ['"DM Sans"', "ui-sans-serif", "system-ui", "sans-serif"], mono: ['"DM Sans"', "ui-monospace", "monospace"] },
      borderRadius: { none: "0", sm: "2px", DEFAULT: "2px", md: "2px", lg: "2px", xl: "2px", full: "9999px" },
    },
  },
  plugins: [],
};
