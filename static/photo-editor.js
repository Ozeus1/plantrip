// Editor de fotos simplificado do administrador: girar, espelhar, cortar e ajustar luz e cor.
// A prévia é feita no navegador; ao salvar, o servidor aplica as mesmas operações no arquivo em tamanho real.
const PHOTO_RATIOS=[['free','Livre'],['orig','Original'],['1','1:1'],['1.3333','4:3'],['1.5','3:2'],['1.7778','16:9'],['0.75','3:4'],['0.5625','9:16']];
function photoEditable(file){return /^image\/(jpeg|png|webp|heic|heif)$/.test(file.mime)}
function photoEditOps(s){
  const full=s.crop.x<.002&&s.crop.y<.002&&s.crop.w>.996&&s.crop.h>.996,r=v=>Math.round(v*1e5)/1e5;
  return {rotate:s.rotate,flip_h:s.flipH,flip_v:s.flipV,crop:full?null:{x:r(s.crop.x),y:r(s.crop.y),w:r(s.crop.w),h:r(s.crop.h)},brightness:s.brightness/100,contrast:s.contrast/100,saturation:s.saturation/100};
}
function photoEditChanged(s){const o=photoEditOps(s);return !!(o.rotate||o.flip_h||o.flip_v||o.crop||o.brightness!==1||o.contrast!==1||o.saturation!==1)}
// Maior retângulo de proporção `ratio` (largura/altura em pixels) centrado na imagem de proporção `image`.
function photoRatioCrop(ratio,image){const rel=ratio/image,w=rel>=1?1:rel,h=rel>=1?1/rel:1;return {x:(1-w)/2,y:(1-h)/2,w,h}}
// Arrasto do retângulo de corte: `mode` é 'move' ou a combinação das bordas (n, s, e, w); tudo em frações 0..1.
function photoDragCrop(start,mode,dx,dy,lock,min=.05){
  let {x,y,w,h}=start;
  if(mode==='move')return {x:Math.min(1-w,Math.max(0,x+dx)),y:Math.min(1-h,Math.max(0,y+dy)),w,h};
  let x2=x+w,y2=y+h;
  if(mode.includes('w'))x=Math.max(0,Math.min(x2-min,x+dx));
  if(mode.includes('e'))x2=Math.min(1,Math.max(x+min,x2+dx));
  if(mode.includes('n'))y=Math.max(0,Math.min(y2-min,y+dy));
  if(mode.includes('s'))y2=Math.min(1,Math.max(y+min,y2+dy));
  w=x2-x;h=y2-y;
  if(lock){
    // lock = largura/altura em frações; mantém fixo o canto oposto ao que está sendo arrastado.
    const horizontal=/[ew]/.test(mode),vertical=/[ns]/.test(mode);
    if(horizontal&&!vertical)h=w/lock;else if(vertical&&!horizontal)w=h*lock;else if(w/h>lock)w=h*lock;else h=w/lock;
    const maxW=mode.includes('w')?start.x+start.w:1-x,maxH=mode.includes('n')?start.y+start.h:1-y;
    const fit=Math.min(1,maxW/w,maxH/h);w*=fit;h*=fit;
    if(mode.includes('w'))x=start.x+start.w-w;
    if(mode.includes('n'))y=start.y+start.h-h;
  }
  return {x,y,w,h};
}
function openPhotoEditor(entry,file,onDone=()=>{}){
  if(!isAdminUser()||!photoEditable(file))return;
  const d=adminDialog('photoEditor','Editor de fotos');
  const s={rotate:0,flipH:false,flipV:false,crop:{x:0,y:0,w:1,h:1},ratio:'free',brightness:100,contrast:100,saturation:100};
  d.innerHTML=`<div class="modal-heading"><div><span class="eyebrow">EDITOR DE FOTOS</span><h2>${esc(file.name)}</h2></div><button type="button" class="close" data-admin-close aria-label="Fechar">×</button></div>
  <div class="pe-stage"><p class="admin-sub" id="peLoading">Carregando a foto…</p><div class="pe-frame" id="peFrame" hidden><canvas id="peCanvas"></canvas><div class="pe-crop" id="peCrop" data-pe-drag="move">${['nw','n','ne','e','se','s','sw','w'].map(h=>`<i class="pe-h pe-${h}" data-pe-drag="${h}"></i>`).join('')}</div></div></div>
  <div class="pe-tools" role="group" aria-label="Girar e espelhar"><button type="button" data-pe="left" title="Girar para a esquerda">↺ Girar</button><button type="button" data-pe="right" title="Girar para a direita">↻ Girar</button><button type="button" data-pe="fliph" title="Espelhar na horizontal">⇋ Espelhar</button><button type="button" data-pe="flipv" title="Espelhar na vertical">⇅ Inverter</button></div>
  <label class="pe-ratio">Corte <small>(arraste as bordas sobre a foto)</small><select id="peRatio">${PHOTO_RATIOS.map(([v,t])=>`<option value="${v}">${t}</option>`).join('')}</select></label>
  <div class="pe-sliders">${[['brightness','Brilho'],['contrast','Contraste'],['saturation','Cor']].map(([k,t])=>`<label>${t} <output id="pe-${k}-out">100%</output><input type="range" min="50" max="150" step="1" value="100" data-pe-range="${k}"></label>`).join('')}</div>
  <p class="error" id="peError" role="alert"></p>
  <div class="admin-row"><button type="button" class="primary" id="peSave" disabled>Salvar alterações</button><button type="button" id="peReset">Desfazer tudo</button>${file.edited?'<button type="button" class="text-btn" id="peRestore" title="Volta ao arquivo enviado originalmente">Restaurar original</button>':''}<button type="button" class="text-btn" data-admin-close>Cancelar</button></div>
  <p class="admin-sub pe-note">O arquivo enviado originalmente fica guardado: depois de salvar, “Restaurar original” desfaz as edições.</p>`;
  const canvas=$('#peCanvas'),frame=$('#peFrame'),box=$('#peCrop'),img=new Image();
  const turned=()=>s.rotate%180!==0,imageRatio=()=>turned()?img.naturalHeight/img.naturalWidth:img.naturalWidth/img.naturalHeight;
  const lock=()=>s.ratio==='free'?0:(s.ratio==='orig'?1:Number(s.ratio)/imageRatio());
  function draw(){
    if(!img.naturalWidth)return;
    const w=turned()?img.naturalHeight:img.naturalWidth,h=turned()?img.naturalWidth:img.naturalHeight,ctx=canvas.getContext('2d');
    canvas.width=w;canvas.height=h;frame.style.aspectRatio=w+' / '+h;
    // A área útil encolhe para caber no diálogo sem deformar.
    frame.style.width=Math.min(frame.parentElement.clientWidth,Math.round(Math.min(window.innerHeight*.46,520)*w/h))+'px';
    ctx.translate(w/2,h/2);ctx.scale(s.flipH?-1:1,s.flipV?-1:1);ctx.rotate(s.rotate*Math.PI/180);ctx.drawImage(img,-img.naturalWidth/2,-img.naturalHeight/2);
    canvas.style.filter=`brightness(${s.brightness}%) contrast(${s.contrast}%) saturate(${s.saturation}%)`;
    paint();
  }
  function paint(){
    Object.assign(box.style,{left:s.crop.x*100+'%',top:s.crop.y*100+'%',width:s.crop.w*100+'%',height:s.crop.h*100+'%'});
    $('#peSave').disabled=!photoEditChanged(s);
  }
  function applyRatio(){s.crop=s.ratio==='free'?{x:0,y:0,w:1,h:1}:photoRatioCrop(s.ratio==='orig'?imageRatio():Number(s.ratio),imageRatio());paint()}
  d.querySelectorAll('[data-pe]').forEach(b=>b.onclick=()=>{
    const a=b.dataset.pe;
    if(a==='left'||a==='right'){s.rotate=(s.rotate+(a==='right'?90:270))%360;draw();applyRatio()}
    else{if(a==='fliph')s.flipH=!s.flipH;else s.flipV=!s.flipV;draw()}
  });
  $('#peRatio').onchange=ev=>{s.ratio=ev.target.value;applyRatio()};
  d.querySelectorAll('[data-pe-range]').forEach(r=>r.oninput=()=>{s[r.dataset.peRange]=Number(r.value);$('#pe-'+r.dataset.peRange+'-out').textContent=r.value+'%';draw()});
  $('#peReset').onclick=()=>{Object.assign(s,{rotate:0,flipH:false,flipV:false,crop:{x:0,y:0,w:1,h:1},ratio:'free',brightness:100,contrast:100,saturation:100});$('#peRatio').value='free';d.querySelectorAll('[data-pe-range]').forEach(r=>{r.value=100;$('#pe-'+r.dataset.peRange+'-out').textContent='100%'});draw()};
  box.onpointerdown=ev=>{
    const mode=ev.target.dataset.peDrag;if(!mode)return;ev.preventDefault();
    const rect=frame.getBoundingClientRect(),start={...s.crop},x0=ev.clientX,y0=ev.clientY;
    box.setPointerCapture(ev.pointerId);
    box.onpointermove=e=>{s.crop=photoDragCrop(start,mode,(e.clientX-x0)/rect.width,(e.clientY-y0)/rect.height,lock());paint()};
    box.onpointerup=box.onpointercancel=()=>{box.onpointermove=box.onpointerup=box.onpointercancel=null};
  };
  d.querySelectorAll('[data-admin-close]').forEach(b=>b.onclick=()=>d.close());
  const send=async(body,message)=>{
    const save=$('#peSave');save.disabled=true;$('#peError').textContent='';
    try{await api('/api/files/edit',{entry_id:entry.id,file_id:file.id,...body});d.close();try{await onDone({action:'edited'})}finally{toast(message)}}
    catch(ex){$('#peError').textContent=ex.message;save.disabled=!photoEditChanged(s);save.textContent='Salvar alterações'}
  };
  $('#peSave').onclick=()=>{$('#peSave').textContent='Salvando…';send(photoEditOps(s),'Foto atualizada.')};
  if($('#peRestore'))$('#peRestore').onclick=()=>{if(confirm('Descartar as edições e voltar à foto enviada originalmente?'))send({restore:true},'Foto original restaurada.')};
  img.onload=()=>{$('#peLoading').hidden=true;frame.hidden=false;draw()};
  img.onerror=()=>{$('#peLoading').textContent='Não foi possível carregar a foto.'};
  img.src=mediaUrl(file,1280);
  if(!d.open)d.showModal();
}
if(typeof module!=='undefined')module.exports={photoEditOps,photoEditChanged,photoRatioCrop,photoDragCrop,photoEditable};
