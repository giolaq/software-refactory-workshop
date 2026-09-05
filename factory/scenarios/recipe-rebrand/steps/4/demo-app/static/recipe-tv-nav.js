export function nextRecipeFocus(row, column, key, lengths) {
  if (key === 'ArrowLeft') return [row, Math.max(0, column - 1)];
  if (key === 'ArrowRight') return [row, Math.min(lengths[row] - 1, column + 1)];
  const nextRow = key === 'ArrowUp' ? Math.max(0, row - 1) : key === 'ArrowDown' ? Math.min(lengths.length - 1, row + 1) : row;
  return [nextRow, Math.min(column, Math.max(0, lengths[nextRow] - 1))];
}

export function initialRecipeFocus(saved, lengths) {
  const bound = (value, max) => Number.isInteger(value) ? Math.max(0, Math.min(value, max)) : 0;
  const row = bound(saved[0], lengths.length - 1);
  return [row, bound(saved[1], (lengths[row] || 1) - 1)];
}

function install() {
  if (!document.body.classList.contains('tv')) return;
  const rows = [...document.querySelectorAll('.recipe-track')].map(track => [...track.querySelectorAll('.recipe-card>a')]).filter(row => row.length);
  if (!rows.flat().length) return;
  const saved = [Number(sessionStorage.getItem('recipe-focus-row')), Number(sessionStorage.getItem('recipe-focus-column'))];
  const [startRow, startColumn] = initialRecipeFocus(saved, rows.map(row => row.length));
  rows.flat().forEach(target => target.tabIndex = -1);
  const start = rows[startRow][startColumn];
  start.tabIndex = 0; start.focus(); start.scrollIntoView({block:'nearest',inline:'nearest'});
  document.addEventListener('keydown', event => {
    const target = document.activeElement;
    let row = rows.findIndex(items => items.includes(target));
    if (row < 0) return;
    const column = rows[row].indexOf(target);
    if (event.key === 'Enter') {
      event.preventDefault();
      sessionStorage.setItem('recipe-focus-row', String(row));
      sessionStorage.setItem('recipe-focus-column', String(column));
      target.click(); return;
    }
    if (!event.key.startsWith('Arrow')) return;
    event.preventDefault();
    const [nextRow,nextColumn] = nextRecipeFocus(row,column,event.key,rows.map(items=>items.length));
    const next = rows[nextRow][nextColumn]; target.tabIndex=-1; next.tabIndex=0; next.focus(); next.scrollIntoView({block:'nearest',inline:'nearest'});
  });
}
if (typeof document !== 'undefined') document.addEventListener('tablestory:rails-ready',install);
