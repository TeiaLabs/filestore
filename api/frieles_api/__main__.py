import uvicorn

from .settings import settings


def main():
    uvicorn.run(
        "frieles_api:create_app",
        factory=True,
        reload=settings.RELOAD,
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS,
    )


if __name__ == "__main__":
    main()
