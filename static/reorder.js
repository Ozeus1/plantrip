let draggedStep=null,stepOrderBusy=false,suppressStepClickUntil=0;

function stepOrderIds(ids,movingId,targetId,after){
  if(movingId===targetId||!ids.includes(movingId)||!ids.includes(targetId))return [...ids];
  const result=ids.filter(id=>id!==movingId),index=result.indexOf(targetId)+(after?1:0);
  result.splice(index,0,movingId);return result;
}
function renderOrderedSteps(rows){
  const custom=state.entries.some(e=>e.kind===view&&e.sort_order!==null&&e.sort_order!==undefined);
  const admin=state.user.role==='admin',canDrag=admin&&!filter&&!stepOrderBusy;
  const hint=admin?(filter?'Limpe a busca para reorganizar as etapas.':'Arraste pela alça ⠿ para mudar a ordem. As datas e horários são mantidos.'):custom?'Sequência definida pelo administrador.':'';
  const controls=`<div class="order-toolbar"><span role="status">${stepOrderBusy?'Salvando sequência…':esc(hint)}${custom?' <span class="tag">Ordem personalizada</span>':''}</span>${admin&&custom?'<button class="text-btn" id="resetStepOrder" '+(stepOrderBusy?'disabled':'')+'>Restaurar por data</button>':''}</div>`;
  // Headings follow consecutive blocks: a move across days never regroups the cards.
  let lastDay=null,html='';
  for(const e of rows){
    const day=e.start?e.start.slice(0,10):'';
    if(day!==lastDay){if(lastDay!==null)html+='</div>';html+=`<h2 class="day-heading">${day?new Date(day+'T12:00').toLocaleDateString('pt-BR',{weekday:'long',day:'numeric',month:'long'}):'Sem data definida'}</h2><div class="list-stack">`;lastDay=day}
    html+=`<article class="entry-card ordered-step" data-step-id="${e.id}" data-detail="${e.id}" tabindex="0" role="button">${admin?`<button type="button" class="drag-handle" draggable="false" ${canDrag?'':'disabled'} aria-label="Reordenar ${esc(e.title)}" title="Arraste para mover. Pelo teclado, use Alt + seta para cima ou para baixo.">⠿</button>`:''}<div class="date-box">${stepEditable(e,"start",date(e.start)+"<strong>"+(time(e.start)||"—")+"</strong>")}</div><div class="step-description"><span class="tag">${esc(e.category)}</span><h3>${stepEditable(e,"title",esc(e.title))}</h3><p>⌖ ${esc(e.place||'Local a definir')}${e.end&&e.start&&e.end.slice(0,10)!==e.start.slice(0,10)?' · até '+date(e.end):''} · ${e.files.length} arquivos · ${e.comments.length} comentários</p>${e.kind==='tour'?`<a class="guide-open-link" href="/attractions/${e.id}" data-open-guide="${e.id}">Conhecer a atração · Guia completo ↗</a>`:''}</div>${admin?`<button type="button" class="text-btn danger" data-remove-step="${e.id}">Excluir ponto</button>`:""}${e.kind==='tour'&&e.guide?.photos?.[0]?`<img class="tour-thumb" src="${esc(e.guide.photos[0].src)}" alt="${esc(e.guide.photos[0].alt)}" loading="lazy">`:''}</article>`;
  }
  return controls+html+(rows.length?'</div>':'');
}
function clearStepDropMarkers(){document.querySelectorAll('.drop-before,.drop-after').forEach(c=>c.classList.remove('drop-before','drop-after'))}
async function saveStepOrder(ids,focusId,reset=false){
  if(stepOrderBusy)return;
  stepOrderBusy=true;
  const tripId=state.trip_id,kind=view;
  renderResults();
  try{
    await api('/api/entries/reorder',{trip_id:tripId,kind,entry_ids:ids,reset});
    await load();toast(reset?'Etapas ordenadas por data.':'Nova ordem salva para todos os participantes.');
  }catch(e){toast(e.message);try{await load()}catch{toast('Não foi possível atualizar a lista. Recarregue a página.')}}
  finally{
    stepOrderBusy=false;
    if(state.trip_id===tripId&&view===kind){renderResults();if(focusId)document.querySelector(`[data-step-id="${focusId}"] .drag-handle`)?.focus()}
  }
}
function bindStepOrdering(){
  const cards=[...document.querySelectorAll('[data-step-id]')];
  if(!cards.length)return;
  cards.forEach(card=>{
    // Capture prevents a click at the end of a drag from opening the detail modal.
    card.addEventListener('click',e=>{if(Date.now()<suppressStepClickUntil){e.preventDefault();e.stopImmediatePropagation()}},true);
    const handle=card.querySelector('.drag-handle');
    if(!handle||handle.disabled)return;
    handle.onclick=e=>e.stopPropagation();
    handle.onkeydown=e=>{
      e.stopPropagation();
      if(!e.altKey||!['ArrowUp','ArrowDown'].includes(e.key)||stepOrderBusy)return;
      e.preventDefault();const ids=filtered().map(x=>x.id),id=Number(card.dataset.stepId),index=ids.indexOf(id),target=index+(e.key==='ArrowUp'?-1:1);
      if(target>=0&&target<ids.length)saveStepOrder(stepOrderIds(ids,id,ids[target],e.key==='ArrowDown'),id);
    };
    let pointer=null,scrollFrame=null;
    function markTarget(){
      clearStepDropMarkers();if(!pointer?.active)return;
      const target=document.elementFromPoint(pointer.x,pointer.y)?.closest('[data-step-id]');
      pointer.target=null;
      if(target&&target!==card){pointer.target=Number(target.dataset.stepId);pointer.after=pointer.y>target.getBoundingClientRect().top+target.offsetHeight/2;target.classList.add(pointer.after?'drop-after':'drop-before')}
    }
    function autoScroll(){
      if(!pointer?.active)return;
      const speed=pointer.y<70?-12:pointer.y>window.innerHeight-70?12:0;
      if(speed){window.scrollBy(0,speed);markTarget()}
      scrollFrame=requestAnimationFrame(autoScroll);
    }
    handle.onpointerdown=e=>{
      if(e.button!==0||stepOrderBusy||filter||state.user.role!=='admin')return;
      e.preventDefault();e.stopPropagation();handle.focus();
      pointer={id:e.pointerId,startX:e.clientX,startY:e.clientY,x:e.clientX,y:e.clientY,active:false,target:null};
      handle.setPointerCapture(e.pointerId);
    };
    handle.onpointermove=e=>{
      if(!pointer||e.pointerId!==pointer.id)return;
      pointer.x=e.clientX;pointer.y=e.clientY;
      if(!pointer.active&&Math.hypot(e.clientX-pointer.startX,e.clientY-pointer.startY)>6){pointer.active=true;draggedStep=Number(card.dataset.stepId);card.classList.add('is-dragging');scrollFrame=requestAnimationFrame(autoScroll)}
      if(pointer.active){e.preventDefault();markTarget()}
    };
    function finishPointer(e,cancelled=false){
      if(!pointer||e.pointerId!==pointer.id)return;
      const saved=pointer,moving=Number(card.dataset.stepId);pointer=null;draggedStep=null;
      if(scrollFrame!==null)cancelAnimationFrame(scrollFrame);
      if(handle.hasPointerCapture(e.pointerId))handle.releasePointerCapture(e.pointerId);
      card.classList.remove('is-dragging');clearStepDropMarkers();
      if(saved.active)suppressStepClickUntil=Date.now()+300;
      if(!cancelled&&saved.active&&saved.target!==null){
        const ids=filtered().map(x=>x.id),result=stepOrderIds(ids,moving,saved.target,saved.after);
        if(ids.some((id,i)=>id!==result[i]))saveStepOrder(result,moving);
      }
    }
    handle.onpointerup=e=>finishPointer(e);
    handle.onpointercancel=e=>finishPointer(e,true);
    handle.onlostpointercapture=e=>finishPointer(e,true);
  });
  if($('#resetStepOrder'))$('#resetStepOrder').onclick=()=>saveStepOrder([],null,true);
}

