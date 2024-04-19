from typing import Any, Iterable, Literal, overload

from pymongo.results import DeleteResult, InsertOneResult, UpdateResult
from redbaby.errors import DocumentNotFound, InvalidUpdateDict

from .errors import InvalidStoreError
from .schemas import Blob, BlobbedFile, File, Literal, Location, Metadata, Provider
from .stores import LocalDriver, MongoDriver, S3Driver
from .utils import flatten_collections

Driver = LocalDriver | MongoDriver | S3Driver

BLOB_DRIVER_MAP: dict[Provider, Driver] = {
    "local": LocalDriver,
    "mongodb": MongoDriver,
    "s3": S3Driver,
}


def find_blob(blob_ref: str, location: Location) -> Blob:
    """
    Find a blob in store.

    :param blob_ref: The blob reference of the file to find.
    :param location: The location of the store.
    :return: The blob content.
    :raises: DocumentNotFound if the file does not exist.
    :raises InvalidStoreError if the provider is not one of ["local", "mongodb", "s3"].
    """

    driver = BLOB_DRIVER_MAP.get(location.provider)
    if driver is None:
        raise InvalidStoreError

    return driver.find(blob_ref, location.config)


def insert_blob(blob: Blob, location: Location) -> str:
    """
    Insert a blob in store.

    :param blob: The blob to insert.
    :param location: The location of the store.
    :return: The blob reference.
    :raises InvalidStoreError if the provider is not one of ["local", "mongodb", "s3"].
    """

    driver = BLOB_DRIVER_MAP.get(location.provider)
    if driver is None:
        raise InvalidStoreError

    return driver.insert(blob, location.config)


def delete_blob(blob_ref: str, location: Location) -> str:
    """
    Delete a blob from store.

    :param blob_ref: The blob reference of the file to delete.
    :param location: The location of the store.
    :return: The blob reference.
    :raises InvalidStoreError if the provider is not one of ["local", "mongodb", "s3"].
    """

    driver = BLOB_DRIVER_MAP.get(location.provider)
    if driver is None:
        raise InvalidStoreError

    return driver.delete(blob_ref, location.config)


def _inject_blob(dict_file: dict[str, Any]) -> BlobbedFile:
    blob_ref = dict_file.pop("blob_ref")
    dict_file["blob"] = find_blob(blob_ref, Location(**dict_file["location"]))
    return BlobbedFile(**dict_file)


