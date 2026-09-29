import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    watch: {
      ignored: ['**/models/**'],
    },
    proxy: {
      '/crypto': 'http://127.0.0.1:5000',
      '/crypto-static': 'http://127.0.0.1:5000',
      '/steganography': 'http://127.0.0.1:5000',
      '/combined': 'http://127.0.0.1:5000',
      '/detection': 'http://127.0.0.1:5000',
      '/api': 'http://127.0.0.1:5000',
    },
  },
})
