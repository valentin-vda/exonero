/**
 * El calendario semanal de 1i, con GET /api/agenda/yo/semana:
 *
 *   [<] Semana del 19 al 25 de octubre [>] [Hoy]     [ ] Ver como lo ve el alumno
 *          lun 19   mar 20   mie 21   jue 22   vie 23   sab 24   dom 25
 *   14:00  |....|   |####|   |....|   |xxxx|   |====|
 *   15:00  |....|   |####|   |....|   |xxxx|   |....|
 *   ...
 *   (.... disponible  #### confirmada  ==== a confirmar  xxxx bloqueo)
 *
 * El fondo de cada columna son las franjas de ese dia de la semana (lo que el
 * profesor dijo que puede). Encima van las clases y los bloqueos, en su hora.
 * Con "Ver como lo ve el alumno" se suman los huecos libres que devuelve
 * GET /agenda/profesores/{yo}/disponibilidad: lo mismo que ve el alumno en
 * 1f, ya descontado todo.
 *
 * Tocar una clase avisa a la pantalla (`alElegirClase`), que muestra sus
 * acciones abajo del calendario.
 *
 * Todas las horas son de Montevideo (formato.js y fechas.js), no las de la
 * computadora. En el celular la grilla no entra: se muestra una lista por dia
 * (ver agenda.css).
 */

import Alerta from '../../componentes/Alerta.jsx'
import { hora } from '../../utiles/formato.js'
import { ESTADOS_CLASE } from '../panel/opciones.js'
import { diaEnMontevideo, hoy, lunesDe, sumarDias } from '../panel/fechas.js'
import { DIAS } from './opciones.js'

// Cuantos pixeles mide una hora en la grilla.
const ALTO_HORA = 44

/** '14:30' -> 870 (minutos desde la medianoche). */
function aMinutos(hhmm) {
  const [h, m] = hhmm.split(':').map(Number)
  return h * 60 + m
}

/** 870 -> '14:30'. */
function aHora(minutos) {
  return `${String(Math.floor(minutos / 60)).padStart(2, '0')}:${String(minutos % 60).padStart(2, '0')}`
}

/**
 * Lo que ocupa un rango [inicio, fin) dentro de un dia, en minutos de ese dia.
 * Un bloqueo de varios dias se corta: el primer dia va de su hora a la
 * medianoche, los del medio enteros y el ultimo desde las 0. Las fechas
 * 'AAAA-MM-DD' se comparan como texto.
 */
function tramoDelDia(inicioIso, finIso, dia) {
  const diaInicio = diaEnMontevideo(inicioIso)
  const diaFin = diaEnMontevideo(finIso)
  if (diaInicio > dia || diaFin < dia) return null
  const desde = diaInicio < dia ? 0 : aMinutos(hora(inicioIso))
  const hasta = diaFin > dia ? 24 * 60 : aMinutos(hora(finIso))
  return hasta > desde ? { desde, hasta } : null
}

/** "Semana del 19 al 25 de octubre" (o "del 28 de octubre al 3 de noviembre"). */
function tituloSemana(desde) {
  const formato = (dia, conMes) =>
    new Date(`${dia}T12:00:00Z`).toLocaleDateString('es-UY', { day: 'numeric', ...(conMes && { month: 'long' }), timeZone: 'UTC' })
  const hasta = sumarDias(desde, 6)
  const mismoMes = desde.slice(0, 7) === hasta.slice(0, 7)
  return `Semana del ${formato(desde, !mismoMes)} al ${formato(hasta, true)}`
}

