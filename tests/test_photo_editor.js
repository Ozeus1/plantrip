const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const context=vm.createContext({console,Math,Number,Object});
vm.runInContext(fs.readFileSync('static/photo-editor.js','utf8'),context);
const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-9,a+' ≠ '+b);
const base={rotate:0,flipH:false,flipV:false,crop:{x:0,y:0,w:1,h:1},brightness:100,contrast:100,saturation:100};

// Sem mudanças não há o que salvar; corte inteiro é enviado como "sem corte".
assert.equal(context.photoEditChanged(base),false);
assert.equal(context.photoEditOps(base).crop,null);
assert.equal(context.photoEditChanged({...base,brightness:110}),true);
const ops=context.photoEditOps({...base,rotate:90,flipH:true,crop:{x:.1,y:.2,w:.5,h:.25},contrast:120});
assert.equal(ops.rotate,90);assert.equal(ops.flip_h,true);assert.equal(ops.contrast,1.2);assert.equal(ops.crop.w,.5);
assert.equal(context.photoEditable({mime:'image/jpeg'}),true);assert.equal(context.photoEditable({mime:'image/gif'}),false);assert.equal(context.photoEditable({mime:'video/mp4'}),false);

// Proporção: 1:1 numa foto 2:1 usa metade da largura, centrado; 16:9 numa foto 4:3 usa toda a largura.
let c=context.photoRatioCrop(1,2);near(c.w,.5);near(c.h,1);near(c.x,.25);near(c.y,0);
c=context.photoRatioCrop(16/9,4/3);near(c.w,1);near(c.h,.75);near(c.y,.125);

// Arrasto: mover respeita as bordas; redimensionar respeita o tamanho mínimo e a imagem.
const start={x:.2,y:.2,w:.4,h:.4};
c=context.photoDragCrop(start,'move',.9,-.9,0);near(c.x,.6);near(c.y,0);near(c.w,.4);
c=context.photoDragCrop(start,'se',.1,.2,0);near(c.w,.5);near(c.h,.6);near(c.x,.2);
c=context.photoDragCrop(start,'nw',.9,.9,0);near(c.w,.05);near(c.h,.05);near(c.x+c.w,.6);near(c.y+c.h,.6);
c=context.photoDragCrop(start,'e',5,0,0);near(c.x+c.w,1);
// Proporção travada (largura/altura em frações = 2): o canto oposto fica parado e nada sai da imagem.
c=context.photoDragCrop({x:.2,y:.2,w:.4,h:.2},'se',.2,0,2);near(c.w/c.h,2);near(c.x,.2);near(c.y,.2);
c=context.photoDragCrop({x:.2,y:.2,w:.4,h:.2},'nw',-.9,-.9,2);near(c.w/c.h,2);near(c.x+c.w,.6);near(c.y+c.h,.4);assert.ok(c.x>=-1e-9&&c.y>=-1e-9);
c=context.photoDragCrop({x:.2,y:.2,w:.4,h:.2},'s',0,.9,2);near(c.w/c.h,2);assert.ok(c.x+c.w<=1+1e-9&&c.y+c.h<=1+1e-9);

// Foco: sem nitidez nem fundo suavizado não há o que enviar; sem objeto marcado, o fundo é ignorado.
const focus=f=>context.photoEditOps({...base,focus:{x:null,y:null,r:.25,sharpen:0,blur:0,...f}}).focus;
assert.equal(focus({}),null);assert.equal(focus({blur:60}),null);assert.equal(focus({x:.3,y:.4}),null);
let f=focus({sharpen:40,blur:60});assert.equal(f.x,null);assert.equal(f.sharpen,.4);assert.equal(f.blur,0);
f=focus({x:.3,y:.4,blur:60});assert.equal(f.x,.3);assert.equal(f.blur,.6);assert.equal(f.sharpen,0);
assert.equal(context.photoEditChanged({...base,focus:{x:null,y:null,r:.25,sharpen:10,blur:0}}),true);
assert.equal(context.photoFocusWeight(0,100),1);assert.equal(context.photoFocusWeight(60,100),1);assert.equal(context.photoFocusWeight(100,100),0);near(context.photoFocusWeight(80,100),.5);
// Pixels: no centro do objeto a diferença para a cópia borrada é ampliada; fora dele vale o fundo borrado.
const px=new Uint8ClampedArray(4*4*4).fill(100),soft=new Uint8ClampedArray(64).fill(90),back=new Uint8ClampedArray(64).fill(50);
context.photoFocusPixels(px,soft,back,4,4,{x:.125,y:.125,r:.5,sharpen:1,blur:1});
assert.equal(px[0],122);assert.equal(px[3],100,'alfa intacto');assert.equal(px[4*15],50);

