from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from decimal import Decimal

from app.database import get_db
from app.schemas import (
    CargaPuntosRequest, CargaPuntosResponse,
    UsoPuntosRequest, UsoPuntosResponse,
    EquivalenciaPuntosResponse,
)
from app.services.puntos_service import (
    cargar_puntos, utilizar_puntos, consultar_equivalencia_puntos, procesar_vencimientos
)

router = APIRouter(prefix="/servicios", tags=["Servicios de Puntos"])


@router.post("/cargar-puntos", response_model=CargaPuntosResponse, status_code=201)
def svc_cargar_puntos(data: CargaPuntosRequest, db: Session = Depends(get_db)):
    """
    Carga de puntos: recibe cliente_id y monto_operacion.
    Calcula puntos según reglas y crea una bolsa de puntos para el cliente.
    """
    try:
        bolsa = cargar_puntos(data.cliente_id, data.monto_operacion, db)
    except ValueError as e:
        raise HTTPException(400, str(e))

    return CargaPuntosResponse(
        mensaje="Puntos asignados correctamente.",
        bolsa=bolsa,
        puntos_asignados=bolsa.puntaje_asignado,
    )


@router.post("/utilizar-puntos", response_model=UsoPuntosResponse, status_code=201)
async def svc_utilizar_puntos(data: UsoPuntosRequest, db: Session = Depends(get_db)):
    """
    Uso de puntos (FIFO): recibe cliente_id y concepto_id.
    Descuenta los puntos requeridos por el concepto usando primero las bolsas más antiguas.
    Envía correo de comprobante al cliente.
    """
    try:
        uso = await utilizar_puntos(data.cliente_id, data.concepto_id, db)
    except ValueError as e:
        raise HTTPException(400, str(e))

    email_enviado = getattr(uso, "_email_enviado", False)

    return UsoPuntosResponse(
        mensaje="Puntos utilizados correctamente.",
        uso=uso,
        puntos_descontados=uso.puntaje_utilizado,
        email_enviado=email_enviado,
    )


@router.get("/equivalencia-puntos", response_model=EquivalenciaPuntosResponse)
def svc_equivalencia_puntos(
    monto: Decimal = Query(..., gt=0, description="Monto en Gs. para calcular equivalencia"),
    db: Session = Depends(get_db),
):
    """
    Consulta informativa: retorna cuántos puntos equivalen al monto proporcionado,
    usando las reglas de asignación configuradas.
    """
    resultado = consultar_equivalencia_puntos(monto, db)
    return EquivalenciaPuntosResponse(**resultado)


@router.post("/procesar-vencimientos", tags=["Proceso Planificado"])
def svc_procesar_vencimientos(db: Session = Depends(get_db)):
    """
    Ejecuta manualmente el proceso de vencimiento de puntos.
    Normalmente se ejecuta automáticamente según el intervalo configurado.
    """
    cantidad = procesar_vencimientos(db)
    return {"mensaje": f"Proceso ejecutado. {cantidad} bolsa(s) marcada(s) como VENCIDA(S)."}
