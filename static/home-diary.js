// Destaque do diário de viagem na Visão geral, com visualização selecionável: cards, lista ou calendário.
const HOME_DIARY_LIMIT=6;
diaryBrowsers.home={mode:'calendar',place:null,month:null,day:null};
let homeDiaryMode=(()=>{try{return localStorage.getItem('plantrip-home-diary')||'cards'}catch{return 'cards'}})();

// Ordem crescente de data (mais antiga primeiro); sem data vai para o fim.
function byDateAsc(entries){return [...entries].sort((a,b)=>(!a.start)-(!b.start)||String(a.start||'').localeCompare(String(b.start||''))||a.id-b.id)}
// Na Visão geral o clique abre os slides; a edição/detalhes fica num ícone discreto.
function homeEditButton(e){return `<button type="button" class="home-diary-edit" data-home-edit="${e.id}" title="${canEdit(e)?'Editar e ver detalhes':'Ver detalhes e comentários'}" aria-label="${canEdit(e)?'Editar':'Detalhes de'} ${esc(e.title)}">${canEdit(e)?'✎':'⋯'}</button>`}
function homeCard(e){return card(e).replace('data-detail=','data-home-slides=').replace(/<\/article>$/,homeEditButton(e)+'</article>')}
function homeDiaryRow(e){
  const cover=(e.files||[]).find(f=>f.mime.startsWith('image/')),media=(e.files||[]).filter(f=>/^(image|video)\//.test(f.mime)).length;
  return `<article class="home-diary-row" data-home-slides="${e.id}" tabindex="0" role="button">${cover?`<img src="/media/${cover.id}" alt="" loading="lazy">`:'<span class="home-diary-thumb">▧</span>'}<div class="home-diary-copy"><h3>${esc(e.title)}</h3><p>⌖ ${esc(e.place||'Local não informado')} · ${date(e.start)}</p></div><span class="author-label">${avatarHtml({name:e.author,photo:e.author_photo})}<span>${esc(e.author)}</span></span><small>${media} ${media===1?'foto/vídeo':'fotos/vídeos'}</small>${homeEditButton(e)}</article>`;
}
function homeDiaryBody(diary){
  if(!diary.length)return `<div class="panel">${empty('Os melhores momentos vão morar aqui.','Publique uma foto, um vídeo ou uma história para o grupo.','diary')}</div>`;
  // As 6 memórias mais recentes, exibidas em ordem crescente de data.
  const recent=byDateAsc(diary).slice(-HOME_DIARY_LIMIT),more=diary.length>HOME_DIARY_LIMIT?`<button class="text-btn home-diary-more" data-go="diary">Ver todas as ${diary.length} memórias ↗</button>`:'';
  if(homeDiaryMode==='list')return `<div class="panel home-diary-list">${recent.map(homeDiaryRow).join('')}</div>`+more;
  if(homeDiaryMode==='calendar')return `<div class="home-diary-calendar">${renderMemoryBrowser(diary,'home',posts=>`<div class="card-grid">${byDateAsc(posts).map(homeCard).join('')}</div>`,false)}</div>`;
  return `<div class="card-grid home-diary-cards">${recent.map(homeCard).join('')}</div>`+more;
}
function homeDiaryHtml(diary){
  const modes=[['cards','▦ Cards'],['list','☰ Lista'],['calendar','▣ Calendário']];
  return `<section class="home-diary" aria-labelledby="homeDiaryTitle"><div class="section-title home-diary-heading"><div><span class="eyebrow">DIÁRIO DE VIAGEM</span><h2 id="homeDiaryTitle">Memórias do caminho</h2><p>${diary.length?`${diary.length} ${diary.length===1?'memória publicada':'memórias publicadas'} pelo grupo.`:'Ainda sem memórias publicadas.'}</p></div><div class="home-diary-tools"><div class="memory-modes" role="group" aria-label="Visualização do diário">${modes.map(([m,l])=>`<button type="button" data-home-diary="${m}" aria-pressed="${homeDiaryMode===m}">${l}</button>`).join('')}</div>${diary.length?`<button class="text-btn" id="homeDiaryClip">▷ Miniclipe</button>`:''}<button class="text-btn" data-go="diary">Abrir diário ↗</button></div></div><div id="homeDiaryBody">${homeDiaryBody(diary)}</div></section>`;
}
function bindHomeDiary(diary){
  document.querySelectorAll('[data-home-diary]').forEach(b=>b.onclick=()=>{homeDiaryMode=b.dataset.homeDiary;try{localStorage.setItem('plantrip-home-diary',homeDiaryMode)}catch{}render()});
  if($('#homeDiaryClip'))$('#homeDiaryClip').onclick=()=>presentMemories(byDateAsc(diary),true);
  if(homeDiaryMode==='calendar'&&diary.length)bindMemoryBrowser(diary,'home');
  const entry=id=>diary.find(e=>e.id===Number(id));
  document.querySelectorAll('[data-home-slides]').forEach(el=>{
    el.onclick=()=>{const e=entry(el.dataset.homeSlides);if(!e)return;if((e.files||[]).some(f=>/^(image|video)\//.test(f.mime)))presentMemories([e],false);else detail(e.id)};
    el.onkeydown=ev=>{if(ev.key==='Enter'&&ev.target===el)el.click()};
    el.title='Ver fotos em slides';
  });
  document.querySelectorAll('[data-home-edit]').forEach(b=>b.onclick=ev=>{ev.stopPropagation();detail(Number(b.dataset.homeEdit))});
}
