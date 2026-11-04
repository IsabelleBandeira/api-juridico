import logging
import time
import uuid
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from api.routes.autor import router as autor_router
from app.exceptions import (
    tratar_http_exception,
    tratar_validacao,
    tratar_erro_interno,
)
from app.logging_config import configurar_logs

configurar_logs()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="API Jurídico",
    description="API para consulta de autores, acordos e documentos.",
    version="1.0.0",
)

@app.middleware("http")
async def registrar_requisicao(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID")

    if not correlation_id:
        correlation_id = str(uuid.uuid4())

    inicio = time.perf_counter()

    try:
        response = await call_next(request)

        duracao_ms = (time.perf_counter() - inicio) * 1000

        response.headers["X-Correlation-ID"] = correlation_id

        logger.info(
            "Requisição concluída | method=%s path=%s status=%s "
            "duration_ms=%.2f correlation_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            duracao_ms,
            correlation_id,
        )

        return response

    except Exception:
        logger.exception(
            "Falha inesperada na requisição | method=%s path=%s "
            "correlation_id=%s",
            request.method,
            request.url.path,
            correlation_id,
        )
        raise

app.add_exception_handler(
    StarletteHTTPException,
    tratar_http_exception,
)

app.add_exception_handler(
    RequestValidationError,
    tratar_validacao,
)

app.add_exception_handler(
    Exception,
    tratar_erro_interno,
)

app.include_router(autor_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}