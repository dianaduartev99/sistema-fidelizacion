from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import ReglaAsignacion
from app.schemas import ReglaAsignacionCreate, ReglaAsignacionUpdate, ReglaAsignacionOut

router = APIRouter(prefix="/reglas-asignacion", tags=["Reglas de Asignación de Puntos"])


@router.post("/", response_model=ReglaAsignacionOut, status_code=201)
def crear_regla(data: ReglaAsignacionCreate, db: Session = Depends(get_db)):
    regla = ReglaAsignacion(**data.model_dump())
    db.add(regla)
    db.commit()
    db.refresh(regla)
    return regla


@router.get("/", response_model=List[ReglaAsignacionOut])
def listar_reglas(skip: int = 0, limit: int = Query(100, le=500), db: Session = Depends(get_db)):
    return db.query(ReglaAsignacion).order_by(ReglaAsignacion.limite_inferior).offset(skip).limit(limit).all()


@router.get("/{regla_id}", response_model=ReglaAsignacionOut)
def obtener_regla(regla_id: int, db: Session = Depends(get_db)):
    regla = db.query(ReglaAsignacion).filter(ReglaAsignacion.id == regla_id).first()
    if not regla:
        raise HTTPException(404, "Regla no encontrada.")
    return regla


@router.put("/{regla_id}", response_model=ReglaAsignacionOut)
def actualizar_regla(regla_id: int, data: ReglaAsignacionUpdate, db: Session = Depends(get_db)):
    regla = db.query(ReglaAsignacion).filter(ReglaAsignacion.id == regla_id).first()
    if not regla:
        raise HTTPException(404, "Regla no encontrada.")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(regla, field, value)
    db.commit()
    db.refresh(regla)
    return regla


@router.delete("/{regla_id}", status_code=204)
def eliminar_regla(regla_id: int, db: Session = Depends(get_db)):
    regla = db.query(ReglaAsignacion).filter(ReglaAsignacion.id == regla_id).first()
    if not regla:
        raise HTTPException(404, "Regla no encontrada.")
    db.delete(regla)
    db.commit()
