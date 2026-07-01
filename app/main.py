from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
import os

from app.database import engine, SessionLocal
from app.models import (  # noqa: F401 – importar para que SQLAlchemy cree las tablas
    Cliente, ConceptoUso, ReglaAsignacion, ParametroVencimiento,
    BolsaPuntos, UsoPuntosCabecera, UsoPuntosDetalle
)
from app.database import Base
from app.routers import (
    clientes, conceptos_uso, reglas_asignacion,
    parametros_vencimiento, bolsas_puntos, uso_puntos, servicios
)
from app.services.puntos_service import procesar_vencimientos

load_dotenv()

SCHEDULER_INTERVAL_HOURS = float(os.getenv("SCHEDULER_INTERVAL_HOURS", "24"))

scheduler = AsyncIOScheduler()


def job_vencimientos():
    """Job periódico: procesa vencimientos de bolsas de puntos."""
    db = SessionLocal()
    try:
        procesar_vencimientos(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear tablas al iniciar
    Base.metadata.create_all(bind=engine)

    # Iniciar scheduler
    scheduler.add_job(
        job_vencimientos,
        "interval",
        hours=SCHEDULER_INTERVAL_HOURS,
        id="procesar_vencimientos",
        replace_existing=True,
    )
    scheduler.start()
    print(f"[SCHEDULER] Iniciado. Procesará vencimientos cada {SCHEDULER_INTERVAL_HOURS}h.")

    yield

    scheduler.shutdown()
    print("[SCHEDULER] Detenido.")


app = FastAPI(
    title="Sistema de Fidelización de Clientes",
    description=(
        "API REST para la gestión de un sistema de fidelización de clientes. "
        "Incluye CRUD de clientes, conceptos de uso, reglas de asignación de puntos, "
        "parametrización de vencimientos, bolsa de puntos y uso de puntos (FIFO)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────
app.include_router(clientes.router)
app.include_router(conceptos_uso.router)
app.include_router(reglas_asignacion.router)
app.include_router(parametros_vencimiento.router)
app.include_router(bolsas_puntos.router)
app.include_router(uso_puntos.router)
app.include_router(servicios.router)


@app.get("/", tags=["Root"])
def root():
    return {
        "sistema": "Fidelización de Clientes",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }
