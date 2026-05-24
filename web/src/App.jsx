// ============================================================
// App — orchestrates the whole game (state, turns, AI, animations)
// ============================================================

const { useState, useEffect, useRef, useLayoutEffect, useCallback } = React;

function App() {
  const [game, setGame]                   = useState(null);
  const [settings, setSettings]           = useState({ ...window.RummyGame.DEFAULT_SETTINGS });
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [selected, setSelected]           = useState([]);      // card ids currently selected
  const [speeches, setSpeeches]           = useState({});      // { playerIdx: 'text' }
  const [toast, setToast]                 = useState(null);
  const [aiTurnRunning, setAiTurnRunning] = useState(false);
  const [showScoreboard, setShowScoreboard] = useState(false);
  const [undoSnapshot, setUndoSnapshot]   = useState(null);  // saved before drawFromDiscard
  const mascotsRef = useRef([null]);      // index 0 = human (no mascot)

  // Spread the current mutated game object into React state to trigger a re-render.
  // IMPORTANT: must use the closure-captured `game` reference (not the functional-updater
  // `g` arg) because the engine mutates game in-place and the functional updater would
  // spread the previous React-state snapshot, which has stale primitive fields like
  // currentPlayer and phase after any earlier refresh() call.
  const refresh = () => setGame(game ? { ...game } : null);

  // ---------- Game lifecycle ----------
  const startGame = useCallback((numOpponents) => {
    const shuffledMascots = window.MASCOTS.slice().sort(() => Math.random() - 0.5);
    const picked          = shuffledMascots.slice(0, numOpponents);
    const playerNames     = ['You', ...picked.map(m => m.name)];
    const newGame         = window.RummyGame.createGame(playerNames, { settings });
    mascotsRef.current    = [null, ...picked];
    setGame(newGame);
    setSelected([]);
    setSpeeches({});
    setShowScoreboard(false);
    setAiTurnRunning(false);
    // Each AI says hi
    setTimeout(() => {
      const greetings = {};
      picked.forEach((m, i) => { greetings[i + 1] = window.pickLine(m, 'greet'); });
      setSpeeches(greetings);
      setTimeout(() => setSpeeches({}), 2200);
    }, 600);
  }, [settings]);

  // ---------- Speech helper ----------
  const sayFor = (playerIdx, key, duration = 1800) => {
    const mascot = mascotsRef.current[playerIdx];
    if (!mascot) return;
    const line = window.pickLine(mascot, key);
    if (!line) return;
    setSpeeches(s => ({ ...s, [playerIdx]: line }));
    setTimeout(() => {
      setSpeeches(s => {
        const next = { ...s };
        if (next[playerIdx] === line) delete next[playerIdx];
        return next;
      });
    }, duration);
  };

  // ---------- Toast ----------
  const showToast = (msg, kind = 'info') => {
    setToast({ msg, kind });
    setTimeout(() => setToast(null), 2200);
  };

  // ---------- Human actions ----------
  const onStockClick = () => {
    if (!game || game.currentPlayer !== 0 || game.phase !== 'draw') return;
    setUndoSnapshot(null); // stock draws can't be undone
    const result = window.RummyGame.drawFromStock(game);
    if (result.error) return showToast(result.error, 'error');
    if (result.roundOver) { finishRound(); return; }
    refresh();
  };

  const onDiscardClick = (idx) => {
    if (!game || game.currentPlayer !== 0 || game.phase !== 'draw') return;
    // Snapshot state before the draw so the player can undo if they get stuck
    const snapshot = {
      hand:      game.players[0].hand.map(c => ({ ...c })),
      discard:   game.discard.map(c => ({ ...c })),
      lastDrawn: game.lastDrawn,
    };
    const result = window.RummyGame.drawFromDiscard(game, idx);
    if (result.error) return showToast(result.error, 'error');
    setUndoSnapshot(snapshot);
    refresh();
  };

  const onUndoDraw = () => {
    if (!undoSnapshot || !game) return;
    // Restore player's hand and discard pile to pre-draw state
    game.players[0].hand = undoSnapshot.hand;
    game.discard         = undoSnapshot.discard;
    game.phase           = 'draw';
    game.lastDrawn       = undoSnapshot.lastDrawn;
    setUndoSnapshot(null);
    setSelected([]);
    refresh();
  };

  const onCardClick = (cardId) => {
    if (!game || game.currentPlayer !== 0 || game.phase !== 'play') return;
    setSelected(sel =>
      sel.includes(cardId) ? sel.filter(x => x !== cardId) : [...sel, cardId]
    );
  };

  const onMeldSelected = () => {
    if (selected.length < 3) return;
    const result = window.RummyGame.playMeld(game, selected);
    if (result.error) return showToast(result.error, 'error');
    setSelected([]);
    setUndoSnapshot(null); // committed — can't go back
    if (result.roundOver) { finishRound(); return; }
    refresh();
  };

  const onLayoffMeld = (targetPlayerIdx, meldIdx) => {
    if (selected.length !== 1) return;
    const result = window.RummyGame.playLayOff(game, selected[0], targetPlayerIdx, meldIdx);
    if (result.error) return showToast(result.error, 'error');
    setSelected([]);
    setUndoSnapshot(null); // committed — can't go back
    if (result.roundOver) { finishRound(); return; }
    refresh();
  };

  const onDiscardSelected = () => {
    if (selected.length !== 1) return;
    const result = window.RummyGame.discardCard(game, selected[0]);
    if (result.error) return showToast(result.error, 'error');
    setSelected([]);
    setUndoSnapshot(null); // turn is over — can't go back
    if (result.roundOver) { finishRound(); return; }
    refresh();
  };

  // ---------- Round management ----------
  const finishRound = () => {
    setSelected([]);
    setSpeeches({});
    setUndoSnapshot(null);
    setTimeout(() => setShowScoreboard(true), 700);
    refresh();
  };

  const nextRound = () => {
    window.RummyGame.startNewRound(game);
    setSelected([]);
    setSpeeches({});
    setUndoSnapshot(null);
    setShowScoreboard(false);
    setAiTurnRunning(false);
    refresh();
  };

  const newGame = () => {
    setGame(null);
    setSelected([]);
    setSpeeches({});
    setUndoSnapshot(null);
    setShowScoreboard(false);
    setAiTurnRunning(false);
  };

  // ---------- AI turn ----------
  useEffect(() => {
    if (!game) return;
    if (game.phase !== 'draw') return; // only fire at the start of a draw phase
    if (game.currentPlayer === 0) return; // human's turn
    if (aiTurnRunning) return;
    setAiTurnRunning(true);
    runAITurn(game.currentPlayer);
  // aiTurnRunning is intentionally in deps: when it flips false after an AI turn,
  // the effect must re-check whether the *next* player is also an AI (needed for
  // 3- and 4-player games where two AIs take turns back-to-back).
  }, [game?.currentPlayer, game?.phase, aiTurnRunning]);

  const wait = (ms) => new Promise(res => setTimeout(res, ms));

  async function runAITurn(aiIdx) {
    // try/finally guarantees setAiTurnRunning(false) always fires — even if a JS
    // error occurs mid-turn — so the game can never permanently freeze.
    try {
      await wait(700);
      if (game.phase !== 'draw') return;

      // — Draw —
      const drawDecision = window.RummyAI.decideDraw(aiIdx, game);
      if (drawDecision.source === 'discard') {
        const r = window.RummyGame.drawFromDiscard(game, drawDecision.index);
        if (r.error) {
          const sr = window.RummyGame.drawFromStock(game); // fallback to stock
          if (sr.roundOver) { finishRound(); return; }
        }
      } else {
        const r = window.RummyGame.drawFromStock(game);
        if (r.roundOver) { finishRound(); return; }
      }
      sayFor(aiIdx, 'draw');
      refresh();
      await wait(900);

      // — Melds —
      const meldsToPlay = window.RummyAI.decideMelds(aiIdx, game);
      for (const meldIds of meldsToPlay) {
        const r = window.RummyGame.playMeld(game, meldIds);
        if (!r.error) {
          sayFor(aiIdx, 'meld');
          refresh();
          if (r.roundOver) { finishRound(); return; }
          await wait(700);
        }
      }

      // — Lay offs —
      const acesHigh = game.settings?.acesHigh ?? false;
      let layoffsDone = 0;
      while (layoffsDone < 20) {
        const player  = game.players[aiIdx];
        const layoffs = window.RummyAI.findLayOffs(player.hand, game.players, acesHigh);
        if (layoffs.length === 0) break;
        const lo = layoffs[0];
        const r  = window.RummyGame.playLayOff(game, lo.cardId, lo.targetPlayerIdx, lo.meldIdx);
        if (r.error) break;
        sayFor(aiIdx, 'layoff');
        refresh();
        if (r.roundOver) { finishRound(); return; }
        await wait(500);
        layoffsDone++;
      }

      // — Discard —
      await wait(300);
      if (game.players[aiIdx].hand.length === 0) return;

      // Try AI's preferred card first
      let discarded = false;
      const discardId = window.RummyAI.decideDiscard(aiIdx, game);
      console.log('[AI] discard attempt', discardId, 'phase=', game.phase, 'cp=', game.currentPlayer);
      if (discardId) {
        const r = window.RummyGame.discardCard(game, discardId);
        console.log('[AI] discardCard result', r, '→ phase=', game.phase, 'cp=', game.currentPlayer);
        if (!r.error) {
          sayFor(aiIdx, 'discard', 1200);
          refresh();
          if (r.roundOver) { finishRound(); return; }
          discarded = true;
        }
      }

      // Fallback: try every card in hand until one is accepted by the engine.
      if (!discarded) {
        console.log('[AI] primary discard failed, trying fallback over', game.players[aiIdx].hand.length, 'cards');
        for (const c of [...game.players[aiIdx].hand]) {
          const r = window.RummyGame.discardCard(game, c.id);
          if (!r.error) {
            console.log('[AI] fallback discard succeeded', c.id, '→ phase=', game.phase, 'cp=', game.currentPlayer);
            refresh();
            if (r.roundOver) { finishRound(); return; }
            discarded = true;
            break;
          }
        }
      }

      // Last resort: bypass engine and force-advance the turn.
      if (!discarded && game.players[aiIdx].hand.length > 0) {
        console.warn('[AI] ALL discards failed — force-advancing turn');
        const card = game.players[aiIdx].hand[0];
        game.players[aiIdx].hand = game.players[aiIdx].hand.filter(c => c.id !== card.id);
        game.discard.push(card);
        game.currentPlayer = (game.currentPlayer + 1) % game.players.length;
        game.phase         = 'draw';
        game.lastDrawn     = null;
        refresh();
      }

      console.log('[AI] turn end → phase=', game.phase, 'cp=', game.currentPlayer);
    } catch (err) {
      console.error('[AI] Unexpected error in runAITurn:', err);
      // Emergency: advance past the stuck play phase so the game can recover
      try {
        if (game.phase === 'play') {
          if (game.players[aiIdx]?.hand?.length > 0) {
            const card = game.players[aiIdx].hand[0];
            game.players[aiIdx].hand = game.players[aiIdx].hand.filter(c => c.id !== card.id);
            game.discard.push(card);
          }
          game.currentPlayer = (game.currentPlayer + 1) % game.players.length;
          game.phase         = 'draw';
          game.lastDrawn     = null;
        }
      } catch (_) { /* ignore */ }
      refresh();
    } finally {
      setAiTurnRunning(false);
    }
  }

  // ---------- Compute UI state ----------
  const human         = game?.players[0];
  const isHumanTurn   = game?.currentPlayer === 0;
  const isPlayPhase   = game?.phase === 'play';
  const acesHigh      = game?.settings?.acesHigh   ?? false;
  const deuceWild     = game?.settings?.deuceWild  ?? false;
  const sortedHand    = human ? window.RummyGame.sortHand(human.hand) : [];

  // Which melds can the selected single card lay off on?
  let layoffTargets = [];
  if (game && isHumanTurn && isPlayPhase && selected.length === 1) {
    const card = human.hand.find(c => c.id === selected[0]);
    if (card) {
      const anyMeld = game.settings?.layoffAnyMeld ?? true;
      for (let pi = 0; pi < game.players.length; pi++) {
        if (!anyMeld && pi !== 0) continue; // restrict to own melds
        const p = game.players[pi];
        for (let mi = 0; mi < p.melds.length; mi++) {
          if (window.RummyGame.tryLayOff(card, p.melds[mi], acesHigh, deuceWild)) {
            layoffTargets.push({ playerIdx: pi, meldIdx: mi });
          }
        }
      }
    }
  }

  const selectedCards      = selected.map(id => human?.hand.find(c => c.id === id)).filter(Boolean);
  const selectionIsValidMeld = game && window.RummyGame.isValidMeld(selectedCards, acesHigh, deuceWild);

  // mustMeldFirst: player drew from discard and the bottom card is still in their hand
  const mustMeldFirst = !!(
    game?.settings?.mustMeldDrawnCard
    && game?.lastDrawn?.source === 'discard'
    && human?.hand?.some(c => c.id === game?.lastDrawn?.targetCard?.id)
  );
  const mustMeldCard = mustMeldFirst ? game.lastDrawn.targetCard : null;

  const canDiscard = game && isHumanTurn && isPlayPhase && selected.length === 1
    && !mustMeldFirst;

  // ---------- FLIP card animations ----------
  const prevPositions = useRef({});
  const rafWorks      = useRef(null);
  useEffect(() => {
    let fired = false;
    const handle = requestAnimationFrame(() => { fired = true; });
    const timer = setTimeout(() => {
      rafWorks.current = fired;
      cancelAnimationFrame(handle);
    }, 200);
    return () => { clearTimeout(timer); cancelAnimationFrame(handle); };
  }, []);
  useLayoutEffect(() => {
    if (!game) return;
    const cards = document.querySelectorAll('[data-card-id]');
    const newPositions = {};
    cards.forEach(el => {
      const id   = el.dataset.cardId;
      const rect = el.getBoundingClientRect();
      newPositions[id] = { left: rect.left, top: rect.top };
      if (rafWorks.current === false) return;
      const prev = prevPositions.current[id];
      if (prev) {
        const dx = prev.left - rect.left;
        const dy = prev.top  - rect.top;
        if (Math.abs(dx) > 4 || Math.abs(dy) > 4) {
          try {
            el.animate(
              [
                { transform: `translate(${dx}px,${dy}px) scale(1.08)`, zIndex: 999, offset: 0 },
                { transform: 'translate(0,0) scale(1)',                              offset: 1 },
              ],
              { duration: 460, easing: 'cubic-bezier(.34,1.56,.64,1)', fill: 'none' }
            );
          } catch (e) { /* ignore */ }
        }
      }
    });
    prevPositions.current = newPositions;
  });

  // ---------- Render ----------
  if (!game) {
    return (
      <React.Fragment>
        <StartScreen onStart={startGame} onOpenSettings={() => setShowSettingsModal(true)} />
        {showSettingsModal && (
          <SettingsModal
            settings={settings}
            onChange={setSettings}
            onClose={() => setShowSettingsModal(false)}
          />
        )}
      </React.Fragment>
    );
  }

  return (
    <div className="dd-stage">
      <ScalingStage>
        <div className="dd-table">
          {/* HEADER */}
          <div className="dd-header">
            <div className="dd-logo">
              <HeartGlyph />
              <span>Doki Doki Rummy</span>
            </div>
            <div className="dd-header-scores">
              {game.players.map((p, idx) => {
                const m = mascotsRef.current[idx];
                return (
                  <div key={p.id} className={`dd-score-pill ${game.currentPlayer === idx ? 'is-active' : ''}`}>
                    <div className="dd-avatar">
                      {idx === 0 ? window.PLAYER_AVATAR : m?.svg}
                    </div>
                    <span style={{ fontFamily: 'var(--font-rounded)', fontSize: 13 }}>{p.name}</span>
                    <span className="dd-score-num">{p.score}</span>
                  </div>
                );
              })}
            </div>
            <div className="dd-header-actions">
              <button className="dd-btn dd-btn--small dd-btn--ghost" onClick={newGame}>
                New Game
              </button>
            </div>
          </div>

          {/* TABLE */}
          <Table
            game={game}
            mascots={mascotsRef.current}
            speeches={speeches}
            selected={selected}
            layoffTargets={layoffTargets}
            onCardClick={onCardClick}
            onStockClick={onStockClick}
            onDiscardClick={onDiscardClick}
            onPlayerMeldClick={(mi) => onLayoffMeld(0, mi)}
            onOpponentMeldClick={(pi, mi) => onLayoffMeld(pi, mi)}
          />

          {/* PLAYER AREA */}
          <div className="dd-player-area">
            <div className="dd-hand-wrap">
              <div className="dd-hand" data-hand-of="human">
                {sortedHand.map((c, idx) => {
                  const isSel = selected.includes(c.id);
                  return (
                    <div
                      key={c.id}
                      data-card-id={c.id}
                      style={{
                        marginLeft: idx === 0 ? 0 : -28,
                        transform: `rotate(${(idx - sortedHand.length / 2) * 1.5}deg) translateY(${isSel ? -24 : 0}px)`,
                        transition: 'transform 280ms cubic-bezier(.34,1.56,.64,1)',
                      }}
                    >
                      <Card
                        card={c}
                        selected={isSel}
                        onClick={isHumanTurn && isPlayPhase ? () => onCardClick(c.id) : null}
                      />
                    </div>
                  );
                })}
              </div>
            </div>

            <ActionPanel
              game={game}
              human={human}
              isHumanTurn={isHumanTurn}
              isPlayPhase={isPlayPhase}
              selected={selected}
              selectionIsValidMeld={selectionIsValidMeld}
              layoffTargets={layoffTargets}
              canDiscard={canDiscard}
              mustMeldFirst={mustMeldFirst}
              mustMeldCard={mustMeldCard}
              undoSnapshot={undoSnapshot}
              onMeldSelected={onMeldSelected}
              onDiscardSelected={onDiscardSelected}
              onClearSelection={() => setSelected([])}
              onUndoDraw={onUndoDraw}
            />
          </div>
        </div>
      </ScalingStage>

      {/* Toast */}
      {toast && (
        <div className={`dd-toast ${toast.kind === 'error' ? 'dd-toast--error' : ''}`}>
          {toast.msg}
        </div>
      )}

      {/* Scoreboard / round-end */}
      {showScoreboard && (
        <Scoreboard
          game={game}
          onNextRound={nextRound}
          onNewGame={newGame}
        />
      )}
    </div>
  );
}

