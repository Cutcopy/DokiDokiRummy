from typing import List
from card import Card


class Player:
    def __init__(self, name: str, is_ai: bool = False):
        self.name = name
        self.is_ai = is_ai
        self.hand: List[Card] = []
        self.score: int = 0

    def add_cards(self, cards: List[Card]):
        self.hand.extend(cards)

    def remove_card(self, card: Card) -> bool:
        if card in self.hand:
            self.hand.remove(card)
            return True
        return False

    def remove_cards(self, cards: List[Card]) -> bool:
        temp = list(self.hand)
        for c in cards:
            if c in temp:
                temp.remove(c)
            else:
                return False
        self.hand = temp
        return True

    def has_card(self, card: Card) -> bool:
        return card in self.hand

    @property
    def hand_points(self) -> int:
        return sum(c.points for c in self.hand)

    @property
    def hand_empty(self) -> bool:
        return len(self.hand) == 0

    def sort_hand(self):
        self.hand.sort(key=lambda c: (c.suit, c.rank))
