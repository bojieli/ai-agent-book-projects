"""对象存储协议 — 内存 mock 与 SeaweedFS S3-compatible 实现。"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from urllib.parse import urlparse


@runtime_checkable
class ObjectStore(Protocol):
    """大转写/产物对象读写契约。"""

    @property
    def scheme(self) -> str:
        """URI 前缀，如 mock 或 s3。"""
        ...

    def put(self, key: str, data: bytes, *, content_type: str = "application/octet-stream") -> str:
        """写入对象，返回完整 URI。"""
        ...

    def get(self, key: str) -> bytes:
        """读取对象字节；不存在时抛 KeyError。"""
        ...

    def delete(self, key: str) -> bool:
        """删除对象；存在则 True。"""
        ...

    def exists(self, key: str) -> bool:
        """对象是否存在。"""
        ...


def normalize_object_key(key: str) -> str:
    """去掉 s3://bucket/ 或 mock:// 前缀，得到纯对象键。"""
    if "://" in key:
        parsed = urlparse(key)
        path = parsed.path.lstrip("/")
        return path
    return key.lstrip("/")


class MockObjectStore:
    """进程内对象存储 — 默认离线路径。"""

    def __init__(self, bucket: str = "mock") -> None:
        self.bucket = bucket
        self._objects: dict[str, bytes] = {}

    @property
    def scheme(self) -> str:
        return "mock"

    def _uri(self, key: str) -> str:
        return f"s3://{self.bucket}/{normalize_object_key(key)}"

    def put(self, key: str, data: bytes, *, content_type: str = "application/octet-stream") -> str:
        norm = normalize_object_key(key)
        self._objects[norm] = bytes(data)
        return self._uri(norm)

    def get(self, key: str) -> bytes:
        norm = normalize_object_key(key)
        if norm not in self._objects:
            raise KeyError(norm)
        return self._objects[norm]

    def delete(self, key: str) -> bool:
        norm = normalize_object_key(key)
        if norm in self._objects:
            del self._objects[norm]
            return True
        return False

    def exists(self, key: str) -> bool:
        return normalize_object_key(key) in self._objects


class S3ObjectStore:
    """SeaweedFS / 任意 S3-compatible 端点；path-style 寻址。"""

    def __init__(
        self,
        *,
        endpoint: str,
        bucket: str,
        access_key: str = "",
        secret_key: str = "",
    ) -> None:
        import boto3
        from botocore.client import Config
        from botocore.exceptions import ClientError

        self.bucket = bucket
        self._ClientError = ClientError
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key or "local-dev-access",
            aws_secret_access_key=secret_key or "local-dev-secret",
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )
        self._ensure_bucket()

    @property
    def scheme(self) -> str:
        return "s3"

    def _ensure_bucket(self) -> None:
        """bucket 不存在时创建（SeaweedFS 本地常需显式 create_bucket）。"""
        try:
            self._client.head_bucket(Bucket=self.bucket)
        except self._ClientError:
            try:
                self._client.create_bucket(Bucket=self.bucket)
            except self._ClientError:
                # 并发创建或已存在
                self._client.head_bucket(Bucket=self.bucket)

    def _uri(self, key: str) -> str:
        return f"s3://{self.bucket}/{normalize_object_key(key)}"

    def put(self, key: str, data: bytes, *, content_type: str = "application/octet-stream") -> str:
        norm = normalize_object_key(key)
        self._client.put_object(
            Bucket=self.bucket,
            Key=norm,
            Body=data,
            ContentType=content_type,
        )
        return self._uri(norm)

    def get(self, key: str) -> bytes:
        norm = normalize_object_key(key)
        try:
            resp = self._client.get_object(Bucket=self.bucket, Key=norm)
        except self._ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code in {"NoSuchKey", "404", "NotFound"}:
                raise KeyError(norm) from exc
            raise
        body = resp.get("Body")
        if body is None:
            raise KeyError(norm)
        return body.read()

    def delete(self, key: str) -> bool:
        norm = normalize_object_key(key)
        if not self.exists(norm):
            return False
        self._client.delete_object(Bucket=self.bucket, Key=norm)
        return True

    def exists(self, key: str) -> bool:
        norm = normalize_object_key(key)
        try:
            self._client.head_object(Bucket=self.bucket, Key=norm)
            return True
        except self._ClientError:
            return False


def s3_reachable(
    endpoint: str,
    bucket: str,
    access_key: str = "",
    secret_key: str = "",
) -> bool:
    """探测 S3 端点是否可用（集成测试 skip 用）。"""
    try:
        store = S3ObjectStore(
            endpoint=endpoint,
            bucket=bucket,
            access_key=access_key,
            secret_key=secret_key,
        )
        probe_key = "__reachability_probe__"
        store.put(probe_key, b"ok")
        store.delete(probe_key)
        return True
    except Exception:
        return False
