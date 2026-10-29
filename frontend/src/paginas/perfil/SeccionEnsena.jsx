/**
 * La pestania "Materias y modalidad" de 1j. Es la mas larga del perfil.
 *
 * Dos tarjetas y un solo boton de guardar, como en el mockup:
 *
 *   Materias y niveles   materias, etapas, programa e idiomas
 *   Modalidad            como y donde da clase, precios, duraciones,
 *                        descanso, tope diario, aviso minimo y formato
 *
 * El backend tiene un endpoint por cada parte, asi que "Guardar cambios"
 * hace cuatro llamadas seguidas:
 *
 *   PUT .../oferta     materias, etapas (con su programa), idiomas
 *   PUT .../modalidad  modalidad, lugar, direccion, zonas, costo de traslado
 *   PUT .../precios    precio presencial y online
 *   PUT .../reglas     duraciones, descanso, tope, aviso, formato y cupos
 *
 * Si una falla, las anteriores ya quedaron guardadas: se muestra el error y
 * al volver a guardar se manda todo de nuevo (cada PUT reemplaza lo que habia,
 * asi que repetirlo no duplica nada).
 *
 * Varios campos aparecen o desaparecen segun lo elegido (si das clase solo
 * online, no hace falta el precio presencial). Eso se hace con && en el JSX:
 * {condicion && <loQueSeMuestra />}.
 */

import { useState } from 'react'

import { mensajeDeError } from '../../api/mensajes.js'
import { guardarModalidad, guardarOferta, guardarPrecios, guardarReglas } from '../../api/perfiles.js'
import Alerta from '../../componentes/Alerta.jsx'
import Campo from '../../componentes/Campo.jsx'
import CampoSelect from '../../componentes/CampoSelect.jsx'
import ListaEtiquetas from '../../componentes/ListaEtiquetas.jsx'
import { aNumero, aTexto } from '../../utiles/formato.js'
import { validarFormulario } from '../../utiles/validaciones.js'
import {
  AVISOS,
  DESCANSOS,
  DURACIONES,
  FORMATOS,
  LUGARES,
  MODALIDADES,
  PROGRAMAS,
} from './opciones.js'

/** Los valores del formulario a partir de la ficha (MiFichaOut). */
function valoresIniciales(ficha) {
  return {
    materias: ficha.materias.map((m) => m.id),
    etapas: ficha.etapas.map((e) => e.id),
    // El mockup tiene UN desplegable de programa: se toma el de la primera
    // etapa que tenga, y al guardar se aplica a todas.
    programa: ficha.etapas.find((e) => e.programa)?.programa || '',
    idiomas: ficha.idioma_ids,
    modalidad: ficha.modalidad,
    lugar: ficha.lugar_clase,
    direccion: ficha.direccion_espacio || '',
    zonas: ficha.zona_ids,
    // Los importes llegan como texto con decimales ("900.00"). aNumero los
    // pasa a 900 y aTexto de vuelta a "900", que es lo que se ve en el campo.
    costoTraslado: aTexto(aNumero(ficha.costo_traslado)),
    precioPresencial: aTexto(aNumero(ficha.precio_hora_presencial)),
    precioOnline: aTexto(aNumero(ficha.precio_hora_online)),
    duracionMin: aTexto(ficha.duracion_min),
    duracionMax: aTexto(ficha.duracion_max),
    duraciones: ficha.duraciones, // numeros: [60, 90]
    descanso: aTexto(ficha.descanso_min),
    maxClasesDia: aTexto(ficha.max_clases_dia),
    aviso: aTexto(ficha.aviso_minimo_horas),
    formato: ficha.formato,
    cupoMin: aTexto(ficha.cupo_min),
    cupoMax: aTexto(ficha.cupo_max),
  }
}

/**
 * {id: nombre} para mostrar lo elegido aunque no hayan cargado los
 * catalogos. Recibe dos listas paralelas: [1, 2] y ['Espanol', 'Ingles'].
 */
function nombresPorId(ids, nombres) {
  return Object.fromEntries(ids.map((id, i) => [id, nombres[i]]))
}

/** Agrega el valor si no esta, o lo saca si esta. Para casillas y botones. */
function alternar(lista, valor) {
  return lista.includes(valor) ? lista.filter((x) => x !== valor) : [...lista, valor]
}

