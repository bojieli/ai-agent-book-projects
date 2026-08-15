/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
      },
      keyframes: {
        "accordion-down": {
          from: { height: 0 },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: 0 },
        },
        "fade-in": {
          '0%': { opacity: 0 },
          '100%': { opacity: 1 },
        },
        "slide-in": {
          '0%': { transform: 'translateY(5px)', opacity: 0 },
          '100%': { transform: 'translateY(0)', opacity: 1 },
        }
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "fade-in": "fade-in 0.3s ease-out",
        "slide-in": "slide-in 0.3s ease-out",
      },
      typography: (theme) => ({
        DEFAULT: {
          css: {
            '--tw-prose-body': theme('colors.gray.900'),
            '--tw-prose-headings': theme('colors.gray.900'),
            '--tw-prose-links': theme('colors.blue.600'),
            '--tw-prose-code': theme('colors.gray.900'),
            maxWidth: 'none',
            color: 'var(--tw-prose-body)',
            fontSize: '1rem',
            lineHeight: '1.75',
            p: {
              marginTop: '1em',
              marginBottom: '1em',
              fontSize: '1rem',
              '&:first-child': {
                marginTop: 0,
              },
              '&:last-child': {
                marginBottom: 0,
              },
            },
            'ul, ol': {
              paddingLeft: '1.5em',
              marginTop: '0.5em',
              marginBottom: '0.5em',
            },
            li: {
              marginTop: '0.25em',
              marginBottom: '0.25em',
              fontSize: '1rem',
              lineHeight: '1.5',
              p: {
                marginTop: '0.375em',
                marginBottom: '0.375em',
              },
            },
            'h1, h2, h3, h4': {
              color: 'var(--tw-prose-headings)',
              marginTop: '1.5em',
              marginBottom: '0.5em',
              fontSize: '1.25rem',
              fontWeight: '600',
              lineHeight: '1.3',
              '&:first-child': {
                marginTop: 0,
              },
            },
            pre: {
              margin: '0.5em 0',
              padding: '0.5em',
              backgroundColor: 'transparent',
              borderRadius: '0.375rem',
              fontSize: '0.875rem',
              lineHeight: '1.5',
              overflowX: 'auto',
            },
            code: {
              color: 'var(--tw-prose-code)',
              backgroundColor: theme('colors.gray.100'),
              padding: '0.2em 0.4em',
              borderRadius: '0.25rem',
              fontSize: '0.875rem',
              fontWeight: '400',
            },
            'pre code': {
              backgroundColor: 'transparent',
              padding: 0,
              fontSize: '0.875rem',
              color: 'inherit',
              fontWeight: '400',
            },
            blockquote: {
              borderLeftWidth: '4px',
              borderLeftColor: theme('colors.gray.200'),
              paddingLeft: '1em',
              fontStyle: 'italic',
              marginTop: '1em',
              marginBottom: '1em',
              fontSize: '1rem',
            },
            hr: {
              marginTop: '2em',
              marginBottom: '2em',
            },
            a: {
              color: 'var(--tw-prose-links)',
              textDecoration: 'underline',
              '&:hover': {
                color: theme('colors.blue.700'),
              },
            },
            table: {
              width: '100%',
              marginTop: '1em',
              marginBottom: '1em',
              borderCollapse: 'collapse',
              fontSize: '0.875rem',
              lineHeight: '1.5',
            },
            'th, td': {
              padding: '0.5em',
              borderWidth: '1px',
              borderColor: theme('colors.gray.200'),
            },
          },
        },
      }),
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
    require("tailwindcss-animate")
  ],
}
