// ============================================================
// Rummy 500 — AI player logic (simple but functional)
// ============================================================
//
// Strategy:
//  - DRAW: take from discard pile only if doing so completes or extends a meld
//          AND satisfies the mustMeldDrawnCard rule if active.
//  - PLAY: find all valid melds in hand, lay them down. Lay off remaining cards.
//  - DISCARD: discard the highest-value card NOT part of a near-meld.
// ============================================================

// Destructure helpers from the game engine (loaded before this file).
// This makes them available even when Babel evaluates each file in its own scope.
const {
  rankIndex, isValidRun, isValidMeld, isValidSet, tryLayOff, cardValue, arrangeRun, isWild,
} = window.RummyGame;

// ---------- Combination finder ----------

function findBestMelds(hand, acesHigh = false, deuceWild = false) {
  const used = new Set();
  const melds = [];
  const candidates = enumerateMelds(hand, acesHigh, deuceWild);
  candidates.sort((a, b) => {
    const aVal = a.reduce((s, c) => s + cardValue(c), 0);
    const bVal = b.reduce((s, c) => s + cardValue(c), 0);
    return bVal - aVal;
  });
  for (const meld of candidates) {
    if (meld.some(c => used.has(c.id))) continue;
    for (const c of meld) used.add(c.id);
    melds.push(meld);
  }
  return melds;
}

function enumerateMelds(hand, acesHigh = false, deuceWild = false) {
  const results = [];
  const byRank = {};
  for (const c of hand) {
    if (isWild(c, deuceWild)) continue; // wilds don't form natural rank groups
    (byRank[c.rank] = byRank[c.rank] || []).push(c);
  }
  const wilds = hand.filter(c => isWild(c, deuceWild));

  // Sets of 3 or 4 (with optional wild fill)
  for (const rank in byRank) {
    const group = byRank[rank];
    if (group.length >= 3) results.push(group.slice(0, 4));
    if (group.length >= 2 && wilds.length >= 1) results.push([...group.slice(0, 2), wilds[0]]);
    if (group.length >= 1 && wilds.length >= 2) results.push([group[0], ...wilds.slice(0, 2)]);
  }

  // Runs: group by suit (exclude wilds)
  const bySuit = {};
  for (const c of hand) {
    if (isWild(c, deuceWild)) continue;
    (bySuit[c.suit] = bySuit[c.suit] || []).push(c);
  }
  for (const suit in bySuit) {
    const group = [...bySuit[suit]].sort((a, b) => rankIndex(a.rank) - rankIndex(b.rank));

    // Find consecutive runs (ace-low)
    let run = [];
    for (let i = 0; i < group.length; i++) {
      if (run.length === 0 || rankIndex(group[i].rank) === rankIndex(run[run.length - 1].rank) + 1) {
        run.push(group[i]);
      } else if (rankIndex(group[i].rank) === rankIndex(run[run.length - 1].rank)) {
        continue; // duplicate rank, skip
      } else {
        if (run.length >= 3) results.push([...run]);
        run = [group[i]];
      }
    }
    if (run.length >= 3) results.push([...run]);

    // Wild bridging a single gap
    if (wilds.length >= 1) {
      for (let i = 0; i < group.length - 1; i++) {
        for (let j = i + 1; j < group.length; j++) {
          const gap = rankIndex(group[j].rank) - rankIndex(group[i].rank);
          if (gap === 2) {
            const trio = [group[i], wilds[0], group[j]];
            if (isValidRun(trio, acesHigh, deuceWild)) results.push(trio);
          }
        }
      }
    }

    // Ace-high run (Q-K-A) — only when acesHigh setting is on
    if (acesHigh) {
      const hasAce = group.find(c => c.rank === 'A');
      const hasK   = group.find(c => c.rank === 'K');
      const hasQ   = group.find(c => c.rank === 'Q');
      if (hasAce && hasK && hasQ) {
        const aceRun = [hasQ, hasK, hasAce];
        if (isValidRun(aceRun, acesHigh, deuceWild)) results.push(aceRun);
      }
    }
  }

  // Deduplicate by sorted id set
  const seen   = new Set();
  const unique = [];
  for (const m of results) {
    const key = m.map(c => c.id).sort().join(',');
    if (!seen.has(key)) { seen.add(key); unique.push(m); }
  }
  return unique;
}

// Find all possible lay-offs from hand onto existing melds.
// Returns array of { cardId, targetPlayerIdx, meldIdx, value }.
function findLayOffs(hand, players, acesHigh = false, deuceWild = false) {
  const layoffs = [];
  for (const card of hand) {
    for (let pi = 0; pi < players.length; pi++) {
      const p = players[pi];
      for (let mi = 0; mi < p.melds.length; mi++) {
        const newMeld = tryLayOff(card, p.melds[mi], acesHigh, deuceWild);
        if (newMeld) {
          layoffs.push({ cardId: card.id, targetPlayerIdx: pi, meldIdx: mi, value: cardValue(card) });
          break; // one lay-off target per card
        }
      }
    }
  }
  return layoffs;
}

