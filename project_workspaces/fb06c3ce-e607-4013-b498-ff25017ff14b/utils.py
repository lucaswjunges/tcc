import os
import random
import sqlite3

DB_NAME = "tarot.db"

def create_database():
    if os.path.exists(DB_NAME):
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spread TEXT,
            cards TEXT,
            interpretation TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

def get_random_cards(spread):
    # Placeholder - Replace with actual Tarot deck and spread logic
    deck = [str(i) for i in range(1, 79)]  # Example: 78 cards
    return random.sample(deck, k=len(spread))


def save_reading(spread, cards, interpretation):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO readings (spread, cards, interpretation)
        VALUES (?, ?, ?)
    """, (",".join(spread), ",".join(cards), interpretation))


    conn.commit()
    conn.close()

def load_spreads():
    # Placeholder - Replace with loading from file or database
    spreads = {
        "Three-Card Spread": ["Past", "Present", "Future"],
        "Celtic Cross": ["Present", "Challenge", "Past", "Future", "Above", "Below", "Self", "Environment", "Hopes/Fears", "Outcome"]
        # Add more spreads as needed
    }

    return spreads

def format_spread_output(spread_name, cards, spread_positions, interpretation=""):
    output = f"**{spread_name}**\n\n"

    for i, card in enumerate(cards):
        output += f"{spread_positions[i]}: {card}\n"

    if interpretation:
        output += f"\n**Interpretation:**\n{interpretation}"

    return output