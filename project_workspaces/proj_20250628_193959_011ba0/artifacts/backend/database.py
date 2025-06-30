from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Configuração do banco de dados SQLite
DATABASE_URL = 'sqlite:///ecommerce.db'
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()

# Modelo de Produto
class Produto(Base):
    __tablename__ = 'produtos'

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    descricao = Column(String)
    preco = Column(Float)
    quantidade = Column(Integer)

    pedidos = relationship('Pedido', back_populates='produtos')

# Modelo de Pedido
class Pedido(Base):
    __tablename__ = 'pedidos'

    id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, ForeignKey('produtos.id'))
    quantidade = Column(Integer)
    data_criacao = Column(DateTime, default=datetime.now)

    produtos = relationship('Produto', back_populates='pedidos')

# Criação das tabelas
Base.metadata.create_all(bind=engine)

# Função para obter sessão de banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
