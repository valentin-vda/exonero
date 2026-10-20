/**
 * El estado de un bloque del panel: los datos, el error y si esta cargando.
 *
 * Cada bloque de 1d (la proxima clase, los indicadores, los graficos...) pide
 * sus datos por separado y tiene su propio "cargando" y su propio error. Asi,
 * si una llamada falla, ese bloque muestra el error y el resto del panel se ve
 * igual. Como los seis bloques hacen lo mismo, la logica esta escrita una vez.
 *
 * Es un "hook propio": una funcion que empieza con use y adentro usa otros
 * hooks (useState, useRef). Se usa como useState:
 *
 *   const proxima = useBloque()
 *   proxima.cargar(proximaClase())     // le pasa la PROMESA de la llamada
 *   proxima.cargando / proxima.datos / proxima.error
 *
 * Por que el contador: si el profesor toca "Mes" y enseguida "Anio", salen dos
 * llamadas y la de "Mes" puede volver DESPUES. Sin el contador, la respuesta
 * vieja pisaria a la nueva. Cada cargar() se anota un numero, y al volver solo
 * se guarda la respuesta si nadie pidio otra mientras tanto.
 */

import { useRef, useState } from 'react'

import { mensajeDeError } from '../../api/mensajes.js'

export default function useBloque() {
  const [datos, setDatos] = useState(null)
  const [error, setError] = useState(null)
  const [cargando, setCargando] = useState(true)

  // useRef guarda un valor que sobrevive entre dibujos pero que, al cambiar,
  // NO redibuja. Para un contador interno es justo lo que hace falta.
  const ultimaLlamada = useRef(0)

  /** Espera la promesa y guarda lo que devuelva. Devuelve la misma promesa, ya resuelta. */
  function cargar(promesa) {
    const numero = ++ultimaLlamada.current
    const vigente = () => numero === ultimaLlamada.current

    setCargando(true)
    setError(null)
    return promesa
      .then((recibidos) => {
        if (vigente()) setDatos(recibidos)
      })
      .catch((err) => {
        if (vigente()) setError(mensajeDeError(err.codigo))
      })
      // El finally apaga el "cargando" pase lo que pase (ver "Dos cosas que
      // siempre se olvidan" en la documentacion).
      .finally(() => {
        if (vigente()) setCargando(false)
      })
  }

  return { datos, error, cargando, cargar }
}
