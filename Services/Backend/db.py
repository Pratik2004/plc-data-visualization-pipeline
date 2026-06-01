import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://plcuser:plcpassword_dev@postgres:5432/plcdata",
)

if "@postgres:" in DATABASE_URL and os.getenv("RUNNING_IN_DOCKER") != "1":
    raise RuntimeError(
        "This backend is configured for Docker only. Start it with docker compose, not local venv."
    )

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
