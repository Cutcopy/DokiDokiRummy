from typing import List, Optional
from card import Card


class MeldError(Exception):
    pass


# ── Wild card helper ──────────────────────────────────────────────────────────

def is_wild(card: Card, wild_rank: Optional[int]) -> bool:
    """True if this card is wild under the given setting.
    wild_rank=None  → no wilds
    wild_rank=0     → Joker cards (rank 0, suit 'Joker') are wild
    wild_rank=1-13  → all cards of that rank are wild
    """
    if wild_rank is None:
        return False
    if wild_rank == 0:
        return card.suit == 'Joker'
    return card.rank == wild_rank


# ── Meld validation ───────────────────────────────────────────────────────────

def cards_form_set(cards: List[Card],
                   wild_rank: Optional[int] = None) -> bool:
    """3+ cards of the same rank, all different suits.
    With wilds: at least 2 natural (non-wild) cards of the same rank;
    wilds substitute for missing suits.  Max 4 cards total (one per suit).
    """
    n = len(cards)
    if n < 3 or n > 4:
        return False

    naturals = [c for c in cards if not is_wild(c, wild_rank)]
    wilds    = [c for c in cards if     is_wild(c, wild_rank)]

    if len(naturals) < 2:
        return False          # always need at least 2 real cards

    # All naturals must share the same rank
    if len({c.rank for c in naturals}) != 1:
        return False

    # Natural suits must all be distinct
    nat_suits = [c.suit for c in naturals]
    if len(nat_suits) != len(set(nat_suits)):
        return False

    # Wilds can't exceed the number of remaining (missing) suits
    missing_suits = 4 - len(set(nat_suits))
    return len(wilds) <= missing_suits


def _check_run_ranks(nat_ranks_sorted: list, n_wilds: int, n_total: int,
                     min_rank: int = 1, max_rank: int = 13) -> bool:
    """Core run-validity test given already-sorted, duplicate-free natural ranks.
    Assumes caller has checked len >= 2 and no duplicates.
    min_rank / max_rank define the legal rank window for the whole run.
    """
    min_nat, max_nat = nat_ranks_sorted[0], nat_ranks_sorted[-1]
    if min_nat < min_rank or max_nat > max_rank:
        return False
    nat_set = set(nat_ranks_sorted)
    gaps = sum(1 for r in range(min_nat, max_nat + 1) if r not in nat_set)
    if n_wilds < gaps:
        return False
    extra = n_wilds - gaps
    run_length = (max_nat - min_nat + 1) + extra
    if run_length != n_total:
        return False
    run_lo_min = max(min_rank, min_nat - extra)
    run_lo_max = min(min_nat, max_rank - run_length + 1)
    return run_lo_min <= run_lo_max


def cards_form_run(cards: List[Card],
                   wild_rank: Optional[int] = None,
                   aces_high: bool = False) -> bool:
    """3+ cards of the same suit in consecutive rank order.
    With aces_high=True the ace may also play as rank 14 (after King).
    Wrap-around runs (K-A-2) are never allowed.
    With wilds: at least 2 natural cards of the same suit; wilds fill internal
    gaps or extend the run at either end.
    """
    n = len(cards)
    if n < 3:
        return False

    naturals = [c for c in cards if not is_wild(c, wild_rank)]
    wilds    = [c for c in cards if     is_wild(c, wild_rank)]

    if len(naturals) < 2:
        return False
    if len({c.suit for c in naturals}) != 1:
        return False

    nat_ranks = sorted(c.rank for c in naturals)
    if len(nat_ranks) != len(set(nat_ranks)):
        return False  # duplicate natural ranks

    n_wilds = len(wilds)

    # ── Low ace (rank 1), run fits inside [1, 13] ─────────────────────────
    if _check_run_ranks(nat_ranks, n_wilds, n, min_rank=1, max_rank=13):
        return True

    # ── High ace (rank 14), run fits inside [2, 14] ───────────────────────
    if aces_high and 1 in nat_ranks:
        high_ranks = sorted(14 if r == 1 else r for r in nat_ranks)
        if len(high_ranks) == len(set(high_ranks)):   # no duplicates after remap
            if _check_run_ranks(high_ranks, n_wilds, n, min_rank=2, max_rank=14):
                return True

    return False


