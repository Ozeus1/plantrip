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
  for(const {point,entries} of rows)publicMapLayers[point.level].addLayer(mapMarker(point,entries,()=>point.level==='attraction'?openMapGallery(point,entries):openMapDetail(point)));
  const trip=$('#publicTrip')?.value||'';
  if(publicMapTrip!==trip){
    const first=publicMapTrip===null;publicMapTrip=trip;
    if(trip)fitPublicMapPoints();else if(!first)publicMap.setView(...MAP_WORLD_VIEW);
  }
  syncPublicMapLevels();
  const hidden=publicDiaryData.map.unlocated.filter(id=>posts.some(e=>e.id===id)).length;
  $('#publicMapStatus').textContent=!rows.length?'Nenhuma memória com localização reconhecida para esta busca.':`${rows.filter(x=>x.point.level==='attraction').length} pontos com fotos no mapa. Aproxime para ver cidades e locais visitados.`+(hidden?` ${hidden} ${hidden===1?'memória sem localização reconhecida aparece':'memórias sem localização reconhecida aparecem'} apenas na lista.`:'');
}
function mapCountLabel(count){return `${count} ${count===1?'foto/vídeo':'fotos/vídeos'}`}
function mapMarker(point,entries,onClick){
  const count=mapMediaCount(entries),[w,h]=mapPinSize(point.level);
  const marker=L.marker([point.lat,point.lng],{icon:L.divIcon({html:`<span class="map-pin map-pin-${point.level}"><b>${count}</b></span>`,className:'map-pin-wrap',iconSize:[w,h],iconAnchor:[w/2,h/2]}),title:`${point.name} · ${memoryPostCount(entries.length)}`,alt:point.name,riseOnHover:true});
  marker.bindTooltip(`${esc(point.name)} · ${mapCountLabel(count)}`,{direction:'top',offset:[0,-h/2]});
  marker.on('click',onClick);
  return marker;
}
let mapDetailMap=null;
function mapDetailChildren(point){
  const rows=visiblePublicMapPoints(publicMapPosts);
  return point.level==='trip'?rows.filter(x=>x.point.level==='city'&&x.point.trip_id===point.trip_id):rows.filter(x=>x.point.level==='attraction'&&x.point.trip_id===point.trip_id&&x.point.city===point.name);
}
function openMapDetail(point){
  const self=visiblePublicMapPoints(publicMapPosts).find(x=>x.point.id===point.id);if(!self)return;
  const children=mapDetailChildren(point),parent=point.level==='city'?visiblePublicMapPoints(publicMapPosts).find(x=>x.point.level==='trip'&&x.point.trip_id===point.trip_id):null;
  let dialog=$('#mapDetail');
  if(!dialog){dialog=document.createElement('dialog');dialog.id='mapDetail';dialog.className='map-detail';document.body.append(dialog);dialog.addEventListener('close',()=>{mapDetailMap?.remove();mapDetailMap=null})}
  dialog.setAttribute('aria-label',`Mapa de ${point.name}`);
  const total=mapMediaCount(self.entries),childLabel=point.level==='trip'?'Cidades':'Pontos visitados';
  dialog.innerHTML=`<div class="modal-heading"><div><span class="eyebrow">${MAP_LEVELS[point.level].label}</span><h2>${esc(point.name)}</h2><p class="map-gallery-count">${children.length} ${point.level==='trip'?(children.length===1?'cidade':'cidades'):(children.length===1?'ponto':'pontos')} · ${memoryPostCount(self.entries.length)} · ${mapCountLabel(total)}</p></div><button type="button" class="close" data-detail-close aria-label="Fechar mapa">×</button></div><div class="map-gallery-actions">${parent?`<button type="button" data-detail-parent>← ${esc(parent.point.name)}</button>`:''}<button type="button" data-detail-all>▧ Ver todas as fotos</button><button type="button" data-detail-clip>▷ Miniclipe</button></div><div id="mapDetailCanvas" role="region" aria-label="Mapa ampliado de ${esc(point.name)}"></div><h3 class="map-detail-subtitle">${childLabel}</h3><ol class="map-detail-list">${children.map((x,i)=>{const cover=x.entries.flatMap(e=>e.files||[]).find(f=>f.mime.startsWith('image/'));return `<li><button type="button" data-detail-child="${i}">${cover?`<img src="/media/${cover.id}" alt="" loading="lazy">`:'<span class="map-detail-noimg">⌖</span>'}<span><strong>${esc(x.point.name)}</strong><small>${memoryPostCount(x.entries.length)} · ${mapCountLabel(mapMediaCount(x.entries))}</small><em>${point.level==='trip'?'Abrir mapa da cidade →':'Ver fotos →'}</em></span></button></li>`}).join('')}</ol>`;
  const openChild=x=>point.level==='trip'?openMapDetail(x.point):openMapGallery(x.point,x.entries);
  dialog.querySelector('[data-detail-close]').onclick=()=>dialog.close();
  dialog.querySelector('[data-detail-all]').onclick=()=>openMapGallery(point,self.entries);
  dialog.querySelector('[data-detail-clip]').onclick=()=>presentMemories(self.entries,true);
  if(parent)dialog.querySelector('[data-detail-parent]').onclick=()=>openMapDetail(parent.point);
  dialog.querySelectorAll('[data-detail-child]').forEach(b=>b.onclick=()=>openChild(children[Number(b.dataset.detailChild)]));
  if(!dialog.open)dialog.showModal();dialog.scrollTop=0;
  mapDetailMap?.remove();
  const map=mapDetailMap=L.map('mapDetailCanvas',{maxZoom:18,scrollWheelZoom:true,zoomSnap:.5});
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>'}).addTo(map);
  children.forEach(x=>mapMarker(x.point,x.entries,()=>openChild(x)).addTo(map));
  const coords=children.map(x=>[x.point.lat,x.point.lng]);
  if(coords.length>1)map.fitBounds(coords,{padding:[45,45],maxZoom:15});else map.setView(coords[0]||[point.lat,point.lng],point.level==='trip'?6:14);
  requestAnimationFrame(()=>map.invalidateSize());
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
  dialog.innerHTML=`<div class="modal-heading"><div><span class="eyebrow">${MAP_LEVELS[point.level].label}</span><h2>${esc(point.name)}</h2><p class="map-gallery-count">${memoryPostCount(entries.length)} · ${total} ${total===1?'foto/vídeo':'fotos/vídeos'}</p></div><button type="button" class="close" data-map-close aria-label="Fechar fotos">×</button></div><div class="map-gallery-actions"><button type="button" data-map-slides>▧ Ver slides</button><button type="button" data-map-clip>▷ Ver miniclipe</button></div>${entries.map(e=>`<article class="map-gallery-memory"><h3>${esc(e.title)}</h3><p>${esc(e.author)} · ${date(e.start)}${e.place?' · '+esc(e.place):''}</p>${e.description?`<p class="map-gallery-text">${esc(e.description)}</p>`:''}${memoryGallery(e)}</article>`).join('')}`;
  dialog.querySelector('[data-map-close]').onclick=()=>dialog.close();
  dialog.querySelector('[data-map-slides]').onclick=()=>presentMemories(entries,false);
  dialog.querySelector('[data-map-clip]').onclick=()=>presentMemories(entries,true);
  dialog.querySelectorAll('[data-memory-thumbnail]').forEach(b=>b.onclick=()=>presentMemories(entries,false,Number(b.dataset.memoryFile)));
  dialog.scrollTop=0;if(!dialog.open)dialog.showModal();
}
