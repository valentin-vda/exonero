/**
 * 1j - Perfil del profesor. Ruta: /perfil-profesor
 *
 * Es la pantalla donde el profesor arma su ficha publica: todo lo que edita
 * aca es lo que ven los alumnos en la busqueda (1c) y en el detalle (1f).
 *
 * Como esta armada:
 *
 *   PerfilProfesor              <- esta pantalla: carga la ficha y decide
 *   |                              que pestania se ve
 *   +-- MenuLateral             <- pestanias, % completo, publicar/pausar,
 *   |                              modo oscuro, cerrar sesion
 *   +-- CabeceraPerfil          <- la tarjeta verde con la foto
 *   +-- la seccion elegida:
 *         SeccionDatosProfesor   datos personales, titulo, barrio base
 *         SeccionEnsena          materias, modalidad, precios, duraciones
 *         EditorFranjas          la disponibilidad semanal (el mismo de 1i, P3)
 *         SeccionBio             titular, biografia, como es una clase
 *         SeccionFotos           fotos del lugar
 *         SeccionClave           cambiar la contrasena, darse de baja
 *
 * La ficha (GET /api/perfiles/profesor/yo) la guarda ESTA pantalla y se la
 * pasa a cada seccion. Cuando una seccion guarda, llama a alGuardar(), que
 * vuelve a pedir la ficha: asi el % completo y la cabecera se actualizan.
 */

import { useEffect, useState } from 'react'

import { mensajeDeError } from '../api/mensajes.js'
import { cambiarEstadoFicha, obtenerCatalogos, obtenerMiFicha } from '../api/perfiles.js'
import { useAuth } from '../auth/ContextoAuth.jsx'
import Alerta from '../componentes/Alerta.jsx'
import { ESTRELLA, mesYAnio, puntaje, unir } from '../utiles/formato.js'
import EditorFranjas from './agenda/EditorFranjas.jsx'
import CabeceraPerfil from './perfil/CabeceraPerfil.jsx'
import MenuLateral from './perfil/MenuLateral.jsx'
import { AVISO_SIN_CATALOGOS, ESTADOS_FICHA } from './perfil/opciones.js'
import SeccionBio from './perfil/SeccionBio.jsx'
import SeccionClave from './perfil/SeccionClave.jsx'
import SeccionDatosProfesor from './perfil/SeccionDatosProfesor.jsx'
import SeccionEnsena from './perfil/SeccionEnsena.jsx'
import SeccionFotos from './perfil/SeccionFotos.jsx'

const PESTANIAS = [
  { id: 'datos', texto: 'Informacion personal' },
  { id: 'ensena', texto: 'Materias y modalidad' },
  { id: 'disponibilidad', texto: 'Disponibilidad' },
  { id: 'bio', texto: 'Biografia' },
  { id: 'fotos', texto: 'Fotos del lugar' },
  { id: 'seguridad', texto: 'Contrasena' },
]

/**
 * El "Perfil 82 % completo" del menu lateral. Es solo una guia para el
 * profesor (el backend no lo usa): cuenta cuantos de estos pasos ya hizo.
 */
function porcentajeCompleto(ficha, usuario) {
  const pasos = [
    Boolean(usuario.foto_base64),
    Boolean(ficha.titulo_habilitante),
    ficha.anios_experiencia !== null,
    Boolean(ficha.barrio),
    ficha.materias.length > 0,
    ficha.etapas.length > 0,
    Boolean(ficha.precio_hora_presencial || ficha.precio_hora_online),
    Boolean(ficha.titular),
    Boolean(ficha.biografia),
    ficha.puntos_metodo.length > 0,
    ficha.fotos.length > 0,
  ]
  const hechos = pasos.filter(Boolean).length
  return Math.round((100 * hechos) / pasos.length)
}

