/**
 * 1g - Checkout. Ruta: /checkout (solo estudiante)
 *
 * El paso 2 de 2 de reservar una clase. En el detalle del profesor (1f) el
 * alumno ya eligio materia, horario, duracion y modalidad; aca ve el desglose
 * del importe, elige con que tarjeta pagar y confirma.
 *
 * ---------------------------------------------------------------------------
 * COMO SE LLEGA: el contrato de la URL. 1f (P2) navega asi:
 *
 *   /checkout?profesor=<usuario_id>&materia=<id>&inicio=<ISO 8601 con zona>
 *            &duracion=<minutos>&modalidad=presencial|online
 *            [&traslado=1][&etapa=<id>][&tema=<texto>]
 *
 *   profesor   obligatorio. El id del USUARIO profesor, el mismo de /profesor/:id
 *   materia    obligatorio. El id de la materia; tiene que ser una de las del profe
 *   inicio     obligatorio. Fecha y hora con zona: 2026-10-21T18:00:00-03:00
 *              o 2026-10-21T21:00:00Z. Sin zona no se acepta: "18:00" seria la
 *              hora de la computadora del alumno, y no hay por que adivinar.
 *   duracion   obligatorio. En minutos: 60, 90, 120...
 *   modalidad  obligatorio. presencial u online
 *   traslado   opcional. 1 si el profe va a la casa del alumno. Solo cuenta
 *              con modalidad presencial y si el profe se traslada; si no, se
 *              ignora (y cotizar no cobra traslado).
 *   etapa      opcional. El id de la etapa educativa
 *   tema       opcional. Texto libre ("Derivadas")
 *
 * Desde 1f, URLSearchParams se encarga de codificar todo (el "+" de la zona,
 * los espacios del tema):
 *
 *   const parametros = new URLSearchParams({
 *     profesor: ficha.id, materia: materiaId, inicio: horario.inicio,
 *     duracion: 90, modalidad: 'presencial',
 *   })
 *   navegar(`/checkout?${parametros}`)
 *
 * Va en la URL y no en el state del router para que sobreviva a un recargar.
 * Si falta algo o no tiene sentido, la pantalla lo dice y ofrece volver a
 * buscar, sin romperse.
 * ---------------------------------------------------------------------------
 *
 * Como esta armada:
 *
 *   Checkout                  <- esta pantalla: lee la URL, carga, confirma
 *   +-- la tarjeta verde      <- la clase elegida, con "Cambiar"
 *   +-- ElegirMedio           <- las tarjetas guardadas o una nueva
 *   +-- Resumen               <- el desglose y "Confirmar reserva"
 *   +-- ReservaEnviada        <- el cartel del final
 *
 * Que llamadas hace:
 *   al entrar, las cuatro AL MISMO TIEMPO (Promise.all):
 *     GET  /api/profesores/{id}     la cabecera: nombre, foto, materias
 *     POST /api/clases/cotizar      el desglose (el MISMO calculo que 1f)
 *     GET  /api/pagos/tarjetas      las tarjetas guardadas
 *     POST /api/agenda/verificar    sigue libre el horario? (la segunda vez)
 *   al confirmar, una detras de la otra:
 *     POST   /api/pagos/tarjetas       solo si es una tarjeta nueva
 *     POST   /api/clases               la reserva: pendiente, cobro retenido
 *     DELETE /api/pagos/tarjetas/{id}  solo si la nueva NO se queria guardar
 *
 * Aca no se hace ninguna cuenta de plata: los importes salen de cotizar y de
 * crear la clase, y pesos() solo les da formato.
 */

import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { verificarHorario } from '../api/agenda.js'
import { cotizar, crearClase } from '../api/clases.js'
import { mensajeDeError } from '../api/mensajes.js'
import { agregarTarjeta, borrarTarjeta, listarTarjetas } from '../api/pagos.js'
import { obtenerFichaPublica } from '../api/perfiles.js'
import Alerta from '../componentes/Alerta.jsx'
import Avatar from '../componentes/Avatar.jsx'
import { SEPARADOR, diaYHora, unir } from '../utiles/formato.js'
import {
  NUEVA,
  TARJETA_VACIA,
  nombreTarjeta,
  tarjetaParaBackend,
  tarjetaVencida,
  validarTarjeta,
} from '../utiles/tarjetas.js'
import ElegirMedio from './checkout/ElegirMedio.jsx'
import ReservaEnviada from './checkout/ReservaEnviada.jsx'
import Resumen from './checkout/Resumen.jsx'

