from sqlalchemy import Column, Integer, String
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    telegram_id = Column(String)
    verification_code = Column(String, nullable=True)

class ShortLink(Base):
    __tablename__ = "shortlinks"
    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(String)
    short_code = Column(String, unique=True, index=True)
    clicks = Column(Integer, default=0)
    owner_phone = Column(String)
