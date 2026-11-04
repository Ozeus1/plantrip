// Página pública aberta pelo QR-code individual: escolhe o passeio (ou cria um local) e envia fotos ao diário.
const $=s=>document.querySelector(s),esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const token=location.pathname.split('/').filter(Boolean)[1]||'';
const api=`/api/u/${encodeURIComponent(token)}`;
let info=null,files=[],entry=null; // entry: memória já criada, reaproveitada ao reenviar arquivos com erro

const day=s=>s?new Date(s.length===10?s+'T12:00':s).toLocaleDateString('pt-BR',{day:'2-digit',month:'short'}):'';
const show=id=>['#upLoading','#upInvalid','#upForm','#upDone'].forEach(s=>$(s).hidden=s!==id);

async function start(){
  try{
    const r=await fetch(api);const j=await r.json();
    if(!r.ok)throw Error(j.error||'Link inválido');
    info=j;
  }catch(e){$('#upInvalidMsg').textContent=e.message;return show('#upInvalid')}
  const first=info.participant.name.split(' ')[0];
  document.title=`Plantrip — fotos de ${first}`;
  $('#upTitle').textContent=`Olá, ${first}!`;
  $('#upTrip').textContent=info.trip.name.toUpperCase();
  $('#upAvatar').innerHTML=info.participant.photo?`<img src="${esc(info.participant.photo)}" alt="">`:esc(first.slice(0,1).toUpperCase());
  renderPlaces();show('#upForm');
}

function renderPlaces(){
  const q=$('#upSearch').value.trim().toLowerCase();
  const checked=document.querySelector('#upPlaces input:checked')?.value;
  const today=new Date().toLocaleDateString('sv'),rank=p=>!p.start?2:p.start.slice(0,10)===today?0:1;
  const list=info.places.filter(p=>!q||(p.title+' '+(p.place||'')).toLowerCase().includes(q)).sort((a,b)=>rank(a)-rank(b)||String(a.start).localeCompare(String(b.start))||a.id-b.id);
  $('#upPlaces').innerHTML=list.length?list.map(p=>`<label class="up-place"><input type="radio" name="place" value="${p.id}" ${String(p.id)===checked?'checked':''}><span><strong>${esc(p.title)}</strong><small>${esc([rank(p)===0?'Hoje':day(p.start),p.place&&p.place!==p.title?p.place:''].filter(Boolean).join(' · '))}</small></span></label>`).join(''):`<p class="up-empty">${q?'Nenhum passeio encontrado. Crie um novo local abaixo.':'Ainda não há passeios cadastrados. Crie um novo local abaixo.'}</p>`;
}

function renderPreview(){
  $('#upPreview').innerHTML=files.map((f,i)=>`<div class="up-thumb ${f.state||''}" data-i="${i}">${f.file.type.startsWith('video/')?`<video src="${f.url}" muted playsinline></video>`:`<img src="${f.url}" alt="">`}${f.state?'':`<button type="button" aria-label="Remover ${esc(f.file.name)}" data-remove="${i}">×</button>`}</div>`).join('');
  document.querySelectorAll('[data-remove]').forEach(b=>b.onclick=()=>{URL.revokeObjectURL(files[b.dataset.remove].url);files.splice(Number(b.dataset.remove),1);renderPreview()});
  $('#upSend').textContent=files.length?`Enviar ${files.length} ${files.length===1?'arquivo':'arquivos'}`:'Enviar fotos';
}

function sendFile(entryId,item,onProgress){
  return new Promise((resolve,reject)=>{
    const x=new XMLHttpRequest();
    x.open('POST',api+'/upload');
    x.setRequestHeader('X-Entry-Id',entryId);
    x.setRequestHeader('X-File-Name',encodeURIComponent(fileName(item.file)));
    x.upload.onprogress=e=>e.lengthComputable&&onProgress(e.loaded/e.total);
    x.onload=()=>{if(x.status<300)return resolve();let msg='Falha no envio';try{msg=JSON.parse(x.responseText).error||msg}catch{}reject(Error(msg))};
    x.onerror=()=>reject(Error('Sem conexão. Tente novamente.'));
    x.send(item.file);
  });
}
function fileName(f){
  if(/\.[a-z0-9]{2,5}$/i.test(f.name))return f.name;
  const ext={'image/jpeg':'.jpg','image/png':'.png','image/webp':'.webp','image/heic':'.heic','video/mp4':'.mp4','video/quicktime':'.mov','video/webm':'.webm'}[f.type]||'';
  return (f.name||'foto')+ext;
}

