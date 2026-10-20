import { useCallback, useEffect, useState } from 'react'
import { useMap } from 'react-leaflet'

export function useZoomConEnter() {
  const [zoomRuedaActivo, setZoomRuedaActivo] = useState(false)

  const manejarTeclaZoom = useCallback((evento) => {
    const etiqueta = evento.target?.tagName
    const esControl = ['A', 'BUTTON', 'INPUT', 'SELECT', 'TEXTAREA'].includes(etiqueta)

    if (evento.key === 'Escape') {
      setZoomRuedaActivo(false)
      return
    }

    if (evento.key === 'Enter' && !esControl) {
      evento.preventDefault()
      setZoomRuedaActivo((activo) => !activo)
    }
  }, [])

  return { zoomRuedaActivo, manejarTeclaZoom }
}

export function ControlZoomRueda({ activo }) {
  const mapa = useMap()

  useEffect(() => {
    if (activo) mapa.scrollWheelZoom.enable()
    else mapa.scrollWheelZoom.disable()
  }, [activo, mapa])

  return null
}

export function AvisoZoomRueda({ activo, compacto = false }) {
  const texto = compacto
    ? activo ? 'Rueda activa · Esc para salir' : 'Enter: activar rueda'
    : activo ? 'Zoom con rueda activo · Escape para salir' : 'Enter para usar la rueda en el mapa'

  return (
    <span className={`mapa-zoom-aviso${activo ? ' esta-activo' : ''}${compacto ? ' compacto' : ''}`}>
      {texto}
    </span>
  )
}
