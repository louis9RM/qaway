/* Qaway — frontend (mapa real MapLibre + polígono + GPS + voz + capas SAR demo) */
(function(){
"use strict";
const CFG = window.SARVIGIA_CONFIG;

// ---------- Datos ----------
const DATES = ['19 Jun','01 Jul','13 Jul','25 Jul','06 Ago','18 Ago','30 Ago','11 Sep','23 Sep','05 Oct','17 Oct','29 Oct'];
const LAYERS = [
  {id:'gunw', name:'Deformación', sub:'GUNW · mm línea de vista', on:true},
  {id:'gcov', name:'Cambios', sub:'GCOV · retrodispersión', on:false},
  {id:'coh',  name:'Coherencia', sub:'confiabilidad del dato', on:false},
  {id:'opt',  name:'Óptico (contexto)', sub:'solo mapa base', on:false},
];

let state = {layer:'gunw', t:11, aoi:null, playing:false, drawing:false, geoms:[], geomIdx:0, idioma:"en", nivel:"sencillo", ubicacion:null, autoAnalizar:false};
let drawPts = [];

function growth(t){ const f=t/(DATES.length-1); return Math.pow(f,1.7)*0.85 + f*0.15; }
// campo de deformación procedural (varía en el espacio y crece en el tiempo)
function field(lon,lat){
  let v = Math.sin(lon*120+2)*Math.cos(lat*110) + 0.6*Math.sin(lon*260-lat*150) + 0.4*Math.cos(lon*90+lat*200);
  return Math.max(0,Math.min(1, v*0.5+0.5));
}
function deformAt(lon,lat,t){ return -field(lon,lat)*growth(t)*46; } // mm (negativo = hundimiento)

function colDeform(mm){
  const t=Math.max(-40,Math.min(10,mm));
  if(t<0){const k=(-t)/40;return `rgba(${40+k*200|0},${90+k*40|0},${230-k*60|0},${0.15+0.7*k})`;}
  const k=t/10;return `rgba(240,${90-k*30|0},${80-k*30|0},${0.15+0.5*k})`;
}
function colChange(mm){const k=Math.min(1,Math.abs(mm)/40);return `rgba(242,177,52,${0.08+0.7*k})`;}
function colCoh(lon,lat){
  const veg=0.5+0.5*Math.sin(lon*210)*Math.cos(lat*180);
  const coh=Math.max(0,Math.min(1,0.8-veg*0.4));
  return `rgba(${50+coh*20|0},${120+coh*110|0},${90+coh*60|0},${0.2+0.5*(1-coh)})`;
}

function buildOverlay(bbox,t,layer){
  if(layer==='opt') return {type:'FeatureCollection',features:[]};
  const [w,s,e,n]=bbox, cols=26, rows=22;
  const dx=(e-w)/cols, dy=(n-s)/rows, feats=[];
  for(let j=0;j<rows;j++)for(let i=0;i<cols;i++){
    const lon=w+(i+0.5)*dx, lat=s+(j+0.5)*dy;
    let color,keep=true;
    if(layer==='gunw'){const mm=deformAt(lon,lat,t); keep=Math.abs(mm)>=2; color=colDeform(mm);}
    else if(layer==='gcov'){const mm=deformAt(lon,lat,t); keep=Math.abs(mm)>=4; color=colChange(mm);}
    else {color=colCoh(lon,lat);}
    if(!keep) continue;
    const x0=w+i*dx,y0=s+j*dy,x1=x0+dx,y1=y0+dy;
    feats.push({type:'Feature',properties:{color},geometry:{type:'Polygon',
      coordinates:[[[x0,y0],[x1,y0],[x1,y1],[x0,y1],[x0,y0]]]}});
  }
  return {type:'FeatureCollection',features:feats};
}

// ---------- Mapa (bases NASA GIBS + OSM) ----------
const BASES = CFG.BASEMAPS || {osm:{tiles:CFG.OSM_TILES,maxzoom:19,attribution:'© OpenStreetMap',label:'Calles'}};
let activeBase = CFG.DEFAULT_BASE || Object.keys(BASES)[0];
const _baseSources={}, _baseLayers=[];
for(const [id,b] of Object.entries(BASES)){
  _baseSources['b_'+id]={type:'raster',tiles:b.tiles,tileSize:256,maxzoom:b.maxzoom||19,attribution:b.attribution||''};
  _baseLayers.push({id:'base_'+id,type:'raster',source:'b_'+id,layout:{visibility:id===activeBase?'visible':'none'}});
}
// capa transparente de carreteras/rótulos (para superponer sobre imágenes NASA)
if(CFG.LABELS_OVERLAY){
  _baseSources['b_labels']={type:'raster',tiles:CFG.LABELS_OVERLAY,tileSize:256,attribution:'© CARTO'};
  _baseLayers.push({id:'base_labels',type:'raster',source:'b_labels',
    layout:{visibility:(BASES[activeBase]&&BASES[activeBase].labels)?'visible':'none'}});
}
const map = new maplibregl.Map({
  container:'map',
  style:{version:8, sources:_baseSources, layers:_baseLayers},
  center:CFG.MAP_CENTER, zoom:CFG.MAP_ZOOM, attributionControl:true
});

function setBase(id){
  if(!BASES[id]) return; activeBase=id;
  for(const k of Object.keys(BASES)) map.setLayoutProperty('base_'+k,'visibility',k===id?'visible':'none');
  if(map.getLayer('base_labels')) map.setLayoutProperty('base_labels','visibility', BASES[id].labels?'visible':'none');
  document.querySelectorAll('#basemaps button').forEach(b=>b.classList.toggle('on',b.dataset.b===id));
  document.body.classList.toggle('imagery-base', id!=='osm'); // no invertir imágenes NASA en modo oscuro
}
(function buildBasemapSwitcher(){
  document.body.classList.toggle('imagery-base', activeBase!=='osm');
  const el=document.getElementById('basemaps'); if(!el) return;
  if(Object.keys(BASES).length < 2){ el.style.display='none'; return; }  // 1 sola base → sin selector
  el.innerHTML=Object.entries(BASES).map(([id,b])=>`<button data-b="${id}" class="${id===activeBase?'on':''}">${b.label||id}</button>`).join('');
  el.querySelectorAll('button').forEach(btn=>btn.onclick=()=>setBase(btn.dataset.b));
})();

map.on('load',()=>{
  map.addSource('sar',{type:'geojson',data:empty()});
  map.addLayer({id:'sar-fill',type:'fill',source:'sar',
    paint:{'fill-color':['get','color'],'fill-outline-color':'rgba(0,0,0,0)'}});
  map.addSource('aoi',{type:'geojson',data:empty()});
  map.addLayer({id:'aoi-fill',type:'fill',source:'aoi',
    paint:{'fill-color':'#34d1c4','fill-opacity':0.12}});
  map.addLayer({id:'aoi-line',type:'line',source:'aoi',
    paint:{'line-color':'#34d1c4','line-width':2,'line-dasharray':[2,1.5]}});
  map.addSource('draw',{type:'geojson',data:empty()});
  map.addLayer({id:'draw-line',type:'line',source:'draw',paint:{'line-color':'#f2b134','line-width':2}});
  map.addLayer({id:'draw-pts',type:'circle',source:'draw',filter:['==','$type','Point'],
    paint:{'circle-radius':4,'circle-color':'#f2b134'}});
});
function empty(){return {type:'FeatureCollection',features:[]};}

// clic/doble-clic para dibujar
map.on('click',e=>{ if(!state.drawing) return; drawPts.push([e.lngLat.lng,e.lngLat.lat]); updateDrawSource(); });
map.on('dblclick',e=>{ if(!state.drawing) return; e.preventDefault(); finishDraw(); });

function updateDrawSource(){
  const feats=drawPts.map(p=>({type:'Feature',geometry:{type:'Point',coordinates:p},properties:{}}));
  if(drawPts.length>=2) feats.push({type:'Feature',geometry:{type:'LineString',coordinates:drawPts},properties:{}});
  map.getSource('draw').setData({type:'FeatureCollection',features:feats});
}

function finishDraw(){
  if(drawPts.length<3){ toast('Mark at least 3 points.'); return; }
  const ring=[...drawPts,drawPts[0]];
  const lons=ring.map(p=>p[0]), lats=ring.map(p=>p[1]);
  const bbox=[Math.min(...lons),Math.min(...lats),Math.max(...lons),Math.max(...lats)];
  const wkt='POLYGON(('+ring.map(p=>p[0].toFixed(4)+' '+p[1].toFixed(4)).join(',')+'))';
  state.aoi={bbox,wkt,center:[(bbox[0]+bbox[2])/2,(bbox[1]+bbox[3])/2],name:'Área dibujada'};
  map.getSource('aoi').setData({type:'FeatureCollection',features:[
    {type:'Feature',geometry:{type:'Polygon',coordinates:[ring]},properties:{}}]});
  map.getSource('draw').setData(empty());
  drawPts=[]; state.drawing=false; map.getCanvas().style.cursor='';
  if(map.doubleClickZoom) map.doubleClickZoom.enable();
  const info=(document.getElementById('aoiinfo')||{classList:{add(){},remove(){}}}); info.textContent=wkt; info.classList.add('show');
  document.getElementById('clear').style.display='';
  (document.getElementById('maphint')||{style:{}}).style.display='none';
  refreshOverlay(); updateReadout();
  buscarFechas();   // paso 2: buscar fechas disponibles
}

// ---------- Paso 2: buscar pasadas — Qaway elige SOLO las 2 últimas (automático) ----------
async function buscarFechas(){
  const hint=document.getElementById('drawhint');
  if(CFG.DEMO_MODE){ hint.textContent='Modo demo: pulsa “Analizar área”.'; document.getElementById('analyze').disabled=false; return; }
  hint.textContent='Searching available NISAR passes…';
  const analyze=document.getElementById('analyze');
  try{
    const res=await fetch(CFG.API_BASE+'/buscar',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({wkt:state.aoi.wkt})});
    if(!res.ok) throw new Error('HTTP '+res.status);
    const data=await res.json();
    state.geoms=data.geometrias||[];
    if(!state.geoms.length){ hint.textContent='No NISAR coverage here yet.'; analyze.disabled=true; return; }
    state.geomIdx=0;  // el backend ya ordena: geometría con la cobertura más reciente
    const ult=fechasUltimas2(state.geoms[0]);
    if(ult.length<2){ hint.textContent='Only 1 NISAR pass here; 2 are needed to compare. Waiting for the next pass.'; analyze.disabled=true; return; }
    hint.textContent='Qaway will use the 2 most recent passes: '+ult.join(' → ')+'.';
    analyze.disabled=false;
    if(state.autoAnalizar){ state.autoAnalizar=false; analyzeAOI(); }  // voz/GPS → análisis automático
  }catch(err){ hint.textContent='Could not reach the backend.'; analyze.disabled=true; }
}

// las 2 fechas más recientes (distintas) de una geometría
function fechasUltimas2(g){
  if(!g||!g.fechas) return [];
  return [...new Set(g.fechas.map(f=>f.fecha))].sort().slice(-2);
}

// Qaway toma automáticamente los gránulos de las 2 últimas fechas (sin menús)
function granulosSeleccionados(){
  const g=state.geoms[state.geomIdx]; if(!g||!g.fechas) return [];
  const porFecha={}; g.fechas.forEach(f=>{ porFecha[f.fecha]=f.granule; });
  return fechasUltimas2(g).map(fx=>porFecha[fx]).filter(Boolean);
}

function clearAOI(){
  state.aoi=null; drawPts=[]; state.drawing=false; map.getCanvas().style.cursor='';
  if(map.doubleClickZoom) map.doubleClickZoom.enable();
  map.getSource('aoi').setData(empty()); map.getSource('draw').setData(empty()); map.getSource('sar').setData(empty());
  (document.getElementById('aoiinfo')||{classList:{add(){},remove(){}}}).classList.remove('show');
  document.getElementById('analyze').disabled=true;
  document.getElementById('clear').style.display='none';
  // (menú de fechas eliminado)
  state.geoms=[]; state.geomIdx=0;
  document.getElementById('drawhint').textContent='';
  (document.getElementById('maphint')||{style:{}}).style.display='';
  resetReadout();
}

function refreshOverlay(){
  // Sin overlay simulado: el mapa solo muestra el corredor/polígono real.
  if(map.getSource('sar')) map.getSource('sar').setData(empty());
}

// ---------- Lectura ----------
function resetReadout(){ const e=document.getElementById('explain'); if(e) e.innerHTML=''; }
function updateReadout(){ /* El diagnóstico real lo da el agente por voz, no un texto fijo. */ }

// ---------- Paneles ----------
function buildLayers(){
  const lc=document.getElementById('layers');
  lc.innerHTML=LAYERS.map(l=>`<div class="layer ${l.id===state.layer?'on':''}" data-l="${l.id}">
    <span class="sw"></span><span class="meta">${l.name}<small>${l.sub}</small></span></div>`).join('');
  lc.querySelectorAll('.layer').forEach(el=>el.onclick=()=>{state.layer=el.dataset.l;buildLayers();syncLegend();refreshOverlay();updateReadout();});
}
function syncLegend(){
  const t=document.getElementById('legTitle'),r=document.getElementById('ramp');if(!t)return;const
    mn=document.getElementById('legMin'),mx=document.getElementById('legMax');
  if(state.layer==='gunw'){t.textContent='Deformación (mm)';r.style.background='linear-gradient(90deg,#2a7af0,#95a8c0,#ef4a52)';mn.textContent='−40';mx.textContent='+10';}
  else if(state.layer==='gcov'){t.textContent='Cambio (GCOV)';r.style.background='linear-gradient(90deg,transparent,#f2b134)';mn.textContent='0';mx.textContent='alto';}
  else if(state.layer==='coh'){t.textContent='Coherencia';r.style.background='linear-gradient(90deg,#1a2a20,#2fbf71)';mn.textContent='baja';mx.textContent='alta';}
  else {t.textContent='Mapa base';r.style.background='linear-gradient(90deg,#556,#99a)';mn.textContent='';mx.textContent='';}
}
function buildTicks(){ document.getElementById('ticks').innerHTML=DATES.map((d,i)=>i%2===0?`<span>${d.split(' ')[0]}</span>`:'<span></span>').join(''); }
function syncDates(){ document.getElementById('dA').textContent=DATES[0]; document.getElementById('dB').textContent=DATES[state.t]; }

// ---------- Dibujar / Analizar / Borrar ----------
document.getElementById('draw').onclick=()=>{
  state.drawing=true; drawPts=[]; map.getCanvas().style.cursor='crosshair';
  if(map.doubleClickZoom) map.doubleClickZoom.disable();
  map.getSource('aoi') && map.getSource('aoi').setData(empty());
  document.getElementById('drawhint').textContent='Tap points on the map; double-tap to close.';
  (document.getElementById('maphint')||{style:{}}).style.display='';
  (document.getElementById('maphint')||{style:{}}).innerHTML='Toca el mapa para marcar puntos; <b>doble toque</b> para cerrar el polígono.';
  closeSide();
};
document.getElementById('clear').onclick=clearAOI;
document.getElementById('analyze').onclick=analyzeAOI;

function demoJob(){
  const ov=document.getElementById('joboverlay'),bar=document.getElementById('jobbar'),step=document.getElementById('jobstep');
  ov.classList.add('show'); bar.style.width='6%';
  const steps=['Agrupando por geometría…','Descargando par NISAR…','Recortando al polígono…','Detectando cambios…','Generando capas…'];
  let k=0; const iv=setInterval(()=>{k++;step.textContent=steps[Math.min(k,steps.length-1)];
    bar.style.width=Math.min(100,6+k*20)+'%';
    if(k>=steps.length){clearInterval(iv);setTimeout(()=>{ov.classList.remove('show');refreshOverlay();},500);}},700);
}

async function analyzeAOI(){
  if(!state.aoi) return;
  if(CFG.DEMO_MODE){ demoJob(); return; }
  const granulos=granulosSeleccionados();
  if(!granulos.length){ toast('Choose the dates to analyze.'); return; }
  const ov=document.getElementById('joboverlay'),bar=document.getElementById('jobbar'),step=document.getElementById('jobstep');
  ov.classList.add('show'); bar.style.width='8%'; step.textContent='Sending request…';
  try{
    const res=await fetch(CFG.API_BASE+'/analisis',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({granulos, wkt:state.aoi.wkt, bbox:state.aoi.bbox})});
    if(!res.ok) throw new Error('HTTP '+res.status);
    const job=await res.json();
    seguirJob(job.id);
  }catch(err){ step.textContent='Error: '+err.message; setTimeout(()=>ov.classList.remove('show'),1500); }
}

