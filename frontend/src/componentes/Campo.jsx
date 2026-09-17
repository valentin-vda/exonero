/**
 * Un campo de formulario: etiqueta + input + texto de ayuda o de error.
 *
 * Existe para no repetir el mismo bloque de cuatro elementos en cada campo de
 * cada formulario, y para que la accesibilidad quede bien UNA vez:
 *   - el <label> apunta al input con htmlFor/id
 *   - el error se anuncia con aria-describedby y aria-invalid
 *
 * Uso:
 *   <Campo id="correo" etiqueta="Correo" tipo="email"
 *          valor={correo} alCambiar={setCorreo} error={errores.correo} />
 */

export default function Campo({
  id,
  etiqueta,
  tipo = 'text',
  valor,
  alCambiar,
  error = null,
  ayuda = null,
  requerido = false,
  autoComplete,
  placeholder,
  children,       // para meter algo adentro del campo, como el ojo de la clave
  ...resto
}) {
  const idAyuda = `${id}-ayuda`

  return (
    <div className="field">
      <label htmlFor={id}>
        {etiqueta}
        {requerido && <span aria-hidden="true"> *</span>}
      </label>

      <div style={{ position: 'relative' }}>
        <input
          id={id}
          name={id}
          type={tipo}
          className={`input${error ? ' input-error' : ''}`}
          value={valor}
          onChange={(e) => alCambiar(e.target.value)}
          autoComplete={autoComplete}
          placeholder={placeholder}
          // Le avisa al lector de pantalla que el campo esta mal.
          aria-invalid={error ? 'true' : undefined}
          // Y le dice donde esta el texto que explica por que.
          aria-describedby={error || ayuda ? idAyuda : undefined}
          {...resto}
        />
        {children}
      </div>

      {(error || ayuda) && (
        <span id={idAyuda} className={`field-hint${error ? ' field-hint-error' : ''}`}>
          {error || ayuda}
        </span>
      )}
    </div>
  )
}
