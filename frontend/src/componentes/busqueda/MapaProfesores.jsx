import { useEffect } from 'react'
import { MapContainer, TileLayer, useMap } from 'react-leaflet'

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

export default function MapaProfesores({ ubicacion }) {
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
    <section className="mapa-profesores" aria-label="Mapa de profesores">
      <MapContainer
        center={[MONTEVIDEO.latitud, MONTEVIDEO.longitud]}
        zoom={MONTEVIDEO.zoom}
        scrollWheelZoom
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <RecentrarMapa
          latitud={latitud}
          longitud={longitud}
          zoom={zoom}
        />
      </MapContainer>

      <p className="mapa-ayuda">
        {tieneCoordenadas
          ? `Mapa centrado en ${ubicacion.nombre}.`
          : ubicacion
            ? `${ubicacion.nombre} no tiene coordenadas cargadas.`
            : 'Seleccioná un barrio o centro educativo para acercar el mapa.'}
      </p>
    </section>
  )
}
