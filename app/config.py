from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_host: str
    database_port: int = 1433
    database_name: str
    database_user: str
    database_password: str
    database_driver: str = "ODBC Driver 18 for SQL Server"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


settings = Settings()