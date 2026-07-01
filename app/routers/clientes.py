from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, extract
from typing import List, Optional

from app.database import get_db
from app.models import Cliente
from app.schemas import ClienteCreate, ClienteUpdate, ClienteOut

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.post("/", response_model=ClienteOut, status_code=201)
def crear_cliente(data: ClienteCreate, db: Session = Depends(get_db)):
    existente = db.query(Cliente).filter(
        or_(Cliente.email == data.email, Cliente.numero_documento == data.numero_documento)
    ).first()
    if existente:
        raise HTTPException(400, "Ya existe un cliente con ese email o número de documento.")
    cliente = Cliente(**data.model_dump())
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


@router.get("/", response_model=List[ClienteOut])
def listar_clientes(
    skip: int = 0,
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
):
    return db.query(Cliente).offset(skip).limit(limit).all()


@router.get("/buscar", response_model=List[ClienteOut])
def buscar_clientes(
    nombre: Optional[str] = Query(None, description="Aproximación por nombre"),
    apellido: Optional[str] = Query(None, description="Aproximación por apellido"),
    cumpleanos_mes: Optional[int] = Query(None, ge=1, le=12, description="Mes de cumpleaños (1-12)"),
    cumpleanos_dia: Optional[int] = Query(None, ge=1, le=31, description="Día de cumpleaños"),
    db: Session = Depends(get_db),
):
    query = db.query(Cliente)
    if nombre:
        query = query.filter(Cliente.nombre.ilike(f"%{nombre}%"))
    if apellido:
        query = query.filter(Cliente.apellido.ilike(f"%{apellido}%"))
    if cumpleanos_mes:
        query = query.filter(extract("month", Cliente.fecha_nacimiento) == cumpleanos_mes)
    if cumpleanos_dia:
        query = query.filter(extract("day", Cliente.fecha_nacimiento) == cumpleanos_dia)
    return query.all()


@router.get("/{cliente_id}", response_model=ClienteOut)
def obtener_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(404, "Cliente no encontrado.")
    return cliente


@router.put("/{cliente_id}", response_model=ClienteOut)
def actualizar_cliente(cliente_id: int, data: ClienteUpdate, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(404, "Cliente no encontrado.")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(cliente, field, value)
    db.commit()
    db.refresh(cliente)
    return cliente


@router.delete("/{cliente_id}", status_code=204)
def eliminar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(404, "Cliente no encontrado.")
    db.delete(cliente)
    db.commit()
