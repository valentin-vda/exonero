/**
 * Pantalla de registro, para los dos roles.
 *
 * La spec tiene DOS endpoints de alta (/auth/registro/estudiante y
 * /auth/registro/profesor) pero UN solo cuerpo: los mismos campos para los dos.
 * Por eso hay una sola pantalla con un selector arriba, y no dos formularios.
 * El rol elegido decide a que ruta se llama.
 *
 * El rol es DEFINITIVO: no hay cambio de rol, y quien quiera ser las dos cosas
 * se crea dos cuentas con dos correos. Por eso se avisa abajo del selector.
 *
 * Los campos son exactamente los de RegistroIn en
 * backend/app/modulos/cuentas/esquemas.py.
 */

import { useEffect, useState } from 'react'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom'

import { mensajeDeError } from '../api/mensajes.js'
import { obtenerAviso } from '../api/privacidad.js'
import { useAuth } from '../auth/ContextoAuth.jsx'
import Alerta from '../componentes/Alerta.jsx'
import Campo from '../componentes/Campo.jsx'
import CampoClave from '../componentes/CampoClave.jsx'
import MarcoAuth from '../componentes/MarcoAuth.jsx'
import SelectorRol from '../componentes/SelectorRol.jsx'
import {
  esMenorDeEdad,
  validarClave,
  validarCorreo,
  validarFechaNacimiento,
  validarFormulario,
  validarRepetirClave,
  validarTexto,
} from '../utiles/validaciones.js'

