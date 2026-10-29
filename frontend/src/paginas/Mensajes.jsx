/**
 * 1h - Mensajes. Ruta: /mensajes (con ?hilo=ID abre esa conversacion; asi
 * llegan los botones "Mensaje" de 1a, 1b, 1d, 1f y 1i).
 *
 * Chat directo entre alumno y profesor, sin contexto de clase y sin reservar
 * desde aca. La comparten los dos roles.
 *
 *   Mensajes           <- esta pantalla: la bandeja y cual esta abierta
 *   +-- Bandeja        la lista de conversaciones, con buscador    /mensajes/hilos?q=
 *   +-- Conversacion   la abierta: historial, enviar, rapidas      /mensajes/hilos/{id}/mensajes
 *
 * La conversacion elegida vive en la URL (?hilo=ID): se puede recargar o
 * compartir el enlace y vuelve a la misma. En el celular se ve una sola
 * columna a la vez: la bandeja, o la conversacion con un boton para volver.
 *
 * La bandeja se refresca cada diez segundos (los no leidos y el orden
 * cambian cuando escribe el otro) y despues de cada envio. La busqueda espera
 * un momento a que se termine de escribir antes de preguntar.
 */

import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { mensajeDeError } from '../api/mensajes.js'
import { bandeja } from '../api/mensajeria.js'
import { useAuth } from '../auth/ContextoAuth.jsx'
import Bandeja from './mensajes/Bandeja.jsx'
import Conversacion from './mensajes/Conversacion.jsx'

const CADA_MS = 10_000
const ESPERA_BUSQUEDA_MS = 300

export default function Mensajes() {
  const { usuario } = useAuth()
  const [parametros, setParametros] = useSearchParams()
  const elegido = Number(parametros.get('hilo')) || null

  const [hilos, setHilos] = useState(null)
  const [error, setError] = useState(null)
  const [busqueda, setBusqueda] = useState('')
  // La busqueda vigente, para que el reloj de diez segundos use la ultima.
  const busquedaRef = useRef('')

  function cargar() {
    return bandeja(busquedaRef.current)
      .then((lista) => {
        setHilos(lista)
        setError(null)
      })
      .catch((err) => setError(mensajeDeError(err.codigo)))
  }

  useEffect(() => {
    const reloj = setInterval(() => !document.hidden && cargar(), CADA_MS)
    return () => clearInterval(reloj)
  }, [])

  // La primera carga, y cada busqueda: espera a que se deje de escribir (al
  // entrar no hay nada escrito y pregunta enseguida).
  useEffect(() => {
    busquedaRef.current = busqueda
    const espera = setTimeout(cargar, busqueda ? ESPERA_BUSQUEDA_MS : 0)
    return () => clearTimeout(espera)
  }, [busqueda])

  function elegir(id) {
    setParametros(id ? { hilo: String(id) } : {})
  }

  // El hilo elegido sale de la bandeja. Si se filtro y no esta en la lista,
  // se conserva el ultimo que se vio para no cerrar la conversacion.
  const vistoRef = useRef(null)
  const hiloElegido = hilos?.find((h) => h.id === elegido) || (vistoRef.current?.id === elegido ? vistoRef.current : null)
  if (hiloElegido) vistoRef.current = hiloElegido

  // La conversacion abierta ya esta leida (abrir es leer): su fila va sin el
  // numerito aunque la bandeja se haya pedido antes de abrirla.
  const filas = hilos?.map((h) => (h.id === elegido && h.no_leidos ? { ...h, no_leidos: 0 } : h))

  return (
    <div className="mensajes-pantalla">
      <div className="perfil-titulo">
        <h2>Mensajes</h2>
      </div>
      <div className={`mensajes${elegido ? ' mensajes-con-hilo' : ''}`}>
        <Bandeja
          hilos={filas}
          error={error}
          elegido={elegido}
          alElegir={elegir}
          busqueda={busqueda}
          alBuscar={setBusqueda}
          esAlumno={usuario.rol === 'estudiante'}
        />
        {hiloElegido ? (
          <Conversacion key={hiloElegido.id} hilo={hiloElegido} alVolver={() => elegir(null)} alCambiar={cargar} />
        ) : (
          <section className="conversacion conversacion-nada">
            <p className="tablero-vacio">
              {elegido && hilos ? 'Esa conversacion no existe o no es tuya.' : 'Elegi una conversacion de la lista.'}
            </p>
            {/* En el celular la bandeja esta escondida mientras hay un hilo
                elegido: sin este boton no habria por donde volver. */}
            {elegido && (
              <button type="button" className="btn btn-secondary conversacion-nada-volver" onClick={() => elegir(null)}>
                Volver a la bandeja
              </button>
            )}
          </section>
        )}
      </div>
    </div>
  )
}
