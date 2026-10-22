/**
 * La pestania "Bloqueos" de 1i: los ratos puntuales en que el profesor no
 * puede, aunque caigan dentro de su disponibilidad semanal.
 *
 *   Dia [30/10/2026]  Desde [14:00]  Hasta [16:00]  [ ] Todo el dia
 *   Motivo [Turno medico          ]                       [Bloquear]
 *
 *   Proximos bloqueos
 *   viernes 30 de octubre, 14:00 a 16:00 · Turno medico       [Quitar]
 *
 * No se puede bloquear encima de una clase confirmada (409
 * hay_clase_aprobada): primero hay que cancelarla o reprogramarla. Encima de
 * una solicitud a confirmar si se puede; despues, al aprobarla, el backend
 * avisa que el horario esta ocupado.
 *
 * Carga su propia lista (GET /api/agenda/yo/bloqueos: los que todavia no
 * terminaron) y llama a `alCambiar` despues de crear o quitar, para que la
 * pantalla redibuje el calendario.
 */

import { useEffect, useState } from 'react'

import { borrarBloqueo, crearBloqueo, listarBloqueos } from '../../api/agenda.js'
import { mensajeDeError } from '../../api/mensajes.js'
import Alerta from '../../componentes/Alerta.jsx'
import { diaYHora, hora } from '../../utiles/formato.js'
import { diaEnMontevideo, hoy, sumarDias } from '../panel/fechas.js'

export default function Bloqueos({ alCambiar }) {
  const [lista, setLista] = useState(null)
  const [errorCarga, setErrorCarga] = useState(null)
  const [dia, setDia] = useState(sumarDias(hoy(), 1))
  const [desde, setDesde] = useState('14:00')
  const [hasta, setHasta] = useState('16:00')
  const [todoElDia, setTodoElDia] = useState(false)
  const [motivo, setMotivo] = useState('')
  const [mensaje, setMensaje] = useState(null)
  const [ocupado, setOcupado] = useState(false)

  function cargar() {
    return listarBloqueos()
      .then(setLista)
      .catch((error) => setErrorCarga(mensajeDeError(error.codigo)))
  }

  useEffect(() => {
    cargar()
  }, [])

  async function bloquear(evento) {
    evento.preventDefault()
    setMensaje(null)
    if (!todoElDia && hasta <= desde) {
      setMensaje({ tipo: 'error', texto: 'El bloqueo tiene que terminar despues de empezar.' })
      return
    }
    setOcupado(true)
    try {
      // Sin zona: el backend las toma en hora de Montevideo. "Todo el dia" va
      // de las 0 a las 0 del dia siguiente.
      await crearBloqueo({
        inicio: `${dia}T${todoElDia ? '00:00' : desde}:00`,
        fin: todoElDia ? `${sumarDias(dia, 1)}T00:00:00` : `${dia}T${hasta}:00`,
        motivo: motivo.trim() || null,
      })
      setMotivo('')
      setMensaje({ tipo: 'ok', texto: 'Listo, ese rato ya no se puede reservar.' })
      await cargar()
      alCambiar()
    } catch (error) {
      setMensaje({ tipo: 'error', texto: mensajeDeError(error.codigo) })
    } finally {
      setOcupado(false)
    }
  }

  async function quitar(id) {
    setMensaje(null)
    try {
      await borrarBloqueo(id)
      await cargar()
      alCambiar()
    } catch (error) {
      setMensaje({ tipo: 'error', texto: mensajeDeError(error.codigo) })
    }
  }

  /** "viernes 30 de octubre, 14:00 a 16:00", o con los dos dias si son distintos. */
  function cuando(b) {
    const mismoDia = diaEnMontevideo(b.inicio) === diaEnMontevideo(new Date(new Date(b.fin).getTime() - 1))
    return mismoDia ? `${diaYHora(b.inicio)} a ${hora(b.fin)}` : `${diaYHora(b.inicio)} a ${diaYHora(b.fin)}`
  }

  return (
    <div className="bloqueos">
      <form className="bloqueos-form" onSubmit={bloquear} noValidate>
        <div className="field">
          <label htmlFor="bloqueo-dia">Dia</label>
          <input id="bloqueo-dia" type="date" className="input" min={hoy()} value={dia} onChange={(e) => setDia(e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="bloqueo-desde">Desde</label>
          <input id="bloqueo-desde" type="time" className="input" step="900" value={desde} disabled={todoElDia}
                 onChange={(e) => setDesde(e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="bloqueo-hasta">Hasta</label>
          <input id="bloqueo-hasta" type="time" className="input" step="900" value={hasta} disabled={todoElDia}
                 onChange={(e) => setHasta(e.target.value)} />
        </div>
        <label className="bloqueos-todo-el-dia">
          <input type="checkbox" checked={todoElDia} onChange={(e) => setTodoElDia(e.target.checked)} />
          Todo el dia
        </label>
        <div className="field bloqueos-motivo">
          <label htmlFor="bloqueo-motivo">Motivo (solo lo ves vos)</label>
          <input id="bloqueo-motivo" className="input" maxLength={200} value={motivo}
                 onChange={(e) => setMotivo(e.target.value)} placeholder="Turno medico" />
        </div>
        <button type="submit" className="btn btn-primary" disabled={ocupado || !dia}>
          {ocupado ? 'Bloqueando...' : 'Bloquear'}
        </button>
      </form>

      <Alerta tipo={mensaje?.tipo}>{mensaje?.texto}</Alerta>

      <h4>Proximos bloqueos</h4>
      {errorCarga && <Alerta tipo="error">{errorCarga}</Alerta>}
      {!lista && !errorCarga && <p className="tablero-vacio">Cargando...</p>}
      {lista && lista.length === 0 && <p className="tablero-vacio">No tenes bloqueos por delante.</p>}
      {lista && lista.length > 0 && (
        <ul className="bloqueos-lista">
          {lista.map((b) => (
            <li key={b.id}>
              <span>
                <strong>{cuando(b)}</strong>
                {b.motivo && <span className="texto-chico"> · {b.motivo}</span>}
              </span>
              <button type="button" className="btn btn-ghost" onClick={() => quitar(b.id)}
                      aria-label={`Quitar el bloqueo del ${cuando(b)}`}>
                Quitar
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
