import random

# Dados dos Arcanos Maiores
major_arcana = {
    "0": "O Louco",
    "1": "O Mago",
    "2": "A Sacerdotisa",
    "3": "A Imperatriz",
    "4": "O Imperador",
    "5": "O Papa",
    "6": "Os Enamorados",
    "7": "O Carro",
    "8": "A Justiça",
    "9": "O Eremita",
    "10": "A Roda da Fortuna",
    "11": "A Força",
    "12": "O Enforcado",
    "13": "A Morte",
    "14": "A Temperança",
    "15": "O Diabo",
    "16": "A Torre",
    "17": "A Estrela",
    "18": "A Lua",
    "19": "O Sol",
    "20": "O Julgamento",
    "21": "O Mundo"
}

# Dados dos Arcanos Menores (simplificado para exemplo)
minor_arcana = {
    "naipes": ["Copas", "Espadas", "Ouros", "Paus"],
    "cartas": ["Ás", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Valete", "Rainha", "Rei"]
}


def get_tarot_reading(n_major=3, n_minor=0):
    """
    Retorna uma leitura de tarô com cartas dos Arcanos Maiores e Menores.

    Args:
        n_major: Número de cartas dos Arcanos Maiores a serem sorteadas.
        n_minor: Número de cartas dos Arcanos Menores a serem sorteadas.

    Returns:
        Um dicionário contendo as cartas sorteadas dos Arcanos Maiores e Menores.
    """
    reading = {}

    major_cards = random.sample(list(major_arcana.keys()), n_major)
    reading["major_arcana"] = [{"id": card, "name": major_arcana[card]} for card in major_cards]

    minor_cards = []
    for _ in range(n_minor):
        naipe = random.choice(minor_arcana["naipes"])
        carta = random.choice(minor_arcana["cartas"])
        minor_cards.append(f"{carta} de {naipe}")
    reading["minor_arcana"] = minor_cards

    return reading


def interpret_card(card_id):
    """
    Retorna a interpretação de uma carta específica.

    Args:
        card_id: ID da carta (ex: "0" para O Louco, ou "Rainha de Copas").

    Returns:
        Uma string com a interpretação da carta.
    """

    # Aqui você implementaria a lógica para buscar a interpretação 
    # da carta em um banco de dados ou outro local.
    # Este é apenas um exemplo.

    if card_id in major_arcana:
        return f"Interpretação para {major_arcana[card_id]}:  Lorem ipsum dolor sit amet..."
    elif card_id in [f"{carta} de {naipe}" for naipe in minor_arcana["naipes"] for carta in minor_arcana["cartas"]]:
        return f"Interpretação para {card_id}: Lorem ipsum dolor sit amet..."  # Substituir pela interpretação real
    else:
       return "Carta não encontrada."