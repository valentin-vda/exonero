/**
 * Campo de contrasena con el boton de mostrar/ocultar.
 *
 * Es un Campo normal con un boton encima que alterna el type entre "password"
 * y "text". Poder ver lo que uno escribio baja mucho los errores de tipeo,
 * sobre todo en el registro.
 */

import { useState } from 'react'

import Campo from './Campo.jsx'

export default function CampoClave({ id, etiqueta, valor, alCambiar, error, ayuda, autoComplete }) {
  const [visible, setVisible] = useState(false)

  return (
    <div className="auth-clave">
      <Campo
        id={id}
        etiqueta={etiqueta}
        tipo={visible ? 'text' : 'password'}
        valor={valor}
        alCambiar={alCambiar}
        error={error}
        ayuda={ayuda}
        requerido
        autoComplete={autoComplete}
      >
        <button
          type="button"
          className="auth-ver-clave"
          onClick={() => setVisible((v) => !v)}
          // El boton no es parte del formulario, es una ayuda visual: se saca
          // del recorrido del Tab para no estorbar al completar los campos.
          tabIndex={-1}
          aria-label={visible ? 'Ocultar contrasena' : 'Mostrar contrasena'}
        >
          {visible ? 'Ocultar' : 'Mostrar'}
        </button>
      </Campo>
    </div>
  )
}
