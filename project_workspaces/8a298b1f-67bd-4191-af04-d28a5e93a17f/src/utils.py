# src/utils.py

import random
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

class TarotCard:
    """Classe para representar uma carta do tarot."""
    
    def __init__(self, id: int, name: str, meaning: str, reversed_meaning: str = None):
        self.id = id
        self.name = name
        self.meaning = meaning
        self.reversed_meaning = reversed_meaning
    
    def __str__(self):
        return self.name
    
    def get_random_meaning(self, reversed: bool = False) -> str:
        """Obtém um significado aleatório para a carta."""
        if reversed and self.reversed_meaning:
            return self.reversed_meaning
        return self.meaning

class TarotDeck:
    """Classe para gerenciar o baralho completo do tarot."""
    
    def __init__(self, path: str = "data/tarot_cards.json"):
        self.path = path
        self.cards = self._load_cards()
    
    def _load_cards(self) -> List[TarotCard]:
        """Carrega as cartas do arquivo JSON."""
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"Arquivo de cartas não encontrado em {self.path}")
        
        with open(self.path, 'r') as f:
            data = json.load(f)
        
        cards = []
        for card_data in data:
            cards.append(TarotCard(
                id=card_data['id'],
                name=card_data['name'],
                meaning=card_data['meaning'],
                reversed_meaning=card_data.get('reversed_meaning')
            ))
        return cards
    
    def get_all_cards(self) -> List[TarotCard]:
        """Retorna todas as cartas do baralho."""
        return self.cards
    
    def get_card_by_id(self, card_id: int) -> Optional[TarotCard]:
        """Busca uma carta pelo ID."""
        for card in self.cards:
            if card.id == card_id:
                return card
        return None
    
    def get_random_card(self) -> TarotCard:
        """Retorna uma carta aleatória do baralho."""
        return random.choice(self.cards)
    
    def get_spread_positions(self) -> List[Dict[str, Any]]:
        """Retorna as posições do spread."""
        return [
            {"name": "Passado", "cards": []},
            {"name": "Presente", "cards": []},
            {"name": "Futuro", "cards": []},
            {"name": "Desafio", "cards": []},
            {"name": "Oportunidade", "cards": []},
            {"name": "Conselho", "cards": []}
        ]

class ReadingGenerator:
    """Classe para gerar leituras de tarot."""
    
    def __init__(self, deck: TarotDeck):
        self.deck = deck
    
    def generate_three_card_reading(self) -> List[TarotCard]:
        """Gera uma leitura de três cartas."""
        return [
            self.deck.get_random_card(),
            self.deck.get_random_card(),
            self.deck.get_random_card()
        ]
    
    def generate_celtic_cross(self) -> List[TarotCard]:
        """Gera uma leitura Celtic Cross."""
        positions = self.deck.get_spread_positions()
        cards = []
        
        # Primeira carta - Posição Geral
        cards.append(self.deck.get_random_card())
        positions[0]["cards"] = [cards[0]]
        
        # Segunda carta - Posição Atual
        cards.append(self.deck.get_random_card())
        positions[1]["cards"] = [cards[1]]
        
        # Terceira carta - Posição Desafio/Oportunidade
        cards.append(self.deck.get_random_card())
        positions[2]["cards"] = [cards[2]]
        
        # Quarta carta - Posição Específica
        cards.append(self.deck.get_random_card())
        positions[3]["cards"] = [cards[3]]
        
        # Quinta carta - Posição Específica
        cards.append(self.deck.get_random_card())
        positions[4]["cards"] = [cards[4]]
        
        # Sexta carta - Posição Específica
        cards.append(self.deck.get_random_card())
        positions[5]["cards"] = [cards[5]]
        
        return cards
    
    def generate_custom_reading(self, num_cards: int) -> List[TarotCard]:
        """Gera uma leitura personalizada com um número específico de cartas."""
        if num_cards < 1:
            raise ValueError("Número de cartas deve ser maior que zero")
        
        cards = []
        for _ in range(num_cards):
            cards.append(self.deck.get_random_card())
        return cards
    
    def get_card_position(self, card: TarotCard, reversed: bool = False) -> str:
        """Obtém a posição da carta na leitura."""
        # Lógica para determinar a posição baseada no ID da carta
        position = card.id % 6
        if position == 0:
            return "Posição Geral"
        elif position == 1:
            return "Posição Atual"
        elif position == 2:
            return "Posição Desafio"
        elif position == 3:
            return "Posição Oportunidade"
        elif position == 4:
            return "Posição Conselho"
        else:
            return "Posição Específica"
    
    def generate_interpretation(self, card: TarotCard, reversed: bool = False) -> str:
        """Gera uma interpretação para a carta."""
        # Lógica simplificada para gerar interpretações
        if reversed:
            return f"Interpretação invertida de {card.name}: Esta carta está mostrando um lado mais negativo ou desafiador."
        
        return f"Interpretação de {card.name}: Esta carta sugere reflexão sobre {card.meaning[:100]}..."

class PaymentProcessor:
    """Classe para processar pagamentos."""
    
    def __init__(self, payment_method: str = "credit_card"):
        self.payment_method = payment_method
    
    def process_payment(self, amount: float) -> bool:
        """Processa um pagamento."""
        # Simulação de processamento de pagamento
        print(f"Processando pagamento de R${amount:.2f} via {self.payment_method}")
        return True  # Simulação de sucesso
    
    def generate_invoice(self, user_email: str, amount: float) -> str:
        """Gera uma fatura para o usuário."""
        invoice_id = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        invoice_data = {
            "id": invoice_id,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "amount": amount,
            "user": user_email
        }
        return json.dumps(invoice_data)

class FileReader:
    """Classe para ler arquivos de configuração."""
    
    @staticmethod
    def read_config(config_path: str) -> Dict[str, Any]:
        """Lê um arquivo de configuração JSON."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Arquivo de configuração não encontrado em {config_path}")
        
        with open(config_path, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def read_tarot_data(file_path: str) -> List[Dict[str, Any]]:
        """Lê dados do tarot a partir de um arquivo JSON."""
        with open(file_path, 'r') as f:
            return json.load(f)

class SessionManager:
    """Classe para gerenciar sessões de leitura."""
    
    @staticmethod
    def start_session(user_id: str) -> Dict[str, Any]:
        """Inicia uma nova sessão de leitura."""
        session_id = f"SESSION-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        session_data = {
            "id": session_id,
            "user_id": user_id,
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "cards_drawn": [],
            "payment_status": "pending"
        }
        return session_data
    
    @staticmethod
    def save_session(session_data: Dict[str, Any]):
        """Salva os dados da sessão."""
        with open("data/sessions.json", 'a') as f:
            f.write(json.dumps(session_data) + "\n")
    
    @staticmethod
    def get_session(session_id: str) -> Optional[Dict[str, Any]]:
        """Recupera uma sessão pelo ID."""
        try:
            with open("data/sessions.json", 'r') as f:
                for line in f:
                    session = json.loads(line)
                    if session["id"] == session_id:
                        return session
            return None
        except FileNotFoundError:
            return None

class SecurityHelper:
    """Classe para ajudar na segurança da aplicação."""
    
    @staticmethod
    def generate_secret_key(length: int = 32) -> str:
        """Gera uma chave secreta para segurança."""
        import secrets
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash de senha para armazenamento seguro."""
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(stored_hash: str, input_password: str) -> bool:
        """Verifica se a senha corresponde ao hash armazenado."""
        return stored_hash == SecurityHelper.hash_password(input_password)