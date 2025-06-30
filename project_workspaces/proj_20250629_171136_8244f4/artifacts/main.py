from flask import Flask, render_template

app = Flask(__name__)

# Rota principal
@app.route('/')
def index():
    return render_template('index.html', title='Vape Shop', description='Loja online de vapes e pods premium')

# Rota para produtos
@app.route('/products')
def products():
    return render_template('products.html', title='Produtos', description='Nossos produtos em destaque')

# Rota para carrinho
@app.route('/cart')
def cart():
    return render_template('cart.html', title='Carrinho', description='Produtos no seu carrinho')

# Rota de checkout
@app.route('/checkout')
def checkout():
    return render_template('checkout.html', title='Checkout', description='Finalize sua compra')

if __name__ == '__main__':
    app.run(debug=True)

# Estrutura básica do projeto
PROJECT_STRUCTURE = {
    "venv": "Ambiente virtual",
    "src": {
        "main.py": "Aplicação principal",
        "models": "Modelos de dados",
        "routes": "Rotas da aplicação",
        "templates": {
            "base.html": "Template base",
            "index.html": "Página inicial",
            "products.html": "Catálogo de produtos",
            "product.html": "Detalhes do produto",
            "cart.html": "Carrinho de compras",
            "checkout.html": "Checkout"
        }
    },
    "static": {
        "css": "Arquivos CSS",
        "js": "Arquivos JavaScript",
        "images": "Imagens"
    },
    "tests": "Testes da aplicação",
    "docs": "Documentação"
}