function stepEditable(e,field,label){
  return state.user.role==='admin'?`<button type="button" class="inline-step" data-inline-step="${e.id}" data-field="${field}" title="Clique para editar" aria-label="Editar ${field==='title'?'título':'data e horário'} de ${esc(e.title)}">${label}</button>`:label;
}
function bindInlineSteps(){
  document.querySelectorAll('[data-inline-step]').forEach(button=>{
    button.onkeydown=ev=>ev.stopPropagation();
    button.onclick=ev=>{
      ev.stopPropagation();if(state.user.role!=='admin')return;
      const entry=state.entries.find(e=>e.id===Number(button.dataset.inlineStep)),field=button.dataset.field;
      const form=document.createElement('form');form.className='inline-step-form';
      form.innerHTML=`<input aria-label="${field==='title'?'Título':'Data e horário'}" type="${field==='title'?'text':entry[field]?.length===10?'date':'datetime-local'}" value="${esc(entry[field])}" required><button type="submit">Salvar</button><button type="button">Cancelar</button>`;
      form.onclick=e=>e.stopPropagation();form.onkeydown=e=>{e.stopPropagation();if(e.key==='Escape'){e.preventDefault();form.replaceWith(button)}};
      form.querySelector('button[type=button]').onclick=()=>form.replaceWith(button);
      form.onsubmit=async event=>{
        event.preventDefault();const value=form.querySelector('input').value.trim();if(!value)return;
        const payload={...entry,[field]:value};
        if(field==='start'&&entry.end&&entry.start){
          const delta=new Date(value)-new Date(entry.start);
          const end=new Date(new Date(entry.end).getTime()+delta);
          if(Number.isFinite(end.getTime())){const local=new Date(end.getTime()-end.getTimezoneOffset()*60000).toISOString();payload.end=local.slice(0,entry.end.length===10?10:16)}
        }
        form.querySelectorAll('button').forEach(b=>b.disabled=true);
        try{await api('/api/entries',payload);await load();toast('Etapa atualizada.')}catch(error){toast(error.message);form.querySelectorAll('button').forEach(b=>b.disabled=false)}
      };
      button.replaceWith(form);form.querySelector('input').focus();
    };
  });
  document.querySelectorAll('[data-remove-step]').forEach(button=>{
    button.onkeydown=ev=>ev.stopPropagation();button.onclick=async ev=>{ev.stopPropagation();if(state.user.role!=='admin'||!confirm('Excluir este ponto e seus arquivos e comentários?'))return;try{await api('/api/delete',{entry_id:Number(button.dataset.removeStep)});await load()}catch(error){toast(error.message)}};
  });
}
