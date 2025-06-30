import random
from models.card import Card

class TarotService:
    def __init__(self, db_session):
        self.db_session = db_session
        self.load_cards()

    def load_cards(self):
        if not self.db_session.query(Card).count():  # Check if the database is empty
            self.create_default_deck()

    def create_default_deck(self):
        suits = ["Copas", "Espadas", "Ouros", "Paus"]
        arcana_major = [
            "O Louco", "O Mago", "A Sacerdotisa", "A Imperatriz", "O Imperador", "O Hierofante",
            "Os Enamorados", "O Carro", "A Justiça", "O Eremita", "A Roda da Fortuna", "A Força",
            "O Enforcado", "A Morte", "A Temperança", "O Diabo", "A Torre", "A Estrela", "A Lua",
            "O Sol", "O Julgamento", "O Mundo"
        ]

        for card_name in arcana_major:
            card = Card(name=card_name, arcana="Maior", suit=None, meaning_up="Meaning Up Placeholder", meaning_reversed="Meaning Reversed Placeholder", img_url=f"images/major/{card_name}.jpg") # Placeholder image URLs
            self.db_session.add(card)

        for suit in suits:
            for rank in range(1, 15):  # Ace (1) to King (14), adjusting for Page, Knight, Queen
                if rank == 1:
                    rank_name = "Ás"
                elif rank == 11:
                    rank_name = "Valete"
                elif rank == 12:
                    rank_name = "Cavaleiro"
                elif rank == 13:
                    rank_name = "Rainha"
                elif rank == 14:
                    rank_name = "Rei"
                else:
                    rank_name = str(rank)

                card_name = f"{rank_name} de {suit}"
                card = Card(name=card_name, arcana="Menor", suit=suit, meaning_up="Meaning Up Placeholder", meaning_reversed="Meaning Reversed Placeholder", img_url=f"images/minor/{suit}/{card_name}.jpg") # Placeholder image URLs
                self.db_session.add(card)


        self.db_session.commit()




    def get_random_cards(self, num_cards):
        all_cards = self.db_session.query(Card).all()
        chosen_cards = random.sample(all_cards, num_cards)
        for card in chosen_cards:
            card.reversed = random.choice([True, False])
        return chosen_cards

    def get_card_by_name(self, name):
        return self.db_session.query(Card).filter(Card.name == name).first()

    def get_spread(self, spread_type="three_card"):
        if spread_type == "three_card":
            cards = self.get_random_cards(3)
            return {"past": cards[0], "present": cards[1], "future": cards[2]}
        else:
            return None # Handle other spread types later