// Filtros prontos: 100% dá os valores do filtro, 0% o neutro, 50% o meio; filtro desconhecido = neutro.
const golden=context.photoPresetValues('golden',100);assert.equal(golden.warmth,48);assert.equal(golden.saturation,118);assert.equal(golden.soften,0);
assert.equal(context.photoPresetValues('golden',50).warmth,24);assert.equal(context.photoPresetValues('golden',0).saturation,100);
assert.equal(context.photoPresetValues('',100).contrast,100);
context.PHOTO_PRESETS=vm.runInContext('PHOTO_PRESETS',context);
const groups=new Set(Array.from(context.PHOTO_PRESETS,p=>p.group));assert.ok(groups.has('Paisagem')&&groups.has('Pessoas'));
assert.equal(new Set(Array.from(context.PHOTO_PRESETS,p=>p.id)).size,context.PHOTO_PRESETS.length);
// Todo filtro fica dentro dos limites aceitos pelo servidor.
for(const p of context.PHOTO_PRESETS){const o=context.photoEditOps({...base,...context.photoPresetValues(p.id),focus:{x:null,y:null,r:.25,sharpen:context.photoPresetValues(p.id).sharpen,blur:0}});
  assert.ok(o.brightness>=.5&&o.brightness<=1.5&&o.contrast>=.5&&o.contrast<=1.5&&o.saturation>=0&&o.saturation<=2,p.id);
  if(o.look)assert.ok(Math.abs(o.look.warmth)<=1&&[o.look.vignette,o.look.fade,o.look.soften].every(v=>v>=0&&v<=1),p.id);assert.ok(context.photoEditChanged({...base,...context.photoPresetValues(p.id)})||o.focus,p.id)}
assert.equal(context.photoEditOps(base).look,null);assert.equal(context.photoEditOps({...base,warmth:-50}).look.warmth,-.5);
// Pixels do acabamento: mesmos números do servidor (cinza 120 quente = 142/120/98; desbotado = 130; canto com vinheta escuro).
const gray=()=>new Uint8ClampedArray(4*8*8).fill(120),whole={x:0,y:0,w:1,h:1},none={warmth:0,vignette:0,fade:0,soften:0};
let q=context.photoLookPixels(gray(),null,8,8,{...none,warmth:1},whole);assert.deepEqual([q[0],q[1],q[2]],[142,120,98]);
q=context.photoLookPixels(gray(),null,8,8,{...none,fade:1},whole);assert.equal(q[1],130);
q=context.photoLookPixels(gray(),null,8,8,{...none,vignette:1},whole);assert.ok(q[1]<45);assert.equal(q[4*(8*4+4)+1],120);
q=context.photoLookPixels(gray(),new Uint8ClampedArray(256).fill(100),8,8,{...none,soften:1},whole);assert.equal(q[0],110,'diferença 20 de 40: mistura metade');

// Pincel de apagar: tela -> original e de volta, em todos os giros e espelhos; os traços entram no que é salvo.
for(const rotate of [0,90,180,270])for(const flipH of [false,true])for(const flipV of [false,true]){
  const view={rotate,flipH,flipV},[x,y]=context.photoViewToOriginal(.2,.7,view),[u,v]=context.photoOriginalToView(x,y,view);near(u,.2);near(v,.7);
}
// Girar 90° à direita leva o canto superior esquerdo do original para o canto superior direito da tela.
let o2v=context.photoOriginalToView(0,0,{rotate:90});near(o2v[0],1);near(o2v[1],0);
o2v=context.photoOriginalToView(.1,.2,{rotate:0,flipH:true});near(o2v[0],.9);near(o2v[1],.2);
assert.equal(context.photoEditOps(base).erase,null);
const erased=context.photoEditOps({...base,erase:[{r:.02,pts:[[.1,.1]]}],erasePending:[{r:.03,pts:[[.5,.5]]}]});
assert.equal(erased.erase.length,2);assert.equal(context.photoEditChanged({...base,erasePending:[{r:.02,pts:[[.1,.1]]}]}),true);
console.log('photo editor ok');
