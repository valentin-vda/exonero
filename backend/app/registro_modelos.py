"""Importa los modelos de los nueve modulos en un solo lugar.

Este archivo es la UNICA excepcion a la regla "nadie importa modelos.py de otro
modulo". Existe por una razon tecnica: Alembic tiene que ver las 24 tablas
registradas en Base.metadata para poder comparar los modelos con la base y
generar las migraciones. Si un modulo no se importa aca, autogenerate cree que
sus tablas no existen y escribe un DROP TABLE.

Lo importan alembic/env.py y app/main.py. Ningun modulo lo importa.
"""

from app.db import Base  # noqa: F401

from app.modulos.catalogos import modelos as _catalogos  # noqa: F401
from app.modulos.cuentas import modelos as _cuentas      # noqa: F401
from app.modulos.perfiles import modelos as _perfiles    # noqa: F401
from app.modulos.agenda import modelos as _agenda        # noqa: F401
from app.modulos.clases import modelos as _clases        # noqa: F401
from app.modulos.pagos import modelos as _pagos          # noqa: F401
from app.modulos.mensajeria import modelos as _mensajeria  # noqa: F401
from app.modulos.resenas import modelos as _resenas      # noqa: F401
# busqueda no tiene tablas propias: consulta las de perfiles y catalogos.

metadata = Base.metadata
