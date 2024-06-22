from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship, Session

from .base import Base


class Client(Base):
    __tablename__ = 'client'
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True)
    name = Column(String)
    company = Column(String)
    sphere = Column(String)
    special_prompt = Column(String)

    messages = relationship('Message', back_populates='client')


def email_exists(session: Session, email: str) -> bool:
    return session.query(Client).filter_by(email=email).first() is not None