"""
Pygame renderer for Rummy 500.
All drawing, layout constants, and hit-detection live here.
"""
import pygame
from typing import List, Optional, Dict, Tuple, Set
from card import Card
from meld import Meld, classify_meld
from game_state import GameState, Phase

# ── Screen ────────────────────────────────────────────────────────────────────
SW, SH = 1280, 800

# ── Card dimensions ────────────────────────────────────────────────────────────
CW, CH = 72, 108          # normal card
MINI_CW, MINI_CH = 44, 66  # opponent / overlay card

# ── Colours ────────────────────────────────────────────────────────────────────
C_FELT       = (25,  90,  25)
C_FELT_DARK  = (18,  65,  18)
C_FELT_LIGHT = (35, 110,  35)
C_CARD       = (255, 252, 240)
C_BACK       = (28,  56, 140)
C_BACK_PAT   = (20,  40, 110)
C_RED        = (200,  25,  25)
C_BLACK      = (18,   18,  18)
C_SELECT     = (255, 220,   0)
C_HOVER      = (200, 200, 255)
C_PANEL      = (15,  30,  15)
C_PANEL2     = (12,  22,  50)
C_TEXT       = (235, 235, 235)
C_TEXT_DIM   = (150, 150, 150)
C_BTN        = (50,  80, 160)
C_BTN_HOV    = (70, 110, 210)
C_BTN_DIS    = (60,  60,  80)
C_GOLD       = (220, 175,  20)
C_SHADOW     = (0, 0, 0, 100)
C_OVERLAY    = (0, 0, 0, 170)
C_OBLIGATION = (255, 100,  0)
C_WILD       = (160,  0, 220)   # purple – wild card border / badge
C_JOKER_BG   = ( 70,  0, 110)   # dark purple – Joker card background
C_JOKER_BORD = (200, 120, 255)  # light purple – Joker card border


def _font_cache():
    cache: Dict[Tuple, pygame.font.Font] = {}

    def get(size: int, bold: bool = False) -> pygame.font.Font:
        key = (size, bold)
        if key not in cache:
            for name in ('Segoe UI', 'Arial', 'DejaVu Sans', None):
                try:
                    f = pygame.font.SysFont(name, size, bold=bold)
                    cache[key] = f
                    break
                except Exception:
                    pass
        return cache[key]

    return get


_font = _font_cache()


# ── Low-level draw helpers ─────────────────────────────────────────────────────

def _shadow(surf: pygame.Surface, rect: pygame.Rect, r: int = 6):
    s = pygame.Surface((rect.w + 4, rect.h + 4), pygame.SRCALPHA)
    pygame.draw.rect(s, (0, 0, 0, 80), s.get_rect(), border_radius=r)
    surf.blit(s, (rect.x + 3, rect.y + 3))


def _roundrect(surf, color, rect, r=6, border=0, border_color=None):
    pygame.draw.rect(surf, color, rect, border_radius=r)
    if border and border_color:
        pygame.draw.rect(surf, border_color, rect, border, border_radius=r)


def _text(surf, txt, x, y, size=16, color=C_TEXT, bold=False, center=False, anchor_right=False):
    f = _font(size, bold)
    s = f.render(txt, True, color)
    if center:
        x -= s.get_width() // 2
    elif anchor_right:
        x -= s.get_width()
    surf.blit(s, (x, y))
    return s.get_width(), s.get_height()


def _text_size(txt, size=16, bold=False):
    return _font(size, bold).size(txt)


# ── Card rendering ─────────────────────────────────────────────────────────────

def draw_card_back(surf: pygame.Surface, x: int, y: int,
                   w: int = CW, h: int = CH, hover: bool = False):
    r = pygame.Rect(x, y, w, h)
    _shadow(surf, r)
    _roundrect(surf, C_BACK, r, r=5,
               border=2, border_color=C_HOVER if hover else (50, 80, 180))
    inner = pygame.Rect(x + 5, y + 5, w - 10, h - 10)
    _roundrect(surf, C_BACK_PAT, inner, r=3)
    # Simple crosshatch
    for i in range(0, inner.w, 8):
        pygame.draw.line(surf, C_BACK, (inner.x + i, inner.y),
                         (inner.x, inner.y + i), 1)
        pygame.draw.line(surf, C_BACK, (inner.right - i, inner.bottom),
                         (inner.right, inner.bottom - i), 1)


def draw_card(surf: pygame.Surface, card: Card, x: int, y: int,
              w: int = CW, h: int = CH,
              selected: bool = False, hover: bool = False,
              obligation: bool = False,
              wild_rank: Optional[int] = None):
    r = pygame.Rect(x, y, w, h)
    _shadow(surf, r)

    small = max(10, w // 5)
    large = max(22, w // 3)
    cx = x + w // 2
    cy = y + h // 2

    # ── Joker card (rank 0, suit 'Joker') ─────────────────────────────────
    if card.suit == 'Joker':
        border_col = C_SELECT if selected else (C_OBLIGATION if obligation else C_JOKER_BORD)
        border_w   = 3 if (selected or obligation) else 2
        _roundrect(surf, C_JOKER_BG, r, r=5, border=border_w, border_color=border_col)
        # "JO" / "KER" stacked at centre
        half = max(14, w // 4)
        _text(surf, "JO",  cx, cy - half,       size=half, bold=True,
              color=(255, 255, 255), center=True)
        _text(surf, "KER", cx, cy - half // 4,  size=max(10, half * 2 // 3),
              bold=True, color=C_GOLD, center=True)
        # Corner asterisks
        _text(surf, "*", x + 3, y + 2,
              size=small, color=C_JOKER_BORD, bold=True)
        _text(surf, "*", x + w - small - 3, y + h - small - 4,
              size=small, color=C_JOKER_BORD, bold=True)
        return

    # ── Determine whether this card is a wild (non-Joker) ─────────────────
    is_wild_card = (wild_rank is not None and wild_rank != 0
                    and card.rank == wild_rank)

    # ── Border / background ───────────────────────────────────────────────
    bg = C_CARD
    if selected:
        border_col, border_w = C_SELECT, 3
    elif obligation:
        border_col, border_w = C_OBLIGATION, 3
    elif is_wild_card:
        border_col, border_w = C_WILD, 3
    elif hover:
        border_col, border_w = C_HOVER, 2
    else:
        border_col, border_w = (170, 165, 155), 1

    _roundrect(surf, bg, r, r=5, border=border_w, border_color=border_col)

    suit_col = C_RED if card.is_red else C_BLACK

    # Top-left rank + suit
    _text(surf, card.rank_name,   x + 3, y + 2,             size=small, color=suit_col, bold=True)
    _text(surf, card.suit_symbol, x + 3, y + 2 + small + 1, size=small, color=suit_col)

    # Bottom-right (mirrored)
    rn_w, _ = _text_size(card.rank_name, size=small, bold=True)
    _text(surf, card.rank_name,
          x + w - rn_w - 3, y + h - small * 2 - 6, size=small, color=suit_col, bold=True)
    _text(surf, card.suit_symbol,
          x + w - small - 3, y + h - small - 4,    size=small, color=suit_col)

    # Centre suit (large)
    suit_surf = _font(large).render(card.suit_symbol, True, suit_col)
    surf.blit(suit_surf, (cx - suit_surf.get_width() // 2,
                          cy - suit_surf.get_height() // 2))

    # ── Wild badge (top-right corner) ─────────────────────────────────────
    if is_wild_card:
        badge_r = max(6, w // 9)
        bx = x + w - badge_r - 2
        by = y + badge_r + 2
        pygame.draw.circle(surf, C_WILD, (bx, by), badge_r)
        _text(surf, "W", bx, by - badge_r // 2 - 1,
              size=max(8, badge_r), bold=True, color=(255, 255, 255), center=True)


# ── Button ─────────────────────────────────────────────────────────────────────

class Button:
    def __init__(self, rect: pygame.Rect, label: str,
                 enabled: bool = True, color=None):
        self.rect = rect
        self.label = label
        self.enabled = enabled
        self.color = color or C_BTN
        self._hovered = False

    def draw(self, surf: pygame.Surface):
        if not self.enabled:
            col = C_BTN_DIS
        elif self._hovered:
            col = C_BTN_HOV
        else:
            col = self.color
        _shadow(surf, self.rect, r=8)
        _roundrect(surf, col, self.rect, r=8)
        _roundrect(surf, tuple(min(255, c + 40) for c in col),
                   self.rect, r=8, border=1,
                   border_color=tuple(min(255, c + 40) for c in col))
        tx = self.rect.centerx
        ty = self.rect.centery - 8
        _text(surf, self.label, tx, ty, size=16, bold=True, center=True)

    def update(self, mouse_pos):
        self._hovered = self.enabled and self.rect.collidepoint(mouse_pos)

    def clicked(self, event) -> bool:
        return (self.enabled and event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1 and self.rect.collidepoint(event.pos))


# ── Main Renderer ──────────────────────────────────────────────────────────────

class Renderer:
    # Layout constants (y positions)
    Y_TOPBAR   = 0
    H_TOPBAR   = 44
    Y_OPP      = 44
    H_OPP      = 130
    Y_TABLE    = 174
    H_TABLE    = 296
    Y_MSG      = 470
    H_MSG      = 40
    Y_HAND     = 510
    H_HAND     = 160
    Y_BTNS     = 670
    H_BTNS     = 130

    def __init__(self, screen: pygame.Surface):
        self.screen = screen

        # UI state
        self.selected: Set[int] = set()   # indices into current_player.hand
        self.lay_off_mode: bool = False    # clicked "Lay Off" button
        self.show_pile_overlay: bool = False
        self.pile_hover_idx: int = -1      # which card in overlay is hovered
        self.meld_hover_idx: int = -1      # which table meld is hovered

        # Hit-detection rects (rebuilt each frame)
        self.hand_rects: List[pygame.Rect] = []
        self.meld_rects: List[pygame.Rect] = []
        self.deck_rect: Optional[pygame.Rect] = None
        self.discard_rect: Optional[pygame.Rect] = None

        # Overlay: list of (card, pile_index, rect)
        self.overlay_entries: List[Tuple[Card, int, pygame.Rect]] = []
        self.pile_overlay_readonly: bool = False  # True = view-only, no drawing
        self.rummy_valid_meld_indices: set = set()  # meld indices valid for rummy call

        # Buttons
        self._build_buttons()

    # ── Button factory ────────────────────────────────────────────────────────

    def _build_buttons(self):
        bw, bh = 172, 52
        gap = 13
        total = bw * 5 + gap * 4
        sx = (SW - total) // 2
        by = self.Y_BTNS + (self.H_BTNS - bh) // 2

        def btn(i, label, enabled=True, color=None):
            x = sx + i * (bw + gap)
            return Button(pygame.Rect(x, by, bw, bh), label, enabled, color)

        C_UNDO = (150, 95, 10)   # amber — visually distinct from action buttons

        # Draw phase (slots 0-3) + Undo (slot 4)
        self.btn_deck      = btn(0, "Draw from Deck")
        self.btn_discard   = btn(1, "Draw from Discard")
        self.btn_view_pile = btn(2, "View Discard Pile")
        self.btn_sort_draw = btn(3, "Sort Hand")
        self.btn_undo      = btn(4, "Undo", color=C_UNDO)

        # Action phase (slots 0-3) — btn_undo reused at slot 4
        self.btn_meld       = btn(0, "Play Meld")
        self.btn_layoff     = btn(1, "Lay Off on Meld")
        self.btn_do_discard = btn(2, "Discard Card")
        self.btn_sort_act   = btn(3, "Sort Hand")

        # Round-end / game-over
        cx = SW // 2
        self.btn_next_round = Button(pygame.Rect(cx - 120, 580, 240, 56),
                                     "Next Round", color=(60, 130, 60))
        self.btn_play_again = Button(pygame.Rect(cx - 120, 580, 240, 56),
                                     "Play Again", color=(60, 130, 60))
        self.btn_menu_back  = Button(pygame.Rect(cx - 120, 650, 240, 56),
                                     "Main Menu", color=C_BTN)

        # Overlay
        self.btn_cancel_overlay = Button(pygame.Rect(SW // 2 - 100, SH - 90, 200, 48),
                                         "Cancel", color=(120, 40, 40))

        # Pass-device
        self.btn_ready = Button(pygame.Rect(SW // 2 - 130, SH // 2 + 60, 260, 60),
                                "I'm Ready – Show My Hand", color=(60, 130, 60))

        # Menu
        self.btn_new_game = Button(pygame.Rect(SW // 2 - 120, 330, 240, 52),
                                   "New Game", color=(60, 130, 60))
        self.btn_settings = Button(pygame.Rect(SW // 2 - 120, 400, 240, 52),
                                   "Settings", color=C_BTN)
        self.btn_quit     = Button(pygame.Rect(SW // 2 - 120, 470, 240, 52),
                                   "Quit", color=(120, 40, 40))

        # In-game top-bar "Menu" button (visible during DRAW / ACTION phases)
        self.btn_ingame_menu = Button(pygame.Rect(SW - 98, 8, 90, 28),
                                      "Menu", color=(60, 50, 90))

        # Rummy-call window
        self.btn_pass_rummy = Button(pygame.Rect(SW // 2 - 110, 709, 220, 52),
                                     "Pass", color=(120, 40, 40))

        # Setup screen buttons
        self.setup_btn_play = Button(pygame.Rect(SW // 2 - 130, 650, 260, 56),
                                     "Start Game", color=(60, 130, 60))
        self.setup_btn_back = Button(pygame.Rect(SW // 2 + 150, 650, 180, 56),
                                     "Back", color=C_BTN)

    # ── Master draw dispatch ──────────────────────────────────────────────────

    def draw(self, game: GameState, mouse_pos: Tuple[int, int]):
        self.screen.fill(C_FELT_DARK)
        phase = game.phase

        if phase == Phase.MENU:
            self._draw_menu(mouse_pos)
        elif phase == Phase.SETUP:
            self._draw_setup(game, mouse_pos)
        elif phase == Phase.PASS_DEVICE:
            self._draw_pass_device(game, mouse_pos)
        elif phase in (Phase.DRAW, Phase.ACTION, Phase.RUMMY_WINDOW):
            self._draw_game(game, mouse_pos)
        elif phase == Phase.ROUND_END:
            self._draw_round_end(game, mouse_pos)
        elif phase == Phase.GAME_OVER:
            self._draw_game_over(game, mouse_pos)

        pygame.display.flip()

    # ── Menu screen ───────────────────────────────────────────────────────────

    def _draw_menu(self, mp):
        self.screen.fill(C_PANEL)
        # Decorative felt strip
        pygame.draw.rect(self.screen, C_FELT, pygame.Rect(0, 200, SW, 400))

        _text(self.screen, "RUMMY  500", SW // 2, 100,
              size=72, bold=True, color=C_GOLD, center=True)
        _text(self.screen, "Classic card game — first to 500 points wins",
              SW // 2, 190, size=20, color=C_TEXT_DIM, center=True)

        for b in (self.btn_new_game, self.btn_settings, self.btn_quit):
            b.update(mp)
            b.draw(self.screen)

    # ── Setup screen ─────────────────────────────────────────────────────────

    def _draw_setup(self, game: GameState, mp):
        # Background drawn by caller; just draw the action buttons
        for b in (self.setup_btn_play, self.setup_btn_back):
            b.update(mp)
            b.draw(self.screen)

    # ── Pass-device screen ────────────────────────────────────────────────────

    def _draw_pass_device(self, game: GameState, mp):
        self.screen.fill(C_PANEL2)
        cy = SH // 2
        _text(self.screen, "Pass the Device", SW // 2, cy - 120,
              size=40, bold=True, color=C_GOLD, center=True)
        _text(self.screen, game.current_player.name + "'s Turn",
              SW // 2, cy - 55, size=30, bold=True, color=C_TEXT, center=True)
        _text(self.screen, "Other players, please look away.",
              SW // 2, cy, size=18, color=C_TEXT_DIM, center=True)
        self.btn_ready.update(mp)
        self.btn_ready.draw(self.screen)

    # ── Main game screen ──────────────────────────────────────────────────────

    def _draw_game(self, game: GameState, mp):
        rummy = (game.phase == Phase.RUMMY_WINDOW)

        # Pre-compute which melds are valid for the rummy caller (used in table draw)
        if rummy and game.rummy_callers:
            caller_idx = game.rummy_callers[0]
            self.rummy_valid_meld_indices = {
                mi for mi, m in enumerate(game.table_melds)
                if game.rummy_card and m.can_add(game.rummy_card) and
                (game.settings.layoff_any_meld or m.owner_idx == caller_idx)
            }
        else:
            self.rummy_valid_meld_indices = set()

        self._draw_topbar(game, mp)
        self._draw_opponents(game)
        self._draw_table_area(game, mp)

        if not rummy:
            self._draw_message(game)
            self._draw_hand(game, mp)
            self._draw_action_buttons(game, mp)

        if self.show_pile_overlay:
            self._draw_pile_overlay(game, mp)

        if rummy:
            self._draw_rummy_overlay(game, mp)

    def _draw_topbar(self, game: GameState, mp):
        bar = pygame.Rect(0, 0, SW, self.H_TOPBAR)
        pygame.draw.rect(self.screen, C_PANEL, bar)

        # ── Row 1 (y=5): title | round | deck info | menu button ─────────
        _text(self.screen, "RUMMY 500", 10, 5, size=18, bold=True, color=C_GOLD)
        _text(self.screen, f"Round {game.round_num}",
              SW // 2, 6, size=15, center=True)
        # Deck/pile counts sit to the left of the Menu button
        _text(self.screen, f"Dk:{game.deck.size}  Pl:{len(game.discard_pile)}",
              SW - 106, 8, size=12, color=C_TEXT_DIM, anchor_right=True)
        self.btn_ingame_menu.update(mp)
        self.btn_ingame_menu.draw(self.screen)

        # ── Row 2 (y=27): per-player scores, evenly slotted ──────────────
        # Each player gets an equal-width slot; active player shown in gold.
        n = len(game.players)
        for i, p in enumerate(game.players):
            cx = (SW * (2 * i + 1)) // (2 * n)
            is_cur = (i == game.display_player_idx)
            col  = C_GOLD if is_cur else C_TEXT_DIM
            bold = is_cur
            prefix = "> " if is_cur else "  "
            _text(self.screen, f"{prefix}{p.name}: {p.score} pts",
                  cx, 27, size=13, bold=bold, color=col, center=True)

    def _draw_opponents(self, game: GameState):
        area = pygame.Rect(0, self.Y_OPP, SW, self.H_OPP)
        pygame.draw.rect(self.screen, C_FELT, area)

        opponents = [(i, p) for i, p in enumerate(game.players)
                     if i != game.display_player_idx]
        if not opponents:
            return

        slot_w = SW // len(opponents)
        for slot, (i, p) in enumerate(opponents):
            sx = slot * slot_w
            # Name + score
            active = (i == game.current_player_idx)
            col = C_GOLD if active else C_TEXT_DIM
            _text(self.screen, f"{p.name}  ({p.score} pts)",
                  sx + slot_w // 2, self.Y_OPP + 4, size=14, color=col, center=True)
            _text(self.screen, f"{len(p.hand)} cards",
                  sx + slot_w // 2, self.Y_OPP + 22, size=12, color=C_TEXT_DIM, center=True)
            # Draw face-down card fan
            n = len(p.hand)
            if n == 0:
                continue
            max_fan = min(n, 12)
            spacing = min(MINI_CW + 2, (slot_w - MINI_CW - 20) // max(1, max_fan - 1))
            total_w = spacing * (max_fan - 1) + MINI_CW
            fx = sx + (slot_w - total_w) // 2
            fy = self.Y_OPP + 42
            for k in range(max_fan):
                draw_card_back(self.screen, fx + k * spacing, fy, MINI_CW, MINI_CH)

    def _draw_table_area(self, game: GameState, mp):
        area = pygame.Rect(0, self.Y_TABLE, SW, self.H_TABLE)
        pygame.draw.rect(self.screen, C_FELT_LIGHT, area)
        pygame.draw.line(self.screen, C_FELT_DARK, (0, self.Y_TABLE), (SW, self.Y_TABLE), 2)

        # Deck
        deck_x = 40
        deck_y = self.Y_TABLE + (self.H_TABLE - CH) // 2
        self.deck_rect = pygame.Rect(deck_x, deck_y, CW, CH)
        hover_deck = self.deck_rect.collidepoint(mp) if not self.show_pile_overlay else False
        draw_card_back(self.screen, deck_x, deck_y, hover=hover_deck)
        _text(self.screen, str(game.deck.size),
              deck_x + CW // 2, deck_y + CH + 4, size=13, color=C_TEXT_DIM, center=True)
        _text(self.screen, "DECK", deck_x + CW // 2, deck_y + CH + 18,
              size=11, color=C_TEXT_DIM, center=True)

        # Discard pile
        disc_x = 140
        disc_y = deck_y
        self.discard_rect = pygame.Rect(disc_x, disc_y, CW, CH)
        hover_disc = self.discard_rect.collidepoint(mp) if not self.show_pile_overlay else False
        if game.discard_pile:
            top = game.discard_pile[-1]
            obligation = (game.discard_obligation == top)
            draw_card(self.screen, top, disc_x, disc_y, hover=hover_disc,
                      obligation=obligation,
                      wild_rank=game.settings.wild_rank)
        else:
            # Empty slot
            r = pygame.Rect(disc_x, disc_y, CW, CH)
            _roundrect(self.screen, (20, 70, 20), r, r=5,
                       border=2, border_color=(40, 100, 40))
            _text(self.screen, "Empty", disc_x + CW // 2, disc_y + CH // 2 - 8,
                  size=13, color=C_TEXT_DIM, center=True)
        _text(self.screen, f"Pile ({len(game.discard_pile)})",
              disc_x + CW // 2, disc_y + CH + 4, size=13, color=C_TEXT_DIM, center=True)
        _text(self.screen, "DISCARD", disc_x + CW // 2, disc_y + CH + 18,
              size=11, color=C_TEXT_DIM, center=True)

        # Table melds
        meld_area_x = 260
        meld_area_w = SW - meld_area_x - 20
        self._draw_table_melds(game, meld_area_x, self.Y_TABLE + 8,
                               meld_area_w, self.H_TABLE - 16, mp)

    def _draw_table_melds(self, game: GameState,
                          x: int, y: int, w: int, h: int, mp):
        self.meld_rects = []
        if not game.table_melds:
            _text(self.screen, "No melds yet", x + w // 2, y + h // 2 - 10,
                  size=14, color=C_TEXT_DIM, center=True)
            return

        mini_w, mini_h = 46, 70
        spacing_card = 30          # overlap
        pad_x, pad_y = 6, 4
        row_h = mini_h + pad_y * 2 + 20
        cols = max(1, w // 200)
        col_w = w // cols

        for mi, meld in enumerate(game.table_melds):
            col = mi % cols
            row = mi // cols
            mx = x + col * col_w + pad_x
            my = y + row * row_h + pad_y
            if my + mini_h > y + h:
                break  # overflow

            n = len(meld.cards)
            total_meld_w = spacing_card * (n - 1) + mini_w
            meld_rect = pygame.Rect(mx, my, total_meld_w + 2, mini_h + 2)
            self.meld_rects.append(meld_rect)

            hovered = (self.lay_off_mode and meld_rect.collidepoint(mp))
            if hovered:
                self.meld_hover_idx = mi
                pygame.draw.rect(self.screen, C_SELECT,
                                 meld_rect.inflate(4, 4), 2, border_radius=5)
            elif mi in self.rummy_valid_meld_indices:
                # Gold highlight: valid target for a Rummy call
                hov_col = (255, 220, 60) if meld_rect.collidepoint(mp) else C_GOLD
                pygame.draw.rect(self.screen, hov_col,
                                 meld_rect.inflate(6, 6), 3, border_radius=5)

            for ci, card in enumerate(meld.cards):
                cx = mx + ci * spacing_card
                hover_c = (hovered and ci == len(meld.cards) - 1)
                draw_card(self.screen, card, cx, my, mini_w, mini_h,
                          hover=hover_c, wild_rank=game.settings.wild_rank)

            # Owner label
            owner = game.players[meld.owner_idx].name
            _text(self.screen, f"{meld.label}  [{owner}]",
                  mx, my + mini_h + 2, size=11, color=C_TEXT_DIM)

    def _draw_message(self, game: GameState):
        bar = pygame.Rect(0, self.Y_MSG, SW, self.H_MSG)
        pygame.draw.rect(self.screen, C_PANEL, bar)
        msg = game.message.split("\n")[0]   # single line in gameplay
        _text(self.screen, msg, SW // 2, self.Y_MSG + 10,
              size=16, center=True)
        if game.discard_obligation:
            _text(self.screen,
                  f"[!] Must meld {game.discard_obligation} before discarding",
                  SW // 2, self.Y_MSG + 24, size=13,
                  color=C_OBLIGATION, center=True)

    def _draw_hand(self, game: GameState, mp):
        area = pygame.Rect(0, self.Y_HAND, SW, self.H_HAND)
        pygame.draw.rect(self.screen, C_FELT, area)
        pygame.draw.line(self.screen, C_FELT_DARK,
                         (0, self.Y_HAND), (SW, self.Y_HAND), 2)

        p = game.current_player
        hand = p.hand
        self.hand_rects = []

        if not hand:
            _text(self.screen, "No cards", SW // 2, self.Y_HAND + 60,
                  size=18, color=C_TEXT_DIM, center=True)
            return

        n = len(hand)
        max_w = SW - 40
        spacing = min(CW + 4, (max_w - CW) // max(1, n - 1))
        total_w = spacing * (n - 1) + CW
        start_x = (SW - total_w) // 2
        base_y = self.Y_HAND + (self.H_HAND - CH) // 2

        for i, card in enumerate(hand):
            cx = start_x + i * spacing
            sel = i in self.selected
            cy = base_y - (20 if sel else 0)
            r = pygame.Rect(cx, cy, CW, CH)
            hover = r.collidepoint(mp) and not self.show_pile_overlay
            is_oblig = (game.discard_obligation == card)
            draw_card(self.screen, card, cx, cy, selected=sel,
                      hover=hover, obligation=is_oblig,
                      wild_rank=game.settings.wild_rank)
            self.hand_rects.append(pygame.Rect(cx, base_y - 20, CW, CH + 20))

    def _draw_action_buttons(self, game: GameState, mp):
        area = pygame.Rect(0, self.Y_BTNS, SW, self.H_BTNS)
        pygame.draw.rect(self.screen, C_PANEL, area)
        pygame.draw.line(self.screen, C_FELT_DARK,
                         (0, self.Y_BTNS), (SW, self.Y_BTNS), 2)

        sel_count = len(self.selected)
        can_undo = (bool(game.undo_stack)
                    and not game.current_player.is_ai)

        # Undo button is always slot-4; update here so both branches share it
        self.btn_undo.enabled = can_undo
        self.btn_undo.update(mp)

        if game.phase == Phase.DRAW:
            has_pile = bool(game.discard_pile)
            self.btn_deck.enabled = True
            self.btn_discard.enabled = has_pile
            self.btn_view_pile.enabled = has_pile
            self.btn_sort_draw.enabled = True
            for b in (self.btn_deck, self.btn_discard,
                      self.btn_view_pile, self.btn_sort_draw, self.btn_undo):
                b.update(mp)
                b.draw(self.screen)

        elif game.phase == Phase.ACTION:
            self.btn_meld.enabled = sel_count >= 3
            self.btn_layoff.enabled = sel_count >= 1
            self.btn_do_discard.enabled = sel_count == 1
            self.btn_sort_act.enabled = True

            # Highlight layoff button when in lay-off mode
            self.btn_layoff.color = (180, 130, 20) if self.lay_off_mode else C_BTN
            if self.lay_off_mode:
                self.btn_layoff.label = "Lay Off: Click a Meld ↑"
            else:
                self.btn_layoff.label = "Lay Off on Meld"

            for b in (self.btn_meld, self.btn_layoff,
                      self.btn_do_discard, self.btn_sort_act, self.btn_undo):
                b.update(mp)
                b.draw(self.screen)

            # Hint
            if self.lay_off_mode:
                _text(self.screen, "Select a meld above to lay off your selected card(s)",
                      SW // 2, self.Y_BTNS + 95, size=13, color=C_GOLD, center=True)

    # ── Discard pile overlay ──────────────────────────────────────────────────

    def _draw_pile_overlay(self, game: GameState, mp):
        # Semi-transparent backdrop
        overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        panel_w, panel_h = 860, 480
        px = (SW - panel_w) // 2
        py = (SH - panel_h) // 2
        panel = pygame.Rect(px, py, panel_w, panel_h)
        _roundrect(self.screen, C_PANEL2, panel, r=12,
                   border=2, border_color=C_GOLD)

        readonly = self.pile_overlay_readonly
        if readonly:
            _text(self.screen, "Discard Pile  (view only)",
                  SW // 2, py + 12, size=16, bold=True, color=C_GOLD, center=True)
            _text(self.screen, "Most recent on the left  —  planning view",
                  SW // 2, py + 34, size=13, color=C_TEXT_DIM, center=True)
        else:
            _text(self.screen, "Discard Pile  (click a card to draw it + all above)",
                  SW // 2, py + 12, size=16, bold=True, color=C_GOLD, center=True)
            _text(self.screen, "Most recent on the left",
                  SW // 2, py + 34, size=13, color=C_TEXT_DIM, center=True)

        self.pile_hover_idx = -1   # reset each frame; set below on hover
        pile = game.discard_pile   # index 0 = oldest, -1 = newest
        if not pile:
            _text(self.screen, "Pile is empty", SW // 2, py + panel_h // 2,
                  size=18, color=C_TEXT_DIM, center=True)
        else:
            # Display newest-first (right-to-left reversed)
            display = list(reversed(list(enumerate(pile))))  # (pile_idx, card)
            col_count = min(len(display), 8)
            total_w = col_count * (MINI_CW + 6) - 6
            cx_start = px + (panel_w - total_w) // 2
            cy_card = py + 60

            self.overlay_entries = []
            for slot, (pile_idx, card) in enumerate(display):
                if slot >= 40:   # safety cap
                    break
                row = slot // 8
                col = slot % 8
                ox = cx_start + col * (MINI_CW + 6)
                oy = cy_card + row * (MINI_CH + 30)
                r = pygame.Rect(ox, oy, MINI_CW, MINI_CH)

                hover_this = r.collidepoint(mp)

                if readonly:
                    # View-only: plain hover, no draw-selection highlighting
                    draw_card(self.screen, card, ox, oy, MINI_CW, MINI_CH,
                              hover=hover_this,
                              wild_rank=game.settings.wild_rank)
                    n_above = len(pile) - pile_idx
                    label = f"#{n_above}" if n_above > 1 else "top"
                    _text(self.screen, label, ox + MINI_CW // 2, oy + MINI_CH + 2,
                          size=11, color=C_TEXT_DIM, center=True)
                else:
                    # Draw mode: highlight this card + all above it on hover
                    hov = (self.pile_hover_idx >= 0
                           and pile_idx >= self.pile_hover_idx)
                    if hover_this:
                        self.pile_hover_idx = pile_idx
                    draw_card(self.screen, card, ox, oy, MINI_CW, MINI_CH,
                              selected=hov, hover=hover_this,
                              wild_rank=game.settings.wild_rank)
                    n_above = len(pile) - pile_idx
                    label = f"+{n_above}" if n_above > 1 else "top"
                    _text(self.screen, label, ox + MINI_CW // 2, oy + MINI_CH + 2,
                          size=11, color=C_GOLD if hov else C_TEXT_DIM, center=True)

                self.overlay_entries.append((card, pile_idx, r))

        self.btn_cancel_overlay.label = "Close" if readonly else "Cancel"
        self.btn_cancel_overlay.update(mp)
        self.btn_cancel_overlay.draw(self.screen)

    # ── Rummy-call overlay ────────────────────────────────────────────────────

    def _draw_rummy_overlay(self, game: GameState, mp):
        """Draw the rummy-call panel over the lower portion of the screen."""
        caller_idx  = game.rummy_callers[0] if game.rummy_callers else -1
        caller_name = game.players[caller_idx].name if caller_idx >= 0 else "?"
        card        = game.rummy_card

        # Fill message + hand + buttons areas
        pygame.draw.rect(self.screen, C_PANEL,
                         pygame.Rect(0, self.Y_MSG, SW, SH - self.Y_MSG))
        pygame.draw.line(self.screen, C_FELT_DARK,
                         (0, self.Y_MSG), (SW, self.Y_MSG), 2)
        pygame.draw.line(self.screen, C_FELT_DARK,
                         (0, self.Y_BTNS), (SW, self.Y_BTNS), 2)

        # Header
        _text(self.screen, "RUMMY OPPORTUNITY",
              SW // 2, self.Y_MSG + 10, size=17, bold=True,
              color=C_GOLD, center=True)

        # Player prompt
        _text(self.screen, f"{caller_name}  —  do you want to call it?",
              SW // 2, self.Y_HAND + 14, size=21, bold=True,
              color=C_TEXT, center=True)

        # Discarded card (mini, left of centre)
        card_x = SW // 2 - MINI_CW - 110
        card_y = self.Y_HAND + 52
        _text(self.screen, "Discarded:",
              card_x + MINI_CW // 2, card_y - 16,
              size=12, color=C_TEXT_DIM, center=True)
        if card:
            draw_card(self.screen, card, card_x, card_y,
                      MINI_CW, MINI_CH, wild_rank=game.settings.wild_rank)

        # Instructions (right of card)
        ix = SW // 2 - 30
        _text(self.screen, "Click a gold-highlighted meld above",
              ix, card_y + 6,  size=15, color=C_GOLD, center=True)
        _text(self.screen, "to call Rummy and lay it off.",
              ix, card_y + 26, size=15, color=C_GOLD, center=True)
        _text(self.screen, "Or click Pass below to decline.",
              ix, card_y + 52, size=14, color=C_TEXT_DIM, center=True)

        # Pass button (in the buttons area)
        self.btn_pass_rummy.update(mp)
        self.btn_pass_rummy.draw(self.screen)

    # ── Round end screen ──────────────────────────────────────────────────────

    def _draw_round_end(self, game: GameState, mp):
        self.screen.fill(C_PANEL)
        cy = 160
        _text(self.screen, f"Round {game.round_num} Complete",
              SW // 2, cy, size=40, bold=True, color=C_GOLD, center=True)

        for i, p in enumerate(game.players):
            delta = game.round_scores[i]
            sign = "+" if delta >= 0 else ""
            col = (100, 220, 100) if delta >= 0 else (220, 80, 80)
            y = cy + 80 + i * 50
            _text(self.screen, f"{p.name}",
                  SW // 2 - 180, y, size=22, bold=True)
            _text(self.screen, f"{sign}{delta} pts this round",
                  SW // 2 - 10, y, size=20, color=col)
            _text(self.screen, f"Total: {p.score}",
                  SW // 2 + 240, y, size=20, color=C_TEXT_DIM)

        # Win condition note
        _text(self.screen, f"First to {500} points wins",
              SW // 2, cy + 80 + len(game.players) * 50 + 20,
              size=14, color=C_TEXT_DIM, center=True)

        self.btn_next_round.update(mp)
        self.btn_next_round.draw(self.screen)
        self.btn_menu_back.update(mp)
        self.btn_menu_back.draw(self.screen)

    # ── Game-over screen ──────────────────────────────────────────────────────

    def _draw_game_over(self, game: GameState, mp):
        self.screen.fill(C_PANEL2)
        winner = max(game.players, key=lambda p: p.score)
        _text(self.screen, "GAME OVER", SW // 2, 130,
              size=56, bold=True, color=C_GOLD, center=True)
        _text(self.screen, f"{winner.name} wins!", SW // 2, 205,
              size=32, color=C_GOLD, center=True)

        # Leaderboard
        ranked = sorted(game.players, key=lambda p: p.score, reverse=True)
        medals = ["1st", "2nd", "3rd", "4th"]
        for i, p in enumerate(ranked):
            y = 275 + i * 52
            col = C_GOLD if i == 0 else C_TEXT
            # Draw a small badge circle
            badge_x = SW // 2 - 200
            pygame.draw.circle(self.screen, col, (badge_x, y + 12), 16)
            pygame.draw.circle(self.screen, C_PANEL2, (badge_x, y + 12), 14)
            _text(self.screen, medals[min(i, 3)],
                  badge_x, y + 4, size=12, bold=True, color=col, center=True)
            _text(self.screen, f"{p.name}  -  {p.score} pts",
                  SW // 2 - 170, y, size=24, color=col)

        self.btn_play_again.update(mp)
        self.btn_play_again.draw(self.screen)
        self.btn_menu_back.update(mp)
        self.btn_menu_back.draw(self.screen)

    # ── Input helpers ─────────────────────────────────────────────────────────

    def toggle_select(self, hand_idx: int):
        if hand_idx in self.selected:
            self.selected.discard(hand_idx)
        else:
            self.selected.add(hand_idx)

    def clear_selection(self):
        self.selected.clear()
        self.lay_off_mode = False
        self.meld_hover_idx = -1

    def reset_turn_ui(self):
        self.clear_selection()
        self.show_pile_overlay = False
        self.pile_overlay_readonly = False
        self.pile_hover_idx = -1
        self.rummy_valid_meld_indices = set()
