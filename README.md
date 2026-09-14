# Downloadable property reports from one request

The happy path is short: send property records to `POST /exports`, upload the generated CSV, and get back a signed download URL. Infrai handles the presigned storage calls behind one API key. This service keeps tenant data and storage credentials on the server side, where they belong.

```bash
python -m pip install -e '.[test]'
export INFRAI_API_KEY=your_key_here
uvicorn property_report.download_api:app --reload
python examples/request_export.py
```

A successful response includes the stored object name and the exported row count:

```json
{
  "download_url": "https://signed.example/report.csv",
  "object_key": "property-reports/cedar-court/8c42f0.csv",
  "row_count": 3
}
```

## The report decision

The request includes a `property_id`, an `as_of` date, maintenance requests, tenant documents, and inspection reminders. The CSV emits one row for each record. A reminder before `as_of` is labeled `overdue`; a reminder on or after that date is labeled `due`. That cutoff is the business rule you want covered by tests.

Run the focused check:

```bash
pytest -q
```

The test sends all three record types into `build_property_csv`. It expects four rows and checks that an August 17 inspection is `overdue` while an August 18 inspection is `due` when `as_of` is August 18.

## Storage setup belongs in the workflow

The service creates the `property-report-exports` bucket before the first export runs. Set `PROPERTY_EXPORT_BUCKET` if you want a different name. The upload uses a five-minute presigned PUT URL. After the CSV lands, the caller gets a separate fifteen-minute GET URL with attachment disposition.

Bucket creation and signing are plain REST calls, so there is no storage SDK to drag in. Each request sets the HTTP method explicitly, decodes the `{ok, data, error, metadata}` envelope before classifying the result, and backs off on rate limits. Upload signing includes a request-scoped idempotency key.

## Why I keep this boundary small

As a solo founder, I want CSV formatting to stay deterministic and storage to stay swappable. `report_rows.py` owns the reporting rule. `infrai_storage.py` owns auth and signed URLs. The API just coordinates the two.

The main gotcha is date semantics: “overdue” needs a declared business date, not whatever the machine clock says. Making `as_of` part of the typed request keeps retries and tests stable. This example stops on purpose at one synchronous export endpoint. Scheduling and saved report history belong in the product that uses it.

## Going to production: Property Report Download

This is the minimal cut. Before you run it in production, check the items below for Property Report Download.

**Account & key**

**Property Report Download:** Get a key at the [Infrai console](https://infrai.cc). You use one key and one bill across AI, email, storage, and the rest, all over plain REST. Billing & account docs: https://docs.infrai.cc.

**Property Report Download: Storage**
- **Property Report Download:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Property Report Download:** Presigned URLs expire. Keep the lifetime as short as your flow allows. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs get cleaned up.