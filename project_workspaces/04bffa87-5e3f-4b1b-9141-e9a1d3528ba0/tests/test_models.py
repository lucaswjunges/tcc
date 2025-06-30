import pytest
from datetime import datetime
from app import db, Carta, Leitura, Oraculo, Cliente

def test_carta_model():
    # Testar criação de uma carta
    carta = Carta(
        nome="A Carteira Perdida",
        significado="Encontrar algo perdido ou recuperar um valor financeiro",
        numero=5,
        naipe="Cups",
        imagem_url="https://tarot.example.com/cart5.jpg"
    )
    assert isinstance(carta, Carta)
    assert carta.nome == "A Carteira Perdida"
    assert carta.significado == "Encontrar algo perdido ou recuperar um valor financeiro"
    assert carta.numero == 5
    assert carta.naipe == "Cups"
    assert carta.imagem_url == "https://tarot.example.com/cart5.jpg"
    
    # Testar campos obrigatórios
    with pytest.raises(Exception):
        Carta(nome="", significado="", numero=0, naipe="", imagem_url="")

def test_leitura_model():
    # Testar criação de uma leitura
    cliente = Cliente(nome="João Silva", email="joao@example.com")
    db.session.add(cliente)
    db.session.commit()
    
    oraculo = Oraculo(nome="Oracle Místico", descricao="Oracle com 78 cartas tradicionais")
    db.session.add(oraculo)
    db.session.commit()
    
    leitura = Leitura(
        cliente_id=cliente.id,
        oraculo_id=oraculo.id,
        data=datetime.now(),
        resultado="Carta 1, Carta 2, Carta 3"
    )
    
    assert isinstance(leitura, Leitura)
    assert leitura.cliente_id == cliente.id
    assert leitura.oraculo_id == oraculo.id
    assert isinstance(leitura.data, datetime)
    assert leitura.resultado == "Carta 1, Carta 2, Carta 3"

def test_oraculo_model():
    # Testar criação de um oráculo
    oraculo = Oraculo(
        nome="Oracle Místico",
        descricao="Oracle com 78 cartas tradicionais",
        preco=150.00
    )
    assert isinstance(oraculo, Oraculo)
    assert oraculo.nome == "Oracle Místico"
    assert oraculo.descricao == "Oracle com 78 cartas tradicionais"
    assert oraculo.preco == 150.00
    
    # Testar campos obrigatórios
    with pytest.raises(Exception):
        Oraculo(nome="", descricao="", preco=0.0)

def test_cliente_model():
    # Testar criação de um cliente
    cliente = Cliente(
        nome="João Silva",
        email="joao@example.com",
        telefone="(11) 99999-9999",
        endereco="Rua dos Testes, 123"
    )
    assert isinstance(cliente, Cliente)
    assert cliente.nome == "João Silva"
    assert cliente.email == "joao@example.com"
    assert cliente.telefone == "(11) 99999-9999"
    assert cliente.endereco == "Rua dos Testes, 123"

def test_relacionamentos():
    # Testar relacionamentos entre modelos
    cliente = Cliente(nome="João Silva", email="joao@example.com")
    db.session.add(cliente)
    db.session.flush()
    
    oraculo = Oraculo(nome="Oracle Místico", descricao="Oracle com 78 cartas tradicionais", preco=150.00)
    db.session.add(oraculo)
    db.session.flush()
    
    leitura = Leitura(
        cliente_id=cliente.id,
        oraculo_id=oraculo.id,
        data=datetime.now(),
        resultado="Carta 1, Carta 2, Carta 3"
    )
    db.session.add(leitura)
    db.session.flush()
    
    assert leitura.cliente.nome == "João Silva"
    assert leitura.oraculo.nome == "Oracle Místico"
    
    # Testar se a leitura está ligada ao cliente e oráculo
    assert leitura.cliente_id == cliente.id
    assert leitura.oraculo_id == oraculo.id

def test_timestamps():
    # Testar campos de timestamp
    carta = Carta(
        nome="A Carteira Perdida",
        significado="Encontrar algo perdido ou recuperar um valor financeiro",
        numero=5,
        naipe="Cups",
        imagem_url="https://tarot.example.com/cart5.jpg"
    )
    db.session.add(carta)
    db.session.flush()
    
    assert hasattr(carta, 'data_criacao')
    assert hasattr(carta, 'data_atualizacao')
    assert carta.data_criacao is not None
    assert carta.data_atualizacao is not None