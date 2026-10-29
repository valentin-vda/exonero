"""Tablas del modulo pagos - dueno P4.

Tres tablas: tarjeta y cobro (el lado del alumno y la plata) y cuenta_cobro
(el lado del profesor: a donde se le liquida).

cobro es LA UNICA TABLA DE PLATA de todo el sistema. No hay liquidaciones: el
historial del alumno son las filas de cobro, y los ingresos del profesor son
sum(importe) sobre sus cobros en estado cobrado. cuenta_cobro no cambia eso:
dice A DONDE iria esa plata, no cuanta es.

Por que el estado del pago no puede vivir en clase: porque la clase RECHAZADA
se borra, y el cobro liberado tiene que quedar registrado igual.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Numeric, Text, func, text
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
    #
    # NULLABLE y SET NULL, no CASCADE: al RECHAZAR se borra la clase, y el
    # cobro liberado tiene que quedar registrado (es el motivo de que la plata
    # viva en esta tabla y no en clase). Con CASCADE, borrar la clase se
    # llevaba puesto el cobro. Lo cambio la segunda migracion (P4). El UNIQUE
    # sigue valiendo: PostgreSQL permite varios NULL.
    clase_id: Mapped[int | None] = mapped_column(
        ForeignKey("clase.id", ondelete="SET NULL"), unique=True
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


class CuentaCobro(Base, Marcas):
    """Las cuentas de cobro del profesor: donde se le liquida lo que cobra. 1j.

    Dos tipos:
      banco         una cuenta bancaria: banco (de la lista fija de
                    pagos/logica.py), numero, moneda y titular
      mercado_pago  una cuenta de Mercado Pago: solo el correo

    `identificador` es el numero de cuenta (solo digitos) o el correo. Como con
    las tarjetas, el numero se guarda entero pero la API NUNCA lo devuelve
    entero: solo "•••• 3391" (ver pagos/logica.py, _cuenta_visible).

    Una de las activas es la PRINCIPAL: la que se usa para liquidar. Las demas
    son alternativas. El indice unico parcial de abajo es el que garantiza que
    haya una sola, aunque dos pedidos lleguen a la vez.

    tipo y moneda son Text con un CHECK, y no un ENUM nuevo: un ENUM obliga a
    acordarse del DROP TYPE en el downgrade (la trampa de la seccion 4 de la
    documentacion), y sumar un valor despues es mas engorroso que cambiar un
    CHECK.
    """

    __tablename__ = "cuenta_cobro"
    __table_args__ = (
        CheckConstraint("tipo IN ('banco', 'mercado_pago')", name="tipo_cuenta_valido"),
        CheckConstraint("moneda IN ('UYU', 'USD')", name="moneda_valida"),
        # Lo que pide cada tipo, tambien en la base: una cuenta bancaria sin
        # banco, moneda o titular no sirve para liquidar, y una de Mercado
        # Pago no tiene ninguna de las tres.
        CheckConstraint(
            "(tipo = 'banco' AND banco IS NOT NULL AND moneda IS NOT NULL AND titular IS NOT NULL)"
            " OR (tipo = 'mercado_pago' AND banco IS NULL AND moneda IS NULL AND titular IS NULL)",
            name="datos_segun_tipo",
        ),
        # Una sola principal ACTIVA por profesor. Parcial: las alternativas y
        # las dadas de baja no cuentan, asi que puede haber muchas de esas.
        # text() en minuscula: ver la trampa del postgresql_where en la
        # seccion 4 de la documentacion.
        Index(
            "ux_cuenta_cobro_principal", "usuario_id",
            unique=True, postgresql_where=text("es_principal AND activa"),
        ),
    )

    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(Text, nullable=False)
    # El codigo del banco ("brou", "itau"...), no el nombre que se muestra.
    banco: Mapped[str | None] = mapped_column(Text)
    identificador: Mapped[str] = mapped_column(Text, nullable=False)
    titular: Mapped[str | None] = mapped_column(Text)
    moneda: Mapped[str | None] = mapped_column(Text)
    es_principal: Mapped[bool] = mapped_column(nullable=False, default=False)
    # Baja logica, como las tarjetas: la fila queda para saber a donde se
    # liquido antes, aunque el profesor ya no la use.
    activa: Mapped[bool] = mapped_column(nullable=False, default=True)
