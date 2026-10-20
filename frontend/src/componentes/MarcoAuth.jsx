/**
 * El marco de dos columnas que comparten login, registro y recuperar clave.
 *
 * Izquierda: el panel terracota con la marca y para que sirve Exonero.
 * Derecha: lo que le pase cada pantalla como children (el formulario).
 *
 * Esta separado en su propio componente para que las tres pantallas se vean
 * exactamente iguales sin copiar y pegar el layout tres veces.
 */

export default function MarcoAuth({ children, ancho = false }) {
  return (
    <div className="auth">
      {/* --- Panel izquierdo --- */}
      <aside className="auth-panel">
        <div className="auth-marca">Exonero</div>

        {/* Los textos son los de la pantalla "0 Ingreso" del mockup. */}
        <div className="auth-lema">
          <h1>Clases particulares con profes de tu barrio</h1>
          <p>
            Busca por materia y zona, elegi un horario y paga cuando el profe
            apruebe la clase.
          </p>
        </div>
      </aside>

      {/* --- Columna derecha: el formulario --- */}
      <main className="auth-form-col">
        <div className={`auth-caja${ancho ? ' auth-caja-ancha' : ''}`}>{children}</div>
      </main>
    </div>
  )
}
