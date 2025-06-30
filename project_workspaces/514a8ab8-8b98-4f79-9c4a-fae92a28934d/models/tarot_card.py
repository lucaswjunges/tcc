from sqlalchemy import Column, Integer, String, Text
from database import Base

class TarotCard(Base):
    __tablename__ = "tarot_cards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    arcana = Column(String(50), nullable=False)  # Major or Minor
    suit = Column(String(50), nullable=True)  # Cups, Pentacles, Swords, Wands, or None for Major Arcana
    rank = Column(Integer, nullable=True) # Number for Minor Arcana, None for Major Arcana
    keywords = Column(String(255), nullable=False)
    meaning_upright = Column(Text, nullable=False)
    meaning_reversed = Column(Text, nullable=False)
    image_url = Column(String(255), nullable=True)


    def __repr__(self):
        return f"<TarotCard(name='{self.name}', arcana='{self.arcana}')>"