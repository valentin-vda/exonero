/**
 * Marcador de posicion para las pantallas que todavia no estan hechas.
 *
 * Existe para que la navegacion funcione entera desde el dia uno: se puede
 * hacer clic en cualquier enlace del menu sin que la app se rompa, y cada uno
 * ve de un vistazo que pantalla le toca y de que numero del mockup viene.
 *
 * A medida que cada uno hace la suya, reemplaza el uso de este componente en
 * App.jsx por la pantalla de verdad.
 */

export default function EnConstruccion({ nombre, codigo, dueno, descripcion }) {
  return (
    <div style={{ maxWidth: '680px', margin: '60px auto', textAlign: 'center' }}>
      <span className="tag tag-neutral">{codigo}</span>
      <h2 style={{ marginTop: '14px' }}>{nombre}</h2>
      <p className="text-muted">{descripcion}</p>
      <p className="text-muted" style={{ fontSize: '13px' }}>
        Pantalla pendiente. Le toca a <strong>{dueno}</strong>.
      </p>
    </div>
  )
}
