/**
 * La pestania "Informacion personal" de 1e (perfil del estudiante).
 *
 * Un solo formulario, pero los datos viven en DOS lugares del backend:
 *
 *   de la cuenta (modulo cuentas)     del perfil de estudiante (perfiles)
 *   PATCH /api/usuarios/yo            PUT /api/perfiles/estudiante/yo
 *   ---------------------------       ---------------------------------
 *   nombre, apellido                  etapa, nivel, centro, barrio
 *   documento, telefono               direccion
 *   fecha de nacimiento               adulto responsable
 *
 * Por eso "Guardar cambios" hace dos llamadas, y en ese orden: el backend
 * decide si el adulto responsable es obligatorio mirando la fecha de
 * nacimiento, asi que la fecha tiene que estar guardada primero.
 *
 * Que entra por props:
 *   perfil     lo que devolvio GET /api/perfiles/estudiante/yo
 *   catalogos  barrios, centros, etapas... o null si no cargaron
 *   alGuardar  funcion de la pantalla para volver a pedir el perfil
 */

import { useState } from 'react'

import { actualizarYo } from '../../api/auth.js'
import { mensajeDeError } from '../../api/mensajes.js'
import { guardarPerfilEstudiante } from '../../api/perfiles.js'
import { useAuth } from '../../auth/ContextoAuth.jsx'
import Alerta from '../../componentes/Alerta.jsx'
import Campo from '../../componentes/Campo.jsx'
import CampoSelect from '../../componentes/CampoSelect.jsx'
import { aNumero, aTexto } from '../../utiles/formato.js'
import {
  esMenorDeEdad,
  validarFechaNacimiento,
  validarFormulario,
  validarTexto,
} from '../../utiles/validaciones.js'
import { opcionesDeCatalogo } from './opciones.js'

/**
 * Los valores del formulario a partir de lo que vino del backend.
 *
 * En el estado TODO es texto, aunque sea un id o una fecha: es lo que manejan
 * los <input> y los <select>. Se convierte de vuelta al guardar.
 */
function valoresIniciales(usuario, perfil) {
  return {
    nombre: usuario.nombre,
    apellido: usuario.apellido,
    documento: usuario.documento || '',
    telefono: usuario.telefono || '',
    fechaNacimiento: usuario.fecha_nacimiento || '',
    etapaId: aTexto(perfil.etapa_id),
    nivel: perfil.nivel || '',
    centroId: aTexto(perfil.centro_id),
    barrioId: aTexto(perfil.barrio_id),
    direccion: perfil.direccion || '',
    adultoNombre: perfil.adulto_nombre || '',
    adultoTelefono: perfil.adulto_telefono || '',
  }
}

