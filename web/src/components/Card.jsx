// ============================================================
// Card — the visual building block. Handles face, back, joker.
// ============================================================

function Card({ card, size, faceDown, decorative, selected, onClick, style, className = '', cardId }) {
  if (!card && !faceDown) return null;
  const dataId = cardId || card?.id;
  const isJoker = card?.isJoker;
  const isRed = card?.suit === '♥' || card?.suit === '♦';
  const sizeClass = size === 'sm' ? 'dd-card--sm' : size === 'md' ? 'dd-card--md' : '';

  if (faceDown) {
    return (
      <div
        data-card-id={dataId}
        className={`dd-card dd-card--back ${sizeClass} ${onClick ? 'is-clickable' : ''} ${className}`}
        style={style}
        onClick={onClick}
      >
        <div className="dd-card-face">
          {!decorative && (
            <div className="dd-back-stamp">
              <span className="dd-back-stamp-label">DD</span>
            </div>
          )}
        </div>
      </div>
    );
  }

  if (isJoker) {
    return (
      <div
        data-card-id={dataId}
        className={`dd-card dd-card--joker ${sizeClass} ${selected ? 'is-selected' : ''} ${onClick ? 'is-clickable' : ''} ${className}`}
        style={style}
        onClick={onClick}
      >
        <div className="dd-card-face">
          <div className="dd-card-corner dd-card-corner-top">JKR</div>
          <div className="dd-card-center">★</div>
          <div className="dd-card-corner dd-card-corner-bot">JKR</div>
        </div>
      </div>
    );
  }

  return (
    <div
      data-card-id={dataId}
      className={`dd-card ${isRed ? 'dd-card--red' : 'dd-card--black'} ${sizeClass} ${selected ? 'is-selected' : ''} ${onClick ? 'is-clickable' : ''} ${className}`}
      style={style}
      onClick={onClick}
    >
      <div className="dd-card-face">
        <div className="dd-card-corner dd-card-corner-top">
          {card.rank}
          <span className="suit">{card.suit}</span>
        </div>
        <div className="dd-card-center">{card.suit}</div>
        <div className="dd-card-corner dd-card-corner-bot">
          {card.rank}
          <span className="suit">{card.suit}</span>
        </div>
      </div>
    </div>
  );
}

window.Card = Card;
