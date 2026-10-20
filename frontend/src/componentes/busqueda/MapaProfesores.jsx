import { useEffect } from 'react'
import { divIcon } from 'leaflet'
import { Link } from 'react-router-dom'
import {
  Circle,
  MapContainer,
  Marker,
  Popup,
  TileLayer,
  useMap,
  ZoomControl,
} from 'react-leaflet'

import {
  AvisoZoomRueda,
  ControlZoomRueda,
  useZoomConEnter,
} from '../mapas/ZoomConEnter.jsx'

const MONTEVIDEO = {
  latitud: -34.9011,
  longitud: -56.1645,
  zoom: 12,
}

function RecentrarMapa({ latitud, longitud, zoom }) {
  const mapa = useMap()

  useEffect(() => {
    mapa.flyTo([latitud, longitud], zoom, { duration: 0.7 })
  }, [mapa, latitud, longitud, zoom])

  return null
}

function QuitarZoomAutomatico() {
  const mapa = useMap()

  useEffect(() => {
    // Leaflet puede conservar este control durante una recarga en caliente.
    // Lo quitamos expresamente para que solo quede el ZoomControl inferior.
    mapa.zoomControl?.remove()
  }, [mapa])

  return null
}

function iconoProfesor(pin) {
  const primeraLetra = pin.nombre?.trim().charAt(0).toUpperCase()
  const inicial = /^\p{L}$/u.test(primeraLetra) ? primeraLetra : 'P'
  const secundaria = pin.id % 3 === 0 ? ' mapa-pin-secundario' : ''

  return divIcon({
    className: `mapa-pin${secundaria}`,
    html: inicial,
    iconSize: [38, 38],
    iconAnchor: [19, 19],
    popupAnchor: [0, -20],
  })
}

function dinero(valor) {
  if (valor == null) return 'Precio a consultar'
  return `$ ${new Intl.NumberFormat('es-UY').format(Number(valor))} por hora`
}

export default function MapaProfesores({ ubicacion, pines = [], cargando = false }) {
  const { zoomRuedaActivo, manejarTeclaZoom } = useZoomConEnter()
  const tieneCoordenadas =
    ubicacion?.latitud != null && ubicacion?.longitud != null
  const latitud = tieneCoordenadas
    ? Number(ubicacion.latitud)
    : MONTEVIDEO.latitud
  const longitud = tieneCoordenadas
    ? Number(ubicacion.longitud)
    : MONTEVIDEO.longitud
  const zoom = tieneCoordenadas ? 14 : MONTEVIDEO.zoom

  return (
    <section
      className="mapa-profesores mapa-con-teclado"
      aria-label="Mapa de profesores"
      tabIndex={0}
      onKeyDown={manejarTeclaZoom}
    >
      <MapContainer
        key="mapa-con-zoom-inferior"
        center={[MONTEVIDEO.latitud, MONTEVIDEO.longitud]}
        zoom={MONTEVIDEO.zoom}
        zoomControl={false}
        scrollWheelZoom={false}
      >
        <QuitarZoomAutomatico />
        <ControlZoomRueda activo={zoomRuedaActivo} />
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <RecentrarMapa
          latitud={latitud}
          longitud={longitud}
          zoom={zoom}
        />

        {tieneCoordenadas && (
          <Circle
            center={[latitud, longitud]}
            radius={3000}
            pathOptions={{
              color: 'var(--color-accent)',
              fillColor: 'var(--color-accent)',
              fillOpacity: 0.08,
              dashArray: '6 7',
            }}
          />
        )}

        {pines.map((pin) => (
          <Marker
            key={pin.id}
            position={[Number(pin.latitud), Number(pin.longitud)]}
            icon={iconoProfesor(pin)}
          >
            <Popup>
              <strong>{pin.nombre}</strong>
              <span className="mapa-popup-meta">
                ★ {Number(pin.puntaje_promedio || 0).toFixed(1).replace('.', ',')}
                {' · '}
                {dinero(pin.precio_hora)}
              </span>
              <Link to={`/profesor/${pin.id}`}>Ver profesor</Link>
            </Popup>
          </Marker>
        ))}

        <ZoomControl position="bottomright" />
      </MapContainer>

      <AvisoZoomRueda activo={zoomRuedaActivo} />

      <p className="mapa-ayuda">
        {cargando
          ? 'Buscando profesores…'
          : pines.length
            ? 'Tocá un pin para ver al profe'
            : 'No hay profesores para mostrar en el mapa.'}
      </p>
    </section>
  )
}
