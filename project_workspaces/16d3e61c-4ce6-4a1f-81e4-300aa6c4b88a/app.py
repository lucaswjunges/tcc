from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import random

app = Flask(__name__)

# Lista de fofocas (em memória, não persistente)
fofoocas = [
    {
        "conteudo": "Amanda e Carlos estão namorando há 3 meses e já planejam o casamento!",
        "autor": "FofocaFiel",
        "data": datetime.now().strftime("%d/%m/%Y"),
        "popularidade": random.randint(1, 5)
    },
    {
        "conteudo": "João e Mariana trocam mensagens até madrugada todos os dias!",
        "autor": "FofocaFiel",
        "data": datetime.now().strftime("%d/%m/%Y"),
        "popularidade": random.randint(1, 5)
    },
    {
        "conteudo": "A diretora da escola está namorando um funcionário há 6 meses!",
        "autor": "FofocaFiel",
        "data": datetime.now().strftime("%d/%m/%Y"),
        "popularidade": random.randint(1, 5)
    }
]

@app.route('/')
def index():
    return render_template('index.html', fofoocas=fofoocas)

@app.route('/nova_fofoca', methods=['GET', 'POST'])
def nova_fofoca():
    if request.method == 'POST':
        conteudo = request.form['conteudo']
        autor = request.form['autor']
        
        if not conteudo or not autor:
            return redirect(url_for('nova_fofoca'))
        
        nova_fofoca = {
            "conteudo": conteudo,
            "autor": autor,
            "data": datetime.now().strftime("%d/%m/%Y"),
            "popularidade": random.randint(1, 5)
        }
        
        fofoocas.append(nova_fofoca)
        return redirect(url_for('index'))
    
    return render_template('nova_fofoca.html')

if __name__ == '__main__':
    app.run(debug=True)