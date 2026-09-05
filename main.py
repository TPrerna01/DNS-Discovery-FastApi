import logging
import time

import uvicorn
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.core.logging_config import setup_logging
from app.core.urls import api_router
from db_connection import engine

setup_logging()
logger = logging.getLogger("app.requests")


def create_app():
    app = FastAPI()
    # app.mount("/static", StaticFiles(directory="static"), name="static")
    app.include_router(api_router)

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start) * 1000
        logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.1f}ms)")
        return response

    # our schemas raise ValueError from model_validator for bad input (invalid FQDN, weak password, etc.) -
    # FastAPI reports these as 422 by default, but the spec wants 400 for validation failures
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"Validation failed for {request.method} {request.url.path}: {exc.errors()}")
        return JSONResponse(status_code=400, content=jsonable_encoder({"detail": exc.errors()}))

    @app.get("/health")
    async def health_check():
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception:
            logger.exception("Health check failed - database unreachable")
            return JSONResponse(status_code=503, content={"status": "error", "database": "disconnected"})
        return {"status": "ok", "database": "connected"}

    return app

app = create_app()

if __name__ == "__main__":
    is_local = True
    uvicorn.run(app, host="0.0.0.0", port=8000)
