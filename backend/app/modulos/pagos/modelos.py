"""Tablas del modulo pagos - dueno P4.

Dos tablas: tarjeta y cobro.

cobro es LA UNICA TABLA DE PLATA de todo el sistema. No hay liquidaciones ni
cuenta bancaria del profesor: el historial del alumno son las filas de cobro,
y los ingresos del profesor son sum(importe) sobre sus cobros en estado
cobrado.

Por que el estado del pago no puede vivir en clase: porque la clase RECHAZADA
se borra, y el cobro liberado tiene que quedar registrado igual.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, Marcas
from app.enums import EstadoCobro


class Tarjeta(Base, Marcas):
    """Las tarjetas del alumno. No hay tarjeta principal: elige una en cada compra.

    ============================= ATENCION ==================================
    Guardar el numero completo y el CCV es aceptable en este trabajo academico
    con datos inventados, y simplifica mucho: no hay pasarela de pago.

    Ninguna plataforma real puede hacerlo, ni siquiera cifrado (lo prohibe
    PCI-DSS). Conviene decirlo en la defensa ANTES de que lo pregunten: muestra
    que la decision fue consciente y no un descuido.

    Y en la base no cargar NUNCA un numero de tarjeta real, ni propio ni de
    nadie. Los datos de prueba con 4111 1111 1111 1111 alcanzan.
    ========================================================================
    """

    __tablename__ = "tarjeta"
    __table_args__ = (CheckConstraint("vence_mes BETWEEN 1 AND 12", name="mes_valido"),)

    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False
    )
    numero: Mapped[str] = mapped_column(Text, nullable=False)
    titular: Mapped[str] = mapped_column(Text, nullable=False)
    vence_mes: Mapped[int] = mapped_column(nullable=False)
    vence_anio: Mapped[int] = mapped_column(nullable=False)
    ccv: Mapped[str] = mapped_column(Text, nullable=False)
    # Baja logica: si se borrara la fila, los cobros viejos se quedarian sin
    # tarjeta y el historial de 1e no podria decir con que se pago.
    activa: Mapped[bool] = mapped_column(nullable=False, default=True)


class Cobro(Base, Marcas):
    """El dinero de una clase. Una fila por clase, y solo una.

    Ciclo de vida:
      retenido    al crear la clase, en 1g
      cobrado     cuando el profesor aprueba, en 1i
      liberado    cuando el profesor rechaza (la clase se borra, esto queda)
      reembolsado cuando se cancela una clase ya aprobada
    """

    __tablename__ = "cobro"
    __table_args__ = (Index("ix_cobro_estado", "estado"),)

    # UNIQUE: una clase tiene exactamente un cobro.
    clase_id: Mapped[int] = mapped_column(
        ForeignKey("clase.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    tarjeta_id: Mapped[int | None] = mapped_column(ForeignKey("tarjeta.id"))
    # Copia del total de la clase al momento de retener. Si la clase cambiara,
    # el movimiento de plata ya registrado no tiene que cambiar con ella.
    importe: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    estado: Mapped[EstadoCobro] = mapped_column(
        Enum(EstadoCobro, name="cobro_enum"), nullable=False, default=EstadoCobro.retenido
    )

    # Un timestamp por transicion, en vez de un historial aparte: alcanza para
    # reconstruir que paso y cuando.
    retenido_el: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    cobrado_el: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    liberado_el: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reembolsado_el: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
