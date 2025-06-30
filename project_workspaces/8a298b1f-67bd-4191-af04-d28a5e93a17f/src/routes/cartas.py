from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
import random
import json
from datetime import datetime
from ..models import Carta, Leitura, CartaLeitura, User
from .. import db
from ..utils import get_card_by_name

cartas_bp = Blueprint('cartas', __name__, url_prefix='/cartas')

@cartas_bp.route('/')
@login_required
def index():
    return render_template('cartas/index.html')

@cartas_bp.route('/sobre')
@login_required
def sobre():
    return render_template('cartas/sobre.html')

@cartas_bp.route('/leitura')
@login_required
def leitura():
    return render_template('cartas/leitura.html')

@cartas_bp.route('/precos')
@login_required
def precos():
    return render_template('cartas/precos.html')

@cartas_bp.route('/agendar', methods=['GET', 'POST'])
@login_required
def agendar():
    if request.method == 'POST':
        data = request.form.get('data')
        hora = request.form.get('hora')
        tipo = request.form.get('tipo')
        mensagem = request.form.get('mensagem', '')

        # Validar data e hora
        if not data or not hora:
            flash('Por favor, selecione uma data e hora válidas.', 'error')
            return redirect(url_for('cartas.agendar'))

        # Verificar disponibilidade
        # Aqui seria implementada a lógica de verificação de disponibilidade
        # Para simplificar, vamos considerar que sempre está disponível

        # Criar leitura
        nova_leitura = Leitura(
            usuario_id=current_user.id,
            tipo=tipo,
            data=datetime.strptime(f"{data} {hora}", "%Y-%m-%d %H:%M"),
            mensagem=mensagem
        )
        db.session.add(nova_leitura)
        db.session.commit()

        flash('Leitura agendada com sucesso! Aguardo seu contato para confirmar.', 'success')
        return redirect(url_for('cartas.leitura'))

    return render_template('cartas/agendar.html')

@cartas_bp.route('/interpretar', methods=['POST'])
@login_required
def interpretar():
    if request.method == 'POST':
        cartas_selecionadas = request.form.getlist('cartas[]')
        pergunta = request.form.get('pergunta')

        # Selecionar 3 cartas aleatórias
        todas_cartas = Carta.query.all()
        cartas_aleatorias = random.sample(todas_cartas, min(3, len(todas_cartas)))
        
        resultado = []
        for carta in cartas_aleatorias:
            carta_interpretacao = {
                'nome': carta.nome,
                'descricao': carta.descricao,
                'imagem': carta.imagem_url,
                'posicao': resultado.index(carta) + 1
            }
            resultado.append(carta_interpretacao)

        return jsonify({
            'resultado': resultado,
            'pergunta': pergunta
        })

@cartas_bp.route('/historico')
@login_required
def historico():
    leituras = Leitura.query.filter_by(usuario_id=current_user.id).all()
    return render_template('cartas/historico.html', leituras=leituras)

@cartas_bp.route('/cartas')
@login_required
def listar_cartas():
    cartas = Carta.query.all()
    return jsonify({
        'cartas': [carta.to_dict() for carta in cartas]
    })