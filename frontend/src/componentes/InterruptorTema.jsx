/**
 * El interruptor de modo claro / modo oscuro del menu lateral de los perfiles.
 *
 * Que pasa al tocarlo:
 *   1. PUT /api/usuarios/yo/tema guarda el tema nuevo en la cuenta.
 *   2. refrescar() vuelve a pedir el usuario, que ahora trae el tema nuevo.
 *   3. ContextoAuth ve el cambio y pone <html data-tema="oscuro">.
 *   4. tokens.css redefine los colores para ese atributo, y toda la app cambia.
 *
 * Es un <button role="switch">: asi los lectores de pantalla lo anuncian como
 * un interruptor ("modo oscuro, activado"), y funciona con el teclado.
 */

import { useState } from 'react'

import { cambiarTema } from '../api/auth.js'
import { useAuth } from '../auth/ContextoAuth.jsx'

export default function InterruptorTema() {
  const { usuario, refrescar } = useAuth()
  const [guardando, setGuardando] = useState(false)

  const oscuro = usuario?.tema === 'oscuro'

  async function alternar() {
    setGuardando(true)
    try {
      await cambiarTema(oscuro ? 'claro' : 'oscuro')
      await refrescar()
    } catch {
      // Si falla (sin conexion, por ejemplo) el tema queda como estaba. No
      // vale la pena un cartel de error por esto.
    } finally {
      setGuardando(false)
    }
  }

  return (
    <button
      type="button"
      role="switch"
      aria-checked={oscuro}
      className="interruptor"
      onClick={alternar}
      disabled={guardando}
    >
      {oscuro ? 'Modo oscuro' : 'Modo claro'}
      {/* La pista y la perilla son puro dibujo: el CSS mueve la perilla segun
          aria-checked (ver .interruptor en perfil.css). */}
      <span className="interruptor-pista" aria-hidden="true">
        <span className="interruptor-perilla" />
      </span>
    </button>
  )
}
