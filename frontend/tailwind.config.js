export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          900: '#1B4332',
          800: '#2D6A4F',
          700: '#40916C',
          600: '#52B788',
          500: '#74C69D',
          400: '#95D5B2',
          300: '#B7E4C7',
          200: '#D8F3DC',
        },
        accent: {
          700: '#5C3D11',
          600: '#7B5B3A',
          500: '#A67C52',
          400: '#C9A87C',
          300: '#E6D5B8',
        },
        surface: {
          50: '#FFFFFF',
          100: '#FAFAFA',
          200: '#F5F5F5',
          300: '#EEEEEE',
          400: '#E0E0E0',
          500: '#BDBDBD',
          600: '#9E9E9E',
        },
        text: {
          900: '#1A1A1A',
          700: '#4A4A4A',
          500: '#717171',
          400: '#9E9E9E',
          300: '#BDBDBD',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Outfit', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
}