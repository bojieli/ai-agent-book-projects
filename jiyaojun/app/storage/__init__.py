"""对象存储抽象 — mock 与 S3-compatible（SeaweedFS）。"""

from app.storage.object_store import MockObjectStore, ObjectStore, S3ObjectStore

__all__ = ["ObjectStore", "MockObjectStore", "S3ObjectStore"]
