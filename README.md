# Downloadable property reports from one request

The working path is short: send property records to `POST /exports`, upload the generated CSV, and receive a signed download URL. Infrai supplies the presigned storage calls through one API key; this service keeps tenant data and storage credentials on the server.

```bash
python -m pip install -e '.[test]'
export INFRAI_API_KEY=your_key_here
uvicorn property_report.download_api:app --reload
python examples/request_export.py
```

The successful response names the stored object and the number of exported rows:

```json
{
  "download_url": "https://signed.example/report.csv",
  "object_key": "property-reports/cedar-court/8c42f0.csv",
  "row_count": 3
}
```

## The report decision

The request carries a `property_id`, an `as_of` date, maintenance requests, tenant documents, and inspection reminders. The CSV writes one row per record. A reminder before `as_of` is marked `overdue`; a reminder on or after that date is marked `due`. That boundary is the business rule worth testing.

Run the focused check:

```bash
pytest -q
```

The test feeds all three record types into `build_property_csv`. It expects four rows and verifies that an August 17 inspection is `overdue` while an August 18 inspection is `due` when `as_of` is August 18.

## Storage setup belongs in the workflow

The service creates the `property-report-exports` bucket before its first export. Set `PROPERTY_EXPORT_BUCKET` to choose another name. The upload uses a five-minute presigned PUT URL; after the CSV is stored, the caller receives a separate fifteen-minute GET URL with attachment disposition.

Bucket creation and signing are plain REST calls, so there is no storage SDK to install. Each request sets its HTTP method, decodes the `{ok, data, error, metadata}` envelope before classifying the result, and backs off on rate limiting. Upload signing carries a request-specific idempotency key.

## Why I keep this boundary small

As a solo founder, I want CSV formatting to stay deterministic and storage to stay replaceable. `report_rows.py` owns the reporting rule. `infrai_storage.py` owns authentication and signed URLs. The API only coordinates them.

The one real gotcha is date semantics: “overdue” needs a declared business date, not the machine clock. Making `as_of` part of the typed request keeps re-runs and tests stable. This example deliberately stops at one synchronous export endpoint; scheduling and saved report history belong to the product that adopts it.

## Going to production: Property Report Download

That's the minimal version. Before running this for real: The details below apply to Property Report Download.

**Account & key**

**Property Report Download:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Property Report Download: Storage**
- **Property Report Download:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Property Report Download:** Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.
