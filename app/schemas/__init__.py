from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


# ─────────────────────────── CLIENTE ───────────────────────────

class ClienteBase(BaseModel):
    nombre: str = Field(..., max_length=100)
    apellido: str = Field(..., max_length=100)
    numero_documento: str = Field(..., max_length=30)
    tipo_documento: str = Field(..., max_length=20, description="CI, RUC, Pasaporte, etc.")
    nacionalidad: str = Field(..., max_length=60)
    email: EmailStr
    telefono: Optional[str] = Field(None, max_length=30)
    fecha_nacimiento: date

class ClienteCreate(ClienteBase):
    pass

class ClienteUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=100)
    apellido: Optional[str] = Field(None, max_length=100)
    numero_documento: Optional[str] = Field(None, max_length=30)
    tipo_documento: Optional[str] = Field(None, max_length=20)
    nacionalidad: Optional[str] = Field(None, max_length=60)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=30)
    fecha_nacimiento: Optional[date] = None

class ClienteOut(ClienteBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ─────────────────────────── CONCEPTO USO ───────────────────────────

class ConceptoUsoBase(BaseModel):
    descripcion: str = Field(..., max_length=200)
    puntos_requeridos: int = Field(..., gt=0)

class ConceptoUsoCreate(ConceptoUsoBase):
    pass

class ConceptoUsoUpdate(BaseModel):
    descripcion: Optional[str] = Field(None, max_length=200)
    puntos_requeridos: Optional[int] = Field(None, gt=0)

class ConceptoUsoOut(ConceptoUsoBase):
    id: int
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ─────────────────────────── REGLA ASIGNACION ───────────────────────────

class ReglaAsignacionBase(BaseModel):
    limite_inferior: Decimal = Field(..., ge=0, description="Límite inferior del rango en Gs.")
    limite_superior: Optional[Decimal] = Field(None, description="Límite superior (None = sin límite)")
    monto_equivalencia: Decimal = Field(..., gt=0, description="Gs. necesarios para obtener 1 punto")

class ReglaAsignacionCreate(ReglaAsignacionBase):
    pass

class ReglaAsignacionUpdate(BaseModel):
    limite_inferior: Optional[Decimal] = Field(None, ge=0)
    limite_superior: Optional[Decimal] = None
    monto_equivalencia: Optional[Decimal] = Field(None, gt=0)

class ReglaAsignacionOut(ReglaAsignacionBase):
    id: int
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ─────────────────────────── PARAMETRO VENCIMIENTO ───────────────────────────

class ParametroVencimientoBase(BaseModel):
    fecha_inicio_validez: date
    fecha_fin_validez: date
    dias_duracion: int = Field(..., gt=0)

    @field_validator("fecha_fin_validez")
    @classmethod
    def fin_mayor_inicio(cls, v, info):
        if "fecha_inicio_validez" in info.data and v <= info.data["fecha_inicio_validez"]:
            raise ValueError("fecha_fin_validez debe ser mayor a fecha_inicio_validez")
        return v

class ParametroVencimientoCreate(ParametroVencimientoBase):
    pass

class ParametroVencimientoUpdate(BaseModel):
    fecha_inicio_validez: Optional[date] = None
    fecha_fin_validez: Optional[date] = None
    dias_duracion: Optional[int] = Field(None, gt=0)

class ParametroVencimientoOut(ParametroVencimientoBase):
    id: int
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ─────────────────────────── BOLSA PUNTOS ───────────────────────────

class BolsaPuntosOut(BaseModel):
    id: int
    cliente_id: int
    fecha_asignacion: datetime
    fecha_caducidad: datetime
    puntaje_asignado: int
    puntaje_utilizado: int
    saldo_puntos: int
    monto_operacion: Decimal
    estado: str
    model_config = {"from_attributes": True}


# ─────────────────────────── USO PUNTOS ───────────────────────────

class UsoPuntosDetalleOut(BaseModel):
    id: int
    bolsa_id: int
    puntaje_utilizado: int
    model_config = {"from_attributes": True}

class UsoPuntosCabeceraOut(BaseModel):
    id: int
    cliente_id: int
    concepto_id: int
    puntaje_utilizado: int
    fecha: datetime
    detalles: List[UsoPuntosDetalleOut] = []
    model_config = {"from_attributes": True}


# ─────────────────────────── SERVICIOS ───────────────────────────

class CargaPuntosRequest(BaseModel):
    cliente_id: int
    monto_operacion: Decimal = Field(..., gt=0, description="Monto de la operación en Gs.")

class CargaPuntosResponse(BaseModel):
    mensaje: str
    bolsa: BolsaPuntosOut
    puntos_asignados: int

class UsoPuntosRequest(BaseModel):
    cliente_id: int
    concepto_id: int

class UsoPuntosResponse(BaseModel):
    mensaje: str
    uso: UsoPuntosCabeceraOut
    puntos_descontados: int
    email_enviado: bool

class EquivalenciaPuntosResponse(BaseModel):
    monto: Decimal
    puntos_equivalentes: int
    detalle_reglas: List[dict]


# ─────────────────────────── CONSULTAS ───────────────────────────

class ClientePuntosVencerOut(BaseModel):
    cliente_id: int
    nombre: str
    apellido: str
    email: str
    puntos_por_vencer: int
    fecha_caducidad: datetime
    dias_restantes: int
    model_config = {"from_attributes": True}
