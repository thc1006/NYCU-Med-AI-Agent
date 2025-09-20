/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 醫療藍綠色系
        medical: {
          50: '#f0fdf9',
          100: '#ccfbf1',
          200: '#99f6e4',
          300: '#5eead4',
          400: '#2dd4bf',
          500: '#14b8a6',
          600: '#0891b2',
          700: '#0e7490',
          800: '#155e75',
          900: '#164e63',
        },
        // 現代化藍色
        brand: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0891b2',
          600: '#06b6d4',
          700: '#0284c7',
          800: '#0369a1',
          900: '#0c4a6e',
        },
        // 溫暖珊瑚色
        accent: {
          50: '#fef7f0',
          100: '#fde6cc',
          200: '#fbcc99',
          300: '#f9b366',
          400: '#f79a33',
          500: '#f97316',
          600: '#ea6a13',
          700: '#db6110',
          800: '#cc580d',
          900: '#bd4f0a',
        },
        // 玻璃效果漸層
        glass: {
          light: 'rgba(255, 255, 255, 0.25)',
          medium: 'rgba(255, 255, 255, 0.18)',
          dark: 'rgba(255, 255, 255, 0.1)',
        }
      },
      backgroundImage: {
        'gradient-medical': 'linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 25%, #f0fdf9 50%, #fef7f0 100%)',
        'gradient-glass': 'linear-gradient(135deg, rgba(255,255,255,0.25) 0%, rgba(255,255,255,0.18) 50%, rgba(255,255,255,0.1) 100%)',
        'gradient-brand': 'linear-gradient(135deg, #0891b2 0%, #06b6d4 50%, #14b8a6 100%)',
        'gradient-accent': 'linear-gradient(135deg, #f97316 0%, #ea6a13 100%)',
      },
      backdropBlur: {
        xs: '2px',
        '3xl': '64px',
      },
      animation: {
        'float': 'float 6s ease-in-out infinite',
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite alternate',
        'slide-up': 'slide-up 0.5s ease-out',
        'fade-in': 'fade-in 0.3s ease-out',
        'scale-in': 'scale-in 0.3s ease-out',
        'bounce-soft': 'bounce-soft 2s infinite',
      },
      keyframes: {
        'float': {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        'pulse-glow': {
          '0%': {
            boxShadow: '0 0 20px rgba(8, 145, 178, 0.3)',
            transform: 'scale(1)'
          },
          '100%': {
            boxShadow: '0 0 40px rgba(8, 145, 178, 0.6)',
            transform: 'scale(1.02)'
          },
        },
        'slide-up': {
          '0%': {
            opacity: '0',
            transform: 'translateY(20px)'
          },
          '100%': {
            opacity: '1',
            transform: 'translateY(0)'
          },
        },
        'fade-in': {
          '0%': {
            opacity: '0',
            transform: 'translateY(10px)'
          },
          '100%': {
            opacity: '1',
            transform: 'translateY(0)'
          },
        },
        'scale-in': {
          '0%': {
            opacity: '0',
            transform: 'scale(0.9)'
          },
          '100%': {
            opacity: '1',
            transform: 'scale(1)'
          },
        },
        'bounce-soft': {
          '0%, 100%': {
            transform: 'translateY(0%)',
            animationTimingFunction: 'cubic-bezier(0.8, 0, 1, 1)'
          },
          '50%': {
            transform: 'translateY(-5%)',
            animationTimingFunction: 'cubic-bezier(0, 0, 0.2, 1)'
          },
        },
      },
      fontFamily: {
        sans: ['Inter', 'Noto Sans TC', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['Plus Jakarta Sans', 'Inter', 'Noto Sans TC', 'sans-serif'],
      },
      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '0.75rem' }],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
      },
      borderRadius: {
        '4xl': '2rem',
        '5xl': '2.5rem',
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
        'glow': '0 0 20px rgba(8, 145, 178, 0.3)',
        'glow-accent': '0 0 20px rgba(249, 115, 22, 0.3)',
        'soft': '0 2px 15px -3px rgba(0, 0, 0, 0.07), 0 10px 20px -2px rgba(0, 0, 0, 0.04)',
        'card': '0 4px 20px -2px rgba(0, 0, 0, 0.08)',
        'float': '0 20px 40px -12px rgba(0, 0, 0, 0.15)',
      },
    },
  },
  plugins: [],
}