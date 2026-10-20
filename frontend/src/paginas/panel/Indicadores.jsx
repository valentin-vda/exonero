/**
 * Los cinco indicadores del panel (1d), con su selector Mes / Trimestre / Anio:
 *
 *   ALUMNOS ATENDIDOS  HORAS DICTADAS  ALUMNOS RECURRENTES  TASA DE CANCELACION  INGRESOS DEL MES
 *   38                 112             21                   6 %                  $ 24.300
 *   +6 % que el mes... -3 % que el...  55 % vuelve a ...    -25 % que el ...     cobrado este mes
 *
 * Salen de dos llamadas, cada una con su propio "cargando" y su propio error:
 *   GET /api/clases/metricas?periodo=   los cuatro primeros y sus variaciones
 *   GET /api/pagos/ingresos?periodo=    el cobrado del quinto
 *
 * La variacion la calcula el backend (en porcentaje, contra el periodo
 * anterior). Aca solo se decide como decirla y de que color: en la tasa de
 * cancelacion, bajar es bueno. El color nunca va solo: el texto dice "+" o "-".
 */

import Alerta from '../../componentes/Alerta.jsx'
import { pesos } from '../../utiles/formato.js'
import { DEL_PERIODO, ESTE_PERIODO, PERIODO_PASADO, PERIODOS } from './opciones.js'
import Selector from './Selector.jsx'

// Las flechas y el signo menos van como codigo para que el archivo siga sin
// caracteres especiales (ver formato.js).
const SUBE = '\u25B2'
const BAJA = '\u25BC'
const MENOS = '\u2212'

/** "18.5" -> "18,5". Para horas y porcentajes, que llegan como texto. */
function numero(valor) {
  return Number(valor).toLocaleString('es-UY', { maximumFractionDigits: 1 })
}

/**
 * La variacion contra el periodo anterior, lista para mostrar:
 *   6, 'mes'          -> { flecha: SUBE, texto: '+6 % que el mes pasado', tono: 'buena' }
 *   -25, 'mes', true  -> { flecha: BAJA, texto: '-25 % que el mes pasado', tono: 'buena' }
 *   null              -> el periodo anterior fue 0: no hay con que comparar
 */
function variacion(porcentaje, periodo, bajarEsBueno = false) {
  const pasado = PERIODO_PASADO[periodo]
  if (porcentaje === null || porcentaje === undefined) {
    return { texto: `Nada que comparar con ${pasado}` }
  }
  const redondo = Math.round(Number(porcentaje))
  if (redondo === 0) return { texto: `Igual que ${pasado}` }

  const sube = redondo > 0
  return {
    flecha: sube ? SUBE : BAJA,
    texto: `${sube ? '+' : MENOS}${Math.abs(redondo)} % que ${pasado}`,
    // Sube y subir es bueno, o baja y bajar es bueno: buena.
    tono: sube !== bajarEsBueno ? 'buena' : 'mala',
  }
}

/** Una de las cinco tarjetas. `valor` es null mientras carga o si fallo. */
function Indicador({ titulo, valor, notas, destacado = false }) {
  return (
    <div className={`tablero-indicador${destacado ? ' tablero-indicador-destacado' : ''}`}>
      <div className="tablero-indicador-titulo">{titulo}</div>
      <div className="tablero-indicador-valor">{valor ?? '\u2014'}</div>
      {/* Cada nota es un renglon chico. Si trae tono, se pinta (y lleva flecha). */}
      {notas.filter(Boolean).map((nota) => (
        <div key={nota.texto} className={`tablero-indicador-nota${nota.tono ? ` tablero-variacion-${nota.tono}` : ''}`}>
          {nota.flecha && <span aria-hidden="true">{nota.flecha} </span>}
          {nota.texto}
        </div>
      ))}
    </div>
  )
}

export default function Indicadores({ periodo, alCambiarPeriodo, metricas, cobrado }) {
  const m = metricas.datos
  // El periodo de los numeros que hay en pantalla. Mientras llegan los nuevos
  // puede no ser el del selector (ver useBloque.js).
  const delPeriodo = metricas.para || periodo
  const delCobrado = cobrado.para || periodo
  const cambio = m?.variacion || {}
  // "55 % vuelve a reservar": de los alumnos atendidos, cuantos ya habian venido.
  const vuelven = m && m.alumnos_atendidos > 0 ? Math.round((100 * m.alumnos_recurrentes) / m.alumnos_atendidos) : null

  return (
    <section aria-labelledby="indicadores-titulo">
      <div className="tablero-encabezado">
        <h3 id="indicadores-titulo">Tus numeros</h3>
        <Selector
          nombre="periodo"
          etiqueta="Periodo de los indicadores"
          opciones={PERIODOS}
          valor={periodo}
          alCambiar={alCambiarPeriodo}
        />
      </div>

      {metricas.error && <Alerta tipo="error">No pudimos traer tus indicadores. {metricas.error}</Alerta>}

      {/* aria-busy avisa que se esta actualizando; la clase lo atenua mientras
          tanto, sin borrar los numeros viejos (asi no salta todo de lugar). */}
      <div
        className={`tablero-indicadores${metricas.cargando || cobrado.cargando ? ' tablero-recargando' : ''}`}
        aria-busy={metricas.cargando || cobrado.cargando}
      >
        <Indicador
          titulo="Alumnos atendidos"
          valor={m ? m.alumnos_atendidos : null}
          notas={[m && variacion(cambio.alumnos_atendidos, delPeriodo)]}
        />
        <Indicador
          titulo="Horas dictadas"
          valor={m ? numero(m.horas_dictadas) : null}
          notas={[m && variacion(cambio.horas_dictadas, delPeriodo)]}
        />
        <Indicador
          titulo="Alumnos recurrentes"
          valor={m ? m.alumnos_recurrentes : null}
          notas={[
            vuelven !== null && { texto: `${vuelven} % vuelve a reservar` },
            m && variacion(cambio.alumnos_recurrentes, delPeriodo),
          ]}
        />
        <Indicador
          titulo="Tasa de cancelacion"
          valor={m ? `${numero(m.tasa_cancelacion)} %` : null}
          notas={[m && variacion(cambio.tasa_cancelacion, delPeriodo, true)]}
        />
        <Indicador
          titulo={`Ingresos ${DEL_PERIODO[delCobrado]}`}
          valor={cobrado.datos ? pesos(cobrado.datos.cobrado) : null}
          notas={[
            cobrado.datos && { texto: `cobrado ${ESTE_PERIODO[delCobrado]}` },
            cobrado.error && { texto: 'No pudimos traer tus ingresos.' },
          ]}
          destacado
        />
      </div>
    </section>
  )
}
