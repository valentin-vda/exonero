/**
 * El marco de dos columnas que comparten login, registro y recuperar clave.
 *
 * Izquierda: el panel azul oscuro con el logo completo arriba, el buho
 * gigante en el centro y para que sirve Exonero abajo.
 * Derecha: lo que le pase cada pantalla como children (el formulario).
 *
 * Esta separado en su propio componente para que las tres pantallas se vean
 * exactamente iguales sin copiar y pegar el layout tres veces.
 */

import buhoAuth from '../assets/buho-auth.png'
import logoExonero from '../assets/logo-exonero.png'

export default function MarcoAuth({ children, ancho = false }) {
  return (
    <div className="auth">
      {/* --- Panel izquierdo --- */}
      <aside className="auth-panel">
        {/* El logo completo: el buho y la palabra. El alt va vacio porque
            "Exonero" ya esta escrito al lado. */}
        <div className="auth-marca">
          <img className="auth-marca-logo" src={logoExonero} alt="" />
          <span>Exonero</span>
        </div>

        {/* El buho gigante, parado sobre la columna. Es decoracion: el lector
            de pantalla lo saltea. */}
        <img className="auth-buho" src={buhoAuth} alt="" aria-hidden="true" />

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
