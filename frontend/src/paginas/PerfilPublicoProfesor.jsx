import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { obtenerDisponibilidad } from '../api/agenda.js'
import { obtenerMejorPuntuados } from '../api/busqueda.js'
import { cotizar } from '../api/clases.js'
import { mensajeDeError } from '../api/mensajes.js'
import { obtenerFichaPublica, obtenerPerfilEstudiante } from '../api/perfiles.js'
import { obtenerResenas } from '../api/resenas.js'
import Avatar from '../componentes/Avatar.jsx'
import BotonMensaje from '../componentes/BotonMensaje.jsx'
import MapaUbicacionProfesor from '../componentes/perfil-publico/MapaUbicacionProfesor.jsx'
import { ESTRELLA, pesos, puntaje, unir } from '../utiles/formato.js'

const DIAS = ['lun', 'mar', 'mié', 'jue', 'vie', 'sáb', 'dom']

function isoLocal(fecha) {
  const anio = fecha.getFullYear()
  const mes = String(fecha.getMonth() + 1).padStart(2, '0')
  const dia = String(fecha.getDate()).padStart(2, '0')
  return `${anio}-${mes}-${dia}`
}

function semana(numero) {
  const inicio = new Date()
  inicio.setHours(12, 0, 0, 0)
  const desdeLunes = (inicio.getDay() + 6) % 7
  inicio.setDate(inicio.getDate() - desdeLunes + numero * 7)
  const dias = Array.from({ length: 7 }, (_, indice) => {
    const fecha = new Date(inicio)
    fecha.setDate(inicio.getDate() + indice)
    return fecha
  })
  return { inicio, fin: dias[6], dias }
}

function mesCorto(fecha) {
  return fecha.toLocaleDateString('es-UY', { day: 'numeric', month: 'short' })
}

function hora(fechaIso) {
  return new Date(fechaIso).toLocaleTimeString('es-UY', {
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
    timeZone: 'America/Montevideo',
  })
}

function modalidades(ficha) {
  if (ficha.modalidad === 'ambas') return ['presencial', 'online']
  return [ficha.modalidad]
}

function modalidadVisible(valor) {
  return valor === 'online' ? 'Online' : 'Presencial'
}

function lugarVisible(ficha) {
  const textos = {
    espacio_propio: ficha.direccion_espacio
      ? `En su espacio, ${ficha.direccion_espacio}.`
      : 'En su propio espacio de estudio.',
    a_domicilio: `Se traslada a domicilio${ficha.zonas_traslado.length ? ` por ${ficha.zonas_traslado.join(', ')}` : ''}.`,
    ambos: `En su espacio${ficha.direccion_espacio ? `, ${ficha.direccion_espacio}` : ''}, o a domicilio.`,
    espacio_publico: 'En un espacio público acordado con el estudiante.',
  }
  return textos[ficha.lugar_clase] || 'El lugar se acuerda con el profesor.'
}

function duracionVisible(minutos) {
  if (minutos < 60) return `${minutos} min`
  return `${(minutos / 60).toLocaleString('es-UY', { maximumFractionDigits: 1 })} h`
}

function selectorClase(claseBase, activo) {
  return `${claseBase}${activo ? ' esta-activo' : ''}`
}

