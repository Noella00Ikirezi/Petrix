import { useEffect } from 'react';
import { Link } from 'react-router-dom';

/* ── CSS landing page ───────────────────────────────────────────────────── */
const CSS = `
.hp-page{overflow-x:hidden;width:100%}
.hp-wrap{max-width:1280px;margin:0 auto;padding:0 clamp(16px,3vw,40px);box-sizing:border-box}
canvas.w3d{display:block;width:100%;height:100%}

/* Nav */
.hp-nav{position:sticky;top:0;z-index:50;background:var(--panel);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
.hp-nav .hp-wrap{display:flex;align-items:center;justify-content:space-between;height:56px;gap:16px}
.hp-logo{font-family:var(--font-display);font-size:14px;letter-spacing:.1em;color:var(--text);flex-shrink:0}
.hp-logo .l{color:var(--lime)}
.nav-cta{font-size:11px;letter-spacing:.2em;color:var(--text);transition:color .15s;flex-shrink:0;white-space:nowrap;text-transform:uppercase}
.nav-cta:hover{color:var(--lime)}

/* Hero */
.hero{padding:clamp(56px,9vw,96px) 0 48px;position:relative}
.hero .built{font-size:10px;letter-spacing:.2em;color:var(--dim);text-transform:uppercase;border:1px solid var(--line);padding:7px 14px;display:inline-block;margin-bottom:20px}
.hero .built::before{content:'● ';color:var(--lime)}
.hero h1{font-family:var(--font-display);font-size:clamp(36px,7vw,100px);margin:12px 0 20px;color:var(--text);line-height:1.05;font-weight:400}
.hero h1 .l{color:var(--lime)}
.hero>div>p.sub{max-width:520px;color:var(--dim);font-size:clamp(13px,1.2vw,14px);line-height:1.7}
.hero-bar{margin-top:40px;display:grid;grid-template-columns:1fr 1fr 1fr auto;border:1px solid var(--line);align-items:center}
.hero-bar .cell{padding:clamp(12px,2vw,18px) clamp(14px,2vw,24px);font-size:11px;border-right:1px solid var(--line);min-width:0;overflow:hidden}
.hero-bar .cell .k{color:var(--faint);letter-spacing:.15em;text-transform:uppercase;font-size:10px;display:block;margin-bottom:4px}
.hero-bar .cell .v{color:var(--lime);font-size:11px;word-break:break-word}
.hero-bar .cta-cell{display:flex;justify-content:flex-end;padding:8px;flex-shrink:0}

/* Section header */
.sec-head{display:grid;grid-template-columns:minmax(160px,260px) 1fr auto;border:1px solid var(--line);border-bottom:none}
.sec-head>div{padding:14px 18px;font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--dim);min-width:0;overflow:hidden}
.sec-head>div+div{border-left:1px solid var(--line)}
.sec-head .n::before{content:'// '}

/* Modules */
.modules-grid{display:grid;grid-template-columns:repeat(3,1fr);border:1px solid var(--line)}
.mod{border-right:1px solid var(--line);position:relative;cursor:pointer;min-width:0}
.mod:last-child{border-right:none}
.mod .viz{height:clamp(200px,26vw,320px);opacity:.14;transition:opacity .4s ease}
.mod:hover .viz,.mod.active .viz{opacity:1}
.mod .meta{border-top:1px solid var(--line);padding:14px 18px 10px;transition:background .3s}
.mod:hover .meta,.mod.active .meta{background:var(--panel-hi)}
.mod .idx{font-size:10px;letter-spacing:.2em;color:var(--faint);text-transform:uppercase}
.mod:hover .idx,.mod.active .idx{color:var(--lime)}
.mod h3{font-family:var(--font-display);font-weight:400;font-size:clamp(12px,1.2vw,14px);letter-spacing:.05em;margin-top:6px;text-transform:uppercase;color:var(--text)}
.mod:hover h3,.mod.active h3{color:var(--lime)}
.mod .foot{display:flex;justify-content:space-between;flex-wrap:wrap;gap:4px;border-top:1px solid var(--line);padding:8px 18px;font-size:10px;letter-spacing:.15em;color:var(--faint);text-transform:uppercase}

/* Stat strip */
.stat-strip{border:1px solid var(--line);border-top:none;display:grid;grid-template-columns:repeat(4,1fr) auto}
.stat-strip .sc{padding:clamp(14px,2vw,22px) clamp(16px,2vw,28px);border-right:1px solid var(--line);text-align:center}
.stat-strip .sc .v{font-family:var(--font-display);font-size:clamp(18px,2.2vw,26px);color:var(--lime)}
.stat-strip .sc .k{font-size:9px;letter-spacing:.2em;color:var(--faint);text-transform:uppercase;margin-top:4px}
.stat-strip .launch{background:var(--lime);color:var(--bg);display:flex;align-items:center;justify-content:center;font-size:clamp(10px,1.1vw,12px);letter-spacing:.2em;text-transform:uppercase;cursor:pointer;font-family:var(--font-mono);transition:filter .15s;padding:0 clamp(16px,3vw,40px);white-space:nowrap}
.stat-strip .launch:hover{filter:brightness(1.12)}

/* Footer */
footer.hp-footer{border-top:1px solid var(--line);margin-top:clamp(32px,5vw,64px)}
.foot-bottom{display:grid;grid-template-columns:1fr auto auto;align-items:stretch;border-bottom:1px solid var(--line)}
.foot-bottom .fc{padding:16px clamp(16px,2vw,24px);font-size:10px;letter-spacing:.15em;color:var(--faint);text-transform:uppercase}
.foot-bottom .fc::before{content:'// '}
.foot-bottom .credit{background:var(--lime);color:var(--bg);display:flex;align-items:center;padding:0 clamp(14px,2.5vw,32px);font-size:11px;letter-spacing:.2em;text-transform:uppercase;white-space:nowrap}
.foot-links{display:flex;justify-content:space-between;flex-wrap:wrap;gap:12px;padding:14px clamp(16px,3vw,24px);font-size:10px;letter-spacing:.15em;color:var(--faint);text-transform:uppercase}
.foot-links a{color:var(--faint);transition:color .15s}
.foot-links a:hover{color:var(--lime)}
.foot-links .grp{display:flex;gap:clamp(12px,2vw,24px);flex-wrap:wrap}

/* Reveal */
.reveal{opacity:0;transform:translateY(16px);transition:opacity .5s ease,transform .5s ease}
.reveal.in{opacity:1;transform:none}

/* ── Breakpoints ── */
@media(max-width:1200px){
  .modules-grid{grid-template-columns:1fr 1fr}
  .mod:nth-child(2){border-right:none}
  .mod:nth-child(3){border-right:none;border-top:1px solid var(--line)}
  .hero-bar{grid-template-columns:1fr 1fr}
  .hero-bar .cell:nth-child(3){border-right:none}
  .hero-bar .cta-cell{grid-column:1/-1;border-top:1px solid var(--line);justify-content:flex-start}
  .stat-strip{grid-template-columns:1fr 1fr}
  .stat-strip .sc:nth-child(2){border-right:none}
  .stat-strip .sc:nth-child(3){border-top:1px solid var(--line)}
  .stat-strip .launch{grid-column:1/-1;padding:18px;border-top:1px solid var(--line)}
}
@media(max-width:768px){
  .modules-grid{grid-template-columns:1fr}
  .mod{border-right:none;border-bottom:1px solid var(--line)}
  .mod:last-child{border-bottom:none}
  .mod .viz{opacity:1;height:200px}
  .mod:nth-child(3){border-top:none}
  .hero-bar{grid-template-columns:1fr}
  .hero-bar .cell{border-right:none;border-bottom:1px solid var(--line)}
  .hero-bar .cta-cell{grid-column:auto;border-top:none}
  .sec-head{grid-template-columns:1fr}
  .sec-head>div+div{border-left:none;border-top:1px solid var(--line)}
  .foot-bottom{grid-template-columns:1fr}
  .foot-bottom .credit{display:none}
}
@media(max-width:480px){
  .hero-bar .cta-cell .btn{width:100%;justify-content:center}
}
`;

