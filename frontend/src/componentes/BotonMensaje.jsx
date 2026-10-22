/**
 * El boton "Mensaje": abre la conversacion con otra persona y lleva a 1h.
 *
 *   <BotonMensaje personaId={profe.id} />                      -> "Mensaje"
 *   <BotonMensaje personaId={id} className="btn btn-block">Enviar mensaje</BotonMensaje>
 *
 * Llama a POST /api/mensajes/hilos (que devuelve el hilo existente si ya lo
 * hay) y navega a /mensajes?hilo=ID. El id va en el campo del rol de la otra
 * persona: el alumno le escribe a un profe (profesor_id) y el profe a un
 * alumno (estudiante_id; el backend exige que tengan alguna clase).
 *
 * Lo usan 1a y 1f (P2), 1d (P4) y 1b, 1i (P3). Si falla, muestra el error
 * debajo del boton, sin salir de la pantalla.
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { mensajeDeError } from '../api/mensajes.js'
import { abrirHilo } from '../api/mensajeria.js'
import { useAuth } from '../auth/ContextoAuth.jsx'

export default function BotonMensaje({ personaId, className = 'btn btn-secondary', children = 'Mensaje' }) {
  const { usuario } = useAuth()
  const navigate = useNavigate()
  const [abriendo, setAbriendo] = useState(false)
  const [error, setError] = useState(null)

  async function abrir() {
    setError(null)
    setAbriendo(true)
    try {
      const campo = usuario.rol === 'profesor' ? 'estudiante_id' : 'profesor_id'
      const hilo = await abrirHilo({ [campo]: personaId })
      navigate(`/mensajes?hilo=${hilo.id}`)
    } catch (err) {
      setError(mensajeDeError(err.codigo))
      setAbriendo(false)
    }
  }

  return (
    <>
      <button type="button" className={className} onClick={abrir} disabled={abriendo}>
        {abriendo ? 'Abriendo...' : children}
      </button>
      {error && <span className="boton-mensaje-error" role="alert">{error}</span>}
    </>
  )
}
