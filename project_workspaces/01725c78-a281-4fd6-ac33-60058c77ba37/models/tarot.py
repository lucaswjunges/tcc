import random

class TarotCard:
    def __init__(self, name, arcana, suit=None, number=None, meanings=None, keywords=None, image_url=None):
        self.name = name
        self.arcana = arcana
        self.suit = suit
        self.number = number
        self.meanings = meanings if meanings else {"upright": [], "reversed": []}
        self.keywords = keywords if keywords else {"upright": [], "reversed": []}
        self.image_url = image_url

    def __str__(self):
        return f"{self.name} ({self.arcana})"

    def reading(self, reversed=False):
        orientation = "reversed" if reversed else "upright"
        meaning = random.choice(self.meanings[orientation])
        keywords = ", ".join(self.keywords[orientation])
        return {"meaning": meaning, "keywords": keywords, "orientation": orientation}


class TarotDeck:
    def __init__(self):
        self.cards = []
        # (Adicionar cartas aqui -  Exemplo abaixo)
        self.cards.append(TarotCard(
            name="The Fool",
            arcana="Major",
            meanings={"upright": ["Beginnings, innocence, spontaneity, a free spirit"], "reversed": ["Holding back, recklessness, risk-taking"]},
            keywords={"upright": ["Beginnings", "Innocence", "Free spirit"], "reversed": ["Recklessness", "Risk-taking"]},
            image_url="/static/images/the_fool.jpg"
        ))


    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self, n=1, reversed_chance=0.5):
        drawn_cards = []
        for _ in range(n):
            card = random.choice(self.cards)
            is_reversed = random.random() < reversed_chance
            drawn_cards.append((card, is_reversed))
        return drawn_cards