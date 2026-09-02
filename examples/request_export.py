from __future__ import annotations

import json
import os
import urllib.request


payload = {
    "property_id": "cedar-court",
    "as_of": "2026-08-18",
    "maintenance_requests": [
        {"request_id": "MR-41", "unit": "2B", "summary": "Leaking tap", "status": "scheduled"}
    ],
    "tenant_documents": [
        {
            "document_id": "DOC-9",
            "unit": "2B",
            "document_type": "insurance certificate",
            "received_on": "2026-08-12",
        }
    ],
    "inspection_reminders": [
        {
            "reminder_id": "INS-7",
            "unit": "2B",
            "inspection_type": "smoke alarm",
            "due_on": "2026-08-17",
        }
    ],
}

request = urllib.request.Request(
    os.environ.get("PROPERTY_EXPORT_URL", "http://127.0.0.1:8000/exports"),
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(request) as response:
    print(json.dumps(json.load(response), indent=2))

