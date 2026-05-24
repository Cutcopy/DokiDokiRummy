import copy
from enum import Enum, auto
from typing import List, Optional, Tuple
from card import Card, card_points
from deck import Deck
from meld import Meld, MeldError, classify_meld
from player import Player
from settings import GameSettings
import ai as ai_module


class Phase(Enum):
    MENU = auto()
    SETUP = auto()
    PASS_DEVICE = auto()   # Hot-seat: hide hand before next human's turn
    DRAW = auto()          # Current player must draw
    ACTION = auto()        # Current player can meld / lay-off / discard
    RUMMY_WINDOW = auto()  # Other players may call "Rummy" on the top discard
    ROUND_END = auto()     # Scores displayed
    GAME_OVER = auto()


class Result(Enum):
    OK = auto()
    ERROR = auto()
    ROUND_OVER = auto()
    GAME_OVER = auto()


class GameState:
    def __init__(self):
        self.players: List[Player] = []
        self.deck: Optional[Deck] = None
        self.discard_pile: List[Card] = []
        self.table_melds: List[Meld] = []
        self.current_player_idx: int = 0
        self.phase: Phase = Phase.MENU
        self.message: str = "Welcome to Rummy 500!"
        self.round_num: int = 0
        self.round_scores: List[int] = []
        self.settings: GameSettings = GameSettings()

        # Per-player first-meld tracker (reset each round)
        self.first_meld_done: List[bool] = []

        # Draw-from-discard obligation
        self.drawn_from_discard: bool = False
        self.discard_obligation: Optional[Card] = None
        self.drawn_this_turn: bool = False

        # Undo stack — snapshots pushed before every player action
        self.undo_stack: list = []

        # First-meld-out bonus tracker (reset each round)
        self._bonus_player_idx: Optional[int] = None

        # Rummy-call state (reset each round)
        self.rummy_card: Optional[Card] = None   # top discard eligible for a Rummy call
        self.rummy_callers: List[int] = []       # player indices still to query, in order
        self.rummy_next_turn_idx: int = -1       # who goes after the window resolves

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def new_game(self, configs: List[Tuple[str, bool]],
                 settings: Optional[GameSettings] = None):
        """configs = [(name, is_ai), ...]"""
        if settings is not None:
            self.settings = settings
        self.players = [Player(name, is_ai) for name, is_ai in configs]
        for p in self.players:
            p.score = 0
        self.round_num = 0
        self._start_round()

    def _start_round(self):
        self.round_num += 1
        num_p = len(self.players)

        # Deck count respects settings
        if num_p >= 3 and self.settings.two_decks_3plus:
            num_decks = 2
        else:
            num_decks = 1

        add_jokers = (self.settings.wild_rank == 0)
        self.deck = Deck(num_decks, add_jokers=add_jokers)
        self.discard_pile = []
        self.table_melds = []
        self.round_scores = [0] * num_p
        self.first_meld_done = [False] * num_p
        self._bonus_player_idx = None
        self.rummy_card = None
        self.rummy_callers = []
        self.rummy_next_turn_idx = -1
        self.undo_stack.clear()        # undo doesn't cross round boundaries

        hand_size = self.settings.hand_size
        for p in self.players:
            p.hand = []
            p.add_cards(self.deck.deal(hand_size))
            p.sort_hand()

        first = self.deck.deal_one()
        if first:
            self.discard_pile.append(first)

        self.current_player_idx = 0
        self._begin_turn()

    def _begin_turn(self):
        self.drawn_this_turn = False
        self.drawn_from_discard = False
        self.discard_obligation = None

        p = self.current_player
        if p.is_ai:
            self.phase = Phase.DRAW
            self.message = f"{p.name} is thinking..."
        else:
            human_count = sum(1 for pl in self.players if not pl.is_ai)
            if human_count > 1:
                self.phase = Phase.PASS_DEVICE
                self.message = f"Pass the device to {p.name}"
            else:
                self.phase = Phase.DRAW
                self.message = f"{p.name}'s turn - draw a card"

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def current_player(self) -> Player:
        return self.players[self.current_player_idx]

    @property
    def display_player_idx(self) -> int:
        """Player to highlight in the UI — the rummy caller during RUMMY_WINDOW."""
        if self.phase == Phase.RUMMY_WINDOW and self.rummy_callers:
            return self.rummy_callers[0]
        return self.current_player_idx

    @property
    def discard_top(self) -> Optional[Card]:
        return self.discard_pile[-1] if self.discard_pile else None

    # ------------------------------------------------------------------
    # Pass-device confirmation
    # ------------------------------------------------------------------

    def confirm_pass(self) -> Result:
        if self.phase != Phase.PASS_DEVICE:
            return Result.ERROR
        self.phase = Phase.DRAW
        self.message = f"{self.current_player.name}'s turn - draw a card"
        return Result.OK

    # ------------------------------------------------------------------
    # Undo
    # ------------------------------------------------------------------

    def _save_state(self):
        """Snapshot all mutable game state before a player action."""
        snap = {
            'hands':        [list(p.hand) for p in self.players],
            'scores':       [p.score for p in self.players],
            'deck':         list(self.deck.cards),
            'discard':      list(self.discard_pile),
            'melds':        copy.deepcopy(self.table_melds),
            'cur_idx':      self.current_player_idx,
            'phase':        self.phase,
            'message':      self.message,
            'round_scores': list(self.round_scores),
            'first_meld':   list(self.first_meld_done),
            'drawn':        self.drawn_this_turn,
            'from_disc':    self.drawn_from_discard,
            'obligation':   self.discard_obligation,
            'bonus_idx':    self._bonus_player_idx,
            'rummy_card':   self.rummy_card,
            'rummy_callers': list(self.rummy_callers),
            'rummy_next':   self.rummy_next_turn_idx,
        }
        self.undo_stack.append(snap)
        if len(self.undo_stack) > 20:
            self.undo_stack.pop(0)

    def undo(self) -> bool:
        """Restore the state from before the last action. Returns True on success."""
        if not self.undo_stack:
            self.message = "Nothing left to undo"
            return False
        s = self.undo_stack.pop()
        for i, p in enumerate(self.players):
            p.hand          = list(s['hands'][i])
            p.score         = s['scores'][i]
        self.deck.cards         = list(s['deck'])
        self.discard_pile       = list(s['discard'])
        self.table_melds        = s['melds']
        self.current_player_idx = s['cur_idx']
        self.phase              = s['phase']
        self.message            = s['message'] + "  [undone]"
        self.round_scores       = list(s['round_scores'])
        self.first_meld_done    = list(s['first_meld'])
        self.drawn_this_turn    = s['drawn']
        self.drawn_from_discard = s['from_disc']
        self.discard_obligation = s['obligation']
        self._bonus_player_idx  = s['bonus_idx']
        self.rummy_card          = s['rummy_card']
        self.rummy_callers       = list(s['rummy_callers'])
        self.rummy_next_turn_idx = s['rummy_next']
        return True

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw_from_deck(self) -> Result:
        if self.phase != Phase.DRAW:
            self.message = "You need to draw first!"
            return Result.ERROR
        self._save_state()
        if self.deck.is_empty():
            return self._end_round()
        card = self.deck.deal_one()
        self.current_player.add_cards([card])
        self.drawn_this_turn = True
        self.phase = Phase.ACTION
        self.message = f"{self.current_player.name} drew from the deck - meld or discard"
        return Result.OK

    def draw_from_discard(self, pile_index: int) -> Result:
        """
        Take card at pile_index plus all cards above it (higher indices = more recent).
        pile_index 0 = oldest card in pile.
        If settings.discard_must_meld, the bottom-most taken card must be melded first.
        """
        if self.phase != Phase.DRAW:
            self.message = "You need to draw first!"
            return Result.ERROR
        if not self.discard_pile:
            self.message = "Discard pile is empty"
            return Result.ERROR
        if pile_index < 0 or pile_index >= len(self.discard_pile):
            self.message = "Invalid selection"
            return Result.ERROR

        self._save_state()
        taken = self.discard_pile[pile_index:]
        self.discard_pile = self.discard_pile[:pile_index]
        self.current_player.add_cards(taken)
        self.drawn_this_turn = True
        self.drawn_from_discard = True

        # Only set obligation when the rule is active
        if self.settings.discard_must_meld:
            self.discard_obligation = taken[0]

        n = len(taken)
        self.phase = Phase.ACTION
        if self.settings.discard_must_meld:
            if n == 1:
                self.message = f"Drew {taken[0]} - must use it in a meld!"
            else:
                self.message = f"Drew {n} cards - must meld {taken[0]}!"
        else:
            self.message = f"Drew {n} card(s) from the discard pile"
        return Result.OK

    # ------------------------------------------------------------------
    # Melding
    # ------------------------------------------------------------------

    def play_meld(self, cards: List[Card]) -> Result:
        if self.phase != Phase.ACTION:
            self.message = "Can't meld right now"
            return Result.ERROR
        if not self.drawn_this_turn:
            self.message = "Draw a card first"
            return Result.ERROR

        p = self.current_player
        idx = self.current_player_idx

        if not all(p.has_card(c) for c in cards):
            self.message = "One or more cards not in your hand"
            return Result.ERROR

        wild_rank = self.settings.wild_rank
        ah        = self.settings.aces_high
        meld_type = classify_meld(cards, wild_rank, ah)
        if meld_type is None:
            self.message = "Those cards don't form a valid meld"
            return Result.ERROR

        self._save_state()
        # Minimum first-meld check
        min_req = self.settings.min_first_meld
        qoh = self.settings.queen_of_hearts_bonus
        if min_req > 0 and not self.first_meld_done[idx]:
            meld_pts = sum(card_points(c, qoh) for c in cards)
            if meld_pts < min_req:
                self.message = (f"First meld must be worth at least {min_req} pts "
                                f"(yours: {meld_pts})")
                return Result.ERROR

        try:
            meld = Meld(cards, idx, wild_rank, ah)
        except MeldError as e:
            self.message = str(e)
            return Result.ERROR

        was_first_meld = not self.first_meld_done[idx]
        p.remove_cards(cards)
        self.table_melds.append(meld)
        self.first_meld_done[idx] = True

        if self.discard_obligation and self.discard_obligation in cards:
            self.discard_obligation = None

        self.message = f"{p.name} melded {meld.label}"

        if p.hand_empty:
            if was_first_meld and self.settings.first_meld_out_bonus:
                self._bonus_player_idx = idx
            return self._end_round()
        return Result.OK

    def lay_off(self, cards: List[Card], meld_idx: int) -> Result:
        if self.phase != Phase.ACTION:
            self.message = "Can't lay off right now"
            return Result.ERROR
        if not self.drawn_this_turn:
            self.message = "Draw a card first"
            return Result.ERROR
        if meld_idx < 0 or meld_idx >= len(self.table_melds):
            self.message = "Invalid meld"
            return Result.ERROR

        p = self.current_player
        m = self.table_melds[meld_idx]

        self._save_state()
        # Lay-off ownership restriction
        if not self.settings.layoff_any_meld:
            if m.owner_idx != self.current_player_idx:
                owner = self.players[m.owner_idx].name
                self.message = f"You can only lay off on your own melds (owned by {owner})"
                return Result.ERROR

        for card in cards:
            if not p.has_card(card):
                self.message = f"{card} not in your hand"
                return Result.ERROR
            if not m.can_add(card):
                self.message = f"{card} can't be added to {m.label}"
                return Result.ERROR

        for card in cards:
            m.add(card)
            p.remove_card(card)
            if self.discard_obligation and card == self.discard_obligation:
                self.discard_obligation = None

        self.message = f"{p.name} laid off on {m.label}"
        if p.hand_empty:
            return self._end_round()
        return Result.OK

    def discard_card(self, card: Card) -> Result:
        if self.phase != Phase.ACTION:
            self.message = "Can't discard right now"
            return Result.ERROR
        if not self.drawn_this_turn:
            self.message = "Draw a card first"
            return Result.ERROR

        p = self.current_player
        if not p.has_card(card):
            self.message = "That card isn't in your hand"
            return Result.ERROR

        if self.discard_obligation:
            if self.discard_obligation in p.hand:
                self.message = f"You must meld {self.discard_obligation} first!"
                return Result.ERROR

        self._save_state()
        p.remove_card(card)
        self.discard_pile.append(card)
        self.message = f"{p.name} discarded {card}"

        # Check for a rummy opportunity BEFORE declaring going-out.
        # If someone calls Rummy, they intercept the card and block the discarder
        # from going out on that discard.
        callers = self._rummy_eligible_callers(card)
        if callers:
            self.rummy_card = card
            self.rummy_callers = callers
            self.rummy_next_turn_idx = (self.current_player_idx + 1) % len(self.players)
            return self._advance_rummy_window()

        # No rummy possible — check going-out normally
        if p.hand_empty:
            return self._end_round()

        return self._next_player()

    # ------------------------------------------------------------------
    # Turn / round management
    # ------------------------------------------------------------------

    def _next_player(self) -> Result:
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
        self._begin_turn()
        return Result.OK

    # ------------------------------------------------------------------
    # Rummy-call window
    # ------------------------------------------------------------------

    def _rummy_eligible_callers(self, card: Card) -> List[int]:
        """Return player indices (turn order, excluding discarding player) who can
        call Rummy on card — i.e. they have at least one valid meld to lay it off on."""
        if not self.table_melds:
            return []
        n = len(self.players)
        discarded_by = self.current_player_idx
        callers: List[int] = []
        for offset in range(1, n):
            idx = (discarded_by + offset) % n
            for m in self.table_melds:
                if not self.settings.layoff_any_meld and m.owner_idx != idx:
                    continue
                if m.can_add(card):
                    callers.append(idx)
                    break
        return callers

    def _advance_rummy_window(self) -> Result:
        """Process callers in order; AI decides immediately, humans pause the window."""
        while self.rummy_callers:
            idx = self.rummy_callers[0]
            p = self.players[idx]
            if p.is_ai:
                self.rummy_callers.pop(0)
                card = self.rummy_card
                # AI only calls if it benefits its own meld (avoids gifting opponents)
                for mi, m in enumerate(self.table_melds):
                    if m.owner_idx == idx and m.can_add(card):
                        return self._execute_rummy(idx, mi)
                # AI passes — continue to next caller
            else:
                # Human player — pause and wait for input
                self.phase = Phase.RUMMY_WINDOW
                caller_name = self.players[idx].name
                self.message = (f"Rummy! {caller_name}: {self.rummy_card} "
                                f"can be laid off — call it?")
                return Result.OK
        return self._close_rummy_window()

    def _execute_rummy(self, caller_idx: int, meld_idx: int) -> Result:
        """Caller takes the discarded card and lays it off on table_melds[meld_idx]."""
        card   = self.rummy_card
        m      = self.table_melds[meld_idx]
        caller = self.players[caller_idx]
        # Remove the card from the top of the discard pile
        if self.discard_pile and self.discard_pile[-1] is card:
            self.discard_pile.pop()
        m.add(card)
        self.rummy_card = None
        self.rummy_callers = []
        self.message = (f"Rummy! {caller.name} called it — "
                        f"{card} laid off on {m.label}!")
        self.current_player_idx = self.rummy_next_turn_idx
        self.rummy_next_turn_idx = -1
        self._begin_turn()
        return Result.OK

    def _close_rummy_window(self) -> Result:
        """No one called Rummy; advance to the scheduled next turn.
        If the discarder had emptied their hand, the round ends now —
        nobody intercepted the card so the discard stands as going-out."""
        n = len(self.players)
        discarder_idx = (self.rummy_next_turn_idx + n - 1) % n
        went_out = self.players[discarder_idx].hand_empty
        self.rummy_card = None
        self.rummy_callers = []
        self.current_player_idx = self.rummy_next_turn_idx
        self.rummy_next_turn_idx = -1
        if went_out:
            return self._end_round()
        self._begin_turn()
        return Result.OK

    def call_rummy(self, meld_idx: int) -> Result:
        """Human player calls Rummy and lays the card off on the chosen meld."""
        if self.phase != Phase.RUMMY_WINDOW or not self.rummy_callers:
            return Result.ERROR
        caller_idx = self.rummy_callers[0]
        card = self.rummy_card
        if meld_idx < 0 or meld_idx >= len(self.table_melds):
            self.message = "Invalid meld"
            return Result.ERROR
        m = self.table_melds[meld_idx]
        if not self.settings.layoff_any_meld and m.owner_idx != caller_idx:
            self.message = "You can only call Rummy on your own melds"
            return Result.ERROR
        if not m.can_add(card):
            self.message = f"{card} can't be laid off on that meld"
            return Result.ERROR
        return self._execute_rummy(caller_idx, meld_idx)

    def pass_rummy(self) -> Result:
        """Human player declines the Rummy opportunity."""
        if self.phase != Phase.RUMMY_WINDOW or not self.rummy_callers:
            return Result.ERROR
        self.rummy_callers.pop(0)
        return self._advance_rummy_window()

    def _end_round(self) -> Result:
        self.phase = Phase.ROUND_END
        self._tally_scores()
        lines = [f"Round {self.round_num} over!", ""]
        if self._bonus_player_idx is not None:
            lines.append(f"* {self.players[self._bonus_player_idx].name} "
                         f"went out on their first meld! (+50 bonus)")
            lines.append("")
        for i, p in enumerate(self.players):
            sign = "+" if self.round_scores[i] >= 0 else ""
            lines.append(f"{p.name}: {sign}{self.round_scores[i]} pts  (total {p.score})")
        self.message = "\n".join(lines)

        for p in self.players:
            if p.score >= self.settings.win_score:
                self.phase = Phase.GAME_OVER
                winner = max(self.players, key=lambda pl: pl.score)
                self.message += f"\n\n*** {winner.name} wins with {winner.score} points! ***"
                return Result.GAME_OVER
        return Result.ROUND_OVER

    def _tally_scores(self):
        qoh = self.settings.queen_of_hearts_bonus
        meld_pts = [0] * len(self.players)
        for m in self.table_melds:
            meld_pts[m.owner_idx] += sum(card_points(c, qoh) for c in m.cards)
        for i, p in enumerate(self.players):
            hand_pts = sum(card_points(c, qoh) for c in p.hand)
            delta = meld_pts[i] - hand_pts
            self.round_scores[i] = delta
            p.score += delta
        # First-meld-out bonus (+50 for going out on your very first meld)
        if self._bonus_player_idx is not None:
            i = self._bonus_player_idx
            self.round_scores[i] += 50
            self.players[i].score += 50

    def next_round(self) -> Result:
        if self.phase not in (Phase.ROUND_END,):
            return Result.ERROR
        self._start_round()
        return Result.OK

    # ------------------------------------------------------------------
    # AI turn
    # ------------------------------------------------------------------

    def do_ai_turn(self) -> Result:
        p = self.current_player
        assert p.is_ai
        w   = self.settings.wild_rank              # thread through all AI calls
        qoh = self.settings.queen_of_hearts_bonus
        ah  = self.settings.aces_high

        # Draw: scan the pile for the best opportunity, fall back to deck
        pile_idx = ai_module.best_pile_draw_idx(
            self.discard_pile, p.hand, self.current_player_idx,
            self.table_melds, w, qoh,
            must_meld_bottom=self.settings.discard_must_meld,
            aces_high=ah)
        if pile_idx is not None:
            res = self.draw_from_discard(pile_idx)
        else:
            res = self.draw_from_deck()

        if res not in (Result.OK,):
            return res

        # Melds — respects min_first_meld via play_meld()
        melds, _ = ai_module.pick_best_melds(p.hand, self.current_player_idx,
                                              w, qoh, ah)
        for meld in melds:
            res = self.play_meld(meld.cards)
            if res in (Result.ROUND_OVER, Result.GAME_OVER):
                return res

        # Lay-offs — respects layoff_any_meld via lay_off()
        for i, table_meld in enumerate(self.table_melds):
            for card in list(p.hand):
                if table_meld.can_add(card) and p.has_card(card):
                    res = self.lay_off([card], i)
                    if res in (Result.ROUND_OVER, Result.GAME_OVER):
                        return res

        # Satisfy discard obligation if still present
        if self.discard_obligation and p.has_card(self.discard_obligation):
            target = self.discard_obligation
            for meld_cards in ai_module.find_possible_melds(p.hand, w, qoh, ah):
                if target in meld_cards:
                    res = self.play_meld(meld_cards)
                    if res in (Result.ROUND_OVER, Result.GAME_OVER):
                        return res
                    break
            else:
                for i, table_meld in enumerate(self.table_melds):
                    if table_meld.can_add(target):
                        res = self.lay_off([target], i)
                        if res in (Result.ROUND_OVER, Result.GAME_OVER):
                            return res
                        break

        # Discard
        if not p.hand_empty:
            card = ai_module.choose_discard(p.hand, self.table_melds, w, qoh, ah)
            if card:
                return self.discard_card(card)

        return Result.OK
