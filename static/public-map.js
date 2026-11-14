const LEAFLET_ASSETS={css:['https://unpkg.com/leaflet@1.9.4/dist/leaflet.css','sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY='],js:['https://unpkg.com/leaflet@1.9.4/dist/leaflet.js','sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=']};
const MAP_LEVELS={trip:{label:'VIAGEM',min:0,max:4},city:{label:'CIDADE',min:5,max:9},attraction:{label:'LOCAL VISITADO',min:10,max:99}};
const MAP_WORLD_VIEW=[[25,10],2];
let leafletLoading=null,publicMap=null,publicMapLayers={},publicMapPosts=[],publicMapTrip=null,publicMapReady=false;
function loadLeaflet(){
  if(window.L)return Promise.resolve();
  if(leafletLoading)return leafletLoading;
  leafletLoading=new Promise((resolve,reject)=>{
    const link=document.createElement('link');link.rel='stylesheet';link.href=LEAFLET_ASSETS.css[0];link.integrity=LEAFLET_ASSETS.css[1];link.crossOrigin='';document.head.append(link);
    const script=document.createElement('script');script.src=LEAFLET_ASSETS.js[0];script.integrity=LEAFLET_ASSETS.js[1];script.crossOrigin='';
    script.onload=resolve;script.onerror=()=>reject(new Error('Leaflet indisponível'));document.head.append(script);
  }).catch(error=>{leafletLoading=null;throw error});
  return leafletLoading;
}
function publicMapMarkup(){return `<section class="public-map" aria-labelledby="publicMapTitle"><div class="public-map-heading"><div><span class="eyebrow">MAPA MUNDI</span><h2 id="publicMapTitle">Onde as histórias aconteceram</h2><p>Amplie o mapa para ir da viagem às cidades e aos pontos visitados. Toque em um ponto para abrir as fotos.</p></div><div class="public-map-actions"><button type="button" id="publicMapWorld">◌ Mundo</button><button type="button" id="publicMapFit">⌖ Ir aos pontos</button></div></div><div id="publicMapCanvas" role="region" aria-label="Mapa mundi com as viagens e os pontos visitados"></div><p id="publicMapStatus" class="public-map-status" role="status"></p></section>`}
function mapMediaCount(entries){return entries.reduce((n,e)=>n+(e.files||[]).filter(f=>/^(image|video)\//.test(f.mime)).length,0)}
function mapPinSize(level){return level==='trip'?[52,52]:level==='city'?[40,40]:[32,32]}
async function initPublicMap(){
  const canvas=$('#publicMapCanvas');if(!canvas)return;
  publicMapReady=false;publicMapTrip=null;
  try{await loadLeaflet()}catch{if($('#publicMapCanvas')===canvas)canvas.innerHTML='<div class="public-map-error">Não foi possível carregar o mapa agora. As memórias continuam disponíveis na lista abaixo.</div>';return}
  if($('#publicMapCanvas')!==canvas)return;
  publicMap?.remove();
  const map=publicMap=L.map(canvas,{minZoom:2,maxZoom:18,worldCopyJump:true,scrollWheelZoom:false,zoomSnap:.5});
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>'}).addTo(map);
  publicMapLayers=Object.fromEntries(Object.keys(MAP_LEVELS).map(level=>[level,L.layerGroup()]));
  map.on('click focus',()=>map.scrollWheelZoom.enable());map.on('mouseout blur',()=>map.scrollWheelZoom.disable());
  map.on('zoomend',syncPublicMapLevels);
  map.setView(...MAP_WORLD_VIEW);
  $('#publicMapWorld').onclick=()=>map.setView(...MAP_WORLD_VIEW);
  $('#publicMapFit').onclick=()=>fitPublicMapPoints();
  publicMapReady=true;updatePublicMap(publicMapPosts);
}
function visiblePublicMapPoints(posts){
  const ids=new Map(posts.map(e=>[e.id,e]));
  return (publicDiaryData?.map?.points||[]).map(p=>({point:p,entries:p.entry_ids.map(id=>ids.get(id)).filter(Boolean).sort((a,b)=>String(a.start).localeCompare(String(b.start)))})).filter(x=>x.entries.length);
}
function fitPublicMapPoints(){
  const cities=publicMapLayers.city.getLayers().map(m=>m.getLatLng());
  if(cities.length)publicMap.fitBounds(L.latLngBounds(cities),{padding:[50,50],maxZoom:cities.length===1?9:6});
}
function updatePublicMap(posts){
  publicMapPosts=posts;if(!publicMapReady||!publicMap)return;
  Object.values(publicMapLayers).forEach(layer=>layer.clearLayers());
  const rows=visiblePublicMapPoints(posts);
  for(const {point,entries} of rows){
    const count=mapMediaCount(entries),[w,h]=mapPinSize(point.level);
    const marker=L.marker([point.lat,point.lng],{icon:L.divIcon({html:`<span class="map-pin map-pin-${point.level}"><b>${count}</b></span>`,className:'map-pin-wrap',iconSize:[w,h],iconAnchor:[w/2,h/2]}),title:`${point.name} · ${memoryPostCount(entries.length)}`,alt:point.name,riseOnHover:true});
    marker.bindTooltip(`${esc(point.name)} · ${count} ${count===1?'foto/vídeo':'fotos/vídeos'}`,{direction:'top',offset:[0,-h/2]});
    marker.on('click',()=>openMapGallery(point,entries));
    publicMapLayers[point.level].addLayer(marker);
  }
  const trip=$('#publicTrip')?.value||'';
  if(publicMapTrip!==trip){
    const first=publicMapTrip===null;publicMapTrip=trip;
    if(trip)fitPublicMapPoints();else if(!first)publicMap.setView(...MAP_WORLD_VIEW);
  }
  syncPublicMapLevels();
  const hidden=publicDiaryData.map.unlocated.filter(id=>posts.some(e=>e.id===id)).length;
  $('#publicMapStatus').textContent=!rows.length?'Nenhuma memória com localização reconhecida para esta busca.':`${rows.filter(x=>x.point.level==='attraction').length} pontos com fotos no mapa. Aproxime para ver cidades e locais visitados.`+(hidden?` ${hidden} ${hidden===1?'memória sem localização reconhecida aparece':'memórias sem localização reconhecida aparecem'} apenas na lista.`:'');
}
function syncPublicMapLevels(){
  if(!publicMap)return;const zoom=publicMap.getZoom();
  for(const [level,range] of Object.entries(MAP_LEVELS)){
    const layer=publicMapLayers[level],visible=zoom>=range.min&&zoom<=range.max;
    if(visible&&!publicMap.hasLayer(layer))layer.addTo(publicMap);
    if(!visible&&publicMap.hasLayer(layer))publicMap.removeLayer(layer);
  }
}
function openMapGallery(point,entries){
  let dialog=$('#mapGallery');
  if(!dialog){dialog=document.createElement('dialog');dialog.id='mapGallery';dialog.className='map-gallery';dialog.setAttribute('aria-label','Fotos do ponto selecionado');document.body.append(dialog)}
  const total=mapMediaCount(entries);
  dialog.innerHTML=`<div class="modal-heading"><div><span class="eyebrow">${MAP_LEVELS[point.level].label}</span><h2>${esc(point.name)}</h2><p class="map-gallery-count">${memoryPostCount(entries.length)} · ${total} ${total===1?'foto/vídeo':'fotos/vídeos'}</p></div><button type="button" class="close" data-map-close aria-label="Fechar fotos">×</button></div><div class="map-gallery-actions"><button type="button" data-map-slides>▧ Ver slides</button><button type="button" data-map-clip>▷ Ver miniclipe</button>${point.level!=='attraction'?'<button type="button" data-map-zoom>⌖ Aproximar no mapa</button>':''}</div>${entries.map(e=>`<article class="map-gallery-memory"><h3>${esc(e.title)}</h3><p>${esc(e.author)} · ${date(e.start)}${e.place?' · '+esc(e.place):''}</p>${e.description?`<p class="map-gallery-text">${esc(e.description)}</p>`:''}${memoryGallery(e)}</article>`).join('')}`;
  dialog.querySelector('[data-map-close]').onclick=()=>dialog.close();
  dialog.querySelector('[data-map-slides]').onclick=()=>presentMemories(entries,false);
  dialog.querySelector('[data-map-clip]').onclick=()=>presentMemories(entries,true);
  const zoom=dialog.querySelector('[data-map-zoom]');
  if(zoom)zoom.onclick=()=>{dialog.close();publicMap.setView([point.lat,point.lng],point.level==='trip'?5:11)};
  dialog.querySelectorAll('[data-memory-thumbnail]').forEach(b=>b.onclick=()=>presentMemories(entries,false,Number(b.dataset.memoryFile)));
  dialog.scrollTop=0;if(!dialog.open)dialog.showModal();
}
