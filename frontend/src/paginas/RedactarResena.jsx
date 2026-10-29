/**
 * Redactar resena. Ruta: /resenas/redactar/:destinatarioId - P3.
 *
 * La comparten los dos roles: el alumno califica a un profesor (desde 1b) y
 * el profesor a un alumno (desde 1i, pestania Mis alumnos). No es una pestania
 * del menu: se llega con "Calificar" o "Editar resena".
 *
 *   Calificar a Lucia Fernandez
 *   (LF) Matematica · Fisica
 *   ★ ★ ★ ★ ☆   Muy buena
 *   [ Comentario (opcional)                         ]  120 de 500
 *   Tu calificacion es anonima: Lucia ve el puntaje, no quien lo dejo.
 *                                       [Cancelar] [Guardar calificacion]
 *
 * De donde sale la persona:
 *   - Normalmente viene en el state del Link (persona, miResena y a donde
 *     volver): no hace falta pedir nada.
 *   - Si se recarga la pagina el state se pierde: se piden las mismas listas
 *     de donde salio el boton (mis-profesores o mis-alumnos, segun el rol) y
 *     se busca el id. Si no esta, es alguien con quien no hubo clase dictada.
 *
 * Si ya habia resena, se edita (PUT); si no, se crea (POST). Al guardar
 * vuelve a la pantalla de origen, que recarga su lista sola al montarse.
 */

import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'

import { misAlumnos, misProfesores } from '../api/clases.js'
import { mensajeDeError } from '../api/mensajes.js'
import { dejarResena, editarResena } from '../api/resenas.js'
import { useAuth } from '../auth/ContextoAuth.jsx'
import Alerta from '../componentes/Alerta.jsx'
import Avatar from '../componentes/Avatar.jsx'
import { ESTRELLA, unir } from '../utiles/formato.js'

const MAX_TEXTO = 500

// Lo que dice al lado de las estrellas.
const SIGNIFICADO = { 1: 'Mala', 2: 'Regular', 3: 'Buena', 4: 'Muy buena', 5: 'Excelente' }

const FALTA_PUNTAJE = 'Elegi de 1 a 5 estrellas.'

export default function RedactarResena() {
  const { destinatarioId } = useParams()
  const { state } = useLocation()
  const navigate = useNavigate()
  const { usuario } = useAuth()
  const esProfesor = usuario.rol === 'profesor'
  const volver = state?.volver || (esProfesor ? '/agenda#alumnos' : '/mis-clases')

  const [persona, setPersona] = useState(state?.persona || null)
  const [miResena, setMiResena] = useState(state?.miResena ?? null)
  const [noEncontrada, setNoEncontrada] = useState(false)
  const [puntaje, setPuntaje] = useState(state?.miResena?.puntaje || 0)
  const [texto, setTexto] = useState(state?.miResena?.texto || '')
  const [error, setError] = useState(null)
  const [guardando, setGuardando] = useState(false)

  // Sin state (se recargo la pagina): buscar a la persona en la misma lista.
  useEffect(() => {
    if (persona) return
    const lista = esProfesor ? misAlumnos() : misProfesores()
    lista
      .then((filas) => {
        const fila = filas.find((f) => String(f.persona.id) === destinatarioId)
        if (!fila) {
          setNoEncontrada(true)
          return
        }
        setPersona(fila.persona)
        setMiResena(fila.mi_resena)
        setPuntaje(fila.mi_resena?.puntaje || 0)
        setTexto(fila.mi_resena?.texto || '')
      })
      .catch((err) => setError(mensajeDeError(err.codigo)))
  }, [])

  // Al elegir estrellas se va el aviso de que faltaban (los otros errores quedan).
  function elegirPuntaje(n) {
    setPuntaje(n)
    if (error === FALTA_PUNTAJE) setError(null)
  }

  async function guardar(evento) {
    evento.preventDefault()
    if (!puntaje) {
      setError(FALTA_PUNTAJE)
      return
    }
    setError(null)
    setGuardando(true)
    const datos = { destinatario_id: Number(destinatarioId), puntaje, texto: texto.trim() || null }
    try {
      await (miResena ? editarResena(datos) : dejarResena(datos))
      navigate(volver)
    } catch (err) {
      // Ya la habia dejado (por ejemplo, desde otra pestania): se pasa a
      // editarla, y el proximo guardar es un PUT con lo que esta escrito.
      if (err.codigo === 'ya_resenado') setMiResena(datos)
      setError(mensajeDeError(err.codigo))
      setGuardando(false)
    }
  }

  if (noEncontrada) {
    return (
      <div className="resena-redactar">
        <Alerta tipo="error">{mensajeDeError('sin_clases_con_esa_persona')}</Alerta>
        <Link to={volver} className="btn btn-secondary">Volver</Link>
      </div>
    )
  }
  if (!persona) {
    return error ? <Alerta tipo="error">{error}</Alerta> : <p className="text-muted" style={{ marginTop: '40px' }}>Cargando...</p>
  }

  const nombre = [persona.nombre, persona.apellido].filter(Boolean).join(' ')

  return (
    <div className="resena-redactar">
      <div className="perfil-titulo">
        <h2>{miResena ? 'Editar tu calificacion' : `Calificar a ${persona.nombre}`}</h2>
      </div>

      <form className="panel" onSubmit={guardar} noValidate>
        <div className="resena-quien">
          <Avatar persona={persona} tamanio="mediano" />
          <div>
            <strong>{nombre}</strong>
            {persona.materias?.length > 0 && <div className="texto-chico">{unir(persona.materias)}</div>}
          </div>
        </div>

        {/* Cinco radios de verdad con forma de estrella: se recorren con las
            flechas y el lector de pantalla dice "4 estrellas, 4 de 5". */}
        <fieldset className="resena-estrellas">
          <legend>Puntaje</legend>
          <div className="resena-estrellas-fila">
            {[1, 2, 3, 4, 5].map((n) => (
              <label key={n} className={`resena-estrella${n <= puntaje ? ' resena-estrella-llena' : ''}`}>
                <input type="radio" name="puntaje" value={n} checked={puntaje === n} onChange={() => elegirPuntaje(n)} />
                <span aria-hidden="true">{ESTRELLA}</span>
                <span className="oculto-visual">{n === 1 ? '1 estrella' : `${n} estrellas`}</span>
              </label>
            ))}
            <span className="resena-significado" aria-live="polite">{SIGNIFICADO[puntaje] || ''}</span>
          </div>
        </fieldset>

        <div className="field">
          <label htmlFor="resena-texto">Comentario (opcional)</label>
          <textarea
            id="resena-texto"
            className="input resena-texto"
            value={texto}
            maxLength={MAX_TEXTO}
            onChange={(e) => setTexto(e.target.value)}
            placeholder={esProfesor ? 'Como trabaja, si viene preparado...' : 'Como explica, si te sirvio para el examen...'}
          />
          <span className="field-hint">{texto.length} de {MAX_TEXTO} caracteres</span>
        </div>

        <Alerta tipo="info">
          Tu calificacion es anonima: {persona.nombre} ve el puntaje y el comentario, nunca quien lo dejo.
        </Alerta>
        <Alerta tipo="error">{error}</Alerta>

        <div className="botonera">
          <Link to={volver} className="btn btn-secondary">Cancelar</Link>
          <button type="submit" className="btn btn-primary" disabled={guardando}>
            {guardando ? 'Guardando...' : 'Guardar calificacion'}
          </button>
        </div>
      </form>
    </div>
  )
}
