/**
 * La pestania "Medios de pago" de 1e (perfil del estudiante). Es de P4.
 *
 * Tres cosas en la misma pestania:
 *
 *   1. Las tarjetas guardadas, cada una con "Quitar"
 *        GET    /api/pagos/tarjetas        al entrar
 *        DELETE /api/pagos/tarjetas/{id}   al confirmar el "Quitar"
 *   2. "Agregar medio de pago": el MISMO formulario del checkout
 *      (FormularioTarjeta.jsx), con sus mismas reglas
 *        POST   /api/pagos/tarjetas
 *   3. "Ver historial de pagos": los cobros de las clases reservadas
 *        GET    /api/pagos/historial       (HistorialPagos.jsx)
 *
 * Las tarjetas son el mismo recurso que usa el checkout (1g): la que se
 * guarda aca aparece para elegir al reservar, y la que se guarda al reservar
 * aparece aca.
 *
 * "Quitar" es una baja LOGICA en el backend: la tarjeta deja de aparecer,
 * pero los cobros que ya se hicieron con ella la siguen nombrando, y las
 * reservas pendientes no cambian.
 *
 * Lo del mockup que no esta: la tarjeta "Principal" y "Hacer principal" (no
 * hay principal: en cada reserva se elige con que pagar), "Editar" (no hay
 * endpoint: se quita y se agrega otra), Mercado Pago (solo hay tarjetas), y
 * el tag "Depende del pago in-app" con su aclaracion (aca el pago es siempre
 * in-app, asi que la pestania se muestra siempre).
 */

import { useEffect, useRef, useState } from 'react'

import { mensajeDeError } from '../../api/mensajes.js'
import { agregarTarjeta, borrarTarjeta, listarTarjetas } from '../../api/pagos.js'
import Alerta from '../../componentes/Alerta.jsx'
import FormularioTarjeta from '../../componentes/FormularioTarjeta.jsx'
import { unir } from '../../utiles/formato.js'
import {
  TARJETA_VACIA,
  marcaCorta,
  nombreTarjeta,
  tarjetaParaBackend,
  tarjetaVencida,
  validarTarjeta,
} from '../../utiles/tarjetas.js'
import HistorialPagos from './HistorialPagos.jsx'

