/**
 * El bloque de Ingresos (1d), con GET /api/pagos/ingresos?periodo=mes&agrupar=:
 *
 *   Ingresos  octubre a hoy                                 [Semana|Mes|Anio]
 *   $ 24.300            $ 4.226                  $ 1.350
 *   cobrado este mes    pendiente de aprobacion  promedio por clase
 *   (grafico de barras con lo cobrado en cada tramo)
 *
 * Las tres cifras son siempre del mes en curso, como en el mockup. El selector
 * cambia solo de a cuanto se agrupan las barras (semana, mes o anio), y
 * recarga solo este bloque.
 *
 * Los importes llegan como texto ("1913.18") y se muestran con pesos(). Para
 * el grafico se pasan a numero, pero solo para saber que tan alta va cada
 * barra: ninguna cuenta de plata se hace en el frontend.
 */

import Alerta from '../../componentes/Alerta.jsx'
import { pesos } from '../../utiles/formato.js'
import { conTodosLosTramos, etiquetas, mesActual } from './fechas.js'
import GraficoBarras from './GraficoBarras.jsx'
import { AGRUPAR_INGRESOS, POR_TRAMO } from './opciones.js'
import Selector from './Selector.jsx'

const SERIES = [{ id: 'importe', texto: 'Cobrado', clase: 'serie-ingresos' }]

/** La serie del backend -> las columnas del grafico, con 0 en los tramos sin cobros. */
function columnas(serie, agrupar) {
  const porTramo = new Map(serie.map((punto) => [punto.etiqueta, Number(punto.importe)]))
  return conTodosLosTramos(agrupar, porTramo.keys()).map((dia, i) => ({
    clave: dia,
    ...etiquetas(dia, agrupar, i),
    valores: { importe: porTramo.get(dia) || 0 },
  }))
}

export default function Ingresos({ bloque, agrupar, alCambiarAgrupar }) {
  // `para` es la agrupacion de los datos que hay en pantalla. Mientras llega
  // lo nuevo puede no ser la del selector (ver useBloque.js).
  const { datos, para, error, cargando } = bloque

  return (
    <section className="tablero-bloque tablero-bloque-acento" aria-labelledby="ingresos-titulo">
      <div className="tablero-encabezado">
        <div className="tablero-encabezado-texto">
          <h3 id="ingresos-titulo">Ingresos</h3>
          <span className="tablero-resumen">{mesActual()} a hoy</span>
        </div>
        <Selector
          nombre="ingresos-agrupar"
          etiqueta="Agrupar los ingresos por"
          opciones={AGRUPAR_INGRESOS}
          valor={agrupar}
          alCambiar={alCambiarAgrupar}
        />
      </div>

      {/* La primera vez no hay nada que mostrar mientras carga. Despues, al
          cambiar el selector, se deja lo anterior atenuado hasta que llega lo
          nuevo. */}
      {cargando && !datos && <p className="tablero-vacio">Cargando tus ingresos...</p>}
      {error && <Alerta tipo="error">No pudimos traer tus ingresos. {error}</Alerta>}

      {datos && (
        <div className={cargando ? 'tablero-recargando' : undefined} aria-busy={cargando}>
          <div className="tablero-cifras">
            <div>
              <div className="tablero-cifra-grande">{pesos(datos.cobrado)}</div>
              <div className="tablero-cifra-nota">cobrado este mes</div>
            </div>
            <div>
              <div className="tablero-cifra">{pesos(datos.pendiente)}</div>
              <div className="tablero-cifra-nota">pendiente de aprobacion</div>
            </div>
            <div>
              <div className="tablero-cifra">{pesos(datos.promedio_por_clase)}</div>
              <div className="tablero-cifra-nota">promedio por clase</div>
            </div>
          </div>

          <GraficoBarras
            titulo={`Ingresos cobrados ${POR_TRAMO[para]}`}
            series={SERIES}
            columnas={columnas(datos.serie || [], para)}
            formato={pesos}
            textoVacio="Todavia no hay cobros en este periodo."
          />
        </div>
      )}

      <p className="tablero-nota">
        Se cuenta el cobro cuando aprobas la solicitud. Lo pendiente no entra en el total.
      </p>
    </section>
  )
}
