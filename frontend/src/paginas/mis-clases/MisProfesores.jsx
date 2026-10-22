/**
 * Las dos listas de 1b que salen de GET /api/clases/mis-profesores (los
 * profesores con los que el alumno tuvo al menos una clase DICTADA):
 *
 *   PorCalificar   solo los que todavia no calificaste, arriba y destacados.
 *                  Si no hay ninguno, no se dibuja.
 *   MisProfesores  todos, con tu resena (si la dejaste), "Editar" y
 *                  "Volver a reservar" (que lleva a la ficha, como dice la spec:
 *                  se reserva de nuevo igual que la primera vez).
 *
 * Calificar y Editar abren /resenas/redactar/:id con la persona y la resena
 * en el state, para que el formulario no tenga que pedir nada.
 */

import { Link } from 'react-router-dom'

import Alerta from '../../componentes/Alerta.jsx'
import Avatar from '../../componentes/Avatar.jsx'
import BotonMensaje from '../../componentes/BotonMensaje.jsx'
import { ESTRELLA, diaYHora, pesos, unir } from '../../utiles/formato.js'

function nombreDe(persona) {
  return [persona.nombre, persona.apellido].filter(Boolean).join(' ')
}

function BotonResena({ fila, texto, clase }) {
  return (
    <Link
      to={`/resenas/redactar/${fila.persona.id}`}
      state={{ persona: fila.persona, miResena: fila.mi_resena, volver: '/mis-clases' }}
      className={`btn ${clase}`}
      aria-label={`${texto} a ${nombreDe(fila.persona)}`}
    >
      {texto}
    </Link>
  )
}

export function PorCalificar({ bloque }) {
  const pendientes = (bloque.datos || []).filter((fila) => !fila.mi_resena)
  if (pendientes.length === 0) return null

  return (
    <section className="tablero-bloque tablero-bloque-acento" aria-labelledby="calificar-titulo">
      <div className="tablero-encabezado">
        <h3 id="calificar-titulo">Contanos como te fue</h3>
        <span className="tablero-resumen">Tu calificacion es anonima: el profe ve el puntaje, no quien lo dejo</span>
      </div>
      <ul className="mis-clases-lista">
        {pendientes.map((fila) => (
          <li key={fila.persona.id}>
            <Avatar persona={fila.persona} tamanio="mediano" />
            <div className="mis-clases-lista-quien">
              <strong>{nombreDe(fila.persona)}</strong>
              <span className="texto-chico">{unir(fila.persona.materias || [])}</span>
            </div>
            <BotonResena fila={fila} texto="Calificar" clase="btn-primary" />
          </li>
        ))}
      </ul>
    </section>
  )
}

export default function MisProfesores({ bloque }) {
  const { datos, error, cargando } = bloque

  return (
    <section className="tablero-bloque" aria-labelledby="mis-profes-titulo">
      <div className="tablero-encabezado">
        <h3 id="mis-profes-titulo">Mis profesores</h3>
      </div>
      {cargando && !datos && <p className="tablero-vacio">Cargando tus profesores...</p>}
      {error && <Alerta tipo="error">No pudimos traer tus profesores. {error}</Alerta>}
      {datos && datos.length === 0 && (
        <p className="tablero-vacio">Cuando tengas tu primera clase dictada, tu profe aparece aca para calificarlo.</p>
      )}
      {datos && datos.length > 0 && (
        <ul className="mis-clases-lista">
          {datos.map((fila) => {
            const { persona, mi_resena: resena } = fila
            return (
              <li key={persona.id}>
                <Avatar persona={persona} tamanio="mediano" />
                <div className="mis-clases-lista-quien">
                  <strong>{nombreDe(persona)}</strong>
                  <span className="texto-chico">
                    {unir([
                      unir(persona.materias || []),
                      fila.cantidad_clases === 1 ? '1 clase' : `${fila.cantidad_clases} clases`,
                      fila.ultima_clase && `ultima: ${diaYHora(fila.ultima_clase)}`,
                      persona.precio_hora && `desde ${pesos(persona.precio_hora)}/h`,
                    ])}
                  </span>
                  {resena && (
                    <span className="texto-chico">
                      Tu calificacion: {ESTRELLA} {resena.puntaje}{resena.texto && ` · "${resena.texto}"`}
                    </span>
                  )}
                </div>
                <div className="tablero-botones">
                  <BotonResena fila={fila} texto={resena ? 'Editar resena' : 'Calificar'}
                               clase={resena ? 'btn-ghost' : 'btn-secondary'} />
                  <BotonMensaje personaId={persona.id} className="btn btn-ghost" />
                  <Link to={`/profesor/${persona.id}`} className="btn btn-secondary">Volver a reservar</Link>
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}
