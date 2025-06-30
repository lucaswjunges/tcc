import sqlite3
import os

def init_database():
    # Criar o diretório database se não existir
    if not os.path.exists('database'):
        os.makedirs('database')
    
    # Conectar ao banco de dados (cria se não existir)
    conn = sqlite3.connect('database/tarot.db')
    cursor = conn.cursor()

    # Criar tabela para usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            is_authenticated BOOLEAN DEFAULT 0
        )
    ''')

    # Criar tabela para cartas do tarot
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            meaning_up TEXT,
            meaning_rev TEXT,
            image_path TEXT
        )
    ''')

    # Criar tabela para sessões de tiragem
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            end_time DATETIME,
            description TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Criar tabela para tiragens
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS draws (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            card_id INTEGER NOT NULL,
            position INTEGER NOT NULL,
            draw_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            reading TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions (id),
            FOREIGN KEY (card_id) REFERENCES cards (id)
        )
    ''')

    # Inserir algumas cartas de exemplo (arcana maior)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cards'")
    table_exists = cursor.fetchone()
    if table_exists is None:
        # Inserir algumas cartas para começar
        cursor.executemany("INSERT INTO cards (name, meaning_up, meaning_rev, image_path) VALUES (?, ?, ?, ?)", [
            ("The Fool", "Novidade, início, viagem, liberdade, risco, bondade, imaturo", 
             "Iniciativa, imaturo, bondade, risco, liberdade, viagem, novidade", "images/the_fool.jpg"),
            ("The Magician", "Poder, manifestação, criatividade, habilidades, recursos", 
             "Magia negra, manipulação, poder pessoal, habilidades ocultas", "images/the_magician.jpg"),
            ("The High Priestess", "Intuição, sabedoria, conselhos, segredos, misticismo", 
             "Segredos, intuição, sabedoria, conselhos espirituais, misticismo", "images/the_high_priestess.jpg"),
            ("The Empress", "Criatividade, natureza, fertilidade, abundância, beleza", 
             "Fertilidade, abundância, natureza, criatividade, beleza", "images/the_empress.jpg"),
            ("The Emperor", "Autoridade, estrutura, controle, liderança, poder", 
             "Controle excessivo, autoridade, estrutura, liderança, poder", "images/the_emperor.jpg")
        ])
    
    # Salvar as mudanças e fechar a conexão
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_database()