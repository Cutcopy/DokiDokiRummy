// ============================================================
// SettingsModal — game rules configuration panel
// ============================================================

function SettingsModal({ settings, onChange, onClose }) {
  // Use functional updater so rapid changes don't clobber each other
  const set = (key, val) => onChange(prev => ({ ...prev, [key]: val }));

  return (
    <div className="dd-modal-veil" onClick={onClose}>
      <div
        className="dd-modal"
        style={{ maxWidth: 560, maxHeight: '88vh', overflowY: 'auto' }}
        onClick={e => e.stopPropagation()}
      >
        <div style={{ textAlign: 'center', marginBottom: 4 }}>
          <span className="eyebrow">Customize your game ✨</span>
        </div>
        <h2 style={{ marginBottom: 4 }}>Settings</h2>

        {/* ── Scoring ─────────────────────────────── */}
        <div className="dd-settings-section">
          <h3>Scoring</h3>

          <SettingRow label="Win Score" hint="First player to reach this total wins the game">
            <div className="dd-toggle-group">
              {[200, 300, 500, 1000].map(v => (
                <button
                  key={v}
                  className={`dd-toggle-btn ${settings.winScore === v ? 'is-active' : ''}`}
                  onClick={() => set('winScore', v)}
                >
                  {v}
                </button>
              ))}
            </div>
          </SettingRow>

          <SettingRow label="Queen of Hearts" hint="Q♥ is worth 40 pts instead of 10">
            <BinaryToggle
              value={settings.queenOfHeartsBonus}
              onChange={v => set('queenOfHeartsBonus', v)}
              falseLabel="10 pts"
              trueLabel="40 pts"
            />
          </SettingRow>

          <SettingRow label="First-meld bonus" hint="+50 pts for going out on your very first meld of a round">
            <BinaryToggle
              value={settings.firstMeldOutBonus}
              onChange={v => set('firstMeldOutBonus', v)}
            />
          </SettingRow>

          <SettingRow label="Min first meld" hint="Your first meld each round must be worth at least this many points">
            <div className="dd-toggle-group">
              {[0, 15, 30, 50].map(v => (
                <button
                  key={v}
                  className={`dd-toggle-btn ${settings.minFirstMeld === v ? 'is-active' : ''}`}
                  onClick={() => set('minFirstMeld', v)}
                >
                  {v === 0 ? 'None' : v}
                </button>
              ))}
            </div>
          </SettingRow>
        </div>

        {/* ── Rules ───────────────────────────────── */}
        <div className="dd-settings-section">
          <h3>Rules</h3>

          <SettingRow label="Starting hand" hint="Cards dealt to each player at round start (Auto: 13 for 2-player, 7 for 3–4)">
            <div className="dd-toggle-group">
              {[null, 5, 7, 10, 13].map(v => (
                <button
                  key={v ?? 'auto'}
                  className={`dd-toggle-btn ${settings.handSize === v ? 'is-active' : ''}`}
                  onClick={() => set('handSize', v)}
                >
                  {v === null ? 'Auto' : v}
                </button>
              ))}
            </div>
          </SettingRow>

          <SettingRow label="Aces" hint="Low only: A-2-3 only. High & Low: also Q-K-A runs">
            <BinaryToggle
              value={settings.acesHigh}
              onChange={v => set('acesHigh', v)}
              falseLabel="Low only"
              trueLabel="High & Low"
            />
          </SettingRow>

          <SettingRow label="Jokers wild" hint="Include jokers in the deck as wild cards">
            <BinaryToggle
              value={settings.jokersWild}
              onChange={v => set('jokersWild', v)}
            />
          </SettingRow>

          <SettingRow label="Deuces wild" hint="2s also act as wild cards in melds — they can substitute for any card in a run or set">
            <BinaryToggle
              value={settings.deuceWild}
              onChange={v => set('deuceWild', v)}
            />
          </SettingRow>

          <SettingRow
            label="Discard rule"
            hint="When drawing from the discard pile, the bottom card you took must be melded before you can discard"
          >
            <BinaryToggle
              value={settings.mustMeldDrawnCard}
              onChange={v => set('mustMeldDrawnCard', v)}
              falseLabel="Free"
              trueLabel="Must meld it"
            />
          </SettingRow>

          <SettingRow label="Lay off on" hint="Which melds on the table you can extend">
            <BinaryToggle
              value={settings.layoffAnyMeld}
              onChange={v => set('layoffAnyMeld', v)}
              falseLabel="Own only"
              trueLabel="Any meld"
            />
          </SettingRow>

          <SettingRow label="Two decks (3+ players)" hint="Use two shuffled decks when playing with 3 or 4 players">
            <BinaryToggle
              value={settings.twoDecks3plus}
              onChange={v => set('twoDecks3plus', v)}
            />
          </SettingRow>
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', marginTop: 24 }}>
          <button className="dd-btn dd-btn--primary" onClick={onClose}>
            Done ♥
          </button>
        </div>
      </div>
    </div>
  );
}

// A simple two-option toggle button pair.
function BinaryToggle({ value, onChange, falseLabel = 'Off', trueLabel = 'On' }) {
  return (
    <div className="dd-toggle-group">
      <button
        className={`dd-toggle-btn ${!value ? 'is-active' : ''}`}
        onClick={() => onChange(false)}
      >
        {falseLabel}
      </button>
      <button
        className={`dd-toggle-btn ${value ? 'is-active' : ''}`}
        onClick={() => onChange(true)}
      >
        {trueLabel}
      </button>
    </div>
  );
}

// Row layout: label+hint on left, control on right.
function SettingRow({ label, hint, children }) {
  return (
    <div className="dd-setting-row">
      <div className="dd-setting-label">
        {label}
        {hint && <small>{hint}</small>}
      </div>
      <div style={{ flexShrink: 0 }}>{children}</div>
    </div>
  );
}

window.SettingsModal = SettingsModal;
