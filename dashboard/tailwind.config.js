export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        brand: { DEFAULT: '#7c6fff', light: '#a78bfa', dark: '#5b4fd1' },
        surface: { DEFAULT: '#111118', raised: '#1a1a2e', border: '#2a2a40' }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif']
      }
    }
  },
  plugins: []
}
