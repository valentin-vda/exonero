import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// El dev server del frontend corre en 5173 y el backend en 8000.
// El proxy hace que desde React se pueda llamar a "/api/..." a secas: Vite lo
// reenvia a localhost:8000. Asi el codigo no tiene ninguna URL absoluta y el
// dia que se despliegue no hay que cambiar nada.
//
// EXONERO_API cambia a donde apunta el proxy, para levantar un segundo backend
// en otro puerto sin tocar este archivo:
//   EXONERO_API=http://localhost:8001 npm run dev -- --port 5174
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.EXONERO_API || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