/** Todo lo que se dibuja en un dia: clases, bloqueos y (si se piden) huecos. */
function itemsDelDia(dia, semana, huecos) {
  const items = []
  for (const [lista, tipo] of [[semana.aprobadas, 'aprobada'], [semana.pendientes, 'pendiente'], [semana.cerradas, 'cerrada']]) {
    for (const clase of lista) {
      const fin = new Date(new Date(clase.inicio).getTime() + clase.duracion_min * 60000).toISOString()
      const tramo = tramoDelDia(clase.inicio, fin, dia)
      if (tramo) items.push({ ...tramo, tipo, clase, clave: `c${clase.id}` })
    }
  }
  for (const b of semana.bloqueos) {
    const tramo = tramoDelDia(b.inicio, b.fin, dia)
    if (tramo) items.push({ ...tramo, tipo: 'bloqueo', bloqueo: b, clave: `b${b.id}` })
  }
  for (const h of huecos?.find((d) => d.fecha === dia)?.huecos || []) {
    const tramo = tramoDelDia(h.inicio, h.fin, dia)
    if (tramo) items.push({ ...tramo, tipo: 'hueco', clave: `h${h.inicio}` })
  }
  return items.sort((a, b) => a.desde - b.desde)
}

/** De que hora a que hora se dibuja la grilla: lo que haya, con un margen. Por defecto, 8 a 21. */
function rangoDeHoras(franjas, todos) {
  let desde = 8 * 60
  let hasta = 21 * 60
  for (const f of franjas) {
    desde = Math.min(desde, aMinutos(f.hora_inicio))
    hasta = Math.max(hasta, aMinutos(f.hora_fin))
  }
  for (const item of todos) {
    desde = Math.min(desde, item.desde)
    hasta = Math.max(hasta, item.hasta)
  }
  return [Math.floor(desde / 60), Math.min(24, Math.ceil(hasta / 60))]
}

function textoItem(item) {
  if (item.tipo === 'bloqueo') return item.bloqueo.motivo || 'Bloqueado'
  if (item.tipo === 'hueco') return 'Libre'
  const alumno = item.clase.contraparte
  return [alumno.nombre, alumno.apellido].filter(Boolean).join(' ')
}

function Item({ item, inicioGrilla, seleccionada, alElegirClase }) {
  const estilo = {
    top: `${((item.desde - inicioGrilla) / 60) * ALTO_HORA}px`,
    height: `${Math.max(((item.hasta - item.desde) / 60) * ALTO_HORA - 2, 14)}px`,
  }
  const rango = aHora(item.desde)
  if (!item.clase) {
    return (
      <div className={`cal-item cal-${item.tipo}`} style={estilo} title={`${rango} ${textoItem(item)}`}>
        <span className="cal-item-texto">{textoItem(item)}</span>
      </div>
    )
  }
  const estado = ESTADOS_CLASE[item.clase.estado]?.texto || item.clase.estado
  return (
    <button
      type="button"
      className={`cal-item cal-${item.tipo}${seleccionada ? ' cal-elegida' : ''}`}
      style={estilo}
      onClick={() => alElegirClase(item.clase)}
      aria-pressed={seleccionada}
      aria-label={`${rango}, ${textoItem(item)}, ${item.clase.materia || ''}, ${estado}`}
    >
      <span className="cal-item-hora">{hora(item.clase.inicio)}</span>
      <span className="cal-item-texto">{textoItem(item)}</span>
    </button>
  )
}

