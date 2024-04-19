from abc import ABC
from typing import Any

from pydantic import BaseModel


class Blob(BaseModel):
    content: bytes


class BlobDriver(ABC):
    @staticmethod
    def find(blob_ref: str, config: Any) -> Blob: ...

    @staticmethod
    def insert(blob: Blob, config: Any) -> str: ...

    @staticmethod
    def delete(blob_ref: str, config: Any): ...
