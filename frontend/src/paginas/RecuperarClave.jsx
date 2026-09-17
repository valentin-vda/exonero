/**
 * Recuperar contrasena, en dos pasos dentro de la misma pantalla.
 *
 * Paso 1: se pide el correo -> POST /api/auth/recuperar
 * Paso 2: con el codigo, se fija la clave nueva -> POST /api/auth/restablecer
 *
 * IMPORTANTE para probar: no hay correo saliente (quedo fuera de alcance).
 * El backend IMPRIME EL CODIGO EN SU CONSOLA. Hay que ir a la terminal donde
 * corre uvicorn, copiarlo de ahi y pegarlo en el paso 2.
 */

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { pedirCodigo, restablecerClave } from '../api/auth.js'
import { mensajeDeError } from '../api/mensajes.js'
import Alerta from '../componentes/Alerta.jsx'
import Campo from '../componentes/Campo.jsx'
import CampoClave from '../componentes/CampoClave.jsx'
import MarcoAuth from '../componentes/MarcoAuth.jsx'
import {
  validarClave,
  validarCorreo,
  validarFormulario,
  validarRepetirClave,
} from '../utiles/validaciones.js'

export default function RecuperarClave() {
  const navegar = useNavigate()

  const [paso, setPaso] = useState(1)
  const [correo, setCorreo] = useState('')
  const [codigo, setCodigo] = useState('')
  const [clave, setClave] = useState('')
  const [repetir, setRepetir] = useState('')
  const [errores, setErrores] = useState({})
  const [errorGeneral, setErrorGeneral] = useState(null)
  const [enviando, setEnviando] = useState(false)

  async function enviarPaso1(evento) {
    evento.preventDefault()
    const { errores: nuevos, hayErrores } = validarFormulario({
      correo: () => validarCorreo(correo),
    })
    setErrores(nuevos)
    setErrorGeneral(null)
    if (hayErrores) return

    setEnviando(true)
    try {
      await pedirCodigo(correo.trim())
      // El backend responde ok exista o no el correo, para no revelar que
      // cuentas estan registradas. Por eso siempre pasamos al paso 2.
      setPaso(2)
    } catch (error) {
      setErrorGeneral(mensajeDeError(error.codigo))
    } finally {
      setEnviando(false)
    }
  }

  async function enviarPaso2(evento) {
    evento.preventDefault()
    const { errores: nuevos, hayErrores } = validarFormulario({
      codigo: () => (codigo.trim() ? null : 'Escribi el codigo.'),
      clave: () => validarClave(clave),
      repetir: () => validarRepetirClave(clave, repetir),
    })
    setErrores(nuevos)
    setErrorGeneral(null)
    if (hayErrores) return

    setEnviando(true)
    try {
      await restablecerClave(correo.trim(), codigo.trim(), clave)
      navegar('/login', { replace: true })
    } catch (error) {
      setErrorGeneral(mensajeDeError(error.codigo))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <MarcoAuth>
      <h2 className="auth-titulo">Recuperar contrasena</h2>

      {paso === 1 ? (
        <>
          <p className="auth-bajada">
            Escribi tu correo y te mandamos un codigo para volver a entrar.
          </p>
          <Alerta tipo="error">{errorGeneral}</Alerta>
          <form onSubmit={enviarPaso1} noValidate>
            <Campo
              id="correo"
              etiqueta="Correo"
              tipo="email"
              valor={correo}
              alCambiar={setCorreo}
              error={errores.correo}
              requerido
              autoComplete="email"
            />
            <button type="submit" className="btn btn-primary btn-block" disabled={enviando}>
              {enviando ? 'Enviando...' : 'Pedir codigo'}
            </button>
          </form>
        </>
      ) : (
        <>
          <p className="auth-bajada">
            Mientras no haya envio de correos, el codigo se imprime en la
            consola del backend. Copialo de ahi.
          </p>
          <Alerta tipo="error">{errorGeneral}</Alerta>
          <form onSubmit={enviarPaso2} noValidate>
            <Campo
              id="codigo"
              etiqueta="Codigo"
              valor={codigo}
              alCambiar={setCodigo}
              error={errores.codigo}
              requerido
              inputMode="numeric"
              placeholder="123456"
            />
            <CampoClave
              id="clave"
              etiqueta="Contrasena nueva"
              valor={clave}
              alCambiar={setClave}
              error={errores.clave}
              autoComplete="new-password"
            />
            <CampoClave
              id="repetir"
              etiqueta="Repetir contrasena"
              valor={repetir}
              alCambiar={setRepetir}
              error={errores.repetir}
              autoComplete="new-password"
            />
            <button type="submit" className="btn btn-primary btn-block" disabled={enviando}>
              {enviando ? 'Guardando...' : 'Cambiar contrasena'}
            </button>
          </form>
        </>
      )}

      <p className="auth-pie">
        <Link to="/login">Volver a entrar</Link>
      </p>
    </MarcoAuth>
  )
}
