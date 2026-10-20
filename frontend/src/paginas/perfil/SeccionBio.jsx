/**
 * La pestania "Biografia" de 1j: titular, "sobre mi" y como es una clase.
 *
 * Todo se guarda junto con PUT /api/perfiles/profesor/yo/bio.
 *
 * Lo interesante de esta seccion es la lista de "Como es una clase conmigo":
 * una cantidad variable de renglones que se pueden agregar y quitar. En el
 * estado es una lista, y el JSX dibuja un <input> por elemento con map().
 */

import { useState } from 'react'

import { mensajeDeError } from '../../api/mensajes.js'
import { guardarBio } from '../../api/perfiles.js'
import Alerta from '../../componentes/Alerta.jsx'
import Campo from '../../componentes/Campo.jsx'
import { CRUZ } from '../../utiles/formato.js'

const MAX_BIOGRAFIA = 600

// Cada renglon lleva un id propio para usarlo como `key` en la lista. No sirve
// usar la posicion: al borrar el renglon 2, el 3 pasaria a ser el 2 y React
// confundiria cual es cual. Como estos renglones no vienen del backend con un
// id, se lo inventamos con un contador.
let proximoId = 1
function renglon(texto) {
  return { id: proximoId++, texto }
}

export default function SeccionBio({ ficha, alGuardar }) {
  const [titular, setTitular] = useState(ficha.titular || '')
  const [biografia, setBiografia] = useState(ficha.biografia || '')
  // Si todavia no tiene puntos, se arranca con un renglon vacio para escribir.
  const [puntos, setPuntos] = useState(() =>
    ficha.puntos_metodo.length ? ficha.puntos_metodo.map(renglon) : [renglon('')],
  )
  const [mensaje, setMensaje] = useState(null)
  const [guardando, setGuardando] = useState(false)

  function cambiarPunto(id, texto) {
    // map devuelve una lista nueva: igual a la vieja salvo el renglon tocado.
    setPuntos((lista) => lista.map((p) => (p.id === id ? { ...p, texto } : p)))
  }

  function quitarPunto(id) {
    setPuntos((lista) => lista.filter((p) => p.id !== id))
  }

  function agregarPunto() {
    setPuntos((lista) => [...lista, renglon('')])
  }

  async function guardar(evento) {
    evento.preventDefault()
    setMensaje(null)
    setGuardando(true)
    try {
      await guardarBio({
        titular: titular.trim() || null,
        biografia: biografia.trim() || null,
        // El backend descarta los renglones vacios; igual no los mandamos.
        puntos_metodo: puntos.map((p) => p.texto.trim()).filter(Boolean),
      })
      await alGuardar()
      setMensaje({ tipo: 'ok', texto: 'Listo, se guardo tu biografia.' })
    } catch (error) {
      setMensaje({ tipo: 'error', texto: mensajeDeError(error.codigo) })
    } finally {
      setGuardando(false)
    }
  }

  return (
    <section className="panel">
      <h4 style={{ marginBottom: '4px' }}>Biografia</h4>
      <p className="panel-ayuda" style={{ marginTop: 0 }}>
        Conta como trabajas. Es lo primero que leen los alumnos y sus familias.
      </p>

      <Alerta tipo={mensaje?.tipo}>{mensaje?.texto}</Alerta>

      <form onSubmit={guardar} noValidate>
        <Campo id="titular" etiqueta="Titular corto" valor={titular} alCambiar={setTitular} maxLength={160}
               placeholder="Matematica y Fisica para liceo y UTU, con plan de ejercicios semanal" />

        {/* Campo.jsx es solo para <input>; el textarea va armado a mano, con
            las mismas clases para que se vea igual. */}
        <div className="field">
          <label htmlFor="biografia">Sobre mi</label>
          <textarea
            id="biografia"
            className="input textarea-bio"
            value={biografia}
            onChange={(e) => setBiografia(e.target.value)}
            maxLength={MAX_BIOGRAFIA}
          />
          <span className="field-hint">
            {biografia.length} de {MAX_BIOGRAFIA} caracteres
          </span>
        </div>

        <div className="field">
          <label>Como es una clase conmigo</label>
          {puntos.map((punto, posicion) => (
            <div key={punto.id} className="renglon">
              <input
                className="input"
                value={punto.texto}
                onChange={(e) => cambiarPunto(punto.id, e.target.value)}
                aria-label={`Punto ${posicion + 1}`}
                placeholder="Repasamos lo que trajiste del liceo..."
              />
              <button type="button" className="btn btn-ghost" onClick={() => quitarPunto(punto.id)}
                      aria-label={`Quitar el punto ${posicion + 1}`}>
                {CRUZ}
              </button>
            </div>
          ))}
          <button type="button" className="btn btn-ghost" onClick={agregarPunto}>
            + Agregar punto
          </button>
        </div>

        <div className="botonera">
          <button type="submit" className="btn btn-primary" disabled={guardando}>
            {guardando ? 'Guardando...' : 'Guardar cambios'}
          </button>
        </div>
      </form>
    </section>
  )
}
