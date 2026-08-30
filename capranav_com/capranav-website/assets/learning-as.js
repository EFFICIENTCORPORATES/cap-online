(() => {
  const host=document.querySelector('#asGuideGrid');
  if(!host)return;
  host.innerHTML=(window.CAPRANAV_AS_DEMOS||[]).map((demo,index)=>{
    const number=demo.id.replace('AS ','');
    const reading=10+(index%4);
    return `<article>
      <span>${String(index+1).padStart(2,'0')} · ${reading} min read</span>
      <p class="as-card-code">${demo.id}</p>
      <h3>${demo.title}</h3>
      <p>${demo.steps[0][1]}</p>
      <a href="guide.html?guide=as-${number}">Open ${demo.id} guide →</a>
    </article>`;
  }).join('');
})();
