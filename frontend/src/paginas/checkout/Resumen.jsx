/**
 * La columna "Resumen" del checkout (1g): el desglose, el total y el boton de
 * confirmar.
 *
 *   Subtotal                     $ 1.350
 *     1,5 h x $ 900
 *   Traslado                       $ 150    <- solo si hay traslado
 *   Servicio Exonero (10 %)        $ 150
 *   IVA 22 %                       $ 363
 *   ----------------------------------
 *   Total al aprobarse           $ 2.013
 *   [       Confirmar reserva       ]
 *
 * TODOS los importes son los de POST /clases/cotizar tal cual llegan: aca no
 * se suma ni se multiplica nada, pesos() solo les da formato. Los porcentajes
 * tambien vienen de ahi y no estan escritos en el codigo: si cambia el IVA,
 * se cambia en la base y nada mas.
 *
 * Una diferencia con el mockup, a proposito: ahi "Subtotal" va despues del
 * servicio (clase + servicio, antes del IVA). El backend no devuelve esa suma,
 * y hacerla aca seria justo la cuenta de plata que no hay que duplicar. Asi
 * que "Subtotal" es el del backend: precio por hora por horas.
 *
 * El boton es type="submit": el <form> que lo envuelve esta en Checkout.jsx.
 */

import { Link } from 'react-router-dom'

import Alerta from '../../componentes/Alerta.jsx'
import { pesos } from '../../utiles/formato.js'

// El signo de multiplicar de "1,5 h x $ 900".
const POR = '×'

/** "22.00" -> "22 %". Es solo formato: el numero viene del backend. */
function porcentaje(valor) {
  return `${Number(valor).toLocaleString('es-UY', { maximumFractionDigits: 2 })} %`
}

/** "1.50" -> "1,5". */
function decimal(valor) {
  return Number(valor).toLocaleString('es-UY', { maximumFractionDigits: 2 })
}

export default function Resumen({
  cotizacion,     // lo que devolvio POST /clases/cotizar
  conTraslado,
  nombreProfe,
  textoMedio,     // "Visa •••• 4218", o "la tarjeta nueva"
  error,          // el texto del error al confirmar, o null
  extraError,     // algo para mostrar adentro del error (un enlace), o null
  puedeConfirmar,
  enviando,
  volverA,        // a donde llevan "Cancelar" (el perfil del profe)
}) {
  return (
    <aside className="checkout-resumen" aria-labelledby="resumen-titulo">
      <h4 id="resumen-titulo">Resumen</h4>

      {/* Una lista de definiciones (dt = el concepto, dd = el importe): es la
          etiqueta de HTML para pares "nombre: valor". */}
      <dl className="resumen-lineas">
        <div>
          <dt>
            Subtotal
            <span className="resumen-detalle">
              {decimal(cotizacion.horas)} h {POR} {pesos(cotizacion.precio_hora)}
            </span>
          </dt>
          <dd>{pesos(cotizacion.subtotal)}</dd>
        </div>
        {conTraslado && (
          <div>
            <dt>Traslado</dt>
            <dd>{pesos(cotizacion.costo_traslado)}</dd>
          </div>
        )}
        <div>
          <dt>Servicio Exonero ({porcentaje(cotizacion.pct_comision)})</dt>
          <dd>{pesos(cotizacion.comision)}</dd>
        </div>
        <div>
          <dt>IVA {porcentaje(cotizacion.pct_iva)}</dt>
          <dd>{pesos(cotizacion.impuesto)}</dd>
        </div>
      </dl>

      <div className="resumen-total">
        <span>Total al aprobarse</span>
        <span className="resumen-total-importe">{pesos(cotizacion.total)}</span>
      </div>
      <p className="texto-chico resumen-aviso">
        Se debita de {textoMedio} cuando {nombreProfe} apruebe la reserva.
      </p>

      {/* Un solo hijo, y null si no hay error: Alerta no se dibuja sin hijos
          (con dos hijos sueltos, children seria una lista y siempre se veria). */}
      <Alerta tipo="error">
        {error && (
          <>
            {error} {extraError}
          </>
        )}
      </Alerta>

      {/* Se deshabilita mientras se envia: sin doble clic no hay doble reserva. */}
      <button type="submit" className="btn btn-primary btn-block resumen-confirmar" disabled={!puedeConfirmar || enviando}>
        {enviando ? 'Enviando la reserva...' : 'Confirmar reserva'}
      </button>
      <Link to={volverA} className="resumen-cancelar">
        Cancelar
      </Link>
    </aside>
  )
}
