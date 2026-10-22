/**
 * La bandeja de 1h: la lista de conversaciones, a la izquierda.
 *
 *   [ Buscar por nombre        ]
 *   (LF) Lucia Fernandez        hace 5 min
 *        Ah, y si podes reservar...      (2)
 *   (MS) Martin Silva           ayer
 *        Dale, gracias!
 *
 * Los datos los pide la pantalla (Mensajes.jsx), que tambien la refresca
 * cada diez segundos y despues de enviar. Aca solo se dibuja y se avisa que
 * conversacion se eligio y que se busco.
 */

import Alerta from '../../componentes/Alerta.jsx'
import Avatar from '../../componentes/Avatar.jsx'
import { cuando } from './fechas.js'

export default function Bandeja({ hilos, error, elegido, alElegir, busqueda, alBuscar, esAlumno }) {
  return (
    <aside className="bandeja" aria-label="Conversaciones">
      <input
        type="search"
        className="input bandeja-buscar"
        placeholder="Buscar por nombre"
        aria-label="Buscar conversacion por nombre"
        value={busqueda}
        onChange={(e) => alBuscar(e.target.value)}
      />

      {error && <Alerta tipo="error">{error}</Alerta>}
      {!hilos && !error && <p className="tablero-vacio">Cargando...</p>}
      {hilos && hilos.length === 0 && (
        <p className="tablero-vacio">
          {busqueda ? 'Nadie con ese nombre.' : 'Todavia no tenes conversaciones.'}
          {!busqueda && esAlumno && ' Escribile a un profe desde su ficha.'}
        </p>
      )}

      {hilos && hilos.length > 0 && (
        <ul className="bandeja-lista">
          {hilos.map((h) => {
            const otra = h.contraparte
            const nombre = [otra.nombre, otra.apellido].filter(Boolean).join(' ')
            return (
              <li key={h.id}>
                <button
                  type="button"
                  className={`bandeja-hilo${h.id === elegido ? ' bandeja-hilo-elegido' : ''}${h.no_leidos ? ' bandeja-hilo-nuevo' : ''}`}
                  aria-current={h.id === elegido ? 'true' : undefined}
                  onClick={() => alElegir(h.id)}
                >
                  <Avatar persona={otra} tamanio="mediano" />
                  <span className="bandeja-hilo-texto">
                    <span className="bandeja-hilo-fila">
                      <strong>{nombre}</strong>
                      {h.ultimo_mensaje_el && <span className="texto-chico">{cuando(h.ultimo_mensaje_el)}</span>}
                    </span>
                    <span className="bandeja-hilo-fila">
                      <span className="bandeja-hilo-ultimo">{h.ultimo_mensaje || 'Sin mensajes todavia'}</span>
                      {h.no_leidos > 0 && (
                        <span className="bandeja-sin-leer" aria-label={`${h.no_leidos} sin leer`}>{h.no_leidos}</span>
                      )}
                    </span>
                  </span>
                </button>
              </li>
            )
          })}
        </ul>
      )}
    </aside>
  )
}
