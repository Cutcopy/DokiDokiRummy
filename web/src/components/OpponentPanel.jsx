// ============================================================
// OpponentPanel — shows AI avatar, name, score, hand, melds, speech
// ============================================================

function OpponentPanel({ player, mascot, isCurrent, speech }) {
  const handCount = player.hand.length;
  const miniCount = Math.min(handCount, 13);

  // ---- Speech bubble with enter + leave animations ----
  // `shown`   — text currently rendered in the DOM (null = no bubble)
  // `leaving` — true while the exit animation is playing
  // `bubbleKey` — increments on every new speech so the enter animation
  //               always replays even if the text is the same
  const [shown,     setShown]     = React.useState(null);
  const [leaving,   setLeaving]   = React.useState(false);
  const [bubbleKey, setBubbleKey] = React.useState(0);
  const leaveTimer  = React.useRef(null);
  const shownRef    = React.useRef(null); // readable inside effects without stale closures

  React.useEffect(() => {
    if (speech) {
      // New speech arriving — cancel any pending leave, show immediately
      if (leaveTimer.current) { clearTimeout(leaveTimer.current); leaveTimer.current = null; }
      shownRef.current = speech;
      setLeaving(false);
      setShown(speech);
      setBubbleKey(k => k + 1);
    } else if (shownRef.current) {
      // Speech removed — play exit animation for LEAVE_MS, then unmount
      const LEAVE_MS = 320;
      setLeaving(true);
      leaveTimer.current = setTimeout(() => {
        shownRef.current = null;
        setShown(null);
        setLeaving(false);
        leaveTimer.current = null;
      }, LEAVE_MS);
    }
  }, [speech]);

  // Cleanup on unmount
  React.useEffect(() => {
    return () => { if (leaveTimer.current) clearTimeout(leaveTimer.current); };
  }, []);

  return (
    <div className={`dd-opp ${isCurrent ? 'is-current' : ''}`} style={{ overflow: 'visible' }}>
      {shown && (
        <div
          className={`dd-bubble${leaving ? ' is-leaving' : ''}`}
          key={bubbleKey}
        >
          {shown}
        </div>
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
