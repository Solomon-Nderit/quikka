from typing import Annotated, Generator
import os

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

# Use absolute path to ensure we're using the app database
sqlite_file_name = os.path.join(os.path.dirname(__file__), "database.db")
sqlite_url = f"sqlite:///{sqlite_file_name}"

# Needed for SQLite when using multiple threads (e.g., Uvicorn reload)
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