export default function Registro() {
  const { usuario, registrarse } = useAuth()
  const navegar = useNavigate()

  // Permite entrar directo al formulario de profesor con /registro?rol=profesor,
  // util para un enlace de "Sos profe? Sumate".
  const [parametros] = useSearchParams()
  const rolInicial = parametros.get('rol') === 'profesor' ? 'profesor' : 'estudiante'

  const [rol, setRol] = useState(rolInicial)
  const [campos, setCampos] = useState({
    nombre: '',
    apellido: '',
    correo: '',
    clave: '',
    repetirClave: '',
    documento: '',
    telefono: '',
    fechaNacimiento: '',
    correoAdulto: '',
  })
  const [aceptaPrivacidad, setAceptaPrivacidad] = useState(false)
  const [aviso, setAviso] = useState(null)
  const [registroPendiente, setRegistroPendiente] = useState(false)
  const [errores, setErrores] = useState({})
  const [errorGeneral, setErrorGeneral] = useState(null)
  const [enviando, setEnviando] = useState(false)

  useEffect(() => {
    obtenerAviso().then(setAviso).catch(() => setErrorGeneral('No pudimos cargar el aviso de privacidad.'))
  }, [])

  if (usuario) {
    return <Navigate to={usuario.rol === 'profesor' ? '/panel' : '/inicio'} replace />
  }

  // Un solo manejador para los ocho campos, en vez de ocho funciones.
  function cambiar(campo) {
    return (valor) => setCampos((previos) => ({ ...previos, [campo]: valor }))
  }

  async function alEnviar(evento) {
    evento.preventDefault()

    const { errores: nuevos, hayErrores } = validarFormulario({
      nombre: () => validarTexto(campos.nombre, 'tu nombre', 2),
      apellido: () => validarTexto(campos.apellido, 'tu apellido', 2),
      correo: () => validarCorreo(campos.correo),
      clave: () => validarClave(campos.clave),
      repetirClave: () => validarRepetirClave(campos.clave, campos.repetirClave),
      fechaNacimiento: () => (!campos.fechaNacimiento ? 'La fecha de nacimiento es obligatoria.' : validarFechaNacimiento(campos.fechaNacimiento)),
      privacidad: () => (!aceptaPrivacidad ? 'Tenes que aceptar el aviso de privacidad.' : null),
      correoAdulto: () => (
        esMenorDeEdad(campos.fechaNacimiento) && rol === 'estudiante' && !campos.correoAdulto.trim()
          ? 'Necesitamos el correo de un adulto responsable.' : null
      ),
    })
    setErrores(nuevos)
    setErrorGeneral(null)
    if (hayErrores) return

    setEnviando(true)
    try {
      // Los nombres de las claves son los que espera RegistroIn en el backend.
      // Los opcionales vacios van como null y no como cadena vacia: el backend
      // los declara como str | None.
      const yo = await registrarse(rol, {
        correo: campos.correo.trim(),
        clave: campos.clave,
        nombre: campos.nombre.trim(),
        apellido: campos.apellido.trim(),
        documento: campos.documento.trim() || null,
        telefono: campos.telefono.trim() || null,
        fecha_nacimiento: campos.fechaNacimiento || null,
        correo_adulto: menor && rol === 'estudiante' ? campos.correoAdulto.trim() : null,
        acepta_privacidad: aceptaPrivacidad,
        version_privacidad: aviso?.version,
      })
      if (yo.pendiente) {
        setRegistroPendiente(true)
        return
      }
      // Recien creado, el perfil esta vacio: lo mandamos a completarlo.
      navegar(yo.rol === 'profesor' ? '/perfil-profesor' : '/mi-perfil', { replace: true })
    } catch (error) {
      setErrorGeneral(mensajeDeError(error.codigo))
    } finally {
      setEnviando(false)
    }
  }

  const menor = esMenorDeEdad(campos.fechaNacimiento)

  if (registroPendiente) {
    return (
      <MarcoAuth ancho>
        <h2 className="auth-titulo">Falta la autorizacion del adulto</h2>
        <Alerta tipo="ok">
          Enviamos un enlace al correo del adulto responsable. La cuenta quedara bloqueada
          hasta que lo abra y acepte el tratamiento de datos.
        </Alerta>
        <p className="auth-pie"><Link to="/login">Volver al ingreso</Link></p>
      </MarcoAuth>
    )
  }

  return (
    <MarcoAuth ancho>
      <h2 className="auth-titulo">Crear cuenta</h2>
      <p className="auth-bajada">Es gratis y toma un minuto.</p>

      <Alerta tipo="error">{errorGeneral}</Alerta>

      <SelectorRol valor={rol} alCambiar={setRol} />
      <p className="field-hint" style={{ marginTop: '-8px', marginBottom: '18px' }}>
        El tipo de cuenta no se puede cambiar después. Si querés ser las dos
        cosas, creá una cuenta con cada correo.
      </p>

      <form onSubmit={alEnviar} noValidate>
        <div className="auth-fila">
          <Campo
            id="nombre"
            etiqueta="Nombre"
            valor={campos.nombre}
            alCambiar={cambiar('nombre')}
            error={errores.nombre}
            requerido
            autoComplete="given-name"
          />
          <Campo
            id="apellido"
            etiqueta="Apellido"
            valor={campos.apellido}
            alCambiar={cambiar('apellido')}
            error={errores.apellido}
            requerido
            autoComplete="family-name"
          />
        </div>

        <Campo
          id="correo"
          etiqueta="Correo"
          tipo="email"
          valor={campos.correo}
          alCambiar={cambiar('correo')}
          error={errores.correo}
          ayuda="Va a ser tu usuario. No se puede cambiar después."
          requerido
          autoComplete="email"
          placeholder="tunombre@correo.com"
        />

        <div className="auth-fila">
          <CampoClave
            id="clave"
            etiqueta="Contraseña"
            valor={campos.clave}
            alCambiar={cambiar('clave')}
            error={errores.clave}
            ayuda={errores.clave ? null : 'Mínimo 8 caracteres.'}
            autoComplete="new-password"
          />
          <CampoClave
            id="repetirClave"
            etiqueta="Repetir contraseña"
            valor={campos.repetirClave}
            alCambiar={cambiar('repetirClave')}
            error={errores.repetirClave}
            autoComplete="new-password"
          />
        </div>

        <div className="auth-fila">
          <Campo
            id="documento"
            etiqueta="Documento"
            valor={campos.documento}
            alCambiar={cambiar('documento')}
            error={errores.documento}
            ayuda="Opcional"
            autoComplete="off"
            placeholder="1.234.567-8"
          />
          <Campo
            id="telefono"
            etiqueta="Teléfono"
            tipo="tel"
            valor={campos.telefono}
            alCambiar={cambiar('telefono')}
            error={errores.telefono}
            ayuda="Opcional"
            autoComplete="tel"
            placeholder="099 123 456"
          />
        </div>

        <Campo
          id="fechaNacimiento"
          etiqueta="Fecha de nacimiento"
          tipo="date"
          valor={campos.fechaNacimiento}
          alCambiar={cambiar('fechaNacimiento')}
          error={errores.fechaNacimiento}
          ayuda={
            menor && rol === 'estudiante'
              ? 'Sos menor de edad: después te vamos a pedir los datos de un adulto responsable.'
              : 'Opcional'
          }
          autoComplete="bday"
        />

        {menor && rol === 'estudiante' && (
          <Campo
            id="correoAdulto"
            etiqueta="Correo del adulto responsable"
            tipo="email"
            valor={campos.correoAdulto}
            alCambiar={cambiar('correoAdulto')}
            error={errores.correoAdulto}
            ayuda="Le enviaremos un enlace de autorizacion que vence en 72 horas."
            requerido
          />
        )}

        <label className="privacidad-check">
          <input
            type="checkbox"
            checked={aceptaPrivacidad}
            onChange={(e) => setAceptaPrivacidad(e.target.checked)}
          />
          <span>Lei y acepto el <Link to="/privacidad" target="_blank">aviso de privacidad</Link> version {aviso?.version || 'cargando...'}. Entiendo que es un prototipo y usare datos ficticios.</span>
        </label>
        {errores.privacidad && <p className="field-error">{errores.privacidad}</p>}

        <button type="submit" className="btn btn-primary btn-block" disabled={enviando || !aviso}>
          {enviando ? 'Creando la cuenta...' : 'Crear cuenta'}
        </button>
      </form>

      <p className="auth-pie">
        ¿Ya tenés cuenta? <Link to="/login">Entrar</Link>
      </p>
    </MarcoAuth>
  )
}
