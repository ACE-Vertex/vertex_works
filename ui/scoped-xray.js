/* VERTEX WORKS 0.5.0 — SCOPED X-RAY / VERA HANDOFF
   Additive UI layer. Existing FORGE and Project X-Ray remain untouched. */
(() => {
  "use strict";

  const invoke = window.__TAURI__?.core?.invoke;
  const state = { scope: null, last: null, busy: false };

  const escapeHtml = s => String(s ?? "")
    .replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;")
    .replaceAll('"',"&quot;");

  function createUi(){
    if(document.getElementById("vxScopedXrayMenu")) return;

    const menu=document.createElement("div");
    menu.id="vxScopedXrayMenu";
    menu.className="vx-sx-menu";
    menu.innerHTML=`
      <div class="vx-sx-menu-head">
        <span>VERTEX RAY</span><b>SCOPED X-RAY</b>
        <small id="vxSxMenuScope">Resolve folder…</small>
      </div>
      <button data-vx-sx="standard"><span>⌖</span><div><b>X-RAY THIS FOLDER</b><small>Fast structural + source analysis</small></div></button>
      <button data-vx-sx="deep"><span>◉</span><div><b>DEEP X-RAY</b><small>Deeper source anchors / recent state</small></div></button>
      <button data-vx-sx="clip"><span>↗</span><div><b>X-RAY & CLIP TO VERA</b><small>Deep analysis → handoff capsule</small></div></button>
      <button data-vx-sx="last"><span>▱</span><div><b>OPEN LAST REPORT</b><small>Current session</small></div></button>`;
    document.body.appendChild(menu);

    const overlay=document.createElement("section");
    overlay.id="vxScopedXrayOverlay";
    overlay.className="vx-sx-overlay";
    overlay.innerHTML=`
      <div class="vx-sx-card">
        <header>
          <div><small>VERTEX WORKS / VERTEX RAY</small><h2>SCOPED X-RAY · VERA HANDOFF</h2></div>
          <div class="vx-sx-actions">
            <button id="vxSxCopyReport">COPY REPORT</button>
            <button id="vxSxClipVera" class="primary">↗ CLIP TO VERA</button>
            <button id="vxSxClose">×</button>
          </div>
        </header>
        <div class="vx-sx-meta" id="vxSxMeta">No scoped observation yet.</div>
        <pre id="vxSxReport">Right-click a folder in VERTEX PROJECT EXPLORER.</pre>
      </div>`;
    document.body.appendChild(overlay);

    menu.addEventListener("click", async e=>{
      const b=e.target.closest("[data-vx-sx]");
      if(!b)return;
      const action=b.dataset.vxSx;
      hideMenu();
      if(action==="last"){ showLast(); return; }
      if(!state.scope){ return; }
      await runScope(action==="standard"?"STANDARD":"DEEP", action==="clip");
    });
    document.getElementById("vxSxClose").onclick=()=>overlay.classList.remove("open");
    document.getElementById("vxSxCopyReport").onclick=()=>copyText(state.last?.report || "");
    document.getElementById("vxSxClipVera").onclick=()=>copyText(state.last?.vera_handoff || "");
  }

  function textOf(el){
    try{return (el?.innerText || el?.textContent || "").trim()}catch{return ""}
  }

  function attrSignal(el){
    if(!el || el.nodeType!==1)return "";
    const attrs=[];
    try{
      attrs.push(el.id||"", el.className||"", el.getAttribute("role")||"");
      for(const a of Array.from(el.attributes||[])){
        attrs.push(a.name||"", a.value||"");
      }
      attrs.push(...Object.keys(el.dataset||{}));
    }catch{}
    return attrs.join(" ").toLowerCase();
  }

  function findExplorerRoot(){
    // Strong selectors first.
    const selectors=[
      '[id*="explorer" i]',
      '[class*="explorer" i]',
      '[data-panel*="explorer" i]',
      '[data-view*="explorer" i]',
      '[aria-label*="explorer" i]',
      '[id*="project-tree" i]',
      '[class*="project-tree" i]'
    ];
    for(const sel of selectors){
      const nodes=[...document.querySelectorAll(sel)];
      const usable=nodes.find(el=>{
        const r=el.getBoundingClientRect();
        return r.width>120 && r.height>120;
      });
      if(usable)return usable;
    }

    // Vertex Works currently presents a visible "VERTEX PROJECT EXPLORER"
    // heading. Locate the heading and expand to the nearest panel-shaped ancestor.
    const all=[...document.querySelectorAll("div,section,aside,nav,header,h1,h2,h3,h4,span,strong")];
    const heading=all.find(el=>{
      const t=textOf(el).replace(/\s+/g," ").toUpperCase();
      return t==="VERTEX PROJECT EXPLORER" || t==="PROJECT EXPLORER";
    });
    if(!heading)return null;

    let el=heading;
    let best=null;
    for(let i=0;el && i<8;i++,el=el.parentElement){
      const r=el.getBoundingClientRect();
      if(r.width>160 && r.height>180 && r.height<window.innerHeight*0.98){
        best=el;
        const sig=attrSignal(el);
        if(/panel|pane|sidebar|explorer|tree|project/.test(sig))return el;
      }
    }
    return best;
  }

  function explorerHit(target,x,y){
    // DOM ancestry signal.
    const path=(target?.composedPath?.() || []);
    const chain=path.length ? path : (()=>{const a=[];let n=target;while(n&&a.length<10){a.push(n);n=n.parentElement}return a})();
    for(const el of chain){
      const sig=attrSignal(el);
      if(/explorer|project[-_ ]?tree|folder[-_ ]?tree|treeview/.test(sig))return true;
    }

    // Geometry fallback: right-click occurred inside the visible Explorer panel.
    const root=findExplorerRoot();
    if(root){
      const r=root.getBoundingClientRect();
      if(x>=r.left && x<=r.right && y>=r.top && y<=r.bottom)return true;
      if(root.contains?.(target))return true;
    }

    // Last fallback for folder-like rows: common tree semantics / folder glyph.
    let el=target;
    for(let i=0;el && i<6;i++,el=el.parentElement){
      const role=(el.getAttribute?.("role")||"").toLowerCase();
      const t=textOf(el).slice(0,240);
      if(role==="treeitem" || /^[▸▾▶▼📁📂]/.test(t))return true;
    }
    return false;
  }

  // VERTEX_WORKS_RAY_PROJECT_ROOT_SCOPE_RESET_064
  // Ray does not care about the exact nested folder anymore.
  // Every Explorer row carries the top-level project root that owns it.
  // No text inference, no folder-name search, no selection heuristics.
  function projectRowAtPoint(target,x,y){
    const direct=target?.closest?.("[data-xray-project-root]");
    if(direct)return direct;

    // This is only a hit-test for an already-authoritative row binding.
    // It never guesses a path from text or DOM ancestry.
    try{
      for(const el of document.elementsFromPoint(x,y)||[]){
        const row=el?.closest?.("[data-xray-project-root]");
        if(row)return row;
      }
    }catch{}
    return null;
  }

  function resolveProjectRootScope(target,x,y){
    const row=projectRowAtPoint(target,x,y);
    if(!row){
      throw new Error(
        "No Project Root is bound to this Explorer row. " +
        "Vertex Ray stopped. Whole-Development fallback is forbidden."
      );
    }

    const scope=String(row.dataset.xrayProjectRoot||"").trim();
    if(!/^[A-Za-z]:\\/.test(scope)){
      throw new Error(`Invalid Project Root binding: ${scope||"(empty)"}`);
    }

    const normalized=scope.replaceAll("/","\\").replace(/[\\]+$/,"").toLowerCase();
    if(normalized==="g:\\vertex_project\\development"){
      throw new Error(
        "Development root is not a Scoped Ray target. Use global PROJECT X-RAY explicitly."
      );
    }
    return scope;
  }


  function showMenu(x,y,scope,error){
    const menu=document.getElementById("vxScopedXrayMenu");
    state.scope=scope||null;
    document.getElementById("vxSxMenuScope").textContent=error ? String(error) : scope;
    menu.classList.toggle("error",!!error);
    for(const b of menu.querySelectorAll("[data-vx-sx]")){
      if(b.dataset.vxSx!=="last")b.disabled=!scope;
    }
    const left=Math.min(x,window.innerWidth-340);
    const top=Math.min(y,window.innerHeight-285);
    menu.style.left=Math.max(8,left)+"px";
    menu.style.top=Math.max(8,top)+"px";
    menu.classList.add("open");
  }
  function hideMenu(){document.getElementById("vxScopedXrayMenu")?.classList.remove("open")}

  async function runScope(mode,clip){
    if(!invoke || state.busy || !state.scope)return;
    state.busy=true;
    const overlay=document.getElementById("vxScopedXrayOverlay");
    const report=document.getElementById("vxSxReport");
    const meta=document.getElementById("vxSxMeta");
    overlay.classList.add("open");
    report.textContent=`SCANNING ${state.scope}\nMODE ${mode}\nREAD ONLY…`;
    meta.textContent="VERTEX RAY active · no project mutation";
    try{
      const result=await invoke("xray_scope",{path:state.scope,mode});
      state.last=result;
      report.textContent=result.report;
      meta.innerHTML=`<b>${escapeHtml(result.scope)}</b><span>${escapeHtml(result.kind)} · ${escapeHtml(result.version||"UNKNOWN")} · ${result.files} files · ${result.directories_scanned} dirs · ${escapeHtml(result.fingerprint.slice(0,16))}…</span>`;
      if(clip)await copyText(result.vera_handoff);
    }catch(err){
      report.textContent=`SCOPED X-RAY ERROR\n${err}`;
      meta.textContent="ERROR · source untouched";
    }finally{
      state.busy=false;
    }
  }

  async function copyText(text){
    if(!text)return;
    try{
      await navigator.clipboard.writeText(text);
      const meta=document.getElementById("vxSxMeta");
      const old=meta.innerHTML;
      meta.innerHTML=`<strong class="vx-sx-copied">CLIPPED TO VERA · READY TO PASTE</strong>`;
      setTimeout(()=>{ if(meta)meta.innerHTML=old },1500);
    }catch(err){
      document.getElementById("vxSxReport").textContent += `\n\nCLIP ERROR: ${err}`;
    }
  }

  function showLast(){
    const overlay=document.getElementById("vxScopedXrayOverlay");
    overlay.classList.add("open");
    if(state.last){
      document.getElementById("vxSxReport").textContent=state.last.report;
      document.getElementById("vxSxMeta").textContent=`${state.last.scope} · ${state.last.mode}`;
    }
  }

  createUi();

  let vxContextBusy=false;
  async function onExplorerContextMenu(e){
    if(vxContextBusy)return;
    if(!explorerHit(e.target,e.clientX,e.clientY))return;

    // Intercept before any existing pane handler can consume the native context menu.
    e.preventDefault();
    e.stopPropagation();
    if(typeof e.stopImmediatePropagation==="function")e.stopImmediatePropagation();

    const clickX=e.clientX;
    const clickY=e.clientY;
    const clickTarget=e.target;

    vxContextBusy=true;
    showMenu(clickX,clickY,null,"Resolving Project Root…");
    try{
      const scope=resolveProjectRootScope(clickTarget,clickX,clickY);
      showMenu(clickX,clickY,scope,null);
    }catch(err){
      // The menu still opens so the failure is visible instead of appearing
      // as "right click did nothing".
      showMenu(e.clientX,e.clientY,null,err);
    }finally{
      vxContextBusy=false;
    }
  }

  // Window capture runs before document/pane handlers.
  window.addEventListener("contextmenu",onExplorerContextMenu,true);

  // Some embedded tree widgets swallow contextmenu but still expose right-button
  // pointerup. Keep this as a non-duplicating fallback.
  window.addEventListener("pointerup",e=>{
    if(e.button!==2)return;
    if(document.getElementById("vxScopedXrayMenu")?.classList.contains("open"))return;
    if(!explorerHit(e.target,e.clientX,e.clientY))return;
    onExplorerContextMenu(e);
  },true);

  document.addEventListener("pointerdown",e=>{
    if(!e.target.closest("#vxScopedXrayMenu"))hideMenu();
  },true);
  document.addEventListener("keydown",e=>{
    if(e.key==="Escape"){
      hideMenu();
      document.getElementById("vxScopedXrayOverlay")?.classList.remove("open");
    }
  });
})();
