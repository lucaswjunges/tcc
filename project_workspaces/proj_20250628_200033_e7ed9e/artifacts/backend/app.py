from flask import Flask, jsonify, request
import os
import sys
from datetime import datetime, timedelta

app = Flask(__name__)

# Configurações iniciais
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'supersecretkey')

# Mock de banco de dados
produtos = [
    {'id': 1, 'nome': 'Pod A', 'preco': 29.90, 'descricao': 'Pod de cigarro eletrônico'},
    {'id': 2, 'nome': 'Pod B', 'preco': 35.90, 'descricao': 'Pod premium'},
    {'id': 3, 'nome': 'Dispositivo C', 'preco': 89.90, 'descricao': 'Dispositivo de vapor'}
]

usuarios = [
    {'id': 1, 'username': 'user1', 'password': 'password1', 'email': 'user1@example.com'},
    {'id': 2, 'username': 'user2', 'password': 'password2', 'email': 'user2@example.com'}
]

pedidos = []

# Rota para produtos
@app.route('/api/produtos', methods=['GET'])
def get_produtos():
    return jsonify(produtos)

@app.route('/api/produtos/<int:id>', methods=['GET'])
def get_produto(id):
    produto = next((p for p in produtos if p['id'] == id), None)
    if produto:
        return jsonify(produto)
    return jsonify({'error': 'Produto não encontrado'}), 404

# Rota para usuários
@app.route('/api/usuarios', methods=['GET'])
def get_usuarios():
    return jsonify(usuarios)

@app.route('/api/usuarios', methods=['POST'])
def criar_usuario():
    novo_usuario = request.get_json()
    if not novo_usuario.get('username') or not novo_usuario.get('password'):
        return jsonify({'error': 'Username e senha obrigatórios'}), 400
    novo_id = max(u['id'] for u in usuarios) + 1 if usuarios else 1
    novo_usuario['id'] = novo_id
    usuarios.append(novo_usuario)
    return jsonify(novo_usuario), 201

# Rota para autenticação
@app.route('/api/login', methods=['POST'])
def login():
    dados = request.get_json()
    usuario = next((u for u in usuarios if u['username'] == dados.get('username') and u['password'] == dados.get('password')), None)
    if usuario:
        token = {'access_token': 'token_de_acesso_' + str(usuario['id'])}
        return jsonify({'token': token}), 200
    return jsonify({'error': 'Credenciais inválidas'}), 401

# Rota para carrinho
@app.route('/api/carrinho/<int:user_id>', methods=['GET', 'POST', 'PUT'])
def gerenciar_carrinho(user_id):
    carrinho = None
    for c in pedidos:  # Mock simples, em produção usar banco
        if c.get('user_id') == user_id and c.get('status') == 'carrinho':
            carrinho = c
            break
    
    if request.method == 'GET':
        if carrinho:
            return jsonify(carrinho)
        return jsonify({'error': 'Carrinho não encontrado'}), 404
    
    if request.method == 'POST':
        carrinho = {
            'id': (max(p['id'] for p in pedidos) if pedidos else 1) + 1,
            'user_id': user_id,
            'produtos': [],
            'total': 0,
            'status': 'carrinho',
            'criado_em': datetime.now(),
            'atualizado_em': datetime.now()
        }
        pedidos.append(carrinho)
        return jsonify(carrinho), 201
    
    if request.method == 'PUT':
        if not carrinho:
            return jsonify({'error': 'Carrinho não encontrado'}), 404
        dados = request.get_json()
        if 'produtos' in dados:
            carrinho['produtos'] = dados['produtos']
        carrinho['total'] = sum(p['preco'] for p in dados.get('produtos', [])) 
        carrinho['atualizado_em'] = datetime.now()
        return jsonify(carrinho)

# Rota para pedidos
@app.route('/api/pedidos', methods=['GET'])
def get_pedidos():
    return jsonify(pedidos)

@app.route('/api/pedidos/<int:id>', methods=['GET'])
def get_pedido(id):
    pedido = next((p for p in pedidos if p['id'] == id), None)
    if pedido:
        return jsonify(pedido)
    return jsonify({'error': 'Pedido não encontrado'}), 404

@app.route('/api/pedidos', methods=['POST'])
def criar_pedido():
    dados = request.get_json()
    if not dados.get('user_id') or not dados.get('produtos'):
        return jsonify({'error': 'user_id e produtos obrigatórios'}), 400
    
    carrinho = None
    for c in pedidos:
        if c.get('user_id') == dados['user_id'] and c.get('status') == 'carrinho':
            carrinho = c
            break
    
    if carrinho and carrinho['produtos'] != dados['produtos']:
        return jsonify({'error': 'Este carrinho já existe'}), 400
    
    novo_pedido = {
        'id': (max(p['id'] for p in pedidos) if pedidos else 1) + 1,
        'user_id': dados['user_id'],
        'produtos': dados.get('produtos', []),
        'total': dados.get('total', 0),
        'status': 'pendente',
        'criado_em': datetime.now(),
        'atualizado_em': datetime.now()
    }
    pedidos.append(novo_pedido)
    return jsonify(novo_pedido), 201

if __name__ == '__main__':
    app.run(debug=True)
