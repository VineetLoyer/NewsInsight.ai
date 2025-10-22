/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  darkMode: 'class', // Enable class-based dark mode
  theme: {
    extend: {
      fontFamily: {
        'headline': ['Playfair Display', 'Georgia', 'Times New Roman', 'serif'],
        'body': ['Crimson Text', 'Georgia', 'Times New Roman', 'serif'],
        'sans': ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        // Parchment theme colors
        parchment: {
          50: '#FEFCF7',   // Lightest parchment
          100: '#FDF9F0',  // Very light parchment
          200: '#F9F1E0',  // Light parchment
          300: '#F5E8CE',  // Medium light parchment
          400: '#F1E9D2',  // Main parchment background
          500: '#E8D5B7',  // Medium parchment
          600: '#D4C4A8',  // Darker parchment
          700: '#B8A082',  // Dark parchment
          800: '#8B7355',  // Very dark parchment
          900: '#5D4E37',  // Darkest parchment
        },
        charcoal: {
          50: '#F7F7F7',   // Very light charcoal
          100: '#E3E3E3',  // Light charcoal
          200: '#C8C8C8',  // Medium light charcoal
          300: '#A4A4A4',  // Medium charcoal
          400: '#717171',  // Medium dark charcoal
          500: '#4A4A4A',  // Main charcoal
          600: '#3A3A3A',  // Dark charcoal
          700: '#2D2D2D',  // Very dark charcoal
          800: '#1F1F1F',  // Darkest charcoal
          900: '#0F0F0F',  // Almost black
        },
        // Keep existing colors for compatibility
        primary: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
        },
        accent: {
          50: '#fafafa',
          100: '#f4f4f5',
          200: '#e4e4e7',
          300: '#d4d4d8',
          400: '#a1a1aa',
          500: '#71717a',
          600: '#52525b',
          700: '#3f3f46',
          800: '#27272a',
          900: '#18181b',
        },
        sentiment: {
          positive: '#16A34A',    // Green
          neutral: '#6B7280',     // Gray
          negative: '#DC2626',    // Red
          // Keep old format for compatibility
          positiveOld: {
            bg: '#ecfdf5',
            text: '#065f46',
            border: '#10b981',
          },
          neutralOld: {
            bg: '#f8fafc',
            text: '#64748b',
            border: '#94a3b8',
          },
          negativeOld: {
            bg: '#fef2f2',
            text: '#dc2626',
            border: '#ef4444',
          }
        }
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        }
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}