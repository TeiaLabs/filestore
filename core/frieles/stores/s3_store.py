from typing import Literal

import boto3
from pydantic import BaseModel
from redbaby.errors import DocumentNotFound
from redbaby.hashing import get_hash

from .base import Blob, BlobDriver


class S3Blob(Blob):
    pass


class S3StoreConfig(BaseModel):
    access_key_id: str
    secret_access_key: str
    region: str

    bucket_name: str = "default"
    connect_timeout: int = 60
    read_timeout: int = 60
    max_pool_connections: int = 10
    use_accelerate_endpint: bool = False
    addressing_style: Literal["auto", "virtual", "path"]


class S3Cache:
    sessions = {}

    @classmethod
    def get_session(cls, config: S3StoreConfig):
        key = (config.access_key_id, config.region)

        if key in cls.sessions:
            return cls.sessions[key]

        session = boto3.session.Session(
            aws_access_key_id=config.access_key_id,
            aws_secret_access_key=config.secret_access_key,
            region_name=config.region,
        )
        cls.sessions[key] = session
        return session

    @classmethod
    def get_s3(cls, config: S3StoreConfig):
        session = cls.get_session(config)
        return session.resource("s3")

    @classmethod
    def get_bucket(cls, config: S3StoreConfig):
        s3 = cls.get_s3(config)
        return s3.Bucket(config.bucket_name)


class S3Driver(BlobDriver):
    @staticmethod
    def find(blob_ref: str, config: S3StoreConfig) -> S3Blob:
        bucket = S3Cache.get_bucket(config)

        objs = list(bucket.objects.filter(Prefix=blob_ref))
        if not objs:
            raise DocumentNotFound

        obj = None
        for returned_obj in objs:
            if returned_obj.key == blob_ref:
                obj = returned_obj
                break

        response = obj.get()
        return S3Blob(content=response["Body"].read())

    @staticmethod
    def insert(blob: Blob, config: S3StoreConfig) -> str:
        blob_ref = get_hash(str(blob.content))

        bucket = S3Cache.get_bucket(config)

        obj = bucket.Object(blob_ref)
        obj.put(Body=blob.content)
        return blob_ref

    @staticmethod
    def delete(blob_ref: str, config: S3StoreConfig):
        s3 = S3Cache.get_s3()
        s3.Object(config.bucket_name, blob_ref).delete()
