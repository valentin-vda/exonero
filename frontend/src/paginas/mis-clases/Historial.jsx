/**
 * El historial de 1b: todas las clases DICTADAS, con GET /api/clases?estado=dictada.
 *
 *   Historial                                                    12 clases
 *   jueves 8 de octubre, 15:00   Matematica · Lucia Fernandez   $ 1.207,80
 *   ...
 *                              [Ver mas]
 *
 * El backend las da de a 50 por pagina, ordenadas de la mas vieja a la mas
 * nueva. Aca se muestran al reves (la mas reciente arriba). Con "Ver mas" se
 * pide la pagina siguiente; aparece solo si la ultima vino llena.
 */

import { useEffect, useState } from 'react'

import { listarClases } from '../../api/clases.js'
import { mensajeDeError } from '../../api/mensajes.js'
import Alerta from '../../componentes/Alerta.jsx'
import { diaYHora, pesos, unir } from '../../utiles/formato.js'

// El tamanio de pagina del backend (POR_PAGINA en clases/logica.py).
const POR_PAGINA = 50

/** "viernes, 16 de octubre" -> "Viernes, 16 de octubre". */
function conMayuscula(texto) {
  return texto.charAt(0).toUpperCase() + texto.slice(1)
}

export default function Historial() {
  const [clases, setClases] = useState(null)
  const [pagina, setPagina] = useState(1)
  const [hayMas, setHayMas] = useState(false)
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState(null)

  function cargar(numero) {
    setCargando(true)
    setError(null)
    listarClases({ estado: 'dictada', pagina: numero })
      .then((nuevas) => {
        // La pagina 1 REEMPLAZA: en desarrollo StrictMode corre el efecto dos
        // veces, y si sumara, cada clase saldria repetida.
        setClases((antes) => (numero === 1 ? nuevas : [...antes, ...nuevas]))
        setHayMas(nuevas.length === POR_PAGINA)
        setPagina(numero)
      })
      .catch((err) => setError(mensajeDeError(err.codigo)))
      .finally(() => setCargando(false))
  }

  useEffect(() => {
    cargar(1)
  }, [])

  const ordenadas = clases ? [...clases].sort((a, b) => b.inicio.localeCompare(a.inicio)) : []

  return (
    <section className="tablero-bloque" aria-labelledby="historial-titulo">
      <div className="tablero-encabezado">
        <h3 id="historial-titulo">Historial</h3>
        {clases && <span className="tablero-resumen">{clases.length === 1 ? '1 clase dictada' : `${clases.length} clases dictadas`}</span>}
      </div>
      {error && <Alerta tipo="error">No pudimos traer tu historial. {error}</Alerta>}
      {!clases && !error && <p className="tablero-vacio">Cargando tu historial...</p>}
      {clases && clases.length === 0 && <p className="tablero-vacio">Todavia no tuviste clases dictadas.</p>}
      {ordenadas.length > 0 && (
        <ul className="mis-clases-historial">
          {ordenadas.map((c) => (
            <li key={c.id}>
              <span className="mis-clases-historial-cuando">{conMayuscula(diaYHora(c.inicio))}</span>
              <span>{unir([c.materia, [c.contraparte.nombre, c.contraparte.apellido].filter(Boolean).join(' ')])}</span>
              <span className="mis-clases-historial-total">{pesos(c.total)}</span>
            </li>
          ))}
        </ul>
      )}
      {hayMas && (
        <div className="botonera">
          <button type="button" className="btn btn-secondary" disabled={cargando} onClick={() => cargar(pagina + 1)}>
            {cargando ? 'Cargando...' : 'Ver mas'}
          </button>
        </div>
      )}
    </section>
  )
}
