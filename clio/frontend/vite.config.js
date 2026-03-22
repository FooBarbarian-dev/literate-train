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
      '/relation-service': {
        target: 'http://relation-service:3002',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/relation-service/, ''),
      },
    },
  },
})
