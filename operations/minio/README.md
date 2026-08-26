# MinIO

Object storage for uploaded PDFs.

## Env

- `MINIO_ENDPOINT` — internal address (e.g. `minio:9000` in Docker)
- `MINIO_PUBLIC_ENDPOINT` — browser-reachable host for presigned URLs (e.g. `localhost:9000`)

Bucket `documents` and CORS are configured by the **`ops`** service (`tools/ops`) after app services start — not by a MinIO sidecar.