/* ── Moteur 3D ───────────────────────────────────────────────────────────── */
function run3D() {
  const LIME = getComputedStyle(document.documentElement).getPropertyValue('--lime').trim() || '#60a5fa';
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function vnorm(p: number[]): number[] { const l = Math.hypot(p[0], p[1], p[2]); return [p[0]/l, p[1]/l, p[2]/l]; }
  function d3(a: number[], b: number[]): number { return Math.hypot(a[0]-b[0], a[1]-b[1], a[2]-b[2]); }
  function shapeIco() {
    const t=(1+Math.sqrt(5))/2;
    const raw=[[-1,t,0],[1,t,0],[-1,-t,0],[1,-t,0],[0,-1,t],[0,1,t],[0,-1,-t],[0,1,-t],[t,0,-1],[t,0,1],[-t,0,-1],[-t,0,1]];
    const v=raw.map(vnorm);const edges:number[][]=[];let min=Infinity;
    for(let i=0;i<v.length;i++)for(let j=i+1;j<v.length;j++){const dd=d3(v[i],v[j]);if(dd<min)min=dd;}
    for(let i=0;i<v.length;i++)for(let j=i+1;j<v.length;j++){if(d3(v[i],v[j])<min*1.05)edges.push([i,j]);}
    return {verts:v,edges,dots:true,lw:1};
  }
  function shapeRings(){const polys:number[][][]=[];[1,.76,.52,.3].forEach(r=>{const pts:number[][]=[];for(let a=0;a<=56;a++){const ang=a/56*Math.PI*2;pts.push([Math.cos(ang)*r,Math.sin(ang)*r,0]);}polys.push(pts);});return{polys,lw:5,dash:[2,6],baseTilt:-0.9};}
  function shapeStack(){const verts:number[][]=[];const edges:number[][]=[];for(let k=0;k<4;k++){const y=.72-k*.48,s=.5+k*.16,b=verts.length;verts.push([-s,y,-s*.55],[s,y,-s*.55],[s,y,s*.55],[-s,y,s*.55]);edges.push([b,b+1],[b+1,b+2],[b+2,b+3],[b+3,b]);if(k>0)edges.push([b,b-4],[b+2,b-2]);}return{verts,edges,lw:1,dots:false};}
  const SHAPES:Record<string,()=>any>={ico:shapeIco,rings:shapeRings,stack:shapeStack};
  type Item={cv:HTMLCanvasElement;ctx:CanvasRenderingContext2D;shape:any;ry:number;rx:number;vy:number;vx:number;hoverTX:number;hoverTY:number;curTX:number;curTY:number;auto:number;drag:boolean;lastX:number;lastY:number;dpr:number};
  const items:Item[]=[];
  document.querySelectorAll<HTMLCanvasElement>('canvas.w3d').forEach(cv=>{
    const kind=cv.getAttribute('data-shape')||'ico';
    const shape=(SHAPES[kind]||shapeIco)();
    const ctx=cv.getContext('2d')!;
    const st:Item={cv,ctx,shape,ry:Math.random()*6,rx:shape.baseTilt??-0.35,vy:0,vx:0,hoverTX:0,hoverTY:0,curTX:0,curTY:0,auto:reduced?0:.006,drag:false,lastX:0,lastY:0,dpr:1};
    items.push(st);
    cv.addEventListener('mousemove',ev=>{if(st.drag){st.vy=(ev.clientX-st.lastX)*.008;st.vx=(ev.clientY-st.lastY)*.008;st.ry+=st.vy;st.rx+=st.vx;st.lastX=ev.clientX;st.lastY=ev.clientY;}else{const r=cv.getBoundingClientRect();st.hoverTY=((ev.clientX-r.left)/r.width-.5)*.9;st.hoverTX=((ev.clientY-r.top)/r.height-.5)*.7;}});
    cv.addEventListener('mouseleave',()=>{st.hoverTX=0;st.hoverTY=0;st.drag=false;});
    cv.addEventListener('mousedown',ev=>{st.drag=true;st.lastX=ev.clientX;st.lastY=ev.clientY;ev.preventDefault();});
    window.addEventListener('mouseup',()=>{st.drag=false;});
  });
  function resize(){const dpr=Math.min(window.devicePixelRatio||1,2);items.forEach(st=>{const w=st.cv.clientWidth,h=st.cv.clientHeight;if(w&&h){st.cv.width=w*dpr;st.cv.height=h*dpr;st.dpr=dpr;}});}
  window.addEventListener('resize',resize);resize();
  function project(p:number[],rx:number,ry:number,cx:number,cy:number,scale:number):number[]{
    const cy2=Math.cos(ry),sy=Math.sin(ry),cx2=Math.cos(rx),sx=Math.sin(rx);
    const x=p[0]*cy2+p[2]*sy;let z=-p[0]*sy+p[2]*cy2;
    const y=p[1]*cx2-z*sx;z=p[1]*sx+z*cx2;
    const f=3.4,persp=f/(f-z);
    return[cx+x*scale*persp,cy+y*scale*persp,persp];
  }
  function draw(st:Item){
    const{ctx,cv}=st;if(!cv.width)return;
    const w=cv.width,h=cv.height,cx=w/2,cy=h/2,scale=Math.min(w,h)*.33;
    ctx.clearRect(0,0,w,h);
    ctx.strokeStyle=LIME;ctx.fillStyle=LIME;ctx.globalAlpha=.8;
    ctx.lineWidth=(st.shape.lw||1)*st.dpr;
    ctx.setLineDash(st.shape.dash?st.shape.dash.map((x:number)=>x*st.dpr):[]);
    const rx=st.rx+st.curTX,ry=st.ry+st.curTY;
    if(st.shape.polys){st.shape.polys.forEach((poly:number[][])=>{ctx.beginPath();poly.forEach((pt,i)=>{const q=project(pt,rx,ry,cx,cy,scale);if(i===0)ctx.moveTo(q[0],q[1]);else ctx.lineTo(q[0],q[1]);});ctx.stroke();});}
    if(st.shape.verts){const pts=st.shape.verts.map((p:number[])=>project(p,rx,ry,cx,cy,scale));ctx.beginPath();st.shape.edges.forEach((e:number[])=>{ctx.moveTo(pts[e[0]][0],pts[e[0]][1]);ctx.lineTo(pts[e[1]][0],pts[e[1]][1]);});ctx.stroke();if(st.shape.dots)pts.forEach((q:number[])=>{ctx.beginPath();ctx.arc(q[0],q[1],3.4*st.dpr*q[2],0,Math.PI*2);ctx.fill();});}
    ctx.globalAlpha=1;
  }
  function loop(){
    items.forEach(st=>{
      st.ry+=st.auto+(st.drag?0:st.vy);st.rx+=st.drag?0:st.vx;
      st.vy*=.95;st.vx*=.95;
      const base=st.shape.baseTilt??-.35;
      if(st.rx>base+1.2)st.rx=base+1.2;if(st.rx<base-1.2)st.rx=base-1.2;
      st.curTX+=(st.hoverTX-st.curTX)*.08;st.curTY+=(st.hoverTY-st.curTY)*.08;
      draw(st);
    });
    if(!reduced)requestAnimationFrame(loop);
  }
  if(reduced)items.forEach(draw);else requestAnimationFrame(loop);
}

