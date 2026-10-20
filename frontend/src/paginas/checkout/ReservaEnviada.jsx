/**
 * El cartel "Reserva enviada" del checkout (1g). Aparece encima de todo
 * cuando POST /api/clases salio bien.
 *
 *            ( reloj )
 *         Reserva enviada
 *   Queda pendiente de aprobacion de Lucia. Cuando la apruebe
 *   se debitan $ 2.013 de Visa •••• 4218.
 *   +-----------------------------------+
 *   | Matematica con Lucia Fernandez    |
 *   | martes 21 de octubre, 18:00       |
 *   | Clase #42 · pendiente             |
 *   +-----------------------------------+
 *   [ Ver mis clases ]  [ Ir al inicio ]
 *
 * Es un dialogo modal hecho a mano, y por eso se ocupa de la accesibilidad:
 *   - role="dialog" + aria-modal: el lector de pantalla sabe que es un cartel
 *     encima de la pagina y que lo de atras no cuenta.
 *   - aria-labelledby / aria-describedby: al abrirse lee el titulo y el texto.
 *   - el foco va al primer boton apenas aparece, y Tab da la vuelta entre
 *     los dos botones sin escaparse a la pagina de atras.
 *   - la pagina de atras queda "inert" (Checkout.jsx): ni el teclado ni el
 *     lector de pantalla pueden entrar ahi mientras el cartel esta abierto.
 * No se cierra con Escape a proposito: la reserva ya esta hecha y volver al
 * formulario de pago no tiene sentido. Los dos botones son la salida.
 */

import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'

import { SEPARADOR, diaYHora, pesos } from '../../utiles/formato.js'
import { nombreTarjeta } from '../../utiles/tarjetas.js'

export default function ReservaEnviada({ clase, tarjeta, profesor, materia, inicio }) {
  const primerBoton = useRef(null)

  // Al aparecer, el foco salta al cartel. Sin esto quedaria en el boton de
  // confirmar, que esta atras y tapado.
  useEffect(() => {
    primerBoton.current?.focus()
  }, [])

  // Tab en el ultimo boton vuelve al primero, y Shift+Tab en el primero (o
  // en el cartel mismo, si se hizo clic en su texto) va al ultimo: el foco
  // no sale del cartel.
  function atraparFoco(evento) {
    if (evento.key !== 'Tab') return
    const botones = evento.currentTarget.querySelectorAll('a[href], button')
    const primero = botones[0]
    const ultimo = botones[botones.length - 1]
    const actual = document.activeElement
    if (evento.shiftKey && (actual === primero || actual === evento.currentTarget)) {
      evento.preventDefault()
      ultimo.focus()
    } else if (!evento.shiftKey && actual === ultimo) {
      evento.preventDefault()
      primero.focus()
    }
  }

  // Un clic en el velo de alrededor no le saca el foco al cartel (sin esto,
  // el foco pasaria a la pagina de atras y Tab seguiria por ahi).
  function noSoltarFoco(evento) {
    if (evento.target === evento.currentTarget) evento.preventDefault()
  }

  return (
    <div className="exito-fondo" onMouseDown={noSoltarFoco}>
      {/* tabIndex={-1}: el cartel puede tener el foco (al hacer clic en su
          texto) sin entrar en el recorrido de Tab. */}
      <div
        className="exito"
        role="dialog"
        aria-modal="true"
        aria-labelledby="exito-titulo"
        aria-describedby="exito-texto"
        tabIndex={-1}
        onKeyDown={atraparFoco}
      >
        {/* Un reloj que gira: la reserva esta esperando al profe. Es solo
            decoracion, el texto ya lo dice. */}
        <div className="exito-icono" aria-hidden="true">
          <svg viewBox="0 0 52 52">
            <circle className="exito-icono-pista" cx="26" cy="26" r="17" />
            <circle className="exito-icono-arco" cx="26" cy="26" r="17" />
            <path className="exito-icono-agujas" d="M26 17 L26 27 L33 31" />
          </svg>
        </div>

        <h3 id="exito-titulo" className="exito-titulo">Reserva enviada</h3>
        <p id="exito-texto" className="exito-texto">
          Queda pendiente de aprobacion de {profesor.nombre}. Cuando la apruebe se debitan{' '}
          {pesos(clase.total)} de {nombreTarjeta(tarjeta)}.
        </p>

        <div className="exito-detalle">
          {materia} con {profesor.nombre} {profesor.apellido}
          <br />
          {diaYHora(inicio)}
          <br />
          Clase #{clase.id}
          {SEPARADOR}
          {clase.estado}
        </div>

        <div className="exito-botones">
          {/* Link de react-router acepta ref: llega al <a> de adentro. */}
          <Link ref={primerBoton} to="/mis-clases" className="btn btn-primary">
            Ver mis clases
          </Link>
          <Link to="/inicio" className="btn btn-secondary">
            Ir al inicio
          </Link>
        </div>
      </div>
    </div>
  )
}
