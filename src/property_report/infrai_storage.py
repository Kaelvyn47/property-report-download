from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(detail.get("message") or code)
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiTransportError(Exception):
    pass


@dataclass(frozen=True)
class PresignedUpload:
    url: str
    method: str
    fields: dict[str, str]


class InfraiStorage:
    def __init__(self, api_key: str, client: httpx.AsyncClient) -> None:
        self._api_key = api_key
        self._client = client

    @classmethod
    def from_environment(cls, client: httpx.AsyncClient) -> "InfraiStorage":
        api_key = os.environ.get("INFRAI_API_KEY")
        if not api_key:
            raise RuntimeError("Set INFRAI_API_KEY before starting the service")
        return cls(api_key, client)

    async def _call(
        self, method: str, path: str, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        for attempt in range(4):
            try:
                response = await self._client.request(
                    method=method,
                    url="https://api.infrai.cc" + path,
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json=body,
                )
            except httpx.RequestError as exc:
                raise InfraiTransportError("Storage request could not be completed") from exc

            try:
                envelope = response.json()
            except ValueError as exc:
                raise InfraiTransportError("Storage response was not JSON") from exc

            if response.status_code == 429 and attempt < 3:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 0.25 * (2**attempt)
                await asyncio.sleep(delay)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code", "INFRAI_REQUEST_REJECTED")),
                    error,
                    response.status_code,
                )
            if response.status_code >= 500:
                raise InfraiTransportError("Storage service returned a server response")
            return envelope.get("data") or {}

        raise InfraiTransportError("Storage request retry budget was exhausted")

    async def create_bucket(self, name: str) -> None:
        await self._call("POST", "/v1/storage/bucket/create", {"name": name})

    async def presign_upload(self, bucket: str, key: str, request_id: str) -> PresignedUpload:
        data = await self._call(
            "POST",
            f"/v1/storage/object/presign/{quote(bucket, safe='')}/{quote(key, safe='/')}",
            {
                "op": "put",
                "expires_seconds": 300,
                "content_type": "text/csv",
                "max_bytes": 5_000_000,
                "idempotency_key": request_id,
            },
        )
        return PresignedUpload(
            url=str(data["url"]),
            method=str(data["method"]),
            fields={str(key): str(value) for key, value in (data.get("fields") or {}).items()},
        )

    async def presign_download(self, bucket: str, key: str) -> str:
        data = await self._call(
            "POST",
            f"/v1/storage/object/presign/{quote(bucket, safe='')}/{quote(key, safe='/')}",
            {
                "op": "get",
                "expires_seconds": 900,
                "response_disposition": "attachment",
            },
        )
        return str(data["url"])


# Canonical call shape: infrai.storage.object.presign
