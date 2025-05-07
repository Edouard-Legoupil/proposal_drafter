import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// https://vite.dev/config/
export default defineConfig({
  server: {
    port: 8503,
    host: 'localhost',
    allowedHosts: [
      'ec2-65-2-181-226.ap-south-1.compute.amazonaws.com',
      'localhost'
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
