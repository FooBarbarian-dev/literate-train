import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://backend:3001',
        changeOrigin: true,
      },
      '/admin': {
        target: 'http://backend:3001',
        changeOrigin: true,
      },
      '/static': {
        target: 'http://backend:3001',
        changeOrigin: true,
      },
    },
  },
})
