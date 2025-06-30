from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Configuração do banco de dados
BASE_DE_DADOS = 'sqlite:///loja_vapes.db'
engine = create_engine(BASE_DE_DADOS, echo=True)
Sessao = sessionmaker(bind=engine)

# Declaração da base para modelos
Base = declarative_base()

# Modelo de Produto
class Produto(Base):
    __tablename__ = 'produtos'

    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(String(500))
    preco = Column(Float, nullable=False)
    estoque = Column(Integer, default=0)
    categoria = Column(String(50))
    imagem_url = Column(String(200))
    pedidos = relationship('ItemPedido', back_populates='produto')

# Modelo de Pedido
class Pedido(Base):
    __tablename__ = 'pedidos'

    id = Column(Integer, primary_key=True)
    data_criacao = Column(DateTime, default=datetime.now)
    status = Column(String(20), default='Pendente')
    valor_total = Column(Float, default=0.0)
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
def inicializar_banco():
    Base.metadata.create_all(engine)

# Função para popular banco de dados inicialmente
def popular_banco_inicial():
    sessao = Sessao()

    # Produtos de exemplo
    produtos = [
        Produto(nome='Vape Premium Canábico', descricao='Vape de alta performance para óleos canábicos', preco=299.99, estoque=10, categoria='Vapes', imagem_url='/static/images/vape_premium.jpg'),
        Produto(nome='Atomizador Deluxe', descricao='Atomizador de última geração', preco=129.50, estoque=20, categoria='Atomizadores', imagem_url='/static/images/atomizador_deluxe.jpg'),
        Produto(nome='Kit Iniciante Canábico', descricao='Kit completo para iniciantes', preco=199.00, estoque=15, categoria='Kits', imagem_url='/static/images/kit_iniciante.jpg')
    ]

    sessao.add_all(produtos)
    sessao.commit()
    sessao.close()

# Inicialização do banco ao importar o módulo
inicializar_banco()
