from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Configuração do banco de dados SQLite
BASE_DE_DADOS = 'sqlite:///loja.db'

# Criação do motor de banco de dados
engine = create_engine(BASE_DE_DADOS, echo=True)

# Criação da base declarativa para modelos
Base = declarative_base()

# Modelo de Produto
class Produto(Base):
    __tablename__ = 'produtos'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(String(255))
    preco = Column(Float, nullable=False)
    quantidade = Column(Integer, default=0)
    
    pedidos = relationship('ItemPedido', back_populates='produto')

# Modelo de Pedido
class Pedido(Base):
    __tablename__ = 'pedidos'
    
    id = Column(Integer, primary_key=True)
    data_criacao = Column(DateTime, default=datetime.now)
    status = Column(String(50), default='pendente')
    
    itens = relationship('ItemPedido', back_populates='pedido')

# Modelo de Item de Pedido (relacionamento entre Pedido e Produto)
class ItemPedido(Base):
    __tablename__ = 'itens_pedido'
    
    id = Column(Integer, primary_key=True)
    pedido_id = Column(Integer, ForeignKey('pedidos.id'))
    produto_id = Column(Integer, ForeignKey('produtos.id'))
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Float, nullable=False)
    
    pedido = relationship('Pedido', back_populates='itens')
    produto = relationship('Produto', back_populates='pedidos')

# Criação das tabelas no banco de dados
Base.metadata.create_all(engine)

# Criação da sessão do banco de dados
Sessao = sessionmaker(bind=engine)

def obter_sessao():
    return Sessao()
