from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import Carta, Leitura, Usuario, Oraculo
from . import db
import random
import datetime
import json
from datetime import timedelta

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def home():
    return render_template('home.html')

@home_bp.route('/tarot')
@login_required
def tarot():
    # Selecionar 3 cartas aleatórias para o spread inicial
    cartas = Carta.query.all()
    spread_inicial = random.sample(cartas, 3)
    
    return render_template('tarot.html', spread_inicial=spread_inicial)

@home_bp.route('/interpretar', methods=['POST'])
@login_required
def interpretar():
    if request.method == 'POST':
        cartas_selecionadas = request.form.getlist('cartas')
        tipo_leitura = request.form.get('tipo_leitura')
        duracao = request.form.get('duracao')
        
        # Calcular data de término baseada na duração selecionada
        if duracao == '24h':
            data_fim = datetime.datetime.now() + timedelta(hours=24)
        elif duracao == '72h':
            data_fim = datetime.datetime.now() + timedelta(hours=72)
        else:  # '30d'
            data_fim = datetime.datetime.now() + timedelta(days=30)
        
        # Criar nova leitura
        nova_leitura = Leitura(
            usuario_id=current_user.id,
            tipo=tipo_leitura,
            data_inicio=datetime.datetime.now(),
            data_fim=data_fim,
            status='Em andamento'
        )
        
        db.session.add(nova_leitura)
        db.session.commit()
        
        # Salvar as cartas selecionadas no banco de dados
        for carta_id in cartas_selecionadas:
            carta = Carta.query.get(int(carta_id))
            if carta:
                nova_leitura.cartas.append(carta)
        
        db.session.commit()
        
        # Redirecionar para a página de interpretação
        return redirect(url_for('leitura_bp.detalhes', leitura_id=nova_leitura.id))
    
    return redirect(url_for('home_bp.home'))

@home_bp.route('/tarot/<int:leitura_id>')
@login_required
def mostrar_interpretacao(leitura_id):
    leitura = Leitura.query.get_or_404(leitura_id)
    cartas = leitura.cartas
    
    # Gerar interpretação baseada nas cartas selecionadas
    interpretacoes = []
    for carta in cartas:
        # Pegar dados da carta do arquivo JSON
        with open('app/static/cartas.json', 'r') as f:
            dados_cartas = json.load(f)
        
        carta_data = next((c for c in dados_cartas if c['name'] == carta.nome), None)
        
        if carta_data:
            interpretacao = f"{carta_data['name']} está te mostrando que {carta_data['interpretation']}"
            interpretacoes.append(interpretacao)
    
    return render_template('interpretacao.html', 
                          leitura=leitura, 
                          interpretacoes=interpretacoes)

@home_bp.route('/tarot/<int:leitura_id>/comprar')
@login_required
def comprar_leitura(leitura_id):
    leitura = Leitura.query.get_or_404(leitura_id)
    preco = 0
    
    if leitura.tipo == 'simples':
        preco = 49.90
    elif leitura.tipo == 'detalhada':
        preco = 99.90
    elif leitura.tipo == 'premium':
        preco = 199.90
    
    return render_template('comprar.html', leitura=leitura, preco=preco)

@home_bp.route('/tarot/<int:leitura_id>/pagar')
@login_required
def pagar(leitura_id):
    leitura = Leitura.query.get_or_404(leitura_id)
    # Processar pagamento (integraria com gateway de pagamento real)
    leitura.status = 'Finalizada'
    leitura.data_pagamento = datetime.datetime.now()
    db.session.commit()
    
    return redirect(url_for('leitura_bp.detalhes', leitura_id=leitura.id))

@home_bp.route('/tarot/<int:leitura_id>/salvar')
@login_required
def salvar_leitura(leitura_id):
    leitura = Leitura.query.get_or_404(leitura_id)
    leitura.salvada = not leitura.salvada
    db.session.commit()
    
    return redirect(url_for('leitura_bp.detalhes', leitura_id=leitura.id))

@home_bp.route('/tarot/<int:leitura_id>/compartilhar')
@login_required
def compartilhar(leitura_id):
    leitura = Leitura.query.get_or_404(leitura_id)
    # Implementar compartilhamento (integraria com APIs de compartilhamento)
    return redirect(url_for('leitura_bp.detalhes', leitura_id=leitura.id))

@home_bp.route('/tarot/<int:leitura_id>/favoritos')
@login_required
def favoritos(leitura_id):
    leitura = Leitura.query.get_or_404(leitura_id)
    if leitura.salvada:
        leitura.salvada = False
    else:
        leitura.salvada = True
    db.session.commit()
    
    return redirect(url_for('leitura_bp.detalhes', leitura_id=leitura.id))

@home_bp.route('/tarot/<int:leitura_id>/historico')
@login_required
def historico(leitura_id):
    leituras = Leitura.query.filter_by(usuario_id=current_user.id).all()
    return render_template('historico.html', leituras=leituras)

@home_bp.route('/tarot/<int:leitura_id>/cancelar')
@login_required
def cancelar(leitura_id):
    leitura = Leitura.query.get_or_404(leitura_id)
    if leitura.status == 'Em andamento':
        leitura.status = 'Cancelada'
        db.session.commit()
        flash('Leitura cancelada com sucesso!')
    return redirect(url_for('leitura_bp.detalhes', leitura_id=leitura.id))

@home_bp.route('/tarot/<int:leitura_id>/reagendar')
@login_required
def reagendar(leitura_id):
    leitura = Leitura.query.get_or_404(leitura_id)
    if leitura.status == 'Finalizada':
        # Calcular nova data de término
        duracao = request.form.get('duracao')
        if duracao == '24h':
            data_fim = datetime.datetime.now() + timedelta(hours=24)
        elif duracao == '72h':
            data_fim = datetime.datetime.now() + timedelta(hours=72)
        else:  # '30d'
            data_fim = datetime.datetime.now() + timedelta(days=30)
        
        leitura.data_inicio = datetime.datetime.now()
        leitura.data_fim = data_fim
        leitura.status = 'Em andamento'
        db.session.commit()
        flash('Leitura reagendada com sucesso!')
    
    return redirect(url_for('leitura_bp.detalhes', leitura_id=leitura.id))

@home_bp.route('/tarot/<int:leitura_id>/comentarios')
@login_required
def comentarios(leitura_id):
    leitura = Leitura.query.get_or_404(leitura_id)
    comentarios = Comentario.query.filter_by(leitura_id=leitura_id).all()
    return render_template('comentarios.html', leitura=leitura, comentarios=comentarios)

@home_bp.route('/tarot/<int:leitura_id>/comentar', methods=['POST'])
@login_required
def comentar(leitura_id):
    if request.method == 'POST':
        texto = request.form.get('texto')
        leitura = Leitura.query.get_or_404(leitura_id)
        novo_comentario = Comentario(
            usuario_id=current_user.id,
            leitura_id=leitura_id,
            texto=texto,
            data=datetime.datetime.now()
        )
        db.session.add(novo_comentario)
        db.session.commit()
        flash('Comentário enviado com sucesso!')
    
    return redirect(url_for('leitura_bp.detalhes', leitura_id=leitura.id))