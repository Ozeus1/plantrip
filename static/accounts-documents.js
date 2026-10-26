function avatarContent(user){
  return user?.photo?`<img src="${esc(user.photo)}" alt="Foto de ${esc(user.name)}">`:esc((user?.name||'?').slice(0,1).toUpperCase());
}
function avatarHtml(user){return `<span class="avatar user-photo">${avatarContent(user)}</span>`}

async function userPayload(form){
  const payload=Object.fromEntries(new FormData(form));
  const file=form.elements.photo_file.files[0];
  delete payload.photo_file;delete payload.remove_photo;
  if(form.elements.remove_photo.checked)payload.photo='';
  if(file){
    if(!['image/jpeg','image/png','image/webp'].includes(file.type))throw Error('Escolha uma foto JPEG, PNG ou WebP.');
    if(file.size>15*1024*1024)throw Error('Escolha uma foto de até 15 MB.');
    const url=URL.createObjectURL(file);
    try{
      const img=new Image();img.src=url;await img.decode();
      const canvas=document.createElement('canvas'),scale=Math.min(1,320/Math.max(img.width,img.height));
      canvas.width=Math.max(1,Math.round(img.width*scale));canvas.height=Math.max(1,Math.round(img.height*scale));
      const ctx=canvas.getContext('2d');ctx.fillStyle='#fff';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.drawImage(img,0,0,canvas.width,canvas.height);
      payload.photo=canvas.toDataURL('image/jpeg',0.85);
    }catch{throw Error('Não foi possível ler a foto. Escolha outra imagem.')}
    finally{URL.revokeObjectURL(url)}
  }
  return payload;
}

function configureEntryEditor(kind){
  const f=$('#entryForm'),docs=kind==='documents';
  f.elements.start.closest('.form-row').hidden=docs;
  f.elements.category.closest('label').hidden=docs;
  f.elements.files.closest('label').hidden=kind==='logistics';
  if(kind==='logistics')f.elements.files.value='';
  f.elements.files.accept=docs?'image/jpeg,image/png,image/webp,image/gif,application/pdf':'image/jpeg,image/png,image/webp,image/gif,video/mp4,video/webm,video/quicktime,application/pdf';
  $('#editorTitle').textContent=docs?(f.elements.id.value?'Editar documentação':'Adicionar documentação'):(f.elements.id.value?'Editar etapa':'Um novo passo na viagem');
  f.elements.kind.onchange=()=>configureEntryEditor(f.elements.kind.value);
}

function renderDocuments(){
  resetAttractionLayout();
  document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('active',b.dataset.view==='documents'));
  $('#breadcrumb').textContent='Nossa viagem / Documentação';
  $('#pageTitle').textContent='Seus documentos, organizados.';
  $('#pageSubtitle').textContent='Guarde documentos, reservas e comprovantes da viagem em PDF ou imagem.';
  $('#add').hidden=state.user.role!=='admin'||!state.trip_id;
  $('#add').textContent='＋ Adicionar documentação';$('#add').onclick=()=>openEditor(null,'documents');
  $('#content').innerHTML=`<div class="toolbar"><input id="documentSearch" placeholder="Buscar por título, local ou arquivo…" value="${esc(filter)}" aria-label="Buscar documentos"></div><p class="guide-muted">Os documentos já anexados à logística continuam disponíveis aqui, vinculados às suas etapas.</p><div id="documentResults"></div>`;
  const render=()=>{
    const rows=state.entries.filter(e=>(e.kind==='documents'||(e.kind==='logistics'&&e.files.length))&&`${e.title} ${e.place} ${e.description} ${e.files.map(f=>f.name).join(' ')}`.toLowerCase().includes(filter.toLowerCase()));
    $('#documentResults').innerHTML=rows.length?`<div class="card-grid">${rows.map(e=>`<article class="entry-card document-card"><button type="button" class="document-open" data-detail="${e.id}"><span class="tag">${e.kind==='logistics'?'Vinculado à logística':'Documentação'}</span><h3>${esc(e.title)}</h3><p>${esc(e.place||'Documentos da viagem')} · ${e.files.length} arquivos</p></button><div class="document-files">${e.files.map(f=>`<a class="file-link" href="/media/${f.id}" target="_blank" rel="noopener">↗ ${esc(f.name)}</a>`).join('')||'<p>Nenhum arquivo enviado. Abra o cadastro para anexar.</p>'}</div></article>`).join('')}</div>`:empty('Nenhum documento por aqui.','Adicione um cadastro e anexe seus arquivos.',state.user.role==='admin'?'documents':'');
    bindActions();
  };
  $('#documentSearch').oninput=e=>{filter=e.target.value;render()};render();
}