export default function CalendarioSemanal({
  desde, alCambiarSemana, bloque, franjas, huecos, verHuecos, alCambiarVerHuecos, elegida, alElegirClase,
}) {
  const { datos: semana, error, cargando } = bloque
  const dias = DIAS.map((d, i) => ({ ...d, fecha: sumarDias(desde, i) }))
  const porDia = semana ? dias.map((d) => itemsDelDia(d.fecha, semana, verHuecos ? huecos : null)) : []
  const [horaDesde, horaHasta] = rangoDeHoras(franjas || [], porDia.flat())
  const horas = Array.from({ length: horaHasta - horaDesde }, (_, i) => horaDesde + i)
  const hoyDia = hoy()

  return (
    <section className="tablero-bloque" aria-labelledby="calendario-titulo">
      <div className="tablero-encabezado">
        <div className="cal-navegacion">
          <button type="button" className="btn btn-secondary" onClick={() => alCambiarSemana(sumarDias(desde, -7))}
                  aria-label="Semana anterior">{'‹'}</button>
          <h3 id="calendario-titulo">{tituloSemana(desde)}</h3>
          <button type="button" className="btn btn-secondary" onClick={() => alCambiarSemana(sumarDias(desde, 7))}
                  aria-label="Semana siguiente">{'›'}</button>
          {desde !== lunesDe(hoyDia) && (
            <button type="button" className="btn btn-ghost" onClick={() => alCambiarSemana(lunesDe(hoyDia))}>Hoy</button>
          )}
        </div>
        <label className="cal-ver-huecos">
          <input type="checkbox" checked={verHuecos} onChange={(e) => alCambiarVerHuecos(e.target.checked)} />
          Ver como lo ve el alumno
        </label>
      </div>

      {error && <Alerta tipo="error">No pudimos traer tu semana. {error}</Alerta>}
      {!semana && cargando && <p className="tablero-vacio">Cargando tu semana...</p>}

      {semana && (
        <div className={cargando ? 'tablero-recargando' : undefined}>
          {/* La grilla: escritorio y tablet */}
          <div className="cal-grilla">
            <div className="cal-horas" style={{ paddingTop: 'var(--cal-cabecera)' }}>
              {horas.map((h) => (
                <div key={h} className="cal-hora" style={{ height: ALTO_HORA }}>{aHora(h * 60)}</div>
              ))}
            </div>
            {dias.map((d, i) => (
              <div key={d.fecha} className={`cal-dia${d.fecha === hoyDia ? ' cal-hoy' : ''}`}>
                <div className="cal-dia-cabecera">
                  <span>{d.corto}</span> <strong>{Number(d.fecha.slice(8))}</strong>
                </div>
                <div className="cal-dia-cuerpo" style={{ height: horas.length * ALTO_HORA }}>
                  {(franjas || []).filter((f) => f.dia_semana === d.valor && f.activa).map((f) => (
                    <div
                      key={f.id}
                      className="cal-franja"
                      style={{
                        top: `${((aMinutos(f.hora_inicio) - horaDesde * 60) / 60) * ALTO_HORA}px`,
                        height: `${((aMinutos(f.hora_fin) - aMinutos(f.hora_inicio)) / 60) * ALTO_HORA}px`,
                      }}
                    />
                  ))}
                  {porDia[i].map((item) => (
                    <Item key={item.clave} item={item} inicioGrilla={horaDesde * 60}
                          seleccionada={item.clase && elegida?.id === item.clase.id} alElegirClase={alElegirClase} />
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* La lista: celular */}
          <ol className="cal-lista">
            {dias.map((d, i) => {
              const items = porDia[i].filter((item) => item.tipo !== 'hueco' || verHuecos)
              return (
                <li key={d.fecha} className={d.fecha === hoyDia ? 'cal-hoy' : undefined}>
                  <div className="cal-lista-dia">{d.texto} {Number(d.fecha.slice(8))}</div>
                  {items.length === 0 && <span className="tablero-vacio">Nada agendado.</span>}
                  {items.map((item) => (
                    item.clase ? (
                      <button key={item.clave} type="button" className={`cal-lista-item cal-${item.tipo}`}
                              onClick={() => alElegirClase(item.clase)}>
                        <strong>{hora(item.clase.inicio)}</strong> {textoItem(item)} {item.clase.materia && `· ${item.clase.materia}`}
                      </button>
                    ) : (
                      <div key={item.clave} className={`cal-lista-item cal-${item.tipo}`}>
                        <strong>{aHora(item.desde)}</strong>{' '}
                        {textoItem(item)}
                      </div>
                    )
                  ))}
                </li>
              )
            })}
          </ol>

          <ul className="cal-leyenda" aria-label="Referencias">
            <li><i className="cal-franja" /> Tu disponibilidad</li>
            <li><i className="cal-aprobada" /> Confirmada</li>
            <li><i className="cal-pendiente" /> A confirmar</li>
            <li><i className="cal-cerrada" /> Dictada o no asistio</li>
            <li><i className="cal-bloqueo" /> Bloqueo</li>
            {verHuecos && <li><i className="cal-hueco" /> Libre para el alumno (1 h)</li>}
          </ul>
        </div>
      )}
    </section>
  )
}
