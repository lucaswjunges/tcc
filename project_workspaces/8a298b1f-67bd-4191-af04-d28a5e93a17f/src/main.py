# src/main.py
# Este arquivo é o ponto de entrada da aplicação web de adivinhações de Tarô.
# Utiliza Flask para criar a interface web e processar as requisições.

from flask import Flask, render_template, request, redirect, url_for, flash
import random
import os
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

# Configuração do aplicativo Flask
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Chave secreta para segurança

# Configuração do login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Classes para gerenciar usuários (simulada para este exemplo)
class User(UserMixin):
    def __init__(self, id, username, email, is_authenticated=True):
        self.id = id
        self.username = username
        self.email = email
        self.is_authenticated = is_authenticated

# Dados de usuários fictícios (em um sistema real, isso viria de um banco de dados)
users = {
    'admin': User(1, 'admin', 'admin@example.com'),
    'user1': User(2, 'user1', 'user1@example.com')
}

# Sistema de autenticação simples
@login_manager.user_loader
def load_user(user_id):
    return users.get(int(user_id))

# Rota para a página inicial
@app.route('/')
def index():
    return render_template('index.html')

# Rota para o sistema de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Verificação simplificada (em um sistema real, usar hashing de senha)
        if username in users and users[username].email == 'admin@example.com' and password == 'admin123':
            user = users[username]
            login_user(user)
            return redirect(url_for('dashboard'))
        
        # Tentativa de login com usuário normal
        if username in users and users[username].email == 'user1@example.com' and password == 'user123':
            user = users[username]
            login_user(user)
            return redirect(url_for('dashboard'))
        
        # Senha incorreta
        flash('Usuário ou senha incorreta!')
        return render_template('login.html')
    
    return render_template('login.html')

# Rota para o sistema de logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Rota para o painel administrativo (apenas para usuário 'admin')
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.id != 1:  # ID do usuário admin é 1
        return redirect(url_for('index'))
    
    # Dados fictícios para o painel admin
    stats = {
        'visitas_totais': random.randint(1000, 5000),
        'pagamentos_realizados': random.randint(50, 200),
        'media_por_visita': round(random.uniform(15.5, 35.0), 2)
    }
    
    return render_template('dashboard.html', stats=stats)

# Rota para a página de oráculo
@app.route('/oracle', methods=['GET', 'POST'])
def oracle():
    if request.method == 'POST':
        question = request.form['question']
        session_id = request.form['session_id']
        
        # Processamento da leitura do tarô
        cards = draw_tarot_cards()
        interpretation = interpret_cards(cards)
        
        # Salvar dados da sessão (em um sistema real, salvar no banco de dados)
        save_session(session_id, question, cards, interpretation)
        
        return render_template('oracle_results.html', 
                             question=question,
                             cards=cards,
                             interpretation=interpretation)
    
    return render_template('oracle.html')

# Rota para a página de pagamento
@app.route('/payment/<session_id>', methods=['GET', 'POST'])
def payment(session_id):
    # Em um sistema real, verificar se a sessão existe e obter os dados
    session_data = get_session_data(session_id)
    
    if request.method == 'POST':
        # Processar pagamento (simulado)
        process_payment(session_id, request.form['payment_method'])
        return redirect(url_for('thank_you'))
    
    return render_template('payment.html', session_id=session_id, session_data=session_data)

# Rota para a página de agradecimento
@app.route('/thank-you')
def thank_you():
    return render_template('thank_you.html')

# Funções para simular o funcionamento do oráculo tarot
def draw_tarot_cards():
    # Lista de cartas do tarot (simplificada para este exemplo)
    tarot_deck = [
        {"name": "O Mago", "meaning": "Sabedoria e poder pessoal"},
        {"name": "A Forja", "meaning": "Transformação e crescimento"},
        {"name": "O Herói", "meaning": "Coragem e jornada"},
        {"name": "A Justiça", "meaning": "Equidade e verdade"},
        {"name": "A Rueda da Fortuna", "meaning": "Mudanças e destino"},
        {"name": "A Justiça", "meaning": "Equidade e verdade"},
        {"name": "O Enforcado", "meaning": "Pausa e reflexão"},
        {"name": "A Morte", "meaning": "Fim e renascimento"},
        {"name": "A Temperança", "meaning": "Flexibilidade e adaptação"},
        {"name": "O Diabo", "meaning": "Vínculos e liberdade"},
        {"name": "A Torre", "meaning": "Mudanças drásticas"},
        {"name": "O Arcano", "meaning": "Iluminação e visão"},
        {"name": "O Juíz", "meaning": "Consciência e destino"},
        {"name": "O Mundo", "meaning": "Completação e viagem"}
    ]
    
    # Embaralhar e selecionar 3 cartas
    random.shuffle(tarot_deck)
    return tarot_deck[:3]

def interpret_cards(cards):
    # Interpretações baseadas nas cartas sorteadas
    interpretations = []
    for card in cards:
        # Texto de interpretação mais detalhado
        if card["name"] == "O Mago":
            interpretations.append("Esta carta representa sabedoria, poder pessoal e criatividade. Você tem as ferramentas e o conhecimento para superar desafios. A chave está em aplicar sua mente aguçada e habilidades práticas.")
        elif card["name"] == "A Forja":
            interpretations.append("A Forja simboliza transformação e crescimento. Está passando por um processo de purificação e desenvolvimento. Aceite as dificuldades como oportunidades de crescimento.")
        elif card["name"] == "O Herói":
            interpretations.append("O Herói indica coragem, jornada e proteção. Você está em um estágio de defesa ou proteção de algo importante. Esta é uma oportunidade para liderar com sabedoria.")
        # Adicionar mais interpretações para todas as cartas...
        else:
            interpretations.append(f"A carta {card['name']} sugere que você está conectado(a) a {card['meaning']}. Esta é uma oportunidade para refletir sobre sua jornada e tomar decisões alinhadas com seu verdadeiro eu.")
    
    # Texto de interpretação geral
    general_interpretation = "Lembre-se que o tarô oferece orientação, mas o livre arbítrio é sempre seu. Use estas cartas como um guia para tomar decisões informadas."
    
    return "\n\n".join([general_interpretation] + interpretations)

# Funções para simular o armazenamento de dados (em um sistema real, usar banco de dados)
def save_session(session_id, question, cards, interpretation):
    # Simulação de armazenamento
    pass

def get_session_data(session_id):
    # Simulação de busca de dados da sessão
    return {
        "question": "Qual é o seu caminho agora?",
        "cards": [{"name": "O Mago"}, {"name": "A Forja"}, {"name": "O Herói"}],
        "interpretation": "Esta leitura sugere que você está em um período de desenvolvimento e transformação. Use sua sabedoria para navegar por mudanças importantes."
    }

def process_payment(session_id, payment_method):
    # Simulação de processamento de pagamento
    pass

if __name__ == '__main__':
    app.run(debug=True)