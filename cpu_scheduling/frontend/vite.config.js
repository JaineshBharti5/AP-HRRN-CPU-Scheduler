import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// The Flask API (api.py) runs on :5000; /api calls are proxied to it in dev.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:5000',
    },
  },
})
