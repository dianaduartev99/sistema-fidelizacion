from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from app.models import (
    Cliente, ReglaAsignacion, ParametroVencimiento,
    BolsaPuntos, UsoPuntosCabecera, UsoPuntosDetalle, ConceptoUso
)
from app.services.email_service import enviar_comprobante_uso_puntos


def _calcular_puntos(monto: Decimal, db: Session) -> tuple[int, list[dict]]:
    """
    Calcula cuántos puntos corresponden a un monto dado,
    aplicando las reglas de asignación vigentes (por rango).
    Retorna (total_puntos, detalle_reglas_aplicadas).
    """
    reglas = db.query(ReglaAsignacion).order_by(ReglaAsignacion.limite_inferior).all()
    if not reglas:
        return 0, []

    total_puntos = 0
    detalle = []

    for regla in reglas:
        li = Decimal(str(regla.limite_inferior))
        ls = Decimal(str(regla.limite_superior)) if regla.limite_superior else None

        # ¿Aplica esta regla al monto?
        if monto < li:
            continue
        if ls is not None and monto >= ls:
            # El monto supera este rango; usar el tope del rango
            monto_en_rango = ls - li
        elif ls is not None:
            monto_en_rango = monto - li
        else:
            monto_en_rango = monto - li

        puntos_rango = int(monto_en_rango // Decimal(str(regla.monto_equivalencia)))
        total_puntos += puntos_rango

        detalle.append({
            "regla_id": regla.id,
            "limite_inferior": float(li),
            "limite_superior": float(ls) if ls else None,
            "monto_equivalencia": float(regla.monto_equivalencia),
            "monto_en_rango": float(monto_en_rango),
            "puntos_asignados": puntos_rango,
        })

        # Si el monto no supera el límite superior, no hay más rangos que aplicar
        if ls is None or monto < ls:
            break

    return total_puntos, detalle


def _obtener_parametro_vencimiento_activo(db: Session) -> Optional[ParametroVencimiento]:
    """Retorna el parámetro de vencimiento vigente para la fecha actual."""
    hoy = datetime.utcnow().date()
    return (
        db.query(ParametroVencimiento)
        .filter(
            and_(
                ParametroVencimiento.fecha_inicio_validez <= hoy,
                ParametroVencimiento.fecha_fin_validez >= hoy,
            )
        )
        .first()
    )


def cargar_puntos(cliente_id: int, monto_operacion: Decimal, db: Session) -> BolsaPuntos:
    """
    Servicio de carga de puntos.
    Recibe cliente_id y monto, calcula puntos según reglas y crea una BolsaPuntos.
    """
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise ValueError(f"Cliente con id={cliente_id} no encontrado.")

    puntos, _ = _calcular_puntos(monto_operacion, db)
    if puntos <= 0:
        raise ValueError("No se pudieron calcular puntos para el monto indicado. Verifique las reglas de asignación.")

    parametro = _obtener_parametro_vencimiento_activo(db)
    if parametro:
        dias = parametro.dias_duracion
    else:
        dias = 365  # fallback: 1 año

    fecha_caducidad = datetime.utcnow() + timedelta(days=dias)

    bolsa = BolsaPuntos(
        cliente_id=cliente_id,
        fecha_caducidad=fecha_caducidad,
        puntaje_asignado=puntos,
        puntaje_utilizado=0,
        saldo_puntos=puntos,
        monto_operacion=monto_operacion,
        estado="ACTIVO",
    )
    db.add(bolsa)
    db.commit()
    db.refresh(bolsa)
    return bolsa


async def utilizar_puntos(
    cliente_id: int, concepto_id: int, db: Session
) -> UsoPuntosCabecera:
    """
    Servicio de uso de puntos (FIFO).
    Descuenta los puntos requeridos por el concepto comenzando por las bolsas más antiguas.
    """
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise ValueError(f"Cliente con id={cliente_id} no encontrado.")

    concepto = db.query(ConceptoUso).filter(ConceptoUso.id == concepto_id).first()
    if not concepto:
        raise ValueError(f"Concepto con id={concepto_id} no encontrado.")

    puntos_requeridos = concepto.puntos_requeridos

    # Saldo total disponible
    bolsas_activas = (
        db.query(BolsaPuntos)
        .filter(
            and_(
                BolsaPuntos.cliente_id == cliente_id,
                BolsaPuntos.estado == "ACTIVO",
                BolsaPuntos.saldo_puntos > 0,
                BolsaPuntos.fecha_caducidad > datetime.utcnow(),
            )
        )
        .order_by(BolsaPuntos.fecha_asignacion.asc())  # FIFO
        .all()
    )

    saldo_total = sum(b.saldo_puntos for b in bolsas_activas)
    if saldo_total < puntos_requeridos:
        raise ValueError(
            f"Saldo insuficiente. Se requieren {puntos_requeridos} puntos, "
            f"pero el cliente solo tiene {saldo_total}."
        )

    # Crear cabecera
    cabecera = UsoPuntosCabecera(
        cliente_id=cliente_id,
        concepto_id=concepto_id,
        puntaje_utilizado=puntos_requeridos,
        fecha=datetime.utcnow(),
    )
    db.add(cabecera)
    db.flush()  # obtener id sin commit

    # Descontar FIFO
    restante = puntos_requeridos
    for bolsa in bolsas_activas:
        if restante <= 0:
            break

        a_descontar = min(bolsa.saldo_puntos, restante)

        detalle = UsoPuntosDetalle(
            cabecera_id=cabecera.id,
            bolsa_id=bolsa.id,
            puntaje_utilizado=a_descontar,
        )
        db.add(detalle)

        bolsa.puntaje_utilizado += a_descontar
        bolsa.saldo_puntos -= a_descontar
        if bolsa.saldo_puntos == 0:
            bolsa.estado = "AGOTADO"

        restante -= a_descontar

    db.commit()
    db.refresh(cabecera)

    # Enviar correo
    email_enviado = await enviar_comprobante_uso_puntos(
        email_destino=cliente.email,
        nombre_cliente=f"{cliente.nombre} {cliente.apellido}",
        puntos_utilizados=puntos_requeridos,
        concepto=concepto.descripcion,
        fecha=cabecera.fecha.strftime("%d/%m/%Y %H:%M"),
        id_transaccion=cabecera.id,
    )

    cabecera._email_enviado = email_enviado
    return cabecera


def consultar_equivalencia_puntos(monto: Decimal, db: Session) -> dict:
    """Devuelve cuántos puntos equivalen a un monto dado."""
    puntos, detalle = _calcular_puntos(monto, db)
    return {"monto": monto, "puntos_equivalentes": puntos, "detalle_reglas": detalle}


def procesar_vencimientos(db: Session) -> int:
    """
    Proceso planificado: marca como VENCIDAS las bolsas cuya fecha_caducidad ya pasó.
    Retorna la cantidad de bolsas vencidas en esta ejecución.
    """
    ahora = datetime.utcnow()
    bolsas_vencidas = (
        db.query(BolsaPuntos)
        .filter(
            and_(
                BolsaPuntos.estado == "ACTIVO",
                BolsaPuntos.fecha_caducidad <= ahora,
                BolsaPuntos.saldo_puntos > 0,
            )
        )
        .all()
    )

    count = 0
    for bolsa in bolsas_vencidas:
        bolsa.estado = "VENCIDO"
        count += 1

    if count > 0:
        db.commit()

    print(f"[SCHEDULER] Proceso de vencimientos ejecutado: {count} bolsa(s) vencida(s).")
    return count