function seguirJob(id){
  const ov=document.getElementById('joboverlay'),bar=document.getElementById('jobbar'),step=document.getElementById('jobstep');
  let fallos=0;
  const poll=setInterval(async()=>{
    try{
      const r=await fetch(CFG.API_BASE+'/jobs/'+id);
      if(r.status===404){ clearInterval(poll);  // el job se perdió (servidor reiniciado)
        step.textContent='The analysis was lost (server restarted). Try again.';
        setTimeout(()=>ov.classList.remove('show'),3000); return; }
      const j=await r.json();
      if(!j || !j.status){ if(++fallos>5){ clearInterval(poll);
        step.textContent='Could not track the analysis. Try again.'; setTimeout(()=>ov.classList.remove('show'),3000); } return; }
      fallos=0;
      bar.style.width=(j.progress||10)+'%'; step.textContent=j.step||j.status;
      if(j.status==='done'){ clearInterval(poll);
        bar.style.width='100%';
        const stats=j.result && j.result.stats;
        if(stats && !stats.error){
          step.textContent='Analysis complete. Qaway will tell you the result…';
          setTimeout(()=>{ov.classList.remove('show');},1000);
          narrarAnalisis(stats);
        }else{
          step.textContent=(stats && stats.error) || 'Analysis complete.';
          setTimeout(()=>{ov.classList.remove('show');refreshOverlay();updateReadout();},2200);
        }
      }else if(j.status==='failed'){ clearInterval(poll);
        step.textContent='Error: '+(j.error||'unknown'); setTimeout(()=>ov.classList.remove('show'),2800);
      }
    }catch(err){ clearInterval(poll); step.textContent='Lost connection to the job.'; setTimeout(()=>ov.classList.remove('show'),2000); }
  },2000);
}

