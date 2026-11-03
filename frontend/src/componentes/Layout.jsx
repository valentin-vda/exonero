/**
 * El marco de las pantallas de adentro: la barra de navegacion arriba y el
 * contenido abajo.
 *
 * La barra es la del mockup 1a: marca a la izquierda, los cinco enlaces, y a
 * la derecha el switch de rol y el avatar.
 *
 * Se usa como ruta padre en App.jsx: todo lo que cuelgue de el sale con barra.
 */

import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'

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
  const [menuAbierto, setMenuAbierto] = useState(false)
  const navegacion = useRef(null)
  const ubicacion = useLocation()
  // Los mensajes sin leer: arranca con el de GET /usuarios/yo y se actualiza
  // cada diez segundos (ver useNoLeidos.js, de P3).
  const sinLeer = useNoLeidos()

  useEffect(() => {
    setMenuAbierto(false)
  }, [ubicacion.pathname])

  useEffect(() => {
    if (!menuAbierto) return undefined

    function cerrarConEscape(evento) {
      if (evento.key === 'Escape') setMenuAbierto(false)
    }

    function cerrarAlTocarAfuera(evento) {
      if (!navegacion.current?.contains(evento.target)) setMenuAbierto(false)
    }

    document.addEventListener('keydown', cerrarConEscape)
    document.addEventListener('pointerdown', cerrarAlTocarAfuera)

    return () => {
      document.removeEventListener('keydown', cerrarConEscape)
      document.removeEventListener('pointerdown', cerrarAlTocarAfuera)
    }
  }, [menuAbierto])

  return (
    <>
      <nav className="nav" ref={navegacion}>
        <Link
          to={usuario?.rol === 'profesor' ? '/panel' : '/inicio'}
          className="nav-brand"
          aria-label="Exonero — Inicio"
        >
          <img className="nav-logo" src={logoExonero} alt="" />
          <span>Exonero</span>
        </Link>

        {/* Con el menu cerrado, los no leidos se ven sobre el boton (el CSS
            dibuja data-sin-leer) y se dicen en el aria-label. */}
        <button
          type="button"
          className="nav-hamburguesa"
          aria-label={menuAbierto ? 'Cerrar menú' : `Abrir menú${sinLeer > 0 ? `, ${sinLeer} ${sinLeer === 1 ? 'mensaje' : 'mensajes'} sin leer` : ''}`}
          aria-expanded={menuAbierto}
          aria-controls="menu-principal"
          data-sin-leer={!menuAbierto && sinLeer > 0 ? sinLeer : undefined}
          onClick={() => setMenuAbierto((abierto) => !abierto)}
        >
          <span />
          <span />
          <span />
        </button>

        <div
          id="menu-principal"
          className={`nav-menu${menuAbierto ? ' esta-abierto' : ''}`}
        >
          <div className="nav-enlaces">
            {/* NavLink pone aria-current="page" solo en el enlace activo, y el CSS
                lo pinta con el color de acento. */}
            {menu.map((item) => (
              <NavLink key={item.a} to={item.a}>
                {item.texto}
                {item.a === '/mensajes' && sinLeer > 0 && (
                  <span className="nav-sin-leer" aria-label={`, ${sinLeer} sin leer`}>
                    {sinLeer}
                  </span>
                )}
              </NavLink>
            ))}
          </div>

          <div className="nav-actions">
            <button type="button" className="btn btn-ghost nav-salir" onClick={salir}>
              Salir
            </button>

            {/* La foto o las iniciales (ver Avatar.jsx). Al cambiar la foto en el
                perfil, se actualiza sola: el usuario viene del contexto. */}
            <Avatar persona={usuario} />
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
