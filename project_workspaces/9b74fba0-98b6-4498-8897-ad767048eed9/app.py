from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import datetime

app = Flask(__name__)

# Configuração do banco de dados
def get_db_connection():
    conn = sqlite3.connect('fofocas.db')
    conn.row_factory = sqlite3.Row
    return conn

# Criação da tabela se não existir
def init_db():
    conn = get_db_connection()
    conn.execute('''
    CREATE TABLE IF NOT EXISTS fofocas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT NOT NULL,
        fofoca TEXT NOT NULL,
        data TEXT NOT NULL,
        curtidas INTEGER DEFAULT 0
    )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    conn = get_db_connection()
    fofocas = conn.execute('SELECT * FROM fofocas ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('index.html', fofocas=fofocas)

@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar_fofoca():
    if request.method == 'POST':
        usuario = request.form['usuario']
        fofoca = request.form['fofoca']
        
        if not usuario or not fofoca:
            return redirect(url_for('index'))
        
        conn = get_db_connection()
        conn.execute('''
        INSERT INTO fofocas (usuario, fofoca, data, curtidas)
        VALUES (?, ?, ?, 0)
        ''', (usuario, fofoca, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        conn.close()
        
        return redirect(url_for('index'))
    
    return render_template('adicionar.html')

@app.route('/curtir/<int:id>')
def curtir_fofoca(id):
    conn = get_db_connection()
    conn.execute('UPDATE fofocas SET curtidas = curtidas + 1 WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/deletar/<int:id>')
def deletar_fofoca(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM fofocas WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)