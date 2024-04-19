from pydantic import BaseModel
from redbaby.behaviors import HashIdMixin, ReadingMixin
from redbaby.database import DB
from redbaby.document import Document
from redbaby.errors import DocumentNotFound

from ..settings import settings
from .base import Blob, BlobDriver


class MongoBlob(ReadingMixin, HashIdMixin, Blob, Document):

    @classmethod
    def collection_name(cls) -> str:
        return "blobs"

    def hashable_fields(self) -> list[str]:
        return [str(self.content)]


class MongoStoreConfig(BaseModel):
    database_uri: str

    max_pool_size: int = 100
    min_pool_size: int = 0
    timeout: int = 0


class MongoDriver(BlobDriver):
    @staticmethod
    def find(blob_ref: str, config: MongoStoreConfig) -> MongoBlob:
        setup_connection(config)

        col = MongoBlob.collection(alias=config.database_uri)
        blobs = col.find(filter={"_id": blob_ref}, limit=1)
        if not blobs:
            raise DocumentNotFound(f"Blob with id {blob_ref} not found")
        return blobs[0]

    @staticmethod
    def insert(blob: Blob, config: MongoStoreConfig) -> str:
        setup_connection(config)

        mongo_blob = MongoBlob(content=blob.content)

        col = MongoBlob.collection(alias=config.database_uri)
        col.insert_one(mongo_blob.model_dump(by_alias=True))
        return mongo_blob.id

    @staticmethod
    def delete(blob_ref: str, config: MongoStoreConfig):
        setup_connection(config)

        col = MongoBlob.collection(alias=config.database_uri)
        col.delete_one(filter={"_id": blob_ref})


def setup_connection(config: MongoStoreConfig):
    if config.database_uri not in DB.connections:
        DB.add_conn(
            db_name=settings.DB_NAME,
            uri=config.database_uri,
            alias=config.database_uri,
            start_client=True,
        )
