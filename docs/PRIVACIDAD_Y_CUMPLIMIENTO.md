# Privacidad y cumplimiento — prototipo académico

## Estado

Exonero implementa consentimiento documentado, autorización parental, acceso,
rectificación de perfiles, anonimización, minimización y auditoría. No está
habilitado para datos reales: falta identificar al responsable, aprobar los
textos jurídicos e inscribir las bases ante la URCDP.

## Inventario y finalidades

| Datos | Finalidad | Acceso | Conservación demo |
|---|---|---|---|
| Identidad y contacto | Cuenta, seguridad y coordinación | Titular y contrapartes autorizadas | Mientras la cuenta esté activa; anonimización al cancelar |
| Fecha de nacimiento | Determinar mayoría de edad | Titular y backend | Mientras la cuenta esté activa |
| Adulto responsable | Acreditar autorización parental | Titular y responsable | Contacto eliminado al anonimizar |
| Perfil educativo/profesional | Encontrar y coordinar clases | Según visibilidad del perfil | Mientras la cuenta esté activa |
| Mensajes y clases | Prestación del servicio e historial | Participantes | Política objetivo: 24 meses |
| Reseñas y promedios | Reputación dentro de la plataforma | Usuarios; autor oculto | Hasta eliminación por el autor o cancelación |
| Tarjetas ficticias | Demostración académica | Titular | Solo números de prueba; se borran al cancelar |
| Consentimientos y auditoría | Demostrar responsabilidad | Responsable | Evidencia mínima; auditoría 180 días |

No se solicitan datos sensibles. Los campos libres advierten que no deben
usarse para compartir salud, religión, origen, vida sexual u otra información
innecesaria.

## Derechos

- Acceso: descarga inmediata desde `/privacidad`.
- Rectificación: edición de cuenta y perfiles.
- Cancelación/supresión: anonimización inmediata confirmada con contraseña.
- Reseñas: únicamente el autor puede editar o eliminar la propia.
- Impugnación automatizada: no implementada por decisión del alcance; por ello
  no debe afirmarse cumplimiento ARCO integral ni habilitar producción.

## Operación pendiente antes de producción

1. Identificar razón social/persona responsable, RUT, domicilio y contacto.
2. Obtener revisión jurídica del aviso y de la matriz de conservación.
3. Inscribir todas las bases ante la URCDP y mantener actualizado el registro.
4. Realizar y aprobar una evaluación de impacto por tratar datos de menores.
5. Definir una persona que responda derechos en un máximo de cinco días hábiles.
6. Reemplazar Mailpit por un proveedor contractualizado y el pago ficticio por tokenización.
7. Cifrar discos y copias, definir restauración, monitoreo y control de acceso operativo.

## Incidentes

Ante acceso, pérdida o divulgación no autorizada: contener, preservar evidencia,
determinar titulares/datos afectados, documentar medidas y comunicar a la URCDP
dentro del plazo aplicable. El contacto y la decisión de notificar a titulares
deben quedar registrados. Nunca incluir contraseñas, tokens, PAN o CCV en logs.

## Desarrollo

- Mailpit: `docker compose up -d mailpit`, interfaz en `http://localhost:8025`.
- Migración: `alembic upgrade head`.
- Purgas: `python -m app.privacidad_mantenimiento`.
- Cómo está hecho el módulo `privacidad` (tablas, endpoints, el ciclo del
  menor, qué borra la anonimización y la deuda conocida): sección 12 de
  `docs/DOCUMENTACION.md`.
