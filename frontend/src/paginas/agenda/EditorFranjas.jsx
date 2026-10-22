/**
 * El editor de la disponibilidad semanal. Lo usan 1i (pestania
 * Disponibilidad) y 1j (pestania Disponibilidad): es la misma pantalla
 * embebida dos veces, como pide la spec, y no se duplica nada.
 *
 *   Lunes      [14:00] a [20:00] [Presencial y online v]  x
 *              + Agregar franja
 *   Martes     No atendes este dia.  + Agregar franja
 *   ...
 *                                              [Guardar disponibilidad]
 *
 * Carga sus propias franjas (GET /api/agenda/yo/franjas) y guarda TODAS
 * juntas con PUT: el backend reemplaza la lista entera. Asi el profesor deja
 * la grilla como quiere y guarda una vez.
 *
 * Antes de mandar, revisa lo mismo que el backend (que cada franja termine
 * despues de empezar y que no se pisen dos del mismo dia) para marcar el
 * renglon con el problema. El backend lo vuelve a revisar igual.
 *
 * `alGuardar` (opcional) se llama despues de guardar: 1i lo usa para
 * redibujar el calendario.
 */

import { useEffect, useState } from 'react'

import { guardarFranjas, listarFranjas } from '../../api/agenda.js'
import { mensajeDeError } from '../../api/mensajes.js'
import Alerta from '../../componentes/Alerta.jsx'
import { CRUZ } from '../../utiles/formato.js'
import { DIAS, MODALIDADES_FRANJA } from './opciones.js'

// Igual que en SeccionBio: cada renglon lleva un id propio para el `key`.
let proximoId = 1
function renglon(franja) {
  return {
    id: proximoId++,
    dia: franja.dia_semana,
    // El backend manda '14:00:00'; el <input type="time"> quiere '14:00'.
    inicio: franja.hora_inicio.slice(0, 5),
    fin: franja.hora_fin.slice(0, 5),
    modalidad: franja.modalidad,
  }
}

/** '18:30' -> '20:30'. Solo se usa con horas hasta las 21:00, asi que no pasa de medianoche. */
function masDosHoras(hora) {
  return `${String(Number(hora.slice(0, 2)) + 2).padStart(2, '0')}${hora.slice(2)}`
}

/** Los ids de los renglones con algun problema, y el texto del primero. */
function problemas(renglones) {
  const malos = new Set()
  let texto = null
  for (const r of renglones) {
    if (!r.inicio || !r.fin || r.fin <= r.inicio) {
      malos.add(r.id)
      texto ||= 'Cada franja tiene que terminar despues de empezar.'
    }
  }
  // Las horas son 'HH:MM': compararlas como texto es compararlas como horas.
  for (const dia of DIAS) {
    const delDia = renglones.filter((r) => r.dia === dia.valor).sort((a, b) => a.inicio.localeCompare(b.inicio))
    for (let i = 1; i < delDia.length; i++) {
      if (delDia[i].inicio < delDia[i - 1].fin) {
        malos.add(delDia[i].id)
        malos.add(delDia[i - 1].id)
        texto ||= `Hay dos franjas del ${dia.texto.toLowerCase()} que se pisan.`
      }
    }
  }
  return { malos, texto }
}

