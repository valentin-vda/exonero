/**
 * La pestania "Informacion personal" de 1j (perfil del profesor).
 *
 * Igual que la del estudiante, el formulario guarda en dos lugares:
 *
 *   PATCH /api/usuarios/yo                  nombre, apellido, documento,
 *   (cuentas, el mismo que usa 1e)          telefono, fecha de nacimiento
 *
 *   PATCH /api/perfiles/profesor/yo/personal  titulo habilitante, anios de
 *   (perfiles)                                experiencia y barrio base
 *
 * Que entra por props:
 *   ficha      lo que devolvio GET /api/perfiles/profesor/yo
 *   catalogos  la lista de barrios (entre otras), o null si no cargo
 *   alGuardar  funcion de la pantalla para volver a pedir la ficha
 */

import { useState } from 'react'

import { actualizarYo } from '../../api/auth.js'
import { mensajeDeError } from '../../api/mensajes.js'
import { guardarPersonalProfesor } from '../../api/perfiles.js'
import { useAuth } from '../../auth/ContextoAuth.jsx'
import Alerta from '../../componentes/Alerta.jsx'
import Campo from '../../componentes/Campo.jsx'
import CampoSelect from '../../componentes/CampoSelect.jsx'
import { aNumero, aTexto } from '../../utiles/formato.js'
import { validarFechaNacimiento, validarFormulario, validarTexto } from '../../utiles/validaciones.js'
import { opcionesDeCatalogo } from './opciones.js'

function valoresIniciales(usuario, ficha) {
  return {
    nombre: usuario.nombre,
    apellido: usuario.apellido,
    documento: usuario.documento || '',
    telefono: usuario.telefono || '',
    fechaNacimiento: usuario.fecha_nacimiento || '',
    barrioId: aTexto(ficha.barrio_id),
    titulo: ficha.titulo_habilitante || '',
    anios: aTexto(ficha.anios_experiencia),
  }
}

export default function SeccionDatosProfesor({ ficha, catalogos, alGuardar }) {
  const { usuario, refrescar } = useAuth()
  const [campos, setCampos] = useState(() => valoresIniciales(usuario, ficha))
  const [errores, setErrores] = useState({})
  const [mensaje, setMensaje] = useState(null)
  const [guardando, setGuardando] = useState(false)

  function cambiar(campo) {
    return (valor) => setCampos((previos) => ({ ...previos, [campo]: valor }))
  }

  const opcionesBarrio = opcionesDeCatalogo(catalogos?.barrios, ficha.barrio_id, ficha.barrio)

  async function guardar(evento) {
    evento.preventDefault()

    const { errores: nuevos, hayErrores } = validarFormulario({
      nombre: () => validarTexto(campos.nombre, 'tu nombre', 2),
      apellido: () => validarTexto(campos.apellido, 'tu apellido', 2),
      fechaNacimiento: () => validarFechaNacimiento(campos.fechaNacimiento),
      anios: () => (campos.anios !== '' && Number(campos.anios) < 0 ? 'No puede ser negativo.' : null),
    })
    setErrores(nuevos)
    setMensaje(null)
    if (hayErrores) return

    setGuardando(true)
    try {
      // 1. La cuenta.
      await actualizarYo({
        nombre: campos.nombre.trim(),
        apellido: campos.apellido.trim(),
        documento: campos.documento.trim() || null,
        telefono: campos.telefono.trim() || null,
        fecha_nacimiento: campos.fechaNacimiento || null,
      })

      // 2. Lo del profesor. Es un PATCH: si el barrio no cambio, no se mandan
      //    las coordenadas y quedan las que estaban.
      const cuerpo = {
        titulo_habilitante: campos.titulo.trim() || null,
        anios_experiencia: aNumero(campos.anios),
        barrio_id: aNumero(campos.barrioId),
      }
      if (campos.barrioId !== aTexto(ficha.barrio_id)) {
        // Sin geocodificacion: el punto del mapa es el centro del barrio.
        const barrio = catalogos?.barrios.find((b) => String(b.id) === campos.barrioId)
        cuerpo.latitud = barrio?.latitud ?? null
        cuerpo.longitud = barrio?.longitud ?? null
      }
      await guardarPersonalProfesor(cuerpo)

      // 3. Avisar al resto de la app.
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
    setCampos(valoresIniciales(usuario, ficha))
    setErrores({})
    setMensaje(null)
  }

  return (
    <section className="panel">
      <h4>Informacion personal</h4>

      <Alerta tipo={mensaje?.tipo}>{mensaje?.texto}</Alerta>

      <form onSubmit={guardar} noValidate>
        <div className="grilla-2">
          <Campo id="nombre" etiqueta="Nombre" valor={campos.nombre} alCambiar={cambiar('nombre')}
                 error={errores.nombre} requerido autoComplete="given-name" />
          <Campo id="apellido" etiqueta="Apellido" valor={campos.apellido} alCambiar={cambiar('apellido')}
                 error={errores.apellido} requerido autoComplete="family-name" />

          <Campo id="documento" etiqueta="Cedula de identidad" valor={campos.documento}
                 alCambiar={cambiar('documento')} placeholder="1.234.567-8" />
          <Campo id="correo" etiqueta="Correo electronico" tipo="email" valor={usuario.correo}
                 alCambiar={() => {}} disabled ayuda="Es tu usuario: no se puede cambiar." />

          <Campo id="telefono" etiqueta="Telefono" tipo="tel" valor={campos.telefono}
                 alCambiar={cambiar('telefono')} autoComplete="tel" placeholder="099 123 456" />
          <Campo id="fechaNacimiento" etiqueta="Fecha de nacimiento" tipo="date" valor={campos.fechaNacimiento}
                 alCambiar={cambiar('fechaNacimiento')} error={errores.fechaNacimiento} />

          <CampoSelect id="barrio" etiqueta="Barrio base" valor={campos.barrioId} alCambiar={cambiar('barrioId')}
                       opciones={opcionesBarrio} disabled={!catalogos}
                       ayuda="Es donde te ubica el mapa de la busqueda." />
          <Campo id="titulo" etiqueta="Titulo habilitante" valor={campos.titulo} alCambiar={cambiar('titulo')}
                 placeholder="Profesorado de Matematica, IPA" />

          <Campo id="anios" etiqueta="Anios de experiencia" tipo="number" min="0" valor={campos.anios}
                 alCambiar={cambiar('anios')} error={errores.anios} />
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
