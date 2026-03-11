/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        goose: {
          primary: '#4CAF50',
          light: '#81C784',
          dark: '#388E3C',
        },
        duck: {
          primary: '#FF9800',
          light: '#FFB74D',
          dark: '#F57C00',
        },
        dodo: {
          primary: '#9C27B0',
          light: '#BA68C8',
          dark: '#7B1FA2',
        }
      }
    },
  },
  plugins: [],
}
