import { defineConfig } from 'vite'
import fs from 'fs'
import path from 'path'
import react from '@vitejs/plugin-react'

// Read .env file directly and parse variables
function readEnvFile(): Record<string, string> {
  const envPath = path.resolve(process.cwd(), '.env')
  const env: Record<string, string> = {}
  
  try {
    if (fs.existsSync(envPath)) {
      console.log('[Vite] Reading .env from:', envPath)
      const content = fs.readFileSync(envPath, 'utf-8')
      console.log('[Vite] .env content length:', content.length, 'bytes')
      
      content.split('\n').forEach((line, lineNum) => {
        const match = line.match(/^([^=]+)=(.*)$/)
        if (match) {
          const key = match[1].trim()
          const value = match[2].trim()
          if (key && value) {
            env[key] = value
            console.log(`[Vite] Line ${lineNum}: ${key} = ${value.substring(0, 50)}${value.length > 50 ? '...' : ''}`)
          }
        }
      })
      
      console.log('[Vite] Parsed env variables:', Object.keys(env))
    } else {
      console.warn('[Vite] .env file not found at:', envPath)
    }
  } catch (err) {
    console.error('[Vite] Error reading .env:', err)
  }
  
  return env
}

const envVars = readEnvFile()

// Use actual values or hardcoded fallbacks
const stripeKey = envVars.VITE_STRIPE_PUBLISHABLE_KEY || 'pk_test_51SuaLd8f0rj8wiWDNdeOgNvgt3mFoKpmkXlzV2JWN8gUxash7DzogdtiZUu0rkCEMI5F3HtmTBquAhVVSKrknAy4003kbnRUu6'
const apiUrl = envVars.VITE_API_URL || '/api'
const appName = envVars.VITE_APP_NAME || 'SignalEdge AI'

console.log('[Vite Config] ========================================')
console.log('[Vite Config] Stripe Key Length:', stripeKey.length, '(should be 100+)')
console.log('[Vite Config] Stripe Key Preview:', stripeKey.substring(0, 30) + '...')
console.log('[Vite Config] API URL:', apiUrl)
console.log('[Vite Config] App Name:', appName)
console.log('[Vite Config] ========================================')

if (stripeKey.length < 20) {
  console.error('[Vite Config] ❌ WARNING: Stripe key appears invalid!')
  console.error('[Vite Config] Using HARDCODED fallback key')
}

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3001,
    host: '0.0.0.0',
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        ws: false,
        configure: (proxy, options) => {
          proxy.on('error', (err, req, res) => {
            console.log('proxy error', err);
          });
          proxy.on('proxyReq', (proxyReq, req, res) => {
            console.log('Sending Request to the Target:', req.method, req.url);
          });
          proxy.on('proxyRes', (proxyRes, req, res) => {
            console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
          });
        }
      }
    }
  },
  define: {
    // Define these so they're available in import.meta.env
    'import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY': JSON.stringify(stripeKey),
    'import.meta.env.VITE_API_URL': JSON.stringify(apiUrl),
    'import.meta.env.VITE_APP_NAME': JSON.stringify(appName),
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  }
})
