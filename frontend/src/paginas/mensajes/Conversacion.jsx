/**
 * La conversacion abierta de 1h, a la derecha:
 *
 *   [<] (LF) Lucia Fernandez · Matematica · Fisica          [Ver perfil]
 *   ----------------------------------------------------------------------
 *                         [Cargar anteriores]
 *                               Ayer
 *   | Hola Lucia! Queria saber si das...  |
 *                     | Hola! Si, claro. Contame... |   <- los mios, a la derecha
 *   ----------------------------------------------------------------------
 *   [Tenes lugar esta semana?] [Gracias!] [Te confirmo en un rato]
 *   [ Escribi un mensaje...                                    ] [Enviar]
 *
 * Como funciona:
 *   - Al abrirse pide los ultimos 30 (GET /hilos/{id}/mensajes). Ese GET
 *     marca como leidos los del otro: abrir es leer. Avisa a la cabecera con
 *     EVENTO_LEIDOS para que el contador baje enseguida.
 *   - Cada diez segundos vuelve a pedir los ultimos y suma los nuevos (por id,
 *     sin repetir). Asi llega la respuesta del otro sin recargar la pagina.
 *   - "Cargar anteriores" pide los de antes del mas viejo que hay (antes=id).
 *   - Enter envia, Shift+Enter hace un renglon nuevo. Las respuestas rapidas
 *     son texto fijo del frontend: se mandan como un mensaje comun.
 *
 * Despues de enviar llama a `alCambiar`, para que la bandeja se reordene.
 */

import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import { mensajeDeError } from '../../api/mensajes.js'
import { enviarMensaje, mensajesDelHilo } from '../../api/mensajeria.js'
import { useAuth } from '../../auth/ContextoAuth.jsx'
import Alerta from '../../componentes/Alerta.jsx'
import Avatar from '../../componentes/Avatar.jsx'
import { EVENTO_LEIDOS } from '../../componentes/useNoLeidos.js'
import { hora, unir } from '../../utiles/formato.js'
import { diaEnMontevideo } from '../panel/fechas.js'
import { separadorDeDia } from './fechas.js'

const CADA_MS = 10_000
const POR_PAGINA = 30

// Texto fijo, distinto segun quien escribe.
const RAPIDAS = {
  estudiante: ['¿Tenés lugar esta semana?', '¡Gracias!', 'Te confirmo en un rato'],
  profesor: ['¡Hola! Sí, tengo lugar.', 'Mandame la solicitud desde mi ficha', '¡Gracias!'],
}

/** Junta dos listas de mensajes sin repetir, ordenadas por id (que es el orden de envio). */
function juntar(a, b) {
  const porId = new Map([...a, ...b].map((m) => [m.id, m]))
  return [...porId.values()].sort((x, y) => x.id - y.id)
}

