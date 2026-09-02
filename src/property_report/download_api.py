from __future__ import annotations

import os

import httpx
from fastapi import FastAPI, HTTPException

from .export_service import ExportDownload, PropertyExportService
from .infrai_storage import InfraiError, InfraiStorage, InfraiTransportError
from .report_rows import PropertyExportRequest


app = FastAPI(title="Property report downloads")


@app.post("/exports", response_model=ExportDownload, status_code=201)
async def create_export(request: PropertyExportRequest) -> ExportDownload:
    async with httpx.AsyncClient(timeout=20.0) as client:
        storage = InfraiStorage.from_environment(client)
        service = PropertyExportService(
            storage=storage,
            upload_client=client,
            bucket=os.environ.get("PROPERTY_EXPORT_BUCKET", "property-report-exports"),
        )
        try:
            return await service.export(request)
        except InfraiError as exc:
            client_status = exc.status_code if 400 <= exc.status_code < 500 else 502
            raise HTTPException(
                status_code=client_status,
                detail={"code": exc.code, "message": str(exc)},
            ) from exc
        except (InfraiTransportError, httpx.HTTPError) as exc:
            raise HTTPException(status_code=502, detail="Export storage request failed") from exc

