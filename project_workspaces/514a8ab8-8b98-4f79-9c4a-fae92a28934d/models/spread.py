from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship

from database import Base

class Spread(Base):
    __tablename__ = "spreads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text)
    positions = relationship("Position", back_populates="spread")


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)  # e.g., "Card 1", "The Past", "The Present"
    description = Column(Text)
    spread_id = Column(Integer, ForeignKey("spreads.id"))
    spread = relationship("Spread", back_populates="positions")