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
  { a: '/perfil-profesor', texto: 'Mi ficha' },
]

/** Saca las iniciales para el circulito del avatar: "Martina Silva" -> "MS". */
function iniciales(usuario) {
  const n = (usuario?.nombre || '').trim()[0] || ''
  const a = (usuario?.apellido || '').trim()[0] || ''
  return (n + a).toUpperCase() || '?'
}

export default function Layout() {
  const { usuario, salir } = useAuth()
  const menu = usuario?.rol === 'profesor' ? MENU_PROFESOR : MENU_ESTUDIANTE

  return (
    <>
      <nav className="nav">
        <Link to={usuario?.rol === 'profesor' ? '/panel' : '/inicio'} className="nav-brand">
          Exonero
        </Link>

        {/* NavLink pone aria-current="page" solo en el enlace activo, y el CSS
            lo pinta con el color de acento. */}
        {menu.map((item) => (
          <NavLink key={item.a} to={item.a}>
            {item.texto}
          </NavLink>
        ))}

        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '14px' }}>
          {/* El contador de mensajes no leidos viene adentro de
              GET /usuarios/yo, asi que no hace falta otra llamada para pintarlo. */}
          {usuario?.mensajes_no_leidos > 0 && (
            <span className="tag tag-accent">{usuario.mensajes_no_leidos} sin leer</span>
          )}

          <button type="button" className="btn btn-ghost" onClick={salir}>
            Salir
          </button>

          <div className="avatar" title={`${usuario?.nombre} ${usuario?.apellido || ''}`}>
            {usuario?.foto_base64 ? (
              <img src={usuario.foto_base64} alt="" />
            ) : (
              iniciales(usuario)
            )}
          </div>
        </div>
      </nav>

      {/* Aca react-router dibuja la pantalla que corresponda. */}
      <main style={{ padding: '0 26px 40px' }}>
        <Outlet />
      </main>
    </>
  )
}
