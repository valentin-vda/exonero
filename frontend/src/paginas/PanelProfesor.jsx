/**
 * 1d - Panel del profesor. Ruta: /panel
 *
 * Es la pantalla de entrada del profesor: como viene su semana y su plata.
 *
 * Como esta armada, de arriba hacia abajo (como en el mockup):
 *
 *   PanelProfesor           <- esta pantalla: pide los datos de cada bloque
 *   |                          y guarda lo elegido en los tres selectores
 *   +-- Saludo              "Hola, Lucia", materias y barrio       (la ficha)
 *   +-- ProximaClase        la tarjeta naranja                     /clases/proxima
 *   +-- Indicadores         las cinco cifras + Mes/Trimestre/Anio  /clases/metricas
 *   |                                                              /pagos/ingresos
 *   +-- ReservasDeHoy       la tabla de hoy                        /clases?desde=&hasta=
 *   +-- Ingresos            cifras + barras + Semana/Mes/Anio      /pagos/ingresos
 *   +-- ReservasEnElTiempo  barras apiladas + 10 semanas/Mes/Anio  /clases/series
 *
 * Las piezas estan en src/paginas/panel/.
 *
 * Cada bloque tiene su propio estado (useBloque): sus datos, su "cargando" y
 * su error. Si una llamada falla, ese bloque muestra el error y los demas se
 * ven igual. Y cambiar un selector recarga solo el bloque de ese selector.
 */

import { useEffect, useState } from 'react'

import { listarClases, metricas, proximaClase, series } from '../api/clases.js'
import { ingresos } from '../api/pagos.js'
import { obtenerMiFicha } from '../api/perfiles.js'
import { hoy } from './panel/fechas.js'
import Indicadores from './panel/Indicadores.jsx'
import Ingresos from './panel/Ingresos.jsx'
import ProximaClase from './panel/ProximaClase.jsx'
import ReservasDeHoy from './panel/ReservasDeHoy.jsx'
import ReservasEnElTiempo from './panel/ReservasEnElTiempo.jsx'
import Saludo from './panel/Saludo.jsx'
import useBloque from './panel/useBloque.js'

export default function PanelProfesor() {
  // Lo elegido en cada selector. Arrancan como en el mockup.
  const [periodo, setPeriodo] = useState('mes')
  const [agruparIngresos, setAgruparIngresos] = useState('mes')
  const [agruparReservas, setAgruparReservas] = useState('semana')

  // Un bloque por llamada. Los indicadores son dos (metricas y el cobrado),
  // para que si falla una se vean igual las cifras de la otra.
  const ficha = useBloque()
  const proxima = useBloque()
  const numeros = useBloque()
  const cobrado = useBloque()
  const deHoy = useBloque()
  const plata = useBloque()
  const reservas = useBloque()

  // Al entrar: todo a la vez. Cada cargar() atrapa su propio error (ver
  // useBloque.js), asi que Promise.all nunca falla entero por una llamada: el
  // bloque que fallo muestra su error y el resto del panel sigue.
  useEffect(() => {
    const dia = hoy()
    Promise.all([
      ficha.cargar(obtenerMiFicha()),
      proxima.cargar(proximaClase()),
      numeros.cargar(metricas(periodo)),
      cobrado.cargar(ingresos(periodo)),
      deHoy.cargar(listarClases({ desde: dia, hasta: dia })),
      plata.cargar(ingresos('mes', agruparIngresos)),
      reservas.cargar(series(agruparReservas)),
    ])
    // [] = una sola vez, al entrar. Despues, cada selector recarga lo suyo
    // desde su funcion de abajo.
  }, [])

  function cambiarPeriodo(nuevo) {
    setPeriodo(nuevo)
    numeros.cargar(metricas(nuevo))
    cobrado.cargar(ingresos(nuevo))
  }

  function cambiarAgruparIngresos(nuevo) {
    setAgruparIngresos(nuevo)
    plata.cargar(ingresos('mes', nuevo))
  }

  function cambiarAgruparReservas(nuevo) {
    setAgruparReservas(nuevo)
    reservas.cargar(series(nuevo))
  }

  return (
    <div className="tablero">
      <Saludo ficha={ficha} />
      <ProximaClase bloque={proxima} />
      <Indicadores periodo={periodo} alCambiarPeriodo={cambiarPeriodo} metricas={numeros} cobrado={cobrado} />
      <ReservasDeHoy bloque={deHoy} proxima={proxima.datos} />
      <Ingresos bloque={plata} agrupar={agruparIngresos} alCambiarAgrupar={cambiarAgruparIngresos} />
      <ReservasEnElTiempo bloque={reservas} agrupar={agruparReservas} alCambiarAgrupar={cambiarAgruparReservas} />
    </div>
  )
}
