(() => {
  const data = window.CAPRANAV_KNOWLEDGE?.items || [];
  const $ = (s) => document.querySelector(s);
  const grid = $('#knowledgeGrid'), search = $('#searchInput'), category = $('#categorySelect');
  const type = $('#typeSelect'), status = $('#statusSelect'), loadMore = $('#loadMore');
  const subject = $('#subjectSelect'), attempt = $('#attemptSelect'), layer = $('#layerSelect');
  const difficulty = $('#difficultySelect'), access = $('#accessSelect'), freshness = $('#freshnessSelect');
  const dialog = $('#readerDialog');
  const state = { limit: 24, category: 'All', journey: null, active: null };
  const journeys = {
    plan: { title: 'Study planning and timetable path', match: x => ['Foundation Strategy','CA Inter Strategy'].includes(x.category) },
    concept: { title: 'Concept clarity and Advanced Accounting path', match: x => ['AS 2 & Accounting Standards','Teaching System'].includes(x.category) },
    revise: { title: 'Chapter revision and recall path', match: x => x.category === 'Revision & Exam Execution' || ['Revision Materials','Newton of Accounts Notes'].includes(x.sourceType) },
    practice: { title: 'Exam practice and paper-execution path', match: x => ['Foundation Strategy','CA Inter Strategy','Revision & Exam Execution'].includes(x.category) || x.sourceType === 'Question Bank' },
    habits: { title: 'Daily discipline and focus path', match: x => x.category === 'Daily Discipline' },
    materials: { title: 'Organised study-material path', match: x => x.category === 'Resource Guides' }
  };
  const readStore = (key) => { try { return new Set(JSON.parse(localStorage.getItem(key) || '[]')); } catch { return new Set(); } };
  const saved = readStore('capranav-saved'), done = readStore('capranav-done');
  const persist = () => {
    localStorage.setItem('capranav-saved', JSON.stringify([...saved]));
    localStorage.setItem('capranav-done', JSON.stringify([...done]));
    $('#savedCount').textContent = saved.size; $('#doneCount').textContent = done.size;
  };
  const escapeHTML = (s='') => s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const unique = key => [...new Set(data.map(x => x[key]))].sort();
  const addOptions = (el, values) => values.forEach(v => el.insertAdjacentHTML('beforeend', `<option value="${escapeHTML(v)}">${escapeHTML(v)}</option>`));
  addOptions(category, unique('category')); addOptions(type, unique('sourceType'));
  addOptions(subject, unique('subject')); addOptions(attempt, unique('attempt')); addOptions(layer, unique('revisionLayer'));
  addOptions(difficulty, unique('difficulty')); addOptions(access, unique('access')); addOptions(freshness, unique('freshness'));
  const topCategories = unique('category');
  $('#categoryPills').innerHTML = ['All', ...topCategories].map(x => `<button type="button" data-category="${escapeHTML(x)}"${x==='All'?' class="active"':''}>${escapeHTML(x)}</button>`).join('');

  function filtered() {
    const q = search.value.trim().toLowerCase();
    return data.filter(x => {
      const hay = [x.title,x.summary,x.category,x.sourceType,...x.tags].join(' ').toLowerCase();
      const statusOK = status.value === 'All' || (status.value === 'Saved' && saved.has(x.id)) || (status.value === 'Completed' && done.has(x.id)) || (status.value === 'Unread' && !done.has(x.id));
      const journeyOK = !state.journey || journeys[state.journey].match(x);
      return (!q || hay.includes(q)) && journeyOK && (state.category==='All' || x.category===state.category) &&
        (type.value==='All' || x.sourceType===type.value) && (subject.value==='All' || x.subject===subject.value) &&
        (attempt.value==='All' || x.attempt===attempt.value) && (layer.value==='All' || x.revisionLayer===layer.value) &&
        (difficulty.value==='All' || x.difficulty===difficulty.value) && (access.value==='All' || x.access===access.value) &&
        (freshness.value==='All' || x.freshness===freshness.value) && statusOK;
    });
  }
  function render(reset=false) {
    if (reset) state.limit=24;
    const rows=filtered(); const visible=rows.slice(0,state.limit);
    grid.innerHTML=visible.map(x => x.downloadUrl ? `<article class="knowledge-card resource-result">
      <button class="card-open" type="button" data-id="${x.id}"><span class="card-top"><span class="card-id">${x.id} · ${escapeHTML(x.chapter)}</span><span class="card-type">${escapeHTML(x.sourceType)}</span></span>
      <h3>${escapeHTML(x.title)}</h3><div class="resource-meta"><span>${escapeHTML(x.revisionLayer)}</span><span>${escapeHTML(x.difficulty)}</span><span>${escapeHTML(x.updated)}</span></div><p>${escapeHTML(x.recommendation)}</p></button>
      <div class="direct-resource-actions"><a href="${x.sourceUrl}" target="_blank" rel="noopener">Preview</a><a href="${x.downloadUrl}" target="_blank" rel="noopener">Download</a></div>
    </article>` : `<button class="knowledge-card" type="button" data-id="${x.id}">
      <span class="card-top"><span class="card-id">${x.id} · ${escapeHTML(x.category)}</span><span class="card-type">${escapeHTML(x.sourceType)}</span></span>
      <h3>${escapeHTML(x.title)}</h3><p>${escapeHTML(x.summary)}</p>
      <span class="card-foot"><span>Open action guide ↗</span><span class="card-flags"><span class="${saved.has(x.id)?'saved':''}" title="Saved"></span><span class="${done.has(x.id)?'done':''}" title="Completed"></span></span></span>
    </button>`).join('');
    $('#visibleCount').textContent=rows.length; $('#resultMessage').textContent=`Showing ${visible.length} of ${rows.length}`;
    loadMore.hidden=visible.length>=rows.length;
    persist();
  }
  function openItem(id) {
    const x=data.find(i=>i.id===id); if(!x) return; state.active=x;
    $('#readerId').textContent=x.id; $('#readerCategory').textContent=x.category; $('#readerType').textContent=x.sourceType;
    $('#readerTitle').textContent=x.title; $('#readerSummary').textContent=x.summary;
    $('#readerActions').innerHTML=x.actions.map(a=>`<li>${escapeHTML(a)}</li>`).join('');
    $('#readerMistakes').innerHTML=x.mistakes.map(a=>`<li>${escapeHTML(a)}</li>`).join('');
    $('#readerTags').innerHTML=x.tags.map(a=>`<span>${escapeHTML(a)}</span>`).join('');
    const source=$('#sourceReader'); source.href=x.sourceUrl; source.textContent=x.sourceLabel+' ↗';
    const dl=$('#downloadReader'); dl.hidden=!x.downloadUrl; if(x.downloadUrl) dl.href=x.downloadUrl;
    $('#saveReader').classList.toggle('active',saved.has(x.id)); $('#saveReader').textContent=saved.has(x.id)?'Saved ✓':'Save for later';
    $('#doneReader').classList.toggle('active',done.has(x.id)); $('#doneReader').textContent=done.has(x.id)?'Completed ✓':'Mark completed';
    const related=data.filter(i=>i.id!==x.id && (i.category===x.category || i.tags.some(t=>x.tags.includes(t)))).slice(0,3);
    $('#relatedItems').innerHTML=related.map(r=>`<button type="button" data-related="${r.id}">${escapeHTML(r.title)}</button>`).join('');
    if (!dialog.open) dialog.showModal(); document.body.style.overflow='hidden';
  }
  function closeDialog(){dialog.close();document.body.style.overflow='';}
  grid.addEventListener('click',e=>{const c=e.target.closest('[data-id]');if(c)openItem(c.dataset.id)});
  $('#relatedItems').addEventListener('click',e=>{const b=e.target.closest('[data-related]');if(b)openItem(b.dataset.related)});
  $('.close-reader').addEventListener('click',closeDialog); dialog.addEventListener('click',e=>{if(e.target===dialog)closeDialog()});
  dialog.addEventListener('cancel',e=>{e.preventDefault();closeDialog()});
  $('#saveReader').addEventListener('click',()=>{const id=state.active.id;saved.has(id)?saved.delete(id):saved.add(id);persist();openItem(id);render()});
  $('#doneReader').addEventListener('click',()=>{const id=state.active.id;done.has(id)?done.delete(id):done.add(id);persist();openItem(id);render()});
  search.addEventListener('input',()=>render(true)); [type,status,subject,attempt,layer,difficulty,access,freshness].forEach(el=>el.addEventListener('change',()=>render(true)));
  category.addEventListener('change',()=>{state.category=category.value;document.querySelectorAll('[data-category]').forEach(b=>b.classList.toggle('active',b.dataset.category===state.category));render(true)});
  $('#categoryPills').addEventListener('click',e=>{const b=e.target.closest('[data-category]');if(!b)return;state.category=b.dataset.category;category.value=state.category;document.querySelectorAll('[data-category]').forEach(x=>x.classList.toggle('active',x===b));render(true)});
  $('#clearFilters').addEventListener('click',()=>{search.value='';[category,type,status,subject,attempt,layer,difficulty,access,freshness].forEach(el=>el.value='All');state.category='All';document.querySelectorAll('[data-category]').forEach(b=>b.classList.toggle('active',b.dataset.category==='All'));render(true)});
  function recommend(answers) {
    const stageMap = {
      learning: ['Teaching System','AS 2 & Accounting Standards'],
      revision: ['Revision & Exam Execution','Resource Guides'],
      practice: ['Revision & Exam Execution','CA Inter Strategy','Foundation Strategy'],
      planning: ['CA Inter Strategy','Foundation Strategy','Daily Discipline'],
      final: ['Revision & Exam Execution','Resource Guides']
    };
    const words = {
      concept: ['concept','understand','principle','framework'],
      standards: ['accounting standard','as 2','inventory','standard'],
      time: ['time','paper','mock','selection','ninety'],
      presentation: ['presentation','working note','exam format','heading'],
      discipline: ['discipline','sleep','focus','target','wake','habit'],
      resources: ['material','resource','notes','question bank','study']
    };
    return data.map((item, index) => {
      let score = 0;
      const text = `${item.title} ${item.summary} ${item.sourceType}`.toLowerCase();
      if (answers.level === 'foundation') score += item.category === 'Foundation Strategy' ? 18 : -2;
      if (answers.level === 'inter') score += ['CA Inter Strategy','AS 2 & Accounting Standards','Teaching System'].includes(item.category) ? 9 : 0;
      if ((stageMap[answers.stage] || []).includes(item.category)) score += 10;
      (words[answers.difficulty] || []).forEach(word => { if (text.includes(word)) score += 5; });
      if (answers.stage === 'practice' && item.sourceType === 'Question Bank') score += 12;
      if (answers.stage === 'revision' && /revision|layer 2|layer 3/i.test(text)) score += 10;
      if (answers.difficulty === 'resources' && item.category === 'Resource Guides') score += 14;
      if (answers.attempt === 'sep26' && /september|sep|mock|final/i.test(text)) score += 4;
      return { item, score, index };
    }).sort((a,b) => b.score-a.score || a.index-b.index).slice(0,5).map(x => x.item);
  }
  $('#pathForm').addEventListener('submit', event => {
    event.preventDefault();
    const answers = Object.fromEntries(new FormData(event.currentTarget).entries());
    const rows = recommend(answers);
    $('#recommendedGrid').innerHTML = rows.map((x, i) => `<button type="button" data-id="${x.id}"><span>${String(i+1).padStart(2,'0')} · ${escapeHTML(x.category)}</span><strong>${escapeHTML(x.title)}</strong><p>${escapeHTML(x.summary)}</p><em>Open focused guide →</em></button>`).join('');
    event.currentTarget.hidden = true; $('#pathResults').hidden = false;
    localStorage.setItem('capranav-path-answers', JSON.stringify(answers));
    $('#pathResults').scrollIntoView({behavior:'smooth',block:'start'});
  });
  $('#recommendedGrid').addEventListener('click', event => {
    const button = event.target.closest('[data-id]'); if (button) openItem(button.dataset.id);
  });
  $('#editAnswers').addEventListener('click', () => {
    $('#pathResults').hidden = true; $('#pathForm').hidden = false; $('#pathForm').scrollIntoView({behavior:'smooth',block:'start'});
  });
  $('#clearJourney').addEventListener('click', () => {
    state.journey = null; $('#journeyBanner').hidden = true; $('#categoryPills').hidden = false; render(true);
  });
  loadMore.addEventListener('click',()=>{state.limit+=24;render()});
  const need = new URLSearchParams(location.search).get('need');
  const needDefaults = {
    learning: {stage:'learning',difficulty:'concept'},
    fastrack: {stage:'revision',difficulty:'resources'},
    final: {stage:'final',difficulty:'time'},
    practice: {stage:'practice',difficulty:'presentation'},
    planning: {stage:'planning',difficulty:'discipline'},
    resources: {stage:'revision',difficulty:'resources'}
  };
  if (needDefaults[need]) {
    Object.entries(needDefaults[need]).forEach(([name,value]) => {
      const input = document.querySelector(`input[name="${name}"][value="${value}"]`);
      if (input) input.checked = true;
    });
  }
  persist(); render();
})();
