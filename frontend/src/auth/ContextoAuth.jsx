/**
 * Contexto de autenticacion.
 *
 * Que es un contexto de React, en dos lineas: una forma de compartir un dato
 * con TODOS los componentes de la app sin tener que pasarlo como prop de padre
 * a hijo, nivel por nivel. Aca el dato compartido es "quien esta conectado".
 *
 * Como se usa desde cualquier pantalla:
 *
 *   import { useAuth } from '../auth/ContextoAuth.jsx'
 *
 *   function MiPantalla() {
 *     const { usuario, salir } = useAuth()
 *     return <p>Hola {usuario.nombre}</p>
 *   }
 */

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

import { EVENTO_SESION_VENCIDA, borrarToken, guardarToken, leerToken } from '../api/cliente.js'
import { login as apiLogin, obtenerYo, registrar as apiRegistrar } from '../api/auth.js'

const ContextoAuth = createContext(null)

export function ProveedorAuth({ children }) {
  // El usuario conectado, o null si no hay nadie.
  const [usuario, setUsuario] = useState(null)

  // true mientras se esta averiguando si hay sesion. Importa: sin esto, al
  // recargar la pagina se ve el login por un instante antes de saber que si
  // habia token, y queda feo.
  const [cargando, setCargando] = useState(true)

  // Al arrancar la app: si hay un token guardado, preguntar quien es.
  useEffect(() => {
    const token = leerToken()
    if (!token) {
      setCargando(false)
      return
    }
    obtenerYo()
      .then((yo) => setUsuario(yo))
      .catch((error) => {
        // Un 401 es que el token vencio o no sirve: se descarta. Si fallo la
        // red o el servidor, el token puede seguir valiendo: queda guardado y
        // al recargar se vuelve a probar. En los dos casos, por ahora no hay
        // nadie conectado.
        if (error.estado === 401) borrarToken()
        setUsuario(null)
      })
      .finally(() => setCargando(false))
  }, [])

  // Si un pedido cualquiera recibe un 401 con la app abierta, cliente.js ya
  // borro el token y avisa con este evento: se cierra la sesion aca tambien.
  useEffect(() => {
    function alVencer() {
      setUsuario(null)
    }
    window.addEventListener(EVENTO_SESION_VENCIDA, alVencer)
    return () => window.removeEventListener(EVENTO_SESION_VENCIDA, alVencer)
  }, [])

  /** Entra con correo y clave. Devuelve el usuario. */
  const entrar = useCallback(async (correo, clave) => {
    const respuesta = await apiLogin(correo, clave)
    guardarToken(respuesta.token)
    // El login devuelve un usuario recortado (id, nombre, rol). Pedimos el
    // completo, que es el que necesitan las pantallas para la cabecera.
    const yo = await obtenerYo()
    setUsuario(yo)
    return yo
  }, [])

  /** Crea la cuenta y deja la sesion abierta, sin pasar por el login. */
  const registrarse = useCallback(async (rol, datos) => {
    const respuesta = await apiRegistrar(rol, datos)
    guardarToken(respuesta.token)
    const yo = await obtenerYo()
    setUsuario(yo)
    return yo
  }, [])

  /**
   * Cierra sesion. No hay endpoint: cerrar sesion es descartar el token en el
   * frontend, como dice la spec.
   */
  const salir = useCallback(() => {
    borrarToken()
    setUsuario(null)
  }, [])

  /**
   * Vuelve a pedir GET /usuarios/yo y actualiza el usuario de toda la app.
   *
   * Se llama despues de editar algo de la cuenta (nombre, foto, tema): asi la
   * barra de arriba, el menu lateral y la cabecera muestran lo nuevo sin
   * recargar la pagina. Como `usuario` vive en este contexto, al cambiarlo se
   * redibujan solos todos los componentes que lo usan.
   */
  const refrescar = useCallback(async () => {
    const yo = await obtenerYo()
    setUsuario(yo)
    return yo
  }, [])

  // El tema (claro u oscuro) se guarda en la cuenta. Cada vez que cambia el
  // usuario, se escribe en <html data-tema="..."> y tokens.css hace el resto:
  // redefine las variables de color, y como todo el CSS usa variables, toda
  // la app cambia de color. Sin sesion (en el login) siempre es claro.
  useEffect(() => {
    document.documentElement.dataset.tema = usuario?.tema || 'claro'
  }, [usuario])

  // useMemo evita que el objeto se cree de nuevo en cada render, lo que
  // volveria a renderizar toda la app sin motivo.
  const valor = useMemo(
    () => ({ usuario, cargando, entrar, registrarse, salir, refrescar }),
    [usuario, cargando, entrar, registrarse, salir, refrescar],
  )

  return <ContextoAuth.Provider value={valor}>{children}</ContextoAuth.Provider>
}

/** Atajo para leer el contexto. Falla claro si alguien lo usa fuera del proveedor. */
export function useAuth() {
  const contexto = useContext(ContextoAuth)
  if (!contexto) {
    throw new Error('useAuth() tiene que usarse adentro de <ProveedorAuth>')
  }
  return contexto
}
