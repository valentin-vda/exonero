"""Configuracion de la aplicacion, leida del archivo .env.

Un solo lugar del que sale toda la configuracion. Nadie lee os.environ
directamente: se importa `ajustes` de aca.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Ajustes(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Cadena de conexion de SQLAlchemy hacia el PostgreSQL del docker-compose.
    BASE_URL: str = "postgresql+psycopg://exonero:exonero@localhost:5433/exonero"

    # Firma de los tokens. El token no se guarda en la base: vive en el
    # frontend y vence solo (decision de la seccion 1 de la spec).
    JWT_SECRETO: str = "cambiar-esta-clave-en-cada-maquina"
    JWT_ALGORITMO: str = "HS256"
    JWT_HORAS_VALIDO: int = 24

    # Origenes permitidos para CORS, separados por coma.
    CORS_ORIGENES: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Zona horaria en la que trabaja la aplicacion. La base guarda timestamptz
    # (siempre UTC por dentro); esta es la zona con la que se arman y se
    # muestran las fechas.
    ZONA_HORARIA: str = "America/Montevideo"

    @property
    def cors_lista(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGENES.split(",") if o.strip()]


ajustes = Ajustes()