export default function SeccionPersonalEstudiante({ perfil, catalogos, alGuardar }) {
  const { usuario, refrescar } = useAuth()

  // useState con una FUNCION: React la llama una sola vez, al montar el
  // componente, para calcular el valor inicial.
  const [campos, setCampos] = useState(() => valoresIniciales(usuario, perfil))
  const [errores, setErrores] = useState({})
  const [mensaje, setMensaje] = useState(null) // { tipo, texto }
  const [guardando, setGuardando] = useState(false)

  function cambiar(campo) {
    return (valor) => setCampos((previos) => ({ ...previos, [campo]: valor }))
  }

  // Al cambiar de etapa, el nivel elegido ya no corresponde ("5.o" no existe
  // en Ciclo basico): se vacia.
  function cambiarEtapa(valor) {
    setCampos((previos) => ({ ...previos, etapaId: valor, nivel: '' }))
  }

  // --- Las opciones de los desplegables ---------------------------------
  // usuario.estudiante trae los NOMBRES actuales (la cabecera de 1a): son el
  // plan B para mostrar algo si los catalogos no cargaron.
  const cabecera = usuario.estudiante || {}
  const opcionesEtapa = opcionesDeCatalogo(catalogos?.etapas, perfil.etapa_id, cabecera.etapa)
  const opcionesCentro = opcionesDeCatalogo(catalogos?.centros, perfil.centro_id, cabecera.centro)
  const opcionesBarrio = opcionesDeCatalogo(catalogos?.barrios, perfil.barrio_id, cabecera.barrio)

  // Los niveles dependen de la etapa elegida: Bachillerato tiene 4.o, 5.o y 6.o.
  const etapaElegida = catalogos?.etapas.find((e) => String(e.id) === campos.etapaId)
  const niveles = etapaElegida ? etapaElegida.niveles || [] : campos.nivel ? [campos.nivel] : []
  const opcionesNivel = niveles.map((n) => ({ valor: n, texto: n }))

  const menor = esMenorDeEdad(campos.fechaNacimiento)

  async function guardar(evento) {
    evento.preventDefault()

    // 1. Validar en el cliente, para avisar al instante.
    const { errores: nuevos, hayErrores } = validarFormulario({
      nombre: () => validarTexto(campos.nombre, 'tu nombre', 2),
      apellido: () => validarTexto(campos.apellido, 'tu apellido', 2),
      fechaNacimiento: () => validarFechaNacimiento(campos.fechaNacimiento),
      adultoNombre: () =>
        menor && !campos.adultoNombre.trim() ? 'Como sos menor, completa el nombre de un adulto.' : null,
      adultoTelefono: () =>
        menor && !campos.adultoTelefono.trim() ? 'Y su telefono.' : null,
    })
    setErrores(nuevos)
    setMensaje(null)
    if (hayErrores) return

    setGuardando(true)
    try {
      // 2. Los datos de la cuenta. Vacio se manda como null (= sin dato).
      await actualizarYo({
        nombre: campos.nombre.trim(),
        apellido: campos.apellido.trim(),
        documento: campos.documento.trim() || null,
        telefono: campos.telefono.trim() || null,
        fecha_nacimiento: campos.fechaNacimiento || null,
      })

      // 3. Los datos del perfil. No hay geocodificacion (pasar una direccion
      //    a coordenadas), asi que el punto del mapa es el centro del barrio.
      //    Solo se recalcula si el barrio cambio.
      const barrioCambio = campos.barrioId !== aTexto(perfil.barrio_id)
      const barrio = catalogos?.barrios.find((b) => String(b.id) === campos.barrioId)
      await guardarPerfilEstudiante({
        etapa_id: aNumero(campos.etapaId),
        nivel: campos.nivel || null,
        centro_id: aNumero(campos.centroId),
        barrio_id: aNumero(campos.barrioId),
        direccion: campos.direccion.trim() || null,
        latitud: barrioCambio ? barrio?.latitud ?? null : perfil.latitud,
        longitud: barrioCambio ? barrio?.longitud ?? null : perfil.longitud,
        adulto_nombre: campos.adultoNombre.trim() || null,
        adulto_telefono: campos.adultoTelefono.trim() || null,
      })

      // 4. Que el resto de la app se entere: la cabecera, la barra de arriba
      //    y el perfil que tiene guardado la pantalla.
      await refrescar()
      await alGuardar()
      setMensaje({ tipo: 'ok', texto: 'Listo, se guardaron los cambios.' })
    } catch (error) {
      setMensaje({ tipo: 'error', texto: mensajeDeError(error.codigo) })
    } finally {
      setGuardando(false)
    }
  }

  function cancelar() {
    setCampos(valoresIniciales(usuario, perfil))
    setErrores({})
    setMensaje(null)
  }

  return (
    <section className="panel">
      <div className="panel-encabezado">
        <h4>Informacion personal</h4>
        <span className="texto-chico">Edita lo que necesites y guarda al final</span>
      </div>

      <Alerta tipo={mensaje?.tipo}>{mensaje?.texto}</Alerta>

      <form onSubmit={guardar} noValidate>
        <div className="grilla-2">
          <Campo id="nombre" etiqueta="Nombre" valor={campos.nombre} alCambiar={cambiar('nombre')}
                 error={errores.nombre} requerido autoComplete="given-name" />
          <Campo id="apellido" etiqueta="Apellido" valor={campos.apellido} alCambiar={cambiar('apellido')}
                 error={errores.apellido} requerido autoComplete="family-name" />

          <Campo id="documento" etiqueta="Cedula de identidad" valor={campos.documento}
                 alCambiar={cambiar('documento')} placeholder="1.234.567-8" />
          {/* El correo se muestra pero no se edita: es el usuario de la cuenta.
              disabled llega al <input> porque Campo pasa las props de mas. */}
          <Campo id="correo" etiqueta="Correo electronico" tipo="email" valor={usuario.correo}
                 alCambiar={() => {}} disabled ayuda="Es tu usuario: no se puede cambiar." />

          <Campo id="telefono" etiqueta="Telefono" tipo="tel" valor={campos.telefono}
                 alCambiar={cambiar('telefono')} autoComplete="tel" placeholder="099 123 456" />
          <Campo id="fechaNacimiento" etiqueta="Fecha de nacimiento" tipo="date" valor={campos.fechaNacimiento}
                 alCambiar={cambiar('fechaNacimiento')} error={errores.fechaNacimiento} />

          <CampoSelect id="etapa" etiqueta="Etapa educativa" valor={campos.etapaId} alCambiar={cambiarEtapa}
                       opciones={opcionesEtapa} disabled={!catalogos} />
          <CampoSelect id="nivel" etiqueta="Anio" valor={campos.nivel} alCambiar={cambiar('nivel')}
                       opciones={opcionesNivel} disabled={!catalogos || opcionesNivel.length === 0} />

          <CampoSelect id="centro" etiqueta="Centro educativo" valor={campos.centroId} alCambiar={cambiar('centroId')}
                       opciones={opcionesCentro} vacio="Ninguno / otro" disabled={!catalogos} />
          <CampoSelect id="barrio" etiqueta="Barrio" valor={campos.barrioId} alCambiar={cambiar('barrioId')}
                       opciones={opcionesBarrio} disabled={!catalogos} />
        </div>

        <Campo id="direccion" etiqueta="Direccion (para clases presenciales)" valor={campos.direccion}
               alCambiar={cambiar('direccion')} autoComplete="street-address" placeholder="Soriano 1234, apto. 4" />

        <div className="grilla-2">
          <Campo id="adultoNombre" etiqueta="Adulto responsable" valor={campos.adultoNombre}
                 alCambiar={cambiar('adultoNombre')} error={errores.adultoNombre} requerido={menor}
                 ayuda={menor ? 'Obligatorio porque sos menor de edad.' : 'Solo si sos menor de edad.'} />
          <Campo id="adultoTelefono" etiqueta="Telefono del adulto" tipo="tel" valor={campos.adultoTelefono}
                 alCambiar={cambiar('adultoTelefono')} error={errores.adultoTelefono} requerido={menor} />
        </div>

        <div className="botonera">
          <button type="submit" className="btn btn-primary" disabled={guardando}>
            {guardando ? 'Guardando...' : 'Guardar cambios'}
          </button>
          <button type="button" className="btn btn-ghost" onClick={cancelar} disabled={guardando}>
            Cancelar
          </button>
        </div>
      </form>
    </section>
  )
}
