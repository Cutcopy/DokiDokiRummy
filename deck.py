import random
from typing import List, Optional
from card import Card, SUITS


class Deck:
    def __init__(self, num_decks: int = 1, add_jokers: bool = False):
        self.cards: List[Card] = []
        for _ in range(num_decks):
            for suit in SUITS:
                for rank in range(1, 14):
                    self.cards.append(Card(rank, suit))
            if add_jokers:
                # Two jokers per deck
                self.cards.append(Card(0, 'Joker'))
                self.cards.append(Card(0, 'Joker'))
        random.shuffle(self.cards)

    def deal_one(self) -> Optional[Card]:
        return self.cards.pop() if self.cards else None

    def deal(self, n: int) -> List[Card]:
        dealt = []
        for _ in range(n):
            c = self.deal_one()
            if c is None:
                break
            dealt.append(c)
        return dealt

    def is_empty(self) -> bool:
        return not self.cards

    @property
    def size(self) -> int:
        return len(self.cards)
