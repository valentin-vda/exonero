/**
 * La tarjeta de la proxima clase (1d), con GET /api/clases/proxima:
 *
 *   (18:00)  PROXIMA CLASE · EN 40 MIN
 *            Martina Silva · Matematica, Bachillerato          [Mensaje] [Ver reserva]
 *            Hoy 18:00 a 19:30 · Presencial · Biblioteca del Cordon · tema: funciones
 *            Liceo Bauza · 099 123 456
 *
 * La cuenta regresiva (minutos_restantes) la calcula el backend. Aca solo se
 * decide como decirla: "en 40 min" si es hoy, "manana" o la fecha si no.
 *
 * Si no hay ninguna clase confirmada por delante, el backend responde 204 sin
 * cuerpo y pedir() devuelve null: se muestra un estado vacio tranquilo.
 */

import { Link } from 'react-router-dom'

import Alerta from '../../componentes/Alerta.jsx'
import { hora, SEPARADOR } from '../../utiles/formato.js'
import { cuandoEs, cuantoFalta, finDe } from './fechas.js'
import { MODALIDAD_CLASE } from './opciones.js'

/**
 * Las partes del renglon de detalle, sin las que falten. Es una lista de
 * nodos y no un texto porque el enlace de una clase online va como <a>.
 */
function detalle(clase) {
  const partes = [
    `${cuandoEs(clase.inicio)} ${hora(clase.inicio)} a ${hora(finDe(clase.inicio, clase.duracion_min))}`,
    MODALIDAD_CLASE[clase.modalidad],
  ]
  if (clase.modalidad === 'online' && clase.ubicacion?.startsWith('http')) {
    partes.push(
      <a key="enlace" href={clase.ubicacion} target="_blank" rel="noreferrer">
        enlace de la clase
      </a>,
    )
  } else if (clase.ubicacion) {
    partes.push(clase.ubicacion)
  }
  if (clase.tema) partes.push(`tema: ${clase.tema}`)

  // Entre parte y parte va el separador " · ". flatMap arma [a, ' · ', b, ...].
  return partes.flatMap((parte, i) => (i === 0 ? [parte] : [SEPARADOR, parte]))
}

export default function ProximaClase({ bloque }) {
  const { datos: clase, error, cargando } = bloque

  if (cargando) {
    return (
      <section className="tablero-proxima" aria-busy="true">
        <p className="tablero-vacio">Cargando tu proxima clase...</p>
      </section>
    )
  }

  if (error) {
    return (
      <section className="tablero-proxima">
        <Alerta tipo="error">No pudimos traer tu proxima clase. {error}</Alerta>
      </section>
    )
  }

  if (!clase) {
    return (
      <section className="tablero-proxima" aria-labelledby="proxima-titulo">
        <div className="tablero-proxima-datos">
          <h3 id="proxima-titulo" className="tablero-proxima-titulo">Proxima clase</h3>
          <div className="tablero-proxima-quien">No tenes clases confirmadas por delante</div>
          <div className="tablero-proxima-detalle">
            Cuando apruebes una solicitud en la agenda, la vas a ver aca.
          </div>
        </div>
        <div className="tablero-botones">
          <Link to="/agenda" className="btn btn-secondary">
            Ir a la agenda
          </Link>
        </div>
      </section>
    )
  }

  const alumno = clase.contraparte
  const nombre = [alumno.nombre, alumno.apellido].filter(Boolean).join(' ')
  // La etapa de la clase y, si no vino, la del alumno.
  const queDa = [clase.materia, clase.etapa || alumno.etapa].filter(Boolean).join(', ')

  return (
    <section className="tablero-proxima" aria-labelledby="proxima-titulo">
      {/* aria-hidden: la hora ya esta en el renglon de detalle; el lector de
          pantalla no tiene por que leerla dos veces. */}
      <div className="tablero-proxima-hora" aria-hidden="true">
        {hora(clase.inicio)}
      </div>

      <div className="tablero-proxima-datos">
        <h3 id="proxima-titulo" className="tablero-proxima-titulo">
          Proxima clase{SEPARADOR}
          {cuantoFalta(clase.minutos_restantes, clase.inicio)}
        </h3>
        <div className="tablero-proxima-quien">
          {nombre}
          {queDa && `${SEPARADOR}${queDa}`}
        </div>
        <div className="tablero-proxima-detalle">{detalle(clase)}</div>
        {(alumno.centro || alumno.telefono) && (
          <div className="tablero-proxima-detalle">
            {alumno.centro}
            {alumno.centro && alumno.telefono && SEPARADOR}
            {alumno.telefono && <a href={`tel:${alumno.telefono.replace(/\s/g, '')}`}>{alumno.telefono}</a>}
          </div>
        )}
      </div>

      <div className="tablero-botones">
        <Link to="/mensajes" className="btn btn-secondary">
          Mensaje
        </Link>
        <Link to="/agenda" className="btn btn-primary">
          Ver reserva
        </Link>
      </div>
    </section>
  )
}
