import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { descargarMisDatos, obtenerAviso } from '../api/privacidad.js'
import { useAuth } from '../auth/ContextoAuth.jsx'
import Alerta from '../componentes/Alerta.jsx'

export default function Privacidad() {
  const { usuario } = useAuth()
  const [aviso, setAviso] = useState(null)
  const [mensaje, setMensaje] = useState(null)

  useEffect(() => { obtenerAviso().then(setAviso).catch(() => setMensaje('No se pudo cargar el aviso.')) }, [])

  async function exportar() {
    try {
      await descargarMisDatos()
      setMensaje('Preparamos una copia completa de tus datos.')
    } catch {
      setMensaje('No pudimos preparar la copia. Intenta nuevamente.')
    }
  }

  return (
    <main className="pagina-legal">
      <Link to={usuario ? (usuario.rol === 'profesor' ? '/panel' : '/inicio') : '/registro'}>← Volver</Link>
      <h1>Privacidad y datos personales</h1>
      <Alerta tipo={mensaje?.startsWith('Preparamos') ? 'ok' : 'error'}>{mensaje}</Alerta>
      {!aviso ? <p>Cargando...</p> : (
        <>
          <p className="demo-aviso"><strong>Prototipo academico:</strong> no ingreses datos personales ni tarjetas reales.</p>
          <h2>Como usamos tus datos</h2>
          <p>{aviso.aviso}</p>
          <h2>Si sos menor de edad</h2>
          <p>{aviso.aviso_menores}</p>
          <h2>Tus opciones</h2>
          <p>Podes ver y corregir tus datos desde tu perfil. Si estas conectado, tambien podes descargar una copia estructurada y cancelar la cuenta.</p>
          <h2>Reseñas y rankings</h2>
          <p>El puntaje es el promedio simple de las reseñas recibidas. El podio exige al menos cinco reseñas; ordena por promedio, luego por cantidad y finalmente por identificador para resolver empates. Solo el autor puede editar o eliminar su reseña. Exonero no toma decisiones legales, crediticias ni educativas basándose en ese orden.</p>
          {usuario && <button className="btn btn-primary" type="button" onClick={exportar}>Descargar mis datos</button>}
          <dl className="legal-datos">
            <dt>Version</dt><dd>{aviso.version}</dd>
            <dt>Responsable</dt><dd>{aviso.responsable}</dd>
            <dt>Contacto</dt><dd>{aviso.contacto}</dd>
          </dl>
        </>
      )}
    </main>
  )
}
