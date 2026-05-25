// ============================================================
// Scoreboard — modal after each round + game-over win screen
// ============================================================

function Scoreboard({ game, onNextRound, onNewGame }) {
  const last = game.scoreHistory[game.scoreHistory.length - 1];
  if (!last) return null;
  const isGameOver = game.phase === 'gameOver';
  const winner = game.winner;
  return (
    <div className="dd-modal-veil">
      <div className="dd-modal" style={{ maxWidth: 640 }}>
        {isGameOver ? (
          <React.Fragment>
            <div className="dd-win-trophy">
              {winner?.isHuman
                ? <img src="assets/trophy.svg" alt="Trophy" className="dd-trophy-img" />
                : '★'}
            </div>
            <h1>{winner?.isHuman ? 'You Win!' : `${winner?.name} Wins!`}</h1>
            <p className="lede">
              {winner?.score} points — first to {game.settings?.winScore ?? 500} ♥
            </p>
          </React.Fragment>
        ) : (
          <React.Fragment>
            <h2>Round Over!</h2>
            <p className="lede">
              {last.reason === 'wentOut'
                ? `${game.players[last.goneOut]?.name ?? 'Someone'} went out.`
                : 'Stock ran dry.'}
            </p>
          </React.Fragment>
        )}

        <table className="dd-score-table">
          <thead>
            <tr>
              <th></th>
              {game.scoreHistory.map((_, i) => (
                <th key={i}>R{i + 1}</th>
              ))}
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            {game.players.map((p, pi) => {
              const isLeader = p.score === Math.max(...game.players.map(x => x.score));
              return (
                <tr key={p.id} className={isGameOver && p === winner ? 'is-winner' : ''}>
                  <td className="player-name">
                    {p.name}{isLeader && ' ♥'}
                  </td>
                  {game.scoreHistory.map((round, ri) => (
                    <td key={ri} className={
                      round.scores[pi] > 0 ? 'gain-positive'
                      : round.scores[pi] < 0 ? 'gain-negative' : ''
                    }>
                      {round.scores[pi] > 0 ? '+' : ''}{round.scores[pi]}
                    </td>
                  ))}
                  <td className="total">{p.score}</td>
                </tr>
              );
            })}
          </tbody>
        </table>

        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', marginTop: 24 }}>
          {isGameOver ? (
            <button className="dd-btn dd-btn--primary" onClick={onNewGame}>
              ★ Play Again
            </button>
          ) : (
            <React.Fragment>
              <button className="dd-btn dd-btn--ghost" onClick={onNewGame}>
                New Game
              </button>
              <button className="dd-btn dd-btn--primary" onClick={onNextRound}>
                Next Round →
              </button>
            </React.Fragment>
          )}
        </div>
      </div>
    </div>
  );
}

window.Scoreboard = Scoreboard;
