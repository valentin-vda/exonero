import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import { useAuth } from '../auth/ContextoAuth.jsx'
import {
  obtenerMejorPuntuados,
  obtenerPinesProfesores,
  obtenerProfesoresCercanos,
} from '../api/busqueda.js'
import { proximaClase } from '../api/clases.js'
import { obtenerPerfilEstudiante } from '../api/perfiles.js'
import Avatar from '../componentes/Avatar.jsx'
import MapaInicio from '../componentes/inicio/MapaInicio.jsx'
import { hora, pesos, puntaje, unir } from '../utiles/formato.js'

const ZONA = 'America/Montevideo'

function modalidadVisible(valor) {
  const nombres = {
    ambas: 'Presencial u online',
    presencial: 'Presencial',
    online: 'Online',
  }
  return nombres[valor] || valor
}

function ubicacionVisible(clase) {
  if (clase.modalidad === 'online') return 'Videollamada'
  return clase.ubicacion
}

function fechaLocal(fecha) {
  return fecha.toLocaleDateString('es-UY', { timeZone: ZONA })
}

function fechaClase(inicio) {
  const fecha = new Date(inicio)
  const texto = fecha.toLocaleDateString('es-UY', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    timeZone: ZONA,
  })
  return fechaLocal(fecha) === fechaLocal(new Date()) ? `Hoy, ${texto}` : texto
}

function finClase(clase) {
  return new Date(new Date(clase.inicio).getTime() + clase.duracion_min * 60_000).toISOString()
}

function cuentaRegresiva(minutos) {
  if (minutos <= 0) return 'AHORA'
  if (minutos < 60) return `EN ${minutos} MIN`
  const horas = Math.floor(minutos / 60)
  const resto = minutos % 60
  return `EN ${horas} H${resto ? ` ${resto} MIN` : ''}`
}

function ProximaClase({ clase, cargando, error }) {
  if (cargando) {
    return <section className="inicio-proxima inicio-proxima-vacia">Cargando próxima clase…</section>
  }

  if (error) {
    return <section className="inicio-proxima inicio-proxima-vacia">No pudimos cargar tu próxima clase.</section>
  }

  if (!clase) {
    return (
      <section className="inicio-proxima inicio-proxima-vacia">
        <div>
          <span className="inicio-kicker">PRÓXIMA CLASE</span>
          <h2>Todavía no tenés una clase confirmada</h2>
          <p>Buscá un profesor y elegí el horario que mejor te quede.</p>
        </div>
        <Link className="btn btn-primary" to="/buscar">Buscar profes</Link>
      </section>
    )
  }

  const profesor = [clase.contraparte.nombre, clase.contraparte.apellido]
    .filter(Boolean)
    .join(' ')
  const ubicacion = ubicacionVisible(clase)

  return (
    <section className="inicio-proxima">
      <div className="inicio-proxima-hora">{hora(clase.inicio)}</div>
      <div className="inicio-proxima-info">
        <span className="inicio-kicker">PRÓXIMA CLASE · {cuentaRegresiva(clase.minutos_restantes)}</span>
        <h2>{clase.materia || 'Clase particular'} con {profesor}</h2>
        <p>
          {fechaClase(clase.inicio)} · {hora(clase.inicio)} a {hora(finClase(clase))}
          {' · '}{modalidadVisible(clase.modalidad)}
          {ubicacion ? ` · ${ubicacion}` : ''}
        </p>
      </div>
      <div className="inicio-proxima-acciones">
        <span className="tag tag-neutral">Confirmada</span>
        <Link className="btn btn-secondary" to="/mensajes">Mensaje</Link>
        <Link className="btn btn-primary" to={`/mis-clases?clase=${clase.id}`}>Ver detalle</Link>
      </div>
    </section>
  )
}

function TarjetaProfesor({ profesor }) {
  return (
    <article className="inicio-profe-card">
      <div className="inicio-profe-identidad">
        <Avatar persona={profesor} />
        <div>
          <h3>{profesor.nombre} {profesor.apellido}</h3>
          <span>{unir([profesor.barrio, profesor.distancia_km != null && `${profesor.distancia_km.toLocaleString('es-UY')} km`])}</span>
        </div>
      </div>
      <div className="inicio-profe-tags">
        <span className="tag tag-accent">{profesor.materias[0] || 'Clases particulares'}</span>
        <span>{modalidadVisible(profesor.modalidad)}</span>
      </div>
      <div className="inicio-profe-datos">
        <strong>{profesor.precio_hora == null ? 'Consultar' : `${pesos(profesor.precio_hora)}/h`}</strong>
        <span>★ {puntaje(profesor.puntaje_promedio)} · {profesor.cantidad_resenas} reseñas</span>
      </div>
      <Link className="btn btn-primary" to={`/profesor/${profesor.id}`}>Reservar</Link>
    </article>
  )
}

