// ============================================================
// Mascots — Doki Doki sticker characters for AI opponents
// Each: { id, name, color, svg, lines: { greet, draw, discard, meld, layoff, win, lose, taunt } }
// ============================================================

const MASCOT_MOCHI = {
  id: 'mochi',
  name: 'Mochi',
  color: 'var(--dd-bubblegum-soft)',
  svg: (
    <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <circle cx="50" cy="55" r="38" fill="#FFD4E4" stroke="#14110D" strokeWidth="5" />
      <ellipse cx="38" cy="55" rx="6" ry="8" fill="#14110D" />
      <ellipse cx="62" cy="55" rx="6" ry="8" fill="#14110D" />
      <ellipse cx="40" cy="52" rx="2" ry="3" fill="#FFF" />
      <ellipse cx="64" cy="52" rx="2" ry="3" fill="#FFF" />
      <ellipse cx="28" cy="66" rx="5" ry="3" fill="#FF3D8B" opacity="0.6" />
      <ellipse cx="72" cy="66" rx="5" ry="3" fill="#FF3D8B" opacity="0.6" />
      <path d="M 42 70 Q 50 78 58 70" stroke="#14110D" strokeWidth="4" fill="none" strokeLinecap="round" />
    </svg>
  ),
  lines: {
    greet:   ["hi hi! let's play~", "doki doki ♥"],
    draw:    ["mmm~ snacky", "ooh, lemme see"],
    discard: ["bye bye!", "don't want this one~"],
    meld:    ["look look! ✨", "sticker sheet ♥"],
    layoff:  ["heehee, on yours!", "borrowing this~"],
    win:     ["mochi wins! 🌸", "yay yay yay!"],
    lose:    ["aw beans...", "next round...!"],
    taunt:   ["doing okay?", "be brave!"],
  },
};

const MASCOT_TAKO = {
  id: 'tako',
  name: 'Tako',
  color: 'var(--dd-grape-tint)',
  svg: (
    <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <path d="M 22 45 Q 22 22 50 22 Q 78 22 78 45 L 78 62 Q 70 70 70 55 Q 62 70 62 55 Q 54 70 54 55 Q 46 70 46 55 Q 38 70 38 55 Q 30 70 30 55 L 22 62 Z"
            fill="#8C6BFF" stroke="#14110D" strokeWidth="5" strokeLinejoin="round" />
      <ellipse cx="40" cy="42" rx="5" ry="7" fill="#14110D" />
      <ellipse cx="60" cy="42" rx="5" ry="7" fill="#14110D" />
      <ellipse cx="42" cy="39" rx="1.6" ry="2" fill="#FFF" />
      <ellipse cx="62" cy="39" rx="1.6" ry="2" fill="#FFF" />
      <ellipse cx="32" cy="50" rx="4" ry="2.5" fill="#FF3D8B" opacity="0.6" />
      <ellipse cx="68" cy="50" rx="4" ry="2.5" fill="#FF3D8B" opacity="0.6" />
      <path d="M 44 52 Q 50 56 56 52" stroke="#14110D" strokeWidth="3" fill="none" strokeLinecap="round" />
    </svg>
  ),
  lines: {
    greet:   ["ヘイ ヘイ", "tako time"],
    draw:    ["this'll do", "hmm. okay"],
    discard: ["nope", "trash"],
    meld:    ["count it", "stickers down"],
    layoff:  ["riding yours", "thanks for the meld"],
    win:     ["eight arms, eight wins"],
    lose:    ["tch.", "next time..."],
    taunt:   ["you sure about that?", "interesting move"],
  },
};

