from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.database import Base


class URL(Base):
    __tablename__ = "urls"

    id = Column(String(12), primary_key=True, index=True)
    short_code = Column(String(12), unique=True, index=True, nullable=True)
    target_url = Column(String(2048), nullable=True)
    create_at = Column(DateTime, default=datetime.utcnow)
    click_count = Column(Integer, default=0, nullable=False)
