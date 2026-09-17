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
import Login from './paginas/Login.jsx'
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
          <Route
            path="/inicio"
            element={
              <EnConstruccion
                codigo="1a"
                nombre="Inicio del estudiante"
                dueno="P2"
                descripcion="Saludo, proxima clase, mapa de cercanos, carrusel y ranking."
              />
            }
          />
          <Route
            path="/buscar"
            element={
              <EnConstruccion
                codigo="1c"
                nombre="Buscar profes"
                dueno="P2"
                descripcion="Los nueve filtros, la lista de resultados y el mapa."
              />
            }
          />
          <Route
            path="/profesor/:id"
            element={
              <EnConstruccion
                codigo="1f"
                nombre="Detalle del profesor"
                dueno="P2"
                descripcion="Ficha completa, calendario de disponibilidad y resenas."
              />
            }
          />
          <Route
            path="/checkout"
            element={
              <EnConstruccion
                codigo="1g"
                nombre="Checkout"
                dueno="P4"
                descripcion="Resumen de la clase, desglose del importe y tarjeta."
              />
            }
          />
          <Route
            path="/mis-clases"
            element={
              <EnConstruccion
                codigo="1b"
                nombre="Mis clases"
                dueno="P3"
                descripcion="Proxima clase, semana, resenas pendientes y mis profesores."
              />
            }
          />
          <Route
            path="/mi-perfil"
            element={
              <EnConstruccion
                codigo="1e"
                nombre="Perfil del estudiante"
                dueno="P1"
                descripcion="Datos personales, educativos, tarjetas e historial de pagos."
              />
            }
          />
        </Route>
      </Route>

      {/* ---------------------------------------------------------------
          Privadas del profesor.
          --------------------------------------------------------------- */}
      <Route element={<RutaProtegida rol="profesor" />}>
        <Route element={<Layout />}>
          <Route
            path="/panel"
            element={
              <EnConstruccion
                codigo="1d"
                nombre="Panel del profesor"
                dueno="P4"
                descripcion="Proxima clase, cinco indicadores, clases del dia y graficos."
              />
            }
          />
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
          <Route
            path="/perfil-profesor"
            element={
              <EnConstruccion
                codigo="1j"
                nombre="Perfil del profesor"
                dueno="P1"
                descripcion="Oferta, modalidad, precios, reglas, biografia y fotos."
              />
            }
          />
        </Route>
      </Route>

      {/* ---------------------------------------------------------------
          Compartida por los dos roles.
          --------------------------------------------------------------- */}
      <Route element={<RutaProtegida />}>
        <Route element={<Layout />}>
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
