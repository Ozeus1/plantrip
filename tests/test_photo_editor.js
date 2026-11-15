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
console.log('photo editor ok');
