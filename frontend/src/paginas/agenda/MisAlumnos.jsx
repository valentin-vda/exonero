/**
 * La pestania "Mis alumnos" de 1i, con GET /api/clases/mis-alumnos:
 *
 *   (AP) Ana Perez       6 clases · ultima: martes 9 de septiembre
 *        ★ 5 "Muy puntual y con todo leido"           [Editar resena]
 *   (JD) Juan Diaz       1 clase  · ultima: ...       [Calificar]
 *
 * Solo aparecen los alumnos con al menos una clase DICTADA: es la condicion
 * para poder resenarlos (el backend responde 403 sin_clases_con_esa_persona
 * si no). mi_resena es la que este profesor ya le dejo, o null: con eso se
 * decide entre "Calificar" y "Editar resena".
 *
 * Los dos botones abren /resenas/redactar/:id, el formulario compartido con
 * 1b. Las resenas son anonimas: el alumno ve el puntaje, nunca quien lo dejo.
 */

import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { misAlumnos } from '../../api/clases.js'
import { mensajeDeError } from '../../api/mensajes.js'
import Alerta from '../../componentes/Alerta.jsx'
import Avatar from '../../componentes/Avatar.jsx'
import { ESTRELLA, diaYHora, unir } from '../../utiles/formato.js'

export default function MisAlumnos() {
  const [lista, setLista] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    misAlumnos()
      .then(setLista)
      .catch((err) => setError(mensajeDeError(err.codigo)))
  }, [])

  if (error) return <Alerta tipo="error">No pudimos traer tus alumnos. {error}</Alerta>
  if (!lista) return <p className="tablero-vacio">Cargando tus alumnos...</p>
  if (lista.length === 0) {
    return <p className="tablero-vacio">Cuando marques una clase como dictada, el alumno aparece aca para calificarlo.</p>
  }

  return (
    <ul className="mis-alumnos">
      {lista.map(({ persona, cantidad_clases: cantidad, ultima_clase: ultima, mi_resena: resena }) => {
        const nombre = [persona.nombre, persona.apellido].filter(Boolean).join(' ')
        return (
          <li key={persona.id}>
            <Avatar persona={persona} tamanio="mediano" />
            <div className="mis-alumnos-quien">
              <strong>{nombre}</strong>
              <span className="texto-chico">
                {unir([cantidad === 1 ? '1 clase' : `${cantidad} clases`, ultima && `ultima: ${diaYHora(ultima)}`])}
              </span>
              {resena && (
                <span className="texto-chico">
                  {ESTRELLA} {resena.puntaje}{resena.texto && ` · "${resena.texto}"`}
                </span>
              )}
            </div>
            {/* state: el formulario ya sabe a quien califica y si tiene resena,
                sin pedir nada; y a donde volver al guardar. */}
            <Link to={`/resenas/redactar/${persona.id}`} className={`btn ${resena ? 'btn-ghost' : 'btn-secondary'}`}
                  state={{ persona, miResena: resena, volver: '/agenda#alumnos' }}
                  aria-label={`${resena ? 'Editar la resena de' : 'Calificar a'} ${nombre}`}>
              {resena ? 'Editar resena' : 'Calificar'}
            </Link>
          </li>
        )
      })}
    </ul>
  )
}
