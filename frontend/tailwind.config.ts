import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Surface layers
        surface: {
          DEFAULT: '#18181b', // zinc-900
          raised: '#27272a',  // zinc-800
          overlay: '#3f3f46', // zinc-700
        },
        border: {
          DEFAULT: 'rgba(255,255,255,0.08)',
          subtle: 'rgba(255,255,255,0.04)',
          strong: 'rgba(255,255,255,0.14)',
        },
        brand: {
          DEFAULT: '#6366f1', // indigo-500
          hover: '#818cf8',   // indigo-400
          dim: 'rgba(99,102,241,0.10)',
          glow: 'rgba(99,102,241,0.22)',
        },
        // Glass helpers (reference CSS vars)
        glass: {
          DEFAULT: 'rgba(18,18,21,0.72)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'ui-monospace', 'monospace'],
      },
      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '0.875rem' }],
      },
      borderRadius: {
        sm: '6px',
        DEFAULT: '8px',
        md: '10px',
        lg: '14px',
        xl: '18px',
      },
      boxShadow: {
        'xs': '0 1px 2px rgba(0,0,0,0.45)',
        'sm': '0 2px 6px rgba(0,0,0,0.45), 0 1px 2px rgba(0,0,0,0.3)',
        'md': '0 4px 14px rgba(0,0,0,0.55), 0 1px 3px rgba(0,0,0,0.35)',
        'lg': '0 8px 28px rgba(0,0,0,0.65), 0 2px 8px rgba(0,0,0,0.4)',
        'glow': '0 0 0 1px rgba(99,102,241,0.35), 0 0 18px rgba(99,102,241,0.22)',
        'glow-sm': '0 0 0 1px rgba(99,102,241,0.25), 0 0 10px rgba(99,102,241,0.14)',
        'inner-highlight': 'inset 0 1px 0 rgba(255,255,255,0.035)',
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-out both',
        'enter': 'enter 0.2s cubic-bezier(0.16,1,0.3,1) both',
        'enter-fast': 'enter 0.12s cubic-bezier(0.16,1,0.3,1) both',
        'slide-up': 'slideUp 0.22s cubic-bezier(0.16,1,0.3,1) both',
        'scale-in': 'scaleIn 0.14s cubic-bezier(0.34,1.56,0.64,1) both',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        enter: {
          '0%': { opacity: '0', transform: 'translateY(6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
      },
      transitionTimingFunction: {
        'spring': 'cubic-bezier(0.34, 1.56, 0.64, 1)',
        'out-expo': 'cubic-bezier(0.16, 1, 0.3, 1)',
      },
      transitionDuration: {
        '120': '120ms',
        '250': '250ms',
        '350': '350ms',
      },
      backdropBlur: {
        xs: '6px',
        sm: '10px',
        DEFAULT: '14px',
        lg: '20px',
        xl: '28px',
      },
    },
  },
  plugins: [],
}

export default config