export default function EditorFranjas({ alGuardar }) {
  const [renglones, setRenglones] = useState(null)
  const [errorCarga, setErrorCarga] = useState(null)
  const [mensaje, setMensaje] = useState(null)
  const [guardando, setGuardando] = useState(false)

  useEffect(() => {
    listarFranjas()
      .then((franjas) => setRenglones(franjas.map(renglon)))
      .catch((error) => setErrorCarga(mensajeDeError(error.codigo)))
  }, [])

  if (errorCarga) return <Alerta tipo="error">No pudimos traer tu disponibilidad. {errorCarga}</Alerta>
  if (!renglones) return <p className="tablero-vacio">Cargando tu disponibilidad...</p>

  const { malos, texto } = problemas(renglones)

  function cambiar(id, campo, valor) {
    setMensaje(null)
    setRenglones((lista) => lista.map((r) => (r.id === id ? { ...r, [campo]: valor } : r)))
  }

  function quitar(id) {
    setMensaje(null)
    setRenglones((lista) => lista.filter((r) => r.id !== id))
  }

  /** Una franja nueva ese dia: dos horas despues de la ultima, o de 14 a 18 si no hay. */
  function agregar(dia) {
    setMensaje(null)
    setRenglones((lista) => {
      const ultima = lista.filter((r) => r.dia === dia).sort((a, b) => a.fin.localeCompare(b.fin)).at(-1)
      const [inicio, fin] = ultima && ultima.fin <= '21:00' ? [ultima.fin, masDosHoras(ultima.fin)] : ['14:00', '18:00']
      return [...lista, renglon({ dia_semana: dia, hora_inicio: inicio, hora_fin: fin, modalidad: 'ambas' })]
    })
  }

  async function guardar(evento) {
    evento.preventDefault()
    if (texto) return
    setMensaje(null)
    setGuardando(true)
    try {
      const guardadas = await guardarFranjas(
        renglones.map((r) => ({ dia_semana: r.dia, hora_inicio: r.inicio, hora_fin: r.fin, modalidad: r.modalidad })),
      )
      setRenglones(guardadas.map(renglon))
      setMensaje({ tipo: 'ok', texto: 'Listo, se guardo tu disponibilidad.' })
      if (alGuardar) alGuardar()
    } catch (error) {
      setMensaje({ tipo: 'error', texto: mensajeDeError(error.codigo) })
    } finally {
      setGuardando(false)
    }
  }

  return (
    <form className="franjas" onSubmit={guardar} noValidate>
      <p className="panel-ayuda" style={{ marginTop: 0 }}>
        Marca cuando das clase cada semana. Los alumnos solo pueden reservar dentro de estas franjas, y
        siempre respetando tu descanso, tu tope diario y tu aviso minimo.
      </p>

      {DIAS.map((dia) => {
        const delDia = renglones.filter((r) => r.dia === dia.valor)
        return (
          <fieldset key={dia.valor} className="franjas-dia">
            <legend className="franjas-dia-nombre">{dia.texto}</legend>
            <div className="franjas-dia-renglones">
              {delDia.length === 0 && <span className="franjas-vacio">No atendes este dia.</span>}
              {delDia.map((r, posicion) => {
                const nombre = `${dia.texto}, franja ${posicion + 1}`
                return (
                  <div key={r.id} className={`franjas-renglon${malos.has(r.id) ? ' franjas-renglon-error' : ''}`}>
                    <input type="time" className="input" step="1800" value={r.inicio}
                           onChange={(e) => cambiar(r.id, 'inicio', e.target.value)}
                           aria-label={`${nombre}: desde`} aria-invalid={malos.has(r.id) || undefined} />
                    <span aria-hidden="true">a</span>
                    <input type="time" className="input" step="1800" value={r.fin}
                           onChange={(e) => cambiar(r.id, 'fin', e.target.value)}
                           aria-label={`${nombre}: hasta`} aria-invalid={malos.has(r.id) || undefined} />
                    <select className="input" value={r.modalidad} onChange={(e) => cambiar(r.id, 'modalidad', e.target.value)}
                            aria-label={`${nombre}: modalidad`}>
                      {MODALIDADES_FRANJA.map((m) => <option key={m.valor} value={m.valor}>{m.texto}</option>)}
                    </select>
                    <button type="button" className="btn btn-ghost" onClick={() => quitar(r.id)} aria-label={`Quitar ${nombre}`}>
                      {CRUZ}
                    </button>
                  </div>
                )
              })}
              <button type="button" className="btn btn-ghost franjas-agregar" onClick={() => agregar(dia.valor)}>
                + Agregar franja
              </button>
            </div>
          </fieldset>
        )
      })}

      {texto && <Alerta tipo="error">{texto}</Alerta>}
      <Alerta tipo={mensaje?.tipo}>{mensaje?.texto}</Alerta>
      <Alerta tipo="info">
        Achicar tu disponibilidad no cancela las clases que ya confirmaste: esas siguen en pie.
      </Alerta>

      <div className="botonera">
        <button type="submit" className="btn btn-primary" disabled={guardando || Boolean(texto)}>
          {guardando ? 'Guardando...' : 'Guardar disponibilidad'}
        </button>
      </div>
    </form>
  )
}
