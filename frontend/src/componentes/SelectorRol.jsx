/**
 * Las dos tarjetas de "Quiero aprender" / "Quiero ensenar" del registro.
 *
 * Por que dos tarjetas grandes y no un desplegable: la eleccion del rol es
 * DEFINITIVA. La spec dice que no hay cambio de rol, y quien quiera ser las
 * dos cosas se crea dos cuentas con dos correos. Una decision que no se puede
 * deshacer merece verse, no esconderse en un select.
 *
 * Cada tarjeta es un <button> con aria-pressed, no un div con onClick: asi
 * funciona con teclado y los lectores de pantalla dicen cual esta elegida.
 */

const OPCIONES = [
  {
    valor: 'estudiante',
    titulo: 'Quiero aprender',
    nota: 'Busca profes, reserva clases y llevas tu historial.',
  },
  {
    valor: 'profesor',
    titulo: 'Quiero ensenar',
    nota: 'Publica tu ficha, tu agenda y tus precios. Vos aprobas cada clase.',
  },
]

export default function SelectorRol({ valor, alCambiar }) {
  return (
    <div className="auth-roles" role="group" aria-label="Tipo de cuenta">
      {OPCIONES.map((opcion) => (
        <button
          key={opcion.valor}
          type="button"
          className="auth-rol"
          aria-pressed={valor === opcion.valor}
          onClick={() => alCambiar(opcion.valor)}
        >
          <span className="auth-rol-titulo">{opcion.titulo}</span>
          <span className="auth-rol-nota">{opcion.nota}</span>
        </button>
      ))}
    </div>
  )
}