const MASCOT_NORI = {
  id: 'nori',
  name: 'Nori',
  color: 'var(--dd-matcha-tint)',
  svg: (
    <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <rect x="14" y="20" width="72" height="60" rx="14" fill="#14110D" />
      <rect x="20" y="26" width="60" height="48" rx="10" fill="#FFF8EE" />
      <ellipse cx="50" cy="50" rx="14" ry="10" fill="#FF8A2C" />
      <path d="M 36 50 Q 42 46 50 50 Q 58 54 64 50" stroke="#FFF" strokeWidth="2" fill="none" opacity="0.7" />
      <ellipse cx="32" cy="40" rx="3" ry="4" fill="#14110D" />
      <ellipse cx="68" cy="40" rx="3" ry="4" fill="#14110D" />
      <ellipse cx="33" cy="38.5" rx="1" ry="1.4" fill="#FFF" />
      <ellipse cx="69" cy="38.5" rx="1" ry="1.4" fill="#FFF" />
      <path d="M 44 65 Q 50 68 56 65" stroke="#14110D" strokeWidth="2.5" fill="none" strokeLinecap="round" />
    </svg>
  ),
  lines: {
    greet:   ["hello, friend ♡", "good luck!"],
    draw:    ["one for me~", "fresh roll"],
    discard: ["pass!", "not today"],
    meld:    ["sashimi-set ✨", "tidy"],
    layoff:  ["sneaking in!", "may i? thanks"],
    win:     ["sushi roll victory ✨"],
    lose:    ["good game!", "you got me~"],
    taunt:   ["careful~", "hmm~"],
  },
};

const MASCOTS = [MASCOT_MOCHI, MASCOT_TAKO, MASCOT_NORI];

// Player (human) avatar — strawberry mascot
const PLAYER_AVATAR = (
  <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <path d="M 50 22 L 56 30 Q 75 32 80 50 Q 80 80 50 86 Q 20 80 20 50 Q 25 32 44 30 Z"
          fill="#FF3B30" stroke="#14110D" strokeWidth="5" strokeLinejoin="round" />
    <path d="M 38 22 Q 50 12 62 22 Q 56 26 50 24 Q 44 26 38 22 Z"
          fill="#5BC47A" stroke="#14110D" strokeWidth="3" strokeLinejoin="round" />
    <circle cx="36" cy="48" r="2" fill="#FFD53E" stroke="#14110D" strokeWidth="1.2" />
    <circle cx="58" cy="44" r="2" fill="#FFD53E" stroke="#14110D" strokeWidth="1.2" />
    <circle cx="48" cy="58" r="2" fill="#FFD53E" stroke="#14110D" strokeWidth="1.2" />
    <circle cx="32" cy="64" r="2" fill="#FFD53E" stroke="#14110D" strokeWidth="1.2" />
    <circle cx="60" cy="64" r="2" fill="#FFD53E" stroke="#14110D" strokeWidth="1.2" />
    <circle cx="46" cy="74" r="2" fill="#FFD53E" stroke="#14110D" strokeWidth="1.2" />
    <ellipse cx="40" cy="54" rx="3" ry="4" fill="#14110D" />
    <ellipse cx="56" cy="54" rx="3" ry="4" fill="#14110D" />
    <ellipse cx="41" cy="52.5" rx="1" ry="1.4" fill="#FFF" />
    <ellipse cx="57" cy="52.5" rx="1" ry="1.4" fill="#FFF" />
    <ellipse cx="32" cy="62" rx="3" ry="2" fill="#FF3D8B" opacity="0.7" />
    <ellipse cx="64" cy="62" rx="3" ry="2" fill="#FF3D8B" opacity="0.7" />
    <path d="M 44 64 Q 48 68 52 64" stroke="#14110D" strokeWidth="3" fill="none" strokeLinecap="round" />
  </svg>
);

function pickLine(mascot, key) {
  const lines = mascot.lines[key] || [];
  if (lines.length === 0) return null;
  return lines[Math.floor(Math.random() * lines.length)];
}

window.MASCOTS = MASCOTS;
window.PLAYER_AVATAR = PLAYER_AVATAR;
window.pickLine = pickLine;
