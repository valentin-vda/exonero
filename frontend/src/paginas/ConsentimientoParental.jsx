import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { confirmarConsentimientoParental } from '../api/privacidad.js'
import Alerta from '../componentes/Alerta.jsx'
import Campo from '../componentes/Campo.jsx'
import CampoSelect from '../componentes/CampoSelect.jsx'
import MarcoAuth from '../componentes/MarcoAuth.jsx'

export default function ConsentimientoParental() {
  const token = useMemo(() => new URLSearchParams(window.location.hash.slice(1)).get('token') || '', [])
  const [nombre, setNombre] = useState('')
  const [vinculo, setVinculo] = useState('madre')
  const [acepta, setAcepta] = useState(false)
  const [estado, setEstado] = useState(null)
  const [enviando, setEnviando] = useState(false)

  async function enviar(e) {
    e.preventDefault()
    if (!token || !nombre.trim() || !acepta) {
      setEstado({ tipo: 'error', texto: 'Completa los datos y acepta antes de continuar.' })
      return
    }
    setEnviando(true)
    try {
      await confirmarConsentimientoParental({ token, nombre_adulto: nombre.trim(), vinculo, acepta: true })
      setEstado({ tipo: 'ok', texto: 'Cuenta autorizada. El estudiante ya puede ingresar.' })
    } catch {
      setEstado({ tipo: 'error', texto: 'El enlace no es valido, ya fue usado o vencio.' })
    } finally { setEnviando(false) }
  }

  return (
    <MarcoAuth ancho>
      <h2 className="auth-titulo">Autorizacion de un adulto responsable</h2>
      <p>Exonero usara los datos del menor para su cuenta, perfil educativo, clases, mensajes y resenas. Es un prototipo academico: deben usarse datos ficticios.</p>
      <Alerta tipo={estado?.tipo}>{estado?.texto}</Alerta>
      {estado?.tipo !== 'ok' && (
        <form onSubmit={enviar}>
          <Campo id="adulto" etiqueta="Nombre completo del adulto" valor={nombre} alCambiar={setNombre} requerido />
          <CampoSelect id="vinculo" etiqueta="Vinculo" valor={vinculo} alCambiar={setVinculo} opciones={[
            { valor: 'madre', texto: 'Madre' }, { valor: 'padre', texto: 'Padre' },
            { valor: 'tutor', texto: 'Tutor' }, { valor: 'representante', texto: 'Representante legal' },
          ]} />
          <label className="privacidad-check">
            <input type="checkbox" checked={acepta} onChange={(e) => setAcepta(e.target.checked)} />
            <span>Declaro que ejerzo la representacion legal del menor y autorizo de forma libre, previa, expresa e informada el tratamiento descrito en el <Link to="/privacidad" target="_blank">aviso de privacidad</Link>.</span>
          </label>
          <button className="btn btn-primary btn-block" disabled={enviando}>{enviando ? 'Autorizando...' : 'Autorizar cuenta'}</button>
        </form>
      )}
    </MarcoAuth>
  )
}
