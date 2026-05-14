import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiTarget = env.VITE_API_BASE_URL || 'https://fennec-api-429281326783.us-west1.run.app/'

  return {
    plugins: [react()],
    define: {
      'process.env': {}, // prevents `process` access errors for env reads
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
        process: 'process/browser',
      },
    },
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    },
  }
})
