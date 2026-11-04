from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger(__name__)

async def tratar_http_exception(
    request: Request,
    exc: StarletteHTTPException,
):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "erro": {
                "codigo": exc.status_code,
                "mensagem": exc.detail,
            }
        },
    )


async def tratar_validacao(
    request: Request,
    exc: RequestValidationError,
):
    return JSONResponse(
        status_code=400,
        content={
            "erro": {
                "codigo": 400,
                "mensagem": "Parâmetros da requisição inválidos.",
            }
        },
    )


async def tratar_erro_interno(
    request: Request,
    exc: Exception,
):
    logger.exception(
        "Erro interno não tratado durante a requisição."
    )
    return JSONResponse(
        status_code=500,
        content={
            "erro": {
                "codigo": 500,
                "mensagem": "Erro interno do servidor.",
            }
        },
    )