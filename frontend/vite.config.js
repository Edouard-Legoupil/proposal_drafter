import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// export default defineConfig({ 

// 👈 Set up depployment mode if pushed on github page
export default defineConfig(({ mode }) => {
  const isProduction = mode === 'production'
// 👈 dynamic base if the front end is on github page
// const base = isProduction ? '/proposal_drafter/' : '/'
  const base = isProduction ? '/' : '/'
  return {

  server: {
      
      port: 8503,
      host: '0.0.0.0',
      allowedHosts: [
        'localhost',
        '127.0.0.1',
        'proposalgen-290826171799.europe-west9.run.app/'
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
    base: base,

    // ✅ Force Vite to output to /app/dist
    build: {
      outDir: 'dist'
    }


  }

})
