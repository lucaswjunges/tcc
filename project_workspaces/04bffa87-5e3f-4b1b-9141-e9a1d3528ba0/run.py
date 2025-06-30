from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import random

# Configuração inicial
app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

# Configuração do banco de dados
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'tarot.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Definição dos modelos de dados
class Carta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    numero = db.Column(db.Integer, unique=True)
    sentido_positivo = db.Column(db.Text)
    sentido_negativo = db.Column(db.Text)
    imagem_url = db.Column(db.String(200))

class Tiragem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer)  # Se tivermos autenticação, podemos usar
    cartas = db.relationship('CartaTirada', backref='tiragem', lazy=True)

class CartaTirada(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    carta_id = db.Column(db.Integer, db.ForeignKey('carta.id'), nullable=False)
    posicao = db.Column(db.Integer, nullable=False)  # 1, 2, 3, ... na tiragem
    tiragem_id = db.Column(db.Integer, db.ForeignKey('tiragem.id'), nullable=False)

# Criar as tabelas no banco de dados
with app.app_context():
    db.create_all()

# Rotas
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.route('/como_funciona')
def como_funciona():
    return render_template('como_funciona.html')

@app.route('/tirar_carta')
def tirar_carta():
    return render_template('tirar_carta.html')

@app.route('/tirar_carta', methods=['POST'])
def realizar_tiragem():
    # Lógica para realizar a tiragem e armazenar no banco de dados
    # Vamos supor que o usuário selecionou 3 cartas, então vamos pegar 3 cartas aleatórias
    # Primeiro, vamos pegar todas as cartas do tarô (supondo que temos um baralho completo)
    cartas = Carta.query.all()
    num_cartas = 3  # Vamos fixar 3 cartas para simplificar
    cartas_tiradas = random.sample(cartas, num_cartas)
    
    # Armazenar no banco de dados
    nova_tiragem = Tiragem(usuario_id=None)  # Sem autenticação, então None
    db.session.add(nova_tiragem)
    db.session.flush()  # Para obter o id da tiragem
    
    # Adicionar cada carta tirada
    for i, carta in enumerate(cartas_tiradas):
        nova_carta_tirada = CartaTirada(carta_id=carta.id, posicao=i+1, tiragem_id=nova_tiragem.id)
        db.session.add(nova_carta_tirada)
    
    db.session.commit()
    
    # Redirecionar para a página de resultado, passando o id da tiragem
    flash('Sua tiragem foi realizada com sucesso!')
    return redirect(url_for('ver_resultado', tiragem_id=nova_tiragem.id))

@app.route('/resultado/<tiragem_id>')
def ver_resultado(tiragem_id):
    tiragem = Tiragem.query.get(tiragem_id)
    cartas_tiradas = CartaTirada.query.filter_by(tiragem_id=tiragem_id).all()
    # Vamos mapear as cartas pelo id
    cartas = [Carta.query.get(ct.carta_id) for ct in cartas_tiradas]
    return render_template('resultado.html', cartas=cartas)

if __name__ == '__main__':
    app.run(debug=True)