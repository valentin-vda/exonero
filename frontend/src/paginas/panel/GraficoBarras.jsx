/**
 * Grafico de barras en SVG, hecho a mano (sin librerias). Lo usan los dos
 * graficos del panel: Ingresos (una serie) y Reservas en el tiempo (barras
 * apiladas por estado).
 *
 *        $ 30.000 -  ______________________________
 *        $ 15.000 -  ___________________ #_________    <- lineas guia
 *               0 -  #___#___#___#___#___#___#___#_    <- linea de base
 *                    S1  S2  S3  S4  S5  S6  S7  S8    <- etiquetas (HTML)
 *
 * Como esta hecho:
 *   - Las barras van en un <svg> con viewBox de 620 x 170 y ancho 100 %: el
 *     navegador lo escala solo, asi que en el celular se achica sin hacer nada.
 *   - Las etiquetas de los ejes NO van adentro del SVG sino en HTML, al lado y
 *     abajo. El texto de un SVG se escala con el dibujo: en un celular de
 *     375 px quedaria de 5 px y no se leeria. En HTML queda siempre de 11 px.
 *     Abajo es una grilla de tantas columnas como barras, y como cada barra
 *     ocupa una franja igual del ancho, las dos se alinean solas.
 *   - Los colores son clases de CSS (panel.css) que usan las variables de
 *     tokens.css: en modo oscuro cambian solos.
 *   - Cada columna tiene un <title>: el cartelito con el valor al pasar el
 *     mouse. Para los lectores de pantalla el SVG es una imagen con un resumen
 *     (role="img" + aria-label) y los numeros van en una tabla escondida.
 *
 * Props:
 *   titulo      el resumen ("Reservas por semana, ultimas 10 semanas")
 *   series      [{ id, texto, clase }] en el orden en que se apilan, de abajo
 *               hacia arriba. Con una sola, son barras simples y no hay leyenda.
 *   columnas    [{ clave, corta, larga, valores: { [id de serie]: numero } }]
 *   formato     numero -> texto, para el eje, el cartelito y la tabla
 *   enteros     true si los valores son cantidades (el eje no muestra "2,5")
 *   textoVacio  lo que se muestra si todas las columnas dan 0
 */

const ANCHO = 620
const ALTO = 170
const MARGEN_ARRIBA = 8 // para que la linea guia de arriba no quede cortada
const SEPARACION = 2 // el hueco entre los pedazos de una barra apilada
const RADIO = 6

/**
 * El tope del eje: el primer numero "redondo" que alcanza al maximo.
 * 17 -> 20, 24300 -> 30000. Con enteros, la mitad tambien tiene que ser
 * entera (la linea del medio no puede decir "1,5 reservas").
 */
function topeRedondo(maximo, enteros) {
  if (maximo <= 0) return enteros ? 2 : 1
  const potencia = 10 ** Math.floor(Math.log10(maximo))
  for (const paso of [1, 2, 3, 4, 5, 6, 8, 10]) {
    const tope = paso * potencia
    if (tope >= maximo && (!enteros || Number.isInteger(tope / 2))) return tope
  }
  return 10 * potencia
}

/** Un rectangulo con las dos esquinas de arriba redondeadas (y las de abajo rectas). */
function barraRedondeada(x, y, ancho, alto) {
  const r = Math.min(RADIO, ancho / 2, alto)
  const abajo = y + alto
  return `M${x},${abajo} V${y + r} A${r},${r} 0 0 1 ${x + r},${y} H${x + ancho - r} A${r},${r} 0 0 1 ${x + ancho},${y + r} V${abajo} Z`
}