export default function SeccionMediosPago() {
  // --- Las tarjetas guardadas ---
  const [tarjetas, setTarjetas] = useState([])
  const [cargando, setCargando] = useState(true)
  // Si no se pudieron pedir, no hay que decir "no tenes tarjetas": no se sabe.
  const [cargaFallida, setCargaFallida] = useState(false)
  const [mensaje, setMensaje] = useState(null) // { tipo: 'ok' | 'error', texto }
  const [ocupado, setOcupado] = useState(false) // mientras se guarda o se quita
  // El id de la tarjeta que pide confirmar el "Quitar", o null. Es la
  // confirmacion en linea: el primer clic solo pregunta.
  const [aQuitar, setAQuitar] = useState(null)

  // --- El formulario de una tarjeta nueva ---
  const [agregando, setAgregando] = useState(false)
  const [nueva, setNueva] = useState(TARJETA_VACIA)
  const [errores, setErrores] = useState({})

  const [verHistorial, setVerHistorial] = useState(false)

  const titulo = useRef(null) // el <h4>, para devolverle el foco (volverAlTitulo)

  useEffect(() => {
    listarTarjetas()
      .then(setTarjetas)
      .catch((error) => {
        setCargaFallida(true)
        setMensaje({ tipo: 'error', texto: mensajeDeError(error.codigo) })
      })
      .finally(() => setCargando(false))
  }, [])

  async function quitar(tarjeta) {
    setOcupado(true)
    setMensaje(null)
    try {
      await borrarTarjeta(tarjeta.id)
      // Se saca de la lista sin volver a pedirla: el backend ya dijo que si.
      setTarjetas((previas) => previas.filter((t) => t.id !== tarjeta.id))
      setMensaje({ tipo: 'ok', texto: `Listo, se quito la ${nombreTarjeta(tarjeta)}.` })
    } catch (error) {
      setMensaje({ tipo: 'error', texto: mensajeDeError(error.codigo) })
    } finally {
      setAQuitar(null)
      setOcupado(false)
      volverAlTitulo()
    }
  }

  /**
   * Los botones de quitar y del formulario desaparecen al terminar, y con
   * ellos el foco del teclado (se iria al principio de la pagina). Se lo deja
   * en el titulo de la seccion, justo arriba del mensaje de como salio.
   */
  function volverAlTitulo() {
    titulo.current?.focus()
  }

  function abrirFormulario() {
    setAgregando(true)
    setMensaje(null)
  }

  function cerrarFormulario() {
    setAgregando(false)
    setNueva(TARJETA_VACIA)
    setErrores({})
    volverAlTitulo()
  }

  async function guardarNueva(evento) {
    evento.preventDefault()

    // 1. Las mismas reglas que el checkout, para avisar al instante.
    const { errores: nuevos, hayErrores } = validarTarjeta(nueva)
    setErrores(nuevos)
    setMensaje(null)
    if (hayErrores) return

    setOcupado(true)
    try {
      // 2. El backend devuelve la version segura: sin numero ni CCV.
      const tarjeta = await agregarTarjeta(tarjetaParaBackend(nueva))
      setTarjetas((previas) => [...previas, tarjeta])
      cerrarFormulario()
      setMensaje({ tipo: 'ok', texto: `Listo, se guardo la ${nombreTarjeta(tarjeta)}.` })
    } catch (error) {
      setMensaje({ tipo: 'error', texto: mensajeDeError(error.codigo) })
      // El mensaje sale arriba de la lista: en el celular queda fuera de la
      // pantalla, y el foco se perdio con el boton deshabilitado. El titulo
      // esta justo arriba: enfocarlo trae los dos a la vista.
      volverAlTitulo()
    } finally {
      setOcupado(false)
    }
  }

  return (
    <>
      <section className="panel">
        {/* tabIndex={-1}: puede recibir el foco desde el codigo, pero Tab lo saltea. */}
        <h4 ref={titulo} tabIndex={-1} style={{ marginBottom: '6px' }}>
          Medios de pago
        </h4>
        <p className="panel-ayuda" style={{ marginTop: 0 }}>
          Se usan para pagar las reservas dentro de Exonero. En cada reserva elegis con cual pagar, y no se
          debita nada hasta que el profe la aprueba.
        </p>

        <Alerta tipo={mensaje?.tipo}>{mensaje?.texto}</Alerta>

        {cargando && <p className="text-muted">Cargando tus tarjetas...</p>}

        {!cargando && !cargaFallida && tarjetas.length === 0 && (
          <p className="vacio">
            Todavia no tenes tarjetas guardadas. Podes agregar una aca, o guardarla cuando reserves tu
            proxima clase.
          </p>
        )}

        {tarjetas.length > 0 && (
          <ul className="tarjetas-lista">
            {tarjetas.map((tarjeta) => (
              <li key={tarjeta.id} className="tarjeta-fila">
                <span className="marca-tarjeta" aria-hidden="true">{marcaCorta(tarjeta.marca)}</span>
                <div className="medio-datos">
                  <span className="medio-nombre">{nombreTarjeta(tarjeta)}</span>
                  <span className="medio-meta">{unir([`Vence ${tarjeta.vence}`, tarjeta.titular])}</span>
                </div>
                {tarjetaVencida(tarjeta) && <span className="tag tag-neutral">Vencida</span>}

                <div className="tarjeta-acciones">
                  {/* Dos pasos, como dar de baja la cuenta: el primer clic
                      solo pregunta. Sin window.confirm, que corta el flujo y
                      no se puede estilar. */}
                  {aQuitar === tarjeta.id ? (
                    <>
                      <span className="texto-chico" id={`quitar-${tarjeta.id}`}>
                        ¿Quitar esta tarjeta? Las reservas que ya hiciste no cambian.
                      </span>
                      <button
                        type="button"
                        className="btn btn-primary"
                        onClick={() => quitar(tarjeta)}
                        disabled={ocupado}
                        aria-describedby={`quitar-${tarjeta.id}`}
                      >
                        {ocupado ? 'Quitando...' : 'Si, quitar'}
                      </button>
                      {/* El foco va a "Cancelar", la opcion que no rompe nada. */}
                      <button
                        type="button"
                        className="btn btn-ghost"
                        onClick={() => setAQuitar(null)}
                        disabled={ocupado}
                        autoFocus
                      >
                        Cancelar
                      </button>
                    </>
                  ) : (
                    <button
                      type="button"
                      className="btn btn-ghost"
                      onClick={() => setAQuitar(tarjeta.id)}
                      disabled={ocupado}
                      aria-label={`Quitar la ${nombreTarjeta(tarjeta)}`}
                    >
                      Quitar
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}

        {agregando && (
          <form className="tarjeta-nueva" onSubmit={guardarNueva} noValidate aria-labelledby="tarjeta-nueva-titulo">
            <h5 id="tarjeta-nueva-titulo">Agregar una tarjeta</h5>
            {/* enfocar: al abrirlo, el cursor queda en el numero. */}
            <FormularioTarjeta campos={nueva} alCambiar={setNueva} errores={errores} enfocar />
            <div className="botonera">
              <button type="submit" className="btn btn-primary" disabled={ocupado}>
                {ocupado ? 'Guardando...' : 'Guardar tarjeta'}
              </button>
              <button type="button" className="btn btn-ghost" onClick={cerrarFormulario} disabled={ocupado}>
                Cancelar
              </button>
            </div>
          </form>
        )}

        <div className="botonera" style={{ marginTop: '16px' }}>
          {!agregando && (
            <button type="button" className="btn btn-primary" onClick={abrirFormulario}>
              Agregar medio de pago
            </button>
          )}
          {/* aria-expanded le dice al lector de pantalla si el historial
              esta abierto o cerrado. */}
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => setVerHistorial(!verHistorial)}
            aria-expanded={verHistorial}
            aria-controls={verHistorial ? 'historial-pagos' : undefined}
          >
            {verHistorial ? 'Ocultar historial de pagos' : 'Ver historial de pagos'}
          </button>
        </div>
      </section>

      {verHistorial && <HistorialPagos />}
    </>
  )
}
