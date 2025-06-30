import sqlite3
import os
from datetime import datetime

def init_database():
    # Conectar ao banco de dados (criar se não existir)
    conn = sqlite3.connect('tarot_cards.db')
    cursor = conn.cursor()
    
    # Criar tabela de usuários
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        role TEXT DEFAULT 'user'
    )
    ''')
    
    # Criar tabela de cartas tarot
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        image_path TEXT NOT NULL,
        upright_meaning TEXT NOT NULL,
        reversed_meaning TEXT NOT NULL
    )
    ''')
    
    # Criar tabela de leituras
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        end_time DATETIME,
        status TEXT DEFAULT 'completed',
        price REAL DEFAULT 0.0,
        consultation_type TEXT DEFAULT 'standard',
        duration INTEGER DEFAULT 10,  -- em minutos
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Criar tabela de cartas em leituras
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reading_cards (
        reading_id INTEGER NOT NULL,
        card_id INTEGER NOT NULL,
        position TEXT NOT NULL,
        upright BOOLEAN NOT NULL,
        interpretation TEXT,
        FOREIGN KEY (reading_id) REFERENCES readings (id),
        FOREIGN KEY (card_id) REFERENCES cards (id)
    )
    ''')
    
    # Criar tabela de pagamentos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reading_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        payment_method TEXT NOT NULL,
        transaction_id TEXT,
        status TEXT DEFAULT 'pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (reading_id) REFERENCES readings (id)
    )
    ''')
    
    # Criar tabela de feedbacks
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS feedbacks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reading_id INTEGER NOT NULL,
        rating INTEGER DEFAULT 0,
        comment TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (reading_id) REFERENCES readings (id)
    )
    ''')
    
    # Criar tabela de consultas agendadas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date_time DATETIME NOT NULL,
        status TEXT DEFAULT 'pending',
        duration INTEGER DEFAULT 10,
        consultation_type TEXT DEFAULT 'standard',
        price REAL DEFAULT 0.0,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Criar tabela de mensagens (chat)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER NOT NULL,
        sender_id INTEGER NOT NULL,
        receiver_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        type TEXT DEFAULT 'text',
        FOREIGN KEY (conversation_id) REFERENCES conversations (id),
        FOREIGN KEY (sender_id) REFERENCES users (id),
        FOREIGN KEY (receiver_id) REFERENCES users (id)
    )
    ''')
    
    # Criar tabela de conversações
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Criar tabela de notificações
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        read BOOLEAN DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Criar tabela de configurações
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        language TEXT DEFAULT 'pt-BR',
        currency TEXT DEFAULT 'BRL',
        payment_methods TEXT,
        theme TEXT DEFAULT 'light',
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Criar tabela de tarifas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tariffs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        duration INTEGER DEFAULT 10,
        consultation_type TEXT DEFAULT 'standard',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Criar tabela de FAQs
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS faqs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        category TEXT DEFAULT 'general'
    )
    ''')
    
    # Criar tabela de artigos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        author_id INTEGER NOT NULL,
        published_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        category TEXT,
        featured BOOLEAN DEFAULT 0,
        FOREIGN KEY (author_id) REFERENCES users (id)
    )
    ''')
    
    # Criar tabela de eventos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        date_time DATETIME NOT NULL,
        location TEXT,
        capacity INTEGER DEFAULT 10,
        price REAL DEFAULT 0.0,
        created_by INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES users (id)
    )
    ''')
    
    # Criar tabela de avaliações
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        rating INTEGER DEFAULT 0,
        comment TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        approved BOOLEAN DEFAULT 0
    )
    ''')
    
    # Criar tabela de logs
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT NOT NULL,
        target TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        ip_address TEXT
    )
    ''')
    
    # Criar tabela de referências
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS references (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        reference TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        approved BOOLEAN DEFAULT 0
    )
    ''')
    
    # Criar tabela de bloqueios
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        blocked_user_id INTEGER NOT NULL,
        reason TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        expires_at DATETIME
    )
    ''')
    
    # Criar tabela de relatórios
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reported_user_id INTEGER NOT NULL,
        reporter_id INTEGER NOT NULL,
        reason TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        resolved BOOLEAN DEFAULT 0
    )
    ''')
    
    # Criar tabela de estatísticas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS statistics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        metric_name TEXT NOT NULL,
        value REAL,
        date TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Criar tabela de backup
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS backups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Commit e fechar conexão
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_database()
    print("Database initialized successfully.")