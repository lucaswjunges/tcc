from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from sqlalchemy.orm import relationship

from .base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    profile = relationship("Profile", back_populates="user", uselist=False)
    readings = relationship("Reading", back_populates="user")


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True) # Foreign key linking to User.id
    name = Column(String, nullable=True)
    birthdate = Column(DateTime, nullable=True)
    credits = Column(Float, default=0.0)
    user = relationship("User", back_populates="profile")