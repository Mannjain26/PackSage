/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#123B5D",
        secondary: "#1976A8",
        accent: "#19A974",
        warning: "#E5A11A",
        danger: "#D64545",
        background: "#F6F8FA",
        surface: "#FFFFFF",
        dark: "#17202A",
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
