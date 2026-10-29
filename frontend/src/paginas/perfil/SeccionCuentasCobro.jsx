/**
 * La tarjeta "Cobros" de 1j (perfil del profesor). Es de P4.
 *
 * Las cuentas donde se le liquida al profesor lo que cobra: cuentas bancarias
 * o de Mercado Pago. Una es la PRINCIPAL (ahi se liquida) y las demas quedan
 * de alternativa.
 *
 *   GET    /api/pagos/cuentas                  al entrar
 *   POST   /api/pagos/cuentas                  "Agregar cuenta de cobro"
 *   PUT    /api/pagos/cuentas/{id}/principal   "Hacer principal"
 *   DELETE /api/pagos/cuentas/{id}             "Quitar", con confirmacion en linea
 *
 * Va en la pestania "Contrasena y cobros", entre cambiar la contrasena y dar
 * de baja la cuenta, que es donde la pone el mockup: PerfilProfesor.jsx se la
 * pasa a SeccionClave como children.
 *
 * El backend nunca devuelve el numero de cuenta entero: `visible` ya viene
 * como "•••• 3391". El correo de Mercado Pago si viene entero (asi lo muestra
 * el mockup, y no sirve para sacar plata).
 *
 * La forma de las filas, la confirmacion en dos pasos y el manejo del foco
 * son los de "Medios de pago" de 1e (SeccionMediosPago.jsx), con las mismas
 * clases de pagos.css: las dos listas se ven igual.
 */

import { useEffect, useRef, useState } from 'react'

import { mensajeDeError } from '../../api/mensajes.js'
import { agregarCuentaCobro, hacerPrincipal, listarCuentasCobro, quitarCuentaCobro } from '../../api/pagos.js'
import { useAuth } from '../../auth/ContextoAuth.jsx'
import Alerta from '../../componentes/Alerta.jsx'
import Campo from '../../componentes/Campo.jsx'
import CampoSelect from '../../componentes/CampoSelect.jsx'
import { SEPARADOR, unir } from '../../utiles/formato.js'
import { validarFormulario } from '../../utiles/validaciones.js'
import { BANCOS, MONEDAS } from './opciones.js'

// Los valores de un formulario vacio. Todo es texto, como en los inputs. Se
// arranca por la cuenta bancaria en pesos: es lo mas comun.
const CUENTA_VACIA = { tipo: 'banco', banco: '', numero: '', moneda: 'UYU', titular: '', correo: '' }

// Los dos tipos, para el control segmentado del formulario.
const TIPOS = [
  { valor: 'banco', texto: 'Cuenta bancaria' },
  { valor: 'mercado_pago', texto: 'Mercado Pago' },
]

// La misma regla que validarCorreo() de validaciones.js: algo, arroba, algo,
// punto y algo. La validacion en serio la hace el backend (EmailStr).
const RE_CORREO = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

// La moneda en la linea chica de cada cuenta. El desplegable dice el nombre
// entero (MONEDAS); aca alcanza con esto, y en el celular entra en una linea.
const MONEDA_CORTA = { UYU: 'En pesos', USD: 'En dólares' }

/** El numero sin los espacios ni los guiones con que se suele escribir. */
function numeroLimpio(texto) {
  return texto.replace(/[\s-]/g, '')
}

/**
 * Una cuenta guardada -> "Cuenta bancaria · BROU •••• 3391" o
 * "Mercado Pago · correo", como texto: para los mensajes y los aria-label.
 */
function nombreCuenta(cuenta) {
  return cuenta.tipo === 'banco'
    ? unir(['Cuenta bancaria', `${cuenta.banco_nombre} ${cuenta.visible}`])
    : unir(['Mercado Pago', cuenta.visible])
}

/**
 * Lo mismo que nombreCuenta(), para dibujar. La diferencia es donde puede
 * cortarse la linea en el celular: "BROU •••• 3391" nunca se separa
 * (.cuenta-dato, en perfil.css), y un correo largo se corta antes de la
 * arroba (<wbr> es "aca se puede cortar si hace falta"), no en cualquier
 * letra.
 */
function NombreCuenta({ cuenta }) {
  if (cuenta.tipo === 'banco') {
    return (
      <>
        Cuenta bancaria{SEPARADOR}
        <span className="cuenta-dato">
          {cuenta.banco_nombre} {cuenta.visible}
        </span>
      </>
    )
  }
  const arroba = cuenta.visible.indexOf('@')
  return (
    <>
      Mercado Pago{SEPARADOR}
      {cuenta.visible.slice(0, arroba)}
      <wbr />
      {cuenta.visible.slice(arroba)}
    </>
  )
}

