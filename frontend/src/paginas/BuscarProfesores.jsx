import { useEffect, useState } from 'react'
import { obtenerCatalogos } from '../api/perfiles.js'
import CampoSelect from '../componentes/CampoSelect.jsx'
import MapaProfesores from '../componentes/busqueda/MapaProfesores.jsx'

const PRECIO_MAXIMO = 3000
const PUNTAJES = ['', '4.0', '4.5', '4.8']

export default function BuscarProfesores() {
  const [catalogos, setCatalogos] = useState(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')
  const [materiaId, setMateriaId] = useState('')
  const [etapaId, setEtapaId] = useState('')
  const [barrioId, setBarrioId] = useState('')
  const [centroId, setCentroId] = useState('')
  const [precioMax, setPrecioMax] = useState(PRECIO_MAXIMO)
  const [modalidad, setModalidad] = useState('')
  const [puntajeMin, setPuntajeMin] = useState('')

  useEffect(() => {
    obtenerCatalogos()
      .then((datos) => {
        setCatalogos(datos)
      })
      .catch(() => {
        setError('No se pudieron cargar los catálogos.')
      })
      .finally(() => {
        setCargando(false)
      })
  }, [])

  function cambiarBarrio(nuevoBarrioId) {
    setBarrioId(nuevoBarrioId)
    setCentroId('')
  }

  function limpiarFiltros() {
    setMateriaId('')
    setEtapaId('')
    setBarrioId('')
    setCentroId('')
    setPrecioMax(PRECIO_MAXIMO)
    setModalidad('')
    setPuntajeMin('')
  }

  const hayFiltros = Boolean(
    materiaId ||
    etapaId ||
    barrioId ||
    centroId ||
    precioMax !== PRECIO_MAXIMO ||
    modalidad ||
    puntajeMin,
  )

  const ubicacionMapa = catalogos
    ? centroId
      ? catalogos.centros.find((centro) => String(centro.id) === centroId)
      : catalogos.barrios.find((barrio) => String(barrio.id) === barrioId)
    : null

  return (
    <section className="buscar-pagina">
      {cargando && <p>Cargando opciones...</p>}

      {error && <p>{error}</p>}

      {catalogos && (
        <div className="buscar-contenido">
          <aside className="filtros-panel" aria-label="Filtros de búsqueda">
          <div className="filtros-cabecera">
            <h2>Filtros</h2>
            <button
              type="button"
              className="filtros-limpiar"
              onClick={limpiarFiltros}
              disabled={!hayFiltros}
            >
              Limpiar
            </button>
          </div>

          <CampoSelect
            id="materia"
            etiqueta="Materia"
            valor={materiaId}
            alCambiar={setMateriaId}
            vacio="Todas las materias"
            opciones={catalogos.materias.map((materia) => ({
              valor: materia.id,
              texto: materia.nombre,
            }))}
          />

          <CampoSelect
            id="etapa"
            etiqueta="Etapa educativa"
            valor={etapaId}
            alCambiar={setEtapaId}
            vacio="Todas las etapas"
            opciones={catalogos.etapas.map((etapa) => ({
              valor: etapa.id,
              texto: etapa.nombre,
            }))}
          />

          <div className="filtro-bloque">
            <label htmlFor="precio-maximo">
              Precio por hora —{' '}
              {precioMax === PRECIO_MAXIMO ? 'cualquier precio' : `$ ${precioMax}`}
            </label>
            <input
              id="precio-maximo"
              className="filtro-rango"
              type="range"
              min="300"
              max={PRECIO_MAXIMO}
              step="100"
              value={precioMax}
              onChange={(evento) => setPrecioMax(Number(evento.target.value))}
            />
          </div>

          <CampoSelect
            id="barrio"
            etiqueta="Barrio"
            valor={barrioId}
            alCambiar={cambiarBarrio}
            vacio="Todos los barrios"
            opciones={catalogos.barrios.map((barrio) => ({
              valor: barrio.id,
              texto: barrio.nombre,
            }))}
          />

          <CampoSelect
            id="centro"
            etiqueta="Centro educativo"
            valor={centroId}
            alCambiar={setCentroId}
            vacio="Todos los centros educativos"
            opciones={catalogos.centros
              .filter(
                (centro) => !barrioId || String(centro.barrio_id) === barrioId,
              )
              .map((centro) => ({
                valor: centro.id,
                texto: centro.nombre,
              }))}
            ayuda={barrioId ? 'Se muestran los centros del barrio elegido.' : null}
          />

          <fieldset className="filtro-grupo">
            <legend>Modalidad</legend>
            {[
              { valor: '', texto: 'Cualquiera' },
              { valor: 'presencial', texto: 'Presencial' },
              { valor: 'online', texto: 'Online' },
            ].map((opcion) => (
              <label key={opcion.valor || 'cualquiera'} className="filtro-radio">
                <input
                  type="radio"
                  name="modalidad"
                  value={opcion.valor}
                  checked={modalidad === opcion.valor}
                  onChange={(evento) => setModalidad(evento.target.value)}
                />
                <span>{opcion.texto}</span>
              </label>
            ))}
          </fieldset>

          <fieldset className="filtro-grupo">
            <legend>Puntaje mínimo</legend>
            <div className="filtro-puntajes">
              {PUNTAJES.map((puntaje) => (
                <label key={puntaje || 'cualquiera'}>
                  <input
                    className="oculto-visual"
                    type="radio"
                    name="puntaje-minimo"
                    value={puntaje}
                    checked={puntajeMin === puntaje}
                    onChange={(evento) => setPuntajeMin(evento.target.value)}
                  />
                  <span>{puntaje || 'Cualquiera'}</span>
                </label>
              ))}
            </div>
          </fieldset>
          </aside>

          <MapaProfesores ubicacion={ubicacionMapa} />
        </div>
      )}
    </section>
  )
}
