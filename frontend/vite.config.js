import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const target = env.API_PROXY_TARGET || 'http://127.0.0.1:8000'
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
          target,
          configure(proxy) {
            proxy.on('error', (_error, _request, response) => {
              if (response && 'writeHead' in response && !response.headersSent && !response.writableEnded) {
                response.writeHead(503, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' })
                response.end(JSON.stringify({ detail: 'Cannot reach FastAPI. Start the backend on port 8000, check /health, and verify API_PROXY_TARGET. Vite on 5173 and Next.js on 3000 are separate frontends.' }))
              }
            })
          },
          changeOrigin: true,
        },
      },
    },
  }
})
