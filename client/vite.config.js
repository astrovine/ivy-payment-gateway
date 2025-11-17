import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    strictPort: true,
    watch: { usePolling: true },
    headers: {
      'Access-Control-Allow-Origin': '*'
    }
  },
  preview: {
    host: true,
    port: 5173,
  },
})
