/**
 * La tarjeta verde de arriba de los perfiles (1e y 1j):
 *
 *   ( foto )  Martina Silva
 *             5.o de Bachillerato · Liceo Bauza · Cordon     [Cambiar foto]
 *             [Miembro desde marzo de 2026] [4,8 · 9 resenas]
 *
 * El subtitulo y las etiquetas los decide cada pantalla. Lo que es igual en
 * las dos (la foto, el nombre y el boton de cambiar la foto) vive aca.
 *
 * Cambiar la foto, paso a paso:
 *   1. El usuario toca "Cambiar foto" y elige un archivo.
 *   2. achicarImagen() la achica a 400 px (ver utiles/imagenes.js).
 *   3. PUT /api/usuarios/yo/foto la guarda.
 *   4. refrescar() trae el usuario con la foto nueva, y se actualizan solos
 *      la cabecera, el menu lateral y el circulito de la barra de arriba.
 */

import { useState } from 'react'

import { cambiarFoto } from '../../api/auth.js'
import { mensajeDeError } from '../../api/mensajes.js'
import { useAuth } from '../../auth/ContextoAuth.jsx'
import Avatar from '../../componentes/Avatar.jsx'
import { achicarImagen } from '../../utiles/imagenes.js'

export default function CabeceraPerfil({ subtitulo, children }) {
  const { usuario, refrescar } = useAuth()
  const [subiendo, setSubiendo] = useState(false)
  const [error, setError] = useState(null)

  async function alElegirArchivo(evento) {
    const archivo = evento.target.files[0]
    // Se vacia el input para que elegir OTRA VEZ el mismo archivo tambien
    // dispare el evento (si no, el navegador cree que no cambio nada).
    evento.target.value = ''
    if (!archivo) return

    setError(null)
    setSubiendo(true)
    try {
      const foto = await achicarImagen(archivo, 400)
      await cambiarFoto(foto)
      await refrescar()
    } catch (err) {
      setError(mensajeDeError(err.codigo))
    } finally {
      setSubiendo(false)
    }
  }

  return (
    <section className="cabecera-perfil">
      <Avatar persona={usuario} tamanio="grande" />

      <div className="cabecera-perfil-datos">
        <div className="cabecera-perfil-nombre">
          {usuario.nombre} {usuario.apellido}
        </div>
        {/* && en JSX: "si hay subtitulo, mostra esto". Si no hay, nada. */}
        {subtitulo && <div className="cabecera-perfil-sub">{subtitulo}</div>}
        <div className="cabecera-perfil-etiquetas">{children}</div>
        {error && <p className="field-hint field-hint-error" style={{ paddingLeft: 0 }}>{error}</p>}
      </div>

      <div className="cabecera-perfil-accion">
        {/* Un <input type="file"> es feo y no se puede estilar. El truco: se
            esconde (oculto-visual) adentro de un <label> con forma de boton.
            Hacer clic en el label es hacer clic en el input. */}
        <label className="btn btn-secondary">
          {subiendo ? 'Subiendo...' : 'Cambiar foto'}
          <input
            type="file"
            accept="image/*"
            className="oculto-visual"
            onChange={alElegirArchivo}
            disabled={subiendo}
          />
        </label>
      </div>
    </section>
  )
}
