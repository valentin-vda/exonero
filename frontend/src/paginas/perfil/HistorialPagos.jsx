/**
 * El historial de pagos de 1e: aparece debajo de "Medios de pago" al tocar
 * "Ver historial de pagos". GET /api/pagos/historial.
 *
 * Una fila por cobro de cada clase reservada:
 *
 *   Matematica con Lucia Fernandez        $ 2.013   [Pendiente de aprobacion]
 *   martes 21 de octubre, 18:00 · Clase #42
 *
 * El estado del cobro sale del flujo del dinero (seccion 9 de la doc):
 *   retenido     se reservo y el profe todavia no respondio
 *   cobrado      el profe aprobo: se debito
 *   liberado     el profe rechazo: no se cobro nada
 *   reembolsado  se cancelo despues de aprobada: se devolvio
 *
 * Ojo con los liberados: al rechazar, la clase se BORRA y el cobro queda
 * solo, asi que materia, contraparte y clase_id pueden venir en null.
 *
 * Se arma cada vez que se abre (al cerrarlo desaparece), asi que siempre
 * muestra lo ultimo sin un boton de recargar.
 *
 * El backend lo manda de a paginas, lo mas nuevo primero. Si una pagina
 * llega llena, puede haber mas: aparece "Ver mas pagos", que pide la
 * siguiente y la suma abajo.
 */

import { useEffect, useState } from 'react'

import { mensajeDeError } from '../../api/mensajes.js'
import { historialPagos } from '../../api/pagos.js'
import Alerta from '../../componentes/Alerta.jsx'
import { diaYHora, pesos, unir } from '../../utiles/formato.js'

const POR_PAGINA = 50 // el mismo tamanio de pagina que el backend (pagos/logica.py)

// El texto y el color de la etiqueta de cada estado del cobro.
const ESTADOS = {
  retenido: { texto: 'Pendiente de aprobacion', clase: 'tag-neutral' },
  cobrado: { texto: 'Pagado', clase: 'tag-accent-2' },
  liberado: { texto: 'Solicitud rechazada · no se cobro', clase: 'tag-outline' },
  reembolsado: { texto: 'Reembolsado', clase: 'tag-accent' },
}

/** "Matematica con Lucia Fernandez", con lo que haya. */
function descripcion(movimiento) {
  const { materia, contraparte } = movimiento
  if (materia && contraparte) return `${materia} con ${contraparte}`
  if (materia || contraparte) return materia || `Clase con ${contraparte}`
  // Un liberado: la clase ya no existe.
  return 'Reserva rechazada'
}

export default function HistorialPagos() {
  const [movimientos, setMovimientos] = useState([])
  const [pagina, setPagina] = useState(1) // la ultima que se pidio
  const [hayMas, setHayMas] = useState(false)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)

  /** Pide una pagina y la suma al final de lo que ya se ve. */
  function cargar(numero) {
    setCargando(true)
    setError(null)
    historialPagos({ pagina: numero })
      .then((nuevos) => {
        // Una lista nueva con los de antes y los de esta pagina: nunca push().
        setMovimientos((previos) => (numero === 1 ? nuevos : [...previos, ...nuevos]))
        setPagina(numero)
        setHayMas(nuevos.length === POR_PAGINA)
      })
      .catch((e) => setError(mensajeDeError(e.codigo)))
      .finally(() => setCargando(false))
  }

  useEffect(() => {
    cargar(1)
  }, [])

  return (
    <section className="panel" aria-labelledby="historial-titulo" id="historial-pagos">
      <h4 id="historial-titulo">Historial de pagos</h4>

      <Alerta tipo="error">{error}</Alerta>

      {!cargando && !error && movimientos.length === 0 && (
        <p className="vacio">
          Todavia no hiciste ningun pago. Cuando reserves una clase, el cobro aparece aca.
        </p>
      )}

      {movimientos.length > 0 && (
        <ul className="movimientos">
          {movimientos.map((movimiento) => {
            const estado = ESTADOS[movimiento.estado] || { texto: movimiento.estado, clase: 'tag-neutral' }
            return (
              <li key={movimiento.id} className="movimiento">
                <div className="medio-datos">
                  <span className="medio-nombre">{descripcion(movimiento)}</span>
                  <span className="medio-meta">
                    {unir([diaYHora(movimiento.fecha), movimiento.clase_id && `Clase #${movimiento.clase_id}`])}
                  </span>
                </div>
                <span className="movimiento-importe">{pesos(movimiento.importe)}</span>
                <span className={`tag ${estado.clase}`}>{estado.texto}</span>
              </li>
            )
          })}
        </ul>
      )}

      {cargando && !hayMas && <p className="text-muted">Cargando tus pagos...</p>}

      {/* El boton no desaparece mientras carga la pagina siguiente (si
          desapareciera, quien usa el teclado perderia el foco): solo avisa. */}
      {hayMas && (
        <div className="botonera" style={{ marginTop: '16px' }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => !cargando && cargar(pagina + 1)}
            aria-disabled={cargando ? 'true' : undefined}
          >
            {cargando ? 'Cargando...' : 'Ver mas pagos'}
          </button>
        </div>
      )}
    </section>
  )
}
