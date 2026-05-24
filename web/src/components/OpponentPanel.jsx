// ============================================================
// OpponentPanel — shows AI avatar, name, score, hand, melds, speech
// ============================================================

function OpponentPanel({ player, mascot, isCurrent, speech }) {
  const handCount = player.hand.length;
  const miniCount = Math.min(handCount, 13);
  return (
    <div className={`dd-opp ${isCurrent ? 'is-current' : ''}`} style={{ overflow: 'visible' }}>
      {speech && (
        <div className="dd-bubble" key={speech}>{speech}</div>
      )}
      <div className="dd-opp-avatar" style={{ background: mascot.color }}>
        {mascot.svg}
      </div>
      <div className="dd-opp-info">
        <div className="dd-opp-name">{player.name}</div>
        <div className="dd-opp-meta">
          <span className="dd-opp-chip">♥ {player.score}</span>
          <span className="dd-opp-chip">{handCount} cards</span>
        </div>
        <div className="dd-opp-hand" aria-hidden="true">
          {Array.from({ length: miniCount }).map((_, i) => (
            <span key={i} className="mini-back" />
          ))}
        </div>
      </div>
    </div>
  );
}

window.OpponentPanel = OpponentPanel;
