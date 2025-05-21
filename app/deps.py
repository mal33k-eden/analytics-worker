from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session

from app.core.db import engine


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


AsyncSession = Annotated[Session, Depends(get_db)]


async def get_session() -> AsyncSession:
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
