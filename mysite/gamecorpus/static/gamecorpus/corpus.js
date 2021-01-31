
function toggleTokenized() {
  let posList = ['N', 'V', 'Adj', 'Adv', 'Adn', 'AdjN'];
  posList.forEach((pos) => {
    let posCheckbox = document.getElementById(pos);
    posCheckbox.disabled = !posCheckbox.disabled;
    posCheckbox.checked = false;
  })
};
