import pathlib
import sys

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Server config
    HOST: str = "0.0.0.0"
    PORT: int = 5000
    RELOAD: bool = True
    WORKERS: int = 1

    # Database
    DB_URI: str
    DB_NAME: str

    # Cors
    ORIGINS: list[str] = ["*"]

    # Error handling
    CATCH_ERRORS: bool = True

    # BaseSettings config
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
        frozen=True,
    )


try:
    settings = Settings()
except ValidationError as e:
    directory = pathlib.Path(".").absolute()
    print(
        f"The .env file is invalid or could not be "
        f"found on the current directory={directory}.\nValidation: {e}",
        file=sys.stderr,
    )
    exit(-1)
