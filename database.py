from sqlmodel import create_engine, Session
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL не задан в .env")

engine = create_engine(DATABASE_URL)

def create_db_and_tables():
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session