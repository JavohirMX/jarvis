/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './landing/templates/**/*.html',
    './static/js/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        'slate-950': '#0a0a0a',
        'jarvis-purple': '#d946ef',
        'jarvis-pink': '#ec4899',
        'jarvis-glow': '#a855f7',
      },
      fontFamily: {
        'sans': ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.6s ease-in-out',
        'slide-up': 'slideUp 0.6s ease-out',
        'float': 'float 6s ease-in-out infinite',
        'orbit-1': 'orbit1 35s ease-in-out infinite',
        'orbit-2': 'orbit2 45s ease-in-out infinite',
        'orbit-3': 'orbit3 50s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-20px)' },
        },
        orbit1: {
          '0%': { transform: 'translate(0px, 0px) rotate(0deg) scale(1)' },
          '25%': { transform: 'translate(40vw, -30vh) rotate(90deg) scale(1.1)' },
          '50%': { transform: 'translate(-35vw, 35vh) rotate(180deg) scale(0.9)' },
          '75%': { transform: 'translate(30vw, 25vh) rotate(270deg) scale(1.05)' },
          '100%': { transform: 'translate(0px, 0px) rotate(360deg) scale(1)' },
        },
        orbit2: {
          '0%': { transform: 'translate(0px, 0px) rotate(0deg) scale(1)' },
          '20%': { transform: 'translate(-45vw, 30vh) rotate(72deg) scale(1.15)' },
          '40%': { transform: 'translate(35vw, -25vh) rotate(144deg) scale(0.85)' },
          '60%': { transform: 'translate(-30vw, -35vh) rotate(216deg) scale(1.1)' },
          '80%': { transform: 'translate(40vw, 20vh) rotate(288deg) scale(0.95)' },
          '100%': { transform: 'translate(0px, 0px) rotate(360deg) scale(1)' },
        },
        orbit3: {
          '0%': { transform: 'translate(0px, 0px) rotate(0deg) scale(1)' },
          '16.66%': { transform: 'translate(35vw, 40vh) rotate(60deg) scale(1.08)' },
          '33.33%': { transform: 'translate(-40vw, -20vh) rotate(120deg) scale(0.92)' },
          '50%': { transform: 'translate(25vw, -35vh) rotate(180deg) scale(1.12)' },
          '66.66%': { transform: 'translate(-35vw, 30vh) rotate(240deg) scale(0.88)' },
          '83.33%': { transform: 'translate(45vw, -25vh) rotate(300deg) scale(1.05)' },
          '100%': { transform: 'translate(0px, 0px) rotate(360deg) scale(1)' },
        },
      },
    },
  },
  plugins: [],
}

