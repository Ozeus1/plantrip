// Editor de fotos simplificado do administrador: girar, espelhar, cortar, ajustar luz e cor e realçar o foco de um objeto.
// A prévia é feita no navegador; ao salvar, o servidor aplica as mesmas operações no arquivo em tamanho real.
// Filtros prontos: valores dos mesmos controles do editor (brilho, contraste e cor em %, os demais de -100/0 a 100).
const PHOTO_NEUTRAL={brightness:100,contrast:100,saturation:100,warmth:0,vignette:0,fade:0,soften:0,sharpen:0};
const PHOTO_PRESETS=[
  {id:'vivid',group:'Paisagem',name:'Cores vivas',v:{contrast:112,saturation:130,sharpen:35,vignette:12}},
  {id:'sky',group:'Paisagem',name:'Céu e mar',v:{contrast:108,saturation:122,warmth:-28,sharpen:25}},
  {id:'golden',group:'Paisagem',name:'Hora dourada',v:{brightness:103,contrast:106,saturation:118,warmth:48,vignette:20}},
  {id:'green',group:'Paisagem',name:'Natureza',v:{brightness:102,contrast:110,saturation:138,warmth:10,sharpen:30}},
  {id:'drama',group:'Paisagem',name:'Dramático',v:{brightness:95,contrast:130,saturation:88,sharpen:45,vignette:38}},
  {id:'mist',group:'Paisagem',name:'Antigo suave',v:{contrast:92,saturation:82,warmth:15,fade:55}},
  {id:'natural',group:'Pessoas',name:'Retrato natural',v:{brightness:104,contrast:102,warmth:10,soften:35}},
  {id:'skin',group:'Pessoas',name:'Pele suave',v:{brightness:106,saturation:96,warmth:12,soften:70}},
  {id:'warm',group:'Pessoas',name:'Retrato quente',v:{saturation:106,warmth:32,soften:30,vignette:20}},
  {id:'spot',group:'Pessoas',name:'Destaque',v:{brightness:103,contrast:108,soften:25,vignette:45}},
  {id:'mono',group:'Pessoas',name:'Preto e branco',v:{contrast:118,saturation:0,soften:20,vignette:25}},
  {id:'sepia',group:'Pessoas',name:'Sépia',v:{contrast:105,saturation:22,warmth:70,fade:20,soften:20,vignette:25}}
];
// Valores dos controles para um filtro na intensidade dada (0 a 100): interpola a partir do neutro.
function photoPresetValues(id,strength=100){
  const preset=PHOTO_PRESETS.find(p=>p.id===id),out={};
  for(const k in PHOTO_NEUTRAL)out[k]=Math.round(PHOTO_NEUTRAL[k]+(((preset?.v[k])??PHOTO_NEUTRAL[k])-PHOTO_NEUTRAL[k])*strength/100);
  return out;
}
// Prévia do acabamento nos pixels, igual ao servidor: pele suave, temperatura, desbotado e vinheta (centrada no corte).
function photoLookPixels(data,soft,w,h,look,crop){
  const warm=1+.18*look.warmth,cool=1-.18*look.warmth,lift=40*look.fade,keep=1-.25*look.fade;
  const cx=(crop.x+crop.w/2)*w,cy=(crop.y+crop.h/2)*h,rx=crop.w*w/2,ry=crop.h*h/2;
  for(let y=0,i=0;y<h;y++)for(let x=0;x<w;x++,i+=4){
    let r=data[i],g=data[i+1],b=data[i+2];
    if(look.soften){
      const sr=soft[i],sg=soft[i+1],sb=soft[i+2],d=.299*Math.abs(r-sr)+.587*Math.abs(g-sg)+.114*Math.abs(b-sb),m=look.soften*Math.max(0,1-d/40);
      r+=(sr-r)*m;g+=(sg-g)*m;b+=(sb-b)*m;
    }
    r=lift+Math.min(255,r*warm)*keep;g=lift+g*keep;b=lift+Math.min(255,b*cool)*keep;
    if(look.vignette){
      const t=Math.min(1,Math.max(0,(Math.hypot((x+.5-cx)/rx,(y+.5-cy)/ry)/Math.SQRT2-.35)/.65)),shade=1-.75*look.vignette*t*t*(3-2*t);
      r*=shade;g*=shade;b*=shade;
    }
    data[i]=r;data[i+1]=g;data[i+2]=b;
  }
  return data;
}
// Pincel de apagar: os traços ficam guardados em frações da imagem ORIGINAL (antes de girar/espelhar),
// porque o servidor apaga primeiro e gira depois. Estas duas funções convertem entre a tela e o original.
function photoViewToOriginal(u,v,s){
  if(s.flipH)u=1-u;if(s.flipV)v=1-v;
  return s.rotate===90?[v,1-u]:s.rotate===180?[1-u,1-v]:s.rotate===270?[1-v,u]:[u,v];
}
function photoOriginalToView(x,y,s){
  let [u,v]=s.rotate===90?[1-y,x]:s.rotate===180?[1-x,1-y]:s.rotate===270?[y,1-x]:[x,y];
  if(s.flipH)u=1-u;if(s.flipV)v=1-v;return [u,v];
}
const PHOTO_RATIOS=[['free','Livre'],['orig','Original'],['1','1:1'],['1.3333','4:3'],['1.5','3:2'],['1.7778','16:9'],['0.75','3:4'],['0.5625','9:16']];
function photoEditable(file){return /^image\/(jpeg|png|webp|heic|heif)$/.test(file.mime)}
function photoEditOps(s){
  const full=s.crop.x<.002&&s.crop.y<.002&&s.crop.w>.996&&s.crop.h>.996,r=v=>Math.round(v*1e5)/1e5;
  const f=s.focus||{sharpen:0,blur:0},marked=f.x!=null,focus=f.sharpen>0||(marked&&f.blur>0)?{x:marked?r(f.x):null,y:marked?r(f.y):null,r:f.r,sharpen:f.sharpen/100,blur:marked?f.blur/100:0}:null;
  const strokes=[...(s.erase||[]),...(s.erasePending||[])],erase=strokes.length?strokes:null;
  const look=s.warmth||s.vignette||s.fade||s.soften?{warmth:(s.warmth||0)/100,vignette:(s.vignette||0)/100,fade:(s.fade||0)/100,soften:(s.soften||0)/100}:null;
  return {rotate:s.rotate,flip_h:s.flipH,flip_v:s.flipV,crop:full?null:{x:r(s.crop.x),y:r(s.crop.y),w:r(s.crop.w),h:r(s.crop.h)},brightness:s.brightness/100,contrast:s.contrast/100,saturation:s.saturation/100,focus,look,erase};
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
function photoEditChanged(s){const o=photoEditOps(s);return !!(o.rotate||o.flip_h||o.flip_v||o.crop||o.focus||o.look||o.erase||o.brightness!==1||o.contrast!==1||o.saturation!==1)}
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
  const blank=()=>({rotate:0,flipH:false,flipV:false,crop:{x:0,y:0,w:1,h:1},ratio:'free',brightness:100,contrast:100,saturation:100,warmth:0,vignette:0,fade:0,soften:0,preset:'',strength:100,erase:[],erasePending:[],brush:4,focus:{x:null,y:null,r:.25,sharpen:0,blur:0}}),s=blank();
  const RANGES=[['brightness','Brilho',50,150,'%'],['contrast','Contraste',50,150,'%'],['saturation','Cor',0,200,'%'],['warmth','Temperatura',-100,100,''],['vignette','Vinheta',0,100,'%'],['soften','Suavizar pele',0,100,'%'],['fade','Desbotado',0,100,'%']];
  d.innerHTML=`<div class="modal-heading"><div><span class="eyebrow">EDITOR DE FOTOS</span><h2>${esc(file.name)}</h2></div><button type="button" class="close" data-admin-close aria-label="Fechar">×</button></div>
  <div class="pe-stage"><p class="admin-sub" id="peLoading">Carregando a foto…</p><div class="pe-frame" id="peFrame" hidden><canvas id="peCanvas"></canvas><i class="pe-ring" id="peRing" hidden></i><canvas class="pe-paint" id="pePaint"></canvas><div class="pe-crop" id="peCrop" data-pe-drag="move">${['nw','n','ne','e','se','s','sw','w'].map(h=>`<i class="pe-h pe-${h}" data-pe-drag="${h}"></i>`).join('')}</div></div></div>
  <div class="pe-tools" role="group" aria-label="Girar e espelhar"><button type="button" data-pe="left" title="Girar para a esquerda">↺ Girar</button><button type="button" data-pe="right" title="Girar para a direita">↻ Girar</button><button type="button" data-pe="fliph" title="Espelhar na horizontal">⇋ Espelhar</button><button type="button" data-pe="flipv" title="Espelhar na vertical">⇅ Inverter</button></div>
  <label class="pe-ratio">Corte <small>(arraste as bordas sobre a foto)</small><select id="peRatio">${PHOTO_RATIOS.map(([v,t])=>`<option value="${v}">${t}</option>`).join('')}</select></label>
  <fieldset class="pe-focus pe-presets"><legend>Filtros prontos</legend>${['Paisagem','Pessoas'].map(g=>`<div class="pe-chips" role="group" aria-label="${g}"><span>${g}</span>${PHOTO_PRESETS.filter(p=>p.group===g).map(p=>`<button type="button" data-pe-preset="${p.id}" aria-pressed="false">${p.name}</button>`).join('')}</div>`).join('')}
  <div class="pe-sliders pe-strength"><label>Intensidade do filtro <output id="pe-strength-out">100%</output><input type="range" min="0" max="100" step="1" value="100" id="peStrength" disabled></label><button type="button" id="peNoPreset" disabled>Sem filtro</button></div></fieldset>
  <div class="pe-sliders">${RANGES.map(([k,t,min,max,unit])=>`<label>${t} <output id="pe-${k}-out" data-unit="${unit}">${s[k]}${unit}</output><input type="range" min="${min}" max="${max}" step="1" value="${s[k]}" data-pe-range="${k}"></label>`).join('')}</div>
  <fieldset class="pe-focus"><legend>Foco</legend><p class="admin-sub">Aumente a nitidez da foto toda ou marque um objeto para realçar só ele; “Suavizar fundo” desfoca o que está em volta.</p>
  <div class="pe-tools"><button type="button" id="peMark" aria-pressed="false">◎ Marcar objeto na foto</button><button type="button" id="peUnmark" hidden>Limpar marcação</button></div>
  <div class="pe-sliders"><label>Nitidez <output id="pe-sharpen-out">0%</output><input type="range" min="0" max="100" step="1" value="0" data-pe-focus="sharpen"></label><label>Tamanho da área <output id="pe-r-out">25%</output><input type="range" min="5" max="100" step="1" value="25" data-pe-focus="r" disabled></label><label>Suavizar fundo <output id="pe-blur-out">0%</output><input type="range" min="0" max="100" step="1" value="0" data-pe-focus="blur" disabled></label></div></fieldset>
  <fieldset class="pe-focus"><legend>Apagar objeto</legend><p class="admin-sub">Pinte por cima do que quer tirar (um fio, uma placa, alguém ao fundo) e toque em “Apagar o que pintei”. A área é preenchida com a continuação do entorno: funciona melhor em objetos pequenos sobre céu, parede, chão ou vegetação.</p>
  <div class="pe-tools"><button type="button" id="peBrush" aria-pressed="false">🖌 Pintar o que apagar</button><button type="button" id="peErase" disabled>Apagar o que pintei</button><button type="button" id="peEraseUndo" hidden>Desfazer apagados</button></div>
  <div class="pe-sliders"><label>Tamanho do pincel <output id="pe-brush-out">4</output><input type="range" min="1" max="20" step="1" value="4" id="peBrushSize"></label></div></fieldset>
  <p class="error" id="peError" role="alert"></p>
  <div class="admin-row pe-file"><a class="pe-link" href="/media/${file.id}?download=1" download title="Baixa o arquivo como está salvo no site (sem os ajustes ainda não salvos)">⬇ Baixar imagem</a><button type="button" id="peReplace" title="Envia outro arquivo no lugar deste, por exemplo corrigido em outro editor">⇪ Substituir por outro arquivo…</button><input type="file" id="peReplaceFile" hidden accept="image/jpeg,image/png,image/webp,image/gif,image/heic,image/heif"></div>
  <div class="admin-row"><button type="button" class="primary" id="peSave" disabled>Salvar alterações</button><button type="button" id="peReset">Desfazer tudo</button>${file.edited?'<button type="button" class="text-btn" id="peRestore" title="Volta ao arquivo enviado originalmente">Restaurar original</button>':''}<button type="button" class="text-btn" data-admin-close>Cancelar</button></div>
  <p class="admin-sub pe-note">O arquivo enviado originalmente fica guardado: depois de salvar ou substituir, “Restaurar original” desfaz tudo.</p>`;
  const canvas=$('#peCanvas'),frame=$('#peFrame'),box=$('#peCrop'),ring=$('#peRing'),paintLayer=$('#pePaint'),img=new Image(),baseSrc=mediaUrl(file,1280);
  let erasedUrl=null;
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
  function lookPreview(){
    const look=photoEditOps(s).look;if(!look)return;
    const w=canvas.width,h=canvas.height,ctx=canvas.getContext('2d');
    try{
      ctx.setTransform(1,0,0,1,0,0);
      const soft=look.soften?softened(Math.max(2,Math.max(w,h)/100)):null,image=ctx.getImageData(0,0,w,h);
      photoLookPixels(image.data,soft,w,h,look,s.crop);ctx.putImageData(image,0,0);
    }catch{}
  }
  // Põe nos controles os valores do estado (depois de escolher um filtro ou desfazer tudo).
  function syncControls(){
    d.querySelectorAll('[data-pe-range]').forEach(r=>{const k=r.dataset.peRange,out=$('#pe-'+k+'-out');r.value=s[k];out.textContent=s[k]+out.dataset.unit});
    const sharp=d.querySelector('[data-pe-focus=sharpen]');sharp.value=s.focus.sharpen;$('#pe-sharpen-out').textContent=s.focus.sharpen+'%';
    d.querySelectorAll('[data-pe-preset]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.pePreset===s.preset)));
    $('#peStrength').disabled=$('#peNoPreset').disabled=!s.preset;$('#peStrength').value=s.strength;$('#pe-strength-out').textContent=s.strength+'%';
  }
  function usePreset(id,strength=100){
    s.preset=id;s.strength=strength;const v=photoPresetValues(id,strength);
    for(const k in v){if(k==='sharpen')s.focus.sharpen=v[k];else s[k]=v[k]}
    syncControls();draw();
  }
  function paintRing(){
    const f=s.focus,marked=f.x!=null,w=canvas.width,h=canvas.height,size=2*f.r*Math.min(w,h);
    ring.hidden=!marked;$('#peUnmark').hidden=!marked;
    if(marked)Object.assign(ring.style,{left:f.x*100+'%',top:f.y*100+'%',width:size/w*100+'%',height:size/h*100+'%'});
    document.querySelectorAll('[data-pe-focus=r],[data-pe-focus=blur]').forEach(r=>r.disabled=!marked);
  }
  // Camada vermelha com o que foi pintado e ainda não apagado.
  function paintStrokes(){
    const w=paintLayer.width=canvas.width,h=paintLayer.height=canvas.height,ctx=paintLayer.getContext('2d');
    ctx.strokeStyle=ctx.fillStyle='#ff3b30';ctx.lineCap=ctx.lineJoin='round';paintLayer.style.opacity=.55;
    for(const stroke of s.erasePending){
      const radius=Math.max(2,stroke.r*Math.min(w,h)),pts=stroke.pts.map(([x,y])=>{const [u,v]=photoOriginalToView(x,y,s);return [u*w,v*h]});
      ctx.lineWidth=radius*2;ctx.beginPath();pts.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));ctx.stroke();
      for(const [x,y] of pts){ctx.beginPath();ctx.arc(x,y,radius,0,7);ctx.fill()}
    }
    $('#peErase').disabled=!s.erasePending.length;$('#peEraseUndo').hidden=!s.erase.length&&!s.erasePending.length;
  }
  function brushing(on){if(on)picking(false);frame.classList.toggle('is-brushing',on);$('#peBrush').setAttribute('aria-pressed',String(on));$('#peBrush').textContent=on?'🖌 Pintando… (toque para parar)':'🖌 Pintar o que apagar'}
  function picking(on){if(on)brushing(false);frame.classList.toggle('is-picking',on);$('#peMark').setAttribute('aria-pressed',String(on));$('#peMark').textContent=on?'Toque no objeto…':(s.focus.x!=null?'◎ Marcar outro objeto':'◎ Marcar objeto na foto')}
  const turned=()=>s.rotate%180!==0,imageRatio=()=>turned()?img.naturalHeight/img.naturalWidth:img.naturalWidth/img.naturalHeight;
  const lock=()=>s.ratio==='free'?0:(s.ratio==='orig'?1:Number(s.ratio)/imageRatio());
  function draw(){
    if(!img.naturalWidth)return;
    const w=turned()?img.naturalHeight:img.naturalWidth,h=turned()?img.naturalWidth:img.naturalHeight,ctx=canvas.getContext('2d');
    canvas.width=w;canvas.height=h;frame.style.aspectRatio=w+' / '+h;
    // A área útil encolhe para caber no diálogo sem deformar.
    frame.style.width=Math.min(frame.parentElement.clientWidth,Math.round(Math.min(window.innerHeight*.46,520)*w/h))+'px';
    ctx.translate(w/2,h/2);ctx.scale(s.flipH?-1:1,s.flipV?-1:1);ctx.rotate(s.rotate*Math.PI/180);ctx.drawImage(img,-img.naturalWidth/2,-img.naturalHeight/2);
    focusPreview();lookPreview();tint();paintRing();paintStrokes();paint();
  }
  function tint(){canvas.style.filter=`brightness(${s.brightness}%) contrast(${s.contrast}%) saturate(${s.saturation}%)`;$('#peSave').disabled=!photoEditChanged(s)}
  function paint(){
    Object.assign(box.style,{left:s.crop.x*100+'%',top:s.crop.y*100+'%',width:s.crop.w*100+'%',height:s.crop.h*100+'%'});
    $('#peSave').disabled=!photoEditChanged(s);
  }
  function applyRatio(){s.crop=s.ratio==='free'?{x:0,y:0,w:1,h:1}:photoRatioCrop(s.ratio==='orig'?imageRatio():Number(s.ratio),imageRatio());if(s.vignette)draw();else paint()}
  d.querySelectorAll('[data-pe]').forEach(b=>b.onclick=()=>{
    const a=b.dataset.pe;
    // A marcação do objeto acompanha o giro e o espelho.
    const f=s.focus,marked=f.x!=null;
    if(a==='left'||a==='right'){if(marked)[f.x,f.y]=a==='right'?[1-f.y,f.x]:[f.y,1-f.x];s.rotate=(s.rotate+(a==='right'?90:270))%360;draw();applyRatio()}
    else{if(a==='fliph'){s.flipH=!s.flipH;if(marked)f.x=1-f.x}else{s.flipV=!s.flipV;if(marked)f.y=1-f.y}draw()}
  });
  $('#peRatio').onchange=ev=>{s.ratio=ev.target.value;applyRatio()};
  d.querySelectorAll('[data-pe-range]').forEach(r=>r.oninput=()=>{
    const k=r.dataset.peRange,out=$('#pe-'+k+'-out');s[k]=Number(r.value);out.textContent=r.value+out.dataset.unit;
    // Brilho, contraste e cor são filtros do navegador; os demais mexem nos pixels da prévia.
    if(['brightness','contrast','saturation'].includes(k))tint();else{$('#peSave').disabled=!photoEditChanged(s);clearTimeout(focusTimer);focusTimer=setTimeout(draw,120)}
  });
  d.querySelectorAll('[data-pe-preset]').forEach(b=>b.onclick=()=>usePreset(b.dataset.pePreset,s.preset===b.dataset.pePreset?s.strength:100));
  $('#peStrength').oninput=ev=>{s.strength=Number(ev.target.value);$('#pe-strength-out').textContent=s.strength+'%';clearTimeout(focusTimer);focusTimer=setTimeout(()=>usePreset(s.preset,s.strength),120)};
  $('#peNoPreset').onclick=()=>usePreset('',100);
  d.querySelectorAll('[data-pe-focus]').forEach(r=>r.oninput=()=>{
    const k=r.dataset.peFocus;s.focus[k]=k==='r'?Number(r.value)/100:Number(r.value);$('#pe-'+k+'-out').textContent=r.value+'%';
    paintRing();$('#peSave').disabled=!photoEditChanged(s);clearTimeout(focusTimer);focusTimer=setTimeout(draw,120);
  });
  $('#peBrush').onclick=()=>brushing(!frame.classList.contains('is-brushing'));
  $('#peBrushSize').oninput=ev=>{s.brush=Number(ev.target.value);$('#pe-brush-out').textContent=s.brush};
  paintLayer.onpointerdown=ev=>{
    if(!frame.classList.contains('is-brushing'))return;ev.preventDefault();
    const rect=frame.getBoundingClientRect(),round=v=>Math.round(Math.min(1,Math.max(0,v))*1e4)/1e4;
    const at=e=>photoViewToOriginal((e.clientX-rect.left)/rect.width,(e.clientY-rect.top)/rect.height,s).map(round);
    const stroke={r:s.brush/200,pts:[at(ev)]};let last=[ev.clientX,ev.clientY];
    if(s.erase.length+s.erasePending.length>=80){$('#peError').textContent='Muitos traços: apague o que já pintou antes de continuar.';return}
    s.erasePending.push(stroke);paintStrokes();paint();paintLayer.setPointerCapture(ev.pointerId);
    paintLayer.onpointermove=e=>{
      if(Math.hypot(e.clientX-last[0],e.clientY-last[1])<3||stroke.pts.length>=600)return;
      last=[e.clientX,e.clientY];stroke.pts.push(at(e));paintStrokes();
    };
    paintLayer.onpointerup=paintLayer.onpointercancel=()=>{paintLayer.onpointermove=paintLayer.onpointerup=paintLayer.onpointercancel=null};
  };
  const showImage=src=>new Promise((ok,fail)=>{img.onload=()=>{$('#peLoading').hidden=true;frame.hidden=false;draw();ok()};img.onerror=()=>fail(Error('Não foi possível carregar a foto.'));img.src=src});
  $('#peErase').onclick=async()=>{
    const button=$('#peErase'),all=[...s.erase,...s.erasePending];button.disabled=true;button.textContent='Apagando…';$('#peError').textContent='';
    try{
      const r=await fetch('/api/files/erase-preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({entry_id:entry.id,file_id:file.id,erase:all})});
      if(!r.ok){let message='Não foi possível apagar';try{message=(await r.json()).error||message}catch{}throw Error(message)}
      const url=URL.createObjectURL(await r.blob());
      s.erase=all;s.erasePending=[];await showImage(url);if(erasedUrl)URL.revokeObjectURL(erasedUrl);erasedUrl=url;
    }catch(ex){$('#peError').textContent=ex.message}
    button.textContent='Apagar o que pintei';paintStrokes();
  };
  const unerase=async()=>{s.erase=[];s.erasePending=[];brushing(false);if(erasedUrl){URL.revokeObjectURL(erasedUrl);erasedUrl=null;await showImage(baseSrc).catch(()=>{})}else draw()};
  $('#peEraseUndo').onclick=unerase;
  d.addEventListener('close',()=>{if(erasedUrl)URL.revokeObjectURL(erasedUrl);erasedUrl=null},{once:true});
  $('#peMark').onclick=()=>picking(!frame.classList.contains('is-picking'));
  $('#peUnmark').onclick=()=>{s.focus.x=s.focus.y=null;picking(false);draw()};
  frame.onclick=ev=>{
    if(!frame.classList.contains('is-picking'))return;
    const rect=frame.getBoundingClientRect();s.focus.x=Math.min(1,Math.max(0,(ev.clientX-rect.left)/rect.width));s.focus.y=Math.min(1,Math.max(0,(ev.clientY-rect.top)/rect.height));
    // Marcar já traz um realce visível; o administrador ajusta depois.
    if(!s.focus.sharpen){s.focus.sharpen=50;const r=d.querySelector('[data-pe-focus=sharpen]');r.value=50;$('#pe-sharpen-out').textContent='50%'}
    picking(false);draw();
  };
  $('#peReset').onclick=()=>{const erased=!!erasedUrl;Object.assign(s,blank());$('#peBrushSize').value=4;$('#pe-brush-out').textContent=4;if(erased)unerase();$('#peRatio').value='free';syncControls();d.querySelectorAll('[data-pe-focus]').forEach(r=>{r.value=r.dataset.peFocus==='r'?25:0;$('#pe-'+r.dataset.peFocus+'-out').textContent=r.value+'%'});picking(false);draw()};
  box.onpointerdown=ev=>{
    const mode=ev.target.dataset.peDrag;if(!mode)return;ev.preventDefault();
    const rect=frame.getBoundingClientRect(),start={...s.crop},x0=ev.clientX,y0=ev.clientY;
    box.setPointerCapture(ev.pointerId);
    box.onpointermove=e=>{s.crop=photoDragCrop(start,mode,(e.clientX-x0)/rect.width,(e.clientY-y0)/rect.height,lock());paint()};
    box.onpointerup=box.onpointercancel=()=>{box.onpointermove=box.onpointerup=box.onpointercancel=null;if(s.vignette)draw()};
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
  showImage(baseSrc).catch(ex=>{$('#peLoading').textContent=ex.message});
  if(!d.open)d.showModal();
}
if(typeof module!=='undefined')module.exports={photoEditOps,photoEditChanged,photoRatioCrop,photoDragCrop,photoEditable,photoFocusWeight,photoFocusPixels,photoPresetValues,photoLookPixels,PHOTO_PRESETS,photoViewToOriginal,photoOriginalToView};
