/* Qaway — mascota: alpaca andina 3D (modelo Quaternius, CC0) que CAMINA por la
   franja inferior, de ida y vuelta. Al hablar Qaway, se detiene y mira al frente.
   Lleva una manta peruana (roja con franja blanca) en el lomo 🇵🇪.
   Expuesto como window.LlamaAvatar. */
(function(){
  if(!window.THREE || !THREE.GLTFLoader){ console.warn('Three.js/GLTFLoader no cargó; sin avatar.'); return; }
  const host=document.getElementById('llama-avatar');
  if(!host) return;

  let renderer;
  try{ renderer=new THREE.WebGLRenderer({alpha:true, antialias:true}); }
  catch(e){ host.style.display='none'; return; }

  function size(){ return [host.clientWidth||600, host.clientHeight||120]; }
  let [W,H]=size();
  renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
  renderer.setSize(W,H);
  if(renderer.outputEncoding!==undefined) renderer.outputEncoding=THREE.sRGBEncoding;
  host.appendChild(renderer.domElement);

  const scene=new THREE.Scene();
  const camera=new THREE.PerspectiveCamera(24, W/H, 0.1, 100);
  camera.position.set(0,0.9,7); camera.lookAt(0,0.45,0);

  scene.add(new THREE.AmbientLight(0xffffff,0.9));
  const key=new THREE.DirectionalLight(0xffffff,0.95); key.position.set(2,5,3); scene.add(key);
  const rim=new THREE.DirectionalLight(0xbfd4ff,0.4); rim.position.set(-3,2,-3); scene.add(rim);

  // ancho visible (unidades) en el plano z=0 → hasta dónde camina
  function rangoX(){ return 7*Math.tan((24*Math.PI/180)/2)*(W/H) - 0.6; }
  let X=rangoX();

  const walker=new THREE.Group(); scene.add(walker);   // se mueve en X
  let model=null, mixer=null, aWalk=null, aIdle=null, ready=false;
  let talking=false, dir=1, x=0, wWalk=1;

  window.LlamaAvatar={ setTalking:b=>{ talking=!!b; } };

  new THREE.GLTFLoader().load('assets/alpaca.glb', (gltf)=>{
    model=gltf.scene;
    const box=new THREE.Box3().setFromObject(model);
    const sz=box.getSize(new THREE.Vector3());
    const ctr=box.getCenter(new THREE.Vector3());
    const s=1.7/sz.y; model.scale.setScalar(s);
    model.position.set(-ctr.x*s, -box.min.y*s, -ctr.z*s);   // patas en y=0, centrado
    walker.add(model);

    // 🇵🇪 manta peruana en el lomo (coords locales del modelo)
    const red=new THREE.MeshStandardMaterial({color:0xd91023, roughness:0.55});
    const white=new THREE.MeshStandardMaterial({color:0xffffff, roughness:0.6});
    const base=new THREE.Mesh(new THREE.BoxGeometry(sz.x*0.9, sz.y*0.05, sz.z*0.42), red);
    const stripe=new THREE.Mesh(new THREE.BoxGeometry(sz.x*0.92, sz.y*0.055, sz.z*0.10), white);
    const manta=new THREE.Group(); manta.add(base); manta.add(stripe);
    manta.position.set(ctr.x, ctr.y+sz.y*0.06, ctr.z); model.add(manta);

    // animaciones
    mixer=new THREE.AnimationMixer(model);
    const clip=n=>THREE.AnimationClip.findByName(gltf.animations,n)
               || gltf.animations.find(c=>c.name.endsWith(n));
    aWalk=mixer.clipAction(clip('Walk')); aIdle=mixer.clipAction(clip('Idle'));
    if(aWalk){ aWalk.play(); } if(aIdle){ aIdle.play(); aIdle.weight=0; }
    ready=true;
  }, undefined, (err)=>{ console.warn('No se pudo cargar la alpaca 3D', err); host.style.display='none'; });

  let last=performance.now();
  function frame(now){
    const dt=Math.min(0.05,(now-last)/1000); last=now;
    if(ready){
      mixer.update(dt);
      // la llama SIEMPRE camina de ida y vuelta
      if(aWalk) aWalk.weight=1;
      if(aIdle) aIdle.weight=0;
      x += dir*1.7*dt;
      if(x> X){ x= X; dir=-1; } if(x< -X){ x=-X; dir=1; }
      walker.position.x = x;
      model.rotation.y = dir>0 ? Math.PI/2 : -Math.PI/2;   // mira hacia donde camina
    }
    renderer.render(scene,camera);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  window.addEventListener('resize', ()=>{ [W,H]=size(); renderer.setSize(W,H);
    camera.aspect=W/H; camera.updateProjectionMatrix(); X=rangoX(); });
})();
