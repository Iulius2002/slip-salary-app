from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    app_env: str = Field("dev", alias="APP_ENV")
    database_url: str = Field(..., alias="DATABASE_URL")
    smtp_host: str = Field("localhost", alias="SMTP_HOST")
    smtp_port: int = Field(1025, alias="SMTP_PORT")

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
