/**
 * Un desplegable de formulario: etiqueta + <select> + texto de ayuda o error.
 *
 * Es el hermano de Campo.jsx, pero con un <select> en vez de un <input>. Lo
 * usan los perfiles para elegir barrio, centro, etapa, duraciones...
 *
 * Uso:
 *   <CampoSelect
 *     id="barrio"
 *     etiqueta="Barrio"
 *     valor={campos.barrioId}
 *     alCambiar={(v) => cambiar('barrioId', v)}
 *     opciones={[{ valor: 1, texto: 'Cordon' }, { valor: 2, texto: 'Centro' }]}
 *   />
 *
 * OJO: un <select> siempre devuelve TEXTO. Si las opciones son numeros
 * (ids), lo que llega a alCambiar es "1", no 1. Quien lo usa lo convierte con
 * Number(...) si hace falta.
 */

export default function CampoSelect({
  id,
  etiqueta,
  valor,
  alCambiar,
  opciones,           // [{ valor, texto }]
  vacio = 'Elegir...', // el texto de la opcion "nada elegido"; null para no mostrarla
  error = null,
  ayuda = null,
  disabled = false,
}) {
  const idAyuda = `${id}-ayuda`

  return (
    <div className="field">
      <label htmlFor={id}>{etiqueta}</label>
      <select
        id={id}
        className={`input${error ? ' input-error' : ''}`}
        // null o undefined no son valores validos para un <select>: se usa ''
        // (que es la opcion "vacio").
        value={valor ?? ''}
        onChange={(e) => alCambiar(e.target.value)}
        disabled={disabled}
        aria-invalid={error ? 'true' : undefined}
        aria-describedby={error || ayuda ? idAyuda : undefined}
      >
        {vacio !== null && <option value="">{vacio}</option>}
        {/* map() recorre la lista y devuelve un <option> por elemento.
            El key le dice a React cual es cual (ver la documentacion). */}
        {opciones.map((opcion) => (
          <option key={opcion.valor} value={opcion.valor}>
            {opcion.texto}
          </option>
        ))}
      </select>

      {(error || ayuda) && (
        <span id={idAyuda} className={`field-hint${error ? ' field-hint-error' : ''}`}>
          {error || ayuda}
        </span>
      )}
    </div>
  )
}
