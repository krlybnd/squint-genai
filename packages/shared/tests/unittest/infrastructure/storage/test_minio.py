import unittest
from io import BytesIO
from unittest.mock import MagicMock

from agentic_shared.infrastructure.cache.redis.settings import RedisSettings
from agentic_shared.infrastructure.storage.minio.reader import MinioStorageReader
from agentic_shared.infrastructure.storage.minio.settings import MinioSettings
from agentic_shared.infrastructure.storage.minio.writer import MinioStorageWriter


class TestRedisSettings(unittest.TestCase):
    def test_defaults(self) -> None:
        settings = RedisSettings()
        self.assertEqual(settings.title, "redis")
        self.assertTrue(settings.redis_url.startswith("redis://"))
        self.assertTrue(settings.celery_broker_url.startswith("redis://"))
        self.assertTrue(settings.celery_result_backend.startswith("redis://"))


class TestMinioSettings(unittest.TestCase):
    def test_defaults(self) -> None:
        settings = MinioSettings()
        self.assertEqual(settings.title, "minio")
        self.assertEqual(settings.minio_endpoint, "localhost:9000")
        self.assertIsNone(settings.minio_public_endpoint)
        self.assertEqual(settings.minio_bucket, "documents")
        self.assertFalse(settings.minio_secure)
        self.assertEqual(settings.minio_presign_expiry_seconds, 3600)
        self.assertEqual(settings.minio_access_key.get_secret_value(), "minioadmin")


class TestMinioStorageReader(unittest.TestCase):
    def test_object_exists_delegates(self) -> None:
        client = MagicMock()
        client.object_exists.return_value = True
        reader = MinioStorageReader(client)
        self.assertTrue(reader.object_exists("k"))
        client.object_exists.assert_called_once_with("k")

    def test_download_reads_and_releases(self) -> None:
        response = MagicMock()
        response.read.return_value = b"pdf"
        client = MagicMock()
        client.bucket = "documents"
        client.sdk.get_object.return_value = response
        reader = MinioStorageReader(client)
        self.assertEqual(reader.download("a.pdf"), b"pdf")
        response.close.assert_called_once()
        response.release_conn.assert_called_once()


class TestMinioStorageWriter(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = MinioSettings(
            minio_endpoint="minio:9000",
            minio_public_endpoint="localhost:9000",
            minio_secure=False,
            minio_presign_expiry_seconds=120,
        )
        self.client = MagicMock()
        self.client.settings = self.settings
        self.client.bucket = "documents"
        self.writer = MinioStorageWriter(self.client)

    def test_presigned_put_url_rewrites_public_host(self) -> None:
        self.client.sdk.presigned_put_object.return_value = (
            "http://minio:9000/documents/key?X-Amz-Signature=abc"
        )
        url, expires = self.writer.presigned_put_url("key")
        self.client.ensure_bucket.assert_called_once()
        self.assertEqual(expires, 120)
        self.assertTrue(url.startswith("http://localhost:9000/"))
        self.assertIn("X-Amz-Signature=abc", url)

    def test_presigned_put_url_keeps_host_when_public_unset(self) -> None:
        self.client.settings = MinioSettings(minio_endpoint="minio:9000")
        self.client.sdk.presigned_put_object.return_value = "http://minio:9000/documents/key"
        url, _expires = self.writer.presigned_put_url("key", expires_seconds=30)
        self.assertEqual(url, "http://minio:9000/documents/key")

    def test_upload_and_delete(self) -> None:
        self.assertEqual(self.writer.upload("k", b"data", content_type="text/plain"), "k")
        self.client.sdk.put_object.assert_called_once()
        args, kwargs = self.client.sdk.put_object.call_args
        self.assertEqual(args[0], "documents")
        self.assertEqual(args[1], "k")
        self.assertIsInstance(args[2], BytesIO)
        self.assertEqual(kwargs["length"], 4)
        self.assertEqual(kwargs["content_type"], "text/plain")

        self.writer.delete("k")
        self.client.sdk.remove_object.assert_called_once_with("documents", "k")
