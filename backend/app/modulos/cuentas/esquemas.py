"""Contratos de entrada y salida del modulo cuentas.

Los de registro y login son los que consume la pantalla de login/registro del
frontend; estan copiados tal cual de la seccion 9 de la spec.
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.enums import Tema


# --- Registro ---------------------------------------------------------------

class RegistroIn(BaseModel):
    """Cuerpo de POST /auth/registro/estudiante y /auth/registro/profesor.

    Es el mismo cuerpo para los dos: el rol sale de la ruta, no del cuerpo, asi
    nadie puede darse de alta como profesor mandando un campo de mas.
    """

    correo: EmailStr
    clave: str = Field(min_length=8, max_length=72)  # 72 es el tope de bcrypt
    nombre: str = Field(min_length=1, max_length=80)
    apellido: str = Field(min_length=1, max_length=80)
    documento: str | None = Field(default=None, max_length=20)
    telefono: str | None = Field(default=None, max_length=30)
    fecha_nacimiento: date | None = None


# --- Login ------------------------------------------------------------------

class LoginIn(BaseModel):
    """Cuerpo de POST /auth/login."""

    correo: EmailStr
    clave: str


class UsuarioSesionOut(BaseModel):
    """El pedacito de usuario que viaja adentro de la respuesta del login."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    rol: str


class TokenOut(BaseModel):
    """Respuesta de POST /auth/login y de los dos registros.

        { "token": "eyJhbGci...", "expira_en": 86400,
          "usuario": { "id": 12, "nombre": "Ana", "rol": "estudiante" } }
    """

    token: str
    expira_en: int  # segundos
    usuario: UsuarioSesionOut


# --- Recuperar contrasena ---------------------------------------------------

class RecuperarIn(BaseModel):
    """Paso 1: se pide el codigo. Sin correo saliente, el codigo se imprime en
    la consola del backend."""

    correo: EmailStr


class RestablecerIn(BaseModel):
    """Paso 2: con el codigo, se fija la contrasena nueva."""

    correo: EmailStr
    codigo: str
    clave_nueva: str = Field(min_length=8, max_length=72)


# --- El usuario del token ---------------------------------------------------

class EstudianteEnCabecera(BaseModel):
    """Los datos del estudiante que muestra la cabecera de 1a:
    '5.º de Bachillerato · Liceo Bauza · Cordon'.

    Vienen con los NOMBRES ya resueltos, no los ids. `nivel` es solo el anio
    dentro de la etapa ("5.o"): el frontend arma "5.o de Bachillerato".
    """

    etapa: str | None = None
    nivel: str | None = None
    centro: str | None = None
    barrio: str | None = None
    puntaje_promedio: float = 0
    cantidad_resenas: int = 0


class YoOut(BaseModel):
    """Respuesta de GET /usuarios/yo — la usan las diez pantallas.

    Trae el contador de mensajes no leidos adentro para que la cabecera se
    arme con un solo llamado al entrar.

    documento, telefono y fecha_nacimiento estan para que 1e y 1j puedan
    llenar el formulario de "Informacion personal" sin otro llamado.
    creado_el es el "Miembro desde marzo de 2026" de la cabecera de 1e.
    """

    id: int
    nombre: str
    apellido: str
    correo: str
    rol: str
    foto_base64: str | None = None
    tema: str
    documento: str | None = None
    telefono: str | None = None
    fecha_nacimiento: date | None = None
    creado_el: datetime | None = None
    mensajes_no_leidos: int = 0
    estudiante: EstudianteEnCabecera | None = None


class ActualizarUsuarioIn(BaseModel):
    """Cuerpo de PATCH /usuarios/yo — 1e · 1j.

    El correo NO esta en la lista, a proposito: es la credencial y no se cambia.
    Todos los campos son opcionales; solo se tocan los que vienen. Los topes de
    largo son los mismos que los de RegistroIn.
    """

    nombre: str | None = Field(default=None, max_length=80)
    apellido: str | None = Field(default=None, max_length=80)
    telefono: str | None = Field(default=None, max_length=30)
    documento: str | None = Field(default=None, max_length=20)
    fecha_nacimiento: date | None = None


class FotoIn(BaseModel):
    """PUT /usuarios/yo/foto. La imagen entera como data URL base64."""

    foto_base64: str


class ClaveIn(BaseModel):
    """PUT /usuarios/yo/clave. Pide la actual para que un token robado no
    alcance para tomar la cuenta."""

    clave_actual: str
    clave_nueva: str = Field(min_length=8, max_length=72)


class TemaIn(BaseModel):
    """PUT /usuarios/yo/tema.

    Con el tipo Tema (el enum de app/enums.py), FastAPI rechaza solo cualquier
    valor que no sea 'claro' u 'oscuro', con un 422.
    """

    tema: Tema


class OkOut(BaseModel):
    """Confirmacion simple para los PUT que no devuelven un recurso."""

    ok: bool = True
