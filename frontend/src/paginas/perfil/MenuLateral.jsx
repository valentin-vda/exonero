/**
 * El menu de la izquierda de los perfiles (1e y 1j).
 *
 *   [foto] Martina Silva
 *          Cuenta de estudiante
 *   [ Informacion personal ]   <- la pestania elegida va pintada
 *     Contrasena
 *     ...
 *   ---------------------
 *   (lo que pase la pantalla como children: en 1j, el % y el estado de la ficha)
 *   Modo claro  (o)
 *   [ Cerrar sesion ]
 *
 * Este componente no sabe que pestania esta elegida: se lo dice la pantalla
 * (prop `activa`) y le avisa cuando el usuario toca otra (prop `alElegir`).
 * La pantalla es la que guarda el estado. Es el patron de React de "subir el
 * estado": quien necesita el dato para decidir que mostrar, lo guarda.
 */

import { useAuth } from '../../auth/ContextoAuth.jsx'
import Avatar from '../../componentes/Avatar.jsx'
import InterruptorTema from '../../componentes/InterruptorTema.jsx'

export default function MenuLateral({ pestanias, activa, alElegir, subtitulo, children }) {
  const { usuario, salir } = useAuth()

  return (
    <aside className="menu-lateral">
      <div className="menu-lateral-quien">
        <Avatar persona={usuario} tamanio="mediano" />
        <div style={{ minWidth: 0 }}>
          <div className="menu-lateral-nombre">
            {usuario.nombre} {usuario.apellido}
          </div>
          <div className="menu-lateral-rol">{subtitulo}</div>
        </div>
      </div>

      <nav className="menu-lateral-pestanias" aria-label="Secciones del perfil">
        {pestanias.map((pestania) => (
          <button
            key={pestania.id}
            type="button"
            className="pestania"
            // aria-current marca la elegida: el CSS la pinta y el lector de
            // pantalla la anuncia como "actual".
            aria-current={pestania.id === activa ? 'page' : undefined}
            onClick={() => alElegir(pestania.id)}
          >
            {pestania.texto}
          </button>
        ))}
      </nav>

      <div className="separador" />

      {/* children = lo que la pantalla ponga entre las etiquetas de
          <MenuLateral> ... </MenuLateral>. Si no pone nada, no se dibuja nada. */}
      {children}

      <InterruptorTema />

      {/* salir() borra el token y el usuario. Sin usuario, RutaProtegida
          manda solo al login: no hace falta navegar a mano. */}
      <button type="button" className="btn btn-secondary btn-block" style={{ margin: 0 }} onClick={salir}>
        Cerrar sesion
      </button>
    </aside>
  )
}
