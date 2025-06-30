from flask import Flask, render_template

app = Flask(__name__)

# Configurações básicas
app.config['SECRET_KEY'] = 'secreta'

# Estrutura básica da aplicação
@app.route('/')
def home():
    return render_template('index.html', 
        titulo='Loja de Vapes', 
        produtos=['Pods', 'Vapes', 'Cessadores'], 
        mensagem_bem_vindo='Bem-vindo à nossa loja!'
    )

# Rota para produtos
@app.route('/produtos')
def produtos():
    return render_template('produtos.html', 
        titulo='Produtos', 
        categorias=['Pods', 'Vapes', 'Acessórios'], 
        categorias_selecionada='Todos'
    )

# Rota para carrinho
@app.route('/carrinho')
def carrinho():
    return render_template('carrinho.html', 
        titulo='Meu Carrinho'
    )

# Rota para checkout
@app.route('/checkout')
def checkout():
    return render_template('checkout.html', 
        titulo='Checkout'
    )

if __name__ == '__main__':
    app.run(debug=True)