export default function GraficoBarras({ titulo, series, columnas, formato, enteros = false, textoVacio }) {
  const totales = columnas.map((c) => series.reduce((suma, s) => suma + (c.valores[s.id] || 0), 0))
  const maximo = Math.max(0, ...totales)

  if (maximo === 0) return <p className="tablero-vacio">{textoVacio}</p>

  const tope = topeRedondo(maximo, enteros)
  const altoUtil = ALTO - MARGEN_ARRIBA
  const franja = ANCHO / columnas.length
  const anchoBarra = Math.min(franja * 0.55, 36)
  const simple = series.length === 1

  // Las tres lineas guia: el tope, la mitad y el cero. `y` es la altura en el
  // dibujo; `porcentaje`, la misma altura para ubicar la etiqueta en HTML.
  const marcas = [tope, tope / 2, 0].map((valor) => {
    const y = ALTO - (valor / tope) * altoUtil
    return { valor, y, porcentaje: (100 * y) / ALTO }
  })

  /** Los pedazos de una columna, de abajo hacia arriba, con su posicion. */
  function pedazos(columna) {
    let base = ALTO
    const lista = []
    for (const serie of series) {
      const valor = columna.valores[serie.id] || 0
      if (!valor) continue
      const alto = (valor / tope) * altoUtil
      lista.push({ serie, y: base - alto, alto })
      base -= alto
    }
    // El hueco va entre pedazo y pedazo: a cada uno (menos al de abajo) se le
    // recorta un poco por abajo, sin bajar de 1 para que no desaparezca.
    return lista.map((p, i) => (i === 0 ? p : { ...p, alto: Math.max(p.alto - SEPARACION, 1) }))
  }

  return (
    <div className="grafico">
      {/* El eje de la izquierda. El primer span es invisible: esta solo para
          que la columna tenga el ancho de la etiqueta mas larga (las de verdad
          estan en position: absolute y no ocupan lugar). */}
      <div className="grafico-eje-y" aria-hidden="true">
        <span className="grafico-eje-y-medida">{formato(tope)}</span>
        {marcas.map((m) => (
          <span key={m.valor} className="grafico-eje-y-marca" style={{ top: `${m.porcentaje}%` }}>
            {formato(m.valor)}
          </span>
        ))}
      </div>

      <svg className="grafico-lienzo" viewBox={`0 0 ${ANCHO} ${ALTO}`} role="img" aria-label={titulo}>
        {marcas.map((m) => (
          <line key={m.valor} className="grafico-linea" x1="0" x2={ANCHO} y1={m.y} y2={m.y} />
        ))}

        {columnas.map((columna, i) => {
          const x = i * franja + (franja - anchoBarra) / 2
          const lista = pedazos(columna)
          const actual = i === columnas.length - 1

          // El cartelito: "semana del 12 de octubre: 17" y, si es apilada, el
          // detalle por serie en los renglones de abajo.
          const detalle = simple ? [] : lista.map((p) => `${p.serie.texto}: ${formato(columna.valores[p.serie.id])}`)
          const cartel = [`${columna.larga}: ${formato(totales[i])}`, ...detalle].join('\n')

          return (
            <g key={columna.clave} className={`grafico-columna${actual ? ' grafico-columna-actual' : ''}`}>
              <title>{cartel}</title>
              {/* La franja entera, transparente: es la zona del mouse. Asi el
                  cartelito sale aunque la barra sea finita o este vacia. */}
              <rect className="grafico-zona" x={i * franja} y="0" width={franja} height={ALTO} />
              {lista.map((p, j) =>
                // Solo el pedazo de arriba lleva las esquinas redondeadas.
                j === lista.length - 1 ? (
                  <path key={p.serie.id} className={`grafico-barra ${p.serie.clase}`} d={barraRedondeada(x, p.y, anchoBarra, p.alto)} />
                ) : (
                  <rect key={p.serie.id} className={`grafico-barra ${p.serie.clase}`} x={x} y={p.y} width={anchoBarra} height={p.alto} />
                ),
              )}
            </g>
          )
        })}
      </svg>

      <div className="grafico-eje-x" style={{ '--columnas': columnas.length }} aria-hidden="true">
        {columnas.map((columna) => (
          <span key={columna.clave}>{columna.corta}</span>
        ))}
      </div>

      {/* La leyenda, solo si hay mas de una serie: con una, el titulo del
          bloque ya dice que se esta mirando. */}
      {!simple && (
        <ul className="grafico-leyenda">
          {series.map((serie) => (
            <li key={serie.id}>
              <span className={`grafico-muestra ${serie.clase}`} aria-hidden="true" />
              {serie.texto}
            </li>
          ))}
        </ul>
      )}

      {/* Los mismos datos en una tabla, para los lectores de pantalla. Se
          esconde el div y no la tabla: a una tabla el navegador no le respeta
          el overflow: hidden de oculto-visual. */}
      <div className="oculto-visual">
        <table>
          <caption>{titulo}</caption>
          <thead>
            <tr>
              <th scope="col">Periodo</th>
              {series.map((serie) => (
                <th key={serie.id} scope="col">{serie.texto}</th>
              ))}
              {!simple && <th scope="col">Total</th>}
            </tr>
          </thead>
          <tbody>
            {columnas.map((columna, i) => (
              <tr key={columna.clave}>
                <th scope="row">{columna.larga}</th>
                {series.map((serie) => (
                  <td key={serie.id}>{formato(columna.valores[serie.id] || 0)}</td>
                ))}
                {!simple && <td>{formato(totales[i])}</td>}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
