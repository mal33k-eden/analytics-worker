from sqlmodel import Session, create_engine

from app.core.config import settings

from app.models import *

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


def init_db(session: Session) -> None:
    from sqlmodel import SQLModel
    # Create tables for any models not handled by migrations
    # Usually you'd rely on Alembic for this, but this ensures development consistency
    if settings.ENVIRONMENT == "local":
        SQLModel.metadata.create_all(engine)
