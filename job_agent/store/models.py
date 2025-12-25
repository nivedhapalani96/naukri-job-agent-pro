from sqlalchemy import Column, String, Integer, DateTime, Text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class JobRecord(Base):
    __tablename__ = "jobs"
    
    job_key = Column(String(32), primary_key=True)
    source = Column(String(50), nullable=False)
    title = Column(String(500), nullable=False)
    company = Column(String(200), nullable=False)
    location = Column(String(200), nullable=False)
    url = Column(Text, nullable=False)
    posted_text = Column(String(100), default="")
    description = Column(Text, default="")
    
    first_seen_at = Column(DateTime(timezone=True), nullable=False)
    score = Column(Integer, nullable=False)
    score_reasons = Column(Text, default="")
    action = Column(String(20), nullable=False)  # EMAIL, QUEUE, SKIP
    
    emailed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="NEW")  # NEW, APPLIED, SKIPPED, MANUAL
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