export default function PerfilPublicoProfesor() {
  const { id } = useParams()
  const navegar = useNavigate()
  const [ficha, setFicha] = useState(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')
  const [materiaId, setMateriaId] = useState(null)
  const [modalidad, setModalidad] = useState(null)
  const [duracion, setDuracion] = useState(60)
  const [semanaNumero, setSemanaNumero] = useState(0)
  const [diasDisponibles, setDiasDisponibles] = useState([])
  const [agendaNoDisponible, setAgendaNoDisponible] = useState(false)
  const [horario, setHorario] = useState(null)
  const [cotizacion, setCotizacion] = useState(null)
  const [resenas, setResenas] = useState([])
  const [ordenResenas, setOrdenResenas] = useState('recientes')
  const [puestoRanking, setPuestoRanking] = useState(null) // 1, 2 o 3 si esta en el podio

  const fechas = useMemo(() => semana(semanaNumero), [semanaNumero])

  useEffect(() => {
    let vigente = true
    setCargando(true)
    setError('')
    obtenerFichaPublica(id)
      .then((datos) => {
        if (!vigente) return
        setFicha(datos)
        setMateriaId(datos.materias[0]?.id ?? null)
        setModalidad(modalidades(datos)[0])
        setDuracion(datos.duraciones[0] || 60)
      })
      .catch((errorRecibido) => {
        if (vigente) setError(mensajeDeError(errorRecibido.codigo))
      })
      .finally(() => vigente && setCargando(false))
    return () => { vigente = false }
  }, [id])

  // Si el profe esta en el podio de "los mejor rankeados del momento", la
  // ficha sale con detalles dorados. Es el MISMO podio de la pantalla de
  // inicio (la etapa del alumno, los tres primeros), asi lo que el alumno ve
  // alla coincide con lo que ve aca. Si algo falla, la ficha sale normal.
  useEffect(() => {
    let vigente = true
    setPuestoRanking(null)
    obtenerPerfilEstudiante()
      .catch(() => null)
      .then((perfil) => obtenerMejorPuntuados({ etapa: perfil?.etapa_id || undefined, limite: 3 }))
      .then((podio) => {
        if (!vigente) return
        const indice = podio.findIndex((profesor) => profesor.id === Number(id))
        setPuestoRanking(indice >= 0 ? indice + 1 : null)
      })
      .catch(() => {})
    return () => { vigente = false }
  }, [id])

  useEffect(() => {
    if (!ficha) return undefined
    let vigente = true
    obtenerDisponibilidad(
      ficha.id,
      isoLocal(fechas.inicio),
      isoLocal(fechas.fin),
      duracion,
    )
      .then((datos) => {
        if (!vigente) return
        setDiasDisponibles(datos)
        setAgendaNoDisponible(false)
      })
      .catch(() => {
        if (!vigente) return
        setDiasDisponibles([])
        setAgendaNoDisponible(true)
      })
    return () => { vigente = false }
  }, [ficha, fechas, duracion])

  useEffect(() => {
    if (!ficha || !modalidad) return undefined
    let vigente = true
    setCotizacion(null)
    cotizar({
      profesor_id: ficha.id,
      duracion_min: duracion,
      modalidad,
      con_traslado: false,
    })
      .then((datos) => vigente && setCotizacion(datos))
      .catch(() => vigente && setCotizacion(null))
    return () => { vigente = false }
  }, [ficha, duracion, modalidad])

  useEffect(() => {
    if (!ficha) return undefined
    let vigente = true
    obtenerResenas(ficha.id, ordenResenas)
      .then((datos) => vigente && setResenas(datos.resenas || []))
      .catch(() => vigente && setResenas([]))
    return () => { vigente = false }
  }, [ficha, ordenResenas])

  useEffect(() => {
    setHorario(null)
  }, [semanaNumero, duracion])

  if (cargando) return <p className="publico-estado">Cargando perfil…</p>
  if (error || !ficha) {
    return (
      <section className="panel publico-error">
        <h4>No pudimos abrir este perfil</h4>
        <p>{error || 'El profesor no está disponible.'}</p>
        <Link className="btn btn-primary" to="/buscar">Volver a la búsqueda</Link>
      </section>
    )
  }

  const modos = modalidades(ficha)
  const materia = ficha.materias.find((item) => item.id === materiaId)
  const diasPorFecha = new Map(diasDisponibles.map((dia) => [dia.fecha, dia.huecos]))
  const precioCabecera = modalidad === 'online'
    ? ficha.precio_hora_online
    : ficha.precio_hora_presencial
  const estrellas = ESTRELLA.repeat(Math.max(0, Math.min(5, Math.round(Number(ficha.puntaje_promedio)))))
  const esPresencial = modos.includes('presencial')
  const esOnline = modos.includes('online')

  function reservar() {
    if (!horario || !materia || !modalidad) return
    const parametros = new URLSearchParams({
      profesor: ficha.id,
      materia: materia.id,
      inicio: horario.inicio,
      duracion,
      modalidad,
    })
    navegar(`/checkout?${parametros}`)
  }

  return (
    <div className="perfil-publico">
      <Link to="/buscar" className="publico-volver">‹ Volver a la búsqueda</Link>

      <header className={`publico-cabecera${puestoRanking ? ' publico-cabecera-dorada' : ''}`}>
        <div className="publico-avatar"><Avatar persona={ficha} tamanio="grande" /></div>
        <div className="publico-identidad">
          {puestoRanking && (
            <span className="publico-medalla">
              <span className="publico-medalla-puesto">{puestoRanking}</span>
              Mejor rankeado del momento
            </span>
          )}
          <h1>{ficha.nombre} {ficha.apellido}</h1>
          <p>{unir([ficha.materias.map((item) => item.nombre).join(', '), ficha.barrio && `${ficha.barrio}, Montevideo`])}</p>
          <div className="publico-etiquetas">
            {ficha.materias.map((item) => <span className="tag tag-accent" key={item.id}>{item.nombre}</span>)}
            {ficha.etapas.map((item) => <span className="tag tag-neutral" key={item.id}>{item.nombre}</span>)}
            <span className="tag tag-accent-2">{modos.map(modalidadVisible).join(' u ')}</span>
          </div>
          <div className="publico-metricas">
            <div><strong>{ficha.anios_experiencia ?? 0} años</strong><span>de experiencia</span></div>
            <div><strong>{ficha.clases_dictadas}</strong><span>dictadas en Exonero</span></div>
            <div><strong>{ficha.titulo_habilitante || 'Docente'}</strong><span>título habilitante</span></div>
          </div>
        </div>
        <div className="publico-precio">
          <strong>{precioCabecera == null ? 'Consultar' : pesos(precioCabecera)}</strong>
          <span>por hora</span>
          <div className="publico-estrellas" aria-label={`${puntaje(ficha.puntaje_promedio)} de 5`}>{estrellas || '☆'}</div>
          <div><b>{puntaje(ficha.puntaje_promedio)}</b> <span>{ficha.cantidad_resenas} reseñas</span></div>
        </div>
      </header>

      <div className="publico-columnas">
        <div className="publico-principal">
          <section className="publico-panel publico-disponibilidad">
            <div className="publico-panel-cabecera">
              <h2>Disponibilidad</h2>
              <div className="publico-semana-controles">
                <button type="button" className="btn btn-secondary btn-icon" disabled={semanaNumero === 0} onClick={() => setSemanaNumero((n) => n - 1)}>‹</button>
                <span>{mesCorto(fechas.inicio)} – {mesCorto(fechas.fin)}</span>
                <button type="button" className="btn btn-secondary btn-icon" onClick={() => setSemanaNumero((n) => n + 1)}>›</button>
              </div>
            </div>
            <p className="publico-ayuda">Elegí un horario para reservar. Solo se muestran los que siguen libres.</p>
            <div className="publico-calendario">
              {fechas.dias.map((fecha, indice) => {
                const huecos = diasPorFecha.get(isoLocal(fecha)) || []
                return (
                  <div className="publico-dia" key={isoLocal(fecha)}>
                    <div className="publico-dia-cabecera"><span>{DIAS[indice]}</span><strong>{fecha.getDate()}</strong></div>
                    {huecos.map((hueco) => (
                      <button
                        type="button"
                        className={selectorClase('publico-horario', horario?.inicio === hueco.inicio)}
                        key={hueco.inicio}
                        onClick={() => setHorario(hueco)}
                      >
                        {hora(hueco.inicio)}
                      </button>
                    ))}
                    {!agendaNoDisponible && huecos.length === 0 && <span className="publico-sin-horario">—</span>}
                  </div>
                )
              })}
            </div>
            {agendaNoDisponible && (
              <div className="publico-aviso-agenda">La agenda todavía no publicó horarios disponibles.</div>
            )}
            <div className="publico-reserva-pie">
              <div>
                <strong>{horario ? `${mesCorto(new Date(horario.inicio))}, ${hora(horario.inicio)}` : 'Elegí un horario'}</strong>
                <span>{unir([materia?.nombre, duracionVisible(duracion), modalidadVisible(modalidad)])}</span>
              </div>
              <button type="button" className="publico-reservar" disabled={!horario} onClick={reservar}>Reservar</button>
            </div>
          </section>

          <section className="publico-panel">
            <h2>Modalidad y zona</h2>
            <div className="publico-modalidades">
              {esPresencial && <article className="publico-modalidad presencial"><h3>Presencial</h3><p>{lugarVisible(ficha)}</p></article>}
              {esOnline && <article className="publico-modalidad online"><h3>Online</h3><p>Por videollamada, con material y ejercicios compartidos.</p></article>}
            </div>

            {esPresencial && (
              <>
                <h2 className="publico-subtitulo">El lugar donde doy clase</h2>
                {ficha.fotos.length === 0 ? (
                  <div className="publico-fotos-vacio">No se cargaron fotos del lugar.</div>
                ) : (
                  <div className="publico-galeria">
                    {ficha.fotos.slice(0, 4).map((foto, indice) => {
                      const esUnica = ficha.fotos.length === 1
                      const posicion = esUnica
                        ? ' unica'
                        : indice === 0
                          ? ' principal'
                          : indice === 3
                            ? ' entrada'
                            : ''
                      return (
                        <figure className={`publico-foto${posicion}`} key={foto.id}>
                          <img
                            src={foto.imagen_base64}
                            alt={foto.epigrafe || `Foto ${indice + 1} del lugar de clase`}
                          />
                          {foto.epigrafe && <figcaption>{foto.epigrafe}</figcaption>}
                        </figure>
                      )
                    })}
                  </div>
                )}
              </>
            )}

            <h2 className="publico-subtitulo">Sobre {ficha.nombre}</h2>
            <p className="publico-biografia">{ficha.biografia || 'Este profesor todavía no agregó una biografía.'}</p>
            {ficha.puntos_metodo.length > 0 && (
              <ul className="publico-metodo">{ficha.puntos_metodo.map((punto) => <li key={punto}>{punto}</li>)}</ul>
            )}
          </section>

          <section className="publico-resenas">
            <div className="publico-panel-cabecera">
              <div className="publico-resenas-titulo"><h2>Reseñas</h2><span>{ficha.cantidad_resenas} · promedio {puntaje(ficha.puntaje_promedio)}</span></div>
              <select className="input" value={ordenResenas} onChange={(evento) => setOrdenResenas(evento.target.value)}>
                <option value="recientes">Más recientes</option>
                <option value="puntaje">Mejor puntuadas</option>
              </select>
            </div>
            <div className="publico-resenas-lista">
              {resenas.map((resena, indice) => (
                <article className="publico-resena" key={`${resena.fecha}-${indice}`}>
                  <div><strong>{ESTRELLA.repeat(resena.puntaje)}</strong><span>Reseña anónima · {new Date(`${resena.fecha}T12:00:00`).toLocaleDateString('es-UY')}</span></div>
                  <p>{resena.texto || 'Sin comentario.'}</p>
                </article>
              ))}
              {resenas.length === 0 && (
                <div className="publico-resenas-vacio">
                  {ficha.cantidad_resenas === 0
                    ? 'Este profesor todavía no tiene reseñas.'
                    : 'Las reseñas detalladas todavía no están disponibles.'}
                </div>
              )}
            </div>
          </section>
        </div>

        <aside className="publico-lateral">
          <section className="publico-resumen">
            <span className="publico-kicker">Tu reserva</span>
            <h2>{horario ? `${mesCorto(new Date(horario.inicio))}, ${hora(horario.inicio)}` : 'Elegí un horario'}</h2>
            <p>{unir([materia?.nombre, duracionVisible(duracion), modalidadVisible(modalidad)])}</p>

            <div className="publico-selectores">
              <fieldset><legend>Materia</legend><div className="publico-segmentado">{ficha.materias.map((item) => <button type="button" className={selectorClase('', item.id === materiaId)} key={item.id} onClick={() => setMateriaId(item.id)}>{item.nombre}</button>)}</div></fieldset>
              <fieldset><legend>Modalidad</legend><div className="publico-segmentado">{modos.map((item) => <button type="button" className={selectorClase('', item === modalidad)} key={item} onClick={() => setModalidad(item)}>{modalidadVisible(item)}</button>)}</div></fieldset>
              <fieldset><legend>Duración</legend><div className="publico-segmentado">{(ficha.duraciones.length ? ficha.duraciones : [60]).map((item) => <button type="button" className={selectorClase('', item === duracion)} key={item} onClick={() => setDuracion(item)}>{duracionVisible(item)}</button>)}</div></fieldset>
            </div>

            <div className="publico-total"><span>Total estimado</span><strong>{cotizacion ? pesos(cotizacion.total) : '—'}</strong></div>
            <button type="button" className="publico-reservar ancho" disabled={!horario} onClick={reservar}>Reservar</button>
            <BotonMensaje personaId={ficha.id} className="btn btn-secondary btn-block">Enviar mensaje</BotonMensaje>
          </section>

          {esPresencial && ficha.latitud != null && ficha.longitud != null && (
            <section className="publico-ubicacion">
              <h2>Dónde da clase</h2>
              <p>{unir([ficha.barrio, ficha.direccion_espacio])}</p>
              <MapaUbicacionProfesor
                latitud={ficha.latitud}
                longitud={ficha.longitud}
                nombre={ficha.nombre}
              />
            </section>
          )}
        </aside>
      </div>
    </div>
  )
}
