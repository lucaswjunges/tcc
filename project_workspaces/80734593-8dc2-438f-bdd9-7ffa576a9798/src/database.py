import sqlite3
from datetime import datetime
import os
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_name: str = 'tarot_app.db'):
        self.db_name = db_name
        self.conn = None
        self.create_tables()

    def connect(self):
        """Conecta ao banco de dados SQLite"""
        self.conn = sqlite3.connect(self.db_name)
        return self.conn

    def create_tables(self):
        """Cria as tabelas necessárias no banco de dados"""
        with self.connect() as conn:
            # Tabela para usuários
            conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                balance REAL DEFAULT 0.0,
                is_premium BOOLEAN DEFAULT 0
            )
            ''')

            # Tabela para cartas de tarô
            conn.execute('''
            CREATE TABLE IF NOT EXISTS tarot_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                type TEXT NOT NULL,
                position INTEGER NOT NULL,
                image_path TEXT,
                is_reversed BOOLEAN DEFAULT 0
            )
            ''')

            # Tabela para leituras
            conn.execute('''
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date DATETIME DEFAULT CURRENT_TIMESTAMP,
                num_cards INTEGER NOT NULL,
                cost REAL NOT NULL,
                is_confirmed BOOLEAN DEFAULT 0,
                session_id TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            ''')

            # Tabela para cartas em leituras
            conn.execute('''
            CREATE TABLE IF NOT EXISTS reading_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reading_id INTEGER NOT NULL,
                card_id INTEGER NOT NULL,
                position INTEGER NOT NULL,
                interpretation TEXT,
                FOREIGN KEY (reading_id) REFERENCES readings (id),
                FOREIGN KEY (card_id) REFERENCES tarot_cards (id)
            )
            ''')

            # Tabela para feedbacks
            conn.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reading_id INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                comment TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (reading_id) REFERENCES readings (id)
            )
            ''')

            # Tabela para transações
            conn.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT NOT NULL,
                transaction_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            ''')

    def execute_query(self, query: str, params: tuple = (), fetch: bool = False) -> Optional[List[Dict]]:
        """Executa uma consulta SQL e retorna os resultados se necessário"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                if query.lower().startswith('select'):
                    columns = [col[0] for col in cursor.description]
                    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                    return results
                
                conn.commit()
                return None
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None

    def get_all_readings(self) -> List[Dict]:
        """Recupera todas as leituras realizadas"""
        query = """
        SELECT 
            r.id,
            u.name,
            r.date,
            r.num_cards,
            tc.name AS tarot_type,
            r.cost,
            r.is_confirmed
        FROM readings r
        JOIN users u ON r.user_id = u.id
        JOIN tarot_cards tc ON r.num_cards = tc.position
        ORDER BY r.date DESC
        """
        return self.execute_query(query)

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Busca usuário pelo email"""
        query = "SELECT * FROM users WHERE email = ?"
        result = self.execute_query(query, (email,), fetch=True)
        return result[0] if result else None

    def create_user(self, name: str, email: str, password_hash: str) -> bool:
        """Cria um novo usuário"""
        query = "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)"
        return self.execute_query(query, (name, email, password_hash))

    def update_user_balance(self, user_id: int, amount: float) -> bool:
        """Atualiza o saldo do usuário"""
        query = "UPDATE users SET balance = balance + ? WHERE id = ?"
        return self.execute_query(query, (amount, user_id))

    def get_tarot_cards(self) -> List[Dict]:
        """Recupera todas as cartas do tarô"""
        query = """
        SELECT id, name, description, type, position, image_path, is_reversed
        FROM tarot_cards
        ORDER BY type, position
        """
        return self.execute_query(query)

    def create_reading(self, user_id: int, num_cards: int, cost: float) -> Optional[int]:
        """Cria uma nova leitura"""
        query = "INSERT INTO readings (user_id, num_cards, cost) VALUES (?, ?, ?)"
        result = self.execute_query(query, (user_id, num_cards, cost))
        return result if result else None

    def add_card_to_reading(self, reading_id: int, card_id: int, position: int, interpretation: str) -> bool:
        """Adiciona uma carta à leitura"""
        query = """
        INSERT INTO reading_cards 
        (reading_id, card_id, position, interpretation) 
        VALUES (?, ?, ?, ?)
        """
        return self.execute_query(query, (reading_id, card_id, position, interpretation))

    def complete_reading(self, reading_id: int) -> bool:
        """Marca uma leitura como concluída"""
        query = "UPDATE readings SET is_confirmed = 1 WHERE id = ?"
        return self.execute_query(query, (reading_id,))

    def get_reading_details(self, reading_id: int) -> Optional[Dict]:
        """Recupera detalhes de uma leitura específica"""
        query = """
        SELECT 
            r.id,
            u.name,
            r.date,
            r.num_cards,
            tc.name AS tarot_type,
            r.cost,
            r.is_confirmed,
            rc.card_id,
            tc2.name AS card_name,
            rc.position,
            rc.interpretation
        FROM readings r
        JOIN users u ON r.user_id = u.id
        JOIN tarot_cards tc ON r.num_cards = tc.position
        LEFT JOIN reading_cards rc ON r.id = rc.reading_id
        LEFT JOIN tarot_cards tc2 ON rc.card_id = tc2.id
        WHERE r.id = ?
        ORDER BY rc.position ASC
        """
        result = self.execute_query(query, (reading_id,), fetch=True)
        return result[0] if result else None

    def record_feedback(self, reading_id: int, rating: int, comment: str) -> bool:
        """Registra feedback para uma leitura"""
        query = """
        INSERT INTO feedback 
        (reading_id, rating, comment) 
        VALUES (?, ?, ?)
        """
        return self.execute_query(query, (reading_id, rating, comment))

    def get_user_readings(self, user_id: int) -> List[Dict]:
        """Recupera leituras de um usuário específico"""
        query = """
        SELECT 
            r.id,
            r.date,
            tc.name AS tarot_type,
            r.cost,
            r.is_confirmed
        FROM readings r
        JOIN tarot_cards tc ON r.num_cards = tc.position
        WHERE r.user_id = ?
        ORDER BY r.date DESC
        """
        return self.execute_query(query, (user_id,))

    def create_transaction(self, user_id: int, amount: float, description: str, transaction_id: str) -> bool:
        """Cria uma transação financeira"""
        query = """
        INSERT INTO transactions 
        (user_id, type, amount, description, transaction_id) 
        VALUES (?, ?, ?, ?, ?)
        """
        return self.execute_query(query, (user_id, 'payment', amount, description, transaction_id))

    def get_premium_users(self) -> List[Dict]:
        """Recupera usuários premium"""
        query = "SELECT id, name, email, balance FROM users WHERE is_premium = 1"
        return self.execute_query(query)

    def close_connection(self):
        """Fecha a conexão com o banco de dados"""
        if self.conn:
            self.conn.close()