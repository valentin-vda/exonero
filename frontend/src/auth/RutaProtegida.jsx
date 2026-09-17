/**
 * Envoltorio para las rutas que exigen estar conectado.
 *
 * Se usa asi en App.jsx:
 *
 *   <Route element={<RutaProtegida />}>
 *     <Route path="/inicio" element={<Inicio />} />
 *   </Route>
 *
 * Todo lo que este adentro solo se muestra si hay sesion. Si no la hay, manda
 * al login y se acuerda a donde queria ir, para volver ahi despues de entrar.
 */

import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from './ContextoAuth.jsx'

export default function RutaProtegida({ rol = null }) {
  const { usuario, cargando } = useAuth()
  const ubicacion = useLocation()

  // Todavia no sabemos si hay sesion (se esta llamando a /usuarios/yo).
  // Sin este paso, se veria un parpadeo del login antes de entrar.
  if (cargando) {
    return (
      <div style={{ display: 'grid', placeItems: 'center', minHeight: '100vh' }}>
        <p className="text-muted">Cargando...</p>
      </div>
    )
  }

  if (!usuario) {
    // replace evita que el login quede en el historial: si el usuario aprieta
    // "atras" despues de entrar, no vuelve al formulario.
    return <Navigate to="/login" replace state={{ desde: ubicacion.pathname }} />
  }

  // Algunas pantallas son de un rol solo (el panel del profesor, el checkout
  // del alumno). Si el rol no coincide, se lo manda a su propio inicio.
  if (rol && usuario.rol !== rol) {
    return <Navigate to={usuario.rol === 'profesor' ? '/panel' : '/inicio'} replace />
  }

  // <Outlet /> es donde react-router dibuja la ruta hija que coincidio.
  return <Outlet />
}
