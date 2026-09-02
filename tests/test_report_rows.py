import csv
import io
from datetime import date

from property_report.report_rows import (
    InspectionReminder,
    MaintenanceRequest,
    PropertyExportRequest,
    TenantDocument,
    build_property_csv,
)


def test_export_labels_past_inspections_and_keeps_all_record_types() -> None:
    request = PropertyExportRequest(
        property_id="cedar-court",
        as_of=date(2026, 8, 18),
        maintenance_requests=[
            MaintenanceRequest(
                request_id="MR-41", unit="2B", summary="Leaking tap", status="scheduled"
            )
        ],
        tenant_documents=[
            TenantDocument(
                document_id="DOC-9",
                unit="2B",
                document_type="insurance certificate",
                received_on=date(2026, 8, 12),
            )
        ],
        inspection_reminders=[
            InspectionReminder(
                reminder_id="INS-7",
                unit="2B",
                inspection_type="smoke alarm",
                due_on=date(2026, 8, 17),
            ),
            InspectionReminder(
                reminder_id="INS-8",
                unit="4A",
                inspection_type="annual safety",
                due_on=date(2026, 8, 18),
            ),
        ],
    )

    rows = list(csv.DictReader(io.StringIO(build_property_csv(request).decode("utf-8"))))

    assert [row["record_type"] for row in rows] == [
        "maintenance_request",
        "tenant_document",
        "inspection_reminder",
        "inspection_reminder",
    ]
    assert [row["status"] for row in rows] == ["scheduled", "received", "overdue", "due"]

