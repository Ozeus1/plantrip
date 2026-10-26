const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const nodes=new Map();
const node=selector=>{if(!nodes.has(selector))nodes.set(selector,{hidden:false,innerHTML:'',textContent:'',value:''});return nodes.get(selector)};
let opened=null,bound=0;
const context=vm.createContext({
  console,esc:s=>String(s??'').replaceAll('&','&amp;').replaceAll('"','&quot;').replaceAll('<','&lt;'),
  $:node,document:{querySelectorAll:()=>[]},resetAttractionLayout:()=>{},
  bindActions:()=>bound++,openEditor:(entry,kind)=>opened=kind,
  empty:(title,body,action)=>`${title}|${action}`,
  state:{user:{role:'admin'},trip_id:1,entries:[
    {id:1,kind:'documents',title:'Passaportes',place:'',description:'',files:[]},
    {id:2,kind:'logistics',title:'Hotel Roma',place:'Roma',description:'',files:[{id:8,name:'reserva.pdf'}]},
    {id:3,kind:'logistics',title:'Voo sem anexos',place:'',description:'',files:[]},
    {id:4,kind:'diary',title:'Memória privada',place:'',description:'',files:[{id:9,name:'foto.jpg'}]},
  ]},filter:'',
});
vm.runInContext(fs.readFileSync('static/accounts-documents.js','utf8'),context);
context.renderDocuments();
assert.ok(node('#documentResults').innerHTML.includes('Passaportes'));
assert.ok(node('#documentResults').innerHTML.includes('Hotel Roma'));
assert.ok(node('#documentResults').innerHTML.includes('/media/8'));
assert.ok(!node('#documentResults').innerHTML.includes('Voo sem anexos'));
assert.ok(!node('#documentResults').innerHTML.includes('Memória privada'));
node('#add').onclick();assert.equal(opened,'documents');assert.equal(bound,1);
node('#documentSearch').oninput({target:{value:'reserva.pdf'}});
assert.ok(node('#documentResults').innerHTML.includes('Hotel Roma'));
assert.ok(!node('#documentResults').innerHTML.includes('Passaportes'));
context.state.user.role='member';context.renderDocuments();assert.equal(node('#add').hidden,true);
assert.ok(context.avatarHtml({name:'Ana',photo:'data:image/png;base64,abc'}).includes('<img'));
assert.ok(context.avatarHtml({name:'Ana'}).includes('>A</span>'));
console.log('Documentação: anexos antigos, busca, acesso e fotos: OK');
