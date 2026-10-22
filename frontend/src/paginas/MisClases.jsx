/**
 * 1b - Mis clases. Ruta: /mis-clases (con ?clase=ID abre el detalle de esa
 * clase si es la proxima; asi llega el "Ver detalle" de 1a).
 *
 * Todo lo del alumno alrededor de sus clases, de arriba hacia abajo:
 *
 *   MisClases           <- esta pantalla: la semana elegida y quien recarga que
 *   +-- ProximaClaseGrande  la siguiente confirmada, en grande     /clases/proxima
 *   +-- PorCalificar        los profes que todavia no califico     /clases/mis-profesores
 *   +-- CalendarioSemanal   la semana (el mismo componente de 1i)  /clases?desde&hasta
 *   +-- DetalleClase        Reprogramar / Cancelar de la que toco  /clases/{id}/...
 *   +-- MisProfesores       todos, con su resena y volver a reservar
 *   +-- Historial           las dictadas, paginadas                /clases?estado=dictada
 *
 * Para volver a tomar clase se entra a la ficha del profesor y se reserva de
 * nuevo, igual que la primera vez (no hay "repetir reserva").
 *
 * Igual que 1d y 1i, cada bloque tiene su propio estado (useBloque).
 * Cancelar o reprogramar terminan en recargar(): la proxima y la semana.
 */

import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { listarClases, misProfesores, proximaClase } from '../api/clases.js'
import CalendarioSemanal from '../componentes/clases/CalendarioSemanal.jsx'
import DetalleClase from '../componentes/clases/DetalleClase.jsx'
import Historial from './mis-clases/Historial.jsx'
import MisProfesores, { PorCalificar } from './mis-clases/MisProfesores.jsx'
import ProximaClaseGrande from './mis-clases/ProximaClaseGrande.jsx'
import { diaEnMontevideo, hoy, lunesDe, sumarDias } from './panel/fechas.js'
import useBloque from './panel/useBloque.js'

/**
 * Las clases de GET /clases -> la forma que dibuja CalendarioSemanal (la de
 * GET /agenda/yo/semana). Las canceladas no ocupan nada: no se dibujan.
 */
function aSemana(clases) {
  const de = (...estados) => clases.filter((c) => estados.includes(c.estado))
  return {
    aprobadas: de('aprobada'),
    pendientes: de('pendiente'),
    cerradas: de('dictada', 'no_asistida'),
    bloqueos: [],
  }
}

export default function MisClases() {
  const [parametros, setParametros] = useSearchParams()
  const [desde, setDesde] = useState(() => lunesDe(hoy()))
  const [elegida, setElegida] = useState(null)

  const proxima = useBloque()
  const profesores = useBloque()
  const semana = useBloque()

  function cargarSemana(lunes) {
    semana.cargar(listarClases({ desde: lunes, hasta: sumarDias(lunes, 6) }).then(aSemana), lunes)
  }

  useEffect(() => {
    const pedida = Number(parametros.get('clase'))
    proxima.cargar(
      proximaClase().then((clase) => {
        // ?clase=ID de 1a: si es la proxima, se abre su detalle en su semana.
        if (clase && clase.id === pedida) verDetalle(clase)
        return clase
      }),
    )
    profesores.cargar(misProfesores())
    cargarSemana(desde)
  }, [])

  function verDetalle(clase) {
    const lunes = lunesDe(diaEnMontevideo(clase.inicio))
    setElegida(clase)
    if (lunes !== desde) {
      setDesde(lunes)
      cargarSemana(lunes)
    }
    // Lleva la vista al detalle, que se dibuja abajo del calendario.
    setTimeout(() => document.getElementById('detalle-titulo')?.scrollIntoView({ behavior: 'smooth' }), 50)
  }

  /** Despues de cancelar o reprogramar: la proxima y la semana pudieron cambiar. */
  function recargar() {
    setElegida(null)
    if (parametros.has('clase')) setParametros({}, { replace: true })
    proxima.cargar(proximaClase())
    cargarSemana(desde)
  }

  function cambiarSemana(lunes) {
    setDesde(lunes)
    setElegida(null)
    cargarSemana(lunes)
  }

  return (
    <div className="tablero">
      <div className="perfil-titulo">
        <h2>Mis clases</h2>
        <p className="text-muted">Tu proxima clase, tu semana y los profes con los que ya estudiaste</p>
      </div>

      <ProximaClaseGrande bloque={proxima} alVerDetalle={verDetalle} />
      <PorCalificar bloque={profesores} />

      <CalendarioSemanal
        desde={desde}
        alCambiarSemana={cambiarSemana}
        bloque={semana}
        elegida={elegida}
        alElegirClase={(clase) => setElegida(elegida?.id === clase.id ? null : clase)}
      />

      {/* key: al tocar otra clase el detalle arranca de cero. */}
      {elegida && <DetalleClase key={elegida.id} clase={elegida} alCerrar={() => setElegida(null)} alCambiar={recargar} />}

      <MisProfesores bloque={profesores} />
      <Historial />
    </div>
  )
}
