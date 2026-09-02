from __future__ import annotations

import csv
import io
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class MaintenanceRequest(BaseModel):
    request_id: str
    unit: str
    summary: str
    status: Literal["open", "scheduled", "closed"]


class TenantDocument(BaseModel):
    document_id: str
    unit: str
    document_type: str
    received_on: date


class InspectionReminder(BaseModel):
    reminder_id: str
    unit: str
    inspection_type: str
    due_on: date


class PropertyExportRequest(BaseModel):
    property_id: str = Field(min_length=1, pattern=r"^[A-Za-z0-9_-]+$")
    as_of: date
    maintenance_requests: list[MaintenanceRequest] = Field(default_factory=list)
    tenant_documents: list[TenantDocument] = Field(default_factory=list)
    inspection_reminders: list[InspectionReminder] = Field(default_factory=list)


CSV_COLUMNS = ("record_type", "record_id", "unit", "subject", "status", "date")


def build_property_csv(export: PropertyExportRequest) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS)
    writer.writeheader()

    for request in export.maintenance_requests:
        writer.writerow(
            {
                "record_type": "maintenance_request",
                "record_id": request.request_id,
                "unit": request.unit,
                "subject": request.summary,
                "status": request.status,
                "date": "",
            }
        )

    for document in export.tenant_documents:
        writer.writerow(
            {
                "record_type": "tenant_document",
                "record_id": document.document_id,
                "unit": document.unit,
                "subject": document.document_type,
                "status": "received",
                "date": document.received_on.isoformat(),
            }
        )

    for reminder in export.inspection_reminders:
        writer.writerow(
            {
                "record_type": "inspection_reminder",
                "record_id": reminder.reminder_id,
                "unit": reminder.unit,
                "subject": reminder.inspection_type,
                "status": "overdue" if reminder.due_on < export.as_of else "due",
                "date": reminder.due_on.isoformat(),
            }
        )

    return output.getvalue().encode("utf-8")

