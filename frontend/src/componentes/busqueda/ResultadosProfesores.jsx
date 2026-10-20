import { Link } from 'react-router-dom'

import Avatar from '../Avatar.jsx'

function precioVisible(profesor, modalidad) {
  if (modalidad === 'presencial') return profesor.precio_hora_presencial
  if (modalidad === 'online') return profesor.precio_hora_online

  const precios = [
    profesor.precio_hora_presencial,
    profesor.precio_hora_online,
  ]
    .filter((precio) => precio != null)
    .map(Number)

  return precios.length ? Math.min(...precios) : null
}

function dinero(valor) {
  if (valor == null) return '—'
  return `$ ${new Intl.NumberFormat('es-UY').format(Number(valor))}`
}

function puntaje(valor) {
  return Number(valor || 0).toFixed(1).replace('.', ',')
}

function zona(profesor) {
  const barrio = profesor.barrio || 'Sin barrio'
  if (profesor.distancia_km == null) return barrio
  const distancia = Number(profesor.distancia_km).toFixed(1).replace('.', ',')
  return `${barrio} · ${distancia} km`
}

export default function ResultadosProfesores({
  pagina,
  modalidad,
  cargando,
  error,
  hayFiltros,
  alLimpiar,
  alCambiarPagina,
}) {
  const resultados = pagina?.resultados || []
  const total = pagina?.total ?? 0
  const totalPaginas = pagina
    ? Math.ceil(pagina.total / pagina.por_pagina)
    : 0

  return (
    <section className="resultados-bloque" aria-live="polite">
      <div className="resultados-cabecera">
        <h2>
          {cargando && !pagina
            ? 'Buscando profesores…'
            : `${total} ${total === 1 ? 'profe coincide' : 'profes coinciden'} con tus filtros`}
        </h2>
        <span>ordenados por distancia</span>
      </div>

      <div className={`resultados-panel${cargando ? ' esta-cargando' : ''}`}>
        <div className="resultados-tabla">
          <div className="resultado-fila resultado-encabezado" aria-hidden="true">
            <span>Profe</span>
            <span>Materia</span>
            <span>Zona</span>
            <span>Puntaje</span>
            <span>Precio</span>
            <span />
          </div>

          {resultados.map((profesor) => (
            <div className="resultado-fila" key={profesor.id}>
              <span className="resultado-profesor">
                <Avatar persona={profesor} />
                <span>{profesor.nombre} {profesor.apellido}</span>
              </span>
              <span>{profesor.materias.join(', ') || 'Sin materias'}</span>
              <span>{zona(profesor)}</span>
              <span>★ {puntaje(profesor.puntaje_promedio)}</span>
              <strong>{dinero(precioVisible(profesor, modalidad))}</strong>
              <span className="resultado-accion">
                <Link className="btn btn-secondary" to={`/profesor/${profesor.id}`}>
                  Ver Profesor
                </Link>
              </span>
            </div>
          ))}

          {!cargando && !error && resultados.length === 0 && (
            <div className="resultados-vacio">
              Ningún profe coincide con estos filtros.{' '}
              {hayFiltros && (
                <button type="button" onClick={alLimpiar}>
                  Limpiar filtros
                </button>
              )}
            </div>
          )}

          {error && <div className="resultados-error">{error}</div>}
        </div>
      </div>

      {totalPaginas > 1 && (
        <nav className="resultados-paginacion" aria-label="Páginas de resultados">
          <button
            type="button"
            className="btn btn-secondary"
            disabled={cargando || pagina.pagina === 1}
            onClick={() => alCambiarPagina(pagina.pagina - 1)}
          >
            Anterior
          </button>
          <span>Página {pagina.pagina} de {totalPaginas}</span>
          <button
            type="button"
            className="btn btn-secondary"
            disabled={cargando || pagina.pagina === totalPaginas}
            onClick={() => alCambiarPagina(pagina.pagina + 1)}
          >
            Siguiente
          </button>
        </nav>
      )}
    </section>
  )
}
