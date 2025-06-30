from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()

class Produto(Base):
    __tablename__ = 'produto'
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(Text)
    preco = Column(Float, nullable=False)
    categoria_id = Column(Integer, ForeignKey('categoria.id'))
    imagem = Column(String(255))
    data_cadastro = Column(DateTime, default=datetime.utcnow)

class Categoria(Base):
    __tablename__ = 'categoria'
    id = Column(Integer, primary_key=True)
    nome = Column(String(50), nullable=False)
    produtos = relationship('Produto', backref='categoria')

class Pedido(Base):
    __tablename__ = 'pedido'
    id = Column(Integer, primary_key=True)
    data = Column(DateTime, default=datetime.utcnow)
    total = Column(Float)
    status = Column(String(20), default='pendente')
    usuario_id = Column(Integer, ForeignKey('usuario.id'))

class ItemPedido(Base):
    __tablename__ = 'item_pedido'
    id = Column(Integer, primary_key=True)
    pedido_id = Column(Integer, ForeignKey('pedido.id'))
    produto_id = Column(Integer, ForeignKey('produto.id'))
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Float, nullable=False)

class Usuario(Base):
    __tablename__ = 'usuario'
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True)
    senha = Column(String(255), nullable=False)
    administrador = Column(Boolean, default=False)
    pedidos = relationship('Pedido', backref='usuario')

class Carrinho(Base):
    __tablename__ = 'carrinho'
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey('usuario.id'))
    itens = relationship('ItemCarrinho', backref='carrinho')

class ItemCarrinho(Base):
    __tablename__ = 'item_carrinho'
    id = Column(Integer, primary_key=True)
    carrinho_id = Column(Integer, ForeignKey('carrinho.id'))
    produto_id = Column(Integer, ForeignKey('produto.id'))
    quantidade = Column(Integer, nullable=False)

# Configuração do banco de dados
engine = create_engine('sqlite:///vapes.db')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()