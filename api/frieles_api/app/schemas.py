from typing import Any

from frieles.schemas import Location, Metadata
from pydantic import BaseModel


class SearchTag(BaseModel):
    key: str
    value: Any


class UpdateOne(BaseModel):
    metadata: Metadata | None = None
    location: Location | None = None
    search_tags: dict[str, Any] | None = None


class DeleteMany(UpdateOne):
    blob_ref: str
