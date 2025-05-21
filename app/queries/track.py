from sqlmodel import Session, select

from app.core.db import engine
from app.models.track import AnalyticsTrackBase


def select_un_processed_analytics(query_size: int, session: Session = None):
    use_default_session = False

    if session is None:
        session = Session(engine)
        use_default_session = True

    try:
        statement = select(AnalyticsTrackBase).where(AnalyticsTrackBase.processed_at == None).limit(query_size)
        results = session.exec(statement)
        return results.fetchall()

    finally:
        if use_default_session:
            session.close()