export default function SeccionEnsena({ ficha, catalogos, alGuardar }) {
  const [campos, setCampos] = useState(() => valoresIniciales(ficha))
  const [errores, setErrores] = useState({})
  const [mensaje, setMensaje] = useState(null)
  const [guardando, setGuardando] = useState(false)

  function cambiar(campo) {
    return (valor) => setCampos((previos) => ({ ...previos, [campo]: valor }))
  }

  // --- Lo que se deriva de lo elegido (se recalcula en cada render) -------
  const daPresencial = campos.modalidad !== 'online'
  const daOnline = campos.modalidad !== 'presencial'
  const vaADomicilio = campos.lugar === 'a_domicilio' || campos.lugar === 'ambos'
  const tieneEspacio = campos.lugar !== 'a_domicilio'
  const haceGrupales = campos.formato !== 'individual'

  const minimo = Number(campos.duracionMin)
  const maximo = Number(campos.duracionMax)
  // Solo se pueden ofrecer las duraciones que caen entre la minima y la maxima.
  const duracionesPosibles = DURACIONES.filter((d) => d.valor >= minimo && d.valor <= maximo)

  // Las etapas para las casillas: las del catalogo, o (plan B) las que ya tenia.
  const etapasParaElegir = catalogos ? catalogos.etapas : ficha.etapas

  // El programa actual puede no estar en la lista fija (si lo cargo otro
  // sistema, por ejemplo): se agrega para no perderlo.
  const programas = PROGRAMAS.includes(campos.programa) || !campos.programa
    ? PROGRAMAS
    : [campos.programa, ...PROGRAMAS]

  async function guardar(evento) {
    evento.preventDefault()
    setMensaje(null)

    // Lo que vale la pena chequear antes de llamar: el resto lo valida el
    // backend y el error vuelve con su codigo. Los precios van antes que
    // nada: si fallaran en PUT .../precios, la oferta y la modalidad ya
    // habrian quedado guardadas.
    const negativo = (valor) => (valor !== '' && Number(valor) < 0 ? 'No puede ser negativo.' : null)
    const { errores: nuevos, hayErrores } = validarFormulario({
      precioPresencial: () => (daPresencial ? negativo(campos.precioPresencial) : null),
      precioOnline: () => (daOnline ? negativo(campos.precioOnline) : null),
    })
    setErrores(nuevos)
    if (hayErrores) {
      // El campo puede haber quedado lejos del boton: se lleva el foco ahi.
      document.getElementById(Object.keys(nuevos)[0])?.focus()
      return
    }

    if (maximo < minimo) {
      setMensaje({ tipo: 'error', texto: mensajeDeError('duraciones_incoherentes') })
      return
    }

    setGuardando(true)
    try {
      await guardarOferta({
        materias: campos.materias,
        etapas: campos.etapas.map((id) => ({ id, programa: campos.programa || null })),
        idiomas: campos.idiomas,
      })
      await guardarModalidad({
        modalidad: campos.modalidad,
        lugar_clase: campos.lugar,
        direccion_espacio: campos.direccion.trim() || null,
        zonas_traslado: campos.zonas,
        costo_traslado: aNumero(campos.costoTraslado) ?? 0,
      })
      await guardarPrecios({
        precio_hora_presencial: aNumero(campos.precioPresencial),
        precio_hora_online: aNumero(campos.precioOnline),
      })
      await guardarReglas({
        duracion_min: minimo,
        duracion_max: maximo,
        duraciones: campos.duraciones.filter((d) => d >= minimo && d <= maximo),
        descanso_min: Number(campos.descanso),
        max_clases_dia: aNumero(campos.maxClasesDia),
        aviso_minimo_horas: Number(campos.aviso),
        formato: campos.formato,
        cupo_min: aNumero(campos.cupoMin),
        cupo_max: aNumero(campos.cupoMax),
      })
      await alGuardar()
      setMensaje({ tipo: 'ok', texto: 'Listo, se guardaron los cambios.' })
    } catch (error) {
      setMensaje({ tipo: 'error', texto: mensajeDeError(error.codigo) })
    } finally {
      setGuardando(false)
    }
  }

  return (
    // Un solo <form> envuelve las dos tarjetas: el boton de abajo guarda todo.
    <form onSubmit={guardar} noValidate className="perfil-contenido">
      {/* ================= Materias y niveles ================= */}
      <section className="panel">
        <h4 style={{ marginBottom: '4px' }}>Materias y niveles</h4>
        <p className="panel-ayuda" style={{ marginTop: 0 }}>
          Los alumnos filtran por estos dos campos, asi que conviene ser preciso.
        </p>

        <ListaEtiquetas
          id="materias"
          etiqueta="Materias que dictas"
          seleccion={campos.materias}
          opciones={catalogos?.materias}
          nombres={nombresPorId(ficha.materias.map((m) => m.id), ficha.materias.map((m) => m.nombre))}
          alCambiar={cambiar('materias')}
          textoAgregar="+ Agregar materia"
        />

        <div className="field">
          <label>Etapas educativas</label>
          <div className="casillas">
            {etapasParaElegir.map((etapa) => (
              <label key={etapa.id} className="casilla">
                <input
                  type="checkbox"
                  checked={campos.etapas.includes(etapa.id)}
                  onChange={() => cambiar('etapas')(alternar(campos.etapas, etapa.id))}
                  disabled={!catalogos}
                />
                {etapa.nombre}
              </label>
            ))}
          </div>
        </div>

        <div className="grilla-2">
          <CampoSelect
            id="programa"
            etiqueta="Programa que seguis"
            valor={campos.programa}
            alCambiar={cambiar('programa')}
            opciones={programas.map((p) => ({ valor: p, texto: p }))}
            vacio="Sin especificar"
          />
          <ListaEtiquetas
            id="idiomas"
            etiqueta="Idiomas de la clase"
            seleccion={campos.idiomas}
            opciones={catalogos?.idiomas}
            nombres={nombresPorId(ficha.idioma_ids, ficha.idiomas)}
            alCambiar={cambiar('idiomas')}
          />
        </div>
      </section>

      {/* ================= Modalidad ================= */}
      <section className="panel">
        <h4>Modalidad</h4>

        <div className="field">
          <label id="modalidad-etiqueta">Como das clase</label>
          {/* Un control segmentado: radios escondidos dentro de labels (ver
              .seg-opt en componentes.css). Se ve como tres botones pegados. */}
          <div className="seg seg-ancho" role="radiogroup" aria-labelledby="modalidad-etiqueta">
            {MODALIDADES.map((m) => (
              <label key={m.valor} className="seg-opt">
                <input
                  type="radio"
                  name="modalidad"
                  checked={campos.modalidad === m.valor}
                  onChange={() => cambiar('modalidad')(m.valor)}
                />
                {m.texto}
              </label>
            ))}
          </div>
        </div>

        {daPresencial && (
          <div className="grilla-2">
            <CampoSelect id="lugar" etiqueta="Donde das las clases presenciales" valor={campos.lugar}
                         alCambiar={cambiar('lugar')} opciones={LUGARES} vacio={null} />
            {tieneEspacio && (
              <Campo id="direccion" etiqueta="Direccion del espacio" valor={campos.direccion}
                     alCambiar={cambiar('direccion')} placeholder="Biblioteca del Cordon, Soriano 1234"
                     ayuda="Se muestra en tu ficha publica." />
            )}
            {vaADomicilio && (
              <ListaEtiquetas
                id="zonas"
                etiqueta="Barrios donde te trasladas"
                seleccion={campos.zonas}
                opciones={catalogos?.barrios}
                nombres={nombresPorId(ficha.zona_ids, ficha.zonas_traslado)}
                alCambiar={cambiar('zonas')}
              />
            )}
            {vaADomicilio && (
              <Campo id="costoTraslado" etiqueta="Costo fijo de traslado (cualquier distancia)" tipo="number"
                     min="0" valor={campos.costoTraslado} alCambiar={cambiar('costoTraslado')} />
            )}
          </div>
        )}

        <div className="grilla-2">
          {daPresencial && (
            <Campo id="precioPresencial" etiqueta="Precio por hora presencial" tipo="number" min="0"
                   valor={campos.precioPresencial} alCambiar={cambiar('precioPresencial')}
                   error={errores.precioPresencial} />
          )}
          {daOnline && (
            <Campo id="precioOnline" etiqueta="Precio por hora online" tipo="number" min="0"
                   valor={campos.precioOnline} alCambiar={cambiar('precioOnline')}
                   error={errores.precioOnline} />
          )}
        </div>

        {/* --- Duracion de las clases --- */}
        <h4 style={{ margin: '14px 0 4px' }}>Duracion de las clases</h4>
        <p className="panel-ayuda" style={{ marginTop: 0 }}>
          El alumno solo puede reservar dentro de estas preferencias.
        </p>
        <div className="grilla-3">
          <CampoSelect id="duracionMin" etiqueta="Duracion minima" valor={campos.duracionMin}
                       alCambiar={cambiar('duracionMin')} opciones={DURACIONES} vacio={null} />
          <CampoSelect id="duracionMax" etiqueta="Duracion maxima" valor={campos.duracionMax}
                       alCambiar={cambiar('duracionMax')} opciones={DURACIONES} vacio={null} />
          <div className="field">
            <label>Duraciones que ofreces</label>
            <div className="etiquetas">
              {duracionesPosibles.map((d) => {
                const elegida = campos.duraciones.includes(d.valor)
                return (
                  // aria-pressed: es un boton que queda "apretado" o no.
                  <button
                    key={d.valor}
                    type="button"
                    className="tag tag-boton tag-neutral"
                    aria-pressed={elegida}
                    onClick={() => cambiar('duraciones')(alternar(campos.duraciones, d.valor))}
                  >
                    {d.texto}
                  </button>
                )
              })}
            </div>
          </div>
          <CampoSelect id="descanso" etiqueta="Descanso entre clases" valor={campos.descanso}
                       alCambiar={cambiar('descanso')} opciones={DESCANSOS} vacio={null} />
          <Campo id="maxClasesDia" etiqueta="Maximo de clases por dia" tipo="number" min="1"
                 valor={campos.maxClasesDia} alCambiar={cambiar('maxClasesDia')} ayuda="Vacio = sin tope" />
          <CampoSelect id="aviso" etiqueta="Aviso minimo para reservar" valor={campos.aviso}
                       alCambiar={cambiar('aviso')} opciones={AVISOS} vacio={null} />
        </div>

        {/* --- Alumnos por clase --- */}
        <h4 style={{ margin: '14px 0 4px' }}>Alumnos por clase</h4>
        <p className="panel-ayuda" style={{ marginTop: 0 }}>
          Las clases grupales todavia no se pueden reservar: por ahora esto queda guardado para mas adelante.
        </p>
        <div className="field">
          <label id="formato-etiqueta">Formato</label>
          <div className="seg seg-ancho" role="radiogroup" aria-labelledby="formato-etiqueta">
            {FORMATOS.map((f) => (
              <label key={f.valor} className="seg-opt">
                <input
                  type="radio"
                  name="formato"
                  checked={campos.formato === f.valor}
                  onChange={() => cambiar('formato')(f.valor)}
                />
                {f.texto}
              </label>
            ))}
          </div>
        </div>
        {haceGrupales && (
          <div className="grilla-2">
            <Campo id="cupoMax" etiqueta="Maximo de alumnos por clase grupal" tipo="number" min="1"
                   valor={campos.cupoMax} alCambiar={cambiar('cupoMax')} />
            <Campo id="cupoMin" etiqueta="Minimo para que salga la grupal" tipo="number" min="1"
                   valor={campos.cupoMin} alCambiar={cambiar('cupoMin')} />
          </div>
        )}

        <Alerta tipo={mensaje?.tipo}>{mensaje?.texto}</Alerta>

        <div className="botonera">
          <button type="submit" className="btn btn-primary" disabled={guardando}>
            {guardando ? 'Guardando...' : 'Guardar cambios'}
          </button>
          <button type="button" className="btn btn-ghost" disabled={guardando}
                  onClick={() => { setCampos(valoresIniciales(ficha)); setErrores({}); setMensaje(null) }}>
            Cancelar
          </button>
        </div>
      </section>
    </form>
  )
}
