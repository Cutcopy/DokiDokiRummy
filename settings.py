"""
GameSettings — configurable Rummy 500 rule-set.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class GameSettings:
    # ── Scoring ───────────────────────────────────────────────────────────────
    win_score: int = 500          # Points needed to win the game
    min_first_meld: int = 0       # Minimum combined points for a player's very
                                  # first meld in each round (0 = no minimum)

    # ── Rule variations ───────────────────────────────────────────────────────
    discard_must_meld: bool = True  # When you draw from the discard pile the
                                    # bottom-most card taken must go into a meld
                                    # before you can discard.
    layoff_any_meld: bool = True    # True  → lay off on any meld on the table
                                    # False → only on melds you own

    # ── Deck ─────────────────────────────────────────────────────────────────
    two_decks_3plus: bool = True    # Use two decks when 3+ players are playing

    # ── Hand size ─────────────────────────────────────────────────────────────
    hand_size: int = 7               # Cards dealt to each player at round start

    # ── Bonus scoring ─────────────────────────────────────────────────────────
    queen_of_hearts_bonus: bool = False  # Queen of Hearts worth 40 pts instead of 10
    first_meld_out_bonus:  bool = True   # +50 pts for going out on your very first meld

    # ── Wild cards ────────────────────────────────────────────────────────────
    wild_rank: Optional[int] = None  # None = no wilds
                                     # 0    = Jokers (added to the deck)
                                     # 1-13 = that rank acts as wild

    # ── Ace rank ──────────────────────────────────────────────────────────────
    aces_high: bool = False           # True  → A can also be played after K (rank 14)
                                      # False → A is low only (rank 1, before 2)
