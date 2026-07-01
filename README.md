# Sistema de Fidelización de Clientes — API REST

Backend desarrollado con **Python 3.11 + FastAPI + SQLAlchemy + SQLite**.

---

## Estructura del proyecto

```
fidelizacion/
├── app/
│   ├── main.py                  # Entrada principal, lifespan, scheduler
│   ├── database.py              # Engine y sesión SQLAlchemy
│   ├── models/
│   │   └── __init__.py          # Todos los modelos ORM
│   ├── schemas/
│   │   └── __init__.py          # Todos los schemas Pydantic
│   ├── routers/
│   │   ├── clientes.py
│   │   ├── conceptos_uso.py
│   │   ├── reglas_asignacion.py
│   │   ├── parametros_vencimiento.py
│   │   ├── bolsas_puntos.py
│   │   ├── uso_puntos.py
│   │   └── servicios.py
│   └── services/
│       ├── puntos_service.py    # Lógica de negocio (FIFO, carga, vencimientos)
│       └── email_service.py     # Envío de correo SMTP
├── requirements.txt
├── .env.example
└── README.md
```

---

## Instalación

```bash
# 1. Clonar / copiar el proyecto
cd fidelizacion

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Copiar y editar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales SMTP si querés enviar correos reales

# 5. Levantar el servidor
uvicorn app.main:app --reload --port 8000
```

La API queda disponible en: http://localhost:8000  
Documentación Swagger: http://localhost:8000/docs  
Documentación ReDoc: http://localhost:8000/redoc

---

## Módulos implementados

### 1. Clientes — `/clientes`
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/clientes/` | Crear cliente |
| GET | `/clientes/` | Listar clientes |
| GET | `/clientes/buscar` | Buscar por nombre, apellido, cumpleaños |
| GET | `/clientes/{id}` | Obtener cliente por ID |
| PUT | `/clientes/{id}` | Actualizar cliente |
| DELETE | `/clientes/{id}` | Eliminar cliente |

### 2. Conceptos de Uso — `/conceptos-uso`
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/conceptos-uso/` | Crear concepto |
| GET | `/conceptos-uso/` | Listar conceptos |
| GET | `/conceptos-uso/{id}` | Obtener por ID |
| PUT | `/conceptos-uso/{id}` | Actualizar |
| DELETE | `/conceptos-uso/{id}` | Eliminar |

### 3. Reglas de Asignación — `/reglas-asignacion`
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/reglas-asignacion/` | Crear regla |
| GET | `/reglas-asignacion/` | Listar reglas |
| GET | `/reglas-asignacion/{id}` | Obtener por ID |
| PUT | `/reglas-asignacion/{id}` | Actualizar |
| DELETE | `/reglas-asignacion/{id}` | Eliminar |

### 4. Parametrización de Vencimientos — `/parametros-vencimiento`
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/parametros-vencimiento/` | Crear parámetro |
| GET | `/parametros-vencimiento/` | Listar |
| GET | `/parametros-vencimiento/{id}` | Obtener por ID |
| PUT | `/parametros-vencimiento/{id}` | Actualizar |
| DELETE | `/parametros-vencimiento/{id}` | Eliminar |

### 5. Bolsa de Puntos — `/bolsas-puntos`
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/bolsas-puntos/` | Listar bolsas (filtros: cliente, estado, rango de puntos) |
| GET | `/bolsas-puntos/por-vencer` | Clientes con puntos a vencer en X días |
| GET | `/bolsas-puntos/{id}` | Obtener bolsa por ID |

### 6. Uso de Puntos — `/uso-puntos`
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/uso-puntos/` | Listar usos (filtros: cliente, concepto, fechas) |
| GET | `/uso-puntos/{id}` | Obtener uso por ID |

### 7. Servicios — `/servicios`
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/servicios/cargar-puntos` | Carga puntos a cliente según monto |
| POST | `/servicios/utilizar-puntos` | Usa puntos (FIFO) + envía correo |
| GET | `/servicios/equivalencia-puntos?monto=X` | Cuántos puntos vale un monto |
| POST | `/servicios/procesar-vencimientos` | Ejecuta manualmente el proceso planificado |

---

## Proceso planificado (Scheduler)

El proceso de vencimiento de bolsas corre automáticamente cada `SCHEDULER_INTERVAL_HOURS` horas (configurable en `.env`, default 24h).  
También puede ejecutarse manualmente con `POST /servicios/procesar-vencimientos`.

---

## Lógica FIFO para uso de puntos

Al ejecutar `POST /servicios/utilizar-puntos`, el sistema:
1. Obtiene todas las bolsas activas del cliente, ordenadas por fecha de asignación (más antigua primero).
2. Descuenta de cada bolsa lo necesario hasta satisfacer los puntos requeridos por el concepto.
3. Registra el detalle de cada bolsa utilizada.
4. Envía un correo de comprobante al cliente.

---

## Ejemplo de reglas de asignación (del enunciado)

```json
[
  { "limite_inferior": 0, "limite_superior": 199999, "monto_equivalencia": 50000 },
  { "limite_inferior": 200000, "limite_superior": 499999, "monto_equivalencia": 30000 },
  { "limite_inferior": 500000, "limite_superior": null, "monto_equivalencia": 20000 }
]
```

Con estas reglas, una operación de **Gs. 350.000** genera:
- Primero rango (0-199.999): 199.999 / 50.000 = 3 puntos
- Segundo rango (200.000-499.999): 150.000 / 30.000 = 5 puntos
- **Total: 8 puntos**

---

## Configuración de email (.env)

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_correo@gmail.com
SMTP_PASSWORD=tu_password_de_aplicacion
EMAIL_FROM=tu_correo@gmail.com
```

> Para Gmail se necesita una **contraseña de aplicación** (no la contraseña normal).
> Si no se configura, los emails se omiten silenciosamente y la API sigue funcionando.