// El agente narra por audio el resultado REAL del polígono analizado
async function narrarAnalisis(stats){
  const contexto={zona: state.aoi?state.aoi.name:'tu zona', bbox: state.aoi?state.aoi.bbox:null, stats_cambio: stats};
  const pregunta = state.idioma==='en'
    ? 'Give me the diagnosis of the area I just analyzed with NISAR.'
    : 'Dame el diagnóstico de la zona que acabo de analizar con NISAR.';
  try{
    const res=await fetch(CFG.API_BASE+'/preguntar',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({pregunta, idioma:state.idioma, nivel:state.nivel, contexto})});
    const d=await res.json();
    const txt=d.respuesta||'';
    speak(txt);
    toast('Qaway analyzed your area ✔',3000);
  }catch(e){ toast('Analysis ready, but I could not narrate it.',3500); }
}

// ---------- Tema / menú / util ----------
document.getElementById('theme').onclick=()=>{
  const cur=document.documentElement.getAttribute('data-theme');
  const isLight = cur==='light' || (!cur && matchMedia('(prefers-color-scheme: light)').matches);
  document.documentElement.setAttribute('data-theme', isLight?'dark':'light');
};
const side=document.getElementById('side'),scrim=document.getElementById('scrim');
function openSide(){side.classList.add('open');scrim.classList.add('show');}
function closeSide(){side.classList.remove('open');scrim.classList.remove('show');}
document.getElementById('hamb').onclick=()=> side.classList.contains('open')?closeSide():openSide();
scrim.onclick=closeSide;
document.getElementById('about').onclick=()=>toast('SAR = radar that measures the surface day/night and through clouds. NISAR (L-band) sees under vegetation and detects millimeter movements → early landslide warning.',6000);

