/**
 * El circulo con la foto de la persona, o sus iniciales si no tiene foto.
 *
 * Aparece en tres tamanios: en la barra de arriba (chico), en el menu lateral
 * del perfil (mediano) y en la cabecera del perfil (grande).
 *
 * Uso:
 *   <Avatar persona={usuario} />
 *   <Avatar persona={usuario} tamanio="grande" />
 *
 * `persona` es cualquier objeto con nombre, apellido y foto_base64: el
 * usuario de useAuth(), una ficha de profesor, etc.
 */

import { iniciales } from '../utiles/formato.js'

// Que clase de CSS le toca a cada tamanio (estan en componentes.css y perfil.css).
const CLASES = {
  chico: 'avatar',
  mediano: 'avatar avatar-mediano',
  grande: 'avatar avatar-grande',
}

export default function Avatar({ persona, tamanio = 'chico' }) {
  return (
    <div className={CLASES[tamanio]} title={`${persona?.nombre || ''} ${persona?.apellido || ''}`}>
      {/* Si hay foto, la foto. Si no, las iniciales. Es un "if" adentro del
          JSX: condicion ? esto : aquello. */}
      {persona?.foto_base64 ? <img src={persona.foto_base64} alt="" /> : iniciales(persona)}
    </div>
  )
}
