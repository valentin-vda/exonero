/**
 * La tabla de "Reservas de hoy" (1d), con GET /api/clases?desde=hoy&hasta=hoy:
 *
 *   Reservas de hoy                       5 clases · 6 h 30 min · jueves 3 de septiembre
 *   Hora   Alumno           Materia y etapa           Modalidad   Estado
 *   15:00  Joaquin Antunez  Matematica · Ciclo basico Online      [Dictada]       Ver
 *   18:00  Martina Silva    Matematica · Bachillerato Presencial  [En 40 min]   [Ver]
 *   21:00  Agustina Nunez   Fisica · Examen de ingreso Online     [A confirmar] [Confirmar]
 *
 * "Hoy" es el de Montevideo (fechas.js), no el de la computadora.
 *
 * La clase que es la proxima (la misma de la tarjeta de arriba) se resalta y
 * en vez del estado dice cuanto falta. Para eso recibe la proxima clase como
 * prop: no hace otra llamada.
 *
 * Los botones llevan a la agenda (1i): aprobar y rechazar una solicitud son de
 * alla, no de aca.
 *
 * En el celular la tabla se convierte en tarjetas (ver panel.css): las
 * columnas no entran en 375 px y la pagina nunca tiene que scrollear de costado.
 */

import { Link } from 'react-router-dom'

import Alerta from '../../componentes/Alerta.jsx'
import { hora, unir } from '../../utiles/formato.js'
import { cuantoFalta, diaLargo, duracion, hoy } from './fechas.js'
import { ESTADOS_CLASE, MODALIDAD_CLASE } from './opciones.js'

/** "5 clases · 6 h 30 min · jueves 3 de septiembre". Las canceladas no cuentan. */
function resumen(clases) {
  const activas = clases.filter((c) => c.estado !== 'cancelada')
  const minutos = activas.reduce((suma, c) => suma + c.duracion_min, 0)
  return unir([
    activas.length === 1 ? '1 clase' : `${activas.length} clases`,
    minutos > 0 && duracion(minutos),
    diaLargo(hoy()),
  ])
}

/** La etiqueta de la columna Estado y el boton de la fila. */
function estadoYAccion(clase, esLaProxima) {
  const estado = ESTADOS_CLASE[clase.estado] || { texto: clase.estado, clase: 'tag-neutral' }
  if (esLaProxima) {
    const falta = cuantoFalta(clase.minutos_restantes, clase.inicio)
    return { texto: falta[0].toUpperCase() + falta.slice(1), clase: 'tag-accent', accion: 'Ver', boton: 'btn-primary' }
  }
  if (clase.estado === 'pendiente') return { ...estado, accion: 'Confirmar', boton: 'btn-secondary' }
  if (clase.estado === 'aprobada') return { ...estado, accion: 'Ver', boton: 'btn-secondary' }
  // Las que ya pasaron (dictada, cancelada, no asistio): un boton mas discreto.
  return { ...estado, accion: 'Ver', boton: 'btn-ghost' }
}

export default function ReservasDeHoy({ bloque, proxima }) {
  const { datos, error, cargando } = bloque
  // Ordenadas por hora. Se ordena una COPIA: sort() modifica la lista, y la
  // del estado no se toca nunca.
  const clases = datos ? [...datos].sort((a, b) => a.inicio.localeCompare(b.inicio)) : []

  return (
    <section className="tablero-bloque" aria-labelledby="hoy-titulo">
      <div className="tablero-encabezado">
        <h3 id="hoy-titulo">Reservas de hoy</h3>
        {datos && <span className="tablero-resumen">{resumen(clases)}</span>}
      </div>

      {cargando && <p className="tablero-vacio">Cargando las clases de hoy...</p>}
      {error && <Alerta tipo="error">No pudimos traer las clases de hoy. {error}</Alerta>}
      {datos && clases.length === 0 && (
        <p className="tablero-vacio">No tenes clases para hoy. Las solicitudes nuevas te llegan a la agenda.</p>
      )}

      {clases.length > 0 && (
        <table className="tablero-tabla" aria-labelledby="hoy-titulo">
          <thead>
            <tr>
              <th scope="col">Hora</th>
              <th scope="col">Alumno</th>
              <th scope="col">Materia y etapa</th>
              <th scope="col">Modalidad</th>
              <th scope="col">Estado</th>
              <th scope="col">
                <span className="oculto-visual">Accion</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {clases.map((clase) => {
              const alumno = clase.contraparte
              const nombre = [alumno.nombre, alumno.apellido].filter(Boolean).join(' ')
              const esLaProxima = proxima?.id === clase.id && proxima.minutos_restantes > 0
              const fila = estadoYAccion(esLaProxima ? proxima : clase, esLaProxima)

              return (
                <tr key={clase.id} className={esLaProxima ? 'tablero-fila-proxima' : undefined}>
                  <td className="tablero-celda-hora">{hora(clase.inicio)}</td>
                  <td className="tablero-celda-alumno">{nombre}</td>
                  <td className="tablero-celda-materia">{unir([clase.materia, clase.etapa || alumno.etapa])}</td>
                  <td className="tablero-celda-modalidad">{MODALIDAD_CLASE[clase.modalidad]}</td>
                  <td className="tablero-celda-estado">
                    <span className={`tag ${fila.clase}`}>{fila.texto}</span>
                  </td>
                  <td className="tablero-celda-accion">
                    {/* Todos los botones dicen "Ver": el aria-label dice de
                        cual clase, para quien recorre la tabla con lector. */}
                    <Link
                      to="/agenda"
                      className={`btn ${fila.boton}`}
                      aria-label={`${fila.accion} la clase de las ${hora(clase.inicio)} con ${nombre}`}
                    >
                      {fila.accion}
                    </Link>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </section>
  )
}
