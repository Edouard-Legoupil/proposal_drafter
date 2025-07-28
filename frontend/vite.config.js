import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

export default defineConfig(({ mode }) => {
  const isProduction = mode === 'production'

  return {
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
    base: isProduction ? '/proposal_drafter/' : '/', // 👈 dynamic base
  }
})