/**
 * La linea chica de abajo: si es la principal o una alternativa (como en el
 * mockup) y, de un banco, la moneda y el titular.
 */
function detalleCuenta(cuenta) {
  return unir([
    cuenta.es_principal ? 'Los cobros se liquidan los viernes' : 'Alternativa',
    MONEDA_CORTA[cuenta.moneda],
    cuenta.titular,
  ])
}

/**
 * Valida el formulario de una cuenta nueva. Duplica las reglas de
 * agregar_cuenta() del backend para avisar al instante: si cambian alla,
 * hay que cambiarlas aca.
 */
function validarCuenta(campos) {
  if (campos.tipo === 'mercado_pago') {
    return validarFormulario({
      correo: () => {
        if (!campos.correo.trim()) return 'Escribí el correo de tu cuenta de Mercado Pago.'
        if (!RE_CORREO.test(campos.correo.trim())) return 'Ese correo no parece válido.'
        return null
      },
    })
  }
  const numero = numeroLimpio(campos.numero)
  return validarFormulario({
    banco: () => (campos.banco ? null : 'Elegí el banco.'),
    numero: () => {
      if (!numero) return 'Escribí el número de cuenta.'
      if (!/^\d+$/.test(numero)) return 'Va solo con números (podés separarlos con espacios o guiones).'
      // 6 a 20: los mismos limites que el backend (DIGITOS_MIN y DIGITOS_MAX).
      if (numero.length < 6 || numero.length > 20) return 'Son entre 6 y 20 dígitos.'
      return null
    },
    moneda: () => (campos.moneda ? null : 'Elegí la moneda de la cuenta.'),
    titular: () => (campos.titular.trim() ? null : 'Escribí a nombre de quién está la cuenta.'),
  })
}

/**
 * Lo que se escribio -> el cuerpo de POST /api/pagos/cuentas. Solo lo que usa
 * cada tipo. Llamarla despues de validarCuenta(): da por hecho que esta bien.
 */
function cuentaParaBackend(campos) {
  if (campos.tipo === 'mercado_pago') {
    return { tipo: 'mercado_pago', identificador: campos.correo.trim() }
  }
  return {
    tipo: 'banco',
    banco: campos.banco,
    identificador: numeroLimpio(campos.numero),
    moneda: campos.moneda,
    titular: campos.titular.trim(),
  }
}

