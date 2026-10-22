/**
 * El marco de las pantallas de adentro: la barra de navegacion arriba y el
 * contenido abajo.
 *
 * La barra es la del mockup 1a: marca a la izquierda, los cinco enlaces, y a
 * la derecha el switch de rol y el avatar.
 *
 * Se usa como ruta padre en App.jsx: todo lo que cuelgue de el sale con barra.
 */

import { Link, NavLink, Outlet } from 'react-router-dom'

import { useAuth } from '../auth/ContextoAuth.jsx'
import logoExonero from '../assets/logo-exonero.png'
import Avatar from './Avatar.jsx'
import useNoLeidos from './useNoLeidos.js'

// Los enlaces de cada rol. Cada uno ve su propio menu.
const MENU_ESTUDIANTE = [
  { a: '/inicio', texto: 'Inicio' },
  { a: '/buscar', texto: 'Buscar profes' },
  { a: '/mis-clases', texto: 'Mis clases' },
  { a: '/mensajes', texto: 'Mensajes' },
  { a: '/mi-perfil', texto: 'Mi perfil' },
]

const MENU_PROFESOR = [
  { a: '/panel', texto: 'Panel' },
  { a: '/agenda', texto: 'Agenda' },
  { a: '/mensajes', texto: 'Mensajes' },
  { a: '/perfil-profesor', texto: 'Mi perfil' },
]

export default function Layout() {
  const { usuario, salir } = useAuth()
  const menu = usuario?.rol === 'profesor' ? MENU_PROFESOR : MENU_ESTUDIANTE
  // Los mensajes sin leer: arranca con el de GET /usuarios/yo y se actualiza
  // cada diez segundos (ver useNoLeidos.js, de P3).
  const sinLeer = useNoLeidos()

  return (
    <>
      <nav className="nav">
        <Link to={usuario?.rol === 'profesor' ? '/panel' : '/inicio'} className="nav-brand">
          <img className="nav-logo" src={logoExonero} alt="" />
          <span>Exonero</span>
        </Link>

        {/* NavLink pone aria-current="page" solo en el enlace activo, y el CSS
            lo pinta con el color de acento. */}
        {menu.map((item) => (
          <NavLink key={item.a} to={item.a}>
            {item.texto}
            {item.a === '/mensajes' && sinLeer > 0 && (
              <span className="nav-sin-leer" aria-label={`, ${sinLeer} sin leer`}>{sinLeer}</span>
            )}
          </NavLink>
        ))}

        <div className="nav-actions">
          <button type="button" className="btn btn-ghost nav-salir" onClick={salir}>
            Salir
          </button>

          {/* La foto o las iniciales (ver Avatar.jsx). Al cambiar la foto en el
              perfil, se actualiza sola: el usuario viene del contexto. */}
          <Avatar persona={usuario} />
        </div>
      </nav>

      {/* Aca react-router dibuja la pantalla que corresponda. */}
      <main style={{ padding: '0 26px 40px' }}>
        <Outlet />
      </main>
    </>
  )
}
