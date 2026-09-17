"""Tablas del modulo cuentas · dueno P1.

Una sola tabla: usuario. Es la unica fuente de la identidad de todo el sistema.

El cambio mas importante que trajo la revision del esquema fue separar la
cuenta del perfil. Estudiante y profesor comparten correo, clave, nombre,
documento y foto; con dos tablas paralelas habria dos lugares para hacer login,
dos para cambiar la contrasena y ninguno del cual colgar el chat, que une a los
dos. El rol es una columna, no una tabla.
"""

from datetime import date

from sqlalchemy import Date, Enum, Text
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, Marcas
from app.enums import EstadoCuenta, Rol, Tema


class Usuario(Base, Marcas):
    """La persona. De aca cuelgan los dos perfiles, las clases, el chat y las resenas."""

    __tablename__ = "usuario"

    # El correo ES la credencial y no se cambia (por eso PATCH /usuarios/yo no
    # lo acepta). citext lo hace insensible a mayusculas: Ana@ y ana@ son la misma.
    correo: Mapped[str] = mapped_column(CITEXT, nullable=False, unique=True)

    # bcrypt. La contrasena en texto plano no se guarda ni se loguea nunca.
    hash_clave: Mapped[str] = mapped_column(Text, nullable=False)

    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    apellido: Mapped[str] = mapped_column(Text, nullable=False)
    documento: Mapped[str | None] = mapped_column(Text, unique=True)
    telefono: Mapped[str | None] = mapped_column(Text)

    # Define si es menor de edad, y con eso si el adulto responsable del perfil
    # de estudiante es obligatorio.
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date)

    # Base64 en la base, no archivos en disco: una cosa menos que montar.
    # Tiene costo (la base crece), asi que las listas devuelven solo lo que
    # necesitan y no arrastran la foto en cada fila.
    foto_base64: Mapped[str | None] = mapped_column(Text)

    # Fijo al registrarse. No hay cambio de rol: quien quiera ser las dos cosas
    # se crea dos cuentas con dos correos.
    rol: Mapped[Rol] = mapped_column(Enum(Rol, name="rol_enum"), nullable=False)

    # La baja es logica: la cuenta queda inactiva y las clases pasadas se conservan.
    estado: Mapped[EstadoCuenta] = mapped_column(
        Enum(EstadoCuenta, name="estado_cuenta_enum"),
        nullable=False,
        default=EstadoCuenta.activa,
    )

    tema: Mapped[Tema] = mapped_column(
        Enum(Tema, name="tema_enum"), nullable=False, default=Tema.claro
    )