export default function Conversacion({ hilo, alVolver, alCambiar }) {
  const { usuario } = useAuth()
  const [mensajes, setMensajes] = useState(null)
  const [hayAnteriores, setHayAnteriores] = useState(false)
  const [texto, setTexto] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState(null)
  const finRef = useRef(null)
  // Si el ultimo cambio fue sumar mensajes al final (y no cargar anteriores),
  // se baja hasta el ultimo.
  const bajar = useRef(true)

  const otra = hilo.contraparte
  const nombre = [otra.nombre, otra.apellido].filter(Boolean).join(' ')
  const detalle = otra.rol === 'profesor' ? unir(otra.materias) : unir([otra.etapa, otra.centro])

  useEffect(() => {
    let vigente = true

    function traerUltimos(primeraVez) {
      mensajesDelHilo(hilo.id, null, POR_PAGINA)
        .then((nuevos) => {
          if (!vigente) return
          setMensajes((antes) => {
            const juntos = juntar(antes || [], nuevos)
            bajar.current = primeraVez || juntos.length !== (antes || []).length
            return juntos
          })
          if (primeraVez) setHayAnteriores(nuevos.length === POR_PAGINA)
          window.dispatchEvent(new Event(EVENTO_LEIDOS))
        })
        .catch((err) => vigente && setError(mensajeDeError(err.codigo)))
    }

    setMensajes(null)
    setError(null)
    traerUltimos(true)
    const reloj = setInterval(() => !document.hidden && traerUltimos(false), CADA_MS)
    return () => {
      vigente = false
      clearInterval(reloj)
    }
  }, [hilo.id])

  useEffect(() => {
    if (bajar.current) finRef.current?.scrollIntoView({ block: 'end' })
  }, [mensajes])

  async function cargarAnteriores() {
    const anteriores = await mensajesDelHilo(hilo.id, mensajes[0].id, POR_PAGINA)
    bajar.current = false
    setMensajes((actuales) => juntar(anteriores, actuales))
    setHayAnteriores(anteriores.length === POR_PAGINA)
  }

  async function enviar(contenido) {
    const limpio = contenido.trim()
    if (!limpio || enviando) return
    setEnviando(true)
    setError(null)
    try {
      const nuevo = await enviarMensaje(hilo.id, limpio)
      bajar.current = true
      setMensajes((actuales) => juntar(actuales || [], [nuevo]))
      setTexto('')
      alCambiar()
    } catch (err) {
      setError(mensajeDeError(err.codigo))
    } finally {
      setEnviando(false)
    }
  }

  function alTeclear(evento) {
    if (evento.key === 'Enter' && !evento.shiftKey) {
      evento.preventDefault()
      enviar(texto)
    }
  }

  // Los mensajes con un separador cada vez que cambia el dia.
  const renglones = []
  let diaAnterior = null
  for (const m of mensajes || []) {
    const dia = diaEnMontevideo(m.enviado_el)
    if (dia !== diaAnterior) renglones.push({ tipo: 'dia', dia })
    renglones.push({ tipo: 'mensaje', m })
    diaAnterior = dia
  }

  return (
    <section className="conversacion" aria-label={`Conversacion con ${nombre}`}>
      <header className="conversacion-cabecera">
        <button type="button" className="btn btn-ghost conversacion-volver" onClick={alVolver} aria-label="Volver a la bandeja">
          {'‹'}
        </button>
        <Avatar persona={otra} tamanio="mediano" />
        <div className="conversacion-quien">
          <strong>{nombre}</strong>
          {detalle && <span className="texto-chico">{detalle}</span>}
        </div>
        {otra.rol === 'profesor' && (
          <Link to={`/profesor/${otra.id}`} className="btn btn-secondary">Ver perfil</Link>
        )}
      </header>

      <div className="conversacion-mensajes" aria-live="polite">
        {hayAnteriores && (
          <button type="button" className="btn btn-ghost conversacion-anteriores" onClick={cargarAnteriores}>
            Cargar anteriores
          </button>
        )}
        {!mensajes && !error && <p className="tablero-vacio">Cargando...</p>}
        {mensajes && mensajes.length === 0 && (
          <p className="tablero-vacio conversacion-vacia">Todavia no se escribieron. Arranca vos.</p>
        )}
        {renglones.map((r) => (r.tipo === 'dia' ? (
          <div key={`d${r.dia}`} className="conversacion-dia">{separadorDeDia(r.dia)}</div>
        ) : (
          <div key={r.m.id} className={`burbuja${r.m.autor_id === usuario.id ? ' burbuja-mia' : ''}`}>
            <span className="burbuja-texto">{r.m.contenido}</span>
            <span className="burbuja-hora">{hora(r.m.enviado_el)}</span>
          </div>
        )))}
        <div ref={finRef} />
      </div>

      {error && <Alerta tipo="error">{error}</Alerta>}

      <div className="conversacion-rapidas" aria-label="Respuestas rapidas">
        {(RAPIDAS[usuario.rol] || []).map((r) => (
          <button key={r} type="button" className="tag tag-outline tag-boton" disabled={enviando} onClick={() => enviar(r)}>
            {r}
          </button>
        ))}
      </div>
      <form className="conversacion-escribir" onSubmit={(e) => { e.preventDefault(); enviar(texto) }}>
        <textarea
          className="input"
          rows={2}
          maxLength={2000}
          placeholder="Escribi un mensaje..."
          aria-label="Mensaje"
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          onKeyDown={alTeclear}
        />
        <button type="submit" className="btn btn-primary" disabled={enviando || !texto.trim()}>
          {enviando ? 'Enviando...' : 'Enviar'}
        </button>
      </form>
    </section>
  )
}
