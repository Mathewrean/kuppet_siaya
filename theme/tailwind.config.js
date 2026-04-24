/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static_src/**/*.{html,js,css}",
    "../core/templates/**/*.html",
    "../accounts/templates/**/*.html",
    "../dashboard/templates/**/*.html",
  ],
  theme: {
    extend: {
      colors: {
        'primary-green': '#006633',
        'secondary-yellow': '#FFCC00',
      },
    },
  },
  plugins: [],
}
