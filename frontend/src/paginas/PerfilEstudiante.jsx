/**
 * 1e - Perfil del estudiante. Ruta: /mi-perfil
 *
 * Como esta armada (de afuera hacia adentro):
 *
 *   PerfilEstudiante            <- esta pantalla: carga los datos y decide
 *   |                              que pestania se ve
 *   +-- MenuLateral             <- las pestanias, modo oscuro, cerrar sesion
 *   +-- CabeceraPerfil          <- la tarjeta verde con la foto
 *   +-- la seccion elegida:
 *         SeccionPersonalEstudiante   datos de la cuenta y del perfil
 *         SeccionClave                cambiar la contrasena, darse de baja
 *         SeccionMediosPago           tarjetas e historial de pagos (P4)
 *         (Mis resenas)               de P3: todavia pendiente
 *
 * Que llamadas hace al entrar:
 *   GET /api/perfiles/estudiante/yo   etapa, centro, barrio, adulto...
 *   GET /api/catalogos/todo           las opciones de los desplegables (P2)
 * Los datos de la cuenta (nombre, foto, correo) no se piden: ya estan en
 * useAuth(), que los trajo de GET /api/usuarios/yo al entrar a la app.
 * Las tarjetas y los pagos los pide SeccionMediosPago recien cuando se abre
 * esa pestania: no hace falta cargarlos para ver los datos personales.
 */

import { useEffect, useState } from 'react'

import { mensajeDeError } from '../api/mensajes.js'
import { obtenerCatalogos, obtenerPerfilEstudiante } from '../api/perfiles.js'
import { useAuth } from '../auth/ContextoAuth.jsx'
import Alerta from '../componentes/Alerta.jsx'
import EnConstruccion from '../componentes/EnConstruccion.jsx'
import { ESTRELLA, mesYAnio, puntaje, unir } from '../utiles/formato.js'
import CabeceraPerfil from './perfil/CabeceraPerfil.jsx'
import MenuLateral from './perfil/MenuLateral.jsx'
import { AVISO_SIN_CATALOGOS } from './perfil/opciones.js'
import SeccionClave from './perfil/SeccionClave.jsx'
import SeccionMediosPago from './perfil/SeccionMediosPago.jsx'
import SeccionPersonalEstudiante from './perfil/SeccionPersonalEstudiante.jsx'

// Las pestanias del menu lateral, en orden. El id es lo que se guarda en el
// estado; el texto, lo que se ve.
const PESTANIAS = [
  { id: 'personal', texto: 'Informacion personal' },
  { id: 'clave', texto: 'Contrasena' },
  { id: 'pagos', texto: 'Medios de pago' },
  { id: 'resenas', texto: 'Mis resenas' },
]

export default function PerfilEstudiante() {
  const { usuario } = useAuth()

  const [pestania, setPestania] = useState('personal')
  const [perfil, setPerfil] = useState(null)       // lo de GET /perfiles/estudiante/yo
  const [catalogos, setCatalogos] = useState(null) // null = no cargaron
  const [cargando, setCargando] = useState(true)
  const [errorCarga, setErrorCarga] = useState(null)

  // Al entrar a la pantalla (el [] del final = una sola vez): pedir el perfil
  // y los catalogos AL MISMO TIEMPO con Promise.all, en vez de uno detras del
  // otro. Si los catalogos fallan (P2 todavia no los hizo), el .catch los deja
  // en null y la pantalla funciona igual.
  useEffect(() => {
    Promise.all([obtenerPerfilEstudiante(), obtenerCatalogos().catch(() => null)])
      .then(([perfilRecibido, catalogosRecibidos]) => {
        setPerfil(perfilRecibido)
        setCatalogos(catalogosRecibidos)
      })
      .catch((error) => setErrorCarga(mensajeDeError(error.codigo)))
      .finally(() => setCargando(false))
  }, [])

  /** Vuelve a pedir el perfil. Las secciones lo llaman despues de guardar. */
  async function recargarPerfil() {
    setPerfil(await obtenerPerfilEstudiante())
  }

  if (cargando) return <p className="text-muted" style={{ marginTop: '40px' }}>Cargando tu perfil...</p>
  if (errorCarga) return <Alerta tipo="error">{errorCarga}</Alerta>

  // --- La cabecera: "5.o de Bachillerato · Liceo Bauza · Cordon, Montevideo"
  const cabecera = usuario.estudiante || {}
  const etapaYNivel = cabecera.nivel && cabecera.etapa ? `${cabecera.nivel} de ${cabecera.etapa}` : cabecera.etapa
  const subtitulo = unir([etapaYNivel, cabecera.centro, cabecera.barrio && `${cabecera.barrio}, Montevideo`])

  return (
    <div className="perfil">
      <MenuLateral pestanias={PESTANIAS} activa={pestania} alElegir={setPestania} subtitulo="Cuenta de estudiante" />

      <div className="perfil-contenido">
        <CabeceraPerfil subtitulo={subtitulo || 'Completa tus datos educativos para que los profes te conozcan.'}>
          <span className="tag tag-neutral">Miembro desde {mesYAnio(usuario.creado_el)}</span>
          {cabecera.cantidad_resenas > 0 && (
            <span className="tag tag-accent-2">
              {ESTRELLA} {puntaje(cabecera.puntaje_promedio)} {'·'} {cabecera.cantidad_resenas} resenas
            </span>
          )}
        </CabeceraPerfil>

        {!catalogos && pestania === 'personal' && <Alerta tipo="info">{AVISO_SIN_CATALOGOS}</Alerta>}

        {/* Solo se dibuja la seccion de la pestania elegida. Al cambiar de
            pestania, la anterior desaparece y la nueva arranca de cero. */}
        {pestania === 'personal' && (
          <SeccionPersonalEstudiante perfil={perfil} catalogos={catalogos} alGuardar={recargarPerfil} />
        )}
        {pestania === 'clave' && <SeccionClave />}
        {pestania === 'pagos' && <SeccionMediosPago />}
        {pestania === 'resenas' && (
          <div className="panel">
            <EnConstruccion
              codigo="1e"
              nombre="Mis resenas"
              dueno="P3"
              descripcion="Tu puntaje como estudiante y las resenas que te dejaron los profesores (GET /api/resenas/usuario/{id})."
            />
          </div>
        )}
      </div>
    </div>
  )
}
