// QR-code individual de cada participante: leva à página pública /u/<token> para envio de fotos.
let qrMember=null,qrUrl='';
function qrButtonHtml(m){
  // Só para quem participa da viagem ativa (o QR é por viagem).
  if(!state?.trip_id||!state.members.some(x=>x.id===m.id)||(state.user.role!=='admin'&&m.id!==state.user.id))return '';
  return `<button class="text-btn" data-qr="${m.id}">▦ QR-code de fotos</button>`;
}
function bindQrButtons(){
  document.querySelectorAll('[data-qr]').forEach(b=>b.onclick=ev=>{ev.stopPropagation();openQr(state.members.find(m=>m.id===Number(b.dataset.qr)))});
}
function qrSvg(text){
  if(typeof qrcode!=='function')throw Error('Não foi possível carregar o gerador de QR-code. Verifique a conexão.');
  const qr=qrcode(0,'M');qr.addData(text,'Byte');qr.make();
  return qr.createSvgTag({cellSize:8,margin:2,scalable:true});
}
async function openQr(member,regenerate=false){
  if(!member)return;
  qrMember=member;
  $('#qrPerson').innerHTML=`${avatarHtml(member)}<div><strong>${esc(member.name)}</strong><small>${esc(state.trips.find(t=>t.id===state.trip_id)?.name||'')}</small></div>`;
  $('#qrError').textContent='';$('#qrBox').textContent='Gerando…';$('#qrLink').value='';
  $('#qrRegenerate').hidden=state.user.role!=='admin';
  if(!$('#qrDialog').open)$('#qrDialog').showModal();
  try{
    const r=await api('/api/upload-links',{trip_id:state.trip_id,user_id:member.id,regenerate});
    qrUrl=location.origin+r.path;
    $('#qrLink').value=qrUrl;
    $('#qrBox').innerHTML=qrSvg(qrUrl);
    $('#qrBox svg')?.setAttribute('aria-label','QR-code para '+member.name);
  }catch(e){$('#qrBox').textContent='';$('#qrError').textContent=e.message}
}
function qrFileName(){return 'qrcode-fotos-'+(qrMember?.name||'participante').normalize('NFD').replace(/[̀-ͯ]/g,'').replace(/[^a-z0-9]+/gi,'-').toLowerCase()}
function downloadQr(){
  const svg=$('#qrBox svg');if(!svg)return;
  const size=1024,img=new Image(),blob=new Blob([new XMLSerializer().serializeToString(svg)],{type:'image/svg+xml'}),src=URL.createObjectURL(blob);
  img.onload=()=>{
    const pad=60,label=qrMember?.name||'',canvas=document.createElement('canvas');canvas.width=size;canvas.height=size+120;
    const ctx=canvas.getContext('2d');ctx.fillStyle='#fff';ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.drawImage(img,pad,pad,size-pad*2,size-pad*2);
    ctx.fillStyle='#263d35';ctx.textAlign='center';ctx.font='600 44px Manrope, sans-serif';ctx.fillText(label,size/2,size+10);
    ctx.font='28px DM Sans, sans-serif';ctx.fillStyle='#758279';ctx.fillText('Aponte a câmera e envie suas fotos da viagem',size/2,size+65);
    URL.revokeObjectURL(src);
    const a=document.createElement('a');a.download=qrFileName()+'.png';a.href=canvas.toDataURL('image/png');a.click();
  };
  img.src=src;
}
function printQr(){
  const svg=$('#qrBox svg');if(!svg)return;
  const w=window.open('','_blank','width=600,height=750');if(!w)return toast('Permita pop-ups para imprimir.');
  w.document.write(`<!doctype html><meta charset="utf-8"><title>${esc(qrFileName())}</title><style>body{font-family:sans-serif;text-align:center;padding:40px;color:#263d35}svg{width:360px;height:360px}h1{margin:24px 0 6px}p{color:#758279}</style><h2>plantrip ✳</h2>${svg.outerHTML}<h1>${esc(qrMember?.name||'')}</h1><p>Aponte a câmera e envie suas fotos da viagem</p>`);
  w.document.close();w.focus();w.print();
}
function initQrControls(){
  $('#qrCopy').onclick=async()=>{if(!qrUrl)return;try{await navigator.clipboard.writeText(qrUrl);toast('Link copiado.')}catch{$('#qrLink').select();toast('Selecione e copie o link.')}};
  $('#qrDownload').onclick=downloadQr;
  $('#qrPrint').onclick=printQr;
  $('#qrRegenerate').onclick=()=>{if(qrMember&&confirm('Gerar um novo QR-code? O código anterior deixará de funcionar.'))openQr(qrMember,true)};
}
