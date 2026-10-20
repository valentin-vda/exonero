/**
 * El mapa de rutas de toda la aplicacion.
 *
 * Como leerlo: cada <Route path="..." element={...} /> dice "cuando la URL sea
 * esto, mostra este componente". Las rutas anidadas heredan del padre: las que
 * estan adentro de <RutaProtegida> exigen sesion, y las que estan adentro de
 * <Layout> salen con la barra de navegacion.
 *
 * Los codigos (1a, 1b, ...) son los de los mockups, para poder ir y venir entre
 * el diseno y el codigo sin perderse.
 */

import { Navigate, Route, Routes } from 'react-router-dom'

import RutaProtegida from './auth/RutaProtegida.jsx'
import EnConstruccion from './componentes/EnConstruccion.jsx'
import Layout from './componentes/Layout.jsx'
import BuscarProfesores from './paginas/BuscarProfesores.jsx'
import Checkout from './paginas/Checkout.jsx'
import InicioEstudiante from './paginas/InicioEstudiante.jsx'
import Login from './paginas/Login.jsx'
import PanelProfesor from './paginas/PanelProfesor.jsx'
import PerfilEstudiante from './paginas/PerfilEstudiante.jsx'
import PerfilPublicoProfesor from './paginas/PerfilPublicoProfesor.jsx'
import PerfilProfesor from './paginas/PerfilProfesor.jsx'
import RecuperarClave from './paginas/RecuperarClave.jsx'
import Registro from './paginas/Registro.jsx'

export default function App() {
  return (
    <Routes>
      {/* ---------------------------------------------------------------
          Publicas. Son las unicas tres pantallas sin sesion.
          --------------------------------------------------------------- */}
      <Route path="/login" element={<Login />} />
      <Route path="/registro" element={<Registro />} />
      <Route path="/recuperar" element={<RecuperarClave />} />

      {/* ---------------------------------------------------------------
          Privadas del estudiante. Piden sesion Y rol estudiante.
          --------------------------------------------------------------- */}
      <Route element={<RutaProtegida rol="estudiante" />}>
        <Route element={<Layout />}>
          <Route path="/inicio" element={<InicioEstudiante />} />
          <Route path="/buscar" element={<BuscarProfesores />} />
          <Route path="/profesor/:id" element={<PerfilPublicoProfesor />} />
          {/* 1g - P4. Se llega desde 1f con los datos en la URL (ver Checkout.jsx). */}
          <Route path="/checkout" element={<Checkout />} />
          <Route
            path="/mis-clases"
            element={
              <EnConstruccion
                codigo="1b"
                nombre="Mis clases"
                dueno="P3"
                descripcion="Próxima clase, semana, reseñas pendientes con el botón Calificar y mis profesores."
              />
            }
          />
          {/* 1e - P1 */}
          <Route path="/mi-perfil" element={<PerfilEstudiante />} />
        </Route>
      </Route>

      {/* ---------------------------------------------------------------
          Privadas del profesor.
          --------------------------------------------------------------- */}
      <Route element={<RutaProtegida rol="profesor" />}>
        <Route element={<Layout />}>
          {/* 1d - P4 */}
          <Route path="/panel" element={<PanelProfesor />} />
          <Route
            path="/agenda"
            element={
              <EnConstruccion
                codigo="1i"
                nombre="Agenda del profesor"
                dueno="P3"
                descripcion="Solicitudes por aprobar, calendario, franjas y bloqueos."
              />
            }
          />
          {/* 1j - P1 */}
          <Route path="/perfil-profesor" element={<PerfilProfesor />} />
        </Route>
      </Route>

      {/* ---------------------------------------------------------------
          Compartida por los dos roles.
          --------------------------------------------------------------- */}
      <Route element={<RutaProtegida />}>
        <Route element={<Layout />}>
          {/* P3. Se abre desde Calificar en 1b o 1i; no es una pestaña del menu. */}
          <Route
            path="/resenas/redactar/:destinatarioId"
            element={
              <EnConstruccion
                codigo="1b / 1i"
                nombre="Redactar reseña"
                dueno="P3"
                descripcion="Formulario para calificar con 1 a 5 estrellas y escribir un comentario opcional. También permite editar la reseña propia."
              />
            }
          />
          <Route
            path="/mensajes"
            element={
              <EnConstruccion
                codigo="1h"
                nombre="Mensajes"
                dueno="P3"
                descripcion="Bandeja de hilos y conversacion."
              />
            }
          />
        </Route>
      </Route>

      {/* La raiz manda al login; si ya hay sesion, RutaProtegida se encarga de
          redirigir al tablero que corresponda. */}
      <Route path="/" element={<Navigate to="/login" replace />} />

      {/* Cualquier URL que no exista tambien va a la raiz. */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