export default function SeccionCuentasCobro() {
  const { usuario } = useAuth()

  // --- Las cuentas guardadas ---
  const [cuentas, setCuentas] = useState([])
  const [cargando, setCargando] = useState(true)
  // Si no se pudieron pedir, no hay que decir "no tenes cuentas": no se sabe.
  const [cargaFallida, setCargaFallida] = useState(false)
  const [mensaje, setMensaje] = useState(null) // { tipo: 'ok' | 'error', texto }
  const [ocupado, setOcupado] = useState(false) // mientras se guarda, se cambia o se quita
  // El id de la cuenta que pide confirmar el "Quitar", o null.
  const [aQuitar, setAQuitar] = useState(null)

  // --- El formulario de una cuenta nueva ---
  const [agregando, setAgregando] = useState(false)
  const [nueva, setNueva] = useState(CUENTA_VACIA)
  const [errores, setErrores] = useState({})

  const titulo = useRef(null) // el <h4>, para devolverle el foco (volverAlTitulo)

  useEffect(() => {
    listarCuentasCobro()
      .then(setCuentas)
      .catch((error) => {
        setCargaFallida(true)
        setMensaje({ tipo: 'error', texto: mensajeDeError(error.codigo) })
      })
      .finally(() => setCargando(false))
  }, [])

  /**
   * Los botones de cada fila y los del formulario desaparecen al terminar, y
   * con ellos el foco del teclado (se iria al principio de la pagina). Se lo
   * deja en el titulo, justo arriba del mensaje de como salio.
   */
  function volverAlTitulo() {
    titulo.current?.focus()
  }

  async function marcarPrincipal(cuenta) {
    setOcupado(true)
    setMensaje(null)
    try {
      // El backend devuelve todas, ya reordenadas: cambian dos filas.
      setCuentas(await hacerPrincipal(cuenta.id))
      setMensaje({ tipo: 'ok', texto: `Listo, ahora cobrás en ${nombreCuenta(cuenta)}.` })
    } catch (error) {
      setMensaje({ tipo: 'error', texto: mensajeDeError(error.codigo) })
    } finally {
      setOcupado(false)
      volverAlTitulo()
    }
  }

  async function quitar(cuenta) {
    setOcupado(true)
    setMensaje(null)
    try {
      await quitarCuentaCobro(cuenta.id)
      if (cuenta.es_principal) {
        // El backend eligio otra principal (la mas vieja que queda): se
        // vuelve a pedir la lista en vez de adivinar cual.
        setCuentas(await listarCuentasCobro())
      } else {
        // Una alternativa: la principal no cambia, alcanza con sacarla.
        setCuentas((previas) => previas.filter((c) => c.id !== cuenta.id))
      }
      setMensaje({ tipo: 'ok', texto: `Listo, se quitó ${nombreCuenta(cuenta)}.` })
    } catch (error) {
      setMensaje({ tipo: 'error', texto: mensajeDeError(error.codigo) })
    } finally {
      setAQuitar(null)
      setOcupado(false)
      volverAlTitulo()
    }
  }

  /** Lo que pasa si se quita esta cuenta, para la confirmacion. */
  function consecuencia(cuenta) {
    if (!cuenta.es_principal) return 'Tu cuenta principal no cambia.'
    // La que queda segunda en la lista es la mas vieja de las alternativas:
    // la misma que elige el backend.
    const siguiente = cuentas.find((c) => c.id !== cuenta.id)
    return siguiente
      ? `Los cobros pasan a ${nombreCuenta(siguiente)}.`
      : 'Te quedás sin cuenta de cobro hasta que agregues otra.'
  }

  function abrirFormulario() {
    setAgregando(true)
    setMensaje(null)
  }

  function cerrarFormulario() {
    setAgregando(false)
    setNueva(CUENTA_VACIA)
    setErrores({})
    volverAlTitulo()
  }

  // Devuelve la funcion que actualiza UN campo, como en SeccionClave.
  function cambiar(campo) {
    return (valor) => setNueva((previa) => ({ ...previa, [campo]: valor }))
  }

  function elegirTipo(tipo) {
    setNueva((previa) => ({ ...previa, tipo }))
    // Los errores eran de los campos del otro tipo, que ya no se ven.
    setErrores({})
  }

  async function guardarNueva(evento) {
    evento.preventDefault()

    // 1. Las mismas reglas que el backend, para avisar al instante.
    const { errores: nuevos, hayErrores } = validarCuenta(nueva)
    setErrores(nuevos)
    setMensaje(null)
    if (hayErrores) return

    setOcupado(true)
    try {
      // 2. El backend devuelve la version visible, sin el numero entero. La
      //    nueva es la mas reciente, asi que va al final (y si es la primera,
      //    el backend ya la marco principal).
      const cuenta = await agregarCuentaCobro(cuentaParaBackend(nueva))
      setCuentas((previas) => [...previas, cuenta])
      cerrarFormulario()
      setMensaje({
        tipo: 'ok',
        texto: cuenta.es_principal
          ? `Listo, se guardó ${nombreCuenta(cuenta)} como tu cuenta principal.`
          : `Listo, se guardó ${nombreCuenta(cuenta)} como alternativa.`,
      })
    } catch (error) {
      setMensaje({ tipo: 'error', texto: mensajeDeError(error.codigo) })
    } finally {
      setOcupado(false)
    }
  }

  return (
    <section className="panel panel-angosto">
      {/* tabIndex={-1}: puede recibir el foco desde el codigo, pero Tab lo saltea. */}
      <h4 ref={titulo} tabIndex={-1} style={{ marginBottom: '6px' }}>
        Cobros
      </h4>
      <p className="panel-ayuda" style={{ marginTop: 0 }}>
        Donde te depositamos lo que cobrás por tus clases. Se liquida en la cuenta principal; las otras
        quedan de alternativa.
      </p>

      <Alerta tipo={mensaje?.tipo}>{mensaje?.texto}</Alerta>

      {cargando && <p className="text-muted">Cargando tus cuentas...</p>}

      {!cargando && !cargaFallida && cuentas.length === 0 && !agregando && (
        <p className="vacio">
          Todavía no tenés cuentas de cobro. Agregá una para poder recibir lo que cobrás por tus clases.
        </p>
      )}

      {cuentas.length > 0 && (
        <ul className="tarjetas-lista">
          {cuentas.map((cuenta) => (
            <li key={cuenta.id} className="tarjeta-fila">
              <div className="medio-datos">
                <span className="medio-nombre">
                  <NombreCuenta cuenta={cuenta} />
                </span>
                <span className="medio-meta">{detalleCuenta(cuenta)}</span>
              </div>

              <div className="tarjeta-acciones">
                {/* Dos pasos, como en "Medios de pago": el primer clic solo
                    pregunta. Sin window.confirm, que corta el flujo y no se
                    puede estilar. */}
                {aQuitar === cuenta.id ? (
                  <>
                    <span className="texto-chico" id={`quitar-cuenta-${cuenta.id}`}>
                      ¿Quitar esta cuenta? {consecuencia(cuenta)}
                    </span>
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={() => quitar(cuenta)}
                      disabled={ocupado}
                      aria-describedby={`quitar-cuenta-${cuenta.id}`}
                    >
                      {ocupado ? 'Quitando...' : 'Sí, quitar'}
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
                  <>
                    {cuenta.es_principal ? (
                      <span className="tag tag-accent-2">Principal</span>
                    ) : (
                      <button
                        type="button"
                        className="btn btn-ghost"
                        onClick={() => marcarPrincipal(cuenta)}
                        disabled={ocupado}
                        aria-label={`Hacer principal: ${nombreCuenta(cuenta)}`}
                      >
                        Hacer principal
                      </button>
                    )}
                    <button
                      type="button"
                      className="btn btn-ghost"
                      onClick={() => setAQuitar(cuenta.id)}
                      disabled={ocupado}
                      aria-label={`Quitar ${nombreCuenta(cuenta)}`}
                    >
                      Quitar
                    </button>
                  </>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      {agregando && (
        <form className="tarjeta-nueva" onSubmit={guardarNueva} noValidate aria-labelledby="cuenta-nueva-titulo">
          <h5 id="cuenta-nueva-titulo">Agregar una cuenta de cobro</h5>

          <div className="field">
            <label id="cuenta-tipo-etiqueta">Dónde querés cobrar</label>
            {/* Un control segmentado: radios escondidos dentro de labels (ver
                .seg-opt en componentes.css), como la modalidad de 1j. */}
            <div className="seg seg-ancho" role="radiogroup" aria-labelledby="cuenta-tipo-etiqueta">
              {TIPOS.map((tipo, indice) => (
                <label key={tipo.valor} className="seg-opt">
                  <input
                    type="radio"
                    name="cuenta-tipo"
                    checked={nueva.tipo === tipo.valor}
                    onChange={() => elegirTipo(tipo.valor)}
                    // Al abrir el formulario, el foco queda en el primer radio.
                    autoFocus={indice === 0}
                  />
                  {tipo.texto}
                </label>
              ))}
            </div>
          </div>

          {nueva.tipo === 'banco' ? (
            <>
              <div className="grilla-2">
                <CampoSelect
                  id="cuenta-banco"
                  etiqueta="Banco"
                  valor={nueva.banco}
                  alCambiar={cambiar('banco')}
                  opciones={BANCOS}
                  vacio="Elegí el banco"
                  error={errores.banco}
                />
                <CampoSelect
                  id="cuenta-moneda"
                  etiqueta="Moneda"
                  valor={nueva.moneda}
                  alCambiar={cambiar('moneda')}
                  opciones={MONEDAS}
                  vacio={null}
                  error={errores.moneda}
                />
              </div>
              {/* inputMode="numeric": el teclado de numeros en el celular, sin
                  los problemas de type="number" (borra los ceros de adelante,
                  que en un numero de cuenta importan). */}
              <Campo
                id="cuenta-numero"
                etiqueta="Número de cuenta"
                valor={nueva.numero}
                alCambiar={cambiar('numero')}
                error={errores.numero}
                ayuda="Tal como figura en tu banco. Podés escribirlo con espacios o guiones."
                inputMode="numeric"
                autoComplete="off"
                placeholder="001234567"
              />
              <Campo
                id="cuenta-titular"
                etiqueta="Titular de la cuenta"
                valor={nueva.titular}
                alCambiar={cambiar('titular')}
                error={errores.titular}
                autoComplete="name"
                placeholder={`${usuario.nombre} ${usuario.apellido}`}
              />
            </>
          ) : (
            <Campo
              id="cuenta-correo"
              tipo="email"
              etiqueta="Correo de tu cuenta de Mercado Pago"
              valor={nueva.correo}
              alCambiar={cambiar('correo')}
              error={errores.correo}
              ayuda="Es el correo con el que entrás a Mercado Pago."
              autoComplete="email"
              placeholder={usuario.correo}
            />
          )}

          <div className="botonera">
            <button type="submit" className="btn btn-primary" disabled={ocupado}>
              {ocupado ? 'Guardando...' : 'Guardar cuenta'}
            </button>
            <button type="button" className="btn btn-ghost" onClick={cerrarFormulario} disabled={ocupado}>
              Cancelar
            </button>
          </div>
        </form>
      )}

      {/* Mientras se carga no se sabe si hay cuentas: el boton espera. */}
      {!agregando && !cargando && (
        <button type="button" className="btn btn-secondary btn-block" onClick={abrirFormulario}>
          Agregar cuenta de cobro
        </button>
      )}
    </section>
  )
}
