from flask import Flask, render_template, request, redirect, url_for, session
from config import app, db
from models import User, Reading, Card, Spread

# Rotas para gerenciamento de usuários (login, registro, etc.)
# ... (implementação em arquivos separados para melhor organização)

# Rota principal - Seleção de leitura
@app.route("/", methods=["GET", "POST"])
def index():
    spreads = Spread.query.all()
    return render_template("index.html", spreads=spreads)


# Rota para realizar uma leitura
@app.route("/reading/<int:spread_id>", methods=["GET", "POST"])
def reading(spread_id):
    spread = Spread.query.get_or_404(spread_id)
    if request.method == "POST":
        # Lógica para processar o pagamento (integração com gateway de pagamento)
        # ...

        # Gerar a leitura
        reading = Reading(spread_id=spread_id, user_id=session.get('user_id'))  # Associa a leitura ao usuário logado, se houver
        db.session.add(reading)
        db.session.flush()  # Para obter o ID da leitura gerado

        cards = Card.query.order_by(db.func.random()).limit(spread.card_count).all()
        for card in cards:
            reading.cards.append(card)  # Associa as cartas sorteadas à leitura

        db.session.commit()

        return redirect(url_for('reading_result', reading_id=reading.id))

    return render_template("reading.html", spread=spread)



# Rota para exibir o resultado da leitura
@app.route("/reading/result/<int:reading_id>")
def reading_result(reading_id):
    reading = Reading.query.get_or_404(reading_id)
    # Verificar se o usuário logado tem permissão para ver esta leitura
    if reading.user_id and reading.user_id != session.get('user_id'):
       return "Você não tem permissão para ver esta leitura.", 403
    return render_template("reading_result.html", reading=reading)


# ... (Outras rotas, como perfil do usuário, histórico de leituras, etc.)



if __name__ == "__main__":
    # db.create_all()  # Cria as tabelas do banco de dados (apenas na primeira execução)
    app.run(debug=True)