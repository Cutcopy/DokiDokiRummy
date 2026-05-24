from itertools import combinations
from typing import List, Tuple, Optional
from card import Card, card_points
from meld import Meld, MeldError, cards_form_set, cards_form_run, is_wild


# ---------------------------------------------------------------------------
# Meld discovery
# ---------------------------------------------------------------------------

def find_possible_melds(hand: List[Card],
                        wild_rank: Optional[int] = None,
                        qoh_bonus: bool = False,
                        aces_high: bool = False) -> List[List[Card]]:
    """Return all valid meld combinations available from hand."""
    wilds    = [c for c in hand if     is_wild(c, wild_rank)]
    naturals = [c for c in hand if not is_wild(c, wild_rank)]
    results: List[List[Card]] = []

    # ── SETS ──────────────────────────────────────────────────────────────────
    by_rank: dict = {}
    for c in naturals:
        by_rank.setdefault(c.rank, []).append(c)

    for rank, cards in by_rank.items():
        # All-natural combos (3+ same rank, distinct suits)
        for size in range(3, len(cards) + 1):
            for combo in combinations(cards, size):
                combo_list = list(combo)
                if cards_form_set(combo_list, wild_rank):
                    results.append(combo_list)

        # Natural + wild combos (need ≥ 2 naturals of same rank)
        if len(cards) >= 2 and wilds:
            for n_nat in range(2, len(cards) + 1):
                for nat_combo in combinations(cards, n_nat):
                    max_w = min(len(wilds), 4 - n_nat)
                    for n_w in range(1, max_w + 1):
                        for wild_combo in combinations(wilds, n_w):
                            combo_list = list(nat_combo) + list(wild_combo)
                            if cards_form_set(combo_list, wild_rank):
                                results.append(combo_list)

    # ── RUNS ──────────────────────────────────────────────────────────────────
    by_suit: dict = {}
    for c in naturals:
        by_suit.setdefault(c.suit, []).append(c)

    for suit, cards in by_suit.items():
        sorted_cards = sorted(cards, key=lambda c: c.rank)
        n = len(sorted_cards)

        # All-natural consecutive runs (low-ace: rank 1..13)
        for start in range(n):
            run = [sorted_cards[start]]
            for end in range(start + 1, n):
                if sorted_cards[end].rank == run[-1].rank + 1:
                    run.append(sorted_cards[end])
                    if len(run) >= 3:
                        results.append(list(run))
                else:
                    break

        # High-ace runs: ace plays as 14 after King
        if aces_high:
            aces = [c for c in cards if c.rank == 1]
            kings = [c for c in cards if c.rank == 13]
            if aces and kings:
                # Re-sort with ace=14 and look for consecutive runs
                high_cards = sorted(cards, key=lambda c: 14 if c.rank == 1 else c.rank)
                for start in range(len(high_cards)):
                    run = [high_cards[start]]
                    for end in range(start + 1, len(high_cards)):
                        eff_prev = 14 if run[-1].rank == 1 else run[-1].rank
                        eff_curr = 14 if high_cards[end].rank == 1 else high_cards[end].rank
                        if eff_curr == eff_prev + 1:
                            run.append(high_cards[end])
                            if len(run) >= 3 and cards_form_run(run, wild_rank, aces_high):
                                results.append(list(run))
                        else:
                            break

        # Natural slices + wilds filling gaps or extending ends
        if wilds:
            for start in range(n):
                for end in range(start + 1, n):
                    nat_slice = sorted_cards[start:end + 1]
                    min_nat   = nat_slice[0].rank
                    max_nat   = nat_slice[-1].rank
                    nat_set   = {c.rank for c in nat_slice}
                    gaps = sum(1 for r in range(min_nat, max_nat + 1)
                               if r not in nat_set)

                    if gaps > len(wilds):
                        continue   # can't fill internal gaps

                    extra_avail = len(wilds) - gaps
                    for n_extra in range(0, extra_avail + 1):
                        n_w = gaps + n_extra
                        if n_w == 0:
                            continue  # pure-natural case handled above
                        if n_w > len(wilds):
                            break
                        for wild_combo in combinations(wilds, n_w):
                            combo_list = list(nat_slice) + list(wild_combo)
                            if (len(combo_list) >= 3
                                    and cards_form_run(combo_list, wild_rank,
                                                       aces_high)):
                                results.append(combo_list)

    # Deduplicate by frozenset of object ids (handles 2-deck duplicates)
    seen: set = set()
    unique: List[List[Card]] = []
    for combo in results:
        key = frozenset(id(c) for c in combo)
        if key not in seen:
            seen.add(key)
            unique.append(combo)

    # Longest / highest-value melds first (respects QoH bonus in valuation)
    unique.sort(key=lambda m: sum(card_points(c, qoh_bonus) for c in m), reverse=True)
    return unique


