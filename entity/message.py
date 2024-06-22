from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey('client.id'))
    sender = Column(String)
    mess_text = Column(String)
    datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    client = relationship('Client', back_populates='messages')
