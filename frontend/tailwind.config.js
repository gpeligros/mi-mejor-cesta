/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        "primary": "#13ec49",
        "background-dark": "#102215",
        "surface-dark": "#1a2e20",
      },
    },
  },
  plugins: [],
}