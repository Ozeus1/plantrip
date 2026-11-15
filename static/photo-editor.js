// Editor de fotos simplificado do administrador: girar, espelhar, cortar, ajustar luz e cor e realçar o foco de um objeto.
// A prévia é feita no navegador; ao salvar, o servidor aplica as mesmas operações no arquivo em tamanho real.
const PHOTO_RATIOS=[['free','Livre'],['orig','Original'],['1','1:1'],['1.3333','4:3'],['1.5','3:2'],['1.7778','16:9'],['0.75','3:4'],['0.5625','9:16']];
function photoEditable(file){return /^image\/(jpeg|png|webp|heic|heif)$/.test(file.mime)}
function photoEditOps(s){
  const full=s.crop.x<.002&&s.crop.y<.002&&s.crop.w>.996&&s.crop.h>.996,r=v=>Math.round(v*1e5)/1e5;
  const f=s.focus||{sharpen:0,blur:0},marked=f.x!=null,focus=f.sharpen>0||(marked&&f.blur>0)?{x:marked?r(f.x):null,y:marked?r(f.y):null,r:f.r,sharpen:f.sharpen/100,blur:marked?f.blur/100:0}:null;
  return {rotate:s.rotate,flip_h:s.flipH,flip_v:s.flipV,crop:full?null:{x:r(s.crop.x),y:r(s.crop.y),w:r(s.crop.w),h:r(s.crop.h)},brightness:s.brightness/100,contrast:s.contrast/100,saturation:s.saturation/100,focus};
}
// Peso do foco (1 no centro do objeto, 0 fora do círculo), igual ao do servidor: distância em pixels e raio em pixels.
function photoFocusWeight(distance,radius){const t=Math.min(1,Math.max(0,(distance/radius-.6)/.4));return 1-t*t*(3-2*t)}
// Prévia do foco direto nos pixels: nitidez = original + diferença para uma cópia borrada; fundo = cópia mais borrada.
function photoFocusPixels(data,soft,back,w,h,focus){
  const amount=focus.sharpen*2.2,marked=focus.x!=null,cx=marked?focus.x*w:0,cy=marked?focus.y*h:0,radius=focus.r*Math.min(w,h);
  for(let y=0,i=0;y<h;y++)for(let x=0;x<w;x++,i+=4){
    const m=marked?photoFocusWeight(Math.hypot(x+.5-cx,y+.5-cy),radius):1;
    for(let c=0;c<3;c++){
      const o=data[i+c],sharp=amount&&m>0?o+amount*(o-soft[i+c]):o,rest=back&&m<1?back[i+c]:o;
      data[i+c]=m*sharp+(1-m)*rest;
    }
  }
  return data;
}
function photoEditChanged(s){const o=photoEditOps(s);return !!(o.rotate||o.flip_h||o.flip_v||o.crop||o.focus||o.brightness!==1||o.contrast!==1||o.saturation!==1)}
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
  const blank=()=>({rotate:0,flipH:false,flipV:false,crop:{x:0,y:0,w:1,h:1},ratio:'free',brightness:100,contrast:100,saturation:100,focus:{x:null,y:null,r:.25,sharpen:0,blur:0}}),s=blank();
  d.innerHTML=`<div class="modal-heading"><div><span class="eyebrow">EDITOR DE FOTOS</span><h2>${esc(file.name)}</h2></div><button type="button" class="close" data-admin-close aria-label="Fechar">×</button></div>
  <div class="pe-stage"><p class="admin-sub" id="peLoading">Carregando a foto…</p><div class="pe-frame" id="peFrame" hidden><canvas id="peCanvas"></canvas><i class="pe-ring" id="peRing" hidden></i><div class="pe-crop" id="peCrop" data-pe-drag="move">${['nw','n','ne','e','se','s','sw','w'].map(h=>`<i class="pe-h pe-${h}" data-pe-drag="${h}"></i>`).join('')}</div></div></div>
  <div class="pe-tools" role="group" aria-label="Girar e espelhar"><button type="button" data-pe="left" title="Girar para a esquerda">↺ Girar</button><button type="button" data-pe="right" title="Girar para a direita">↻ Girar</button><button type="button" data-pe="fliph" title="Espelhar na horizontal">⇋ Espelhar</button><button type="button" data-pe="flipv" title="Espelhar na vertical">⇅ Inverter</button></div>
  <label class="pe-ratio">Corte <small>(arraste as bordas sobre a foto)</small><select id="peRatio">${PHOTO_RATIOS.map(([v,t])=>`<option value="${v}">${t}</option>`).join('')}</select></label>
  <div class="pe-sliders">${[['brightness','Brilho'],['contrast','Contraste'],['saturation','Cor']].map(([k,t])=>`<label>${t} <output id="pe-${k}-out">100%</output><input type="range" min="50" max="150" step="1" value="100" data-pe-range="${k}"></label>`).join('')}</div>
  <fieldset class="pe-focus"><legend>Foco</legend><p class="admin-sub">Aumente a nitidez da foto toda ou marque um objeto para realçar só ele; “Suavizar fundo” desfoca o que está em volta.</p>
  <div class="pe-tools"><button type="button" id="peMark" aria-pressed="false">◎ Marcar objeto na foto</button><button type="button" id="peUnmark" hidden>Limpar marcação</button></div>
  <div class="pe-sliders"><label>Nitidez <output id="pe-sharpen-out">0%</output><input type="range" min="0" max="100" step="1" value="0" data-pe-focus="sharpen"></label><label>Tamanho da área <output id="pe-r-out">25%</output><input type="range" min="5" max="100" step="1" value="25" data-pe-focus="r" disabled></label><label>Suavizar fundo <output id="pe-blur-out">0%</output><input type="range" min="0" max="100" step="1" value="0" data-pe-focus="blur" disabled></label></div></fieldset>
  <p class="error" id="peError" role="alert"></p>
  <div class="admin-row pe-file"><a class="pe-link" href="/media/${file.id}?download=1" download title="Baixa o arquivo como está salvo no site (sem os ajustes ainda não salvos)">⬇ Baixar imagem</a><button type="button" id="peReplace" title="Envia outro arquivo no lugar deste, por exemplo corrigido em outro editor">⇪ Substituir por outro arquivo…</button><input type="file" id="peReplaceFile" hidden accept="image/jpeg,image/png,image/webp,image/gif,image/heic,image/heif"></div>
  <div class="admin-row"><button type="button" class="primary" id="peSave" disabled>Salvar alterações</button><button type="button" id="peReset">Desfazer tudo</button>${file.edited?'<button type="button" class="text-btn" id="peRestore" title="Volta ao arquivo enviado originalmente">Restaurar original</button>':''}<button type="button" class="text-btn" data-admin-close>Cancelar</button></div>
  <p class="admin-sub pe-note">O arquivo enviado originalmente fica guardado: depois de salvar ou substituir, “Restaurar original” desfaz tudo.</p>`;
  const canvas=$('#peCanvas'),frame=$('#peFrame'),box=$('#peCrop'),ring=$('#peRing'),img=new Image();
  let focusTimer=0;
  // Cópia borrada da prévia: reduz e amplia de volta (rápido e suficiente para a prévia).
  function softened(k){
    const w=canvas.width,h=canvas.height,small=document.createElement('canvas'),big=document.createElement('canvas');
    small.width=Math.max(1,Math.round(w/k));small.height=Math.max(1,Math.round(h/k));big.width=w;big.height=h;
    const a=small.getContext('2d'),b=big.getContext('2d');a.imageSmoothingQuality=b.imageSmoothingQuality='high';
    a.drawImage(canvas,0,0,small.width,small.height);b.drawImage(small,0,0,w,h);return b.getImageData(0,0,w,h).data;
  }
  function focusPreview(){
    const f=photoEditOps(s).focus;if(!f)return;
    const w=canvas.width,h=canvas.height,ctx=canvas.getContext('2d'),side=Math.max(w,h);
    try{
      ctx.setTransform(1,0,0,1,0,0);
      const soft=f.sharpen?softened(Math.max(2,side/420)):null,back=f.blur?softened(Math.max(2,f.blur*side/45)):null,image=ctx.getImageData(0,0,w,h);
      photoFocusPixels(image.data,soft,back,w,h,f);ctx.putImageData(image,0,0);
    }catch{}
  }
  function paintRing(){
    const f=s.focus,marked=f.x!=null,w=canvas.width,h=canvas.height,size=2*f.r*Math.min(w,h);
    ring.hidden=!marked;$('#peUnmark').hidden=!marked;
    if(marked)Object.assign(ring.style,{left:f.x*100+'%',top:f.y*100+'%',width:size/w*100+'%',height:size/h*100+'%'});
    document.querySelectorAll('[data-pe-focus=r],[data-pe-focus=blur]').forEach(r=>r.disabled=!marked);
  }
  function picking(on){frame.classList.toggle('is-picking',on);$('#peMark').setAttribute('aria-pressed',String(on));$('#peMark').textContent=on?'Toque no objeto…':(s.focus.x!=null?'◎ Marcar outro objeto':'◎ Marcar objeto na foto')}
  const turned=()=>s.rotate%180!==0,imageRatio=()=>turned()?img.naturalHeight/img.naturalWidth:img.naturalWidth/img.naturalHeight;
  const lock=()=>s.ratio==='free'?0:(s.ratio==='orig'?1:Number(s.ratio)/imageRatio());
  function draw(){
    if(!img.naturalWidth)return;
    const w=turned()?img.naturalHeight:img.naturalWidth,h=turned()?img.naturalWidth:img.naturalHeight,ctx=canvas.getContext('2d');
    canvas.width=w;canvas.height=h;frame.style.aspectRatio=w+' / '+h;
    // A área útil encolhe para caber no diálogo sem deformar.
    frame.style.width=Math.min(frame.parentElement.clientWidth,Math.round(Math.min(window.innerHeight*.46,520)*w/h))+'px';
    ctx.translate(w/2,h/2);ctx.scale(s.flipH?-1:1,s.flipV?-1:1);ctx.rotate(s.rotate*Math.PI/180);ctx.drawImage(img,-img.naturalWidth/2,-img.naturalHeight/2);
    focusPreview();tint();paintRing();paint();
  }
  function tint(){canvas.style.filter=`brightness(${s.brightness}%) contrast(${s.contrast}%) saturate(${s.saturation}%)`;$('#peSave').disabled=!photoEditChanged(s)}
  function paint(){
    Object.assign(box.style,{left:s.crop.x*100+'%',top:s.crop.y*100+'%',width:s.crop.w*100+'%',height:s.crop.h*100+'%'});
    $('#peSave').disabled=!photoEditChanged(s);
  }
  function applyRatio(){s.crop=s.ratio==='free'?{x:0,y:0,w:1,h:1}:photoRatioCrop(s.ratio==='orig'?imageRatio():Number(s.ratio),imageRatio());paint()}
  d.querySelectorAll('[data-pe]').forEach(b=>b.onclick=()=>{
    const a=b.dataset.pe;
    // A marcação do objeto acompanha o giro e o espelho.
    const f=s.focus,marked=f.x!=null;
    if(a==='left'||a==='right'){if(marked)[f.x,f.y]=a==='right'?[1-f.y,f.x]:[f.y,1-f.x];s.rotate=(s.rotate+(a==='right'?90:270))%360;draw();applyRatio()}
    else{if(a==='fliph'){s.flipH=!s.flipH;if(marked)f.x=1-f.x}else{s.flipV=!s.flipV;if(marked)f.y=1-f.y}draw()}
  });
  $('#peRatio').onchange=ev=>{s.ratio=ev.target.value;applyRatio()};
  d.querySelectorAll('[data-pe-range]').forEach(r=>r.oninput=()=>{s[r.dataset.peRange]=Number(r.value);$('#pe-'+r.dataset.peRange+'-out').textContent=r.value+'%';tint()});
  d.querySelectorAll('[data-pe-focus]').forEach(r=>r.oninput=()=>{
    const k=r.dataset.peFocus;s.focus[k]=k==='r'?Number(r.value)/100:Number(r.value);$('#pe-'+k+'-out').textContent=r.value+'%';
    paintRing();$('#peSave').disabled=!photoEditChanged(s);clearTimeout(focusTimer);focusTimer=setTimeout(draw,120);
  });
  $('#peMark').onclick=()=>picking(!frame.classList.contains('is-picking'));
  $('#peUnmark').onclick=()=>{s.focus.x=s.focus.y=null;picking(false);draw()};
  frame.onclick=ev=>{
    if(!frame.classList.contains('is-picking'))return;
    const rect=frame.getBoundingClientRect();s.focus.x=Math.min(1,Math.max(0,(ev.clientX-rect.left)/rect.width));s.focus.y=Math.min(1,Math.max(0,(ev.clientY-rect.top)/rect.height));
    // Marcar já traz um realce visível; o administrador ajusta depois.
    if(!s.focus.sharpen){s.focus.sharpen=50;const r=d.querySelector('[data-pe-focus=sharpen]');r.value=50;$('#pe-sharpen-out').textContent='50%'}
    picking(false);draw();
  };
  $('#peReset').onclick=()=>{Object.assign(s,blank());$('#peRatio').value='free';d.querySelectorAll('[data-pe-range]').forEach(r=>{r.value=100;$('#pe-'+r.dataset.peRange+'-out').textContent='100%'});d.querySelectorAll('[data-pe-focus]').forEach(r=>{r.value=r.dataset.peFocus==='r'?25:0;$('#pe-'+r.dataset.peFocus+'-out').textContent=r.value+'%'});picking(false);draw()};
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
  $('#peReplace').onclick=()=>$('#peReplaceFile').click();
  $('#peReplaceFile').onchange=async ev=>{
    const chosen=ev.target.files[0];ev.target.value='';if(!chosen)return;
    if(!confirm('Substituir a foto do site por “'+chosen.name+'”? O arquivo enviado originalmente continua guardado.'))return;
    $('#peError').textContent='';$('#peReplace').disabled=true;$('#peReplace').textContent='Enviando…';
    try{await replaceMediaFile(entry,file,chosen);d.close();try{await onDone({action:'edited'})}finally{toast('Arquivo substituído.')}}
    catch(ex){$('#peError').textContent=ex.message;$('#peReplace').disabled=false;$('#peReplace').textContent='⇪ Substituir por outro arquivo…'}
  };
  $('#peSave').onclick=()=>{$('#peSave').textContent='Salvando…';send(photoEditOps(s),'Foto atualizada.')};
  if($('#peRestore'))$('#peRestore').onclick=()=>{if(confirm('Descartar as edições e voltar à foto enviada originalmente?'))send({restore:true},'Foto original restaurada.')};
  img.onload=()=>{$('#peLoading').hidden=true;frame.hidden=false;draw()};
  img.onerror=()=>{$('#peLoading').textContent='Não foi possível carregar a foto.'};
  img.src=mediaUrl(file,1280);
  if(!d.open)d.showModal();
}
if(typeof module!=='undefined')module.exports={photoEditOps,photoEditChanged,photoRatioCrop,photoDragCrop,photoEditable,photoFocusWeight,photoFocusPixels};
