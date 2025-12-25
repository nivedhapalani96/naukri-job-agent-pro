from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from job_agent.store.models import Base

def create_engine_from_url(db_url: str):
    """Create SQLAlchemy engine from database URL."""
    return create_engine(db_url, echo=False)

def create_session_factory(engine):
    """Create session factory from engine."""
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)

def init_db(engine):
    """Initialize database tables."""
    Base.metadata.create_all(engine)

