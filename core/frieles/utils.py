from typing import Any, Iterable

from redbaby.database import DB

from .settings import settings


def flatten_collections(acc: str, data: Any) -> Iterable[tuple[str, Any]]:
    if isinstance(data, dict):
        for k, v in data.items():
            new_acc = f"{acc}.{k}"
            yield from flatten_collections(new_acc, v)
    elif isinstance(data, list):
        new_acc = f"{acc}.$"
        for v in data:
            yield from flatten_collections(new_acc, v)
    else:
        yield (acc, data)


def setup_database():
    DB.add_conn(db_name=settings.DB_NAME, uri=settings.DB_URI, start_client=True)
