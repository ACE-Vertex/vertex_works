(() => {
"use strict";
const VERSION="000089", MAX_VIEW=1048576, HASH_LIMIT=67108864, DIFF_CHUNK=1048576;
const $=(s,r=document)=>r.querySelector(s);
const S={a:null,b:null,active:"a",mode:"HEX",offset:0,length:4096,diff:null,hashA:null,hashB:null};
const G={
  policy:"INTEGRATED_PREFERRED",
  requestedPowerPreference:"low-power",
  highPerformanceRequested:false,
  backend:"PENDING",
  status:"NOT_INITIALIZED",
  adapterName:"UNRESOLVED",
  adapterVendor:"UNRESOLVED",
  adapterArchitecture:"UNRESOLVED",
  adapterDevice:"UNRESOLVED",
  adapterClass:"UNRESOLVED",
  device:null,
  adapter:null,
  context:null,
  format:null,
  pipeline:null
};
const fmt=n=>{if(!Number.isFinite(n))return"N/A";const u=["B","KiB","MiB","GiB"],q=[n,0];while(q[0]>=1024&&q[1]<u.length-1){q[0]/=1024;q[1]++;}return`${q[0].toFixed(q[1]?2:0)} ${u[q[1]]}`};
const hx=n=>n.toString(16).padStart(2,"0").toUpperCase();
const esc=s=>String(s??"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");
const active=()=>S[S.active];
async function read(file,start=0,len=MAX_VIEW){return new Uint8Array(await file.slice(start,Math.min(file.size,start+len)).arrayBuffer())}
async function sha(file){if(file.size>HASH_LIMIT)return"SKIPPED >64MiB";const d=await crypto.subtle.digest("SHA-256",await file.arrayBuffer());return[...new Uint8Array(d)].map(hx).join("").toLowerCase()}
function rawMetrics(b){let p=0,z=0,c=new Uint32Array(256);for(const x of b){c[x]++;if((x>=32&&x<=126)||x===9||x===10||x===13)p++;if(x===0)z++;}let e=0;for(const n of c){if(n){const q=n/b.length;e-=q*Math.log2(q)}}const magic=[...b.slice(0,16)].map(x=>x>=32&&x<=126?String.fromCharCode(x):".").join("");return{magic,header:[...b.slice(0,32)].map(hx).join(" "),printable:b.length?p/b.length:0,zero:b.length?z/b.length:0,entropy:e,vxnHint:magic.toUpperCase().includes("VXN")}}
function hexView(b,base){const o=[];for(let i=0;i<b.length;i+=16){const r=b.slice(i,i+16),a=(base+i).toString(16).padStart(8,"0").toUpperCase(),h=[...r].map(hx).join(" ").padEnd(47," "),t=[...r].map(x=>x>=32&&x<=126?String.fromCharCode(x):".").join("");o.push(`${a}  ${h}  |${t}|`)}return o.join("\n")}
function strView(b){const o=[];let s="",st=0;for(let i=0;i<b.length;i++){const x=b[i];if(x>=32&&x<=126){if(!s)st=i;s+=String.fromCharCode(x)}else{if(s.length>=4)o.push(`${st.toString(16).padStart(8,"0").toUpperCase()}  ${s}`);s=""}if(o.length>=1200)break}return o.join("\n")}
function set(id,v){const e=document.getElementById(id);if(e)e.textContent=String(v)}
async function inspect(slot,file){S[slot]=file;if(slot==="a")S.active="a";const b=await read(file,0,Math.min(file.size,MAX_VIEW));S[slot+"Metrics"]=rawMetrics(b);set(`vwVxn${slot.toUpperCase()}Name`,file.name);set(`vwVxn${slot.toUpperCase()}Size`,fmt(file.size));set(`vwVxn${slot.toUpperCase()}Hash`,"CALCULATING");sha(file).then(h=>{S[slot==="a"?"hashA":"hashB"]=h;set(`vwVxn${slot.toUpperCase()}Hash`,h);renderInspector()});renderStructure();renderData();renderInspector();renderMap(b)}
function renderStructure(){const box=$("#vwVxnStructure"),f=active(),m=S[S.active+"Metrics"];if(!box)return;if(!f||!m){box.innerHTML='<div class="vw-vxn-empty">OPEN A .VXN FILE</div>';return}box.innerHTML=`<article><small>FILE</small><b>${esc(f.name)}</b></article><article><small>SIZE</small><b>${fmt(f.size)}</b></article><article><small>HEADER ASCII</small><code>${esc(m.magic)}</code></article><article><small>HEADER HEX</small><code>${m.header}</code></article><article><small>PRINTABLE</small><b>${(m.printable*100).toFixed(2)}%</b></article><article><small>ZERO</small><b>${(m.zero*100).toFixed(2)}%</b></article><article><small>ENTROPY</small><b>${m.entropy.toFixed(3)} bit/B</b></article><article><small>VXN MAGIC HINT</small><b>${m.vxnHint?"FOUND":"UNRESOLVED"}</b></article><article class="warn"><small>SEMANTIC DECODER</small><b>UNRESOLVED</b><em>RAW TRUTH MODE</em></article>`}
function renderInspector(){const f=active(),h=S.active==="a"?S.hashA:S.hashB;set("vwVxnInspectorSlot",S.active.toUpperCase());set("vwVxnInspectorName",f?.name||"NONE");set("vwVxnInspectorSize",f?fmt(f.size):"N/A");set("vwVxnInspectorHash",h||"N/A");set("vwVxnInspectorMode",S.mode);set("vwVxnInspectorRange",f?`0x${S.offset.toString(16).toUpperCase()} + ${S.length} B`:"N/A");set("vwVxnDiffState",S.diff?.state||"NOT RUN");set("vwVxnDiffChanged",S.diff?.changed??"N/A");set("vwVxnDiffCompared",S.diff?fmt(S.diff.compared):"N/A")}
async function renderData(){const pre=$("#vwVxnData"),f=active();if(!pre)return;if(!f){pre.textContent="Open a VXN file to begin.";return}S.offset=Math.max(0,Number($("#vwVxnOffset")?.value||0));S.length=Math.min(MAX_VIEW,Math.max(16,Number($("#vwVxnLength")?.value||4096)));if(S.mode==="DIFF"){pre.textContent=diffText();renderInspector();return}const b=await read(f,S.offset,S.length);pre.textContent=S.mode==="HEX"?hexView(b,S.offset):S.mode==="UTF8"?new TextDecoder("utf-8",{fatal:false}).decode(b):strView(b);renderInspector()}
function diffText(){const d=S.diff;if(!d)return"Load A and B, then RUN DIFF.";const o=[`STATE: ${d.state}`,`A: ${d.aName} (${fmt(d.aSize)})`,`B: ${d.bName} (${fmt(d.bSize)})`,`COMPARED: ${fmt(d.compared)}`,`CHANGED BYTES: ${d.changed}`,"","FIRST DIFFERENCES:"];for(const x of d.first)o.push(`${x.offset.toString(16).padStart(8,"0").toUpperCase()}  A=${x.a===null?"--":hx(x.a)} B=${x.b===null?"--":hx(x.b)}`);return o.join("\n")}
async function runDiff(){const a=S.a,b=S.b;if(!a||!b){S.diff={state:"NEED A+B",changed:0,compared:0,first:[],aName:a?.name||"NONE",bName:b?.name||"NONE",aSize:a?.size||0,bSize:b?.size||0};return setMode("DIFF")}let changed=0,compared=0,first=[];for(let off=0,max=Math.max(a.size,b.size);off<max;off+=DIFF_CHUNK){const [aa,bb]=await Promise.all([read(a,off,DIFF_CHUNK),read(b,off,DIFF_CHUNK)]),n=Math.max(aa.length,bb.length);for(let i=0;i<n;i++){const av=i<aa.length?aa[i]:null,bv=i<bb.length?bb[i]:null;if(av!==bv){changed++;if(first.length<256)first.push({offset:off+i,a:av,b:bv})}}compared+=n;if(off%(8*DIFF_CHUNK)===0)await new Promise(requestAnimationFrame)}S.diff={state:changed===0&&a.size===b.size?"IDENTICAL":"DIFFERENT",changed,compared,first,aName:a.name,bName:b.name,aSize:a.size,bSize:b.size};setMode("DIFF")}
function gpuInfoText(){
  return [G.adapterVendor,G.adapterArchitecture,G.adapterDevice,G.adapterName]
    .filter(x=>x&&x!=="UNRESOLVED").join(" / ")||"UNRESOLVED";
}
function updateGpuUi(){
  set("vwVxnGpuPolicy",G.policy.replaceAll("_"," "));
  set("vwVxnGpuRequest",`WEBGPU ${G.requestedPowerPreference.toUpperCase()} / NO HIGH-PERF REQUEST`);
  set("vwVxnGpuBackend",G.backend);set("vwVxnGpuBackend2",G.backend);
  set("vwVxnGpuStatus",G.status);
  set("vwVxnGpuAdapter",gpuInfoText());
  set("vwVxnGpuClass",G.adapterClass);
}
async function initGpu(){
  if(G.status!=="NOT_INITIALIZED")return G.backend==="WEBGPU_LOW_POWER";
  G.status="PROBING";
  updateGpuUi();
  try{
    if(!navigator.gpu){
      G.backend="CANVAS2D_SOFTWARE";
      G.status="WEBGPU_UNAVAILABLE";
      updateGpuUi();
      return false;
    }
    const adapter=await navigator.gpu.requestAdapter({powerPreference:"low-power"});
    if(!adapter){
      G.backend="CANVAS2D_SOFTWARE";
      G.status="LOW_POWER_ADAPTER_UNAVAILABLE";
      updateGpuUi();
      return false;
    }
    G.adapter=adapter;
    let info={};
    try{
      if(adapter.info)info=adapter.info;
      else if(adapter.requestAdapterInfo)info=await adapter.requestAdapterInfo();
    }catch(_){}
    G.adapterName=String(info.description||"UNRESOLVED");
    G.adapterVendor=String(info.vendor||"UNRESOLVED");
    G.adapterArchitecture=String(info.architecture||"UNRESOLVED");
    G.adapterDevice=String(info.device||"UNRESOLVED");
    G.adapterClass="UNRESOLVED";
    G.device=await adapter.requestDevice();
    const canvas=$("#vwVxnByteMap");
    if(!canvas)throw new Error("BYTE_MAP_CANVAS_MISSING");
    const ctx=canvas.getContext("webgpu");
    if(!ctx)throw new Error("WEBGPU_CONTEXT_UNAVAILABLE");
    G.context=ctx;
    G.format=navigator.gpu.getPreferredCanvasFormat();
    ctx.configure({device:G.device,format:G.format,alphaMode:"opaque"});
    const shader=G.device.createShaderModule({code:`
struct Params { len:u32, step:u32, width:u32, height:u32 };
@group(0) @binding(0) var<storage, read> packed: array<u32>;
@group(0) @binding(1) var<uniform> params: Params;
@vertex fn vs(@builtin(vertex_index) vi:u32)->@builtin(position) vec4f {
  var p=array<vec2f,3>(vec2f(-1.0,-1.0),vec2f(3.0,-1.0),vec2f(-1.0,3.0));
  return vec4f(p[vi],0.0,1.0);
}
@fragment fn fs(@builtin(position) pos:vec4f)->@location(0) vec4f {
  let x=min(u32(pos.x),params.width-1u);
  let y=min(u32(pos.y),params.height-1u);
  let linear=y*params.width+x;
  let idx=min(linear*params.step,params.len-1u);
  let word=packed[idx/4u];
  let shift=(idx%4u)*8u;
  let v=f32((word>>shift)&255u)/255.0;
  return vec4f(1.0,0.541,0.165,0.06+v*0.84);
}`});
    G.pipeline=G.device.createRenderPipeline({
      layout:"auto",
      vertex:{module:shader,entryPoint:"vs"},
      fragment:{module:shader,entryPoint:"fs",targets:[{format:G.format}]},
      primitive:{topology:"triangle-list"}
    });
    G.backend="WEBGPU_LOW_POWER";
    G.status="LOW_POWER_REQUEST_ACTIVE";
    updateGpuUi();
    try{window.VertexWorksFactoryKernel?.recordEvidence?.("VXN_BROWSER_GPU_POLICY",{
      version:VERSION,
      policy:G.policy,
      requestedPowerPreference:G.requestedPowerPreference,
      highPerformanceRequested:G.highPerformanceRequested,
      backend:G.backend,
      adapterClass:G.adapterClass,
      adapterInfo:gpuInfoText()
    })}catch(_){}
    return true;
  }catch(err){
    G.backend="CANVAS2D_SOFTWARE";
    G.status=`WEBGPU_FALLBACK:${String(err?.message||err)}`;
    G.device=null;G.adapter=null;G.context=null;G.pipeline=null;
    updateGpuUi();
    return false;
  }
}
function renderMapCpu(b){
  const c=$("#vwVxnByteMap");if(!c)return;
  const x=c.getContext("2d");if(!x){G.status="CANVAS2D_UNAVAILABLE";updateGpuUi();return}
  const w=c.width,h=c.height;x.clearRect(0,0,w,h);if(!b?.length)return;
  const step=Math.max(1,Math.floor(b.length/(w*h)));let p=0;
  for(let y=0;y<h;y++)for(let i=0;i<w;i++){
    const v=b[Math.min(b.length-1,p*step)];
    x.fillStyle=`rgba(255,138,42,${.06+(v/255)*.84})`;x.fillRect(i,y,1,1);p++;
  }
}
async function renderMapGpu(b){
  if(!b?.length||!G.device||!G.context||!G.pipeline)return false;
  const c=$("#vwVxnByteMap"),w=c.width,h=c.height;
  const step=Math.max(1,Math.floor(b.length/(w*h)));
  const words=Math.max(1,Math.ceil(b.length/4));
  const packed=new Uint32Array(words);
  new Uint8Array(packed.buffer).set(b);
  const data=G.device.createBuffer({size:Math.max(4,packed.byteLength),usage:GPUBufferUsage.STORAGE|GPUBufferUsage.COPY_DST});
  G.device.queue.writeBuffer(data,0,packed);
  const params=new Uint32Array([b.length,step,w,h]);
  const uniform=G.device.createBuffer({size:16,usage:GPUBufferUsage.UNIFORM|GPUBufferUsage.COPY_DST});
  G.device.queue.writeBuffer(uniform,0,params);
  const bind=G.device.createBindGroup({layout:G.pipeline.getBindGroupLayout(0),entries:[
    {binding:0,resource:{buffer:data}},
    {binding:1,resource:{buffer:uniform}}
  ]});
  const encoder=G.device.createCommandEncoder();
  const pass=encoder.beginRenderPass({colorAttachments:[{
    view:G.context.getCurrentTexture().createView(),
    clearValue:{r:.012,g:.012,b:.012,a:1},
    loadOp:"clear",storeOp:"store"
  }]});
  pass.setPipeline(G.pipeline);pass.setBindGroup(0,bind);pass.draw(3);pass.end();
  G.device.queue.submit([encoder.finish()]);
  return true;
}
async function renderMap(b){
  if(await initGpu()){
    try{if(await renderMapGpu(b))return}catch(err){
      G.backend="CANVAS2D_SOFTWARE";
      G.status=`GPU_RENDER_FALLBACK:${String(err?.message||err)}`;
      updateGpuUi();
    }
  }
  renderMapCpu(b);
}
function setMode(m){S.mode=m;document.querySelectorAll("#vwVxnModes [data-mode]").forEach(b=>b.classList.toggle("active",b.dataset.mode===m));renderData()}
async function clip(){const f=active(),m=S[S.active+"Metrics"],bundle={schema:"vertex-works/vxn-browser-evidence/1",browserVersion:VERSION,timestamp:new Date().toISOString(),activeSlot:S.active.toUpperCase(),file:f?{name:f.name,size:f.size,sha256:S.active==="a"?S.hashA:S.hashB}:null,rawMetrics:m||null,range:{offset:S.offset,length:S.length},mode:S.mode,diff:S.diff,semanticDecoder:"UNRESOLVED",truthMode:"RAW",gpuPolicy:{
policy:G.policy,
requestedPowerPreference:G.requestedPowerPreference,
highPerformanceRequested:G.highPerformanceRequested,
backend:G.backend,
status:G.status,
adapterClass:G.adapterClass,
adapterInfo:gpuInfoText()
}};const t=JSON.stringify(bundle,null,2);try{await navigator.clipboard.writeText(t)}catch(_){const q=document.createElement("textarea");q.value=t;document.body.appendChild(q);q.select();document.execCommand("copy");q.remove()}try{window.VertexWorksFactoryKernel?.recordEvidence?.("VXN_BROWSER_CLIP",bundle)}catch(_){}}
function build(){const factory=$("#vwFactoryWorkspace"),nav=$("#vwFactoryNav");if(!factory||!nav)return false;if($("#vwVxnWorkspace"))return true;if(!nav.querySelector('[data-facility="VXN"]')){const btn=document.createElement("button");btn.type="button";btn.dataset.facility="VXN";btn.innerHTML='<span class="mode-index">03</span><b>VXN</b><em>BROWSE</em>';const judge=nav.querySelector('[data-facility="JUDGE"]');judge?nav.insertBefore(btn,judge):nav.appendChild(btn)}
const s=document.createElement("section");s.id="vwVxnWorkspace";s.className="vw-factory-facility vw-vxn-facility";s.dataset.facility="VXN";s.innerHTML=`<header class="vw-vxn-head"><div><small>VERTEX WORKS / VXN OBSERVATION FACILITY</small><h1>VXN BROWSER</h1><p>Raw truth first. Semantic decode only from a real VXN adapter.</p></div><div class="vw-vxn-actions"><label><input id="vwVxnOpenA" type="file" accept=".vxn,application/octet-stream"><span>OPEN A</span></label><label><input id="vwVxnOpenB" type="file" accept=".vxn,application/octet-stream"><span>OPEN B</span></label><button id="vwVxnDiffBtn">RUN DIFF</button><button id="vwVxnClipBtn">CLIP TO VERA</button></div></header><section class="vw-vxn-status"><div><small>A</small><b id="vwVxnAName">NONE</b><span id="vwVxnASize">N/A</span><code id="vwVxnAHash">N/A</code></div><div><small>B</small><b id="vwVxnBName">NONE</b><span id="vwVxnBSize">N/A</span><code id="vwVxnBHash">N/A</code></div><div><small>DECODER</small><b>RAW TRUTH</b><span>SEMANTIC: UNRESOLVED</span></div><div class="gpu"><small>GPU POLICY</small><b id="vwVxnGpuPolicy">INTEGRATED PREFERRED</b><span id="vwVxnGpuRequest">WEBGPU LOW-POWER / NO HIGH-PERF REQUEST</span><code id="vwVxnGpuBackend">PENDING</code></div></section><div class="vw-vxn-grid"><aside class="vw-vxn-pane structure"><header><small>STRUCTURE</small><b>RAW METRICS</b></header><div id="vwVxnSlots" class="vw-vxn-tabs"><button data-slot="a" class="active">A</button><button data-slot="b">B</button></div><div id="vwVxnStructure" class="vw-vxn-structure"><div class="vw-vxn-empty">OPEN A .VXN FILE</div></div><section class="vw-vxn-mapbox"><header><small>BYTE MAP</small><b>FIRST 1 MiB</b></header><canvas id="vwVxnByteMap" width="320" height="96"></canvas></section></aside><main class="vw-vxn-pane data"><header class="vw-vxn-data-head"><div id="vwVxnModes" class="vw-vxn-tabs"><button data-mode="HEX" class="active">HEX</button><button data-mode="UTF8">UTF-8</button><button data-mode="STRINGS">STRINGS</button><button data-mode="DIFF">DIFF</button></div><div class="vw-vxn-range"><label>OFFSET <input id="vwVxnOffset" type="number" min="0" value="0"></label><label>LENGTH <input id="vwVxnLength" type="number" min="16" max="1048576" value="4096"></label><button id="vwVxnReadBtn">READ</button></div></header><pre id="vwVxnData" class="vw-vxn-data">Open a VXN file to begin.</pre></main><aside class="vw-vxn-pane inspector"><header><small>INSPECTOR</small><b>ACTIVE RANGE</b></header><dl><dt>SLOT</dt><dd id="vwVxnInspectorSlot">A</dd><dt>FILE</dt><dd id="vwVxnInspectorName">NONE</dd><dt>SIZE</dt><dd id="vwVxnInspectorSize">N/A</dd><dt>SHA-256</dt><dd id="vwVxnInspectorHash">N/A</dd><dt>MODE</dt><dd id="vwVxnInspectorMode">HEX</dd><dt>RANGE</dt><dd id="vwVxnInspectorRange">N/A</dd></dl><section class="vw-vxn-diff"><small>DIFF ENGINE</small><b id="vwVxnDiffState">NOT RUN</b><div><span>CHANGED</span><b id="vwVxnDiffChanged">N/A</b></div><div><span>COMPARED</span><b id="vwVxnDiffCompared">N/A</b></div></section><section class="vw-vxn-gpu"><small>GPU AFFINITY SENSOR</small><b id="vwVxnGpuStatus">NOT INITIALIZED</b><dl><dt>BACKEND</dt><dd id="vwVxnGpuBackend2">PENDING</dd><dt>ADAPTER</dt><dd id="vwVxnGpuAdapter">UNRESOLVED</dd><dt>CLASS</dt><dd id="vwVxnGpuClass">UNRESOLVED</dd></dl><p>Low-power adapter is requested. Actual iGPU selection is runtime evidence, not assumed.</p></section><section class="vw-vxn-adapter"><small>VXN SCHEMA ADAPTER</small><b>UNRESOLVED</b><p>No semantic structure is invented.</p></section></aside></div>`;factory.appendChild(s);
$("#vwVxnOpenA").addEventListener("change",e=>{const f=e.target.files?.[0];if(f)inspect("a",f)});$("#vwVxnOpenB").addEventListener("change",e=>{const f=e.target.files?.[0];if(f)inspect("b",f)});$("#vwVxnDiffBtn").addEventListener("click",runDiff);$("#vwVxnClipBtn").addEventListener("click",clip);$("#vwVxnReadBtn").addEventListener("click",renderData);$("#vwVxnModes").addEventListener("click",e=>{const b=e.target.closest("[data-mode]");if(b)setMode(b.dataset.mode)});$("#vwVxnSlots").addEventListener("click",e=>{const b=e.target.closest("[data-slot]");if(!b)return;S.active=b.dataset.slot;document.querySelectorAll("#vwVxnSlots [data-slot]").forEach(x=>x.classList.toggle("active",x===b));renderStructure();renderInspector();renderData();const f=active();if(f)read(f,0,MAX_VIEW).then(renderMap)});updateGpuUi();initGpu();try{window.VertexWorksFactoryKernel?.recordEvidence?.("VXN_BROWSER_BOOT",{version:VERSION,facility:"VXN",semanticDecoder:"UNRESOLVED",rawTruth:true,gpuPolicy:G.policy,requestedPowerPreference:G.requestedPowerPreference,highPerformanceRequested:G.highPerformanceRequested})}catch(_){}return true}
function boot(n=0){if(build())return;if(n<40)setTimeout(()=>boot(n+1),100)}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",()=>boot(),{once:true});else boot();
window.VertexWorksVxnBrowser=Object.freeze({version:VERSION,state:()=>({...S}),gpu:()=>({...G,device:!!G.device,adapter:!!G.adapter,context:!!G.context,pipeline:!!G.pipeline}),setMode,runDiff,clip});
})();