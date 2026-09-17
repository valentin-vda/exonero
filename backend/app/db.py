"""Conexion a PostgreSQL y la clase Base de la que heredan todos los modelos.

Cada modulo define sus propias tablas heredando de `Base`, pero el engine y la
sesion son unicos para toda la aplicacion.
"""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy import create_engine

from app.config import ajustes

engine = create_engine(ajustes.BASE_URL, echo=False, pool_pre_ping=True)

SesionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Base declarativa comun a los nueve modulos."""


class Marcas:
    """Columnas que lleva toda tabla de la spec: id, creado_el y actualizado_el.

    Se hereda como mixin para no repetirlas en las 24 tablas.
    """

    id: Mapped[int] = mapped_column(primary_key=True)
    creado_el: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    actualizado_el: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=func.now()
    )


def obtener_sesion():
    """Dependencia de FastAPI: abre una sesion por request y la cierra al final.

    Se usa asi en cualquier ruta:

        def mi_ruta(db: Session = Depends(obtener_sesion)):
            ...
    """
    db = SesionLocal()
    try:
        yield db
    finally:
        db.close()
