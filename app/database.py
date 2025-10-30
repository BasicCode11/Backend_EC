from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import Pool
import urllib.parse
from .core.config import settings

engine_kwargs = {"echo": True , "pool_pre_ping": True}

if settings.DB_TYPE == "mysql":
    DB_PASSWORD_ENCODED = urllib.parse.quote_plus(settings.DB_PASSWORD)
    # Add timezone parameter to MySQL connection
    DATABASE_URL = f"mysql+pymysql://{settings.DB_USER}:{DB_PASSWORD_ENCODED}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}?charset=utf8mb4"

elif settings.DB_TYPE == "postgresql":
    DATABASE_URL = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

else:
    raise ValueError(f"Invalid database type: {settings.DB_TYPE}")

engine = create_engine(DATABASE_URL, **engine_kwargs)

# Set timezone for MySQL connections
if settings.DB_TYPE == "mysql":
    @event.listens_for(Pool, "connect")
    def set_timezone(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("SET time_zone = '+00:00'")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()