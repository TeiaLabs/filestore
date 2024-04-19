from pathlib import Path

from pydantic import BaseModel
from redbaby.errors import DocumentNotFound
from redbaby.hashing import get_hash

from .base import Blob, BlobDriver


class LocalBlob(Blob):
    pass


class LocalStoreConfig(BaseModel):
    directory: Path


class LocalDriver(BlobDriver):
    @staticmethod
    def find(blob_ref: str, config: LocalStoreConfig) -> LocalBlob:
        for file in config.directory.glob("**/*"):
            if file.name == blob_ref:
                with open(file.absolute(), "rb") as f:
                    content = f.read()
                return LocalBlob(content=content)

        raise DocumentNotFound

    @staticmethod
    def insert(blob: Blob, config: LocalStoreConfig) -> str:
        blob_hash = get_hash(str(blob.content))
        with open(config.directory / blob_hash, "wb") as f:
            f.write(blob.content)

        return blob_hash

    @staticmethod
    def delete(blob_ref: str, config: LocalStoreConfig):
        for file in config.directory.glob("**/*"):
            if file.name == blob_ref:
                file.unlink()
                return
        raise DocumentNotFound
