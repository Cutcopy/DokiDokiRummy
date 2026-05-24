SUITS = ('Hearts', 'Diamonds', 'Clubs', 'Spades')
SUIT_SYMBOLS = {'Hearts': '♥', 'Diamonds': '♦', 'Clubs': '♣', 'Spades': '♠',
                'Joker': '*'}
RANK_NAMES = {0: 'Jk', 1: 'A', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6',
              7: '7', 8: '8', 9: '9', 10: '10', 11: 'J', 12: 'Q', 13: 'K'}


def card_points(card: 'Card', qoh_bonus: bool = False) -> int:
    """Return the point value of a card.
    When qoh_bonus is True the Queen of Hearts is worth 40 instead of 10.
    """
    if qoh_bonus and card.rank == 12 and card.suit == 'Hearts':
        return 40
    return card.points


class Card:
    __slots__ = ('rank', 'suit')

    def __init__(self, rank: int, suit: str):
        self.rank = rank   # 1-13 (1=Ace, 11=J, 12=Q, 13=K)
        self.suit = suit   # 'Hearts', 'Diamonds', 'Clubs', 'Spades'

    @property
    def points(self) -> int:
        if self.rank == 0:   # Joker
            return 25
        if self.rank == 1:
            return 15
        if self.rank >= 10:
            return 10
        return self.rank

    @property
    def rank_name(self) -> str:
        return RANK_NAMES[self.rank]

    @property
    def suit_symbol(self) -> str:
        return SUIT_SYMBOLS[self.suit]

    @property
    def is_red(self) -> bool:
        return self.suit in ('Hearts', 'Diamonds')

    def __eq__(self, other) -> bool:
        return isinstance(other, Card) and self.rank == other.rank and self.suit == other.suit

    def __hash__(self) -> int:
        return hash((self.rank, self.suit))

    def __str__(self) -> str:
        return f"{self.rank_name}{self.suit_symbol}"

    def __repr__(self) -> str:
        return str(self)
