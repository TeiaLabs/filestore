from typing import Iterable

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from frieles import Store
from frieles.schemas import BlobbedFile, File
from pymongo.results import DeleteResult
from redbaby.errors import DocumentNotFound

from .schemas import DeleteMany, SearchTag, UpdateOne

router = APIRouter(prefix="/files")


@router.get("/")
def find(
    path: str | None = Query(None),
    mimetype: str | None = Query(None),
    provider: str | None = Query(None),
    search_tags: list[SearchTag] | None = Query(None),
    return_blob: bool = Query(False),
    skip: int = 0,
    limit: int = 0,
) -> Iterable[BlobbedFile] | Iterable[File]:
    filters = {}
    if path is not None:
        filters["metadata.path"] = path
    if mimetype is not None:
        filters["metadata.mimetype"] = mimetype
    if provider is not None:
        filters["location.provider"] = provider
    if search_tags is not None:
        for search_tag in search_tags:
            filters[f"search_tags.{search_tag.key}"] = search_tag.value

    return Store.read(
        filters=filters,
        return_blob=return_blob,
        skip=skip,
        limit=limit,
    )


@router.get("/{blob_ref}/")
def find_one(blob_ref: str, return_blob: bool = Query()) -> BlobbedFile | File:
    try:
        return Store.read_one(blob_ref, return_blob)
    except DocumentNotFound as e:
        raise HTTPException(status=404, details=str(e))


@router.post("/")
def create(file: BlobbedFile):
    result = Store.create_one(file)
    return JSONResponse(
        headers={"Location": f"/files/{result.inserted_id}/"},
        status_code=201,
        content=result,
    )


@router.put("/{blob_ref}/", status_code=204)
def update_one(blob_ref: str, update: UpdateOne) -> None:
    result = Store.update_one(
        blob_ref=blob_ref,
        metadata=update.metadata,
        location=update.location,
        search_tags=update.search_tags,
    )
    if not result.matched_count:
        raise HTTPException(status_code=404, detail="Document not found.")

    if not result.modified_count:
        raise HTTPException(status_code=304, detail="Document not modified.")


@router.delete("/{blob_ref}/")
def delete_one(blob_ref: str) -> DeleteResult:
    return Store.delete_one(blob_ref)


@router.delete("/bulk/")
def delete_many(delete_filters: DeleteMany) -> DeleteResult:
    return Store.delete(
        blob_ref=delete_filters.blob_ref,
        metadata=delete_filters.metadata,
        location=delete_filters.location,
        search_tags=delete_filters.search_tags,
    )
