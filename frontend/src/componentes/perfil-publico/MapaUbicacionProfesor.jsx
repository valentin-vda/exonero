import { divIcon } from 'leaflet'
import { MapContainer, Marker, TileLayer, ZoomControl } from 'react-leaflet'

import {
  AvisoZoomRueda,
  ControlZoomRueda,
  useZoomConEnter,
} from '../mapas/ZoomConEnter.jsx'

export default function MapaUbicacionProfesor({ latitud, longitud, nombre }) {
  const { zoomRuedaActivo, manejarTeclaZoom } = useZoomConEnter()
  const centro = [Number(latitud), Number(longitud)]
  const icono = divIcon({
    className: 'publico-ubicacion-pin',
    html: nombre?.trim().charAt(0).toUpperCase() || 'P',
    iconSize: [36, 36],
    iconAnchor: [18, 18],
  })

  return (
    <div
      className="publico-mapa-con-zoom mapa-con-teclado"
      aria-label="Ubicación aproximada del profesor"
      tabIndex={0}
      onKeyDown={manejarTeclaZoom}
    >
      <MapContainer
        className="publico-mapa"
        center={centro}
        zoom={15}
        zoomControl={false}
        scrollWheelZoom={false}
      >
        <ControlZoomRueda activo={zoomRuedaActivo} />
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Marker position={centro} icon={icono} />
        <ZoomControl position="bottomright" />
      </MapContainer>
      <AvisoZoomRueda activo={zoomRuedaActivo} compacto />
    </div>
  )
}
