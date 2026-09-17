import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// El dev server del frontend corre en 5173 y el backend en 8000.
// El proxy hace que desde React se pueda llamar a "/api/..." a secas: Vite lo
// reenvia a localhost:8000. Asi el codigo no tiene ninguna URL absoluta y el
// dia que se despliegue no hay que cambiar nada.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
