from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import ParametroVencimiento
from app.schemas import ParametroVencimientoCreate, ParametroVencimientoUpdate, ParametroVencimientoOut

router = APIRouter(prefix="/parametros-vencimiento", tags=["Parametrización de Vencimientos"])


@router.post("/", response_model=ParametroVencimientoOut, status_code=201)
def crear_parametro(data: ParametroVencimientoCreate, db: Session = Depends(get_db)):
    parametro = ParametroVencimiento(**data.model_dump())
    db.add(parametro)
    db.commit()
    db.refresh(parametro)
    return parametro


@router.get("/", response_model=List[ParametroVencimientoOut])
def listar_parametros(skip: int = 0, limit: int = Query(100, le=500), db: Session = Depends(get_db)):
    return db.query(ParametroVencimiento).offset(skip).limit(limit).all()


@router.get("/{parametro_id}", response_model=ParametroVencimientoOut)
def obtener_parametro(parametro_id: int, db: Session = Depends(get_db)):
    parametro = db.query(ParametroVencimiento).filter(ParametroVencimiento.id == parametro_id).first()
    if not parametro:
        raise HTTPException(404, "Parámetro de vencimiento no encontrado.")
    return parametro


@router.put("/{parametro_id}", response_model=ParametroVencimientoOut)
def actualizar_parametro(parametro_id: int, data: ParametroVencimientoUpdate, db: Session = Depends(get_db)):
    parametro = db.query(ParametroVencimiento).filter(ParametroVencimiento.id == parametro_id).first()
    if not parametro:
        raise HTTPException(404, "Parámetro de vencimiento no encontrado.")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(parametro, field, value)
    db.commit()
    db.refresh(parametro)
    return parametro


@router.delete("/{parametro_id}", status_code=204)
def eliminar_parametro(parametro_id: int, db: Session = Depends(get_db)):
    parametro = db.query(ParametroVencimiento).filter(ParametroVencimiento.id == parametro_id).first()
    if not parametro:
        raise HTTPException(404, "Parámetro de vencimiento no encontrado.")
    db.delete(parametro)
    db.commit()
