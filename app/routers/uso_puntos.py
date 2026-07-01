from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.database import get_db
from app.models import UsoPuntosCabecera
from app.schemas import UsoPuntosCabeceraOut

router = APIRouter(prefix="/uso-puntos", tags=["Uso de Puntos"])


@router.get("/", response_model=List[UsoPuntosCabeceraOut])
def listar_usos(
    cliente_id: Optional[int] = Query(None),
    concepto_id: Optional[int] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    skip: int = 0,
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
):
    """
    Consulta uso de puntos.
    Filtra por: cliente, concepto de uso y/o rango de fechas.
    """
    query = db.query(UsoPuntosCabecera)
    if cliente_id:
        query = query.filter(UsoPuntosCabecera.cliente_id == cliente_id)
    if concepto_id:
        query = query.filter(UsoPuntosCabecera.concepto_id == concepto_id)
    if fecha_desde:
        query = query.filter(UsoPuntosCabecera.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(UsoPuntosCabecera.fecha <= fecha_hasta)
    return query.order_by(UsoPuntosCabecera.fecha.desc()).offset(skip).limit(limit).all()


@router.get("/{uso_id}", response_model=UsoPuntosCabeceraOut)
def obtener_uso(uso_id: int, db: Session = Depends(get_db)):
    uso = db.query(UsoPuntosCabecera).filter(UsoPuntosCabecera.id == uso_id).first()
    if not uso:
        raise HTTPException(404, "Registro de uso de puntos no encontrado.")
    return uso
