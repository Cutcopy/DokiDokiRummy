# DokiDokiRummy — Claude Notes

## Project

Static React 18 web app (no bundler, Babel standalone). Source lives in `web/`.
Run locally: `python -m http.server 8765 --directory web` then open `http://localhost:8765`.

Key files:
- `web/src/game.js` — engine, `DEFAULT_SETTINGS`, all game logic
- `web/src/ai.js` — AI decision-making (draw, meld, discard)
- `web/src/App.jsx` — main React component, human turn handling, `runAITurn`
- `web/src/components/` — Card, Table, Scoreboard, SettingsModal, etc.
- `web/styles.css` — all styles (no CSS modules)

## Git Workflow — ALWAYS use a feature branch

**Never commit directly to `main`.**

At the very start of any coding session, before touching any file:

```bash
git checkout -b session/<short-description>
# e.g. session/hard-difficulty, session/card-animation, session/bugfix-rummy
```

At the end of the session, push the branch and open a PR:

```bash
git push origin session/<short-description>
gh pr create --title "..." --base main
```

If `gh` is not available, push the branch and report the compare URL:
`https://github.com/Cutcopy/DokiDokiRummy/compare/session/<branch-name>`

## GitHub

Repo: https://github.com/Cutcopy/DokiDokiRummy  
Default branch: `main`