let toastTimer=null;
function toast(msg,ms=3200){
  let el=document.getElementById('toast');
  if(!el){el=document.createElement('div');el.id='toast';
    el.style.cssText='position:fixed;left:50%;bottom:92px;transform:translateX(-50%);z-index:60;max-width:88vw;'+
      'background:var(--panel);border:1px solid var(--line);color:var(--fg);padding:11px 15px;border-radius:11px;'+
      'box-shadow:var(--shadow);font:500 12.5px var(--body);line-height:1.4';
    document.body.appendChild(el);}
  el.textContent=msg; el.style.opacity='1';
  clearTimeout(toastTimer); toastTimer=setTimeout(()=>{el.style.opacity='0';el.style.transition='opacity .4s';},ms);
}

// ---------- Agente Qaway: GPS "analizar a la redonda" ----------
function kmToDegLat(km){ return km/111.0; }
function kmToDegLon(km,lat){ return km/(111.320*Math.cos(lat*Math.PI/180)); }

function setAOIFromRing(ring,name){
  const lons=ring.map(p=>p[0]), lats=ring.map(p=>p[1]);
  const bbox=[Math.min(...lons),Math.min(...lats),Math.max(...lons),Math.max(...lats)];
  const wkt='POLYGON(('+ring.map(p=>p[0].toFixed(4)+' '+p[1].toFixed(4)).join(',')+'))';
  state.aoi={bbox,wkt,center:[(bbox[0]+bbox[2])/2,(bbox[1]+bbox[3])/2],name:name||'Área'};
  map.getSource('aoi').setData({type:'FeatureCollection',features:[
    {type:'Feature',geometry:{type:'Polygon',coordinates:[ring]},properties:{}}]});
  const info=(document.getElementById('aoiinfo')||{classList:{add(){},remove(){}}}); info.textContent=wkt; info.classList.add('show');
  document.getElementById('clear').style.display='';
  (document.getElementById('maphint')||{style:{}}).style.display='none';
  refreshOverlay(); updateReadout();
  buscarFechas();
}