/* ── Composant principal ─────────────────────────────────────────────────── */
export default function HomePage() {
  useEffect(() => {
    const io = new IntersectionObserver(
      (entries) => entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }),
      { threshold: .12 }
    );
    document.querySelectorAll('.reveal').forEach(el => io.observe(el));

    const mods = document.querySelectorAll('.mod');
    const offs: Array<() => void> = [];
    mods.forEach(m => {
      const h = () => { mods.forEach(x => x.classList.remove('active')); m.classList.add('active'); };
      m.addEventListener('mouseenter', h);
      offs.push(() => m.removeEventListener('mouseenter', h));
    });

    run3D();
    return () => { io.disconnect(); offs.forEach(f => f()); };
  }, []);

  return (
    <div className="hp-page">
      <style>{CSS}</style>

      {/* ── Nav ── */}
      <nav className="hp-nav">
        <div className="hp-wrap">
          <span className="hp-logo">&lt;PETRIX <span className="l">/&gt;</span></span>
          <Link to="/login" className="nav-cta">
            () =&gt; <span style={{ color: 'var(--lime)' }}>CONNEXION</span>
          </Link>
        </div>
      </nav>

      {/* ── Hero ── */}
      <header className="hero">
        <div className="hp-wrap">
          <span className="built">Self-hosted · ANSSI-BP-028 · Mistral AI</span>
          <h1>&lt;PETRIX <span className="l">/&gt;</span></h1>
          <p className="sub">
            Plateforme d'audit cybersécurité auto-hébergée — inventaire d'actifs,
            veille CVE CERT-FR, durcissement ANSSI, analyse&nbsp;
            <strong style={{ color: 'var(--lime)', fontWeight: 600 }}>Mistral AI</strong>.
            Vos données restent chez vous.
          </p>
          <div className="hero-bar reveal">
            <div className="cell">
              <span className="k">Stack</span>
              <span className="v">FastAPI · React · PostgreSQL · Celery</span>
            </div>
            <div className="cell">
              <span className="k">OS supportés</span>
              <span className="v">Linux · macOS · Windows</span>
            </div>
            <div className="cell">
              <span className="k">Contrôles ANSSI</span>
              <span className="v">80+ checks · Grade A–F</span>
            </div>
            <div className="cta-cell">
              <Link to="/login" className="btn">ACCÉDER →</Link>
            </div>
          </div>
        </div>
      </header>

      {/* ── Modules ── */}
      <section className="hp-wrap reveal">
        <div className="sec-head">
          <div className="n">01 · modules</div>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: 15, color: 'var(--text)', letterSpacing: '.04em' }}>
            IMPORT &#123; <span style={{ color: 'var(--lime)' }}>CORE</span> &#125; FROM <span style={{ color: 'var(--lime)' }}>"./PETRIX"</span>
          </div>
          <div>3 MODULES ACTIFS</div>
        </div>
        <div className="modules-grid">
          <article className="mod active">
            <div className="viz"><canvas className="w3d" data-shape="stack" /></div>
            <div className="meta">
              <div className="idx">Modules[01]</div>
              <h3>Inventaire des actifs</h3>
            </div>
            <div className="foot"><span>Cibles SSH · Linux · macOS · Windows</span><span>LIVE</span></div>
          </article>
          <article className="mod">
            <div className="viz"><canvas className="w3d" data-shape="rings" /></div>
            <div className="meta">
              <div className="idx">Modules[02]</div>
              <h3>Veille CVE &amp; CERT-FR</h3>
            </div>
            <div className="foot"><span>Alertes temps réel · Corrélations CVE</span><span>LIVE</span></div>
          </article>
          <article className="mod">
            <div className="viz"><canvas className="w3d" data-shape="ico" /></div>
            <div className="meta">
              <div className="idx">Modules[03]</div>
              <h3>Durcissement HCO</h3>
            </div>
            <div className="foot"><span>ANSSI-BP-028 · Rapport IA Mistral</span><span>LIVE</span></div>
          </article>
        </div>

        {/* Stat strip + CTA final */}
        <div className="stat-strip reveal">
          <div className="sc"><div className="v">80+</div><div className="k">Contrôles ANSSI</div></div>
          <div className="sc"><div className="v">3</div><div className="k">OS</div></div>
          <div className="sc"><div className="v">4</div><div className="k">Rôles RBAC</div></div>
          <div className="sc"><div className="v">A–F</div><div className="k">Grade ANSSI</div></div>
          <Link to="/login" className="launch">LANCER L'APPLICATION →</Link>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="hp-footer" id="confidentialite">
        <div className="hp-wrap" style={{ padding: 0 }}>
          <div className="foot-bottom">
            <div className="fc">© 2026 &lt;PETRIX /&gt; · N. IKIREZI &amp; M. MISSAK · ESGI 4SI4</div>
            <div className="fc">Mistral AI · AWS EC2 eu-west-1 · PostgreSQL RDS</div>
            <div className="credit">OPEN-SOURCE · MIT</div>
          </div>
          <div className="foot-links">
            <div className="grp">
              <a href="#confidentialite">Politique de confidentialité</a>
              <a href="#confidentialite">RGPD — art. 6.1.f · Données hébergées on-prem</a>
            </div>
            <div className="grp">
              <a href="https://gitlab.com/petrix1/petrix" target="_blank" rel="noopener noreferrer">GitLab</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
