from flask import Flask, render_template, request, redirect, url_for, flash
import random
import datetime
import os
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Configurações para upload de arquivos
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB

# Configuração do LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Dados simulados para usuários (em um sistema real, isso viria de um banco de dados)
users = {
    'admin': {'password': 'senha123', 'name': 'Administrador'},
    'user1': {'password': 'user123', 'name': 'Usuário 1'},
    'user2': {'password': 'user123', 'name': 'Usuário 2'}
}

# Dados simulados para cartas do tarot
cartas_tarot = [
    {"name": "A Roupa Nova", "meaning": "Nova oportunidade, mudança positiva"},
    {"name": "A Forja", "meaning": "Transformação, superação de obstáculos"},
    {"name": "O Enforcado", "meaning": "Restrição, necessidade de soltar algo"},
    {"name": "A Justiça", "meaning": "Equidade, justiça e consequências"},
    {"name": "O Herói", "meaning": "Coragem, liderança e proteção"},
    {"name": "A Roda da Fortuna", "meaning": "Mudanças na vida, sorte"},
    {"name": "A Justiça", "meaning": "Equidade, justiça e consequências"},
    {"name": "O Enforcado", "meaning": "Restrição, necessidade de soltar algo"},
    {"name": "A Roupa Nova", "meaning": "Nova oportunidade, mudança positiva"},
    {"name": "O Ermitão", "meaning": "Sagacidade, reflexão e isolamento"},
    {"name": "A Roda da Fortuna", "meaning": "Mudanças na vida, sorte"},
    {"name": "A Justiça", "meaning": "Equidade, justiça e consequências"},
    {"name": "O Enforcado", "meaning": "Restrição, necessidade de soltar algo"},
    {"name": "O Herói", "meaning": "Coragem, liderança e proteção"},
    {"name": "A Forja", "meaning": "Transformação, superação de obstáculos"}
]

# Sistema de pagamento simulado
pagamentos = []

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.route('/tarot')
def tarot():
    return render_template('tarot.html', cartas=cartas_tarot)

@app.route('/consultas')
@login_required
def consultas():
    return render_template('consultas.html')

@app.route('/agendar-consulta', methods=['GET', 'POST'])
@login_required
def agendar_consulta():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        data = request.form['data']
        mensagem = request.form['mensagem']
        
        # Simulação de agendamento bem-sucedido
        flash('Sua consulta foi agendada com sucesso!', 'success')
        return redirect(url_for('consultas'))
    
    return render_template('agendar_consulta.html')

@app.route('/pagamento', methods=['GET', 'POST'])
@login_required
def pagamento():
    if request.method == 'POST':
        cartao = request.form['cartao']
        validade = request.form['validade']
        cvv = request.form['cvv']
        
        # Simulação de pagamento bem-sucedido
        pagamentos.append({
            'user': current_user['name'],
            'data': datetime.datetime.now(),
            'valor': 100.00
        })
        flash('Pagamento realizado com sucesso!', 'success')
        return redirect(url_for('consultas'))
    
    return render_template('pagamento.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in users and users[username]['password'] == password:
            user = users[username]
            login_user(user)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha incorretos!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('index'))

@app.route('/contato')
def contato():
    return render_template('contato.html')

@app.route('/politica-privacidade')
def politica_privacidade():
    return render_template('politica_privacidade.html')

@app.route('/termos-uso')
def termos_uso():
    return render_template('termos_uso.html')

@app.route('/como-funciona')
def como_funciona():
    return render_template('como_funciona.html')

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)