/**
 * El bloque "Reservas en el tiempo" (1d), con GET /api/clases/series?agrupar=:
 *
 *   Reservas en el tiempo                          [10 semanas|Mes|Anio]
 *   17 reservas esta semana, el pico del periodo
 *   (barras apiladas: dictadas, confirmadas, a confirmar, no se dieron)
 *   [] Dictadas  [] Confirmadas  [] A confirmar  [] No se dieron
 *
 * El backend manda un renglon por tramo y por estado:
 *   [{ etiqueta: '2026-10-12', cantidad: 9, estado: 'dictada' },
 *    { etiqueta: '2026-10-12', cantidad: 2, estado: 'cancelada' }, ...]
 * y NO manda los tramos sin clases. Aca se juntan por tramo, se completan los
 * que faltan con 0 y cada estado va a su serie (SERIES_RESERVAS).
 *
 * La frase de arriba se calcula de los mismos datos: cuantas hay en el tramo
 * en curso y si es el pico de la ventana.
 */

import Alerta from '../../componentes/Alerta.jsx'
import { conTodosLosTramos, etiquetas } from './fechas.js'
import GraficoBarras from './GraficoBarras.jsx'
import { AGRUPAR_RESERVAS, ESTE_PERIODO, POR_TRAMO, SERIES_RESERVAS } from './opciones.js'
import Selector from './Selector.jsx'

// A que serie va cada estado: { dictada: 'dictada', cancelada: 'no_se_dio', ... }
const SERIE_DEL_ESTADO = Object.fromEntries(
  SERIES_RESERVAS.flatMap((serie) => serie.estados.map((estado) => [estado, serie.id])),
)

/** Los renglones del backend -> una columna por tramo, con la cantidad de cada serie. */
function columnas(puntos, agrupar) {
  const porTramo = new Map()
  for (const punto of puntos) {
    const serie = SERIE_DEL_ESTADO[punto.estado]
    if (!serie) continue
    const valores = porTramo.get(punto.etiqueta) || {}
    valores[serie] = (valores[serie] || 0) + punto.cantidad
    porTramo.set(punto.etiqueta, valores)
  }
  return conTodosLosTramos(agrupar, porTramo.keys()).map((dia, i) => ({
    clave: dia,
    ...etiquetas(dia, agrupar, i),
    valores: porTramo.get(dia) || {},
  }))
}

/** "17 reservas esta semana, el pico del periodo" o "...; el pico fue ..., con 21". */
function frase(lista, agrupar) {
  const total = (columna) => Object.values(columna.valores).reduce((suma, n) => suma + n, 0)
  const actual = total(lista[lista.length - 1])
  const pico = lista.reduce((mejor, columna) => (total(columna) > total(mejor) ? columna : mejor))

  const reservas = (n) => (n === 1 ? '1 reserva' : `${n} reservas`)
  const ahora = `${reservas(actual)} ${ESTE_PERIODO[agrupar]}`
  if (total(pico) === actual) return `${ahora}, el pico del periodo`
  // "la semana del 12 de octubre", "octubre de 2026", "2025"
  const cuando = agrupar === 'semana' ? `la ${pico.larga}` : pico.larga
  return `${ahora}; el pico fue ${cuando}, con ${total(pico)}`
}

export default function ReservasEnElTiempo({ bloque, agrupar, alCambiarAgrupar }) {
  // `para` es la ventana de los datos que hay en pantalla. Mientras llega lo
  // nuevo puede no ser la del selector (ver useBloque.js).
  const { datos, para, error, cargando } = bloque
  const lista = datos ? columnas(datos, para) : []
  // Se mira la lista ya armada y no lo que vino: un estado que no esta en
  // ninguna serie no cuenta como reserva.
  const hayReservas = lista.some((columna) => Object.values(columna.valores).some((n) => n > 0))

  return (
    <section className="tablero-bloque" aria-labelledby="reservas-titulo">
      <div className="tablero-encabezado">
        <h3 id="reservas-titulo">Reservas en el tiempo</h3>
        <Selector
          nombre="reservas-agrupar"
          etiqueta="Ventana del grafico de reservas"
          opciones={AGRUPAR_RESERVAS}
          valor={agrupar}
          alCambiar={alCambiarAgrupar}
        />
      </div>

      {cargando && !datos && <p className="tablero-vacio">Cargando tus reservas...</p>}
      {error && <Alerta tipo="error">No pudimos traer tus reservas. {error}</Alerta>}

      {datos && (
        <div className={cargando ? 'tablero-recargando' : undefined} aria-busy={cargando}>
          {hayReservas && <p className="tablero-resumen">{frase(lista, para)}</p>}
          <GraficoBarras
            titulo={`Reservas ${POR_TRAMO[para]}, por estado`}
            series={SERIES_RESERVAS}
            columnas={lista}
            formato={(n) => n.toLocaleString('es-UY')}
            enteros
            textoVacio="Todavia no hay reservas en este periodo."
          />
        </div>
      )}
    </section>
  )
}