// ---------------------------------------------------------------------------
// Leer la URL
// ---------------------------------------------------------------------------

const MODALIDADES = ['presencial', 'online']

// Fecha y hora con zona al final: Z, o +hh:mm / -hh:mm.
const RE_FECHA_CON_ZONA = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:\d{2})$/

/** "12" -> 12. Cualquier otra cosa (vacio, "abc", "0", "-3", "1.5") -> null. */
function enteroPositivo(texto) {
  if (!/^\d+$/.test(texto || '')) return null
  const numero = Number(texto)
  return numero > 0 ? numero : null
}

/**
 * Lee la reserva de la URL. Devuelve { reserva } si esta todo bien, o
 * { problema } con el texto para mostrarle al alumno.
 */
function leerReserva(parametros) {
  // En una URL escrita a mano, el "+" de "+00:00" llega como un espacio (en
  // las URLs, "+" quiere decir espacio). Se devuelve a su lugar.
  const inicio = (parametros.get('inicio') || '').replace(/ (\d{2}:\d{2})$/, '+$1')
  const etapa = parametros.get('etapa')

  const reserva = {
    profesorId: enteroPositivo(parametros.get('profesor')),
    materiaId: enteroPositivo(parametros.get('materia')),
    etapaId: etapa ? enteroPositivo(etapa) : null,
    tema: (parametros.get('tema') || '').trim() || null,
    inicio,
    duracion: enteroPositivo(parametros.get('duracion')),
    modalidad: parametros.get('modalidad'),
  }
  // El traslado es que el profe vaya a la casa del alumno: online no tiene.
  reserva.conTraslado = reserva.modalidad === 'presencial' && parametros.get('traslado') === '1'

  const completa =
    reserva.profesorId &&
    reserva.materiaId &&
    reserva.duracion &&
    MODALIDADES.includes(reserva.modalidad) &&
    RE_FECHA_CON_ZONA.test(inicio) &&
    !Number.isNaN(Date.parse(inicio)) &&
    (!etapa || reserva.etapaId)

  if (!completa) {
    return {
      problema:
        'Al enlace de esta reserva le faltan datos o tiene alguno que no es valido. Busca al profe y ' +
        'elegi el horario de nuevo desde su perfil.',
    }
  }
  if (Date.parse(inicio) <= Date.now()) {
    return { problema: 'Ese horario ya paso. Elegi otro desde el perfil del profe.', profesorId: reserva.profesorId }
  }
  return { reserva }
}

// ---------------------------------------------------------------------------
// Textos
// ---------------------------------------------------------------------------

/** 90 -> "1,5 h"; 45 -> "45 min". */
function duracionTexto(minutos) {
  if (minutos < 60) return `${minutos} min`
  return `${(minutos / 60).toLocaleString('es-UY', { maximumFractionDigits: 2 })} h`
}

/**
 * Por que el horario ya no se puede reservar: el motivo de
 * POST /agenda/verificar cuando responde { libre: false, motivo }.
 */
function textoMotivo(motivo, ficha) {
  const textos = {
    ocupado: `${ficha.nombre} ya tiene una clase aprobada en ese horario.`,
    bloqueado: `${ficha.nombre} bloqueo ese dia u horario en su agenda.`,
    fuera_de_franja: `${ficha.nombre} no da clases en ese horario.`,
    aviso_minimo: `${ficha.nombre} pide reservar con al menos ${ficha.aviso_minimo_horas} horas de anticipacion.`,
    tope_diario: `${ficha.nombre} ya llego a su maximo de clases para ese dia.`,
  }
  return `${textos[motivo] || 'Ese horario ya no esta disponible.'} Elegi otro horario.`
}

/**
 * Lo que se ve cuando no se puede armar la reserva: que paso y por donde
 * seguir. Si se sabe de que profe era, se ofrece volver a su perfil.
 */
