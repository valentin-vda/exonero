/**
 * El saludo de arriba del panel (1d):
 *
 *   Hola, Lucia                         [Editar disponibilidad] [Bloquear horario]
 *   Matematica y Fisica · Ciclo basico, Bachillerato y UTU · Cordon
 *
 * El nombre sale del usuario conectado (useAuth), asi el saludo aparece
 * aunque la ficha no cargue. El subtitulo se arma con la ficha
 * (GET /api/perfiles/profesor/yo): materias, etapas y barrio. Si la ficha
 * falla, el subtitulo no se muestra y el resto del panel sigue igual.
 *
 * Los dos botones llevan a la agenda (1i, de P3): la disponibilidad y los
 * bloqueos de horario se editan alla.
 */

import { Link } from 'react-router-dom'

import { useAuth } from '../../auth/ContextoAuth.jsx'
import { unir } from '../../utiles/formato.js'

// Une una lista como se dice en espanol: ['a', 'b', 'c'] -> "a, b y c".
const enLista = new Intl.ListFormat('es', { type: 'conjunction' })

/** "Matematica y Fisica · Ciclo basico, Bachillerato y UTU · Cordon" */
function subtituloDe(ficha) {
  // Un profe puede tener la misma etapa con dos programas: el Set saca los
  // nombres repetidos.
  const etapas = [...new Set(ficha.etapas.map((e) => e.nombre).filter(Boolean))]
  return unir([
    enLista.format(ficha.materias.map((m) => m.nombre)),
    enLista.format(etapas),
    ficha.barrio,
  ])
}

export default function Saludo({ ficha }) {
  const { usuario } = useAuth()
  const subtitulo = ficha.datos ? subtituloDe(ficha.datos) : ''

  return (
    <div className="tablero-saludo">
      <div>
        <h2>Hola, {usuario.nombre}</h2>
        {/* Si la ficha cargo pero esta vacia, en vez del subtitulo se lo
            manda a completarla. Si no cargo (o esta cargando), nada. */}
        {subtitulo && <p className="tablero-subtitulo">{subtitulo}</p>}
        {ficha.datos && !subtitulo && (
          <p className="tablero-subtitulo">
            Todavia no cargaste tus materias. <Link to="/perfil-profesor">Completa tu perfil</Link> para que
            los alumnos te encuentren.
          </p>
        )}
      </div>

      <div className="tablero-botones">
        <Link to="/agenda" className="btn btn-secondary">
          Editar disponibilidad
        </Link>
        <Link to="/agenda" className="btn btn-primary">
          Bloquear horario
        </Link>
      </div>
    </div>
  )
}