// ============================================================
// ScalingStage — scales the 1440×900 canvas to fit any viewport
// ============================================================
function ScalingStage({ children }) {
  const [scale, setScale] = useState(1);
  useEffect(() => {
    const update = () => {
      const sx = window.innerWidth  / 1440;
      const sy = window.innerHeight / 900;
      setScale(Math.min(sx, sy, 1.2));
    };
    update();
    window.addEventListener('resize', update);
    return () => window.removeEventListener('resize', update);
  }, []);
  return (
    <div style={{
      position: 'absolute',
      top: '50%', left: '50%',
      width: 1440, height: 900,
      transform: `translate(-50%,-50%) scale(${scale})`,
      transformOrigin: 'center center',
    }}>
      {children}
    </div>
  );
}

// ============================================================
// ActionPanel — context-sensitive controls during human turn
// ============================================================
function ActionPanel({
  game, human, isHumanTurn, isPlayPhase, selected,
  selectionIsValidMeld, layoffTargets, canDiscard,
  mustMeldFirst, mustMeldCard,
  undoSnapshot, onUndoDraw,
  onMeldSelected, onDiscardSelected, onClearSelection,
}) {
  if (!isHumanTurn) {
    return (
      <div className="dd-actions">
        <span className="eyebrow">Waiting…</span>
        <div className="dd-actions-hint">
          {game.players[game.currentPlayer].name} is thinking ✨
        </div>
      </div>
    );
  }
  if (game.phase === 'draw') {
    return (
      <div className="dd-actions">
        <span className="eyebrow">Draw a card</span>
        <div className="dd-actions-hint">
          Click the <strong>deck</strong> for a fresh card, or click any card in the <strong>discard</strong> pile to grab it (and everything above it).
        </div>
      </div>
    );
  }
  if (game.phase === 'play') {
    const selCount = selected.length;
    return (
      <div className="dd-actions">
        <span className="eyebrow">Your move</span>

        {/* mustMeldFirst hint */}
        {mustMeldFirst && mustMeldCard && (
          <div className="dd-actions-hint" style={{ color: 'var(--dd-cherry)', fontWeight: 600 }}>
            Must meld or lay off the {mustMeldCard.rank}{mustMeldCard.suit} before discarding ♥
          </div>
        )}

        {selCount === 0 && !mustMeldFirst && (
          <div className="dd-actions-hint">
            Tap cards to select. Group 3+ to <strong>lay down</strong> a meld, or pick one to <strong>discard</strong>.
          </div>
        )}
        {selCount === 1 && layoffTargets.length > 0 && (
          <div className="dd-actions-hint">
            Pulsing melds can take this card — click one to lay off ♥
          </div>
        )}
        {selCount >= 2 && !selectionIsValidMeld && (
          <div className="dd-actions-hint" style={{ color: 'var(--dd-mute)' }}>
            Not a valid meld yet — need 3+ same rank, or 3+ same suit in a row.
          </div>
        )}
        {selCount >= 3 && selectionIsValidMeld && (
          <div className="dd-actions-hint" style={{ color: 'var(--dd-matcha)' }}>
            Valid meld! ✨
          </div>
        )}

        <div className="dd-actions-row" style={{ flexWrap: 'wrap', gap: 8 }}>
          <button
            className="dd-btn dd-btn--matcha"
            disabled={!selectionIsValidMeld}
            onClick={onMeldSelected}
          >
            ★ Lay Down{selCount >= 3 && selectionIsValidMeld ? ` (${selCount})` : ''}
          </button>
          <button
            className="dd-btn dd-btn--primary"
            disabled={!canDiscard}
            onClick={onDiscardSelected}
          >
            Discard
          </button>
          {undoSnapshot && (
            <button
              className="dd-btn dd-btn--ghost"
              onClick={onUndoDraw}
              title="Put the cards back and draw differently"
            >
              ↩ Undo Draw
            </button>
          )}
        </div>
        {selCount > 0 && (
          <button className="dd-btn dd-btn--ghost dd-btn--small" onClick={onClearSelection}>
            Clear selection
          </button>
        )}
      </div>
    );
  }
  return null;
}

// ============================================================
// HeartGlyph — animated sticker heart in the header
// ============================================================
function HeartGlyph() {
  return (
    <svg className="dd-logo-heart" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M 50 86 Q 12 60 12 36 Q 12 18 30 18 Q 42 18 50 30 Q 58 18 70 18 Q 88 18 88 36 Q 88 60 50 86 Z"
        fill="#FF3D8B"
        stroke="#14110D"
        strokeWidth="6"
        strokeLinejoin="round"
      />
      <ellipse cx="36" cy="38" rx="5" ry="8" fill="#FFF" opacity="0.6" />
    </svg>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
