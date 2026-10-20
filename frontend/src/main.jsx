/**
 * Punto de entrada del frontend.
 *
 * Es lo primero que corre. Monta React en el <div id="root"> de index.html y
 * envuelve la app en dos cosas:
 *
 *   BrowserRouter  hace que funcionen las URLs (/login, /inicio, ...)
 *   ProveedorAuth  pone "quien esta conectado" al alcance de toda la app
 *
 * Los CSS se importan aca, una sola vez, y en este orden:
 *   1. tokens       define las variables (y las del modo oscuro)
 *   2. componentes  las usa para los botones, inputs, tarjetas
 *   3. auth         los estilos propios de login y registro
 *   4. perfil       los de las pantallas de perfil (1e y 1j)
 *   5. panel        los del panel del profesor (1d) y sus graficos
 *   6. pagos        los del checkout (1g) y de "Medios de pago" (1e)
 *   7. busqueda     los de buscar profesores (1c)
 *   8. inicio        los de la pantalla inicial del estudiante (1a)
 */

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import 'leaflet/dist/leaflet.css'

import App from './App.jsx'
import { ProveedorAuth } from './auth/ContextoAuth.jsx'

import './estilos/tokens.css'
import './estilos/componentes.css'
import './estilos/auth.css'
import './estilos/perfil.css'
import './estilos/panel.css'
import './estilos/pagos.css'
import './estilos/busqueda.css'
import './estilos/perfil-publico.css'
import './estilos/inicio.css'

createRoot(document.getElementById('root')).render(
  // StrictMode solo corre en desarrollo. Hace que los efectos se ejecuten dos
  // veces a proposito, para sacar a la luz codigo que no soporta repetirse.
  // Si ves una llamada duplicada en la pestania de red, es esto, no un error.
  <StrictMode>
    <BrowserRouter>
      <ProveedorAuth>
        <App />
      </ProveedorAuth>
    </BrowserRouter>
  </StrictMode>,
)