class Store:
    @staticmethod
    def create_one(file: BlobbedFile) -> InsertOneResult:
        """
        Create a single file in store.

        :param file: The file to create.
        :return: The result of the insert operation.
        :raises: DuplicateKeyError if the file already exists or if the blob reference is not unique.
        """

        blob_ref = insert_blob(file.blob, file.location)

        db_file = File(
            metadata=file.metadata,
            location=file.location,
            blob_ref=blob_ref,
            created_by=file.created_by,
            search_tags=file.search_tags,
        )
        dict_file = db_file.model_dump(by_alias=True)

        col = File.collection()
        result = col.insert_one(dict_file)
        raise result

    @staticmethod
    @overload
    def read_one(blob_ref: str, return_blob: Literal[True]) -> BlobbedFile: ...
    @staticmethod
    @overload
    def read_one(blob_ref: str, return_blob: Literal[False]) -> File: ...
    @staticmethod
    @overload
    def read_one(blob_ref: str, return_blob=...) -> File: ...
    @staticmethod
    def read_one(blob_ref: str, return_blob: bool = False) -> BlobbedFile | File:
        """
        Read a single file from store.

        :param blob_ref: The blob reference of the file to read.
        :param return_blob: If True, returns a BlobbedFile with the Blob content.
        :return: A BlobbedFile or File object.
        :raises: DocumentNotFound if the file does not exist.
        """

        files = File.find(filter={"blob_ref": blob_ref}, limit=1)
        if not files:
            raise DocumentNotFound

        dict_file = files[0]
        if not return_blob:
            return File(**dict_file)
        return _inject_blob(dict_file)

    @staticmethod
    @overload
    def read(
        return_blob: Literal[True],
        filters: dict[str, Any] | None = None,
    ) -> Iterable[BlobbedFile]: ...
    @staticmethod
    @overload
    def read(
        return_blob: Literal[False],
        filters: dict[str, Any] | None = None,
    ) -> Iterable[File]: ...
    @staticmethod
    @overload
    def read(
        return_blob=...,
        filters: dict[str, Any] | None = None,
    ) -> Iterable[File]: ...
    @staticmethod
    def read(
        return_blob: bool = False,
        filters: dict[str, Any] | None = None,
        skip: int = 0,
        limit: int = 0,
    ) -> Iterable[BlobbedFile] | Iterable[File]:
        """
        Read multiple files from store.

        :param return_blob: If True, returns Files with the Blob content.
        :param filters: A dictionary of filters to apply to the query.
        :param skip: The number of documents to skip.
        :param limit: The maximum number of documents to return.
        :return: An iterable of BlobbedFile or File objects.
        """

        files = File.find(filter=filters, skip=skip, limit=limit, lazy=True)
        if not return_blob:
            return (File(**file) for file in files)
        return (_inject_blob(file) for file in files)

    @staticmethod
    def update_one(
        blob_ref: str,
        metadata: Metadata | None = None,
        location: Location | None = None,
        search_tags: dict[str, Any] | None = None,
    ) -> UpdateResult:
        """
        Update a single file in store.

        :param blob_ref: The blob reference of the file to update.
        :param metadata: The metadata to update.
        :param location: The location to update.
        :param search_tags: The search tags to update.
        :return: The result of the update operation.
        :raises: InvalidUpdateDict if no update is provided.
        """

        update = {}
        if metadata is not None:
            for k, v in flatten_collections("metadata", metadata):
                update[k] = v

        if location is not None:
            for k, v in flatten_collections("location", metadata):
                update[k] = v

        if search_tags is not None:
            update["search_tags"] = search_tags

        if not update:
            raise InvalidUpdateDict

        col = File.collection()
        return col.update_one(filter={"_id": blob_ref}, update={"$set": update})

    @staticmethod
    def delete_one(blob_ref: str) -> DeleteResult:
        """
        Delete a single file from store.

        :param blob_ref: The blob reference of the file to delete.
        :return: The result of the delete operation.
        :raises: DocumentNotFound if the file does not exist.
        :raises InvalidStoreError if the file is not unique.
        """

        file = Store.read_one(blob_ref, return_blob=False)
        delete_blob(blob_ref, file.location)

        col = File.collection()
        return col.delete_one(filter={"blob_ref": blob_ref})

    @staticmethod
    def delete(
        blob_ref: str | None = None,
        metadata: Metadata | None = None,
        location: Location | None = None,
        search_tags: dict[str, Any] | None = None,
    ) -> DeleteResult:
        """
        Delete multiple files from store.

        :param blob_ref: The blob reference of the file to delete.
        :param search_tags: The search tags to filter by.
        :return: The result of the delete operation.
        :raises InvalidStoreError if the file is not unique.
        """

        filter = {}
        if blob_ref is not None:
            filter["blob_ref"] = blob_ref
        else:
            if metadata is not None:
                for k, v in flatten_collections("metadata", metadata):
                    filter[k] = v

            if location is not None:
                for k, v in flatten_collections("location", metadata):
                    filter[k] = v

            if search_tags is not None:
                for k, v in flatten_collections("search_tags", search_tags):
                    filter[k] = v

        files = Store.read(return_blob=False, filters=filter)
        for file in files:
            delete_blob(file.blob_ref, file.location)

        col = File.collection()
        return col.delete_many(filter)

    @staticmethod
    def cleanup():
        raise NotImplementedError
