/**
 * Achicar una imagen en el navegador, antes de mandarla al backend.
 *
 * Por que hace falta: una foto sacada con el celular pesa 3 a 5 MB. El backend
 * acepta hasta unos 2 MB, y ademas la foto de perfil viaja en CADA
 * GET /usuarios/yo. Achicada a 800 px de lado queda en unos 100 KB y se ve
 * igual de bien en la pantalla.
 *
 * Como funciona, en tres pasos:
 *   1. FileReader lee el archivo elegido y lo convierte en un data URL
 *      ("data:image/jpeg;base64,...").
 *   2. Se carga ese data URL en un <img> (sin mostrarlo) para saber su tamanio.
 *   3. Se dibuja en un <canvas> mas chico y se exporta como JPEG.
 */

import { ErrorAPI } from '../api/cliente.js'

/**
 * @param {File} archivo        lo que eligio el usuario en el <input type="file">
 * @param {number} ladoMaximo   el lado mas largo de la imagen final, en pixeles
 * @returns {Promise<string>}   el data URL listo para mandar al backend
 */
export function achicarImagen(archivo, ladoMaximo = 800) {
  // Leer archivos en el navegador es asincronico y funciona con "eventos"
  // (onload, onerror). new Promise lo envuelve para poder usar await.
  return new Promise((resolver, rechazar) => {
    // Se usa ErrorAPI (aunque no venga del backend) para que la pantalla
    // muestre el error con mensajeDeError(), igual que cualquier otro.
    const noEsImagen = new ErrorAPI(0, 'foto_invalida')

    if (!archivo.type.startsWith('image/')) {
      rechazar(noEsImagen)
      return
    }

    const lector = new FileReader()
    lector.onerror = () => rechazar(noEsImagen)
    lector.onload = () => {
      const imagen = new Image()
      imagen.onerror = () => rechazar(noEsImagen)
      imagen.onload = () => {
        // Si ya es chica, se deja del mismo tamanio (escala 1).
        const escala = Math.min(1, ladoMaximo / Math.max(imagen.width, imagen.height))
        const lienzo = document.createElement('canvas')
        lienzo.width = Math.round(imagen.width * escala)
        lienzo.height = Math.round(imagen.height * escala)

        const pincel = lienzo.getContext('2d')
        // Fondo blanco: un PNG con partes transparentes saldria con fondo
        // negro al pasarlo a JPEG, que no tiene transparencia.
        pincel.fillStyle = '#ffffff'
        pincel.fillRect(0, 0, lienzo.width, lienzo.height)
        pincel.drawImage(imagen, 0, 0, lienzo.width, lienzo.height)

        // 0.85 = calidad del JPEG. Mas bajo pesa menos pero se nota.
        resolver(lienzo.toDataURL('image/jpeg', 0.85))
      }
      imagen.src = lector.result
    }
    lector.readAsDataURL(archivo)
  })
}
