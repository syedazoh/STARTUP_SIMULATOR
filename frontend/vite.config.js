import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [react()],
    server: {
      host: '0.0.0.0',
      port: 5173,
      strictPort: true,
      watch: { usePolling: env.VITE_USE_POLLING === 'true' },
      proxy: {
        // This address is used by Vite, not the browser. Compose resolves
        // backend via Docker DNS; local development uses localhost.
        '/api': {
          target: env.API_PROXY_TARGET || 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
  }
})
