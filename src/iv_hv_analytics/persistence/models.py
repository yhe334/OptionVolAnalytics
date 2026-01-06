from sqlalchemy import Column, Integer, String, Float, DateTime, Text, UniqueConstraint
from sqlalchemy.sql import func
from iv_hv_analytics.persistence.db import Base

class VolRequest(Base):
    __tablename__ = 'vol_requests'
    id = Column(Integer, primary_key=True, index=True)
    request_hash = Column(String(64),nullable = False, index=True)
    params_json = Column(Text, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False) 

    __table_args__ = (UniqueConstraint('request_hash', name='uq_request_hash'),)    

class VolResult(Base):
    __tablename__ = 'vol_results'
    id = Column(Integer, primary_key=True, index=True)
    request_hash = Column(String(64),nullable = False, index=True)
    result_json = Column(Text, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False) 