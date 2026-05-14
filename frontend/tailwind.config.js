/** @type {import('tailwindcss').Config} */
export default {
    darkMode: ["class"],
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
    	extend: {
    		colors: {
    			'fennec-light': {
    				'50': '#fafafa',
    				'100': '#f5f5f5',
    				'200': '#e5e5e5',
    				'300': '#d4d4d4',
    				'400': '#a3a3a3',
    				'500': '#737373',
    				'600': '#525252',
    				'700': '#404040',
    				'800': '#262626',
    				'900': '#171717',
    				'950': '#0a0a0a'
    			},
    			'fennec-lime': {
    				'50': '#f7fee7',
    				'100': '#ecfccb',
    				'200': '#d9f99d',
    				'300': '#bef264',
    				'400': '#a3e635',
    				'500': '#84cc16',
    				'600': '#65a30d',
    				'700': '#4d7c0f',
    				'800': '#3f6212',
    				'900': '#365314'
    			},
    			'fennec-red': {
    				'50': '#fef2f2',
    				'100': '#fee2e2',
    				'200': '#fecaca',
    				'300': '#fca5a5',
    				'400': '#f87171',
    				'500': '#ef4444',
    				'600': '#dc2626',
    				'700': '#b91c1c',
    				'800': '#991b1b',
    				'900': '#7f1d1d'
    			},
    			'fennec-orange': {
    				'50': '#fff7ed',
    				'100': '#ffedd5',
    				'200': '#fed7aa',
    				'300': '#fdba74',
    				'400': '#fb923c',
    				'500': '#f97316',
    				'600': '#ea580c',
    				'700': '#c2410c',
    				'800': '#9a3412',
    				'900': '#7c2d12'
    			},
    			'fennec-yellow': {
    				'50': '#fefce8',
    				'100': '#fef9c3',
    				'200': '#fef08a',
    				'300': '#fde047',
    				'400': '#facc15',
    				'500': '#eab308',
    				'600': '#ca8a04',
    				'700': '#a16207',
    				'800': '#854d0e',
    				'900': '#713f12'
    			},
    			'fennec-green': {
    				'50': '#f0fdf4',
    				'100': '#dcfce7',
    				'200': '#bbf7d0',
    				'300': '#86efac',
    				'400': '#4ade80',
    				'500': '#22c55e',
    				'600': '#16a34a',
    				'700': '#15803d',
    				'800': '#166534',
    				'900': '#14532d'
    			},
    			'fennec-blue': {
    				'50': '#eff6ff',
    				'100': '#dbeafe',
    				'200': '#bfdbfe',
    				'300': '#93c5fd',
    				'400': '#60a5fa',
    				'500': '#3b82f6',
    				'600': '#2563eb',
    				'700': '#1d4ed8',
    				'800': '#1e40af',
    				'900': '#1e3a8a'
    			},
    			'fennec-purple': {
    				'50': '#faf5ff',
    				'100': '#f3e8ff',
    				'200': '#e9d5ff',
    				'300': '#d8b4fe',
    				'400': '#a78bfa',
    				'500': '#8b5cf6',
    				'600': '#7c3aed',
    				'700': '#6d28d9',
    				'800': '#5b21b6',
    				'900': '#4c1d95'
    			},
    			background: 'hsl(var(--background))',
                foreground: 'hsl(var(--foreground))',
                card: {
                    DEFAULT: 'hsl(var(--card))',
                    foreground: 'hsl(var(--card-foreground))'
                },
                popover: {
                    DEFAULT: 'hsl(var(--popover))',
                    foreground: 'hsl(var(--popover-foreground))'
                },
                primary: {
                    DEFAULT: 'hsl(var(--primary))',
                    foreground: 'hsl(var(--primary-foreground))'
                },
                secondary: {
                    DEFAULT: 'hsl(var(--secondary))',
                    foreground: 'hsl(var(--secondary-foreground))'
                },
                muted: {
                    DEFAULT: 'hsl(var(--muted))',
                    foreground: 'hsl(var(--muted-foreground))'
                },
                accent: {
                    DEFAULT: 'hsl(var(--accent))',
                    foreground: 'hsl(var(--accent-foreground))'
                },
                destructive: {
                    DEFAULT: 'hsl(var(--destructive))',
                    foreground: 'hsl(var(--destructive-foreground))'
                },
                border: 'hsl(var(--border))',
                input: 'hsl(var(--input))',
                ring: 'hsl(var(--ring))',
                chart: {
                    '1': 'hsl(var(--chart-1))',
                    '2': 'hsl(var(--chart-2))',
                    '3': 'hsl(var(--chart-3))',
                    '4': 'hsl(var(--chart-4))',
                    '5': 'hsl(var(--chart-5))'
                },
    			sidebar: {
    				DEFAULT: 'hsl(var(--sidebar-background))',
    				foreground: 'hsl(var(--sidebar-foreground))',
    				primary: 'hsl(var(--sidebar-primary))',
    				'primary-foreground': 'hsl(var(--sidebar-primary-foreground))',
    				accent: 'hsl(var(--sidebar-accent))',
    				'accent-foreground': 'hsl(var(--sidebar-accent-foreground))',
    				border: 'hsl(var(--sidebar-border))',
    				ring: 'hsl(var(--sidebar-ring))'
    			}
    		},
    		fontFamily: {
    			sans: [
    				'Inter',
    				'system-ui',
    				'sans-serif'
    			],
    			mono: [
    				'JetBrains Mono',
    				'Consolas',
    				'monospace'
    			]
    		},
    		animation: {
    			'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
    			'spin-slow': 'spin 3s linear infinite',
    			'gradient-x': 'gradient-x 3s ease infinite',
    			'pulse-border': 'pulse-border 2s ease-in-out infinite',
    			'accordion-down': 'accordion-down 0.2s ease-out',
    			'accordion-up': 'accordion-up 0.2s ease-out'
    		},
    		keyframes: {
    			'gradient-x': {
    				'0%, 100%': { 'background-position': '0% 50%' },
    				'50%': { 'background-position': '100% 50%' }
    			},
    			'pulse-border': {
    				'0%, 100%': { 'border-color': 'rgba(139, 92, 246, 0.3)' },
    				'50%': { 'border-color': 'rgba(139, 92, 246, 0.7)' }
    			},
    			'accordion-down': {
    				from: { height: '0' },
    				to: { height: 'var(--radix-accordion-content-height)' }
    			},
    			'accordion-up': {
    				from: { height: 'var(--radix-accordion-content-height)' },
    				to: { height: '0' }
    			}
    		},
    		borderRadius: {
    			lg: 'var(--radius)',
    			md: 'calc(var(--radius) - 2px)',
    			sm: 'calc(var(--radius) - 4px)'
    		}
    	}
    },
    plugins: [require("tailwindcss-animate"), require('@tailwindcss/container-queries'),],
}