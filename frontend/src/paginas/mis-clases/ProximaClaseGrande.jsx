/**
 * La proxima clase en grande (1b), con GET /api/clases/proxima:
 *
 *   PROXIMA CLASE · en 2 h 15 min
 *   Matematica con Lucia Fernandez                      [Mensaje] [Ver detalle]
 *   Jueves 22 de octubre · 17:00 a 18:30 · Presencial · Av. Brasil 2550
 *
 * "Ver detalle" abre el detalle de la clase (DetalleClase) abajo, con
 * Reprogramar y Cancelar. Si no hay ninguna confirmada por delante, invita a
 * buscar profe.
 */

import { Link } from 'react-router-dom'

import Alerta from '../../componentes/Alerta.jsx'
import Avatar from '../../componentes/Avatar.jsx'
import BotonMensaje from '../../componentes/BotonMensaje.jsx'
import { hora, unir } from '../../utiles/formato.js'
import { cuandoEs, cuantoFalta, finDe } from '../panel/fechas.js'
import { MODALIDAD_CLASE } from '../panel/opciones.js'

export default function ProximaClaseGrande({ bloque, alVerDetalle }) {
  const { datos: clase, error, cargando } = bloque

  if (cargando && !clase) return <section className="tablero-bloque"><p className="tablero-vacio">Cargando tu proxima clase...</p></section>
  if (error) return <Alerta tipo="error">No pudimos traer tu proxima clase. {error}</Alerta>

  if (!clase) {
    return (
      <section className="tablero-bloque mis-clases-proxima-vacia">
        <div>
          <h3>No tenes clases confirmadas por delante</h3>
          <p className="tablero-vacio">Cuando un profe apruebe tu solicitud, la vas a ver aca.</p>
        </div>
        <Link to="/buscar" className="btn btn-primary">Buscar profe</Link>
      </section>
    )
  }

  const profe = clase.contraparte
  const nombre = [profe.nombre, profe.apellido].filter(Boolean).join(' ')
  // "en 40 min" o "manana" suman algo; "el lunes 26 de octubre" ya esta en el renglon de abajo.
  const falta = cuantoFalta(clase.minutos_restantes, clase.inicio)
  const kicker = falta.startsWith('el ') ? 'Proxima clase' : `Proxima clase · ${falta}`

  return (
    <section className="mis-clases-proxima" aria-labelledby="proxima-titulo">
      <Avatar persona={profe} tamanio="mediano" />
      <div className="mis-clases-proxima-datos">
        <span className="mis-clases-kicker">{kicker}</span>
        <h3 id="proxima-titulo">{clase.materia || 'Clase particular'} con {nombre}</h3>
        <p>
          {unir([
            `${cuandoEs(clase.inicio)} · ${hora(clase.inicio)} a ${hora(finDe(clase.inicio, clase.duracion_min))}`,
            MODALIDAD_CLASE[clase.modalidad],
            clase.ubicacion,
          ])}
        </p>
      </div>
      <div className="tablero-botones">
        <BotonMensaje personaId={profe.id} className="btn btn-secondary mis-clases-proxima-mensaje" />
        <button type="button" className="btn btn-primary" onClick={() => alVerDetalle(clase)}>Ver detalle</button>
      </div>
    </section>
  )
}
