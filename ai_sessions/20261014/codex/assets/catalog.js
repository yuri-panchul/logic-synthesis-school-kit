'use strict';
const search = document.querySelector('#search');
const filter = document.querySelector('#kit-filter');
const cards = [...document.querySelectorAll('.exercise')];
function applyFilter() {
  const query = search.value.trim().toLocaleLowerCase();
  let count = 0;
  cards.forEach(card => {
    card.hidden = !(card.textContent.toLocaleLowerCase().includes(query) && (!filter.value || card.dataset.kits.split(' ').includes(filter.value)));
    if (!card.hidden) count++;
  });
  document.querySelector('#result-count').textContent = `${count} of ${cards.length} entries`;
}
search.addEventListener('input', applyFilter);
filter.addEventListener('change', applyFilter);
// Anchor navigation always reveals the requested exercise, including filtered results.
window.addEventListener('hashchange', () => {
  if (document.getElementById(location.hash.slice(1))?.classList.contains('exercise')) {
    search.value = ''; filter.value = ''; applyFilter();
    document.getElementById(location.hash.slice(1)).scrollIntoView();
  }
});
applyFilter();
