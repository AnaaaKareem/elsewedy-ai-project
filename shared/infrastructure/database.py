import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from shared.infrastructure.config import config

# Database URL using config (Vault + Env)
DB_USER = config.DB_CONFIG.get('user')
DB_PASSWORD = config.DB_CONFIG.get('password')
DB_HOST = config.DB_CONFIG.get('host')
DB_PORT = "5432" # Assuming port is standard, or add to config if needed
DB_NAME = config.DB_CONFIG.get('database')

SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
