import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ────────────────────────────────────────────────
# IMPORTANT: Replace with YOUR actual connection name

CLOUD_SQL_CONNECTION_NAME = "mini-iam:us-central1:mini-iam-db"

DB_USER = "miniiam_user"
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = "miniiam"

if not DB_PASSWORD:
    raise ValueError("Environment variable DB_PASSWORD is not set")

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@/"
    f"{DB_NAME}?host=/cloudsql/{CLOUD_SQL_CONNECTION_NAME}"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()