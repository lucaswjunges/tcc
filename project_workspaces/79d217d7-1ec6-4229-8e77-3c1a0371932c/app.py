from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import random
import os
from datetime import datetime
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Configuração do SQLite
DATABASE = 'tarot_app.db'

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.before_first_request
def initialize():
    init_db()

# Configuração do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if user:
        return User(user['id'], user['username'], user['password_hash'])
    return None

class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

# Sistema de cartas do tarot
cartas_tarot = [
    {"name": "A", "meaning": "A força..."},
    {"name": "2", "meaning": "O processo..."},
    # ... (adicionar todas as 78 cartas aqui)
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        if user and check_password_hash(user['password_hash'], password):
            user_obj = User(user['id'], user['username'], user['password_hash'])
            login_user(user_obj)
            return redirect(url_for('tarot'))
        else:
            flash('Usuário ou senha inválidos')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        existing_user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        if existing_user:
            flash('Usuário já existe')
            return render_template('register.html')
        
        db.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                  (username, generate_password_hash(password)))
        db.commit()
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/tarot', methods=['GET', 'POST'])
@login_required
def tarot():
    if request.method == 'POST':
        pergunta = request.form['pergunta']
        num_cartas = int(request.form['num_cartas'])
        
        # Simulação de tirar cartas
        cartas_selecionadas = random.sample(cartas_tarot, num_cartas)
        
        # Salvar consulta no banco de dados
        db = get_db()
        db.execute('INSERT INTO consultas (user_id, pergunta, num_cartas) VALUES (?, ?, ?)',
                  (current_user.id, pergunta, num_cartas))
        db.commit()
        
        return render_template('resultado.html', cartas=cartas_selecionadas, pergunta=pergunta)
    
    return render_template('tarot.html')

@app.route('/consultas')
@login_required
def consultas():
    db = get_db()
    consultas = db.execute('SELECT * FROM consultas WHERE user_id = ? ORDER BY data DESC', (current_user.id,)).fetchall()
    return render_template('consultas.html', consultas=consultas)

@app.route('/tarot/<int:consulta_id>')
@login_required
def detalhes_consulta(consulta_id):
    db = get_db()
    consulta = db.execute('SELECT * FROM consultas WHERE id = ?', (consulta_id,)).fetchone()
    if not consulta:
        return redirect(url_for('tarot'))
    
    # Simulação de interpretação das cartas
    cartas_interpretacao = []
    for i, carta in enumerate(cartas_tarot[:int(consulta['num_cartas'])]):
        if i < 3:  # Primeiras 3 cartas
            interpretacao = f"{carta['name']}: {carta['meaning']}"
        elif i < 6:  # Próximas 3 cartas
            interpretacao = f"{carta['name']}: {carta['meaning']}"
        else:
            interpretacao = f"{carta['name']}: {carta['meaning']}"
        cartas_interpretacao.append({"carta": carta, "interpretacao": interpretacao})
    
    return render_template('detalhes.html', consulta=consulta, cartas=cartas_interpretacao)

if __name__ == '__main__':
    app.run(debug=True)