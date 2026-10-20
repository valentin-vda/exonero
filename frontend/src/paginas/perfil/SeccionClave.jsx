/**
 * La pestania "Contrasena" de los dos perfiles (1e y 1j).
 *
 * Dos tarjetas:
 *   1. Cambiar la contrasena: la actual, la nueva y repetir la nueva.
 *      PUT /api/usuarios/yo/clave. Pide la actual para que alguien que
 *      encuentre la sesion abierta no pueda quedarse con la cuenta.
 *   2. Dar de baja la cuenta: DELETE /api/usuarios/yo, en dos pasos (primero
 *      se pide confirmar) porque no se puede deshacer desde la app.
 *
 * El mockup tiene un boton "Enviarme un enlace por correo": no hay correo
 * saliente en este proyecto, asi que en su lugar se explica como usar
 * "Olvide mi contrasena" del login, que es lo que existe.
 */

import { useState } from 'react'

import { cambiarClave, darmeDeBaja } from '../../api/auth.js'
import { mensajeDeError } from '../../api/mensajes.js'
import { useAuth } from '../../auth/ContextoAuth.jsx'
import Alerta from '../../componentes/Alerta.jsx'
import CampoClave from '../../componentes/CampoClave.jsx'
import { validarClave, validarFormulario, validarRepetirClave } from '../../utiles/validaciones.js'

// Los valores de un formulario vacio. Se usa al empezar y despues de guardar.
const VACIO = { actual: '', nueva: '', repetir: '' }

export default function SeccionClave() {
  const { usuario, salir } = useAuth()

  // --- Estado del formulario de la clave ---
  const [campos, setCampos] = useState(VACIO)
  const [errores, setErrores] = useState({})
  const [mensaje, setMensaje] = useState(null) // { tipo: 'ok' | 'error', texto }
  const [guardando, setGuardando] = useState(false)

  // --- Estado de la baja ---
  const [confirmandoBaja, setConfirmandoBaja] = useState(false)
  const [errorBaja, setErrorBaja] = useState(null)

  // Devuelve la funcion que actualiza UN campo. cambiar('nueva') es una
  // funcion que recibe el texto y lo guarda en campos.nueva.
  function cambiar(campo) {
    return (valor) => setCampos((previos) => ({ ...previos, [campo]: valor }))
  }

  async function guardarClave(evento) {
    evento.preventDefault()

    const { errores: nuevos, hayErrores } = validarFormulario({
      actual: () => (campos.actual ? null : 'Escribi tu contrasena actual.'),
      nueva: () => validarClave(campos.nueva),
      repetir: () => validarRepetirClave(campos.nueva, campos.repetir),
    })
    setErrores(nuevos)
    setMensaje(null)
    if (hayErrores) return

    setGuardando(true)
    try {
      await cambiarClave(campos.actual, campos.nueva)
      setCampos(VACIO)
      setMensaje({ tipo: 'ok', texto: 'Listo, tu contrasena cambio.' })
    } catch (error) {
      setMensaje({ tipo: 'error', texto: mensajeDeError(error.codigo) })
    } finally {
      setGuardando(false)
    }
  }

  async function confirmarBaja() {
    setErrorBaja(null)
    try {
      await darmeDeBaja()
      // La cuenta ya no existe para el backend: el token no sirve mas.
      // salir() lo borra y RutaProtegida manda al login.
      salir()
    } catch (error) {
      setErrorBaja(mensajeDeError(error.codigo))
    }
  }

  return (
    <>
      {/* --- Cambiar la contrasena --- */}
      <section className="panel panel-angosto">
        <h4 style={{ marginBottom: '6px' }}>Cambiar la contrasena</h4>
        <p className="panel-ayuda" style={{ marginTop: 0 }}>
          Usa al menos 8 caracteres. Si no te acordas de la actual, cerra la
          sesion y entra con &quot;Olvide mi contrasena&quot;.
        </p>

        <Alerta tipo={mensaje?.tipo}>{mensaje?.texto}</Alerta>

        <form onSubmit={guardarClave} noValidate>
          <CampoClave
            id="clave-actual"
            etiqueta="Contrasena actual"
            valor={campos.actual}
            alCambiar={cambiar('actual')}
            error={errores.actual}
            autoComplete="current-password"
          />
          <CampoClave
            id="clave-nueva"
            etiqueta="Contrasena nueva"
            valor={campos.nueva}
            alCambiar={cambiar('nueva')}
            error={errores.nueva}
            autoComplete="new-password"
          />
          <CampoClave
            id="clave-repetir"
            etiqueta="Repetir contrasena nueva"
            valor={campos.repetir}
            alCambiar={cambiar('repetir')}
            error={errores.repetir}
            autoComplete="new-password"
          />
          <div className="botonera">
            <button type="submit" className="btn btn-primary" disabled={guardando}>
              {guardando ? 'Guardando...' : 'Guardar contrasena'}
            </button>
          </div>
        </form>
      </section>

      {/* --- Dar de baja --- */}
      <section className="panel panel-angosto">
        <h4 style={{ marginBottom: '6px' }}>Dar de baja la cuenta</h4>
        <p className="panel-ayuda" style={{ marginTop: 0 }}>
          Tu cuenta queda desactivada y no vas a poder volver a entrar con{' '}
          {usuario.correo}. Las clases que ya tuviste se conservan para la otra persona.
          {usuario.rol === 'profesor' && ' Tu ficha deja de aparecer en la busqueda.'}
        </p>

        <Alerta tipo="error">{errorBaja}</Alerta>

        {/* Dos pasos: el primer clic solo muestra la confirmacion. */}
        {!confirmandoBaja ? (
          <button type="button" className="btn btn-secondary" onClick={() => setConfirmandoBaja(true)}>
            Dar de baja mi cuenta
          </button>
        ) : (
          <div className="botonera">
            <button type="button" className="btn btn-primary" onClick={confirmarBaja}>
              Si, dar de baja
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => setConfirmandoBaja(false)}>
              Cancelar
            </button>
          </div>
        )}
      </section>
    </>
  )
}
