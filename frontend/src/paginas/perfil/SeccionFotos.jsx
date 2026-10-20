/**
 * La pestania "Fotos del lugar" de 1j: hasta cuatro fotos del espacio donde
 * da clase. Se muestran en la ficha publica (1f).
 *
 * A diferencia de las otras secciones, casi todo se guarda AL INSTANTE:
 *   - subir una foto       POST   /api/perfiles/profesor/yo/fotos
 *   - hacerla portada      PUT    /api/perfiles/profesor/yo/fotos/{id}
 *   - quitarla             DELETE /api/perfiles/profesor/yo/fotos/{id}
 * Lo unico que espera al boton "Guardar epigrafes" son los textos de abajo de
 * cada foto, para no mandar una llamada por cada letra que se escribe.
 *
 * Despues de cada cambio se llama a alGuardar(): la pantalla vuelve a pedir
 * la ficha y esta seccion se redibuja con las fotos como quedaron.
 */

import { useState } from 'react'

import { mensajeDeError } from '../../api/mensajes.js'
import { agregarFoto, borrarFoto, editarFoto } from '../../api/perfiles.js'
import Alerta from '../../componentes/Alerta.jsx'
import { achicarImagen } from '../../utiles/imagenes.js'

const MAX_FOTOS = 4 // el mismo tope que el backend (perfiles/logica.py)

export default function SeccionFotos({ ficha, alGuardar }) {
  // Los epigrafes que el usuario cambio y todavia no guardo: { idFoto: texto }.
  // Lo que no esta aca se muestra como viene de la ficha.
  const [epigrafes, setEpigrafes] = useState({})
  const [mensaje, setMensaje] = useState(null)
  const [ocupado, setOcupado] = useState(false)

  const fotos = ficha.fotos
  const lugaresLibres = MAX_FOTOS - fotos.length

  /**
   * Corre una accion (subir, borrar, ...) con el mismo manejo para todas:
   * bloquea los botones, recarga la ficha si salio bien y muestra el error si
   * no. Recibe la accion como funcion: `hacer(() => borrarFoto(id))`.
   */
  async function hacer(accion, textoOk) {
    setMensaje(null)
    setOcupado(true)
    try {
      await accion()
      await alGuardar()
      if (textoOk) setMensaje({ tipo: 'ok', texto: textoOk })
    } catch (error) {
      setMensaje({ tipo: 'error', texto: mensajeDeError(error.codigo) })
    } finally {
      setOcupado(false)
    }
  }

  function alElegirArchivo(evento) {
    const archivo = evento.target.files[0]
    evento.target.value = '' // para poder elegir el mismo archivo otra vez
    if (!archivo) return
    hacer(async () => {
      // 1200 px: mas grande que la foto de perfil, porque se ve mas grande.
      const imagen = await achicarImagen(archivo, 1200)
      await agregarFoto({ imagen_base64: imagen, epigrafe: null })
    })
  }

  function textoEpigrafe(foto) {
    // ?? = "si lo de la izquierda es null o undefined, usa lo de la derecha".
    return epigrafes[foto.id] ?? foto.epigrafe ?? ''
  }

  function hacerPortada(foto, posicion) {
    hacer(() => editarFoto(foto.id, { epigrafe: textoEpigrafe(foto), orden: posicion, es_portada: true }))
  }

  function guardarEpigrafes() {
    hacer(async () => {
      // Solo las fotos cuyo epigrafe cambio. Una llamada por foto.
      for (const [posicion, foto] of fotos.entries()) {
        if (foto.id in epigrafes) {
          await editarFoto(foto.id, { epigrafe: epigrafes[foto.id], orden: posicion, es_portada: foto.es_portada })
        }
      }
      setEpigrafes({})
    }, 'Listo, se guardaron los epigrafes.')
  }

  return (
    <section className="panel">
      <h4 style={{ marginBottom: '4px' }}>Fotos del lugar donde doy clase</h4>
      <p className="panel-ayuda" style={{ marginTop: 0 }}>
        Se muestran en tu ficha publica, en el detalle que ve el alumno antes de reservar.
      </p>

      <Alerta tipo={mensaje?.tipo}>{mensaje?.texto}</Alerta>

      <div className="fotos">
        {/* Primero las fotos que ya hay... */}
        {fotos.map((foto, posicion) => (
          <div key={foto.id} className="foto">
            <div className="foto-imagen">
              <img src={foto.imagen_base64} alt={foto.epigrafe || `Foto ${posicion + 1} del lugar`} />
              {foto.es_portada && <span className="tag tag-accent-2">Portada</span>}
            </div>
            <input
              className="input"
              value={textoEpigrafe(foto)}
              onChange={(e) => setEpigrafes((previos) => ({ ...previos, [foto.id]: e.target.value }))}
              placeholder="Epigrafe (opcional)"
              aria-label={`Epigrafe de la foto ${posicion + 1}`}
              maxLength={120}
            />
            <div className="foto-acciones">
              {!foto.es_portada && (
                <button type="button" className="btn btn-ghost" disabled={ocupado}
                        onClick={() => hacerPortada(foto, posicion)}>
                  Hacer portada
                </button>
              )}
              <button type="button" className="btn btn-ghost" disabled={ocupado}
                      onClick={() => hacer(() => borrarFoto(foto.id))}>
                Quitar
              </button>
            </div>
          </div>
        ))}

        {/* ...y despues UN espacio para subir otra, si queda lugar. */}
        {lugaresLibres > 0 && (
          <label className="foto-vacia">
            <span>
              {ocupado ? 'Subiendo...' : '+ Agregar foto'}
              <br />
              <span className="texto-chico">
                {lugaresLibres === 1 ? 'Queda 1 lugar' : `Quedan ${lugaresLibres} lugares`}
              </span>
            </span>
            <input type="file" accept="image/*" className="oculto-visual"
                   onChange={alElegirArchivo} disabled={ocupado} />
          </label>
        )}
      </div>

      <div className="botonera" style={{ marginTop: '16px', alignItems: 'center' }}>
        <span className="tag tag-neutral">La portada es la que se ve primero</span>
        <span className="tag tag-neutral">Sin datos personales visibles</span>
        {fotos.length > 0 && (
          <button type="button" className="btn btn-primary" style={{ marginLeft: 'auto' }}
                  onClick={guardarEpigrafes} disabled={ocupado || Object.keys(epigrafes).length === 0}>
            Guardar epigrafes
          </button>
        )}
      </div>
    </section>
  )
}
