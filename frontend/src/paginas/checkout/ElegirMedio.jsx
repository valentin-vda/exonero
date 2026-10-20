/**
 * El panel "Medio de pago" del checkout (1g).
 *
 *   ( ) [Visa] Visa •••• 4218             <- una fila por tarjeta guardada
 *              Vence 09/29 · MARTINA SILVA
 *   (o) [ +  ] Agregar tarjeta nueva       <- siempre al final
 *       +--------------------------------+
 *       | FormularioTarjeta              |  <- solo si eligio la nueva
 *       | [ ] Guardar esta tarjeta ...   |
 *       +--------------------------------+
 *
 * Son radios de verdad (<input type="radio"> adentro de un <label>): se
 * eligen con las flechas del teclado y el lector de pantalla dice "1 de 3".
 * Lo que se ve es el label entero, y pagos.css lo pinta cuando su radio esta
 * elegido (:has(input:checked)).
 *
 * Una tarjeta guardada que ya vencio se muestra, pero no se puede elegir: el
 * backend la rechazaria con 402 tarjeta_vencida.
 *
 * No guarda estado: la eleccion, lo escrito y el "guardar" viven en
 * Checkout.jsx, que es quien los usa al confirmar.
 */

import FormularioTarjeta from '../../componentes/FormularioTarjeta.jsx'
import { unir } from '../../utiles/formato.js'
import { NUEVA, marcaCorta, nombreTarjeta, tarjetaVencida } from '../../utiles/tarjetas.js'

export default function ElegirMedio({
  tarjetas,          // GET /api/pagos/tarjetas
  medio,             // el id de la tarjeta elegida, o NUEVA
  alElegir,
  nueva,             // lo escrito en el formulario de la tarjeta nueva
  alCambiarNueva,
  errores,           // los errores de ese formulario
  guardar,           // el checkbox "Guardar esta tarjeta en mi perfil"
  alCambiarGuardar,
}) {
  return (
    <section className="panel" aria-labelledby="medio-titulo">
      <h4 id="medio-titulo" style={{ marginBottom: '4px' }}>Medio de pago</h4>
      <p className="panel-ayuda" style={{ marginTop: 0 }}>
        Elegi una de tus tarjetas guardadas o agrega una nueva. No se debita nada hasta que la
        reserva sea aprobada.
      </p>

      {/* fieldset + legend agrupan los radios: el lector de pantalla lee la
          pregunta antes de las opciones. La legend esta escondida porque el
          titulo de arriba ya lo dice a la vista. */}
      <fieldset className="medios">
        <legend className="oculto-visual">Con que tarjeta vas a pagar</legend>

        {tarjetas.map((tarjeta) => {
          const vencida = tarjetaVencida(tarjeta)
          return (
            <label key={tarjeta.id} className="medio">
              <input
                type="radio"
                name="medio"
                checked={medio === tarjeta.id}
                onChange={() => alElegir(tarjeta.id)}
                disabled={vencida}
              />
              <span className="marca-tarjeta" aria-hidden="true">{marcaCorta(tarjeta.marca)}</span>
              <span className="medio-datos">
                <span className="medio-nombre">{nombreTarjeta(tarjeta)}</span>
                <span className="medio-meta">{unir([`Vence ${tarjeta.vence}`, tarjeta.titular])}</span>
              </span>
              {vencida && <span className="tag tag-neutral medio-tag">Vencida</span>}
            </label>
          )
        })}

        <label className="medio">
          <input type="radio" name="medio" checked={medio === NUEVA} onChange={() => alElegir(NUEVA)} />
          <span className="marca-tarjeta marca-tarjeta-mas" aria-hidden="true">+</span>
          <span className="medio-datos">
            <span className="medio-nombre">Agregar tarjeta nueva</span>
            <span className="medio-meta">Se puede guardar para las proximas reservas</span>
          </span>
        </label>
      </fieldset>

      {medio === NUEVA && (
        <div className="medio-nueva">
          <FormularioTarjeta campos={nueva} alCambiar={alCambiarNueva} errores={errores} />
          {/* Sin marcar, la tarjeta se usa para esta reserva y despues se da
              de baja (ver confirmar() en Checkout.jsx). */}
          <label className="casilla">
            <input type="checkbox" checked={guardar} onChange={(e) => alCambiarGuardar(e.target.checked)} />
            Guardar esta tarjeta en mi perfil
          </label>
        </div>
      )}
    </section>
  )
}
