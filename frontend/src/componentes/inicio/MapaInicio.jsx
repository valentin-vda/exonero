import { useEffect } from 'react'
import { divIcon } from 'leaflet'
import { Link } from 'react-router-dom'
import {
  CircleMarker,
  MapContainer,
  Marker,
  Popup,
  TileLayer,
  useMap,
  ZoomControl,
} from 'react-leaflet'

import { pesos, puntaje } from '../../utiles/formato.js'
import {
  AvisoZoomRueda,
  ControlZoomRueda,
  useZoomConEnter,
} from '../mapas/ZoomConEnter.jsx'
import SenalBatman from '../mapas/SenalBatman.jsx'

const MONTEVIDEO = [-34.9011, -56.1645]

function Recentrar({ centro }) {
  const mapa = useMap()

  useEffect(() => {
    mapa.flyTo(centro, 12, { duration: 0.7 })
  }, [centro, mapa])

  return null
}

function QuitarZoomAutomatico() {
  const mapa = useMap()

  useEffect(() => {
    mapa.zoomControl?.remove()
  }, [mapa])

  return null
}

function icono(pin, destacados) {
  const letra = pin.nombre?.trim().charAt(0).toUpperCase() || 'P'
  const claseDestacada = destacados.has(pin.id) ? ' inicio-pin-destacado' : ''

  return divIcon({
    className: `inicio-pin${claseDestacada}`,
    html: letra,
    iconSize: [38, 38],
    iconAnchor: [19, 19],
    popupAnchor: [0, -20],
  })
}

export default function MapaInicio({ pines = [], rankingIds = [], ubicacion }) {
  const { zoomRuedaActivo, manejarTeclaZoom } = useZoomConEnter()
  const tieneUbicacion = ubicacion?.latitud != null && ubicacion?.longitud != null
  const centro = tieneUbicacion
    ? [Number(ubicacion.latitud), Number(ubicacion.longitud)]
    : MONTEVIDEO
  const destacados = new Set(rankingIds)

  return (
    <section
      className="inicio-mapa mapa-con-teclado"
      aria-label="Mapa de profesores cercanos"
      tabIndex={0}
      onKeyDown={manejarTeclaZoom}
    >
      <MapContainer
        center={MONTEVIDEO}
        zoom={12}
        zoomControl={false}
        scrollWheelZoom={false}
      >
        <QuitarZoomAutomatico />
        <ControlZoomRueda activo={zoomRuedaActivo} />
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Recentrar centro={centro} />

        {tieneUbicacion && (
          <CircleMarker
            center={centro}
            radius={7}
            pathOptions={{
              color: 'var(--color-surface)',
              weight: 3,
              fillColor: 'var(--color-text)',
              fillOpacity: 1,
            }}
          />
        )}

        {pines.map((pin) => (
          <Marker
            key={pin.id}
            position={[Number(pin.latitud), Number(pin.longitud)]}
            icon={icono(pin, destacados)}
          >
            <Popup>
              <strong>{pin.nombre}</strong>
              <span>★ {puntaje(pin.puntaje_promedio)} · {pin.precio_hora == null ? 'Consultar' : `${pesos(pin.precio_hora)}/h`}</span>
              <Link to={`/profesor/${pin.id}`}>Ver profesor</Link>
            </Popup>
          </Marker>
        ))}

        <SenalBatman />
        <ZoomControl position="bottomright" />
      </MapContainer>

      <AvisoZoomRueda activo={zoomRuedaActivo} />

      <div className="inicio-mapa-leyenda">
        <span><i className="disponible" />Profe disponible</span>
        <span><i className="destacado" />Mejor rankeado</span>
      </div>
    </section>
  )
}
