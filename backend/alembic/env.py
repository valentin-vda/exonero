"""Configuracion de Alembic.

Lee la cadena de conexion del .env (no de alembic.ini) y toma las 24 tablas de
app/registro_modelos.py, que es el unico archivo que importa los modelos de los
nueve modulos.

Reglas del equipo, de la seccion 3 de la spec:
  - UNA revision por pull request. Si una rama trae tres migraciones sueltas,
    el orden de aplicacion se vuelve imposible de seguir al mezclar ramas.
  - LEER lo que genero el autogenerador antes de subirlo. Alembic interpreta
    "renombre una columna" como "borre una y cree otra", y con eso se pierden
    los datos.
  - NUNCA editar una migracion ya aplicada. Si otro ya la corrio, editarla deja
    las dos bases distintas con el mismo numero de version. Se arregla con una
    revision nueva.
  - Cada uno migra SOLO sus tablas. Si P3 necesita una columna en clase, se la
    pide a P4.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import ajustes
from app.registro_modelos import metadata

config = context.config

# La URL sale del .env, no del ini.
config.set_main_option("sqlalchemy.url", ajustes.BASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = metadata


def run_migrations_offline() -> None:
    """Genera el SQL sin conectarse. Util para revisar que va a hacer."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Se conecta y aplica las migraciones."""
    conectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with conectable.connect() as conexion:
        context.configure(
            connection=conexion,
            target_metadata=target_metadata,
            # Detecta cambios de tipo, no solo altas y bajas de columnas.
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
