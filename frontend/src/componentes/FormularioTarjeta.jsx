/**
 * Los campos de una tarjeta nueva: numero, titular, vencimiento y codigo de
 * seguridad. Es el MISMO formulario en dos pantallas:
 *   - el checkout (1g), en "Agregar tarjeta nueva"
 *   - "Medios de pago" de 1e, en "Agregar medio de pago"
 *
 * Solo dibuja los campos: no tiene <form> ni boton. Cada pantalla lo mete en
 * su propio formulario y decide que pasa al enviar (el checkout lo da de alta
 * y enseguida reserva; 1e solo lo guarda).
 *
 * Es un componente "controlado", como un input: no guarda nada. Los valores y
 * los errores los guarda la pantalla, que es la que valida al enviar.
 *
 * Uso:
 *   const [tarjeta, setTarjeta] = useState(TARJETA_VACIA)
 *   <FormularioTarjeta campos={tarjeta} alCambiar={setTarjeta} errores={errores} />
 * y al enviar:
 *   const { errores, hayErrores } = validarTarjeta(tarjeta)
 *   agregarTarjeta(tarjetaParaBackend(tarjeta))
 * (las tres cosas estan en utiles/tarjetas.js).
 */

import { useAuth } from '../auth/ContextoAuth.jsx'
import { formatearCcv, formatearNumero, formatearVence } from '../utiles/tarjetas.js'
import Campo from './Campo.jsx'

export default function FormularioTarjeta({ id = 'tarjeta', campos, alCambiar, errores = {}, enfocar = false }) {
  const { usuario } = useAuth()

  // Devuelve la funcion que actualiza UN campo, pasando antes lo escrito por
  // su "formateador": el numero se agrupa de a cuatro, al vencimiento se le
  // pone la barra, y las letras de mas se descartan al escribirlas.
  function cambiar(campo, formatear = (texto) => texto) {
    return (texto) => alCambiar({ ...campos, [campo]: formatear(texto) })
  }

  return (
    <div className="formulario-tarjeta">
      {/* inputMode="numeric" saca el teclado de numeros en el celular, sin los
          problemas de type="number" (flechitas, y que borra los ceros de
          adelante). autoComplete deja que el navegador ofrezca las suyas. */}
      <Campo
        id={`${id}-numero`}
        etiqueta="Numero de tarjeta"
        valor={campos.numero}
        alCambiar={cambiar('numero', formatearNumero)}
        error={errores.numero}
        inputMode="numeric"
        autoComplete="cc-number"
        placeholder="0000 0000 0000 0000"
        autoFocus={enfocar}
      />
      <Campo
        id={`${id}-titular`}
        etiqueta="Titular, como figura en la tarjeta"
        valor={campos.titular}
        alCambiar={cambiar('titular')}
        error={errores.titular}
        autoComplete="cc-name"
        placeholder={`${usuario.nombre} ${usuario.apellido}`}
      />
      <div className="formulario-tarjeta-fila">
        <Campo
          id={`${id}-vence`}
          etiqueta="Vencimiento"
          valor={campos.vence}
          alCambiar={cambiar('vence', formatearVence)}
          error={errores.vence}
          inputMode="numeric"
          autoComplete="cc-exp"
          placeholder="MM/AA"
        />
        <Campo
          id={`${id}-ccv`}
          etiqueta="Codigo de seguridad"
          valor={campos.ccv}
          alCambiar={cambiar('ccv', formatearCcv)}
          error={errores.ccv}
          inputMode="numeric"
          autoComplete="cc-csc"
          placeholder="123"
        />
      </div>
    </div>
  )
}
