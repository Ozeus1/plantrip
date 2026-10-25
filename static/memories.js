function memoryToday(){const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`}
function openMemoryEditor(entry=null,attraction=null){
  if(!state.trip_id)return toast('Selecione uma viagem primeiro.');
  const f=$('#memoryForm');f.reset();$('#memoryError').textContent='';
  const tours=state.entries.filter(e=>e.kind==='tour');
  f.elements.attraction_id.innerHTML='<option value="">Outro local — digitar livremente</option>'+tours.map(e=>`<option value="${e.id}">${esc(e.title)} · ${esc(e.place)}</option>`).join('');
  f.elements.id.value=entry?.id||'';f.elements.title.value=entry?.title||'';
  f.elements.attraction_id.value=String(attraction?.id||entry?.attraction_id||'');
  f.elements.place.value=entry?.place||'';
  f.elements.day.value=(entry?.start||attraction?.start||memoryToday()).slice(0,10);
  f.elements.description.value=entry?.description||'';
  $('#memoryTitle').textContent=entry?'Editar memória':'Publicar memória';
  updateMemoryPlace();$('#memoryDialog').showModal();
}
function updateMemoryPlace(){const f=$('#memoryForm'),free=!f.elements.attraction_id.value;$('#memoryFreePlace').hidden=!free;f.elements.place.required=free}
function initMemoryControls(){
  $('#memoryForm').elements.attraction_id.onchange=updateMemoryPlace;
  $('#memoryForm').onsubmit=async ev=>{
    ev.preventDefault();const f=ev.target,b=$('#memorySave');b.disabled=true;$('#memoryError').textContent='';let saved=false;
    try{
      const attraction=state.entries.find(e=>e.kind==='tour'&&String(e.id)===f.elements.attraction_id.value);
      const payload={kind:'diary',trip_id:state.trip_id,title:f.elements.title.value,place:attraction?.title||f.elements.place.value,category:'Memória',start:f.elements.day.value,end:'',description:f.elements.description.value,attraction_id:attraction?.id||null};
      if(f.elements.id.value)payload.id=Number(f.elements.id.value);
      const result=await api('/api/entries',payload);f.elements.id.value=result.id;saved=true;
      for(const file of f.elements.files.files){b.textContent='Enviando '+file.name+'…';const r=await fetch('/api/upload',{method:'POST',headers:{'X-Entry-Id':String(result.id),'X-File-Name':encodeURIComponent(file.name)},body:file});if(!r.ok)throw Error((await r.json()).error||'Não foi possível enviar o arquivo')}
      $('#memoryDialog').close();await load();toast('Memória publicada para o grupo.');
    }catch(ex){$('#memoryError').textContent=(saved?'A memória foi salva. Falha no envio: ':'')+ex.message}finally{b.disabled=false;b.textContent='Publicar memória ↗'}
  };
}
