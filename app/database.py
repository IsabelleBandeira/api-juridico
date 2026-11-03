from sqlalchemy import create_engine
from sqlalchemy.engine import URL

from app.config import settings


connection_url = URL.create(
    "mssql+pyodbc",
    username=settings.database_user,
    password=settings.database_password,
    host=settings.database_host,
    port=settings.database_port,
    database=settings.database_name,
    query={
        "driver": settings.database_driver,
        "Encrypt": "yes",
        "TrustServerCertificate": "yes",
    },
)

engine = create_engine(
    connection_url,
    pool_pre_ping=True,
)