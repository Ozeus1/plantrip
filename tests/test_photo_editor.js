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
console.log('photo editor ok');
