/**
 * Lo que se puede hacer con la clase que se toco en el calendario. Lo usan 1i
 * (el profesor) y 1b (el alumno); lo que se ofrece depende del rol del token:
 *
 *   Martes 27 de octubre · 17:00 · 1 h 30 min        [Confirmada]       x
 *   (AP) Ana Perez · Bachillerato · Liceo Bauza
 *   Matematica · Derivadas · Presencial · Av. Brasil 2550 · $ 1.913,18
 *   [Reprogramar] [Cancelar]                     <- confirmada, por delante
 *   [Marcar dictada] [No asistio]                <- confirmada, ya paso
 *   [Aprobar] [Rechazar] [Reprogramar] [Cancelar] <- a confirmar
 *
 * El alumno ve solo Reprogramar y Cancelar (en una confirmada por delante o
 * en una a confirmar). Son los mismos endpoints para los dos: quien lo hizo
 * sale del token. Aprobar, rechazar y completar son solo del profesor.
 *
 * `contraparte` es la otra persona: el alumno si mira el profesor, y el
 * profesor si mira el alumno (por eso el verificar usa su id en 1b).
 *
 * Reprogramar pregunta primero a POST /agenda/verificar para dar el motivo
 * concreto (fuera de franja, bloqueado...). Si dice "ocupado" se intenta
 * igual: puede ser la misma clase en su horario viejo (sigue confirmada
 * hasta que se mueve), y POST /clases/{id}/reprogramar decide de verdad.
 *
 * Despues de cualquier accion llama a `alCambiar` (la pantalla recarga el
 * calendario y las solicitudes).
 */

import { useState } from 'react'

import { verificarHorario } from '../../api/agenda.js'
import {
  aprobarClase, cancelarClase, completarClase, rechazarClase, reprogramarClase,
} from '../../api/clases.js'
import { mensajeDeError } from '../../api/mensajes.js'
import { useAuth } from '../../auth/ContextoAuth.jsx'
import { MOTIVOS_NO_LIBRE, MOTIVOS_NO_LIBRE_ALUMNO } from '../../paginas/agenda/opciones.js'
import { diaEnMontevideo, duracion } from '../../paginas/panel/fechas.js'
import { ESTADOS_CLASE, MODALIDAD_CLASE } from '../../paginas/panel/opciones.js'
import { CRUZ, diaYHora, hora, pesos, unir } from '../../utiles/formato.js'
import Alerta from '../Alerta.jsx'
import Avatar from '../Avatar.jsx'
import BotonMensaje from '../BotonMensaje.jsx'