// ---------- AI decisions ----------

// Decide whether to take from discard. Returns { source, index? }.
function decideDraw(aiIdx, game) {
  const acesHigh  = game.settings?.acesHigh       ?? false;
  const deuceWild = game.settings?.deuceWild       ?? false;
  const mustMeld  = game.settings?.mustMeldDrawnCard ?? false;
  const player    = game.players[aiIdx];
  const top       = game.discard[game.discard.length - 1];
  if (!top) return { source: 'stock' };

  const hypothetical = [...player.hand, top];
  const meldsBefore  = findBestMelds(player.hand,  acesHigh, deuceWild).reduce((s, m) => s + m.length, 0);
  const meldsAfter   = findBestMelds(hypothetical, acesHigh, deuceWild).reduce((s, m) => s + m.length, 0);

  if (meldsAfter > meldsBefore) {
    // If mustMeldDrawnCard is on, the top card must actually be IN one of the new melds
    if (mustMeld) {
      const topInMeld = findBestMelds(hypothetical, acesHigh, deuceWild).some(m => m.some(c => c.id === top.id));
      if (!topInMeld) return { source: 'stock' };
    }
    return { source: 'discard', index: game.discard.length - 1 };
  }

  // Only try layoff-based draw if mustMeldDrawnCard is NOT required
  if (!mustMeld) {
    for (let pi = 0; pi < game.players.length; pi++) {
      for (const meld of game.players[pi].melds) {
        if (tryLayOff(top, meld, acesHigh, deuceWild)) {
          return { source: 'discard', index: game.discard.length - 1 };
        }
      }
    }
  }

  return { source: 'stock' };
}

// Find melds to play this turn. Returns array of meld card-id arrays.
function decideMelds(aiIdx, game) {
  const acesHigh     = game.settings?.acesHigh          ?? false;
  const deuceWild    = game.settings?.deuceWild          ?? false;
  const minFirstMeld = game.settings?.minFirstMeld       ?? 0;
  const qoh          = game.settings?.queenOfHeartsBonus ?? false;
  const player       = game.players[aiIdx];
  const allMelds     = findBestMelds(player.hand, acesHigh, deuceWild);

  if (allMelds.length === 0) return [];

  // If player hasn't melded yet this round and there's a minimum value, filter candidates
  if (!player.hasMelded && minFirstMeld > 0) {
    const validFirst = allMelds.filter(m =>
      m.reduce((s, c) => s + cardValue(c, qoh), 0) >= minFirstMeld
    );
    if (validFirst.length === 0) return [];
    return validFirst.map(m => m.map(c => c.id));
  }

  return allMelds.map(m => m.map(c => c.id));
}

// Decide what to discard. Returns card id or null.
function decideDiscard(aiIdx, game) {
  const mustMeld  = game.settings?.mustMeldDrawnCard ?? false;
  const deuceWild = game.settings?.deuceWild          ?? false;
  const player    = game.players[aiIdx];
  let candidates  = player.hand;

  // If mustMeldDrawnCard is active and bottom card is still in hand, don't try to discard it
  if (mustMeld && game.lastDrawn?.source === 'discard') {
    const drawnBottom = game.lastDrawn.targetCard;
    if (player.hand.some(c => c.id === drawnBottom?.id)) {
      candidates = candidates.filter(c => c.id !== drawnBottom.id);
    }
  }

  if (candidates.length === 0) candidates = player.hand;

  let best = null, bestScore = -Infinity;
  for (const c of candidates) {
    if (isWild(c, deuceWild)) continue; // never discard a wild
    let score = cardValue(c); // prefer discarding high-value dead cards
    const others = player.hand.filter(x => x.id !== c.id);
    // Pair / triplet — don't break it up
    const sameRank = others.filter(x => x.rank === c.rank).length;
    if (sameRank >= 1) score -= 8 * sameRank;
    // Partial run — don't break it up
    const nearby = others.filter(x => x.suit === c.suit && Math.abs(rankIndex(x.rank) - rankIndex(c.rank)) <= 2 && x.rank !== c.rank);
    score -= 4 * nearby.length;
    if (score > bestScore) { bestScore = score; best = c; }
  }
  // Fallback: first non-forbidden candidate
  if (!best) best = candidates[0];
  return best?.id;
}

if (typeof window !== 'undefined') {
  window.RummyAI = {
    findBestMelds, enumerateMelds, findLayOffs,
    decideDraw, decideMelds, decideDiscard,
  };
}
