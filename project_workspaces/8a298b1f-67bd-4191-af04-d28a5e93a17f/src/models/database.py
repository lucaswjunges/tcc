# src/models/database.py

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import os

# Configurar o caminho do banco de dados
BASE_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

# Criar engine SQLite
engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)

# Criar base declarativa
Base = declarative_base()

# Classe de fábrica para sessões de banco de dados
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Modelo para usuários (leitores e clientes)
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(20), nullable=False)  # 'reader' ou 'client'
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    readings = relationship('Reading', back_populates='user')
    reviews = relationship('Review', back_populates='user')

# Modelo para leituras de tarô
class Reading(Base):
    __tablename__ = 'readings'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    type = Column(String(50), nullable=False)  # 'single', 'relationship', 'career', etc.
    price = Column(Float, default=0.0)
    duration = Column(Integer, default=30)  # em minutos
    status = Column(String(20), default='pending')  # 'pending', 'completed', 'cancelled'
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    notes = Column(Text, nullable=True)
    
    # Relacionamentos
    user = relationship('User', back_populates='readings')
    cards = relationship('Card', secondary='readings_cards', back_populates='readings')
    review = relationship('Review', uselist=False, back_populates='reading')

# Tabela de junção para muitos para muitos entre Leitura e Carta
readings_cards_association = Table(
    'readings_cards', Base.metadata,
    Column('reading_id', Integer, ForeignKey('readings.id')),
    Column('card_id', Integer, ForeignKey('cards.id'))
)

# Modelo para cartas do tarô
class Card(Base):
    __tablename__ = 'cards'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    position = Column(Integer, nullable=True)  # Posição específica na tiragem
    image_url = Column(String(200), nullable=True)
    
    # Relacionamentos
    readings = relationship('Reading', secondary=readings_cards_association, back_populates='cards')

# Modelo para avaliações
class Review(Base):
    __tablename__ = 'reviews'
    
    id = Column(Integer, primary_key=True)
    reading_id = Column(Integer, ForeignKey('readings.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    rating = Column(Integer, default=5)  # De 1 a 5
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    reading = relationship('Reading', back_populates='review')
    user = relationship('User', back_populates='reviews')

# Modelo para pagamento
class Payment(Base):
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True)
    reading_id = Column(Integer, ForeignKey('readings.id'), nullable=False)
    amount = Column(Float, default=0.0)
    payment_method = Column(String(50), nullable=False)
    status = Column(String(20), default='pending')  # 'pending', 'completed', 'failed'
    transaction_id = Column(String(100), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamento
    reading = relationship('Reading')

# Modelo para feedbacks
class Feedback(Base):
    __tablename__ = 'feedbacks'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    message = Column(Text, nullable=False)
    is_anonymous = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamento
    user = relationship('User')

# Modelo para leitores (especialização de User)
class ReaderProfile(Base):
    __tablename__ = 'reader_profiles'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    bio = Column(Text, nullable=True)
    hourly_rate = Column(Float, default=0.0)
    languages = Column(String(100), nullable=True)
    experience_years = Column(Integer, default=0)
    is_available = Column(Boolean, default=True)
    
    # Relacionamento
    user = relationship('User', uselist=False)

# Modelo para newsletter
class Newsletter(Base):
    __tablename__ = 'newsletter'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(100), unique=True, nullable=False)
    subscribed_at = Column(DateTime, default=datetime.utcnow)
    is_confirmed = Column(Boolean, default=False)

# Criação das tabelas no banco de dados
def create_database():
    Base.metadata.create_all(bind=engine)

# Inicializar o banco de dados
if not os.path.exists(DB_PATH):
    create_database()