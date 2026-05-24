// ============================================================
// Table — the main game board layout
// ============================================================

function Table({
  game, mascots, speeches, selected, layoffTargets,
  onCardClick, onStockClick, onDiscardClick, onPlayerMeldClick, onOpponentMeldClick,
}) {
  const human = game.players[0];
  const opponents = game.players.slice(1);

  return (
    <div className="dd-felt">
      {/* OPPONENTS ROW */}
      <div className="dd-zone dd-zone--opponents">
        {opponents.map((p, idx) => {
          const realIdx = idx + 1;
          const mascot = mascots[realIdx];
          const isCurrent = game.currentPlayer === realIdx;
          return (
            <div key={p.id} className="dd-opp-stack">
              <OpponentPanel
                player={p}
                mascot={mascot}
                isCurrent={isCurrent}
                speech={speeches[realIdx]}
              />
              <div className="dd-opp-melds-row">
                {p.melds.map((meld, mi) => {
                  const isTarget = layoffTargets?.some(t => t.playerIdx === realIdx && t.meldIdx === mi);
                  return (
                    <div
                      key={mi}
                      className={`dd-opp-meld ${isTarget ? 'is-layoff-target' : ''}`}
                      onClick={() => isTarget && onOpponentMeldClick(realIdx, mi)}
                      style={isTarget ? { cursor: 'pointer' } : {}}
                    >
                      {meld.map((c) => (
                        <Card key={c.id} card={c} size="sm" />
                      ))}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* CENTER ZONE — deck, turn banner, discard */}
      <div className="dd-zone dd-zone--center">
        <div /> {/* spacer */}

        {/* Deck */}
        <div className="dd-pile" style={{ position: 'relative' }}>
          <div className="dd-pile-stack" style={{ transform: 'rotate(-3deg)' }}>
            {game.stock.length > 0 ? (
              <React.Fragment>
                <Card faceDown decorative style={{ position: 'absolute', top: 3, left: 3 }} />
                <Card faceDown decorative style={{ position: 'absolute', top: 1, left: 1 }} />
                <Card
                  faceDown
                  onClick={game.phase === 'draw' && game.currentPlayer === 0 ? onStockClick : null}
                />
              </React.Fragment>
            ) : (
              <div style={{
                width: 'var(--card-w)', height: 'var(--card-h)',
                border: '3px dashed var(--dd-ink)', borderRadius: 12,
                opacity: 0.4, display: 'grid', placeItems: 'center',
                fontFamily: 'var(--font-rounded)', fontSize: 11, color: 'var(--dd-ink)',
                textAlign: 'center', padding: 4
              }}>empty</div>
            )}
            <div className="dd-deck-count">{game.stock.length}</div>
          </div>
          <div className="dd-pile-label">Deck</div>
        </div>

        {/* Turn banner */}
        <div style={{ display: 'grid', placeItems: 'center', minWidth: 240 }}>
          <TurnBanner game={game} mascot={mascots[game.currentPlayer]} />
        </div>

        {/* Discard fan */}
        <div className="dd-pile" style={{ width: 'auto' }}>
          <div className="dd-discard-fan">
            {game.discard.length === 0 ? (
              <div style={{
                width: 'var(--card-w)', height: 'var(--card-h)',
                border: '3px dashed var(--dd-ink)', borderRadius: 12,
                opacity: 0.4
              }} />
            ) : (
              game.discard.map((c, idx) => {
                const canTake = game.phase === 'draw' && game.currentPlayer === 0;
                const rot = -10 + (idx * 3);
                return (
                  <Card
                    key={c.id}
                    card={c}
                    onClick={canTake ? () => onDiscardClick(idx) : null}
                    style={{
                      transform: `rotate(${Math.max(-12, Math.min(12, rot))}deg)`,
                      zIndex: idx,
                    }}
                  />
                );
              })
            )}
          </div>
          <div className="dd-pile-label">Discard</div>
        </div>

        <div /> {/* spacer */}
      </div>

      {/* PLAYER'S OWN MELDS */}
      <div className="dd-zone dd-zone--player-melds">
        {human.melds.length === 0 ? (
          <div className="dd-meld-empty">
            Your melds will appear here ♥
          </div>
        ) : (
          human.melds.map((meld, mi) => {
            const isTarget = layoffTargets?.some(t => t.playerIdx === 0 && t.meldIdx === mi);
            return (
              <div
                key={mi}
                className={`dd-player-meld ${isTarget ? 'is-layoff-target' : ''}`}
                onClick={() => isTarget && onPlayerMeldClick(mi)}
              >
                {meld.map((c) => (
                  <Card key={c.id} card={c} size="md" />
                ))}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

function TurnBanner({ game, mascot }) {
  const player = game.players[game.currentPlayer];
  const isYou = player.isHuman;
  return (
    <div className="dd-turn-banner">
      <span className="eyebrow">{isYou ? 'YOUR TURN' : `${player.name.toUpperCase()}'S TURN`}</span>
      <span className="name">{isYou ? '♥ Go!' : (game.phase === 'draw' ? 'thinking…' : 'playing…')}</span>
    </div>
  );
}

window.Table = Table;
