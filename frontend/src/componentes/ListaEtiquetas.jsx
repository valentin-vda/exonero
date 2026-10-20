/**
 * Una lista de etiquetas que se pueden quitar, con un desplegable para agregar.
 *
 *   [Matematica x] [Fisica x] [+ Agregar materia v]
 *
 * La usa 1j para las materias, los idiomas y los barrios de traslado. Es la
 * misma pieza tres veces, con distintas opciones.
 *
 * Uso:
 *   <ListaEtiquetas
 *     etiqueta="Materias que dictas"
 *     seleccion={[1, 2]}                           // los ids elegidos
 *     opciones={[{ id: 1, nombre: 'Matematica' }, ...]}  // del catalogo
 *     alCambiar={(nuevaLista) => ...}
 *     textoAgregar="+ Agregar materia"
 *   />
 *
 * `nombres` es un plan B: si los catalogos no cargaron (P2 todavia no hizo el
 * endpoint), no hay `opciones`, pero igual se pueden mostrar los nombres de
 * lo que ya estaba elegido, que vienen en la ficha. En ese caso no se puede
 * agregar nada, solo quitar.
 *
 * Este componente NO guarda nada: avisa con alCambiar y el que lo usa decide.
 * A eso se le dice un componente "controlado", igual que un <input value=...>.
 */

import { CRUZ } from '../utiles/formato.js'

export default function ListaEtiquetas({
  id,
  etiqueta,
  seleccion,
  opciones = [],
  nombres = {},
  alCambiar,
  textoAgregar = '+ Agregar',
}) {
  // El nombre de un id: primero del catalogo, si no, del plan B.
  function nombreDe(idElegido) {
    const opcion = opciones.find((o) => o.id === idElegido)
    return opcion ? opcion.nombre : nombres[idElegido] || `#${idElegido}`
  }

  // Lo que todavia se puede agregar: las opciones que no estan elegidas.
  const disponibles = opciones.filter((o) => !seleccion.includes(o.id))

  function quitar(idQuitado) {
    // filter devuelve una lista NUEVA sin ese id. En React no se modifica la
    // lista vieja (nada de .splice): se arma otra y se avisa.
    alCambiar(seleccion.filter((x) => x !== idQuitado))
  }

  function agregar(texto) {
    if (!texto) return
    // [...lista, nuevo] = una lista nueva con todo lo de antes mas el nuevo.
    alCambiar([...seleccion, Number(texto)])
  }

  return (
    <div className="field">
      <label htmlFor={id}>{etiqueta}</label>
      <div className="etiquetas">
        {seleccion.map((idElegido) => (
          <button
            key={idElegido}
            type="button"
            className="tag tag-accent tag-boton"
            onClick={() => quitar(idElegido)}
            aria-label={`Quitar ${nombreDe(idElegido)}`}
          >
            {nombreDe(idElegido)} {CRUZ}
          </button>
        ))}

        {disponibles.length > 0 && (
          // value="" siempre: el desplegable vuelve a mostrar "+ Agregar"
          // despues de cada eleccion, porque lo elegido ya paso a ser etiqueta.
          <select
            id={id}
            className="tag tag-outline tag-boton"
            value=""
            onChange={(e) => agregar(e.target.value)}
          >
            <option value="">{textoAgregar}</option>
            {disponibles.map((o) => (
              <option key={o.id} value={o.id}>
                {o.nombre}
              </option>
            ))}
          </select>
        )}

        {seleccion.length === 0 && disponibles.length === 0 && (
          <span className="text-muted" style={{ fontSize: '13px' }}>
            Nada elegido todavia.
          </span>
        )}
      </div>
    </div>
  )
}
