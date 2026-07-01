from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import ConceptoUso
from app.schemas import ConceptoUsoCreate, ConceptoUsoUpdate, ConceptoUsoOut

router = APIRouter(prefix="/conceptos-uso", tags=["Conceptos de Uso de Puntos"])


@router.post("/", response_model=ConceptoUsoOut, status_code=201)
def crear_concepto(data: ConceptoUsoCreate, db: Session = Depends(get_db)):
    concepto = ConceptoUso(**data.model_dump())
    db.add(concepto)
    db.commit()
    db.refresh(concepto)
    return concepto


@router.get("/", response_model=List[ConceptoUsoOut])
def listar_conceptos(skip: int = 0, limit: int = Query(100, le=500), db: Session = Depends(get_db)):
    return db.query(ConceptoUso).offset(skip).limit(limit).all()


@router.get("/{concepto_id}", response_model=ConceptoUsoOut)
def obtener_concepto(concepto_id: int, db: Session = Depends(get_db)):
    concepto = db.query(ConceptoUso).filter(ConceptoUso.id == concepto_id).first()
    if not concepto:
        raise HTTPException(404, "Concepto no encontrado.")
    return concepto


@router.put("/{concepto_id}", response_model=ConceptoUsoOut)
def actualizar_concepto(concepto_id: int, data: ConceptoUsoUpdate, db: Session = Depends(get_db)):
    concepto = db.query(ConceptoUso).filter(ConceptoUso.id == concepto_id).first()
    if not concepto:
        raise HTTPException(404, "Concepto no encontrado.")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(concepto, field, value)
    db.commit()
    db.refresh(concepto)
    return concepto


@router.delete("/{concepto_id}", status_code=204)
def eliminar_concepto(concepto_id: int, db: Session = Depends(get_db)):
    concepto = db.query(ConceptoUso).filter(ConceptoUso.id == concepto_id).first()
    if not concepto:
        raise HTTPException(404, "Concepto no encontrado.")
    db.delete(concepto)
    db.commit()
