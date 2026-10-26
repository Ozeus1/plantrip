const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const entry=(id,title,day='2026-10-29',place='Roma')=>({id,title,start:day+'T09:00',place,kind:'tour',trip_id:1});
const stops=[entry(3,'Pantheon'),entry(1,'Fontana di Trevi'),entry(2,'Piazza Navona')];
const link={setAttribute(){}};
const classes=()=>({toggle(){}});
const cards=[{dataset:{mapDay:'2026-10-29'},classList:classes()},{dataset:{mapDay:'2026-10-30'},classList:classes()}];
const buttons=cards.map(c=>({dataset:{selectMapDay:c.dataset.mapDay},setAttribute(){}}));
const context=vm.createContext({URLSearchParams,encodeURIComponent,console,
  memoryDay:s=>s?.slice(0,10),esc:String,
  state:{entries:[...stops,entry(4,'Coliseu','2026-10-30'),entry(5,'Paris','2026-10-29','Paris'),{...entry(6,'Outra viagem'),trip_id:2}]},
  $:()=>link,navigator:{userAgent:'desktop'},
  document:{querySelectorAll:selector=>selector==='[data-map-day]'?cards:selector==='[data-select-map-day]'?buttons:[]},
});
vm.runInContext(fs.readFileSync('static/attractions.js','utf8'),context);
vm.runInContext(`attractionData={entry:state.entries[0],guide:{}}`,context);
assert.deepEqual(Array.from(context.guideDayEntries('2026-10-29'),e=>e.id),[3,1,2]);
const params=new URL(context.guideDayMapUrl(stops)).searchParams;
assert.equal(params.get('origin'),'Pantheon Roma');
assert.equal(params.get('waypoints'),'Fontana di Trevi Roma');
assert.equal(params.get('destination'),'Piazza Navona Roma');
assert.equal(params.get('travelmode'),'walking');
assert.ok(context.guideDayMapUrl([stops[0]]).includes('/search/'));
assert.equal(context.guideDayMapUrl([]),'');
const custom={...stops[0],guide:{map_query:'Pantheon, Piazza della Rotonda, Rome'}};
assert.equal(new URL(context.guidePlaceMapUrl(custom)).searchParams.get('query'),custom.guide.map_query);
const many=Array.from({length:14},(_,i)=>entry(i,'Ponto '+i));
const segments=context.guideMapSegments(many,5);
assert.ok(segments.every(segment=>segment.entries.length<=5));
assert.deepEqual(Array.from(new Set(segments.flatMap(segment=>Array.from(segment.entries,e=>e.id)))),many.map(e=>e.id));
for(let i=1;i<segments.length;i++)assert.equal(segments[i-1].entries.at(-1).id,segments[i].entries[0].id);
const guide={route_summary:[{date:'2026-10-29'},{date:'2026-10-30'}]};
context.bindGuideDayMap(stops[0],guide);
assert.ok(link.href.includes('/dir/'));
assert.equal(new URL(link.href).searchParams.get('waypoints'),'Fontana di Trevi Roma');
cards[1].onclick({target:{closest:()=>null}});
assert.equal(new URL(link.href).searchParams.get('query'),'Coliseu Roma');
const before=link.href;cards[0].onclick({target:{closest:()=>({})}});assert.equal(link.href,before);
vm.runInContext(`guideMapSelection={mode:'place',date:'2026-10-29',id:3}`,context);
context.bindGuideDayMap(stops[0],guide);
assert.equal(new URL(link.href).searchParams.get('query'),'Pantheon Roma');
assert.ok(!new URL(link.href).searchParams.has('waypoints'));
console.log('Mapas por dia e por atração, sequência personalizada e trechos completos: OK');