export default function InicioEstudiante() {
  const { usuario } = useAuth()
  const carrusel = useRef(null)
  const [perfil, setPerfil] = useState(null)
  const [proxima, setProxima] = useState(null)
  const [cercanos, setCercanos] = useState([])
  const [ranking, setRanking] = useState([])
  const [pines, setPines] = useState([])
  const [cargando, setCargando] = useState(true)
  const [errorProxima, setErrorProxima] = useState(false)
  const [errorCercanos, setErrorCercanos] = useState(false)
  const [puedeIrAtras, setPuedeIrAtras] = useState(false)
  const [puedeIrAdelante, setPuedeIrAdelante] = useState(false)

  useEffect(() => {
    let vigente = true

    async function cargar() {
      setCargando(true)
      const [perfilResultado, proximaResultado, pinesResultado] = await Promise.allSettled([
        obtenerPerfilEstudiante(),
        proximaClase(),
        obtenerPinesProfesores({}),
      ])
      if (!vigente) return

      const perfilActual = perfilResultado.status === 'fulfilled' ? perfilResultado.value : null
      setPerfil(perfilActual)
      if (proximaResultado.status === 'fulfilled') setProxima(proximaResultado.value)
      else setErrorProxima(true)
      if (pinesResultado.status === 'fulfilled') setPines(pinesResultado.value)

      const [cercanosResultado, rankingResultado] = await Promise.allSettled([
        perfilActual?.centro_id || perfilActual?.barrio_id
          ? obtenerProfesoresCercanos({
              centro_id: perfilActual.centro_id || undefined,
              barrio: perfilActual.barrio_id || undefined,
              limite: 5,
            })
          : Promise.resolve([]),
        obtenerMejorPuntuados({ etapa: perfilActual?.etapa_id || undefined, limite: 3 }),
      ])
      if (!vigente) return

      if (cercanosResultado.status === 'fulfilled') setCercanos(cercanosResultado.value)
      else setErrorCercanos(true)
      if (rankingResultado.status === 'fulfilled') setRanking(rankingResultado.value)
      setCargando(false)
    }

    cargar()
    return () => { vigente = false }
  }, [])

  useEffect(() => {
    const elemento = carrusel.current
    if (!elemento) return undefined

    function actualizarFlechas() {
      const margen = 4
      setPuedeIrAtras(elemento.scrollLeft > margen)
      setPuedeIrAdelante(
        elemento.scrollLeft + elemento.clientWidth < elemento.scrollWidth - margen,
      )
    }

    const cuadro = requestAnimationFrame(actualizarFlechas)
    elemento.addEventListener('scroll', actualizarFlechas, { passive: true })
    window.addEventListener('resize', actualizarFlechas)

    return () => {
      cancelAnimationFrame(cuadro)
      elemento.removeEventListener('scroll', actualizarFlechas)
      window.removeEventListener('resize', actualizarFlechas)
    }
  }, [cercanos])

  function moverCarrusel(direccion) {
    carrusel.current?.scrollBy({ left: direccion * 320, behavior: 'smooth' })
  }

  const datosEstudiante = usuario?.estudiante || {}

  return (
    <div className="inicio-pagina">
      <div className="inicio-superior">
        <header className="inicio-saludo">
          <h1>¡Hola {usuario?.nombre}!</h1>
        </header>

        <ProximaClase clase={proxima} cargando={cargando} error={errorProxima} />
      </div>

      <div className="inicio-mapa-con-accion">
        <MapaInicio
          pines={pines}
          rankingIds={ranking.map((profesor) => profesor.id)}
          ubicacion={perfil}
        />
        <Link className="inicio-reservar-ya" to="/buscar">Reservar</Link>
      </div>

      <section className="inicio-seccion">
        <div className="inicio-seccion-cabecera">
          <h2>Profes cerca de ti</h2>
          <span className="inicio-cercanos-cantidad">5 más cercanos</span>
        </div>

        {errorCercanos ? (
          <div className="inicio-estado">No pudimos cargar los profesores cercanos.</div>
        ) : cercanos.length ? (
          <div className="inicio-carrusel-marco">
            {puedeIrAtras && (
              <button
                type="button"
                className="inicio-carrusel-flecha anterior"
                aria-label="Profesores anteriores"
                onClick={() => moverCarrusel(-1)}
              >
                ‹
              </button>
            )}
            <div className="inicio-carrusel" ref={carrusel}>
              {cercanos.map((profesor) => <TarjetaProfesor profesor={profesor} key={profesor.id} />)}
            </div>
            {puedeIrAdelante && (
              <button
                type="button"
                className="inicio-carrusel-flecha siguiente"
                aria-label="Profesores siguientes"
                onClick={() => moverCarrusel(1)}
              >
                ›
              </button>
            )}
          </div>
        ) : (
          <div className="inicio-estado">
            {cargando
              ? 'Buscando profesores cerca…'
              : 'Completá tu barrio o centro educativo para ver profesores cercanos.'}
          </div>
        )}
      </section>

      <section className="inicio-seccion inicio-ranking-seccion">
        <div className="inicio-seccion-cabecera inicio-ranking-cabecera">
          <h2>Los 3 mejor rankeados del momento</h2>
          <span>últimas 4 semanas · {datosEstudiante.etapa || 'todas las etapas'}</span>
        </div>

        {ranking.length ? (
          <div className="inicio-ranking">
            {ranking.map((profesor, indice) => (
              <article className="inicio-ranking-card" key={profesor.id}>
                <strong className="inicio-ranking-posicion">{indice + 1}</strong>
                <div>
                  <h3>{profesor.nombre} {profesor.apellido}</h3>
                  <p>{unir([profesor.materias[0], profesor.barrio, `★ ${puntaje(profesor.puntaje_promedio)} con ${profesor.cantidad_resenas} reseñas`])}</p>
                </div>
                <Link className="btn btn-secondary" to={`/profesor/${profesor.id}`}>Ver</Link>
              </article>
            ))}
          </div>
        ) : (
          <div className="inicio-estado">El ranking aparecerá cuando haya profesores con al menos cinco reseñas.</div>
        )}
      </section>
    </div>
  )
}