export default function PerfilProfesor() {
  const { usuario } = useAuth()

  const [pestania, setPestania] = useState('datos')
  const [ficha, setFicha] = useState(null)
  const [catalogos, setCatalogos] = useState(null)
  const [cargando, setCargando] = useState(true)
  const [errorCarga, setErrorCarga] = useState(null)

  // Publicar / pausar
  const [cambiandoEstado, setCambiandoEstado] = useState(false)
  const [errorEstado, setErrorEstado] = useState(null)

  // Al entrar: la ficha y los catalogos, al mismo tiempo. Igual que en 1e, si
  // los catalogos fallan quedan en null y la pantalla sigue andando.
  useEffect(() => {
    Promise.all([obtenerMiFicha(), obtenerCatalogos().catch(() => null)])
      .then(([fichaRecibida, catalogosRecibidos]) => {
        setFicha(fichaRecibida)
        setCatalogos(catalogosRecibidos)
      })
      .catch((error) => setErrorCarga(mensajeDeError(error.codigo)))
      .finally(() => setCargando(false))
  }, [])

  /** Vuelve a pedir la ficha. Las secciones lo llaman despues de guardar. */
  async function recargarFicha() {
    setFicha(await obtenerMiFicha())
  }

  /** Publica la ficha si estaba en borrador o pausada, y la pausa si estaba publicada. */
  async function alternarPublicacion() {
    setErrorEstado(null)
    setCambiandoEstado(true)
    try {
      await cambiarEstadoFicha(ficha.estado_ficha === 'publicada' ? 'pausada' : 'publicada')
      await recargarFicha()
    } catch (error) {
      setErrorEstado(mensajeDeError(error.codigo))
    } finally {
      setCambiandoEstado(false)
    }
  }

  if (cargando) return <p className="text-muted" style={{ marginTop: '40px' }}>Cargando tu ficha...</p>
  if (errorCarga) return <Alerta tipo="error">{errorCarga}</Alerta>

  const publicada = ficha.estado_ficha === 'publicada'
  const completo = porcentajeCompleto(ficha, usuario)

  // "Profesora de Matematica (IPA) · 6 anios de experiencia · Cordon"
  const subtitulo = unir([
    ficha.titulo_habilitante,
    ficha.anios_experiencia !== null && `${ficha.anios_experiencia} anios de experiencia`,
    ficha.barrio,
  ])

  // Las props que reciben casi todas las secciones, juntas para no repetirlas.
  const props = { ficha, catalogos, alGuardar: recargarFicha }

  return (
    <>
      <div className="perfil-titulo">
        <h2>Mi perfil</h2>
        <p className="text-muted">Todo lo que edites aca es lo que ven los alumnos en tu ficha</p>
      </div>

      <div className="perfil">
        <MenuLateral pestanias={PESTANIAS} activa={pestania} alElegir={setPestania} subtitulo="Cuenta de profesor">
          {/* Esto es el children de MenuLateral: va entre el separador y el
              interruptor de modo oscuro. */}
          <div>
            <div className="texto-chico">Perfil {completo} % completo</div>
            <div className="progreso">
              <div className="progreso-relleno" style={{ width: `${completo}%` }} />
            </div>
          </div>

          <div>
            <div className="estado-ficha">
              <span className={`tag ${publicada ? 'tag-accent-2' : 'tag-neutral'}`}>
                Ficha: {ESTADOS_FICHA[ficha.estado_ficha]}
              </span>
              <button type="button" className="btn btn-ghost" onClick={alternarPublicacion} disabled={cambiandoEstado}>
                {publicada ? 'Pausar' : 'Publicar'}
              </button>
            </div>
            <p className="texto-chico" style={{ margin: '6px 0 0' }}>
              {publicada
                ? 'Los alumnos te encuentran en la busqueda.'
                : 'No apareces en la busqueda hasta que publiques.'}
            </p>
            {errorEstado && (
              <p className="field-hint field-hint-error" style={{ paddingLeft: 0 }}>{errorEstado}</p>
            )}
          </div>
        </MenuLateral>

        <div className="perfil-contenido">
          <CabeceraPerfil subtitulo={subtitulo || 'Completa tus datos para que los alumnos te conozcan.'}>
            {ficha.cantidad_resenas > 0 ? (
              <span className="tag tag-accent-2">
                {ESTRELLA} {puntaje(ficha.puntaje_promedio)} {'·'} {ficha.cantidad_resenas} resenas
              </span>
            ) : (
              <span className="tag tag-neutral">Todavia sin resenas</span>
            )}
            <span className="tag tag-neutral">{ficha.clases_dictadas} clases dictadas</span>
            <span className="tag tag-neutral">Miembro desde {mesYAnio(usuario.creado_el)}</span>
          </CabeceraPerfil>

          {!catalogos && (pestania === 'datos' || pestania === 'ensena') && (
            <Alerta tipo="info">{AVISO_SIN_CATALOGOS}</Alerta>
          )}

          {/* {...props} pasa ficha, catalogos y alGuardar de una vez. */}
          {pestania === 'datos' && <SeccionDatosProfesor {...props} />}
          {pestania === 'ensena' && <SeccionEnsena {...props} />}
          {/* La misma edicion que la pestania Disponibilidad de la agenda (1i):
              carga y guarda sus franjas sola, no usa la ficha. */}
          {pestania === 'disponibilidad' && (
            <section className="panel">
              <h4 style={{ marginBottom: '4px' }}>Disponibilidad</h4>
              <EditorFranjas />
            </section>
          )}
          {pestania === 'bio' && <SeccionBio {...props} />}
          {pestania === 'fotos' && <SeccionFotos {...props} />}
          {pestania === 'seguridad' && <SeccionClave />}
        </div>
      </div>
    </>
  )
}
