
function toggleTokenized() {
  let posList = ['noun_flag', 'verb_flag', 'adjective_flag', 'adverb_flag', 'adnomial_flag', 'adjectival_noun_flag'];
  posList.forEach((pos) => {
    let posCheckbox = document.getElementById(pos);
    posCheckbox.disabled = !posCheckbox.disabled;
    posCheckbox.checked = false;
  })
};
