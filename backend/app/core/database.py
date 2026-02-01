# app/core/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


SQLALCHEMY_DATABASE_URL = os.getenv("POSTGRE_URL") 

if not SQLALCHEMY_DATABASE_URL:
    SQL_ALCHEMY_DB = os.getenv("POSTGRES_DB")
    SQL_ALCHEMY_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    SQL_ALCHEMY_USER = os.getenv("POSTGRES_USER")

    SQLALCHEMY_DATABASE_URL = "postgresql://{SQL_ALCHEMY_USER}:{SQL_ALCHEMY_PASSWORD}@db:5432/{SQL_ALCHEMY_DB}"


engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
