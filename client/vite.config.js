import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',  // More explicit than 'true'
    port: 5173,
    allowedHosts: [
      "ivypayments.ddns.net",
      "51.21.130.249",
      "localhost"
    ],
    strictPort: true,
    watch: { usePolling: true },
    proxy: {
      '/api': {
        target: 'http://51.21.130.249:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  },
  preview: {
    host: '0.0.0.0',
    port: 5173,
  },
})