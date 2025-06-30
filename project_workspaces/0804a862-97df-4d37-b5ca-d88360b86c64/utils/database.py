import sqlite3

def create_database(db_name="tarot.db"):
    """Cria o banco de dados SQLite e as tabelas necessárias."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Tabela de usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL
        )
    """)

    # Tabela de leituras de tarô (spreads)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS spreads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            spread_type TEXT NOT NULL,
            cards TEXT NOT NULL,
            interpretation TEXT,
            date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Tabela de cartas de tarô
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            image_url TEXT
        )
    """)

    conn.commit()
    conn.close()

def add_user(username, password, email, db_name="tarot.db"):
    """Adiciona um novo usuário ao banco de dados."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO users (username, password, email) VALUES (?, ?, ?)
        """, (username, password, email))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Nome de usuário ou email já existe
    finally:
        conn.close()

def get_user(username, db_name="tarot.db"):
    """Retorna os dados do usuário com o nome de usuário fornecido."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM users WHERE username = ?
    """, (username,))
    user = cursor.fetchone()
    conn.close()
    return user


def add_spread(user_id, spread_type, cards, interpretation, db_name="tarot.db"):
    """Adiciona uma nova leitura de tarô ao banco de dados."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO spreads (user_id, spread_type, cards, interpretation) VALUES (?, ?, ?, ?)
    """, (user_id, spread_type, cards, interpretation))

    conn.commit()
    conn.close()

def get_spreads(user_id, db_name="tarot.db"):
    """Retorna todas as leituras de tarô para o usuário especificado."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM spreads WHERE user_id = ?
    """, (user_id,))

    spreads = cursor.fetchall()
    conn.close()
    return spreads