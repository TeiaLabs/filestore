from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field
from pymongo import IndexModel
from redbaby.behaviors import ReadingMixin, Timestamping
from redbaby.document import Document
from redbaby.hashing import HashDigest
from redbaby.pyobjectid import PyObjectId

from .stores import (
    Blob,
    LocalBlob,
    LocalStoreConfig,
    MongoBlob,
    MongoStoreConfig,
    S3Blob,
    S3StoreConfig,
)

ConfigType = S3StoreConfig | MongoStoreConfig | LocalStoreConfig
Provider = Literal["s3", "mongodb", "local"]


class Location(BaseModel):
    provider: Provider
    config: ConfigType


class Metadata(BaseModel):
    mimetype: str
    path: str
    size_bytes: int

    created_at: datetime
    modified_at: datetime

    extras: dict[str, Any] | None = None


class File[T: BaseModel](ReadingMixin, Timestamping, Document):
    id: PyObjectId = Field(alias="_id", default_factory=PyObjectId)

    metadata: Metadata
    location: Location

    blob_ref: HashDigest
    created_by: T

    search_tags: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def collection_name(cls) -> str:
        return "files"

    @classmethod
    def indexes(cls) -> list[IndexModel]:
        return [
            IndexModel([("blob_ref", "hash")], unique=True),
            IndexModel([("metadata.path", "text")]),
            IndexModel([("store.provider", "text")]),
        ]


class BlobbedFile[T: BaseModel](BaseModel):
    blob: Blob
    metadata: Metadata
    location: Location

    created_by: T

    search_tags: dict[str, Any] = Field(default_factory=dict)
