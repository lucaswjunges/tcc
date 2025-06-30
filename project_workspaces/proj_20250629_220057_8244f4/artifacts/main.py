from flask import Flask, render_template

app = Flask(__name__)

# Configurações
app.config['SECRET_KEY'] = 'secreta'

# Rotas
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/products')
def products():
    return render_template('products.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/product/<int:id>')
def product_detail(id):
    return render_template('product_detail.html', product_id=id)

if __name__ == '__main__':
    app.run(debug=True)
