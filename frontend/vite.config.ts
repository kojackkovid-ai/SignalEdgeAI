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

// Use process.env first (set by Replit secrets / CI), then .env file, then fallback
// Extract only the first valid Stripe key token in case the env var is accidentally doubled
const rawStripeKey = process.env.VITE_STRIPE_PUBLISHABLE_KEY || envVars.VITE_STRIPE_PUBLISHABLE_KEY || ''
const stripeKey = rawStripeKey.match(/pk_(test|live)_[A-Za-z0-9]+/)?.[0] || rawStripeKey
const apiUrl = process.env.VITE_API_URL || envVars.VITE_API_URL || '/api'
const appName = process.env.VITE_APP_NAME || envVars.VITE_APP_NAME || 'SignalEdge AI'

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
            console.error('[proxy] error:', err.message);
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