async function submit(ev){
  ev.preventDefault();$('#upError').textContent='';
  const choice=document.querySelector('input[name=place]:checked')?.value;
  if(!choice)return $('#upError').textContent='Escolha o local onde as fotos foram tiradas.';
  const newPlace=$('#upNewPlace').value.trim();
  if(choice==='new'&&newPlace.length<2)return $('#upError').textContent='Informe o nome do novo local.';
  const pending=files.filter(f=>f.state!=='done');
  if(!pending.length)return $('#upError').textContent='Escolha ao menos uma foto ou vídeo.';
  const big=pending.find(f=>f.file.size>100*1024*1024);
  if(big)return $('#upError').textContent=`"${big.file.name}" passa de 100 MB.`;
  $('#upSend').disabled=true;$('#upProgress').hidden=false;
  try{
    if(!entry){
      const body=choice==='new'?{new_place:newPlace}:{attraction_id:Number(choice)};
      body.title=$('#upTitleInput').value.trim();body.description=$('#upDescription').value.trim();
      const r=await fetch(api+'/memory',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
      const created=await r.json();if(!r.ok)throw Error(created.error||'Não foi possível criar a memória');
      entry={...created,choice,newPlace};
    }
    const j=entry;
    const total=pending.reduce((s,f)=>s+f.file.size,0)||1;let sent=0,failed=0;
    for(const [i,item] of pending.entries()){
      $('#upStatus').textContent=`Enviando ${i+1} de ${pending.length}…`;
      try{
        await sendFile(j.id,item,p=>$('#upBar').style.width=Math.round((sent+item.file.size*p)/total*100)+'%');
        item.state='done';
      }catch(e){item.state='failed';failed++;$('#upError').textContent=e.message}
      sent+=item.file.size;$('#upBar').style.width=Math.round(sent/total*100)+'%';renderPreview();
    }
    const ok=pending.length-failed;
    const place=j.choice==='new'?j.newPlace:info.places.find(p=>p.id===j.attraction_id)?.title;
    if(j.choice==='new'&&!info.places.some(p=>p.id===j.attraction_id))info.places.push({id:j.attraction_id,title:j.newPlace,place:j.newPlace,start:''});
    if(failed){$('#upStatus').textContent=`${ok} enviado(s), ${failed} com erro. As fotos com erro ficaram marcadas; remova-as ou tente outro arquivo.`;files=files.filter(f=>f.state!=='done');renderPreview();return}
    $('#upDoneMsg').textContent=`${ok} ${ok===1?'arquivo publicado':'arquivos publicados'} em “${place}”. Elas já aparecem no diário de viagem.`;
    show('#upDone');
  }catch(e){$('#upError').textContent=e.message}
  finally{$('#upSend').disabled=false}
}

function reset(){
  files.forEach(f=>URL.revokeObjectURL(f.url));files=[];entry=null;
  $('#upForm').reset();$('#upNewWrap').hidden=true;$('#upProgress').hidden=true;$('#upBar').style.width='0';$('#upStatus').textContent='';
  renderPlaces();renderPreview();show('#upForm');window.scrollTo(0,0);
}

$('#upSearch').oninput=renderPlaces;
$('#upForm').addEventListener('change',e=>{if(e.target.name==='place'){$('#upNewWrap').hidden=e.target.value!=='new';if(e.target.value==='new')$('#upNewPlace').focus()}});
$('#upFiles').onchange=e=>{for(const file of e.target.files)files.push({file,url:URL.createObjectURL(file)});e.target.value='';renderPreview()};
$('#upForm').onsubmit=submit;
$('#upAgain').onclick=reset;
start();
