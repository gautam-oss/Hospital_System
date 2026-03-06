import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  // Path alias — lets you write import { Button } from '@/components/ui/Button'
  // instead of ../../components/ui/Button
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },

  server: {
    host: '0.0.0.0',   // required inside Docker
    port: 5173,
    // Proxy API calls in dev — avoids CORS issues when not using Nginx
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
    },
  },
})
