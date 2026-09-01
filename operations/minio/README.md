# MinIO

Object storage for uploaded PDFs.

## Env

- `MINIO_ENDPOINT` — internal address (e.g. `minio:9000` in Docker)
- `MINIO_PUBLIC_ENDPOINT` — browser-reachable host for presigned URLs (e.g. `localhost:9000`)

Bucket `documents` and CORS (`cors.json`) are applied by **`make initialization`** / **`make setup-minio`** (`scripts/minio/setup.sh`) after Compose marks MinIO healthy. Wipe with `make teardown`.
