from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

from paper2code.config import get_settings
from paper2code.logging_utils import configure_logging
from paper2code.service import Paper2CodeService

settings = get_settings()
configure_logging(settings.log_level)
app = FastAPI(title=settings.app_name, version="0.1.0")


class RunRequest(BaseModel):
    arxiv_url: HttpUrl


def get_service() -> Paper2CodeService:
    return Paper2CodeService(settings)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}


@app.post("/runs")
def create_run(request: RunRequest) -> dict:
    try:
        return get_service().run(str(request.arxiv_url))
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc
