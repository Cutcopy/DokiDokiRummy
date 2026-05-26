// ============================================================
// Rummy 500 — core game engine (pure JS, no React)
// ============================================================
//
// Settings supported (all live in game.settings):
//  - winScore        : first to this score wins (default 500)
//  - acesHigh        : ace can also follow K in runs — Q-K-A (default false)
//  - jokersWild      : include jokers in deck as wild cards (default true)
//  - mustMeldDrawnCard: when drawing from discard, the bottom card must go
//                       into a meld before you can discard (default true)
//  - layoffAnyMeld   : true = lay off on any player's meld; false = own only (default true)
//  - queenOfHeartsBonus: Q♥ scores 40 pts instead of 10 (default false)
//  - firstMeldOutBonus : +50 pts for going out on your very first meld of the round (default true)
//  - minFirstMeld    : minimum combined point value of player's first meld (0 = none)
//  - twoDecks3plus   : use two shuffled decks when 3+ players (default true)
// ============================================================

const SUITS = ['♠', '♥', '♦', '♣'];
const RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'];

let _nextId = 1;
const nextId = () => `c${_nextId++}`;

// ---------- Default settings ----------

const DEFAULT_SETTINGS = {
  winScore:            500,
  acesHigh:            true,   // aces rank both low (A-2-3) and high (Q-K-A)
  jokersWild:          false,  // jokers not included in deck
  deuceWild:           true,   // 2s act as wild cards in melds
  mustMeldDrawnCard:   true,
  layoffAnyMeld:       true,
  queenOfHeartsBonus:  true,   // Q♥ worth 40 pts
  firstMeldOutBonus:   true,
  minFirstMeld:        0,
  twoDecks3plus:       true,
  handSize:            7,      // 7 cards dealt to each player
  difficulty:          'normal', // 'normal' | 'hard'
};

// ---------- Card helpers ----------

function createCard(rank, suit) {
  return { id: nextId(), rank, suit, isJoker: false };
}

function createJoker(color) {
  return { id: nextId(), rank: 'JOKER', suit: null, isJoker: true, color };
}

function cardValue(card, queenOfHeartsBonus = false) {
  if (card.isJoker) return 15;
  if (card.rank === 'A') return 15;
  if (card.rank === 'Q' && card.suit === '♥' && queenOfHeartsBonus) return 40;
  if (['J', 'Q', 'K'].includes(card.rank)) return 10;
  return parseInt(card.rank, 10);
}

function isRed(card) {
  return card.suit === '♥' || card.suit === '♦';
}

function rankIndex(rank) {
  return RANKS.indexOf(rank); // A=0, 2=1, ... K=12
}

// ---------- Deck ----------

function createDeck(includeJokers = true) {
  const deck = [];
  for (const suit of SUITS) {
    for (const rank of RANKS) deck.push(createCard(rank, suit));
  }
  if (includeJokers) {
    deck.push(createJoker('red'));
    deck.push(createJoker('black'));
  }
  return deck;
}

function shuffle(arr, rng = Math.random) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

// ---------- Wild card helper ----------

// Returns true if the card acts as a wild (joker, or a 2 when deuceWild is on).
function isWild(card, deuceWild = false) {
  return card.isJoker || (deuceWild && card.rank === '2');
}

// ---------- Meld validation ----------

// A "set" = 3-4 cards of same rank, wilds allowed.
function isValidSet(cards, deuceWild = false) {
  if (!Array.isArray(cards) || cards.length < 3) return false;
  const nonWilds = cards.filter(c => !isWild(c, deuceWild));
  if (nonWilds.length === 0) return false;
  const rank = nonWilds[0].rank;
  if (!nonWilds.every(c => c.rank === rank)) return false;
  if (cards.length > 4) return false;
  return true;
}

// A "run" = 3+ cards of same suit in consecutive ranks. Wilds fill gaps.
// acesHigh=false → ace is low only (A-2-3).
// acesHigh=true  → ace may also be high (Q-K-A).
function isValidRun(cards, acesHigh = false, deuceWild = false) {
  if (!Array.isArray(cards) || cards.length < 3) return false;
  const arranged = arrangeRun(cards, acesHigh, deuceWild);
  return arranged !== null;
}

// Try to arrange cards into a valid run. Returns ordered cards or null.
function arrangeRun(cards, acesHigh = false, deuceWild = false) {
  if (cards.length < 3) return null;
  const nonWilds = cards.filter(c => !isWild(c, deuceWild));
  const wilds    = cards.filter(c => isWild(c, deuceWild));
  if (nonWilds.length === 0) return null;
  const suit = nonWilds[0].suit;
  if (!nonWilds.every(c => c.suit === suit)) return null;
  // Try ace-low; also try ace-high if the setting allows it.
  const attempts = acesHigh ? [false, true] : [false];
  for (const ah of attempts) {
    const result = tryArrangeRun(nonWilds, wilds, ah);
    if (result) return result;
  }
  return null;
}

function tryArrangeRun(nonJokers, jokers, aceHigh) {
  const pos = (r) => (r === 'A' && aceHigh ? 13 : rankIndex(r));
  const sorted    = [...nonJokers].sort((a, b) => pos(a.rank) - pos(b.rank));
  const positions = sorted.map(c => pos(c.rank));
  for (let i = 1; i < positions.length; i++) {
    if (positions[i] === positions[i - 1]) return null; // duplicate ranks
  }
  const minPos = positions[0];
  const maxPos = positions[positions.length - 1];
  let gapsNeeded = 0;
  for (let i = 1; i < positions.length; i++) {
    gapsNeeded += positions[i] - positions[i - 1] - 1;
  }
  if (gapsNeeded > jokers.length) return null;
  const remainingJokers = jokers.length - gapsNeeded;
  let extendDown = 0;
  let extendUp   = remainingJokers;
  if (maxPos + extendUp > 13) {
    extendUp   = 13 - maxPos;
    extendDown = remainingJokers - extendUp;
  }
  if (minPos - extendDown < 0) {
    extendDown = minPos;
    extendUp   = remainingJokers - extendDown;
    if (maxPos + extendUp > 13) return null;
  }
  const jokerQueue = [...jokers];
  const result = [];
  for (let i = 0; i < extendDown; i++) result.push(jokerQueue.shift());
  let idx = 0;
  for (let p = minPos; p <= maxPos; p++) {
    if (idx < sorted.length && positions[idx] === p) {
      result.push(sorted[idx++]);
    } else {
      result.push(jokerQueue.shift());
    }
  }
  for (let i = 0; i < extendUp; i++) result.push(jokerQueue.shift());
  if (result.length < 3) return null;
  return result;
}

function isValidMeld(cards, acesHigh = false, deuceWild = false) {
  return isValidSet(cards, deuceWild) || isValidRun(cards, acesHigh, deuceWild);
}

function meldType(cards, acesHigh = false, deuceWild = false) {
  if (isValidSet(cards, deuceWild)) return 'set';
  if (isValidRun(cards, acesHigh, deuceWild)) return 'run';
  return null;
}

// ---------- Lay-off logic ----------

// Can we add `card` to an existing `meld`? Returns new card array or null.
function tryLayOff(card, meld, acesHigh = false, deuceWild = false) {
  if (isValidSet(meld, deuceWild)) {
    const nonWilds = meld.filter(c => !isWild(c, deuceWild));
    const rank = nonWilds[0]?.rank;
    if (isWild(card, deuceWild) || card.rank === rank) {
      const candidate = [...meld, card];
      if (isValidSet(candidate, deuceWild)) return candidate;
    }
    return null;
  }
  if (isValidRun(meld, acesHigh, deuceWild)) {
    const arranged = arrangeRun(meld, acesHigh, deuceWild);
    if (!arranged) return null;
    for (const test of [[card, ...arranged], [...arranged, card]]) {
      if (isValidRun(test, acesHigh, deuceWild)) {
        const newArr = arrangeRun(test, acesHigh, deuceWild);
        if (newArr) return newArr;
      }
    }
    return null;
  }
  return null;
}

// ---------- Game state ----------

function createGame(playerNames, options = {}) {
  const settings  = { ...DEFAULT_SETTINGS, ...options.settings };
  const numPlayers = playerNames.length;
  const useTwo     = numPlayers >= 3 && settings.twoDecks3plus;
  const rawDeck    = useTwo
    ? [...createDeck(settings.jokersWild), ...createDeck(settings.jokersWild)]
    : createDeck(settings.jokersWild);
  const deck     = shuffle(rawDeck, options.rng);
  const handSize = settings.handSize ?? (numPlayers === 2 ? 13 : 7);

  const players = playerNames.map((name, i) => ({
    id:         i === 0 ? 'human' : `ai-${i}`,
    name,
    isHuman:    i === 0,
    hand:       [],
    melds:      [],
    score:      0,
    roundScore: 0,
    hasMelded:  false,  // reset each round; used for minFirstMeld + firstMeldOutBonus
  }));

  for (let i = 0; i < handSize; i++) {
    for (const p of players) p.hand.push(deck.pop());
  }

  return {
    players,
    stock:         deck,
    discard:       [deck.pop()],
    currentPlayer: 0,
    phase:         'draw', // 'draw' | 'play' | 'roundOver' | 'gameOver'
    dealer:        numPlayers - 1,
    scoreHistory:  [],
    winner:        null,
    log:           [],
    handSize,
    settings,
    wentOutOnFirstMeld: false, // set in playMeld when player goes out on first meld
  };
}

function topOfDiscard(game) {
  return game.discard[game.discard.length - 1];
}

// Draw top of stock.
function drawFromStock(game) {
  if (game.phase !== 'draw') return { error: 'Not draw phase' };
  if (game.stock.length === 0) return endRound(game, null, 'stockEmpty');
  const card = game.stock.pop();
  game.players[game.currentPlayer].hand.push(card);
  game.phase    = 'play';
  game.lastDrawn = { source: 'stock', cards: [card], targetCard: card };
  pushLog(game, `${game.players[game.currentPlayer].name} drew from the deck.`);
  return { taken: [card] };
}

// Draw from discard pile at `index` (0=bottom of fan, length-1=top).
// All cards from index to top are taken.
function drawFromDiscard(game, index) {
  if (game.phase !== 'draw') return { error: 'Not draw phase' };
  if (index < 0 || index >= game.discard.length) return { error: 'Invalid discard index' };
  const taken = game.discard.splice(index);
  game.players[game.currentPlayer].hand.push(...taken);
  game.phase    = 'play';
  game.lastDrawn = { source: 'discard', cards: taken, targetCard: taken[0] };
  pushLog(game, `${game.players[game.currentPlayer].name} took ${taken.length} from the discard.`);
  return { taken, targetCard: taken[0] };
}

// Play a meld. cardIds = array of card ids from current player's hand.
function playMeld(game, cardIds) {
  if (game.phase !== 'play') return { error: 'Not play phase' };
  const { settings } = game;
  const player = game.players[game.currentPlayer];
  const cards  = cardIds.map(id => player.hand.find(c => c.id === id)).filter(Boolean);
  if (cards.length !== cardIds.length) return { error: 'Some cards not in hand' };
  if (!isValidMeld(cards, settings.acesHigh, settings.deuceWild)) return { error: 'Invalid meld' };

  // Minimum first-meld value check
  if (!player.hasMelded && settings.minFirstMeld > 0) {
    const meldValue = cards.reduce((s, c) => s + cardValue(c, settings.queenOfHeartsBonus), 0);
    if (meldValue < settings.minFirstMeld) {
      return { error: `First meld must be worth at least ${settings.minFirstMeld} pts (these are worth ${meldValue})` };
    }
  }

  const wasFirstMeld = player.melds.length === 0;
  let arranged = cards;
  if (isValidRun(cards, settings.acesHigh, settings.deuceWild)) arranged = arrangeRun(cards, settings.acesHigh, settings.deuceWild);
  player.melds.push(arranged);
  player.hasMelded = true;
  player.hand = player.hand.filter(c => !cardIds.includes(c.id));
  pushLog(game, `${player.name} laid down a ${meldType(arranged, settings.acesHigh, settings.deuceWild)}.`);
  if (player.hand.length === 0) {
    game.wentOutOnFirstMeld = wasFirstMeld;
    return endRound(game, game.currentPlayer, 'wentOut');
  }
  return { ok: true };
}

// Lay off a single card on an existing meld (any player's, or own-only per setting).
function playLayOff(game, cardId, targetPlayerIdx, meldIdx) {
  if (game.phase !== 'play') return { error: 'Not play phase' };
  const { settings } = game;

  if (!settings.layoffAnyMeld && targetPlayerIdx !== game.currentPlayer) {
    return { error: "You can only lay off on your own melds with current settings" };
  }

  const player = game.players[game.currentPlayer];
  const card   = player.hand.find(c => c.id === cardId);
  if (!card) return { error: 'Card not in hand' };
  const target = game.players[targetPlayerIdx];
  const meld   = target.melds[meldIdx];
  if (!meld) return { error: 'Meld not found' };
  const newMeld = tryLayOff(card, meld, settings.acesHigh, settings.deuceWild);
  if (!newMeld) return { error: 'Card does not extend meld' };
  target.melds[meldIdx] = newMeld;
  player.hand = player.hand.filter(c => c.id !== cardId);
  // Track lay-off credit: card.id → layerOffPlayerIdx
  target.melds[meldIdx]._layoffs = {
    ...(meld._layoffs || {}),
    [card.id]: game.currentPlayer,
  };
  pushLog(game, `${player.name} laid off the ${cardLabel(card)} on ${target.name}'s meld.`);
  if (player.hand.length === 0) {
    return endRound(game, game.currentPlayer, 'wentOut');
  }
  return { ok: true };
}

// Discard a card (ends the turn).
function discardCard(game, cardId) {
  if (game.phase !== 'play') return { error: 'Not play phase' };
  const { settings } = game;
  const player = game.players[game.currentPlayer];
  const card   = player.hand.find(c => c.id === cardId);
  if (!card) return { error: 'Card not in hand' };

  // Must meld/lay-off the bottom drawn card first (if setting is on)
  if (settings.mustMeldDrawnCard && game.lastDrawn?.source === 'discard') {
    const drawnBottom = game.lastDrawn.targetCard;
    if (player.hand.some(c => c.id === drawnBottom.id)) {
      return { error: `Must meld or lay off the ${cardLabel(drawnBottom)} before discarding` };
    }
  }

  player.hand = player.hand.filter(c => c.id !== cardId);
  game.discard.push(card);
  pushLog(game, `${player.name} discarded the ${cardLabel(card)}.`);
  if (player.hand.length === 0) {
    return endRound(game, game.currentPlayer, 'wentOut');
  }
  game.currentPlayer = (game.currentPlayer + 1) % game.players.length;
  game.phase    = 'draw';
  game.lastDrawn = null;
  if (game.stock.length === 0) {
    return endRound(game, null, 'stockEmpty');
  }
  return { ok: true };
}

function endRound(game, goneOut, reason) {
  game.phase = 'roundOver';
  const { settings } = game;
  const qoh = settings.queenOfHeartsBonus;
  const roundScores = game.players.map(() => 0);

  // Score melds (with layoff attribution)
  for (let i = 0; i < game.players.length; i++) {
    const p = game.players[i];
    for (const meld of p.melds) {
      const layoffs = meld._layoffs || {};
      for (const c of meld) {
        const credit = layoffs[c.id] != null ? layoffs[c.id] : i;
        roundScores[credit] += cardValue(c, qoh);
      }
    }
    // Penalty for cards left in hand
    roundScores[i] -= p.hand.reduce((s, c) => s + cardValue(c, qoh), 0);
  }

  // First-meld-out bonus: +50 if player went out on their very first meld of the round
  if (settings.firstMeldOutBonus && reason === 'wentOut' && game.wentOutOnFirstMeld) {
    roundScores[goneOut] += 50;
  }

  for (let i = 0; i < game.players.length; i++) {
    game.players[i].roundScore = roundScores[i];
    game.players[i].score     += roundScores[i];
  }
  game.scoreHistory.push({ scores: roundScores, goneOut, reason });

  const max = Math.max(...game.players.map(p => p.score));
  if (max >= settings.winScore) {
    game.winner = game.players.find(p => p.score === max);
    game.phase  = 'gameOver';
  }

  pushLog(game, reason === 'wentOut'
    ? `${game.players[goneOut].name} went out! Round over.`
    : 'Stock empty. Round over.');
  return { ok: true, roundOver: true };
}

// Begin a new round: re-deal, advance dealer, preserve scores + settings.
function startNewRound(game) {
  const { settings, handSize } = game;
  const useTwo  = game.players.length >= 3 && settings.twoDecks3plus;
  const rawDeck = useTwo
    ? [...createDeck(settings.jokersWild), ...createDeck(settings.jokersWild)]
    : createDeck(settings.jokersWild);
  const deck = shuffle(rawDeck);

  for (const p of game.players) {
    p.hand      = [];
    p.melds     = [];
    p.roundScore = 0;
    p.hasMelded = false;
  }
  game.wentOutOnFirstMeld = false;

  for (let i = 0; i < handSize; i++) {
    for (const p of game.players) p.hand.push(deck.pop());
  }
  game.stock    = deck;
  game.discard  = [game.stock.pop()];
  game.dealer   = (game.dealer + 1) % game.players.length;
  game.currentPlayer = (game.dealer + 1) % game.players.length;
  game.phase    = 'draw';
  game.lastDrawn = null;
  pushLog(game, `New round. ${game.players[game.currentPlayer].name} to start.`);
}

// ---------- Misc ----------

function cardLabel(card) {
  if (card.isJoker) return '🃏 Joker';
  return `${card.rank}${card.suit}`;
}

function pushLog(game, msg) {
  game.log.push({ msg, at: Date.now() });
  if (game.log.length > 50) game.log.shift();
}

function sortHand(hand) {
  return [...hand].sort((a, b) => {
    if (a.isJoker && b.isJoker) return 0;
    if (a.isJoker) return 1;
    if (b.isJoker) return -1;
    const suitOrder = ['♠', '♥', '♣', '♦'];
    const sa = suitOrder.indexOf(a.suit);
    const sb = suitOrder.indexOf(b.suit);
    if (sa !== sb) return sa - sb;
    return rankIndex(a.rank) - rankIndex(b.rank);
  });
}

// Expose everything on window for other scripts + React components
if (typeof window !== 'undefined') {
  window.RummyGame = {
    DEFAULT_SETTINGS,
    createGame, createDeck, shuffle, createCard, createJoker,
    cardValue, isRed, rankIndex, isWild,
    isValidSet, isValidRun, isValidMeld, arrangeRun, meldType, tryLayOff,
    topOfDiscard, drawFromStock, drawFromDiscard,
    playMeld, playLayOff, discardCard, startNewRound,
    cardLabel, sortHand,
  };
}
