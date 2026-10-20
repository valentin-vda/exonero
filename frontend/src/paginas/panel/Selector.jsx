/**
 * El control segmentado de los bloques del panel: Mes / Trimestre / Anio,
 * Semana / Mes / Anio, 10 semanas / Mes / Anio.
 *
 * Son radios de verdad escondidos adentro de labels (ver .seg-opt en
 * componentes.css), igual que la modalidad de 1j. Por ser radios con el mismo
 * `name`, se recorren con las flechas del teclado y el lector de pantalla
 * anuncia "Mes, boton de opcion, 1 de 3, seleccionado".
 *
 * Como un input controlado: el valor elegido lo guarda la pantalla (`valor`)
 * y este componente solo le avisa cuando cambia (`alCambiar`).
 */

export default function Selector({ nombre, etiqueta, opciones, valor, alCambiar }) {
  return (
    <div className="seg" role="radiogroup" aria-label={etiqueta}>
      {opciones.map((opcion) => (
        <label key={opcion.valor} className="seg-opt">
          <input
            type="radio"
            name={nombre}
            checked={valor === opcion.valor}
            onChange={() => alCambiar(opcion.valor)}
          />
          {opcion.texto}
        </label>
      ))}
    </div>
  )
}
