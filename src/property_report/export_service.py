from __future__ import annotations

from uuid import uuid4

import httpx
from pydantic import BaseModel

from .infrai_storage import InfraiStorage
from .report_rows import PropertyExportRequest, build_property_csv


class ExportDownload(BaseModel):
    download_url: str
    object_key: str
    row_count: int


class PropertyExportService:
    def __init__(self, storage: InfraiStorage, upload_client: httpx.AsyncClient, bucket: str) -> None:
        self._storage = storage
        self._upload_client = upload_client
        self._bucket = bucket
        self._bucket_ready = False

    async def export(self, request: PropertyExportRequest) -> ExportDownload:
        if not self._bucket_ready:
            await self._storage.create_bucket(self._bucket)
            self._bucket_ready = True

        export_id = uuid4().hex
        object_key = f"property-reports/{request.property_id}/{export_id}.csv"
        csv_bytes = build_property_csv(request)
        upload = await self._storage.presign_upload(self._bucket, object_key, export_id)
        if upload.method.upper() == "POST" and upload.fields:
            upload_response = await self._upload_client.request(
                method=upload.method,
                url=upload.url,
                data=upload.fields,
                files={"file": (object_key.rsplit("/", 1)[-1], csv_bytes, "text/csv")},
            )
        else:
            upload_response = await self._upload_client.request(
                method=upload.method,
                url=upload.url,
                headers=upload.fields or {"Content-Type": "text/csv"},
                content=csv_bytes,
            )
        upload_response.raise_for_status()
        download_url = await self._storage.presign_download(self._bucket, object_key)
        row_count = (
            len(request.maintenance_requests)
            + len(request.tenant_documents)
            + len(request.inspection_reminders)
        )
        return ExportDownload(
            download_url=download_url,
            object_key=object_key,
            row_count=row_count,
        )
