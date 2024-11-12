from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine
#from sqlalchemy.ext.declarative import declarative_base
from fastapi import Depends

# MySQL 연결
DB_USER = 'kelly'
DB_PASSWORD = 'thdnp!1004'
DB_HOST = 'localhost'
DB_PORT = '3306'
DB_NAME = 'database1'

# SQLAlchemy 엔진 생성
engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
