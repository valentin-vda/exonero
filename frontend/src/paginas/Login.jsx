/**
 * Pantalla de login.
 *
 * No existe en el prototipo de mockups (la spec la marca como "sin pantalla en
 * el prototipo"), asi que esta disenada siguiendo el mismo sistema: fondo
 * crema, titulos en Caprasimo, controles en pildora, acento terracota.
 *
 * Que hace, paso a paso:
 *   1. El usuario escribe correo y clave.
 *   2. Al enviar, valida en el cliente (para avisar rapido).
 *   3. Llama a entrar() del contexto, que hace POST /api/auth/login, guarda el
 *      token y pide GET /api/usuarios/yo.
 *   4. Si sale bien, lo manda a su tablero segun el rol.
 *   5. Si sale mal, muestra el error arriba del formulario.
 */

import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'

import { mensajeDeError } from '../api/mensajes.js'
import { useAuth } from '../auth/ContextoAuth.jsx'
import Alerta from '../componentes/Alerta.jsx'
import Campo from '../componentes/Campo.jsx'
import CampoClave from '../componentes/CampoClave.jsx'
import MarcoAuth from '../componentes/MarcoAuth.jsx'
import { validarClave, validarCorreo, validarFormulario } from '../utiles/validaciones.js'

export default function Login() {
  const { usuario, entrar } = useAuth()
  const navegar = useNavigate()
  const ubicacion = useLocation()

  const [correo, setCorreo] = useState('')
  const [clave, setClave] = useState('')
  const [errores, setErrores] = useState({})
  const [errorGeneral, setErrorGeneral] = useState(null)
  const [enviando, setEnviando] = useState(false)

  // Si ya hay sesion, no tiene sentido mostrar el login.
  if (usuario) {
    return <Navigate to={usuario.rol === 'profesor' ? '/panel' : '/inicio'} replace />
  }

  async function alEnviar(evento) {
    // Sin esto el navegador recarga la pagina y se pierde todo.
    evento.preventDefault()

    const { errores: nuevos, hayErrores } = validarFormulario({
      correo: () => validarCorreo(correo),
      clave: () => (clave ? null : 'Escribi tu contrasena.'),
    })
    setErrores(nuevos)
    setErrorGeneral(null)
    if (hayErrores) return

    setEnviando(true)
    try {
      const yo = await entrar(correo.trim(), clave)
      // Si venia de una pantalla protegida, volver ahi. Si no, a su tablero.
      const destino =
        ubicacion.state?.desde || (yo.rol === 'profesor' ? '/panel' : '/inicio')
      navegar(destino, { replace: true })
    } catch (error) {
      setErrorGeneral(mensajeDeError(error.codigo))
    } finally {
      // finally y no dentro del try: si falla, el boton se tiene que
      // desbloquear igual.
      setEnviando(false)
    }
  }

  // Los usuarios que crea `python -m app.seeds`. Los botones del recuadro de
  // abajo completan el formulario con uno de ellos, para probar rapido.
  function completarDemo(correoDemo) {
    setCorreo(correoDemo)
    setClave('exonero123')
    setErrores({})
    setErrorGeneral(null)
  }

  return (
    <MarcoAuth>
      {/* Los textos son los de la pantalla "0 Ingreso" del mockup. */}
      <h2 className="auth-titulo">Ingresa a tu cuenta</h2>
      <p className="auth-bajada">Entra con tu correo y contrasena de Exonero.</p>

      <Alerta tipo="error">{errorGeneral}</Alerta>

      {/* noValidate apaga los globitos del navegador: mostramos los nuestros,
          que son consistentes entre navegadores y se leen mejor. */}
      <form onSubmit={alEnviar} noValidate>
        <Campo
          id="correo"
          etiqueta="Correo"
          tipo="email"
          valor={correo}
          alCambiar={setCorreo}
          error={errores.correo}
          requerido
          autoComplete="email"
          placeholder="tunombre@correo.com"
        />

        <CampoClave
          id="clave"
          etiqueta="Contrasena"
          valor={clave}
          alCambiar={setClave}
          error={errores.clave}
          autoComplete="current-password"
        />

        <div className="auth-entre">
          <span />
          <Link to="/recuperar" className="btn btn-ghost">
            Olvide mi contrasena
          </Link>
        </div>

        <button type="submit" className="btn btn-primary btn-block" disabled={enviando}>
          {enviando ? 'Entrando...' : 'Entrar'}
        </button>
      </form>

      <div className="auth-demo">
        <div>
          <strong>Usuarios de prueba</strong>
          <br />
          alumno1@example.com o profe1@example.com, clave exonero123
        </div>
        <div className="auth-demo-botones">
          <button type="button" className="btn btn-secondary" onClick={() => completarDemo('alumno1@example.com')}>
            Alumno
          </button>
          <button type="button" className="btn btn-secondary" onClick={() => completarDemo('profe1@example.com')}>
            Profe
          </button>
        </div>
      </div>

      <p className="auth-pie">
        No tenes cuenta? <Link to="/registro">Crear una</Link>
      </p>
    </MarcoAuth>
  )
}
