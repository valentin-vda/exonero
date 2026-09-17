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

        <div className="auth-lema">
          <h1>Clases particulares, cerca tuyo.</h1>
          <p>
            Encontra profes de tu materia en tu barrio, mira su agenda real y
            reserva la clase. Sin llamadas, sin vueltas.
          </p>
        </div>

        {/* Decorativo: describe la propuesta en tres puntos */}
        <ul className="auth-puntos">
          <li className="auth-punto">
            <span className="auth-punto-icono" aria-hidden="true">1</span>
            Busca por materia, barrio, precio y horario
          </li>
          <li className="auth-punto">
            <span className="auth-punto-icono" aria-hidden="true">2</span>
            Elegi un hueco libre de su agenda
          </li>
          <li className="auth-punto">
            <span className="auth-punto-icono" aria-hidden="true">3</span>
            El profe confirma y listo
          </li>
        </ul>
      </aside>

      {/* --- Columna derecha: el formulario --- */}
      <main className="auth-form-col">
        <div className={`auth-caja${ancho ? ' auth-caja-ancha' : ''}`}>{children}</div>
      </main>
    </div>
  )
}