function SinReserva({ texto, profesorId = null }) {
  return (
    <section className="panel checkout-sin-reserva">
      <h4>No pudimos armar la reserva</h4>
      <Alerta tipo="error">{texto}</Alerta>
      <div className="botonera">
        {profesorId && (
          <Link to={`/profesor/${profesorId}`} className="btn btn-primary">
            Volver al perfil del profe
          </Link>
        )}
        <Link to="/buscar" className={`btn ${profesorId ? 'btn-secondary' : 'btn-primary'}`}>
          Buscar profes
        </Link>
      </div>
    </section>
  )
}

// ---------------------------------------------------------------------------
// La pantalla
// ---------------------------------------------------------------------------

export default function Checkout() {
  const [parametros] = useSearchParams()
  // useMemo: se lee la URL de nuevo solo si cambia. Sin esto, `reserva` seria
  // un objeto nuevo en cada dibujo y el useEffect de abajo correria sin parar.
  const { reserva, problema, profesorId: profesorDelProblema } = useMemo(() => leerReserva(parametros), [parametros])

  // --- Lo que se carga al entrar ---
  const [datos, setDatos] = useState(null) // { ficha, cotizacion, verificacion }
  const [tarjetas, setTarjetas] = useState([])
  const [cargando, setCargando] = useState(Boolean(reserva))
  const [errorCarga, setErrorCarga] = useState(null) // el codigo del backend

  // --- El medio de pago ---
  const [medio, setMedio] = useState(null) // el id de una tarjeta guardada, o NUEVA
  const [nueva, setNueva] = useState(TARJETA_VACIA)
  const [erroresNueva, setErroresNueva] = useState({})
  // Sin marcar de entrada: los datos de una tarjeta se guardan solo si el
  // alumno lo pide.
  const [guardarNueva, setGuardarNueva] = useState(false)

  // --- El envio ---
  const [enviando, setEnviando] = useState(false)
  const [errorEnvio, setErrorEnvio] = useState(null) // el codigo del backend
  const [reservada, setReservada] = useState(null) // { clase, tarjeta } al terminar bien

  // El estado tarda un dibujo en llegar al boton; una ref cambia en el acto.
  // Es el freno de verdad contra el doble clic (y el doble Enter).
  const enviandoAhora = useRef(false)

  // Al entrar: las cuatro llamadas al mismo tiempo.
  useEffect(() => {
    if (!reserva) return
    // Si la URL cambia antes de que lleguen las respuestas (o React desmonta
    // la pantalla), las respuestas viejas se descartan: no pisan a las nuevas.
    let vigente = true
    setCargando(true)
    setErrorCarga(null)
    Promise.all([
      obtenerFichaPublica(reserva.profesorId),
      cotizar({
        profesor_id: reserva.profesorId,
        duracion_min: reserva.duracion,
        modalidad: reserva.modalidad,
        con_traslado: reserva.conTraslado,
      }),
      listarTarjetas(),
      // La segunda verificacion del horario (la primera es en 1f). Si falla
      // por lo que sea (hoy responde 500 porque es de P3 y no esta hecho) se
      // sigue como si estuviera libre: POST /clases vuelve a verificar, y la
      // restriccion EXCLUDE de la base es la defensa de verdad.
      verificarHorario({
        profesor_id: reserva.profesorId,
        inicio: reserva.inicio,
        duracion_min: reserva.duracion,
      }).catch(() => ({ libre: true })),
    ])
      .then(([ficha, cotizacion, guardadas, verificacion]) => {
        if (!vigente) return
        setDatos({ ficha, cotizacion, verificacion })
        setTarjetas(guardadas)
        // Arranca elegida la primera tarjeta que sirva. Si no hay, la nueva.
        const primera = guardadas.find((tarjeta) => !tarjetaVencida(tarjeta))
        setMedio(primera ? primera.id : NUEVA)
      })
      // Un error que no vino del backend no trae codigo: igual hay que
      // mostrar algo (mensajeDeError da el texto generico).
      .catch((error) => vigente && setErrorCarga(error.codigo || 'desconocido'))
      .finally(() => vigente && setCargando(false))
    return () => {
      vigente = false
    }
  }, [reserva])

  // --- Los casos en que no hay checkout ---------------------------------
  if (problema) return <SinReserva texto={problema} profesorId={profesorDelProblema} />
  if (cargando) return <p className="text-muted" style={{ marginTop: '40px' }}>Preparando tu reserva...</p>
  if (errorCarga) {
    // Si el profe no existe, volver a su perfil no sirve de nada.
    const deQuien = errorCarga === 'profesor_no_existe' ? null : reserva.profesorId
    return <SinReserva texto={mensajeDeError(errorCarga)} profesorId={deQuien} />
  }

  const { ficha, cotizacion, verificacion } = datos
  const materia = ficha.materias.find((m) => m.id === reserva.materiaId)
  if (!materia) {
    return (
      <SinReserva
        texto={`${ficha.nombre} no da esa materia. Volve a su perfil y elegi una de las que ofrece.`}
        profesorId={ficha.id}
      />
    )
  }

  // --- Lo que se calcula para dibujar -------------------------------------
  const perfilDelProfe = `/profesor/${ficha.id}`
  const etapa = reserva.etapaId ? ficha.etapas.find((e) => e.id === reserva.etapaId) : null
  // Hay traslado si se pidio Y el backend lo cobro: si el profe no va a
  // domicilio, cotizar lo ignora y manda costo_traslado en cero. (Comparar
  // con cero no es hacer cuentas: el importe sigue siendo el del backend.)
  const hayTraslado = reserva.conTraslado && Number(cotizacion.costo_traslado) > 0
  const modalidad = reserva.modalidad === 'online' ? 'Online' : hayTraslado ? 'Presencial a domicilio' : 'Presencial'

  // El horario se cae si la verificacion dijo que no, o si al confirmar el
  // backend respondio que otro lo tomo (409 horario_ocupado).
  const horarioTomado = verificacion.libre === false || errorEnvio === 'horario_ocupado'

  const tarjetaElegida = tarjetas.find((tarjeta) => tarjeta.id === medio)
  const textoMedio = tarjetaElegida ? nombreTarjeta(tarjetaElegida) : 'la tarjeta nueva'

  // --- Confirmar --------------------------------------------------------
  async function confirmar(evento) {
    evento.preventDefault()
    if (enviandoAhora.current || horarioTomado || reservada) return

    // 1. Si es una tarjeta nueva, validarla antes de mandar nada.
    if (medio === NUEVA) {
      const { errores, hayErrores } = validarTarjeta(nueva)
      setErroresNueva(errores)
      if (hayErrores) {
        // El foco al primer campo con error, para corregirlo sin buscarlo.
        document.getElementById(`tarjeta-${Object.keys(errores)[0]}`)?.focus()
        return
      }
    }

    enviandoAhora.current = true
    setEnviando(true)
    setErrorEnvio(null)
    let tarjetaNueva = null
    try {
      // 2. La tarjeta nueva se da de alta primero: POST /clases pide su id.
      if (medio === NUEVA) tarjetaNueva = await agregarTarjeta(tarjetaParaBackend(nueva))
      const tarjeta = tarjetaNueva || tarjetaElegida

      // 3. La reserva. El backend vuelve a verificar el horario, congela el
      //    importe y retiene el cobro, todo junto: si algo falla (la tarjeta
      //    rechaza el pago, por ejemplo), la clase no se crea.
      const clase = await crearClase({
        profesor_id: reserva.profesorId,
        materia_id: reserva.materiaId,
        etapa_id: reserva.etapaId,
        tema: reserva.tema,
        inicio: reserva.inicio,
        duracion_min: reserva.duracion,
        modalidad: reserva.modalidad,
        con_traslado: reserva.conTraslado,
        tarjeta_id: tarjeta.id,
      })

      // 4. Si no la queria guardar, se da de baja. Es baja LOGICA: el cobro
      //    sigue apuntando a ella. Si esto falla, la reserva ya esta hecha:
      //    la tarjeta queda en "Medios de pago" y se puede quitar desde ahi.
      if (tarjetaNueva && !guardarNueva) await borrarTarjeta(tarjetaNueva.id).catch(() => null)

      setReservada({ clase, tarjeta })
    } catch (error) {
      setErrorEnvio(error.codigo || 'desconocido')
      if (tarjetaNueva && guardarNueva) {
        // La tarjeta se guardo pero la reserva no salio: pasa a la lista y
        // queda elegida, asi reintentar no la da de alta dos veces.
        setTarjetas((previas) => [...previas, tarjetaNueva])
        setMedio(tarjetaNueva.id)
        setNueva(TARJETA_VACIA)
      } else if (tarjetaNueva) {
        // No la queria guardar y no se uso: se da de baja.
        await borrarTarjeta(tarjetaNueva.id).catch(() => null)
      }
    } finally {
      enviandoAhora.current = false
      setEnviando(false)
    }
  }

  return (
    <div className="checkout">
      {/* Con el cartel de "Reserva enviada" abierto, lo de atras queda inert:
          no se puede enfocar ni lo recorre el lector de pantalla. (En React
          18 inert todavia no es un atributo conocido: va como texto vacio.) */}
      <div inert={reservada ? '' : undefined}>
        <Link to={perfilDelProfe} className="checkout-volver">
          {'‹'} Volver al perfil de {ficha.nombre}
        </Link>

        <header className="checkout-titulo">
          <span className="tag tag-neutral">Paso 2 de 2{SEPARADOR}Pago</span>
          <h2>Confirma y paga tu clase</h2>
          <p>
            La reserva queda pendiente de aprobacion del profesor. El pago se debita solo cuando {ficha.nombre} la
            aprueba.
          </p>
        </header>

        {/* Un solo formulario para toda la pantalla: Enter en un campo de la
            tarjeta es lo mismo que "Confirmar reserva". noValidate apaga los
            globitos del navegador; los errores los mostramos nosotros. */}
        <form className="checkout-columnas" onSubmit={confirmar} noValidate>
          <div className="checkout-principal">
            <section className="checkout-clase" aria-label="La clase que vas a reservar">
              <Avatar persona={ficha} tamanio="mediano" />
              <div className="checkout-clase-datos">
                <div className="checkout-clase-titulo">
                  {materia.nombre} con {ficha.nombre} {ficha.apellido}
                </div>
                <div className="checkout-clase-sub">
                  {unir([diaYHora(reserva.inicio), duracionTexto(reserva.duracion), modalidad])}
                </div>
                {(etapa || reserva.tema) && (
                  <div className="checkout-clase-sub">
                    {unir([etapa?.nombre, reserva.tema && `Tema: ${reserva.tema}`])}
                  </div>
                )}
              </div>
              <Link to={perfilDelProfe} className="btn btn-secondary checkout-clase-cambiar">
                Cambiar
              </Link>
            </section>

            {verificacion.libre === false && (
              <Alerta tipo="error">
                {textoMotivo(verificacion.motivo, ficha)} <Link to={perfilDelProfe}>Ver sus horarios</Link>
              </Alerta>
            )}

            <ElegirMedio
              tarjetas={tarjetas}
              medio={medio}
              alElegir={setMedio}
              nueva={nueva}
              alCambiarNueva={setNueva}
              errores={erroresNueva}
              guardar={guardarNueva}
              alCambiarGuardar={setGuardarNueva}
            />
          </div>

          <Resumen
            cotizacion={cotizacion}
            conTraslado={hayTraslado}
            nombreProfe={ficha.nombre}
            textoMedio={textoMedio}
            error={errorEnvio && mensajeDeError(errorEnvio)}
            extraError={errorEnvio === 'horario_ocupado' && <Link to={perfilDelProfe}>Elegir otro horario</Link>}
            puedeConfirmar={!horarioTomado && !reservada && medio !== null}
            enviando={enviando}
            volverA={perfilDelProfe}
          />
        </form>
      </div>

      {reservada && (
        <ReservaEnviada
          clase={reservada.clase}
          tarjeta={reservada.tarjeta}
          profesor={ficha}
          materia={materia.nombre}
          inicio={reserva.inicio}
        />
      )}
    </div>
  )
}
