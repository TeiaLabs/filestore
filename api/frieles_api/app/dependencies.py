import traceback
from typing import Callable

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from ..settings import settings


def init_app(app: FastAPI):
    setup_cors(app)
    setup_error_handler(app)


def setup_cors(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def setup_error_handler(app: FastAPI) -> None:
    if not settings.CATCH_ERRORS:
        return

    app.add_exception_handler(ValueError, _exception_wrapper(400))
    app.add_exception_handler(Exception, _exception_wrapper(500))


def _exception_wrapper(status_code) -> Callable:
    def handler(_, exc: BaseException):
        if not hasattr(exc, "details"):
            exc.details = str(exc)

        if not hasattr(exc, "msg"):
            exc.msg = "An unknown error occurred"

        exception_content = dict(
            traceback=traceback.format_exc(),
            details=str(exc.details),
            msg=exc.msg,
            type=type(exc).__name__,
        )

        return JSONResponse(
            status_code=status_code,
            content=exception_content,
        )

    return handler
