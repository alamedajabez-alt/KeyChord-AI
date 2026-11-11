/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: { 950: "#0a0b10", 900: "#10121a", 800: "#171a25", 700: "#212535" },
        accent: { DEFAULT: "#7c6cff", soft: "#a79bff" },
      },
    },
  },
  plugins: [],
};
