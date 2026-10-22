/**
 * El contador de mensajes sin leer de la cabecera, siempre al dia.
 *
 *   const sinLeer = useNoLeidos()
 *
 * Arranca con el que vino en GET /usuarios/yo (usuario.mensajes_no_leidos)
 * y despues pregunta GET /api/mensajes/no-leidos cada diez segundos, como
 * pide la spec. Es un solo COUNT en el backend, asi que es barato.
 *
 * Dos detalles:
 *   - Con la pestania escondida (otra pestania del navegador al frente) no
 *     pregunta: nadie lo esta mirando. Al volver, pregunta enseguida.
 *   - La conversacion de 1h avisa con el evento EVENTO_LEIDOS cuando abre un
 *     hilo (abrir es leer): el contador baja en el momento, sin esperar los
 *     diez segundos.
 */

import { useEffect, useState } from 'react'

import { noLeidos } from '../api/mensajeria.js'
import { useAuth } from '../auth/ContextoAuth.jsx'

const CADA_MS = 10_000

/** El evento que dispara 1h al leer mensajes. */
export const EVENTO_LEIDOS = 'exonero:mensajes-leidos'

export default function useNoLeidos() {
  const { usuario } = useAuth()
  const [cantidad, setCantidad] = useState(usuario?.mensajes_no_leidos || 0)

  useEffect(() => {
    if (!usuario) return undefined
    let vigente = true

    function preguntar() {
      if (document.hidden) return
      noLeidos()
        .then((r) => vigente && setCantidad(r.no_leidos))
        // Si falla (el backend se reinicia, se corta la red), queda el ultimo
        // numero: no vale la pena un cartel de error en la cabecera.
        .catch(() => {})
    }

    preguntar()
    const reloj = setInterval(preguntar, CADA_MS)
    document.addEventListener('visibilitychange', preguntar)
    window.addEventListener(EVENTO_LEIDOS, preguntar)
    return () => {
      vigente = false
      clearInterval(reloj)
      document.removeEventListener('visibilitychange', preguntar)
      window.removeEventListener(EVENTO_LEIDOS, preguntar)
    }
  }, [usuario?.id])

  return cantidad
}