def pick_best_melds(hand: List[Card], player_idx: int,
                    wild_rank: Optional[int] = None,
                    qoh_bonus: bool = False,
                    aces_high: bool = False) -> Tuple[List[Meld], List[Card]]:
    """Greedy: pick non-overlapping melds that maximise melded points."""
    working = list(hand)
    chosen: List[Meld] = []

    changed = True
    while changed:
        changed = False
        for meld_cards in find_possible_melds(working, wild_rank, qoh_bonus,
                                              aces_high):
            temp = list(working)
            ok = True
            for c in meld_cards:
                if c in temp:
                    temp.remove(c)
                else:
                    ok = False
                    break
            if ok:
                try:
                    chosen.append(Meld(meld_cards, player_idx, wild_rank,
                                       aces_high))
                    working = temp
                    changed = True
                    break   # restart search on updated hand
                except MeldError:
                    pass

    return chosen, working


# ---------------------------------------------------------------------------
# Card value heuristic
# ---------------------------------------------------------------------------

def card_keep_value(card: Card, hand: List[Card], table_melds,
                    wild_rank: Optional[int] = None,
                    qoh_bonus: bool = False,
                    aces_high: bool = False) -> int:
    """Higher = more useful to keep in hand."""
    # Wild cards are extremely valuable — always keep them
    if is_wild(card, wild_rank):
        return 100

    val = 0

    # Can lay off on existing melds
    for m in table_melds:
        if m.can_add(card):
            val += 4

    # Set potential: how many same-rank cards are in hand
    same_rank = sum(1 for c in hand if c.rank == card.rank and c is not card)
    val += same_rank * 2

    # Run potential: adjacent ranks in same suit
    eff_rank = 14 if (aces_high and card.rank == 1) else card.rank
    same_suit = [c for c in hand if c.suit == card.suit and c is not card]
    for other in same_suit:
        eff_other = 14 if (aces_high and other.rank == 1) else other.rank
        diff = abs(eff_other - eff_rank)
        if diff == 1:
            val += 2
        elif diff == 2:
            val += 1
        # Also check low-ace proximity when aces_high
        if aces_high and card.rank == 1:
            diff_low = abs(other.rank - 1)
            if diff_low == 1:
                val += 2
            elif diff_low == 2:
                val += 1

    return val


def choose_discard(hand: List[Card], table_melds,
                   wild_rank: Optional[int] = None,
                   qoh_bonus: bool = False,
                   aces_high: bool = False) -> Optional[Card]:
    if not hand:
        return None
    # Discard the card with the lowest keep value; break ties by discarding highest points
    return min(hand,
               key=lambda c: (card_keep_value(c, hand, table_melds, wild_rank,
                                              qoh_bonus, aces_high),
                              -card_points(c, qoh_bonus)))


def best_pile_draw_idx(pile: List[Card], hand: List[Card], player_idx: int,
                       table_melds,
                       wild_rank: Optional[int] = None,
                       qoh_bonus: bool = False,
                       must_meld_bottom: bool = False,
                       max_depth: int = 8,
                       aces_high: bool = False) -> Optional[int]:
    """Scan the discard pile and return the best index to draw from, or None
    if drawing from the deck is preferable.

    pile[0] = oldest, pile[-1] = top.  Drawing from pile[i] takes pile[i:]
    (the chosen card plus everything above it).  pile[i] is the 'bottom'
    card of the draw — the one the player specifically wants.

    must_meld_bottom: when the discard-must-meld rule is on, the bottom card
                      must appear in a new meld; positions that can't satisfy
                      this are skipped.
    max_depth:        how many cards deep to search (from the top down).
    """
    if not pile:
        return None

    best_idx   = None
    best_score = 0      # must beat 0 to prefer the pile over the deck

    start = max(0, len(pile) - max_depth)

    for pile_idx in range(len(pile) - 1, start - 1, -1):
        drawn     = pile[pile_idx:]          # slice we'd pick up
        test_hand = hand + drawn

        # Wild on top is always worth taking immediately
        if pile_idx == len(pile) - 1 and is_wild(drawn[0], wild_rank):
            return pile_idx

        melds, remaining = pick_best_melds(test_hand, player_idx,
                                           wild_rank, qoh_bonus, aces_high)

        # Enforce discard-must-meld: the bottom card must land in a meld
        if must_meld_bottom and drawn:
            bottom = drawn[0]
            if not any(bottom in m.cards for m in melds):
                continue

        # Positive: points from new melds
        melded_ids = {id(c) for m in melds for c in m.cards}
        meld_pts   = sum(card_points(c, qoh_bonus)
                         for m in melds for c in m.cards)

        # Positive: drawn cards that can be laid off on existing melds
        layoff_pts  = 0
        used_layoff: set = set()
        for tm in table_melds:
            for c in remaining:
                if id(c) not in used_layoff and tm.can_add(c):
                    layoff_pts += card_points(c, qoh_bonus)
                    used_layoff.add(id(c))

        # Negative: drawn cards that end up stuck in hand (risk losing them)
        stuck = [c for c in drawn
                 if id(c) not in melded_ids and id(c) not in used_layoff]
        hand_penalty = sum(card_points(c, qoh_bonus) for c in stuck)

        net = meld_pts + layoff_pts - hand_penalty
        if net > best_score:
            best_score = net
            best_idx   = pile_idx

    return best_idx
