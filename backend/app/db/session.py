import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.logging import logger

connect_args = {}
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

if settings.USE_SQLITE_FALLBACK or "sqlite" in db_url:
    connect_args = {"check_same_thread": False, "timeout": 30}
    engine = create_engine(db_url, connect_args=connect_args)
else:
    try:
        engine = create_engine(db_url, pool_pre_ping=True, pool_size=10, max_overflow=20)
        # Test connection
        with engine.connect() as conn:
            pass
    except Exception as e:
        logger.warning(
            f"Could not connect to PostgreSQL at {db_url}: {e}. Falling back to SQLite for local development/testing."
        )
        db_url = settings.SQLITE_FALLBACK_URL
        connect_args = {"check_same_thread": False, "timeout": 30}
        engine = create_engine(db_url, connect_args=connect_args)

if "sqlite" in str(engine.url):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

