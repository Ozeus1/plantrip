let publicLoginRequested=false,publicDiaryData=null;
function hidePublicDiary(){if($('#publicDiary'))$('#publicDiary').hidden=true}
function showLogin(){publicLoginRequested=true;hidePublicDiary();$('#auth').hidden=false;$('#app').hidden=true;$('#authForm input[name=email]').focus()}
async function showPublicDiary(){
  $('#auth').hidden=true;$('#app').hidden=true;
  if(!$('#publicDiary')){const el=document.createElement('div');el.id='publicDiary';document.body.prepend(el)}
  const el=$('#publicDiary');el.hidden=false;
  el.innerHTML='<div class="public-loading">Carregando as histórias da viagem…</div>';
  publicDiaryData=await api('/api/public/diary');
  el.innerHTML=`<div class="public-header"><a class="brand" href="/diary">plantrip<span class="dot">✳</span></a><span>HISTÓRIAS PELO CAMINHO</span><button class="primary" id="publicLogin">${state.user?'Minha viagem ↗':'Entrar para participar ↗'}</button></div><main class="public-main"><section class="public-intro"><span class="eyebrow">DIÁRIO DE VIAGEM</span><h1>Os lugares passam.<br>As histórias ficam.</h1><p>Acompanhe os registros, as descobertas e as memórias de quem está vivendo a viagem.</p><span class="tag">Visualização pública · leitura</span></section><div class="toolbar"><input id="publicSearch" aria-label="Buscar memórias" placeholder="Buscar por lugar ou história…"><select id="publicTrip" aria-label="Filtrar por viagem"><option value="">Todas as viagens públicas</option>${publicDiaryData.trips.map(t=>`<option value="${t.id}">${esc(t.name)}</option>`).join('')}</select></div><div id="publicPosts"></div><p class="public-footer">Para publicar fotos, vídeos e comentários, entre com sua conta de participante.</p></main>`;
  $('#publicLogin').onclick=()=>{if(state.user){location.href='/';return}showLogin()};
  $('#publicSearch').oninput=renderPublicPosts;$('#publicTrip').onchange=renderPublicPosts;renderPublicPosts();
}
function publicMedia(f){return f.mime.startsWith('image/')?`<a href="/media/${f.id}" target="_blank" rel="noopener"><img src="/media/${f.id}" alt="${esc(f.name)}" loading="lazy"></a>`:`<video controls preload="metadata" src="/media/${f.id}" aria-label="${esc(f.name)}"></video>`}
function renderPublicPosts(){
  const query=$('#publicSearch').value.toLowerCase(),trip=$('#publicTrip').value;
  const posts=publicDiaryData.entries.filter(e=>(!trip||String(e.trip_id)===trip)&&`${e.title} ${e.place} ${e.description} ${e.author}`.toLowerCase().includes(query));
  $('#publicPosts').innerHTML=posts.length?posts.map(e=>`<article class="public-post"><div class="public-post-heading"><span class="avatar">${esc(e.author.slice(0,1))}</span><div><strong>${esc(e.author)}</strong><p>${esc(publicDiaryData.trips.find(t=>t.id===e.trip_id)?.name||'')} · ${date(e.start)}</p></div></div><h2>${esc(e.title)}</h2><p class="public-place">⌖ ${esc(e.place)}</p><p class="detail-description">${esc(e.description)}</p><div class="public-gallery">${e.files.map(publicMedia).join('')}</div>${e.comments.length?`<details><summary>${e.comments.length} comentários</summary>${e.comments.map(c=>`<div class="comment"><strong>${esc(c.author)}</strong><p>${esc(c.body)}</p></div>`).join('')}</details>`:''}</article>`).join(''):'<div class="panel empty"><span>▧</span><h2>As próximas histórias chegam em breve.</h2><p>Nenhuma publicação pública encontrada.</p></div>';
}
