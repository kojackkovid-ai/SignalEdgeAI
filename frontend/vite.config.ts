import { defineConfig } from 'vite'
import path from 'path'
import react from '@vitejs/plugin-react'

const stripeKey = process.env.VITE_STRIPE_PUBLISHABLE_KEY || ''
const apiUrl = process.env.VITE_API_URL || '/api'
const appName = process.env.VITE_APP_NAME || 'SignalEdge AI'

if (!stripeKey) {
  console.warn('[Vite] VITE_STRIPE_PUBLISHABLE_KEY is not configured. Please set it in your environment.')
}

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5000,
    host: '0.0.0.0',
    strictPort: true,
    allowedHosts: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        ws: false,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.error('[proxy] error:', err.message)
          })
        }
      }
    }
  },
  define: {
    'import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY': JSON.stringify(stripeKey),
    'import.meta.env.VITE_API_URL': JSON.stringify(apiUrl),
    'import.meta.env.VITE_APP_NAME': JSON.stringify(appName),
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  }
})