// dibuja un polígono de 'km' de radio alrededor de (lon,lat).
// Nota: el agente optimizará este polígono para que la carretera quede dentro (próximo paso backend).
function analizarALaRedonda(lon,lat,km){
  const dLat=kmToDegLat(km), dLon=kmToDegLon(km,lat);
  const ring=[[lon-dLon,lat-dLat],[lon+dLon,lat-dLat],[lon+dLon,lat+dLat],[lon-dLon,lat+dLat],[lon-dLon,lat-dLat]];
  map.flyTo({center:[lon,lat],zoom:Math.max(12.5,13.5-Math.log2(km))});
  setAOIFromRing(ring, `A ${km} km a la redonda`);
}

function setAOIFromGeometry(geom,name){
  const bb=turf.bbox(geom); // [minX,minY,maxX,maxY]
  const bbox=[bb[0],bb[1],bb[2],bb[3]];
  const corners=[[bb[0],bb[1]],[bb[2],bb[1]],[bb[2],bb[3]],[bb[0],bb[3]],[bb[0],bb[1]]];
  const wkt='POLYGON(('+corners.map(p=>p[0].toFixed(4)+' '+p[1].toFixed(4)).join(',')+'))';
  state.aoi={bbox,wkt,center:[(bb[0]+bb[2])/2,(bb[1]+bb[3])/2],name:name||'Área'};
  map.getSource('aoi').setData({type:'Feature',geometry:geom,properties:{}});
  const info=(document.getElementById('aoiinfo')||{classList:{add(){},remove(){}}}); info.textContent=wkt; info.classList.add('show');
  document.getElementById('clear').style.display='';
  (document.getElementById('maphint')||{style:{}}).style.display='none';
  refreshOverlay(); updateReadout();
  buscarFechas();
}

