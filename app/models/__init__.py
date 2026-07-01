from sqlalchemy import (
    Column, Integer, String, Date, DateTime, Float,
    ForeignKey, Numeric, Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    numero_documento = Column(String(30), unique=True, nullable=False, index=True)
    tipo_documento = Column(String(20), nullable=False)   # CI, RUC, Pasaporte, etc.
    nacionalidad = Column(String(60), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    telefono = Column(String(30), nullable=True)
    fecha_nacimiento = Column(Date, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    bolsas = relationship("BolsaPuntos", back_populates="cliente")
    usos_cabecera = relationship("UsoPuntosCabecera", back_populates="cliente")


class ConceptoUso(Base):
    """Define a qué fueron destinados los puntos usados (vale de premio, descuento, etc.)"""
    __tablename__ = "conceptos_uso"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    descripcion = Column(String(200), nullable=False)
    puntos_requeridos = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    usos_cabecera = relationship("UsoPuntosCabecera", back_populates="concepto")


class ReglaAsignacion(Base):
    """Regla que rige cuántos puntos se asignan según rango de monto consumido."""
    __tablename__ = "reglas_asignacion"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    limite_inferior = Column(Numeric(15, 2), nullable=False, default=0)
    limite_superior = Column(Numeric(15, 2), nullable=True)   # NULL = sin límite superior
    monto_equivalencia = Column(Numeric(15, 2), nullable=False)  # Gs. por cada 1 punto
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ParametroVencimiento(Base):
    """Define el tiempo de validez de los puntos asignados."""
    __tablename__ = "parametros_vencimiento"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    fecha_inicio_validez = Column(Date, nullable=False)
    fecha_fin_validez = Column(Date, nullable=False)
    dias_duracion = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class BolsaPuntos(Base):
    """Registro de puntos asignados a un cliente por operación."""
    __tablename__ = "bolsas_puntos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, index=True)
    fecha_asignacion = Column(DateTime, server_default=func.now(), nullable=False)
    fecha_caducidad = Column(DateTime, nullable=False)
    puntaje_asignado = Column(Integer, nullable=False)
    puntaje_utilizado = Column(Integer, nullable=False, default=0)
    saldo_puntos = Column(Integer, nullable=False)
    monto_operacion = Column(Numeric(15, 2), nullable=False)
    estado = Column(String(20), nullable=False, default="ACTIVO")  # ACTIVO, VENCIDO, AGOTADO

    cliente = relationship("Cliente", back_populates="bolsas")
    detalles_uso = relationship("UsoPuntosDetalle", back_populates="bolsa")


class UsoPuntosCabecera(Base):
    """Cabecera del registro de uso de puntos (esquema FIFO)."""
    __tablename__ = "uso_puntos_cabecera"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, index=True)
    concepto_id = Column(Integer, ForeignKey("conceptos_uso.id"), nullable=False)
    puntaje_utilizado = Column(Integer, nullable=False)
    fecha = Column(DateTime, server_default=func.now(), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    cliente = relationship("Cliente", back_populates="usos_cabecera")
    concepto = relationship("ConceptoUso", back_populates="usos_cabecera")
    detalles = relationship("UsoPuntosDetalle", back_populates="cabecera")


class UsoPuntosDetalle(Base):
    """Detalle de qué bolsas se usaron para satisfacer un uso de puntos."""
    __tablename__ = "uso_puntos_detalle"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cabecera_id = Column(Integer, ForeignKey("uso_puntos_cabecera.id"), nullable=False, index=True)
    bolsa_id = Column(Integer, ForeignKey("bolsas_puntos.id"), nullable=False)
    puntaje_utilizado = Column(Integer, nullable=False)

    cabecera = relationship("UsoPuntosCabecera", back_populates="detalles")
    bolsa = relationship("BolsaPuntos", back_populates="detalles_uso")
