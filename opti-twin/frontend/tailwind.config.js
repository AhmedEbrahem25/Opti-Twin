/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        steel: {
          50:  "#f4f6f8",
          100: "#e3e8ee",
          500: "#5e7186",
          700: "#374a5c",
          900: "#16202c",
        },
        flame: {
          400: "#ff8a3d",
          500: "#ff6b1a",
          600: "#e2550e",
        },
      },
    },
  },
  plugins: [],
};