// 🧠 Agente Qaway: traza un CORREDOR que circunscribe la carretera cercana
// (no un cuadrado ciego) → solo analiza/descarga lo relevante, sin el "ruido" de cerros lejanos.
async function analizarCorredor(lon,lat,searchKm){
  if(typeof turf==='undefined'){ analizarALaRedonda(lon,lat,searchKm); return; }
  toast('🛣️ Finding the nearest main road…',3500);
  const r=Math.round(searchKm*1000);
  const q=`[out:json][timeout:25];way["highway"~"motorway|trunk|primary|secondary|tertiary|unclassified|road"](around:${r},${lat},${lon});out geom;`;
  try{
    const res=await fetch('https://overpass-api.de/api/interpreter',{method:'POST',body:q});
    if(!res.ok) throw new Error('overpass '+res.status);
    const data=await res.json();
    const lines=(data.elements||[]).filter(e=>e.geometry&&e.geometry.length>1)
      .map(e=>turf.lineString(e.geometry.map(g=>[g.lon,g.lat])));
    if(!lines.length){ toast('No mapped road nearby; using the area around you.',4500); analizarALaRedonda(lon,lat,searchKm); return; }
    const half=Math.min(0.5,Math.max(0.05,searchKm*0.4)); // ancho del corredor (km, a cada lado)
    const fc=turf.featureCollection(lines);
    const buffered=turf.buffer(fc,half,{units:'kilometers'});
    let corridor=buffered.features[0];
    for(let i=1;i<buffered.features.length;i++){ try{ const u=turf.union(corridor,buffered.features[i]); if(u) corridor=u; }catch(e){} }
    map.flyTo({center:[lon,lat],zoom:13});
    setAOIFromGeometry(corridor.geometry, `Corredor de carretera · ${searchKm} km`);
    speak(`Tracé el corredor de la carretera, dentro de ${searchKm} kilómetro${searchKm==1?'':'s'}. Analizando los cerros junto a la vía.`);
  }catch(err){ toast('Could not query the road; using the area around you.',4500); analizarALaRedonda(lon,lat,searchKm); }
}

