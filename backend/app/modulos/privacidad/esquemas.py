from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class ConfirmarParentalIn(BaseModel):
    token: str = Field(min_length=32, max_length=200)
    nombre_adulto: str = Field(min_length=2, max_length=120)
    vinculo: Literal["madre", "padre", "tutor", "representante"]
    acepta: Literal[True]


class SupresionIn(BaseModel):
    clave: str
    confirmacion: Literal["ELIMINAR"]


class ReenviarIn(BaseModel):
    correo: EmailStr


class AvisoOut(BaseModel):
    version: str
    hash: str
    aviso: str
    aviso_menores: str
    modo_demo: bool
    responsable: str
    contacto: str


class EstadoParentalOut(BaseModel):
    ok: bool = True
    estado: str
