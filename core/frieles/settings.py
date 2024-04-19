import pathlib
import sys

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_URI: str
    DB_NAME: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
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
