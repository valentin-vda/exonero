/**
 * Las resenas que recibio una persona: el promedio, una barra por estrella y
 * la lista paginada, con GET /api/resenas/usuario/{id}.
 *
 *    4,6        5 ★ ████████████  6
 *   ★★★★★       4 ★ ████          2
 *   8 resenas   3 ★ ██            1
 *               ...
 *   ★ 5  "Viene con las dudas anotadas..."         12 de octubre de 2026
 *   ...                                              [Ver mas]
 *
 * Es de P3 (resenas) y hoy la usa la pestania "Mis resenas" de 1e. Sirve
 * igual para un profesor: mismo contrato.
 *
 * Son anonimas: el backend no manda el autor, y aca no hay nada que mostrar
 * de el.
 */

import { useEffect, useState } from 'react'

import { mensajeDeError } from '../../api/mensajes.js'
import { obtenerResenas } from '../../api/resenas.js'
import { ESTRELLA, puntaje } from '../../utiles/formato.js'
import Alerta from '../Alerta.jsx'

// De a cuantas las manda el backend (POR_PAGINA en resenas/logica.py).
const POR_PAGINA = 10

/** '2026-10-12' -> "12 de octubre de 2026". La fecha ya viene en Montevideo. */
function fechaLarga(dia) {
  return new Date(`${dia}T12:00:00Z`).toLocaleDateString('es-UY', {
    day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC',
  })
}

export default function ResumenResenas({ usuarioId, vacio = 'Todavia no te calificaron.' }) {
  const [datos, setDatos] = useState(null)
  const [pagina, setPagina] = useState(1)
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState(null)

  function cargar(numero) {
    setCargando(true)
    obtenerResenas(usuarioId, 'recientes', numero)
      .then((respuesta) => {
        setDatos((antes) => (numero === 1 ? respuesta : { ...respuesta, resenas: [...antes.resenas, ...respuesta.resenas] }))
        setPagina(numero)
      })
      .catch((err) => setError(mensajeDeError(err.codigo)))
      .finally(() => setCargando(false))
  }

  useEffect(() => {
    cargar(1)
  }, [usuarioId])

  if (error) return <Alerta tipo="error">No pudimos traer las resenas. {error}</Alerta>
  if (!datos) return <p className="tablero-vacio">Cargando...</p>
  if (datos.total === 0) return <p className="tablero-vacio">{vacio}</p>

  const maximo = Math.max(...Object.values(datos.distribucion), 1)

  return (
    <div className="resumen-resenas">
      <div className="resumen-resenas-cabecera">
        <div className="resumen-resenas-promedio">
          <strong>{puntaje(datos.promedio)}</strong>
          <span aria-hidden="true">{ESTRELLA.repeat(Math.round(datos.promedio))}</span>
          <span className="texto-chico">{datos.total === 1 ? '1 resena' : `${datos.total} resenas`}</span>
        </div>
        <ul className="resumen-resenas-barras" aria-label="Cuantas resenas de cada puntaje">
          {['5', '4', '3', '2', '1'].map((estrella) => (
            <li key={estrella}>
              <span>{estrella} {ESTRELLA}</span>
              <span className="resumen-resenas-barra">
                <span style={{ width: `${(100 * datos.distribucion[estrella]) / maximo}%` }} />
              </span>
              <span>{datos.distribucion[estrella]}</span>
            </li>
          ))}
        </ul>
      </div>

      <ul className="resumen-resenas-lista">
        {datos.resenas.map((r, i) => (
          // Sin id: son anonimas, el backend no manda nada que las identifique.
          <li key={`${r.fecha}-${i}`}>
            <span className="resumen-resenas-puntaje">{ESTRELLA} {r.puntaje}</span>
            <span>{r.texto || <em className="text-muted">Sin comentario</em>}</span>
            <span className="texto-chico">{fechaLarga(r.fecha)}</span>
          </li>
        ))}
      </ul>
      {datos.resenas.length < datos.total && datos.resenas.length === pagina * POR_PAGINA && (
        <div className="botonera">
          <button type="button" className="btn btn-secondary" disabled={cargando} onClick={() => cargar(pagina + 1)}>
            {cargando ? 'Cargando...' : 'Ver mas'}
          </button>
        </div>
      )}
    </div>
  )
}
