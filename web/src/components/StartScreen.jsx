// ============================================================
// StartScreen — initial mode picker (heads-up vs 4-player)
// ============================================================

function StartScreen({ onStart, onOpenSettings }) {
  return (
    <div className="dd-modal-veil">
      <div className="dd-modal">
        <div style={{ textAlign: 'center', marginBottom: 8 }}>
          <span className="eyebrow">ドキドキ ・ EST. 2020</span>
        </div>
        <h1>Rummy 500</h1>
        <p className="lede">
          Stickers, melds, and a race to 500 points. Pick your table~
        </p>
        <div className="dd-mode-grid">
          <div className="dd-mode-card" onClick={() => onStart(1)}>
            <div className="dd-mode-card-avatars">
              <div className="dd-opp-avatar">{window.MASCOTS[0].svg}</div>
            </div>
            <h3>Heads-up</h3>
            <p>You vs. one mascot.<br />13 cards each, longer rounds.</p>
          </div>
          <div className="dd-mode-card" onClick={() => onStart(3)}>
            <div className="dd-mode-card-avatars">
              <div className="dd-opp-avatar">{window.MASCOTS[0].svg}</div>
              <div className="dd-opp-avatar">{window.MASCOTS[1].svg}</div>
              <div className="dd-opp-avatar">{window.MASCOTS[2].svg}</div>
            </div>
            <h3>Four at the Table</h3>
            <p>You + 3 mascots.<br />7 cards each, faster melds.</p>
          </div>
        </div>
        <div style={{ textAlign: 'center', margin: '4px 0 12px' }}>
          <button
            className="dd-btn dd-btn--ghost dd-btn--small"
            onClick={onOpenSettings}
            style={{ fontSize: 12 }}
          >
            ⚙ Settings
          </button>
        </div>

        <div style={{
          background: 'var(--dd-yuzu-tint)',
          border: '3px solid var(--dd-ink)',
          borderRadius: 'var(--r-md)',
          padding: '16px 20px',
          fontFamily: 'var(--font-rounded)',
          fontSize: 13,
          color: 'var(--dd-ink)',
          lineHeight: 1.5,
        }}>
          <strong style={{ fontFamily: 'var(--font-display)', fontSize: 18, display: 'block', marginBottom: 6 }}>
            How to play, quick~
          </strong>
          Each turn: <strong>draw</strong> (deck or discard pile),
          then <strong>meld</strong> (3+ same rank or 3+ same suit in a row),
          <strong> lay off</strong> on any meld on the table, and <strong>discard</strong>.
          Jokers wild ♥ Aces 1 or 15. First to <strong>500</strong> wins!
        </div>
      </div>
    </div>
  );
}

window.StartScreen = StartScreen;
