/**
 * Easter egg: en MODO OSCURO, si alguien aleja el mapa y se va hasta Estados
 * Unidos, encuentra en el medio del pais un pin mas, del mismo tamanio que el
 * de un profe, con el simbolo de Batman. Si lo toca, el popup lo presenta como
 * un profe: el "Caballero de la Noche".
 *
 * NO es un profe real: no esta en la base, no tiene ficha y el popup no lleva
 * a ningun lado. Existe solo en el mapa. Y solo de noche, o sea en modo
 * oscuro: con el modo claro no se dibuja.
 *
 * No se puede enfocar con el teclado (keyboard={false}): Leaflet le daria un
 * tabindex aunque Estados Unidos no este en pantalla, y quien recorre la app
 * con el teclado se toparia con un pin invisible.
 *
 * Va en los tres mapas (inicio, busqueda y la ficha del profe). Ninguno
 * encuadra la vista segun sus marcadores, asi que este no mueve nada.
 */

import { divIcon } from 'leaflet'
import { Marker, Popup } from 'react-leaflet'

import senalBatman from '../../assets/senal-batman.svg'
import { useAuth } from '../../auth/ContextoAuth.jsx'
import { ESTRELLA } from '../../utiles/formato.js'

// El centro geografico de los Estados Unidos continentales (Kansas).
const CENTRO_DE_ESTADOS_UNIDOS = [39.5, -98.35]

// El mismo tamanio y el mismo ancla que el pin de un profe (MapaInicio.jsx).
const icono = divIcon({
  className: 'senal-batman',
  html: `<img src="${senalBatman}" alt="" />`,
  iconSize: [38, 38],
  iconAnchor: [19, 19],
  popupAnchor: [0, -20],
})

export default function SenalBatman() {
  const { usuario } = useAuth()

  // Solo de noche.
  if (usuario?.tema !== 'oscuro') return null

  return (
    <Marker position={CENTRO_DE_ESTADOS_UNIDOS} icon={icono} keyboard={false} alt="Caballero de la Noche">
      {/* La misma forma que el popup de un profe, pero sin "Ver profesor":
          no hay ficha a la que ir. */}
      <Popup>
        <strong>Caballero de la Noche</strong>
        <span>{ESTRELLA} 5,0 · Ciudad Gótica</span>
        <span>Solo da clases de noche.</span>
      </Popup>
    </Marker>
  )
}
