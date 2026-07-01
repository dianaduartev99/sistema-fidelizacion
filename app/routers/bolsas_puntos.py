from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models import BolsaPuntos, Cliente
from app.schemas import BolsaPuntosOut, ClientePuntosVencerOut

router = APIRouter(prefix="/bolsas-puntos", tags=["Bolsa de Puntos"])


@router.get("/", response_model=List[BolsaPuntosOut])
def listar_bolsas(
    cliente_id: Optional[int] = Query(None),
    estado: Optional[str] = Query(None, description="ACTIVO, VENCIDO, AGOTADO"),
    puntos_min: Optional[int] = Query(None, ge=0),
    puntos_max: Optional[int] = Query(None, ge=0),
    skip: int = 0,
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
):
    """Consulta bolsas de puntos. Filtra por cliente, estado y/o rango de saldo."""
    query = db.query(BolsaPuntos)
    if cliente_id:
        query = query.filter(BolsaPuntos.cliente_id == cliente_id)
    if estado:
        query = query.filter(BolsaPuntos.estado == estado.upper())
    if puntos_min is not None:
        query = query.filter(BolsaPuntos.saldo_puntos >= puntos_min)
    if puntos_max is not None:
        query = query.filter(BolsaPuntos.saldo_puntos <= puntos_max)
    return query.order_by(BolsaPuntos.fecha_asignacion.desc()).offset(skip).limit(limit).all()


@router.get("/por-vencer", response_model=List[ClientePuntosVencerOut])
def puntos_por_vencer(
    dias: int = Query(7, ge=1, description="Días hacia adelante para buscar vencimientos"),
    db: Session = Depends(get_db),
):
    """Lista clientes con puntos que vencen en los próximos X días."""
    ahora = datetime.utcnow()
    limite = ahora + timedelta(days=dias)

    bolsas = (
        db.query(BolsaPuntos)
        .filter(
            and_(
                BolsaPuntos.estado == "ACTIVO",
                BolsaPuntos.saldo_puntos > 0,
                BolsaPuntos.fecha_caducidad >= ahora,
                BolsaPuntos.fecha_caducidad <= limite,
            )
        )
        .order_by(BolsaPuntos.fecha_caducidad.asc())
        .all()
    )

    resultado = []
    for bolsa in bolsas:
        cliente = bolsa.cliente
        dias_restantes = (bolsa.fecha_caducidad - ahora).days
        resultado.append(
            ClientePuntosVencerOut(
                cliente_id=cliente.id,
                nombre=cliente.nombre,
                apellido=cliente.apellido,
                email=cliente.email,
                puntos_por_vencer=bolsa.saldo_puntos,
                fecha_caducidad=bolsa.fecha_caducidad,
                dias_restantes=dias_restantes,
            )
        )
    return resultado


@router.get("/{bolsa_id}", response_model=BolsaPuntosOut)
def obtener_bolsa(bolsa_id: int, db: Session = Depends(get_db)):
    bolsa = db.query(BolsaPuntos).filter(BolsaPuntos.id == bolsa_id).first()
    if not bolsa:
        raise HTTPException(404, "Bolsa de puntos no encontrada.")
    return bolsa
