/**
 * "Solicitudes por aprobar" (1i), con GET /api/clases/pendientes:
 *
 *   Solicitudes por aprobar (3)
 *   +--------------------------------------------------------------+
 *   | (JD) Juan Diaz                Martes 27 de octubre · 15:00   |
 *   |      Ciclo basico · Liceo 14  1 h · $ 1.200                  |
 *   |      ★ 4,6 (8)                                               |
 *   |      Fisica · Cinematica          [Rechazar] [Aprobar]       |
 *   +--------------------------------------------------------------+
 *
 * Sin expiracion: quedan hasta que el profesor responda. El importe ya vino
 * calculado (quedo congelado al crearse la clase), no se vuelve a cotizar.
 *
 * Rechazar borra la clase: por eso pide una segunda confirmacion en el mismo
 * renglon (sin window.confirm, que bloquea la pagina).
 *
 * Despues de aprobar o rechazar llama a `alCambiar`, y la pantalla recarga
 * esta lista y el calendario.
 */

import { useState } from 'react'

import { aprobarClase, rechazarClase } from '../../api/clases.js'
import { mensajeDeError } from '../../api/mensajes.js'
import Alerta from '../../componentes/Alerta.jsx'
import Avatar from '../../componentes/Avatar.jsx'
import { ESTRELLA, hora, pesos, puntaje, unir } from '../../utiles/formato.js'
import { cuandoEs, duracion } from '../panel/fechas.js'

function Solicitud({ solicitud, alCambiar }) {
  const [ocupado, setOcupado] = useState(false)
  const [confirmandoRechazo, setConfirmandoRechazo] = useState(false)
  const [error, setError] = useState(null)
  const alumno = solicitud.alumno
  const nombre = [alumno.nombre, alumno.apellido].filter(Boolean).join(' ')

  async function hacer(accion) {
    setError(null)
    setOcupado(true)
    try {
      await accion(solicitud.id)
      alCambiar()
    } catch (err) {
      setError(mensajeDeError(err.codigo))
      setOcupado(false)
    }
  }

  return (
    <li className="solicitud">
      <Avatar persona={alumno} tamanio="mediano" />
      <div className="solicitud-quien">
        <strong>{nombre}</strong>
        <span className="texto-chico">{unir([alumno.etapa, alumno.centro])}</span>
        {alumno.cantidad_resenas > 0 && (
          <span className="texto-chico">
            {ESTRELLA} {puntaje(alumno.puntaje_promedio)} ({alumno.cantidad_resenas})
          </span>
        )}
      </div>
      <div className="solicitud-clase">
        <strong>{cuandoEs(solicitud.inicio)} · {hora(solicitud.inicio)}</strong>
        <span className="texto-chico">{unir([duracion(solicitud.duracion_min), pesos(solicitud.total)])}</span>
        <span className="texto-chico">{unir([solicitud.materia, solicitud.tema])}</span>
      </div>
      <div className="solicitud-acciones">
        {confirmandoRechazo ? (
          <>
            <span className="texto-chico">Se borra la solicitud.</span>
            <button type="button" className="btn btn-ghost" disabled={ocupado} onClick={() => setConfirmandoRechazo(false)}>
              No
            </button>
            <button type="button" className="btn btn-secondary" disabled={ocupado} onClick={() => hacer(rechazarClase)}>
              Si, rechazar
            </button>
          </>
        ) : (
          <>
            <button type="button" className="btn btn-secondary" disabled={ocupado} onClick={() => setConfirmandoRechazo(true)}
                    aria-label={`Rechazar la solicitud de ${nombre}`}>
              Rechazar
            </button>
            <button type="button" className="btn btn-primary" disabled={ocupado} onClick={() => hacer(aprobarClase)}
                    aria-label={`Aprobar la solicitud de ${nombre}`}>
              {ocupado ? 'Aprobando...' : 'Aprobar'}
            </button>
          </>
        )}
      </div>
      {error && <div className="solicitud-error"><Alerta tipo="error">{error}</Alerta></div>}
    </li>
  )
}

export default function Solicitudes({ bloque, alCambiar }) {
  const { datos, error, cargando } = bloque

  return (
    <section className="tablero-bloque" aria-labelledby="solicitudes-titulo">
      <div className="tablero-encabezado">
        <h3 id="solicitudes-titulo">
          Solicitudes por aprobar{datos?.length ? ` (${datos.length})` : ''}
        </h3>
        <span className="tablero-resumen">Quedan pendientes hasta que respondas</span>
      </div>

      {cargando && !datos && <p className="tablero-vacio">Cargando las solicitudes...</p>}
      {error && <Alerta tipo="error">No pudimos traer las solicitudes. {error}</Alerta>}
      {datos && datos.length === 0 && <p className="tablero-vacio">No tenes solicitudes nuevas.</p>}
      {datos && datos.length > 0 && (
        <ul className={`solicitudes${cargando ? ' tablero-recargando' : ''}`}>
          {datos.map((s) => <Solicitud key={s.id} solicitud={s} alCambiar={alCambiar} />)}
        </ul>
      )}
    </section>
  )
}
