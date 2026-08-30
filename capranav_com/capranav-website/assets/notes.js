const catalogue = window.CAPRANAV_NOTES || { notes: [], folderLinks: [], rootFolder: '#' };
const grid = document.querySelector('#notes-grid');
const template = document.querySelector('#note-template');
const search = document.querySelector('#notes-search');
const layerFilters = document.querySelector('#layer-filters');
const categoryFilter = document.querySelector('#category-filter');
const resultCount = document.querySelector('#result-count');
const emptyState = document.querySelector('#empty-state');
const clearFilters = document.querySelector('#clear-filters');
const folderStrip = document.querySelector('#folder-strip');
const heroCount = document.querySelector('#hero-count');
const headerFolderLink = document.querySelector('#header-folder-link');

let activeLayer = 'all';
let activeCategory = 'all';
let query = '';

const layers = ['all', ...new Set(catalogue.notes.map((note) => note.layer))];
const categories = [...new Set(catalogue.notes.map((note) => note.category))].sort();

heroCount.textContent = catalogue.notes.length;
headerFolderLink.href = catalogue.rootFolder;

catalogue.folderLinks.forEach((folder, index) => {
  const link = document.createElement('a');
  link.href = folder.url;
  link.target = '_blank';
  link.rel = 'noopener';
  link.className = `folder-card folder-${index + 1}`;
  link.innerHTML = `<span>${folder.layer}</span><strong>${folder.title}</strong><em>Open folder ↗</em>`;
  folderStrip.append(link);
});

layers.forEach((layer) => {
  const button = document.createElement('button');
  button.type = 'button';
  button.dataset.layer = layer;
  button.textContent = layer === 'all' ? 'All resources' : layer;
  button.classList.toggle('is-active', layer === 'all');
  button.addEventListener('click', () => {
    activeLayer = layer;
    layerFilters.querySelectorAll('button').forEach((item) => {
      item.classList.toggle('is-active', item.dataset.layer === layer);
    });
    render();
  });
  layerFilters.append(button);
});

categories.forEach((category) => {
  const option = document.createElement('option');
  option.value = category;
  option.textContent = category;
  categoryFilter.append(option);
});

function filteredNotes() {
  const normalized = query.trim().toLowerCase();
  return catalogue.notes.filter((note) => {
    const matchesLayer = activeLayer === 'all' || note.layer === activeLayer;
    const matchesCategory = activeCategory === 'all' || note.category === activeCategory;
    const haystack = `${note.title} ${note.category} ${note.layer}`.toLowerCase();
    return matchesLayer && matchesCategory && (!normalized || haystack.includes(normalized));
  });
}

function render() {
  const notes = filteredNotes();
  grid.replaceChildren();
  const fragment = document.createDocumentFragment();

  notes.forEach((note) => {
    const card = template.content.firstElementChild.cloneNode(true);
    card.querySelector('.note-layer').textContent = note.layer;
    card.querySelector('.note-category').textContent = note.category;
    card.querySelector('.note-title').textContent = note.title;
    card.querySelector('.preview-link').href = note.preview;
    card.querySelector('.download-link').href = note.download;
    fragment.append(card);
  });

  grid.append(fragment);
  resultCount.textContent = `${notes.length} resource${notes.length === 1 ? '' : 's'} shown`;
  emptyState.hidden = notes.length !== 0;
}

search.addEventListener('input', () => {
  query = search.value;
  render();
});

categoryFilter.addEventListener('change', () => {
  activeCategory = categoryFilter.value;
  render();
});

clearFilters.addEventListener('click', () => {
  query = '';
  activeLayer = 'all';
  activeCategory = 'all';
  search.value = '';
  categoryFilter.value = 'all';
  layerFilters.querySelectorAll('button').forEach((button) => {
    button.classList.toggle('is-active', button.dataset.layer === 'all');
  });
  render();
});

render();
