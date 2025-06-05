import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// https://vite.dev/config/
export default defineConfig({
  server: {
    port: 8503,
    host: '0.0.0.0',
    allowedHosts: [
      'localhost',
      'https://proposal-drafter.azurewebsites.net/'
    ],
    proxy: {
      '/api': {
        target: 'http://localhost:8502',
        changeOrigin: true,
        secure: false
      }
    }
  },
  plugins: [react()],
})
