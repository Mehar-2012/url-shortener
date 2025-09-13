from sqlalchemy import Column, Integer, String, DateTime
from database import Base
import datetime

class URL(Base):
    __tablename__ = 'urls'

    id = Column(Integer, primary_key=True, index=True)
    long_url = Column(String, nullable=False)
    short_code = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # New expiration column
