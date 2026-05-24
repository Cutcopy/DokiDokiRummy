"""
Rummy 500 — main entry point.
Run:  python main.py
"""
import sys
import pygame
from typing import List, Tuple

from game_state import GameState, Phase, Result
from settings import GameSettings
from renderer import (Renderer, SW, SH, C_FELT, C_PANEL, C_PANEL2, C_TEXT,
                      C_TEXT_DIM, C_GOLD, C_BTN, C_BTN_HOV, C_BTN_DIS,
                      C_SELECT, _text, _roundrect, Button)

FPS = 60
AI_DELAY_MS = 900      # ms before AI takes its turn


# ── Settings screen state ─────────────────────────────────────────────────────

class SettingsState:
    WIN_SCORES  = [250, 500, 750, 1000]
    MIN_MELDS   = [0, 30, 50]
    MIN_LABELS  = ["None", "30 pts", "50 pts"]
    HAND_SIZES  = [5, 7, 10, 13]

    # (wild_rank value, display label)
    WILD_OPTIONS = [
        (None,  "None"),
        (0,     "Jokers"),
        (1,     "Aces"),
        (2,     "2s (Deuces)"),
        (3,     "3s"),
        (4,     "4s"),
        (5,     "5s"),
        (6,     "6s"),
        (7,     "7s"),
        (8,     "8s"),
        (9,     "9s"),
        (10,    "10s"),
        (11,    "Jacks"),
        (12,    "Queens"),
        (13,    "Kings"),
    ]

    def __init__(self):
        self.win_score_idx   = 1      # 500
        self.min_meld_idx    = 0      # None
        self.hand_size_idx   = 1      # 7 cards
        self.qoh_bonus       = False
        self.first_meld_out  = True
        self.discard_must    = True
        self.layoff_any      = True
        self.two_decks       = True
        self.wild_idx        = 0      # None (no wilds)
        self.aces_high       = False  # Ace low only by default

        # Hit rects rebuilt each draw()
        self._ws_l = self._ws_r = None
        self._mm_l = self._mm_r = None
        self._hs_l = self._hs_r = None
        self._qh_y = self._qh_n = None
        self._fo_y = self._fo_n = None
        self._dm_y = self._df_r = None
        self._la_r = self._lo_r = None
        self._ah_y = self._ah_n = None
        self._td_r = self._od_r = None
        self._wc_l = self._wc_r = None

    @property
    def win_score(self):
        return self.WIN_SCORES[self.win_score_idx]

    @property
    def min_first_meld(self):
        return self.MIN_MELDS[self.min_meld_idx]

    @property
    def hand_size(self):
        return self.HAND_SIZES[self.hand_size_idx]

    @property
    def wild_rank(self):
        return self.WILD_OPTIONS[self.wild_idx][0]

    @property
    def wild_label(self):
        return self.WILD_OPTIONS[self.wild_idx][1]

    def to_settings(self) -> GameSettings:
        return GameSettings(
            win_score=self.win_score,
            min_first_meld=self.min_first_meld,
            hand_size=self.hand_size,
            queen_of_hearts_bonus=self.qoh_bonus,
            first_meld_out_bonus=self.first_meld_out,
            discard_must_meld=self.discard_must,
            layoff_any_meld=self.layoff_any,
            two_decks_3plus=self.two_decks,
            wild_rank=self.wild_rank,
            aces_high=self.aces_high,
        )

    def handle_click(self, pos) -> bool:
        changed = False
        if self._ws_l and self._ws_l.collidepoint(pos):
            self.win_score_idx = (self.win_score_idx - 1) % len(self.WIN_SCORES); changed = True
        elif self._ws_r and self._ws_r.collidepoint(pos):
            self.win_score_idx = (self.win_score_idx + 1) % len(self.WIN_SCORES); changed = True
        elif self._mm_l and self._mm_l.collidepoint(pos):
            self.min_meld_idx = (self.min_meld_idx - 1) % len(self.MIN_MELDS); changed = True
        elif self._mm_r and self._mm_r.collidepoint(pos):
            self.min_meld_idx = (self.min_meld_idx + 1) % len(self.MIN_MELDS); changed = True
        elif self._hs_l and self._hs_l.collidepoint(pos):
            self.hand_size_idx = (self.hand_size_idx - 1) % len(self.HAND_SIZES); changed = True
        elif self._hs_r and self._hs_r.collidepoint(pos):
            self.hand_size_idx = (self.hand_size_idx + 1) % len(self.HAND_SIZES); changed = True
        elif self._qh_y and self._qh_y.collidepoint(pos):
            self.qoh_bonus = True;    changed = True
        elif self._qh_n and self._qh_n.collidepoint(pos):
            self.qoh_bonus = False;   changed = True
        elif self._fo_y and self._fo_y.collidepoint(pos):
            self.first_meld_out = True;  changed = True
        elif self._fo_n and self._fo_n.collidepoint(pos):
            self.first_meld_out = False; changed = True
        elif self._dm_y and self._dm_y.collidepoint(pos):
            self.discard_must = True;  changed = True
        elif self._df_r and self._df_r.collidepoint(pos):
            self.discard_must = False; changed = True
        elif self._la_r and self._la_r.collidepoint(pos):
            self.layoff_any = True;    changed = True
        elif self._lo_r and self._lo_r.collidepoint(pos):
            self.layoff_any = False;   changed = True
        elif self._ah_y and self._ah_y.collidepoint(pos):
            self.aces_high = True;     changed = True
        elif self._ah_n and self._ah_n.collidepoint(pos):
            self.aces_high = False;    changed = True
        elif self._td_r and self._td_r.collidepoint(pos):
            self.two_decks = True;     changed = True
        elif self._od_r and self._od_r.collidepoint(pos):
            self.two_decks = False;    changed = True
        elif self._wc_l and self._wc_l.collidepoint(pos):
            self.wild_idx = (self.wild_idx - 1) % len(self.WILD_OPTIONS); changed = True
        elif self._wc_r and self._wc_r.collidepoint(pos):
            self.wild_idx = (self.wild_idx + 1) % len(self.WILD_OPTIONS); changed = True
        return changed

    def draw(self, surf: pygame.Surface, mp):
        """Draw all setting rows; also rebuilds hit rects."""
        lx  = SW // 2 - 300   # label column x
        rx  = SW // 2 + 20    # control column x
        row_h = 46
        y = 100

        def section(title, y_pos):
            pygame.draw.line(surf, (50, 100, 50),
                             (lx, y_pos + 2), (SW // 2 + 300, y_pos + 2), 1)
            _text(surf, title, lx, y_pos + 5, size=13, bold=True, color=C_GOLD)
            return y_pos + 20

        def cycle_row(label, y_pos, display, description=""):
            _text(surf, label, lx, y_pos + 6, size=18, bold=True, color=C_TEXT)
            if description:
                _text(surf, description, lx, y_pos + 28, size=12, color=C_TEXT_DIM)
            bw = 34
            val_w = 180
            r_l = pygame.Rect(rx, y_pos + 4, bw, 36)
            r_v = pygame.Rect(rx + bw + 4, y_pos + 4, val_w, 36)
            r_r = pygame.Rect(rx + bw + 4 + val_w + 4, y_pos + 4, bw, 36)
            col_l = C_BTN_HOV if r_l.collidepoint(mp) else C_BTN
            col_r = C_BTN_HOV if r_r.collidepoint(mp) else C_BTN
            pygame.draw.rect(surf, col_l, r_l, border_radius=6)
            _text(surf, "<", r_l.centerx, r_l.y + 8, size=16, bold=True, color=C_TEXT, center=True)
            pygame.draw.rect(surf, (30, 55, 30), r_v, border_radius=4)
            pygame.draw.rect(surf, (60, 100, 60), r_v, 1, border_radius=4)
            _text(surf, display, r_v.centerx, r_v.y + 8, size=16, bold=True, color=C_GOLD, center=True)
            pygame.draw.rect(surf, col_r, r_r, border_radius=6)
            _text(surf, ">", r_r.centerx, r_r.y + 8, size=16, bold=True, color=C_TEXT, center=True)
            return r_l, r_r

        def toggle_row(label, y_pos, opt_a, opt_b, active_a, description=""):
            _text(surf, label, lx, y_pos + 6, size=18, bold=True, color=C_TEXT)
            if description:
                _text(surf, description, lx, y_pos + 28, size=12, color=C_TEXT_DIM)
            bw = 130
            gap = 6
            r_a = pygame.Rect(rx, y_pos + 4, bw, 36)
            r_b = pygame.Rect(rx + bw + gap, y_pos + 4, bw, 36)
            col_a = (60, 130, 60) if active_a else (40, 40, 60)
            col_b = (60, 130, 60) if not active_a else (40, 40, 60)
            if r_a.collidepoint(mp): col_a = tuple(min(255, c+25) for c in col_a)
            if r_b.collidepoint(mp): col_b = tuple(min(255, c+25) for c in col_b)
            pygame.draw.rect(surf, col_a, r_a, border_radius=6)
            pygame.draw.rect(surf, col_b, r_b, border_radius=6)
            _text(surf, opt_a, r_a.centerx, r_a.y + 8, size=15,
                  bold=active_a, color=C_TEXT, center=True)
            _text(surf, opt_b, r_b.centerx, r_b.y + 8, size=15,
                  bold=not active_a, color=C_TEXT, center=True)
            return r_a, r_b

        # ── SCORING ───────────────────────────────────────────────────────────
        y = section("SCORING", y)
        self._ws_l, self._ws_r = cycle_row(
            "Target Score", y, f"{self.win_score} pts",
            "First player to reach this total wins")
        y += row_h
        self._mm_l, self._mm_r = cycle_row(
            "Min. First Meld", y, self.MIN_LABELS[self.min_meld_idx],
            "Minimum point value required for your first meld each round")
        y += row_h
        self._hs_l, self._hs_r = cycle_row(
            "Starting Hand Size", y, f"{self.hand_size} cards",
            "Number of cards dealt to each player at the start of each round")
        y += row_h
        self._qh_y, self._qh_n = toggle_row(
            "Queen of Hearts", y, "40 pts", "10 pts", self.qoh_bonus,
            "When enabled the Q♥ scores 40 points instead of the usual 10")
        y += row_h
        self._fo_y, self._fo_n = toggle_row(
            "First Meld Out", y, "+50 Bonus", "No Bonus", self.first_meld_out,
            "Go out on your very first meld of a round to earn 50 extra points")
        y += row_h

        # ── RULES ─────────────────────────────────────────────────────────────
        y = section("RULES", y)
        self._dm_y, self._df_r = toggle_row(
            "Drawn discard card", y, "Must Meld", "Free Play", self.discard_must,
            "Must Meld: the targeted card must be used in a meld immediately")
        y += row_h
        self._la_r, self._lo_r = toggle_row(
            "Lay off on", y, "Any Meld", "Own Melds", self.layoff_any,
            "Restrict which table melds you can extend")
        y += row_h
        self._ah_y, self._ah_n = toggle_row(
            "Aces", y, "High & Low", "Low Only", self.aces_high,
            "High & Low: ace may follow King (Q-K-A) as well as lead (A-2-3)")
        y += row_h

        # ── DECK ──────────────────────────────────────────────────────────────
        y = section("DECK", y)
        self._td_r, self._od_r = toggle_row(
            "Decks for 3+ players", y, "2 Decks", "1 Deck", self.two_decks,
            "Standard Rummy 500 uses two decks for three or more players")
        y += row_h

        # ── WILD CARDS ────────────────────────────────────────────────────────
        y = section("WILD CARDS", y)
        self._wc_l, self._wc_r = cycle_row(
            "Wild Card", y, self.wild_label,
            "Wilds substitute for any card in a meld (need 2+ natural cards)")


# ── Setup screen state ────────────────────────────────────────────────────────

class PlayerConfig:
    def __init__(self, idx: int):
        self.name: str = f"Player {idx + 1}"
        self.is_ai: bool = idx > 0   # Player 1 human by default

    def toggle_ai(self):
        self.is_ai = not self.is_ai


class SetupState:
    MIN_PLAYERS = 2
    MAX_PLAYERS = 4

    def __init__(self):
        self.num_players: int = 2
        self.configs: List[PlayerConfig] = [PlayerConfig(i) for i in range(self.num_players)]
        self._build_rects()

    def set_num_players(self, n: int):
        self.num_players = n
        self.configs = [PlayerConfig(i) for i in range(n)]
        self._build_rects()

    def _build_rects(self):
        # Controls are on a second line below the label (y=190 instead of 160)
        self.minus_rect  = pygame.Rect(SW // 2 - 70, 188, 40, 40)
        self.plus_rect   = pygame.Rect(SW // 2 + 30, 188, 40, 40)
        self.ai_rects    = []   # built per-frame based on num_players
        self.name_rects  = []

    def handle_click(self, pos, renderer) -> bool:
        """Returns True if anything changed."""
        if self.minus_rect.collidepoint(pos):
            if self.num_players > self.MIN_PLAYERS:
                self.set_num_players(self.num_players - 1)
            return True
        if self.plus_rect.collidepoint(pos):
            if self.num_players < self.MAX_PLAYERS:
                self.set_num_players(self.num_players + 1)
            return True
        for i, r in enumerate(self.ai_rects):
            if r.collidepoint(pos):
                self.configs[i].toggle_ai()
                return True
        return False

    def to_configs(self) -> List[Tuple[str, bool]]:
        return [(c.name, c.is_ai) for c in self.configs]

    def draw(self, surf: pygame.Surface, mp):
        # Label on its own line, centered
        _text(surf, "Number of Players", SW // 2, 158,
              size=20, bold=True, color=C_TEXT, center=True)

        # [−]  count  [+]  on the line below, all centered
        hov_m = self.minus_rect.collidepoint(mp)
        pygame.draw.rect(surf, C_BTN_HOV if hov_m else C_BTN, self.minus_rect, border_radius=6)
        _text(surf, "−", self.minus_rect.centerx, self.minus_rect.y + 7,
              size=22, bold=True, color=C_TEXT, center=True)

        _text(surf, str(self.num_players),
              SW // 2, 196, size=24, bold=True, color=C_GOLD, center=True)

        hov_p = self.plus_rect.collidepoint(mp)
        pygame.draw.rect(surf, C_BTN_HOV if hov_p else C_BTN, self.plus_rect, border_radius=6)
        _text(surf, "+", self.plus_rect.centerx, self.plus_rect.y + 7,
              size=22, bold=True, color=C_TEXT, center=True)

        # Per-player rows
        self.ai_rects = []
        self.name_rects = []
        for i, cfg in enumerate(self.configs):
            row_y = 240 + i * 90
            # Background
            row_rect = pygame.Rect(SW // 2 - 280, row_y - 8, 560, 78)
            pygame.draw.rect(surf, (18, 35, 18), row_rect, border_radius=8)
            pygame.draw.rect(surf, (40, 80, 40), row_rect, 1, border_radius=8)

            # Player number
            _text(surf, f"Player {i + 1}", SW // 2 - 260, row_y + 6,
                  size=14, color=C_TEXT_DIM)

            # Name (static display — not editable via typing in this version)
            _text(surf, cfg.name, SW // 2 - 260, row_y + 26,
                  size=20, bold=True, color=C_TEXT)

            # AI toggle
            toggle_r = pygame.Rect(SW // 2 + 80, row_y + 16, 140, 36)
            self.ai_rects.append(toggle_r)
            ai_col = (180, 70, 30) if cfg.is_ai else (50, 130, 60)
            hov = toggle_r.collidepoint(mp)
            pygame.draw.rect(surf, ai_col if not hov else tuple(min(255, c + 30) for c in ai_col),
                             toggle_r, border_radius=8)
            label = "[AI]" if cfg.is_ai else "[Human]"
            _text(surf, label, toggle_r.centerx, toggle_r.y + 8,
                  size=16, bold=True, color=C_TEXT, center=True)

        # Hint
        _text(surf, "Click AI / Human to toggle.  At least one Human recommended.",
              SW // 2, 240 + self.num_players * 90 + 10,
              size=13, color=C_TEXT_DIM, center=True)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    pygame.init()
    screen = pygame.display.set_mode((SW, SH))
    pygame.display.set_caption("Rummy 500")
    clock = pygame.time.Clock()

    game          = GameState()
    renderer      = Renderer(screen)
    setup         = SetupState()
    settings_ui   = SettingsState()
    show_settings = False
    game.phase    = Phase.MENU

    ai_timer: int = 0   # ms timestamp when AI should act

    running = True
    while running:
        now = pygame.time.get_ticks()
        mp = pygame.mouse.get_pos()

        # ── AI auto-play ───────────────────────────────────────────────────
        if (not show_settings
                and game.phase == Phase.DRAW
                and game.current_player.is_ai):
            if ai_timer == 0:
                ai_timer = now + AI_DELAY_MS
            elif now >= ai_timer:
                ai_timer = 0
                result = game.do_ai_turn()
                renderer.reset_turn_ui()

        # ── Events ────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if show_settings:
                        show_settings = False
                    elif renderer.show_pile_overlay:
                        renderer.show_pile_overlay = False
                    elif game.phase == Phase.RUMMY_WINDOW:
                        game.pass_rummy()
                    elif renderer.lay_off_mode:
                        renderer.lay_off_mode = False
                    else:
                        game.phase = Phase.MENU
                        renderer.reset_turn_ui()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                show_settings = _handle_click(
                    event, game, renderer, setup, settings_ui, mp, show_settings)

        # ── Draw ──────────────────────────────────────────────────────────
        if show_settings:
            screen.fill(C_PANEL2)
            _text(screen, "GAME SETTINGS", SW // 2, 30,
                  size=36, bold=True, color=C_GOLD, center=True)
            _text(screen, "Changes take effect from the next new game",
                  SW // 2, 72, size=14, color=C_TEXT_DIM, center=True)
            settings_ui.draw(screen, mp)
            renderer.btn_menu_back.update(mp)
            renderer.btn_menu_back.draw(screen)
            pygame.display.flip()

        elif game.phase == Phase.SETUP:
            screen.fill(C_PANEL)
            pygame.draw.rect(screen, C_FELT, pygame.Rect(0, 60, SW, SH - 120))
            _text(screen, "RUMMY 500  —  Game Setup",
                  SW // 2, 15, size=28, bold=True, color=C_GOLD, center=True)
            setup.draw(screen, mp)
            for b in (renderer.setup_btn_play, renderer.setup_btn_back):
                b.update(mp)
                b.draw(screen)
            pygame.display.flip()

        else:
            renderer.draw(game, mp)  # renderer.draw() calls flip() internally

        clock.tick(FPS)

    pygame.quit()
    sys.exit()


# ── Click handler ─────────────────────────────────────────────────────────────

def _handle_click(event, game: GameState, renderer: Renderer,
                  setup: 'SetupState', settings_ui: SettingsState,
                  mp, show_settings: bool) -> bool:
    """Returns the (possibly updated) show_settings flag."""

    # ── SETTINGS overlay (shown over menu) ────────────────────────────────
    if show_settings:
        settings_ui.handle_click(event.pos)
        if renderer.btn_menu_back.clicked(event):
            return False   # close settings
        return True        # stay in settings

    phase = game.phase

    # ── MENU ──────────────────────────────────────────────────────────────
    if phase == Phase.MENU:
        if renderer.btn_new_game.clicked(event):
            game.phase = Phase.SETUP
            renderer.reset_turn_ui()
        elif renderer.btn_settings.clicked(event):
            return True    # open settings
        elif renderer.btn_quit.clicked(event):
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    # ── SETUP ─────────────────────────────────────────────────────────────
    elif phase == Phase.SETUP:
        setup.handle_click(event.pos, renderer)
        if renderer.setup_btn_play.clicked(event):
            configs = setup.to_configs()
            game.new_game(configs, settings=settings_ui.to_settings())
            renderer.reset_turn_ui()
        elif renderer.setup_btn_back.clicked(event):
            game.phase = Phase.MENU

    # ── PASS DEVICE ───────────────────────────────────────────────────────
    elif phase == Phase.PASS_DEVICE:
        if renderer.btn_ready.clicked(event):
            game.confirm_pass()

    # ── In-game Menu button (topbar — visible in DRAW, ACTION, RUMMY_WINDOW) ─
    elif phase in (Phase.DRAW, Phase.ACTION, Phase.RUMMY_WINDOW):
        if renderer.btn_ingame_menu.clicked(event):
            game.phase = Phase.MENU
            renderer.reset_turn_ui()
            return show_settings

    # ── DRAW phase ────────────────────────────────────────────────────────
    if phase == Phase.DRAW:
        p = game.current_player

        # Overlay takes priority — handle it first and consume the click so
        # underlying buttons (which share the same y position) can't fire.
        if renderer.show_pile_overlay:
            if renderer.btn_cancel_overlay.clicked(event):
                renderer.show_pile_overlay = False
                renderer.pile_overlay_readonly = False
                renderer.pile_hover_idx = -1
            elif not renderer.pile_overlay_readonly:
                # Only allow drawing in non-readonly (human draw turn) mode
                for card, pile_idx, r in renderer.overlay_entries:
                    if r.collidepoint(event.pos):
                        renderer.show_pile_overlay = False
                        renderer.pile_overlay_readonly = False
                        renderer.pile_hover_idx = -1
                        result = game.draw_from_discard(pile_idx)
                        renderer.clear_selection()
                        _check_round_result(result, game, renderer)
                        break
            return  # consume click; nothing else fires while overlay is open

        if p.is_ai:
            # Allow viewing the discard pile while the AI is thinking
            if (renderer.discard_rect
                    and renderer.discard_rect.collidepoint(event.pos)
                    and game.discard_pile):
                renderer.show_pile_overlay = True
                renderer.pile_overlay_readonly = True
                renderer.pile_hover_idx = -1
            return   # AI handled separately; no other clicks

        # Draw from deck button
        if renderer.btn_deck.clicked(event):
            result = game.draw_from_deck()
            renderer.clear_selection()
            _check_round_result(result, game, renderer)

        # Draw top of discard pile button
        elif renderer.btn_discard.clicked(event):
            if game.discard_pile:
                result = game.draw_from_discard(len(game.discard_pile) - 1)
                renderer.clear_selection()
                _check_round_result(result, game, renderer)

        # Open pile viewer
        elif renderer.btn_view_pile.clicked(event):
            renderer.show_pile_overlay = True
            renderer.pile_overlay_readonly = False
            renderer.pile_hover_idx = -1

        # Sort hand
        elif renderer.btn_sort_draw.clicked(event):
            game.current_player.sort_hand()

        # Undo (draw phase — e.g. undo a discard from last turn)
        elif renderer.btn_undo.clicked(event):
            game.undo()
            renderer.reset_turn_ui()

        # Click directly on the deck sprite
        elif (renderer.deck_rect
              and renderer.deck_rect.collidepoint(event.pos)):
            result = game.draw_from_deck()
            renderer.clear_selection()
            _check_round_result(result, game, renderer)

        # Click directly on the discard pile sprite
        elif (renderer.discard_rect
              and renderer.discard_rect.collidepoint(event.pos)
              and game.discard_pile):
            renderer.show_pile_overlay = True
            renderer.pile_overlay_readonly = False
            renderer.pile_hover_idx = -1

    # ── ACTION phase ──────────────────────────────────────────────────────
    elif phase == Phase.ACTION:
        p = game.current_player
        hand = p.hand

        # Overlay close
        if renderer.show_pile_overlay:
            if renderer.btn_cancel_overlay.clicked(event):
                renderer.show_pile_overlay = False
                renderer.pile_overlay_readonly = False
            return

        # Click the discard pile card to peek at the pile (view-only)
        if (renderer.discard_rect
                and renderer.discard_rect.collidepoint(event.pos)
                and game.discard_pile):
            renderer.show_pile_overlay = True
            renderer.pile_overlay_readonly = True
            renderer.pile_hover_idx = -1
            return

        # In lay-off mode: clicking a table meld lays off selected cards on it
        if renderer.lay_off_mode:
            for mi, r in enumerate(renderer.meld_rects):
                if r.collidepoint(event.pos):
                    selected_cards = [hand[i] for i in sorted(renderer.selected)
                                      if i < len(hand)]
                    if selected_cards:
                        result = game.lay_off(selected_cards, mi)
                        renderer.clear_selection()
                        _check_round_result(result, game, renderer)
                    renderer.lay_off_mode = False
                    return
            # Clicking elsewhere cancels lay-off mode
            if not any(b.rect.collidepoint(event.pos)
                       for b in (renderer.btn_meld, renderer.btn_layoff,
                                 renderer.btn_do_discard, renderer.btn_sort_act)):
                renderer.lay_off_mode = False
            return

        # Hand card click → toggle selection
        for i, r in enumerate(renderer.hand_rects):
            if r.collidepoint(event.pos) and i < len(hand):
                renderer.toggle_select(i)
                return

        # Play Meld button
        if renderer.btn_meld.clicked(event):
            selected_cards = [hand[i] for i in sorted(renderer.selected)
                              if i < len(hand)]
            result = game.play_meld(selected_cards)
            renderer.clear_selection()
            _check_round_result(result, game, renderer)

        # Lay Off button
        elif renderer.btn_layoff.clicked(event):
            if renderer.selected:
                renderer.lay_off_mode = not renderer.lay_off_mode
                if renderer.lay_off_mode:
                    renderer.meld_hover_idx = -1

        # Discard button
        elif renderer.btn_do_discard.clicked(event):
            if len(renderer.selected) == 1:
                idx = next(iter(renderer.selected))
                if idx < len(hand):
                    result = game.discard_card(hand[idx])
                    renderer.clear_selection()
                    _check_round_result(result, game, renderer)

        # Sort
        elif renderer.btn_sort_act.clicked(event):
            game.current_player.sort_hand()
            renderer.clear_selection()

        # Undo (action phase — undo draw, meld, lay-off, etc.)
        elif renderer.btn_undo.clicked(event):
            game.undo()
            renderer.reset_turn_ui()

    # ── RUMMY WINDOW ──────────────────────────────────────────────────────
    elif phase == Phase.RUMMY_WINDOW:
        # Pass button
        if renderer.btn_pass_rummy.clicked(event):
            game.pass_rummy()
        else:
            # Clicking a gold-highlighted meld calls Rummy on it
            for mi, r in enumerate(renderer.meld_rects):
                if r.collidepoint(event.pos) and mi in renderer.rummy_valid_meld_indices:
                    result = game.call_rummy(mi)
                    _check_round_result(result, game, renderer)
                    break

    # ── ROUND END ─────────────────────────────────────────────────────────
    elif phase == Phase.ROUND_END:
        if renderer.btn_next_round.clicked(event):
            game.next_round()
            renderer.reset_turn_ui()
        elif renderer.btn_menu_back.clicked(event):
            game.phase = Phase.MENU
            renderer.reset_turn_ui()

    # ── GAME OVER ─────────────────────────────────────────────────────────
    elif phase == Phase.GAME_OVER:
        if renderer.btn_play_again.clicked(event):
            configs = [(p.name, p.is_ai) for p in game.players]
            game.new_game(configs, settings=settings_ui.to_settings())
            renderer.reset_turn_ui()
        elif renderer.btn_menu_back.clicked(event):
            game.phase = Phase.MENU
            renderer.reset_turn_ui()

    return show_settings   # unchanged for all non-settings branches


def _check_round_result(result: Result, game: GameState, renderer: Renderer):
    if result in (Result.ROUND_OVER, Result.GAME_OVER):
        renderer.reset_turn_ui()


if __name__ == "__main__":
    main()