def classify_meld(cards: List[Card],
                  wild_rank: Optional[int] = None,
                  aces_high: bool = False) -> Optional[str]:
    """Returns 'set', 'run', or None."""
    if cards_form_set(cards, wild_rank):
        return 'set'
    if cards_form_run(cards, wild_rank, aces_high):
        return 'run'
    return None


# ── Meld object ───────────────────────────────────────────────────────────────

class Meld:
    def __init__(self, cards: List[Card], owner_idx: int,
                 wild_rank: Optional[int] = None,
                 aces_high: bool = False):
        self.wild_rank  = wild_rank
        self.aces_high  = aces_high
        meld_type = classify_meld(cards, wild_rank, aces_high)
        if meld_type is None:
            raise MeldError(f"Not a valid meld: {cards}")
        self.meld_type = meld_type

        # For runs with aces_high: determine whether the ace plays as 14.
        # It does if the run only validates with the high-ace interpretation.
        self._ace_is_high = False
        if aces_high and meld_type == 'run':
            nats_check = [c for c in cards if not is_wild(c, wild_rank)]
            low_ranks  = sorted(c.rank for c in nats_check)
            n_w        = sum(1 for c in cards if is_wild(c, wild_rank))
            if not _check_run_ranks(low_ranks, n_w, len(cards),
                                    min_rank=1, max_rank=13):
                self._ace_is_high = True

        nats = sorted((c for c in cards if not is_wild(c, wild_rank)),
                      key=lambda c: self._eff_rank(c))
        wlds = [c for c in cards if is_wild(c, wild_rank)]
        self.cards: List[Card] = nats + wlds
        self.owner_idx = owner_idx

    def _eff_rank(self, card: Card) -> int:
        """Sorting rank: 14 for ace when it plays high in this run, else face value."""
        if self._ace_is_high and card.rank == 1:
            return 14
        return card.rank

    def can_add(self, card: Card) -> bool:
        """True if card can legally be added to this meld."""
        test = self.cards + [card]
        if self.meld_type == 'set':
            return cards_form_set(test, self.wild_rank)
        return cards_form_run(test, self.wild_rank, self.aces_high)

    def add(self, card: Card) -> bool:
        if not self.can_add(card):
            return False
        self.cards.append(card)
        # Re-sort: naturals by effective rank, wilds at end
        nats = sorted((c for c in self.cards if not is_wild(c, self.wild_rank)),
                      key=lambda c: self._eff_rank(c))
        wlds = [c for c in self.cards if is_wild(c, self.wild_rank)]
        self.cards = nats + wlds
        return True

    @property
    def points(self) -> int:
        return sum(c.points for c in self.cards)

    @property
    def label(self) -> str:
        nats = [c for c in self.cards if not is_wild(c, self.wild_rank)]
        n_wilds = len(self.cards) - len(nats)
        wild_tag = f"+{n_wilds}W" if n_wilds else ""

        if self.meld_type == 'set':
            rank_name = nats[0].rank_name if nats else '?'
            return f"{rank_name}s ({len(self.cards)}){wild_tag}"

        # run — sort by effective rank so Q-K-A shows as Q→A, not A→K
        if nats:
            nat_sorted = sorted(nats, key=lambda c: self._eff_rank(c))
            sym = nat_sorted[0].suit_symbol
            lo  = nat_sorted[0].rank_name
            hi  = nat_sorted[-1].rank_name
            return f"Run {lo}-{hi}{sym}{wild_tag}"
        return f"Wild Run ({len(self.cards)})"

    def __repr__(self) -> str:
        return f"Meld({self.meld_type}: {self.cards})"