function usarMiUbicacion(km){
  km = km || +document.getElementById('radiusKm').value || 1;
  if(!navigator.geolocation){ toast('Your device does not support GPS.'); return; }
  state.autoAnalizar=true;   // GPS/voz → tras dibujar el corredor, analiza solo
  toast('📍 Getting your location…',2500);
  navigator.geolocation.getCurrentPosition(
    pos=>{ guardarUbicacion(pos.coords.latitude, pos.coords.longitude);
           analizarCorredor(pos.coords.longitude, pos.coords.latitude, km); },
    err=>{ toast('Could not get your location (permission denied or no signal).',4000); },
    {enableHighAccuracy:true, timeout:10000, maximumAge:0}
  );
}
document.getElementById('gpsBtn').onclick=()=>usarMiUbicacion();

// ---------- Ubicación del usuario (GPS + nombre del lugar) para el agente ----------
async function geocodeInverso(lat,lon){
  try{
    const r=await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&zoom=12&accept-language=es&lat=${lat}&lon=${lon}`);
    const d=await r.json(); const a=d.address||{};
    return a.city||a.town||a.village||a.county||a.state||d.display_name||null;
  }catch(e){ return null; }
}
async function guardarUbicacion(lat,lon){
  const lugar=await geocodeInverso(lat,lon);
  state.ubicacion={lat:+(+lat).toFixed(5), lon:+(+lon).toFixed(5), lugar};
  return state.ubicacion;
}
function capturarUbicacion(){
  return new Promise(res=>{
    if(!navigator.geolocation){ res(null); return; }
    navigator.geolocation.getCurrentPosition(
      async pos=>{ res(await guardarUbicacion(pos.coords.latitude,pos.coords.longitude)); },
      ()=>res(null), {enableHighAccuracy:true,timeout:8000,maximumAge:60000});
  });
}

// ---------- Agente Qaway: toggles idioma / nivel ----------
document.querySelectorAll('.qseg').forEach(seg=>{
  const key=seg.dataset.k;
  seg.querySelectorAll('button').forEach(b=>b.onclick=()=>{
    seg.querySelectorAll('button').forEach(x=>x.classList.remove('on'));
    b.classList.add('on'); state[key]=b.dataset.v;
  });
});
function voiceLang(){ return state.idioma==='en'?'en-US':'es-PE'; }

// ---------- Agente Qaway: voz (reconocimiento + síntesis) ----------
function speak(text,lang){
  try{ if(!window.speechSynthesis||!text) return;
    // limpiar markdown para que la voz no lea "asterisco", "numeral", etc.
    const limpio=text.replace(/[*_#`>]+/g,'').replace(/^\s*[-•]\s*/gm,' ').replace(/\s{2,}/g,' ').trim();
    const u=new SpeechSynthesisUtterance(limpio); u.lang=lang||voiceLang(); u.rate=1;
    speechSynthesis.cancel(); speechSynthesis.speak(u);
  }catch(e){}
}
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
function startVoice(){
  if(!SR){ toast('Your browser does not support voice recognition. Use Chrome on Android, or type your question.',5000); return; }
  const rec=new SR(); rec.lang=voiceLang(); rec.interimResults=false; rec.maxAlternatives=1;
  const mic=document.getElementById('micBtn');
  mic.classList.add('listening'); mic.textContent='Listening…';
  rec.onresult=e=>{ const txt=e.results[0][0].transcript.toLowerCase();
    toast('I heard: “'+txt+'”',3500); interpretarComando(txt); };
  rec.onerror=()=>{ toast('I did not catch that, try again.',3000); };
  rec.onend=()=>{ mic.classList.remove('listening'); mic.textContent='Ask by voice'; };
  rec.start();
}
// 100% AGENTIC: todo va al LLM; él decide si responder o analizar (sin plantillas).
function interpretarComando(txt){ preguntarAgente(txt); }
// 🧠 Pregunta al agente LLM (backend → Ollama) y responde por voz + texto
async function preguntarAgente(pregunta){
  const mic=document.getElementById('micBtn');
  // Capturamos la ubicación UNA vez (best-effort) y queda disponible para CUALQUIER
  // pregunta → el LLM decide si la usa; no dependemos de frases fijas.
  if(!state.ubicacion){ await capturarUbicacion(); }
  toast('🧠 Qaway is thinking…',2500); mic.textContent='Thinking…';
  const contexto={};
  if(state.aoi){ contexto.zona=state.aoi.name; contexto.bbox=state.aoi.bbox; }
  if(state.ubicacion) contexto.ubicacion=state.ubicacion;
  try{
    const res=await fetch(CFG.API_BASE+'/preguntar',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({pregunta, idioma:state.idioma, nivel:state.nivel, contexto})});
    if(!res.ok) throw new Error('HTTP '+res.status);
    const data=await res.json();
    const r=data.respuesta||'';
    speak(r);
    toast('Qaway answered ✔',2500);
    // Si el LLM decidió ANALIZAR la zona → el frontend ejecuta la acción
    if(data.accion && data.accion.tipo==='analizar'){
      const km=data.accion.km||1;
      document.getElementById('radiusKm').value=km;
      setTimeout(()=>usarMiUbicacion(km), 400);
    }
  }catch(err){ toast('Could not reach the Qaway agent (is the backend up?).',4500); }
  finally{ mic.textContent='Ask by voice'; }
}
document.getElementById('micBtn').onclick=startVoice;
document.getElementById('askBtn').onclick=()=>{ const t=document.getElementById('askText').value.trim(); if(t) preguntarAgente(t); };
document.getElementById('askText').addEventListener('keydown',e=>{ if(e.key==='Enter'){ const t=e.target.value.trim(); if(t) preguntarAgente(t); }});

// ---------- init ----------
resetReadout();
})();