export default function DetalleClase({ clase, alCerrar, alCambiar }) {
  const { usuario } = useAuth()
  // null, 'cancelar', 'reprogramar' o 'rechazar': que formulario esta abierto.
  const [abierto, setAbierto] = useState(null)
  const [motivo, setMotivo] = useState('')
  const [dia, setDia] = useState(diaEnMontevideo(clase.inicio))
  const [horaNueva, setHoraNueva] = useState(hora(clase.inicio))
  const [ocupado, setOcupado] = useState(false)
  const [error, setError] = useState(null)

  const esProfesor = usuario.rol === 'profesor'
  const otra = clase.contraparte
  const nombre = [otra.nombre, otra.apellido].filter(Boolean).join(' ')
  const estado = ESTADOS_CLASE[clase.estado] || { texto: clase.estado, clase: 'tag-neutral' }
  const yaPaso = new Date(clase.inicio).getTime() + clase.duracion_min * 60000 <= Date.now()
  // Lo que queda por hacer con la clase. Una confirmada que ya paso solo la
  // cierra el profesor (dictada o no asistio); el alumno ya no puede tocarla.
  const activa = clase.estado === 'pendiente' || (clase.estado === 'aprobada' && (esProfesor || !yaPaso))
  const motivos = esProfesor ? MOTIVOS_NO_LIBRE : MOTIVOS_NO_LIBRE_ALUMNO

  async function hacer(accion) {
    setError(null)
    setOcupado(true)
    try {
      await accion()
      alCambiar()
    } catch (err) {
      // horario_ocupado solo sale de aprobar (del profe): lleva su texto, no el del alumno.
      setError(mensajeDeError(err.codigo === 'horario_ocupado' ? 'horario_ocupado_al_aprobar' : err.codigo))
    } finally {
      setOcupado(false)
    }
  }

  async function reprogramar(evento) {
    evento.preventDefault()
    // Sin zona: el backend la toma en hora de Montevideo (fechas.con_zona).
    const inicio = `${dia}T${horaNueva}:00`
    setError(null)
    setOcupado(true)
    try {
      const profesorId = esProfesor ? usuario.id : otra.id
      const respuesta = await verificarHorario({ profesor_id: profesorId, inicio, duracion_min: clase.duracion_min })
      if (!respuesta.libre && respuesta.motivo !== 'ocupado') {
        setError(motivos[respuesta.motivo] || 'Ese horario no esta disponible.')
        return
      }
      await reprogramarClase(clase.id, { inicio })
      alCambiar()
    } catch (err) {
      setError(err.codigo === 'horario_ocupado' ? motivos.ocupado : mensajeDeError(err.codigo))
    } finally {
      setOcupado(false)
    }
  }

  function abrir(cual) {
    setError(null)
    setAbierto(abierto === cual ? null : cual)
  }

  return (
    <section className="tablero-bloque detalle-clase" aria-labelledby="detalle-titulo">
      <div className="tablero-encabezado">
        <div className="tablero-encabezado-texto">
          <h3 id="detalle-titulo">{diaYHora(clase.inicio)}</h3>
          <span className="tablero-resumen">{duracion(clase.duracion_min)}</span>
          <span className={`tag ${estado.clase}`}>{estado.texto}</span>
        </div>
        <button type="button" className="btn btn-ghost" onClick={alCerrar} aria-label="Cerrar el detalle de la clase">
          {CRUZ}
        </button>
      </div>

      <div className="detalle-quien">
        <Avatar persona={otra} />
        <span><strong>{nombre}</strong> {unir([otra.etapa, otra.centro]) && `· ${unir([otra.etapa, otra.centro])}`}</span>
        <BotonMensaje personaId={otra.id} className="btn btn-ghost" />
      </div>
      <p className="detalle-datos">
        {unir([clase.materia, clase.tema, MODALIDAD_CLASE[clase.modalidad], clase.ubicacion, pesos(clase.total)])}
      </p>

      <Alerta tipo="error">{error}</Alerta>

      {activa && (
        <div className="tablero-botones">
          {esProfesor && clase.estado === 'pendiente' && (
            <>
              <button type="button" className="btn btn-primary" disabled={ocupado}
                      onClick={() => hacer(() => aprobarClase(clase.id))}>Aprobar</button>
              <button type="button" className="btn btn-secondary" disabled={ocupado}
                      onClick={() => abrir('rechazar')} aria-expanded={abierto === 'rechazar'}>Rechazar</button>
            </>
          )}
          {esProfesor && clase.estado === 'aprobada' && yaPaso ? (
            <>
              <button type="button" className="btn btn-primary" disabled={ocupado}
                      onClick={() => hacer(() => completarClase(clase.id, 'dictada'))}>Marcar dictada</button>
              <button type="button" className="btn btn-secondary" disabled={ocupado}
                      onClick={() => hacer(() => completarClase(clase.id, 'no_asistida'))}>No asistio</button>
            </>
          ) : (
            <>
              <button type="button" className="btn btn-secondary" disabled={ocupado}
                      onClick={() => abrir('reprogramar')} aria-expanded={abierto === 'reprogramar'}>Reprogramar</button>
              <button type="button" className="btn btn-secondary" disabled={ocupado}
                      onClick={() => abrir('cancelar')} aria-expanded={abierto === 'cancelar'}>Cancelar clase</button>
            </>
          )}
        </div>
      )}

      {abierto === 'rechazar' && (
        <div className="detalle-formulario">
          <p className="texto-chico">La solicitud se borra y al alumno se le libera el pago retenido.</p>
          <button type="button" className="btn btn-secondary" disabled={ocupado}
                  onClick={() => hacer(() => rechazarClase(clase.id))}>Si, rechazar</button>
        </div>
      )}

      {abierto === 'cancelar' && (
        <form className="detalle-formulario" onSubmit={(e) => { e.preventDefault(); hacer(() => cancelarClase(clase.id, motivo.trim() || null)) }}>
          <div className="field">
            <label htmlFor="motivo-cancelar">Motivo (lo ve {esProfesor ? 'el alumno' : 'el profe'})</label>
            <input id="motivo-cancelar" className="input" value={motivo} maxLength={300}
                   onChange={(e) => setMotivo(e.target.value)}
                   placeholder={esProfesor ? 'Me surgio una mesa de examen' : 'Me surgio un parcial ese dia'} />
          </div>
          <p className="texto-chico">
            La clase queda cancelada en el historial y {esProfesor ? 'al alumno se le devuelve' : 'se te devuelve'} el total.
          </p>
          <button type="submit" className="btn btn-primary" disabled={ocupado}>
            {ocupado ? 'Cancelando...' : 'Confirmar cancelacion'}
          </button>
        </form>
      )}

      {abierto === 'reprogramar' && (
        <form className="detalle-formulario" onSubmit={reprogramar}>
          <div className="detalle-fila">
            <div className="field">
              <label htmlFor="dia-nuevo">Dia</label>
              <input id="dia-nuevo" type="date" className="input" value={dia} onChange={(e) => setDia(e.target.value)} required />
            </div>
            <div className="field">
              <label htmlFor="hora-nueva">Hora</label>
              <input id="hora-nueva" type="time" className="input" step="900" value={horaNueva}
                     onChange={(e) => setHoraNueva(e.target.value)} required />
            </div>
          </div>
          <p className="texto-chico">
            Misma duracion ({duracion(clase.duracion_min)}) y mismo importe. La clase vuelve a quedar a confirmar
            {esProfesor ? '.' : ': el profe tiene que aprobar el horario nuevo.'}
          </p>
          <button type="submit" className="btn btn-primary" disabled={ocupado || !dia || !horaNueva}>
            {ocupado ? 'Moviendo...' : 'Mover la clase'}
          </button>
        </form>
      )}
    </section>
  )
}
