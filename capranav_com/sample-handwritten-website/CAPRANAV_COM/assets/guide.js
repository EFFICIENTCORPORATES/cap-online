(() => {
  const asOrder=(window.CAPRANAV_AS_DEMOS||[]).map(d=>`as-${d.id.replace('AS ','')}`);
  const order=['timetable','roadmap','accounting-purpose','standards',...asOrder,'revision'];
  const params=new URLSearchParams(location.search); const requestedId=params.get('guide') || 'timetable'; const id=requestedId==='as2'?'as-2':requestedId;
  const guide=window.CAPRANAV_GUIDES[id] || window.CAPRANAV_GUIDES.timetable;
  const $=s=>document.querySelector(s); const key=`capranav-guide-${id}`;
  const completed=new Set(JSON.parse(localStorage.getItem(key)||'[]'));
  document.title=`${guide.title} — CA Pranav`; $('#readingTime').textContent=guide.reading; $('#eyebrow').textContent=guide.eyebrow; $('#guideTitle').textContent=guide.title; $('#guideIntro').textContent=guide.intro;
  if(guide.officialSource){$('#officialSource').hidden=false;$('#officialSource').href=guide.officialSource}
  $('#toc').innerHTML=guide.sections.map((s,i)=>`<a href="#section-${i+1}">${i+1}. ${s.title}</a>`).join('');
  $('#sections').innerHTML=guide.sections.map((s,i)=>`<section id="section-${i+1}" data-section="${i+1}"><div class="section-number">${String(i+1).padStart(2,'0')}</div><h2>${s.title}</h2><p>${s.body}</p><div class="apply-box"><span>Apply this now</span><strong>${s.action}</strong><label><input type="checkbox" data-complete="${i+1}" ${completed.has(i+1)?'checked':''}> Mark this section completed</label></div></section>`).join('');
  function update(){
    localStorage.setItem(key,JSON.stringify([...completed])); $('#completionText').textContent=`Completed: ${completed.size} of ${guide.sections.length} sections`; $('#completionBar').style.width=`${completed.size/guide.sections.length*100}%`;
  }
  document.addEventListener('change',e=>{if(!e.target.matches('[data-complete]'))return;const n=Number(e.target.dataset.complete);e.target.checked?completed.add(n):completed.delete(n);update()});
  const bookmarkKey='capranav-saved-guides'; const saved=new Set(JSON.parse(localStorage.getItem(bookmarkKey)||'[]'));
  function showBookmark(){ $('#bookmarkBtn').textContent=saved.has(id)?'Saved ✓':'Save guide'; }
  $('#bookmarkBtn').onclick=()=>{saved.has(id)?saved.delete(id):saved.add(id);localStorage.setItem(bookmarkKey,JSON.stringify([...saved]));showBookmark()};
  $('#printBtn').onclick=()=>print();
  $('#downloadBtn').onclick=()=>{const text=[guide.title,guide.intro,'',...guide.sections.flatMap((s,i)=>[`${i+1}. ${s.title}`,s.body,`ACTION: ${s.action}`,''])].join('\n');const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type:'text/plain'}));a.download=`${id}-action-sheet.txt`;a.click();URL.revokeObjectURL(a.href)};
  const index=order.indexOf(id), prev=order[(index-1+order.length)%order.length], next=order[(index+1)%order.length];
  $('#prevGuide').href=`guide.html?guide=${prev}`;$('#prevGuide').textContent=`← ${window.CAPRANAV_GUIDES[prev].title}`;
  $('#nextGuide').href=`guide.html?guide=${next}`;$('#nextGuide').textContent=`${window.CAPRANAV_GUIDES[next].title} →`;
  if(guide.animation) renderAnimation();
  function renderAnimation(){
    const demos=window.CAPRANAV_AS_DEMOS||[];
    let active=Math.max(0,demos.findIndex(d=>d.id===(guide.asId||(id==='as2'?'AS 2':'AS 1')))),step=0,timer=null,playing=false;
    if(['AS 2','AS 10','AS 22'].includes(guide.asId)){
      const standardNumber=guide.asId.replace('AS ','');
      const storyTitles={'AS 2':'The Naphthalene Factory','AS 10':'The New Moulding Machine','AS 22':'Two Profit Stories'};
      $('#animationHost').innerHTML=`<section class="kahaani-embed" aria-labelledby="kahaaniTitle"><div><p>Accounting Universe · Full animated story</p><h2 id="kahaaniTitle">${guide.asId} — ${storyTitles[guide.asId]}</h2><span>A complete story with original English and Hindi narration, consistent characters, and Play, Pause, Replay and scene controls.</span></div><iframe src="public/experiences/kahaani/accounting-story.html?standard=${standardNumber}&v=20260801a" title="${guide.asId} animated Accounting Universe story" allow="autoplay"></iframe></section>`;
      return;
    }
    const pranavAvatar=`<svg viewBox="0 0 200 300" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <rect x="80" y="226" width="18" height="68" rx="8" fill="#2a2e44"/><rect x="102" y="226" width="18" height="68" rx="8" fill="#2a2e44"/>
      <rect x="46" y="132" width="16" height="80" rx="8" fill="#D8E4F2"/><rect x="138" y="132" width="16" height="80" rx="8" fill="#D8E4F2"/>
      <circle cx="54" cy="210" r="9.5" fill="#E7B189"/><circle cx="146" cy="210" r="9.5" fill="#E7B189"/>
      <rect x="56" y="124" width="88" height="112" rx="16" fill="#D8E4F2"/><path d="M100 124 L89 124 L97 139 Z" fill="#fff"/><path d="M100 124 L111 124 L103 139 Z" fill="#fff"/>
      <path d="M100 130 L105 139 L103 180 L97 180 L95 139 Z" fill="#1A1A2E"/><circle cx="100" cy="194" r="2.4" fill="#b9c6d8"/><circle cx="100" cy="210" r="2.4" fill="#b9c6d8"/>
      <rect x="90" y="98" width="20" height="26" fill="#E7B189"/><circle cx="100" cy="70" r="40" fill="#E7B189"/><circle cx="86" cy="72" r="3.4" fill="#3a2c22"/><circle cx="114" cy="72" r="3.4" fill="#3a2c22"/>
      <path d="M58 74 q-8 -52 42 -52 q50 0 42 52 q-5 -17 -16 -13 q-4 -15 -26 -15 q-23 0 -27 17 q-11 -3 -15 11 Z" fill="#241b18"/><path d="M72 50 q20 12 46 3 q-7 15 -25 15 q-17 0 -21 -18 Z" fill="#2e221d"/>
      <g stroke="#1A1A2E" stroke-width="2.4" fill="none"><circle cx="86" cy="73" r="8.5"/><circle cx="114" cy="73" r="8.5"/><path d="M94.5 73 h11"/></g><path d="M91 90 q9 5 18 0" stroke="#b5704a" stroke-width="3" fill="none" stroke-linecap="round"/>
    </svg>`;
    $('#animationHost').innerHTML=`<section class="concept-demo" aria-labelledby="demoTitle"><div class="demo-head"><div><span>Accounting Universe · Controlled concept introduction</span><h2 id="demoTitle">${demos[active].id} visual explanation</h2><p>Press Play to follow the highlighted decision sequence. The same Pranav character design is retained from the Accounting Universe.</p></div><div class="demo-controls"><button id="playDemo" type="button">Play</button><button id="pauseDemo" type="button">Pause</button><button id="replayDemo" type="button">Replay</button></div></div><div class="demo-voice-line"><label>Language <select id="demoLang"><option value="en-IN">English · India</option><option value="hi-IN">Hindi · India</option><option value="en-GB">English · UK</option></select></label><label>Voice <select id="demoGender"><option value="auto">Best available</option><option value="male">Male</option><option value="female">Female</option></select></label><span id="voiceStatus">Voice: loading…</span></div><div class="as-stage" id="asStage" aria-live="polite"><div class="as-orbit" aria-hidden="true"><i></i><i></i><i></i></div><div class="universe-presenter" aria-hidden="true"><div>${pranavAvatar}</div><span>PRANAV</span></div><div class="story-content"><p class="as-code" id="asCode"></p><h3 id="asTitle"></h3><ol id="asSteps"></ol><div class="as-caption"><small id="stepLabel"></small><strong id="stepHeading"></strong><p id="stepNarration"></p></div></div><div class="demo-timeline"><i id="demoTimeline"></i></div></div><p class="demo-note">Narration uses voices installed in the visitor’s browser or device. Availability of a particular male or female voice depends on that device. Captions always remain visible.</p></section>`;
    const synth='speechSynthesis' in window?window.speechSynthesis:null;
    let indianVoice=null;
    function selectVoice(){
      if(!synth){$('#voiceStatus').textContent='Voice unavailable on this browser · captions enabled';return}
      const voices=synth.getVoices();
      const lang=$('#demoLang').value,gender=$('#demoGender').value;
      let pool=voices.filter(v=>(v.lang||'').toLowerCase()===lang.toLowerCase());
      if(!pool.length)pool=voices.filter(v=>(v.lang||'').toLowerCase().startsWith(lang.slice(0,2).toLowerCase()));
      if(!pool.length)pool=voices;
      const female=/female|woman|heera|kalpana|neerja|swara|zira|aria|susan|hazel|veena/i;
      const male=/male|man|ravi|hemant|madhur|david|mark|guy|george|prabhat/i;
      indianVoice=gender==='female'?(pool.find(v=>female.test(v.name))||pool[0]):gender==='male'?(pool.find(v=>male.test(v.name))||pool[0]):pool[0]||null;
      $('#voiceStatus').textContent=indianVoice?`Using ${indianVoice.name}`:'Voice loading · captions enabled';
    }
    if(synth){selectVoice();synth.onvoiceschanged=selectVoice}
    function draw(){
      const demo=demos[active],current=demo.steps[step];
      $('#asCode').textContent=demo.id;$('#asTitle').textContent=demo.title;
      $('#asSteps').innerHTML=demo.steps.map((s,i)=>`<li class="${i<step?'done':i===step?'active':''}"><span>${i+1}</span>${s[0]}</li>`).join('');
      $('#stepLabel').textContent=`Step ${step+1} of ${demo.steps.length}`;
      $('#stepHeading').textContent=current[0];$('#stepNarration').textContent=current[1];
      $('#demoTimeline').style.width=`${(step+1)/demo.steps.length*100}%`;
    }
    function finishOrAdvance(){
      if(!playing)return;
      if(step<demos[active].steps.length-1){step+=1;draw();speak()}
      else{playing=false;clearTimeout(timer);$('#asStage').classList.remove('is-playing')}
    }
    function speak(){
      if(!synth){timer=setTimeout(finishOrAdvance,8000);return}
      synth.cancel();
      const demo=demos[active],current=demo.steps[step];
      const opening=step===0?`${demo.id}, ${demo.title}. Follow the four connected cards. `:`Next, step ${step+1}. `;
      const closing=step===demo.steps.length-1?" This completes the decision sequence.":"";
      const utterance=new SpeechSynthesisUtterance(`${opening}${current[0]}. ${current[1]}${closing}`);
      utterance.lang=$('#demoLang').value;utterance.rate=utterance.lang==='hi-IN'?.9:.92;utterance.pitch=1;
      if(indianVoice)utterance.voice=indianVoice;
      utterance.onend=finishOrAdvance;
      utterance.onerror=()=>{if(playing)timer=setTimeout(finishOrAdvance,2500)};
      synth.speak(utterance);
    }
    function play(){
      if(playing)return;
      playing=true;$('#asStage').classList.add('is-playing');
      if(synth&&synth.paused)synth.resume();else speak();
    }
    function pause(){
      playing=false;clearTimeout(timer);$('#asStage').classList.remove('is-playing');
      if(synth&&synth.speaking)synth.pause();
    }
    function replay(){
      clearTimeout(timer);if(synth)synth.cancel();step=0;playing=false;draw();play();
    }
    $('#playDemo').onclick=play;$('#pauseDemo').onclick=pause;$('#replayDemo').onclick=replay;
    $('#demoLang').onchange=$('#demoGender').onchange=()=>{pause();if(synth){synth.cancel();synth.resume()}selectVoice()};
    addEventListener('pagehide',()=>{clearTimeout(timer);if(synth)synth.cancel()},{once:true});
    draw();
  }
  addEventListener('scroll',()=>{const max=document.documentElement.scrollHeight-innerHeight;$('#progressLine').style.width=`${max?scrollY/max*100:0}%`},{passive:true});
  showBookmark();update();
})();
