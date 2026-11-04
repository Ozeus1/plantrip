// Destaque do diário de viagem na Visão geral, com visualização selecionável: cards, lista ou calendário.
const HOME_DIARY_LIMIT=6;
diaryBrowsers.home={mode:'calendar',place:null,month:null,day:null};
let homeDiaryMode=(()=>{try{return localStorage.getItem('plantrip-home-diary')||'cards'}catch{return 'cards'}})();

function newestFirst(entries){return [...entries].sort((a,b)=>String(b.start||'').localeCompare(String(a.start||''))||b.id-a.id)}
function homeDiaryRow(e){
  const cover=(e.files||[]).find(f=>f.mime.startsWith('image/')),media=(e.files||[]).filter(f=>/^(image|video)\//.test(f.mime)).length;
  return `<article class="home-diary-row" data-detail="${e.id}" tabindex="0" role="button">${cover?`<img src="/media/${cover.id}" alt="" loading="lazy">`:'<span class="home-diary-thumb">▧</span>'}<div class="home-diary-copy"><h3>${esc(e.title)}</h3><p>⌖ ${esc(e.place||'Local não informado')} · ${date(e.start)}</p></div><span class="author-label">${avatarHtml({name:e.author,photo:e.author_photo})}<span>${esc(e.author)}</span></span><small>${media} ${media===1?'foto/vídeo':'fotos/vídeos'}</small></article>`;
}
function homeDiaryBody(diary){
  if(!diary.length)return `<div class="panel">${empty('Os melhores momentos vão morar aqui.','Publique uma foto, um vídeo ou uma história para o grupo.','diary')}</div>`;
  const recent=newestFirst(diary).slice(0,HOME_DIARY_LIMIT),more=diary.length>HOME_DIARY_LIMIT?`<button class="text-btn home-diary-more" data-go="diary">Ver todas as ${diary.length} memórias ↗</button>`:'';
  if(homeDiaryMode==='list')return `<div class="panel home-diary-list">${recent.map(homeDiaryRow).join('')}</div>`+more;
  if(homeDiaryMode==='calendar')return `<div class="home-diary-calendar">${renderMemoryBrowser(diary,'home',posts=>`<div class="card-grid">${newestFirst(posts).map(card).join('')}</div>`,false)}</div>`;
  return `<div class="card-grid home-diary-cards">${recent.map(card).join('')}</div>`+more;
}
function homeDiaryHtml(diary){
  const modes=[['cards','▦ Cards'],['list','☰ Lista'],['calendar','▣ Calendário']];
  return `<section class="home-diary" aria-labelledby="homeDiaryTitle"><div class="section-title home-diary-heading"><div><span class="eyebrow">DIÁRIO DE VIAGEM</span><h2 id="homeDiaryTitle">Memórias do caminho</h2><p>${diary.length?`${diary.length} ${diary.length===1?'memória publicada':'memórias publicadas'} pelo grupo.`:'Ainda sem memórias publicadas.'}</p></div><div class="home-diary-tools"><div class="memory-modes" role="group" aria-label="Visualização do diário">${modes.map(([m,l])=>`<button type="button" data-home-diary="${m}" aria-pressed="${homeDiaryMode===m}">${l}</button>`).join('')}</div>${diary.length?`<button class="text-btn" id="homeDiaryClip">▷ Miniclipe</button>`:''}<button class="text-btn" data-go="diary">Abrir diário ↗</button></div></div><div id="homeDiaryBody">${homeDiaryBody(diary)}</div></section>`;
}
function bindHomeDiary(diary){
  document.querySelectorAll('[data-home-diary]').forEach(b=>b.onclick=()=>{homeDiaryMode=b.dataset.homeDiary;try{localStorage.setItem('plantrip-home-diary',homeDiaryMode)}catch{}render()});
  if($('#homeDiaryClip'))$('#homeDiaryClip').onclick=()=>presentMemories(newestFirst(diary),true);
  if(homeDiaryMode==='calendar'&&diary.length)bindMemoryBrowser(diary,'home');
}
