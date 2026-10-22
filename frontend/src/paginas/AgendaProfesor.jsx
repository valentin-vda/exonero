/**
 * 1i - Agenda del profesor. Ruta: /agenda (con #disponibilidad, #bloqueos o
 * #alumnos abre directo esa pestania; asi llegan los botones del panel 1d).
 *
 * Todo lo que pasa alrededor de la clase sin ser la clase: cuando hay lugar y
 * que hay que responder. De arriba hacia abajo:
 *
 *   AgendaProfesor        <- esta pantalla: la semana elegida y quien recarga que
 *   +-- Solicitudes       las pendientes, con Aprobar / Rechazar  /clases/pendientes
 *   +-- CalendarioSemanal la semana con clases, bloqueos y        /agenda/yo/semana
 *   |                     (si se pide) los huecos del alumno      /agenda/profesores/{yo}/disponibilidad
 *   +-- DetalleClase      las acciones de la clase que se toco    /clases/{id}/...
 *   +-- pestanias:
 *       EditorFranjas     la disponibilidad semanal (tambien 1j)  /agenda/yo/franjas
 *       Bloqueos          los ratos puntuales que no puede        /agenda/yo/bloqueos
 *       MisAlumnos        con quienes ya dio clase, para calificar /clases/mis-alumnos
 *
 * Las piezas estan en src/paginas/agenda/. Igual que en 1d, cada bloque tiene
 * su propio estado (useBloque): si una llamada falla, el resto se ve igual.
 *
 * Aprobar, rechazar, cancelar, reprogramar, bloquear o cambiar franjas
 * cambian lo que hay que mostrar arriba: todos terminan en recargar().
 */

import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import { listarFranjas, obtenerDisponibilidad, semanaProfesor } from '../api/agenda.js'
import { solicitudesPendientes } from '../api/clases.js'
import { useAuth } from '../auth/ContextoAuth.jsx'
import CalendarioSemanal from '../componentes/clases/CalendarioSemanal.jsx'
import DetalleClase from '../componentes/clases/DetalleClase.jsx'
import Bloqueos from './agenda/Bloqueos.jsx'
import EditorFranjas from './agenda/EditorFranjas.jsx'
import MisAlumnos from './agenda/MisAlumnos.jsx'
import { PESTANIAS } from './agenda/opciones.js'
import Solicitudes from './agenda/Solicitudes.jsx'
import { hoy, lunesDe, sumarDias } from './panel/fechas.js'
import useBloque from './panel/useBloque.js'

/** La pestania que pide el #hash de la URL, o la primera. */
function pestaniaDe(hash) {
  const id = hash.replace('#', '')
  return PESTANIAS.some((p) => p.id === id) ? id : PESTANIAS[0].id
}

export default function AgendaProfesor() {
  const { usuario } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const [desde, setDesde] = useState(() => lunesDe(hoy()))
  const [verHuecos, setVerHuecos] = useState(false)
  const [elegida, setElegida] = useState(null)
  const pestania = pestaniaDe(location.hash)

  const solicitudes = useBloque()
  const semana = useBloque()
  const franjas = useBloque()
  const huecos = useBloque()

  function cargarSemana(lunes, conHuecos = verHuecos) {
    semana.cargar(semanaProfesor(lunes), lunes)
    // Una hora, que es lo que reserva la mayoria. Es para mirar, no para reservar.
    if (conHuecos) huecos.cargar(obtenerDisponibilidad(usuario.id, lunes, sumarDias(lunes, 6), 60), lunes)
  }

  useEffect(() => {
    solicitudes.cargar(solicitudesPendientes())
    franjas.cargar(listarFranjas())
    cargarSemana(desde)
  }, [])

  // Si se entra con #bloqueos (o se toca el boton del panel estando aca), que
  // la pestania quede a la vista.
  useEffect(() => {
    if (location.hash) document.getElementById('agenda-pestanias')?.scrollIntoView({ behavior: 'smooth' })
  }, [location.hash])

  /** Despues de cualquier accion: lo que pudo haber cambiado arriba. */
  function recargar() {
    setElegida(null)
    solicitudes.cargar(solicitudesPendientes())
    cargarSemana(desde)
  }

  function cambiarSemana(lunes) {
    setDesde(lunes)
    setElegida(null)
    cargarSemana(lunes)
  }

  function cambiarVerHuecos(valor) {
    setVerHuecos(valor)
    if (valor) huecos.cargar(obtenerDisponibilidad(usuario.id, desde, sumarDias(desde, 6), 60), desde)
  }

  function alGuardarFranjas() {
    franjas.cargar(listarFranjas())
    cargarSemana(desde)
  }

  return (
    <div className="tablero">
      <div className="perfil-titulo">
        <h2>Agenda</h2>
        <p className="text-muted">Tus solicitudes, tu semana y cuando pueden reservarte</p>
      </div>

      <Solicitudes bloque={solicitudes} alCambiar={recargar} />

      <CalendarioSemanal
        desde={desde}
        alCambiarSemana={cambiarSemana}
        bloque={semana}
        franjas={franjas.datos}
        // Los huecos de otra semana (si todavia no llegaron los nuevos) no se dibujan.
        huecos={huecos.para === desde ? huecos.datos : null}
        verHuecos={verHuecos}
        alCambiarVerHuecos={cambiarVerHuecos}
        elegida={elegida}
        alElegirClase={(clase) => setElegida(elegida?.id === clase.id ? null : clase)}
      />

      {/* key: al tocar otra clase el detalle arranca de cero (sin el formulario
          que habia quedado abierto de la anterior). */}
      {elegida && <DetalleClase key={elegida.id} clase={elegida} alCerrar={() => setElegida(null)} alCambiar={recargar} />}

      <section className="tablero-bloque" id="agenda-pestanias">
        <div className="agenda-pestanias" role="tablist" aria-label="Configuracion de la agenda">
          {PESTANIAS.map((p) => (
            <button
              key={p.id}
              type="button"
              role="tab"
              id={`pestania-${p.id}`}
              aria-selected={pestania === p.id}
              aria-controls={`panel-${p.id}`}
              className="agenda-pestania"
              onClick={() => navigate({ hash: p.id }, { replace: true })}
            >
              {p.texto}
            </button>
          ))}
        </div>
        <div role="tabpanel" id={`panel-${pestania}`} aria-labelledby={`pestania-${pestania}`}>
          {pestania === 'disponibilidad' && <EditorFranjas alGuardar={alGuardarFranjas} />}
          {pestania === 'bloqueos' && <Bloqueos alCambiar={recargar} />}
          {pestania === 'alumnos' && <MisAlumnos />}
        </div>
      </section>
    </div>
  )
}
