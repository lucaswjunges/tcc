from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from .models import Carta, Tiragem, CartaTiragem, Resultado
from . import db
import random
import json
from datetime import datetime
import uuid

resultado_bp = Blueprint('resultado', __name__)

@resultado_bp.route('/resultado/<tiragem_id>', methods=['GET', 'POST'])
@login_required
def resultado(tiragem_id):
    # Verifica se a tiragem existe
    tiragem = Tiragem.query.get(tiragem_id)
    if not tiragem:
        flash('Tiragem não encontrada.', 'error')
        return redirect(url_for('tirar.tirar'))

    # Verifica se o usuário atual é o dono da tiragem
    if tiragem.usuario_id != current_user.id:
        flash('Você não tem permissão para acessar esta tiragem.', 'error')
        return redirect(url_for('tirar.tirar'))

    # Se ainda não foi gerado o resultado, gera um
    if not tiragem.resultado_id:
        # Seleciona as cartas para o resultado
        cartas_selecionadas = selecionar_cartas_para_resultado(tiragem.tipo_tiragem)
        
        # Salva as cartas na tiragem
        for carta in cartas_selecionadas:
            nova_associacao = CartaTiragem(
                tiragem_id=tiragem.id,
                carta_id=carta.id,
                posicao=carta.posicao,
                interpretacao=gerar_interpretacao(carta)
            )
            db.session.add(nova_associacao)
        
        # Cria o resultado
        novo_resultado = Resultado(
            tiragem_id=tiragem.id,
            interpretacao_geral=gerar_interpretacao_geral(cartas_selecionadas),
            data=datetime.utcnow()
        )
        db.session.add(novo_resultado)
        tiragem.resultado_id = novo_resultado.id
        db.session.commit()
    
    # Obtém todas as cartas associadas à tiragem
    cartas_associadas = CartaTiragem.query.filter_by(tiragem_id=tiragem.id).all()
    
    # Obtém o resultado geral
    resultado_geral = Resultado.query.get(tiragem.resultado_id)
    
    return render_template('resultado.html', 
                          cartas=cartas_associadas, 
                          resultado_geral=resultado_geral)

def selecionar_cartas_para_resultado(tipo_tiragem):
    # Seleciona um número aleatório de cartas com base no tipo de tiragem
    num_cartas = random.randint(3, 6) if tipo_tiragem == 'aleatoria' else tipo_tiragem
    
    # Seleciona as cartas do baralho principal
    cartas = Carta.query.filter_by(ativa=True).order_by(func.random()).limit(num_cartas).all()
    
    # Define as posições para as cartas selecionadas
    for i, carta in enumerate(cartas):
        carta.posicao = i + 1
    
    return cartas

def gerar_interpretacao(carta):
    # Carrega os dados das interpretações para esta carta
    with open('app/static/data/cartas.json', 'r') as f:
        dados_cartas = json.load(f)
    
    if str(carta.id) not in dados_cartas:
        return "Carta sem interpretação disponível."
    
    dados = dados_cartas[str(carta.id)]
    
    # Seleciona uma interpretação aleatória
    if 'interpretacoes' in dados and isinstance(dados['interpretacoes'], list) and len(dados['interpretacoes']) > 0:
        return random.choice(dados['interpretacoes'])
    return dados.get('interpretacao_geral', "Carta sem interpretação disponível.")

def gerar_interpretacao_geral(cartas):
    # Combina as interpretações individuais para criar uma interpretação geral
    interpretacoes = []
    for carta in cartas:
        with open('app/static/data/cartas.json', 'r') as f:
            dados_cartas = json.load(f)
        
        if str(carta.carta_id) in dados_cartas:
            dados = dados_cartas[str(carta.carta_id)]
            if 'interpretacoes' in dados and isinstance(dados['interpretacoes'], list) and len(dados['interpretacoes']) > 0:
                interpretacoes.append(random.choice(dados['interpretacoes']))
            else:
                interpretacoes.append(dados.get('interpretacao_geral', "Carta sem interpretação disponível."))
        else:
            interpretacoes.append("Carta sem interpretação disponível.")
    
    # Cria uma interpretação geral baseada nas cartas
    texto = "A tiragem que você realizou apresenta as seguintes cartas:\n\n"
    for i, carta in enumerate(cartas):
        texto += f"{carta.posicao}ª Carta: {carta.interpretacao}\n"
    
    texto += "\nConsiderando o conjunto de cartas, podemos destacar alguns pontos importantes:\n"
    for i, interpretacao in enumerate(interpretacoes):
        if i < len(interpretacoes) - 1:
            texto += f" - {interpretacao}\n"
    
    texto += "\nLembre-se que o tarot é uma ferramenta de reflexão e autoconhecimento. "
    "As cartas oferecem orientações, mas a interpretação final é sua. "
    "Use esta informação para tomar decisões alinhadas com seu bem-estar e propósito de vida."
    
    return texto