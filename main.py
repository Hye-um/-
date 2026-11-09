# =============================================================
#  우리반 경제나라 — 스트림릿 단일 파일 앱 (main.py)
#  실행: streamlit run main.py
#
#  ▶ 여러 기기에서 같은 학급을 쓰는 방법
#    - 이 앱은 스트림릿 서버에 학급 데이터를 모아 두고, 모든 기기가 같은 데이터를 봐요.
#    - 데이터가 사라지지 않게 하려면, 스트림릿 클라우드의 Settings → Secrets 에
#      아래 두 줄을 넣어 "비공개 깃허브 저장소"에 자동 저장되게 하세요.
#          GITHUB_TOKEN = "github_pat_..."
#          GITHUB_REPO  = "내아이디/class-economy-data"
#    - Secrets가 없으면 "임시 저장 모드"로 동작해요 (앱이 다시 시작되면 사라질 수 있음).
# =============================================================
import base64
import hashlib
import json
import os
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="우리반 경제나라", page_icon="🏫", layout="wide")
st.markdown(
    "<style>#MainMenu, header, footer {visibility:hidden;} "
    ".block-container {padding:0 !important; max-width:100% !important;}</style>",
    unsafe_allow_html=True,
)

APP_HTML = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>우리반 경제나라</title>
<style>
:root{
  --bg:#FFF6EE; --bg2:#FFEADB; --card:#FFFFFF; --ink:#5B4B45; --sub:#A08C84;
  --accent:#FFAA8F; --accent-d:#EE8B6E; --line:#F3E2D6;
  --mint:#C9EEDC; --lav:#E1DBF7; --yel:#FFEDB0; --pink:#FFDCE3; --sky:#D6ECFB;
  --plus:#3BA57A; --minus:#E8746A;
  --shadow:0 6px 18px rgba(196,140,112,.16); --r:22px;
}
body[data-theme=mint]{--bg:#F1FAF5;--bg2:#DDF3E7;--accent:#86D2B0;--accent-d:#5DB990;--line:#D6EDE1;--shadow:0 6px 18px rgba(93,185,144,.16)}
body[data-theme=lavender]{--bg:#F7F4FF;--bg2:#E9E3FF;--accent:#B9A9F2;--accent-d:#9682E2;--line:#E3DCF8;--shadow:0 6px 18px rgba(150,130,226,.16)}
body[data-theme=sky]{--bg:#F2F8FF;--bg2:#DDEEFC;--accent:#8FC6F0;--accent-d:#64A9E0;--line:#D7E8F6;--shadow:0 6px 18px rgba(100,169,224,.16)}
body[data-theme=lemon]{--bg:#FFFBEA;--bg2:#FFF1C2;--accent:#F7C96B;--accent-d:#E3AC3C;--line:#F5E8BE;--shadow:0 6px 18px rgba(227,172,60,.16)}
body[data-theme=berry]{--bg:#FFF4F7;--bg2:#FFE0E9;--accent:#F5A3BC;--accent-d:#E07D9C;--line:#F7DCE4;--shadow:0 6px 18px rgba(224,125,156,.16)}

*{box-sizing:border-box}
html{font-size:16px}
body{margin:0;font-family:'Gowun Dodum','Apple SD Gothic Neo','Malgun Gothic',sans-serif;background:var(--bg);color:var(--ink);min-height:100vh;transition:background .3s}
#scroller{position:fixed;inset:0;overflow-y:auto;-webkit-overflow-scrolling:touch}
#app{max-width:1040px;margin:0 auto;padding:16px 16px 60px;min-height:100vh}
h1,h2,h3,.jua{font-family:'Jua','Apple SD Gothic Neo','Malgun Gothic',sans-serif;font-weight:400}
h1{margin:6px 0}
h3{margin:0 0 10px;font-size:1.15rem}
p{line-height:1.6}
.sub{color:var(--sub);font-size:.92rem}
.mt{margin-top:12px}
.center{text-align:center}
.big{font-size:1.25rem}
.nowrap{white-space:nowrap}
.clip{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.plus{color:var(--plus)} .minus{color:var(--minus)}
.up{color:#E8574A} .down{color:#4A8FE8}

.btn{font-family:'Jua','Apple SD Gothic Neo','Malgun Gothic',sans-serif;border:none;border-radius:14px;padding:10px 16px;font-size:1rem;cursor:pointer;background:var(--accent);color:#fff;box-shadow:0 3px 0 var(--accent-d);transition:transform .08s, box-shadow .08s;white-space:nowrap}
.btn:active{transform:translateY(2px);box-shadow:0 1px 0 var(--accent-d)}
.btn.sub{background:#fff;color:var(--ink);box-shadow:0 3px 0 var(--line);border:2px solid var(--line)}
.btn.sm{padding:6px 11px;font-size:.88rem;border-radius:11px}
.btn.danger{background:#FF9F9F;box-shadow:0 3px 0 #E57E7E}
.btn.mint{background:#7FCFAB;box-shadow:0 3px 0 #58B48C}
.btn.wide{width:100%;padding:14px;font-size:1.15rem}
.btn:disabled{opacity:.45;cursor:not-allowed}
.link{background:none;border:none;color:var(--accent-d);font-family:inherit;font-size:.95rem;cursor:pointer;text-decoration:underline;margin-top:8px}

.card{background:var(--card);border-radius:var(--r);padding:18px;box-shadow:var(--shadow);margin-bottom:14px}
input,select,textarea{font-family:inherit;font-size:1rem;padding:10px 12px;border:2px solid var(--line);border-radius:12px;background:#fff;color:var(--ink);width:100%;outline:none}
input:focus,select:focus,textarea:focus{border-color:var(--accent)}
input[type=range]{border:none;padding:0;accent-color:var(--accent-d)}
input[type=checkbox]{width:20px;height:20px;accent-color:var(--accent-d);vertical-align:middle}
select.sm,input.sm{width:auto;padding:6px 8px;font-size:.9rem;border-radius:10px}
input.num{width:90px}
textarea{resize:vertical;line-height:1.5}
label.f{display:block;margin:10px 0 4px;font-size:.9rem;color:var(--sub)}
.row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.row.end{justify-content:flex-end}
.row.between{justify-content:space-between}
.row>.grow{flex:1;min-width:120px}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px;align-items:start}
.two>.card{margin-bottom:0}
.grid2{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px;margin-bottom:14px}
.grid2>.card{margin-bottom:0}
.stack>*+*{margin-top:14px}

/* 로그인 */
.center-screen{min-height:92vh;display:flex;align-items:center;justify-content:center}
.login-card{max-width:420px;width:100%;text-align:center;padding:32px 26px}
.logo{font-size:68px;line-height:1}
.big-input{text-align:center;font-size:1.4rem;letter-spacing:4px;margin:14px 0;text-transform:uppercase;font-family:'Jua'}
.hint{background:var(--bg2);border-radius:14px;padding:10px;margin:16px 0 6px;font-size:.88rem;color:var(--sub);line-height:1.6}
.role-btns{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:20px}
.role-btn{border:none;border-radius:24px;padding:26px 10px;font-family:'Jua';font-size:1.3rem;cursor:pointer;color:var(--ink);box-shadow:var(--shadow);transition:transform .15s}
.role-btn:hover{transform:translateY(-3px)}
.role-btn span{display:block;font-size:54px;margin-bottom:6px}
.pick-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:10px;margin-top:16px;max-height:55vh;overflow:auto;padding:4px}
.pick-btn{background:#fff;border:2px solid var(--line);border-radius:16px;padding:14px 6px;font-family:'Jua';font-size:1.05rem;cursor:pointer;color:var(--ink)}
.pick-btn:hover{border-color:var(--accent)}
.pick-btn small{display:block;color:var(--sub);font-family:'Gowun Dodum';font-size:.8rem}
.dots{display:flex;justify-content:center;gap:16px;margin:20px 0}
.dot{width:20px;height:20px;border-radius:50%;border:3px solid var(--accent);transition:.15s}
.dot.on{background:var(--accent);transform:scale(1.1)}
.shake{animation:shake .4s}
@keyframes shake{0%,100%{transform:translateX(0)}25%{transform:translateX(-10px)}75%{transform:translateX(10px)}}
.keypad{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;max-width:290px;margin:0 auto}
.key{height:62px;border:none;border-radius:18px;background:var(--bg2);font-family:'Jua';font-size:1.5rem;color:var(--ink);cursor:pointer;transition:.1s}
.key:active{background:var(--accent);color:#fff}

/* 상단바 & 홈 */
.topbar{display:flex;align-items:center;gap:10px;margin-bottom:14px}
.tb-title{flex:1;font-family:'Jua';font-size:1.4rem;min-width:0}
.icon-btn{width:44px;height:44px;flex:0 0 44px;border-radius:14px;border:none;background:#fff;box-shadow:var(--shadow);font-size:1.25rem;cursor:pointer;color:var(--ink)}
.brand{font-size:1.9rem}
.preview-banner{background:var(--yel);border-radius:14px;padding:9px 14px;margin-bottom:14px;font-family:'Jua';text-align:center}
.hero{background:linear-gradient(135deg,var(--bg2),#fff 75%)}
.hello{font-size:1.1rem;margin-bottom:8px}
.money-big{font-family:'Jua';font-size:2.3rem;color:var(--accent-d);margin:2px 0}
.chip{display:inline-block;background:var(--bg2);border-radius:999px;padding:4px 12px;margin:6px 6px 0 0;font-size:.88rem}
.chip.mint{background:var(--mint)} .chip.yel{background:var(--yel)} .chip.pink{background:var(--pink)} .chip.lav{background:var(--lav)}
.notice{cursor:pointer;border-left:6px solid var(--accent)}
.app-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:14px}
.tile{position:relative;border:none;border-radius:26px;padding:18px 8px;cursor:pointer;font-family:'Jua';font-size:1rem;color:var(--ink);box-shadow:var(--shadow);transition:transform .15s;min-height:126px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;line-height:1.25}
.tile:hover{transform:translateY(-4px) rotate(-1deg)}
.tile .ic{font-size:46px;line-height:1}
.tile .badge{position:absolute;top:9px;right:11px;background:#FF8A8A;color:#fff;border-radius:999px;min-width:24px;height:24px;font-size:.82rem;display:flex;align-items:center;justify-content:center;padding:0 7px}
.tile .tag{position:absolute;bottom:7px;font-size:.7rem;color:var(--sub);font-family:'Gowun Dodum'}
.stats3{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.stat{text-align:center;background:#fff;border-radius:16px;padding:10px 4px}
.stat .n{font-family:'Jua';font-size:1.45rem;color:var(--accent-d)}

/* 탭, 표, 목록 */
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px}
.tab{border:none;background:#fff;border-radius:999px;padding:9px 16px;font-family:'Jua';font-size:.98rem;color:var(--sub);cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.05)}
.tab.on{background:var(--accent);color:#fff}
.tbl-wrap{overflow-x:auto}
table.t{width:100%;border-collapse:collapse;font-size:.95rem}
.t th{font-family:'Jua';font-weight:400;color:var(--sub);text-align:left;padding:8px;border-bottom:2px solid var(--line);white-space:nowrap}
.t td{padding:8px;border-bottom:1px dashed var(--line);vertical-align:middle}
.t td.r{white-space:nowrap}
.t input.num{width:78px}
.t td.r,.t th.r{text-align:right}
.kv{display:flex;justify-content:space-between;gap:10px;padding:7px 0;border-bottom:1px dashed var(--line)}
.kv:last-child{border-bottom:none}
.alert{background:var(--pink);border-radius:14px;padding:10px 14px;margin-top:12px;display:flex;gap:10px;align-items:center;justify-content:space-between;flex-wrap:wrap}
.empty{color:var(--sub);text-align:center;padding:20px}
.item{display:flex;gap:12px;align-items:center;padding:11px 0;border-bottom:1px dashed var(--line)}
.item:last-child{border-bottom:none}
.item .grow{flex:1;min-width:0}
.item .emo{font-size:30px;width:42px;text-align:center}
.status{border-radius:8px;padding:2px 9px;font-size:.82rem;white-space:nowrap}
.st-pending{background:var(--yel)} .st-approved,.st-active{background:var(--mint)} .st-rejected{background:#F3E3E3} .st-ended,.st-cancelled{background:#EEE7E2}

/* 마트 */
.prod{text-align:center;display:flex;flex-direction:column;gap:6px}
.prod .emo{font-size:56px;line-height:1.1}
.prod .price{font-family:'Jua';font-size:1.3rem;color:var(--accent-d)}
.stepper{display:flex;align-items:center;justify-content:center;gap:6px}
.stepper button{width:34px;height:34px;border-radius:10px;border:none;background:var(--bg2);font-size:1.1rem;cursor:pointer;color:var(--ink)}
.stepper input{width:56px;text-align:center;padding:6px}

/* 신용 */
.grade-boxes{display:flex;gap:4px;margin:12px 0}
.gb{flex:1;height:34px;border-radius:9px;background:var(--bg2);display:flex;align-items:center;justify-content:center;font-size:.8rem;color:var(--sub)}
.gb.on{background:var(--accent);color:#fff;font-family:'Jua';font-size:1rem}

/* 주식 */
.chart{width:100%;height:auto;display:block;margin:8px 0;background:var(--bg);border-radius:12px}
.price-big{font-family:'Jua';font-size:1.6rem}

/* 자리 */
.desk{background:var(--bg2);text-align:center;padding:9px;border-radius:12px;font-family:'Jua';margin-bottom:12px}
.seatmap{display:grid;gap:8px}
.seat{border:2px solid var(--line);background:#fff;border-radius:14px;padding:7px 3px;font-size:.78rem;cursor:pointer;text-align:center;min-height:70px;font-family:inherit;color:var(--ink);line-height:1.35}
.seat:hover{border-color:var(--accent)}
.seat.taken{background:var(--lav)}
.seat.mine{background:var(--yel);border-color:#F2C443}
.seat.req{border-style:dashed;border-color:var(--accent-d)}
.seat b{display:block;font-family:'Jua';font-size:.95rem}

/* 헌법 & 뉴스 */
.article{padding:12px 0;border-bottom:1px dashed var(--line)}
.article:last-child{border-bottom:none}
.article .no{font-family:'Jua';color:var(--accent-d);font-size:1.08rem}
.preamble{background:var(--bg2);border-radius:16px;padding:14px 16px;line-height:1.8;white-space:pre-wrap}
.meta{color:var(--sub);font-size:.85rem}
.body{white-space:pre-wrap;line-height:1.7;margin-top:8px;word-break:break-word}
.cat{background:var(--mint);border-radius:8px;padding:2px 9px;font-size:.8rem;margin-right:6px}

/* 설정 */
.swatch{width:46px;height:46px;border-radius:50%;border:3px solid #fff;box-shadow:var(--shadow);cursor:pointer}
.swatch.on{outline:3px solid var(--accent-d);outline-offset:2px}
.bar-row{display:flex;align-items:center;gap:8px;margin:6px 0;font-size:.92rem}
.bar-row .nm{width:72px;flex:0 0 72px}
.bar-row .bt{flex:1;background:var(--bg2);border-radius:8px;height:16px;overflow:hidden}
.bar-row .bf{height:100%;background:var(--accent);border-radius:8px}
.bar-row .vv{width:96px;text-align:right;flex:0 0 96px}
.feat{display:flex;gap:16px;align-items:center}
.feat .emo{font-size:52px}
.code-show{font-family:'Jua';font-size:2rem;letter-spacing:4px;color:var(--accent-d)}

/* 모달 & 토스트 */
.overlay{position:fixed;inset:0;background:rgba(90,70,60,.35);display:flex;align-items:center;justify-content:center;z-index:50;padding:16px}
.modal{background:#fff;border-radius:24px;padding:22px;width:100%;max-width:500px;max-height:88vh;overflow:auto;animation:pop .2s}
.modal h3{font-size:1.25rem}
.modal .acts{display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap;margin-top:18px}
@keyframes pop{from{transform:scale(.92);opacity:0}to{transform:scale(1);opacity:1}}
#toast{position:fixed;left:50%;bottom:30px;transform:translateX(-50%) translateY(20px);background:var(--ink);color:#fff;padding:12px 22px;border-radius:999px;opacity:0;transition:.25s;z-index:100;font-family:'Jua';pointer-events:none;max-width:90vw;text-align:center}
#toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
#dim{position:fixed;inset:0;background:#000;opacity:0;pointer-events:none;z-index:200;transition:opacity .2s}

@media (max-width:560px){
  #app{padding:12px 12px 50px}
  .app-grid{grid-template-columns:repeat(3,1fr);gap:10px}
  .tile{min-height:104px;font-size:.84rem;border-radius:20px;padding:12px 4px}
  .tile .ic{font-size:36px}
  .money-big{font-size:1.9rem}
  .tb-title{font-size:1.15rem}
  .stat .n{font-size:1.1rem}
  .bar-row .vv{width:80px;flex-basis:80px;font-size:.8rem}
}
</style>
</head>
<body>
<div id="scroller"><div id="app"></div></div>
<div id="modal-root"></div>
<div id="toast"></div>
<div id="dim"></div>

<script>
'use strict';
/* =========================================================
   우리반 경제나라 — 학급 화폐 경제 시뮬레이션
   데이터는 이 브라우저의 localStorage에 저장됩니다.
   ========================================================= */

/* ---------- 기본 도구 ---------- */
const STORE = 'classEconomy_v1';
const memStore = {};
function lsGet(k){ try{ const v = localStorage.getItem(k); return v!==null ? v : (memStore[k] ?? null); }catch(e){ return memStore[k] ?? null; } }
function lsSet(k,v){ memStore[k]=v; try{ localStorage.setItem(k,v); }catch(e){} }
const $ = id => document.getElementById(id);
const val = id => { const e=$(id); return e ? String(e.value).trim() : ''; };
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const uid = () => Date.now().toString(36) + Math.random().toString(36).slice(2,7);
const now = () => new Date().toISOString();
const rand4 = () => String(Math.floor(Math.random()*10000)).padStart(4,'0');
const num = v => { const n = parseInt(String(v).replace(/[^0-9-]/g,''),10); return isNaN(n) ? 0 : n; };
const pad = n => String(n).padStart(2,'0');
function fdate(iso){ const d=new Date(iso); return `${d.getMonth()+1}/${d.getDate()} ${pad(d.getHours())}:${pad(d.getMinutes())}`; }
function fday(iso){ const d=new Date(iso); return `${d.getFullYear()}.${d.getMonth()+1}.${d.getDate()}`; }
function won(n){ const c=C(); return Math.round(n||0).toLocaleString('ko-KR') + (c ? c.currency : '원'); }
function signed(n){ return (n>0?'+':n<0?'−':'') + won(Math.abs(n)); }

let toastTimer=null;
function toast(msg){ const t=$('toast'); t.textContent=msg; t.classList.add('show'); clearTimeout(toastTimer); toastTimer=setTimeout(()=>t.classList.remove('show'),2200); }
function modal(title, body, actions){
  $('modal-root').innerHTML = `<div class="overlay" onclick="if(event.target===this)closeModal()"><div class="modal"><h3>${title}</h3><div>${body}</div><div class="acts">${actions||''}<button class="btn sub" onclick="closeModal()">닫기</button></div></div></div>`;
}
function closeModal(){ $('modal-root').innerHTML=''; setTimeout(syncIdle,0); }
let _cb=null;
function ask(msg, cb, ok){ _cb=cb; modal('🤔 확인해 주세요', `<p>${msg}</p>`, `<button class="btn" onclick="runCb()">${ok||'확인'}</button>`); }
function runCb(){ const f=_cb; _cb=null; closeModal(); if(f) f(); }

/* ---------- 데이터 ---------- */
let DB = null;
function save(){ lsSet(STORE, JSON.stringify(DB)); syncSoon(); }

/* ---------- 여러 기기 동기화 (스트림릿 서버와 주고받기) ---------- */
const SYNC = {on: window.parent!==window, got:false, ready:false, ver:0, base:null, sent:null, seq:0, nonce:0,
  cid: Date.now().toString(36)+Math.random().toString(36).slice(2,12), timer:null, pending:null, needRender:false, mode:'', err:''};
const clone = o => JSON.parse(JSON.stringify(o));
function stable(o){
  if(o===null || typeof o!=='object') return JSON.stringify(o);
  if(Array.isArray(o)) return '['+o.map(stable).join(',')+']';
  return '{'+Object.keys(o).filter(k=>o[k]!==undefined).sort().map(k=>JSON.stringify(k)+':'+stable(o[k])).join(',')+'}';
}
const same = (a,b) => a===b || stable(a)===stable(b);
const isObj = o => o!==null && typeof o==='object' && !Array.isArray(o);
const keyOf = x => isObj(x) ? (x.id!==undefined ? 'i'+x.id : (x.code!==undefined ? 'c'+x.code : null)) : null;
/* 같은 시간에 두 기기가 바꾼 내용을 합치기 (b: 공통 원본, m: 내 것, t: 서버 것) */
function merge3(b,m,t){
  if(same(m,b)) return clone(t);
  if(same(t,b) || same(m,t)) return clone(m);
  if(typeof m==='number' && typeof t==='number' && typeof b==='number') return t+(m-b);   // 잔액·재고는 변화량을 더함
  if(Array.isArray(m) && Array.isArray(t)){
    const bb = Array.isArray(b) ? b : [], all=[...bb,...m,...t];
    if(all.every(x=>keyOf(x)!==null)) return mergeKeyed(bb,m,t);
    if(all.every(x=>x===null || typeof x!=='object')){
      const out=t.filter(x=>!(bb.includes(x) && !m.includes(x)));
      m.forEach(x=>{ if(!bb.includes(x) && !out.includes(x)) out.push(x); });
      return out;
    }
    return clone(m);
  }
  if(isObj(m) && isObj(t)){
    const bb = isObj(b) ? b : {}, out={};
    new Set([...Object.keys(t), ...Object.keys(m)]).forEach(k=>{
      const inM=k in m, inT=k in t, inB=k in bb;
      if(inM && inT) out[k]=merge3(bb[k], m[k], t[k]);
      else if(inM){ if(!inB) out[k]=clone(m[k]); }
      else if(inT){ if(!inB) out[k]=clone(t[k]); }
    });
    return out;
  }
  return clone(m);
}
function mergeKeyed(b,m,t){
  const bm=new Map(b.map(x=>[keyOf(x),x])), mm=new Map(m.map(x=>[keyOf(x),x])), tm=new Map(t.map(x=>[keyOf(x),x]));
  const mid=[], front=[], back=[]; let old=false;
  t.forEach(x=>{ const k=keyOf(x); if(mm.has(k)) mid.push(merge3(bm.get(k), mm.get(k), x)); else if(!bm.has(k)) mid.push(clone(x)); });
  m.forEach(x=>{ const k=keyOf(x); if(tm.has(k) || bm.has(k)){ old=true; return; } (old?back:front).push(clone(x)); });
  return [...front, ...mid, ...back];
}
function syncSend(){
  if(!SYNC.on) return;
  SYNC.nonce++;
  const value = {cid:SYNC.cid, nonce:SYNC.nonce, baseVer:SYNC.ver, save: SYNC.sent ? {seq:SYNC.sent.seq, base:SYNC.sent.base, db:SYNC.sent.db} : null};
  try{ window.parent.postMessage({isStreamlitMessage:true, type:'streamlit:setComponentValue', value, dataType:'json'}, '*'); }catch(e){}
}
function syncSoon(){ if(!SYNC.on || !SYNC.ready) return; clearTimeout(SYNC.timer); SYNC.timer=setTimeout(syncFlush, 250); }
function syncFlush(){
  if(!SYNC.on || !SYNC.ready || SYNC.sent) return;
  if(SYNC.base && stable(DB)===stable(SYNC.base)) return;
  SYNC.seq++; SYNC.sent = {seq:SYNC.seq, base:SYNC.ver, db:clone(DB), fresh:!SYNC.base};
  syncSend();
}
function syncBusy(){
  if($('modal-root').innerHTML) return true;
  const a=document.activeElement;
  return !!(a && /^(INPUT|TEXTAREA|SELECT)$/.test(a.tagName) && $('app').contains(a));
}
function syncIdle(){
  if(SYNC.pending && !$('modal-root').innerHTML) onServer(SYNC.pending);
  if(SYNC.needRender && !syncBusy()){ SYNC.needRender=false; render(); }
}
function onServer(a){
  if(!a) return;
  const first = !SYNC.got;
  SYNC.got=true; SYNC.mode=a.storage||''; SYNC.err=a.err||'';
  if($('modal-root').innerHTML){ SYNC.pending=a; return; }     // 창이 열려 있으면 닫힌 뒤에 반영
  SYNC.pending=null;
  if(!a.ready){ if(first) render(); return; }
  if(!SYNC.ready){
    SYNC.ready=true; SYNC.ver=a.ver;
    if(a.fresh && Object.keys(DB.classes).length){ syncFlush(); render(); return; }  // 서버가 비어 있으면 이 기기 데이터로 시작
  }
  const srv = a.db ? JSON.parse(a.db) : null;
  let myBase = SYNC.base;
  if(SYNC.sent){
    if((a.seen||0) < SYNC.sent.seq) return;                   // 서버가 아직 처리 전
    const ok = (a.acc||0) >= SYNC.sent.seq;
    myBase = ok ? SYNC.sent.db : (SYNC.sent.fresh ? DB : SYNC.base);
    SYNC.sent=null;
  }
  if(srv){
    const before = stable(DB);
    const merged = (!myBase || stable(myBase)===before) ? srv : merge3(myBase, DB, srv);
    DB = clone(merged); if(!isObj(DB.classes)) DB.classes={};
    Object.values(DB.classes).forEach(fillDefaults);
    SYNC.base = srv; SYNC.ver = a.ver;
    if(ensureDemo()) render();
    lsSet(STORE, JSON.stringify(DB));
    if(first || stable(DB)!==before){ if(syncBusy()) SYNC.needRender=true; else render(); }
  }
  syncFlush();
}
function syncStart(){
  if(!SYNC.on) return;
  window.addEventListener('message', e=>{ const d=e.data; if(d && d.type==='streamlit:render') onServer(d.args && d.args.sync); });
  const post = m => { try{ window.parent.postMessage(Object.assign({isStreamlitMessage:true}, m), '*'); }catch(e){} };
  const fit = () => { let h=900; try{ h=window.parent.innerHeight||900; }catch(e){} post({type:'streamlit:setFrameHeight', height:Math.max(480, h-6)}); };
  post({type:'streamlit:componentReady', apiVersion:1});
  fit(); try{ window.parent.addEventListener('resize', fit); }catch(e){} window.addEventListener('resize', fit);
  setInterval(syncIdle, 700);
  (function poll(){ syncSend(); setTimeout(poll, document.hidden ? 15000 : 3000); })();
  setTimeout(()=>{ if(!SYNC.got){ SYNC.got=true; render(); } }, 6000);
}
function storageNote(){
  if(!SYNC.on) return `<div class="sub mt">💻 이 기기에만 저장되고 있어요</div>`;
  if(SYNC.err) return `<div class="alert">⚠️ 온라인 저장소 문제: ${esc(SYNC.err)}</div>`;
  if(SYNC.mode==='github' && SYNC.ready) return `<div class="mt"><span class="chip mint">☁️ 온라인 저장 연결됨 · 어느 기기에서나 열려요</span></div>`;
  if(SYNC.mode==='memory') return `<div class="alert">⚠️ 임시 저장 모드: 다른 기기에서도 열리지만, 앱이 잠들거나 다시 시작되면 사라질 수 있어요. 깃허브 데이터 저장소를 연결해 주세요.</div>`;
  return '';
}

function blankClass(code,name,pin){
  return {
    code, name, teacherPin:pin, currency:'원',
    names:{bank:'햇살', mart:'꿈나무', news:'무지개', securities:'새싹'},
    features:{stock:false, realty:false, insurance:false},
    savingsRate:2, budget:0, budgetLog:[],
    students:[], jobs:[], certs:[], apps:[], products:[], orders:[], tx:[], payslips:[],
    taxNotices:[], taxBills:[], notices:[], news:[],
    law:{preamble:'', articles:[]},
    stocks:[], holdings:{}, brokerCodes:[],
    seatCfg:{rows:4, cols:6, price:300, cycle:14}, seats:[], seatReqs:[], seatRound:'',
    ins:{fund:0, plans:[], members:{}, claims:[]},
    fees:{electric:50, meal:200},
    creditCfg:{max:1000, start:700},
    creditRules:defaultCreditRules(), creditItems:defaultCreditItems(), creditLog:[],
    teacherPrefs:{}
  };
}
function defaultCreditRules(){
  return [
    {id:'tax_pay',     on:true,  pts:5,   n:0, up:true},
    {id:'save_streak', on:true,  pts:3,   n:3, up:true},
    {id:'pay_streak',  on:false, pts:2,   n:4, up:true},
    {id:'tax_late',    on:true,  pts:-5,  n:3, up:false},
    {id:'minus_bal',   on:true,  pts:-10, n:0, up:false},
    {id:'save_break',  on:false, pts:-1,  n:0, up:false}
  ];
}
function defaultCreditItems(){
  return [
    {id:uid(), label:'친구를 도왔어요', pts:3},
    {id:uid(), label:'맡은 일을 성실히 했어요', pts:5},
    {id:uid(), label:'약속을 어겼어요', pts:-5},
    {id:uid(), label:'규칙을 지키지 않았어요', pts:-3}
  ];
}
const RULE_TEXT = {
  tax_pay:     r=>'세금 고지서를 냈을 때',
  save_streak: r=>`${r.n}달 연속 적금(예금 넣기)을 했을 때`,
  pay_streak:  r=>`월급을 ${r.n}번 연속 받았을 때 (꾸준히 일하기)`,
  tax_late:    r=>`세금 고지서를 ${r.n}일 넘게 내지 않았을 때`,
  minus_bal:   r=>'통장 잔액이 마이너스(−)가 되었을 때',
  save_break:  r=>'예금을 중간에 찾았을 때'
};
function basicPlan(c){ return c.ins.plans.find(p=>p.basic); }
function fillDefaults(c){
  const b = blankClass(c.code, c.name, c.teacherPin);
  for(const k in b){ if(c[k]===undefined) c[k]=b[k]; }
  for(const k in b.names){ if(!c.names[k]) c.names[k]=b.names[k]; }
  for(const k in b.features){ if(c.features[k]===undefined) c.features[k]=false; }
  for(const k in b.ins){ if(c.ins[k]===undefined) c.ins[k]=b.ins[k]; }
  for(const k in b.fees){ if(c.fees[k]===undefined) c.fees[k]=b.fees[k]; }
  for(const k in b.creditCfg){ if(!c.creditCfg[k]) c.creditCfg[k]=b.creditCfg[k]; }
  if(!c.seatCfg.cycle) c.seatCfg.cycle=14;
  b.creditRules.forEach(r=>{ if(!c.creditRules.find(x=>x.id===r.id)) c.creditRules.push(r); });
  // 기본 건강보험(필수)
  if(!basicPlan(c)){
    const old=c.ins.plans.find(p=>p.name==='기본 건강보험');
    if(old) old.basic=true; else c.ins.plans.unshift({id:uid(), basic:true, name:'기본 건강보험', premium:100, coverage:500, desc:'모든 학생이 꼭 가입하는 기본 보험이에요. 아프거나 다쳤을 때 보험금을 받아요.'});
  }
  const bp=basicPlan(c);
  // 예전 방식 자리 요청은 정리
  c.seatReqs.forEach(r=>{ if(r.status==='pending' && r.from===undefined) r.status='cancelled'; });
  c.students.forEach(s=>{
    s.certs=s.certs||[]; s.prefs=s.prefs||{}; s.savings=s.savings||0;
    if(s.credit===undefined) s.credit=c.creditCfg.start;
    if(s.allowance===undefined) s.allowance=0;
    if(s.royalty===undefined) s.royalty=0;
    if(!s.saveMonths) s.saveMonths=[];
    if(!s.awards) s.awards={};
    if(s.payStreak===undefined) s.payStreak=0;
    if(!c.ins.members[s.id] || !c.ins.plans.find(p=>p.id===c.ins.members[s.id])) c.ins.members[s.id]=bp.id;
  });
  return c;
}
function seedClass(code,name,pin){
  const c = blankClass(code,name,pin);
  c.certs = [
    {id:uid(), emoji:'💰', name:'금융 자격증', desc:'돈, 저축, 세금에 대해 공부했어요.'},
    {id:uid(), emoji:'✍️', name:'기자 자격증', desc:'바르고 정확한 글을 쓸 수 있어요.'},
    {id:uid(), emoji:'🌿', name:'환경 지킴이 자격증', desc:'교실을 깨끗하게 지키는 방법을 알아요.'}
  ];
  const [fin, rep, env] = c.certs.map(x=>x.id);
  c.jobs = [
    {id:uid(), emoji:'🏦', name:'은행원', salary:1200, taxRate:10, slots:2, certId:fin, special:'', desc:'친구들의 통장을 정리하고 저축을 도와요.'},
    {id:uid(), emoji:'📰', name:'기자', salary:1100, taxRate:10, slots:2, certId:rep, special:'reporter', desc:'우리 반 소식을 취재해서 뉴스 기사를 써요.'},
    {id:uid(), emoji:'🧹', name:'환경미화원', salary:1000, taxRate:8, slots:3, certId:env, special:'', desc:'교실을 깨끗하고 쾌적하게 정리해요.'},
    {id:uid(), emoji:'🛒', name:'마트 직원', salary:1000, taxRate:8, slots:2, certId:'', special:'', desc:'마트 물건을 정리하고 친구들에게 전달해요.'},
    {id:uid(), emoji:'🧾', name:'국세청 직원', salary:1100, taxRate:10, slots:1, certId:fin, special:'', desc:'세금 납부를 확인하고 친구들에게 알려요.'},
    {id:uid(), emoji:'📈', name:'증권사 직원', salary:1300, taxRate:12, slots:2, certId:fin, special:'broker', desc:'주식 가격을 정하고 주식 정보를 알려요.'},
    {id:uid(), emoji:'👮', name:'경찰', salary:1100, taxRate:10, slots:2, certId:'', special:'', desc:'우리 반 규칙을 잘 지키도록 도와요.'}
  ];
  c.products = [
    {id:uid(), emoji:'🍬', name:'사탕', price:100, stock:30},
    {id:uid(), emoji:'🍫', name:'초콜릿', price:200, stock:20},
    {id:uid(), emoji:'🍪', name:'쿠키', price:150, stock:20},
    {id:uid(), emoji:'✏️', name:'예쁜 연필', price:300, stock:15},
    {id:uid(), emoji:'🎫', name:'자리 바꾸기 쿠폰', price:800, stock:5},
    {id:uid(), emoji:'📚', name:'숙제 하루 면제권', price:1500, stock:3}
  ];
  c.law = {
    preamble:'우리 반은 서로 존중하고 배려하며, 모두가 행복하게 배우는 교실을 만들기 위하여 이 헌법을 만든다.',
    articles:[
      {id:uid(), head:'국가', body:'우리 반은 민주 공화국이며, 모든 권리는 우리 반 학생들로부터 나온다.'},
      {id:uid(), head:'평등', body:'모든 학생은 법 앞에 평등하며, 누구도 차별받지 않는다.'},
      {id:uid(), head:'근로', body:'모든 학생은 일할 권리와 의무를 가지며, 일한 만큼 정당한 월급을 받는다.'},
      {id:uid(), head:'납세', body:'모든 학생은 정해진 세금을 낼 의무를 가진다. 세금은 우리 반 모두를 위해 쓰인다.'},
      {id:uid(), head:'재산', body:'모든 학생의 재산은 보호받는다. 다른 사람의 물건이나 돈을 함부로 가져갈 수 없다.'}
    ]
  };
  c.notices = [{id:uid(), title:'우리반 경제나라에 오신 것을 환영해요! 🎉', body:'직업을 갖고, 월급을 받고, 세금도 내면서 진짜 경제를 배워 봐요.\n궁금한 것은 언제든 선생님께 물어보세요.', date:now()}];
  c.taxNotices = [{id:uid(), title:'세금은 왜 낼까요? 🤔', body:'세금은 우리 반 모두를 위한 돈이에요.\n모인 세금은 학급 행사, 간식 파티, 공공 물품을 사는 데 쓰여요.\n월급을 받을 때 직업별 세율만큼 자동으로 세금이 빠져나가요.', date:now()}];
  fillDefaults(c);
  return c;
}
function newStudent(n,name,pin,credit,cls){
  const c=cls||C()||null;
  const s={id:uid(), num:n, name, pin:pin||'1004', jobId:'', balance:0, savings:0,
    credit: credit!==undefined ? credit : (c ? c.creditCfg.start : 700),
    certs:[], prefs:{}, allowance:0, royalty:0, saveMonths:[], awards:{}, payStreak:0};
  if(c){ const bp=basicPlan(c); if(bp) c.ins.members[s.id]=bp.id; }
  return s;
}
function makeDemo(){
  const c = seedClass('SUNNY','햇살반','0000');
  [['김하늘','1111'],['이바다','2222'],['박구름','3333'],['최별','4444'],['정나무','5555'],['한솔','6666']].forEach(([n,p],i)=>{
    const s = newStudent(i+1,n,p,undefined,c);
    s.balance = 3000;
    const j = c.jobs[i];
    if(j && i<5){ s.jobId=j.id; if(j.certId) s.certs.push(j.certId); }
    c.tx.push({id:uid(), sid:s.id, amount:3000, type:'입금', memo:'시작 자금', date:now(), bal:3000});
    c.students.push(s);
  });
  fillDefaults(c);
  DB.classes[c.code] = c;
  save();
}

/* ---------- 세션 ---------- */
const freshS = () => ({screen:'code', code:'', role:'', sid:'', pick:'', pin:'', app:'', tab:'', preview:false, broker:false});
let S = freshS();
function saveSess(){ try{ sessionStorage.setItem('ce_session', JSON.stringify(S)); }catch(e){} }

const C = () => DB.classes[S.code];
const T = () => S.role==='teacher' && !S.preview;          // 선생님 모드
const PREVIEW = {id:'__preview', num:0, name:'미리보기 학생', pin:'', jobId:'', balance:5000, savings:1000, credit:700, certs:[], prefs:{}};
function me(){
  const c=C(); if(!c) return null;
  if(S.role==='student') return c.students.find(s=>s.id===S.sid) || null;
  if(S.preview) return PREVIEW;
  return null;
}
function guard(){ if(S.preview){ toast('👀 미리보기 중에는 실행되지 않아요'); return true; } return false; }
const stuById = id => (C().students.find(s=>s.id===id));
const stuName = id => { const s=stuById(id); return s ? s.name : '(삭제된 학생)'; };
const jobById = id => C().jobs.find(j=>j.id===id);
const jobOf = s => s && s.jobId ? jobById(s.jobId) : null;
const certById = id => C().certs.find(x=>x.id===id);
const sorted = () => [...C().students].sort((a,b)=>a.num-b.num);
function creditMax(){ const c=C(); return (c && c.creditCfg.max) || 1000; }
function grade(s){ const step=creditMax()/10; return Math.min(10, Math.max(1, 10 - Math.floor(((s.credit||0)-1)/step))); }
function addCredit(s, n, reason){
  if(!s || !n || s.id==='__preview') return;
  const c=C(), before=s.credit||0;
  s.credit = Math.max(0, Math.min(creditMax(), before+n));
  const d=s.credit-before; if(!d) return;
  c.creditLog.unshift({id:uid(), sid:s.id, delta:d, reason:reason||'', date:now()});
  if(c.creditLog.length>3000) c.creditLog.length=3000;
}
function rule(id){ const r=C().creditRules.find(x=>x.id===id); return r && r.on ? r : null; }
function ruleFire(s, id, key){
  const r=rule(id); if(!r) return;
  if(key){ s.awards=s.awards||{}; if(s.awards[id]===key) return; s.awards[id]=key; }
  addCredit(s, r.pts, '자동: '+RULE_TEXT[id](r));
}
const monthKey = (d=new Date()) => `${d.getFullYear()}-${pad(d.getMonth()+1)}`;
function prevMonth(k){ let [y,m]=k.split('-').map(Number); m--; if(m<1){m=12;y--;} return `${y}-${pad(m)}`; }
function saveStreakCheck(s){
  const r=rule('save_streak'); if(!r || r.n<1) return;
  const k=monthKey(); s.saveMonths=s.saveMonths||[];
  if(!s.saveMonths.includes(k)){ s.saveMonths.push(k); if(s.saveMonths.length>36) s.saveMonths.shift(); }
  let n=0, cur=k; while(s.saveMonths.includes(cur)){ n++; cur=prevMonth(cur); }
  if(n>0 && n % r.n===0) ruleFire(s,'save_streak',k);
}
function creditSweep(){            // 세금 체납 같은 '시간이 지나야' 알 수 있는 규칙 검사
  const c=C(); if(!c) return false; let changed=false;
  const r=rule('tax_late');
  if(r){ const lim=Date.now()-r.n*864e5;
    c.taxBills.forEach(b=>{ if(!b.paid && !b.late && new Date(b.date).getTime()<lim){ const s=stuById(b.sid); if(s){ b.late=true; addCredit(s, r.pts, `자동: ${RULE_TEXT.tax_late(r)} (${b.title})`); changed=true; } } }); }
  if(seatSweep()) changed=true;
  return changed;
}
function addTx(s, amount, type, memo){
  const c=C();
  const wasPlus = s.balance>=0;
  s.balance += amount;
  if(wasPlus && s.balance<0) ruleFire(s,'minus_bal');
  c.tx.unshift({id:uid(), sid:s.id, amount, type, memo:memo||'', date:now(), bal:s.balance});
  if(c.tx.length>6000) c.tx.length=6000;
}
function budgetAdd(amount, memo){ const c=C(); c.budget += amount; c.budgetLog.unshift({id:uid(), amount, memo, date:now()}); if(c.budgetLog.length>1000) c.budgetLog.length=1000; }
function stockValue(sid){ const c=C(), h=c.holdings[sid]||{}; return c.stocks.reduce((a,st)=>a+((h[st.id]&&h[st.id].qty)||0)*st.price,0); }

/* ---------- 환경 설정 ---------- */
const THEMES = [
  {k:'peach', n:'복숭아', c:'#FFAA8F'}, {k:'mint', n:'민트', c:'#86D2B0'}, {k:'lavender', n:'라벤더', c:'#B9A9F2'},
  {k:'sky', n:'하늘', c:'#8FC6F0'}, {k:'lemon', n:'레몬', c:'#F7C96B'}, {k:'berry', n:'딸기', c:'#F5A3BC'}
];
function prefs(){
  const c=C(); if(!c || !S.role || (S.screen!=='home' && S.screen!=='app')) return {};
  if(S.role==='teacher') return c.teacherPrefs || (c.teacherPrefs={});
  const s=c.students.find(x=>x.id===S.sid); return s ? (s.prefs||(s.prefs={})) : {};
}
function applyPrefs(){
  const p = prefs();
  document.body.dataset.theme = p.theme || 'peach';
  document.documentElement.style.fontSize = (p.font||16) + 'px';
  $('dim').style.opacity = ((100-(p.bright||100))/100).toFixed(2);
}
function setPref(k,v,rerender){ const p=prefs(); p[k]=v; save(); applyPrefs(); if(rerender) render(); }

/* ---------- 앱 목록 ---------- */
function allApps(){
  const c=C(), n=c.names;
  return [
    {k:'bank', e:'🏦', t:n.bank+'은행', col:'#FFDCCD', fn:appBank, rename:'bank'},
    {k:'mart', e:'🛒', t:n.mart+'마트', col:'#FFEDB0', fn:appMart, rename:'mart'},
    {k:'jobs', e:'💼', t:'한국 직업·자격증 협회', col:'#E1DBF7', fn:appJobs},
    {k:'tax', e:'🧾', t:'국세청', col:'#C9EEDC', fn:appTax},
    {k:'law', e:'⚖️', t:'헌법재판소', col:'#D6ECFB', fn:appLaw},
    {k:'news', e:'📰', t:n.news+'뉴스', col:'#FFDCE3', fn:appNews, rename:'news'},
    {k:'stock', e:'📈', t:n.securities+'증권', col:'#E3F5CC', fn:appStock, feat:'stock', rename:'securities'},
    {k:'realty', e:'🏠', t:'국토교통부', col:'#FFE3C2', fn:appRealty, feat:'realty'},
    {k:'credit', e:'💳', t:'신용평가원', col:'#FCE7C8', fn:appCredit},
    {k:'ins', e:'🏥', t:'국민건강보험', col:'#D3F0EF', fn:appIns},
    {k:'students', e:'👥', t:'학생 관리', col:'#F4E2FB', fn:appStudents, tOnly:1},
    {k:'stats', e:'📊', t:'정부 예산·통계', col:'#FDE6D3', fn:appStats, tOnly:1},
    {k:'features', e:'➕', t:'기능 추가하기', col:'#E6F0D8', fn:appFeatures, tOnly:1},
    {k:'settings', e:'⚙️', t:'설정', col:'#EEE7E2', fn:appSettings}
  ];
}
function visibleApps(){ const c=C(); return allApps().filter(a=>(!a.feat||c.features[a.feat]) && (!a.tOnly||T())); }
function badges(){
  const c=C(), b={};
  if(T()){
    b.jobs = c.apps.filter(a=>a.status==='pending').length;
    b.mart = c.orders.filter(o=>!o.done).length;
    b.realty = c.seatReqs.filter(r=>r.status==='pending' && r.teacherOk===null).length;
    b.ins = c.ins.claims.filter(r=>r.status==='pending').length;
  } else if(S.role==='student'){
    b.tax = c.taxBills.filter(x=>x.sid===S.sid && !x.paid).length;
    if(c.features.realty) b.realty = c.seatReqs.filter(r=>r.status==='pending' && r.owner===S.sid && r.ownerOk===null).length;
  }
  return b;
}
function toTop(){ const s=$('scroller'); if(s) s.scrollTop=0; }
function openApp(k,tab){ S.screen='app'; S.app=k; S.tab=tab||''; render(); toTop(); }
function goHome(){ S.screen='home'; S.app=''; S.tab=''; render(); toTop(); }
function setTab(t){ S.tab=t; render(); }
function togglePreview(){ S.preview=!S.preview; S.tab=''; render(); toast(S.preview?'👀 학생 화면을 보여주고 있어요':'👩‍🏫 선생님 화면으로 돌아왔어요'); }
function tabs(list){
  if(!list.find(t=>t[0]===S.tab)) S.tab=list[0][0];
  return `<div class="tabs">${list.map(([k,l])=>`<button class="tab ${S.tab===k?'on':''}" onclick="setTab('${k}')">${l}</button>`).join('')}</div>`;
}
function renameApp(key){
  const c=C(), suf={bank:'은행',mart:'마트',news:'뉴스',securities:'증권'}[key];
  modal('✏️ 이름 바꾸기', `<label class="f">이름 (뒤에 '${suf}'가 붙어요)</label><div class="row"><input id="rnIn" class="grow" value="${esc(c.names[key])}" maxlength="10"><span class="jua">${suf}</span></div>`,
    `<button class="btn" onclick="doRename('${key}')">바꾸기</button>`);
}
function doRename(key){ const v=val('rnIn'); if(!v) return toast('이름을 입력하세요'); C().names[key]=v; save(); closeModal(); render(); toast('이름을 바꿨어요 ✨'); }

/* =========================================================
   화면 그리기
   ========================================================= */
function render(){
  if(SYNC.on && !SYNC.got && S.screen!=='code' && !C()){
    $('app').innerHTML=`<div class="center-screen"><div class="card login-card"><div class="logo">☁️</div><h1>연결하는 중…</h1><p class="sub">잠시만 기다려 주세요</p></div></div>`; return;
  }
  if(S.screen!=='code' && !C()) S=freshS();
  if((S.screen==='home'||S.screen==='app') && S.role==='student' && !me()) S=freshS();
  if((S.screen==='home'||S.screen==='app') && C() && S.role==='teacher' && !S.preview && (!SYNC.on || SYNC.ready)){ try{ if(creditSweep()) save(); }catch(e){ console.error(e); } }
  applyPrefs();
  let h='';
  switch(S.screen){
    case 'role': h=vRole(); break;
    case 'pick': h=vPick(); break;
    case 'pin':  h=vPin(); break;
    case 'home': h=vHome(); break;
    case 'app':  h=vApp(); break;
    default:     h=vCode();
  }
  $('app').innerHTML=h;
  saveSess();
}

/* ---------- 로그인 ---------- */
function vCode(){
  return `<div class="center-screen"><div class="card login-card">
    <div class="logo">🏫</div>
    <h1>우리반 경제나라</h1>
    <p class="sub">선생님께 받은 학급 코드를 입력하세요</p>
    <input id="codeIn" class="big-input" placeholder="학급 코드" maxlength="12" autocomplete="off" onkeydown="if(event.key==='Enter')enterCode()">
    <button class="btn wide" onclick="enterCode()">입장하기 ➜</button>
    ${DB.classes.SUNNY?`<div class="hint">🌟 체험용 학급 코드 <b>SUNNY</b><br>선생님 비밀번호 0000 · 학생(김하늘) 1111</div>`:''}
    <button class="link" onclick="openNewClass()">👩‍🏫 선생님: 새 학급 만들기</button><br>
    <button class="link" onclick="restoreNewForm()">💾 백업 파일로 학급 되살리기</button>
  </div></div>`;
}
function restoreNewForm(){
  modal('💾 백업으로 학급 되살리기', `<p class="sub">설정 → [백업 파일 받기]로 저장해 둔 파일을 고르세요.</p>
    <input type="file" accept=".json,application/json" onchange="readBackup(this)">
    <label class="f">또는 백업 글자 붙여넣기</label><textarea id="rsT" rows="6"></textarea>`,
    `<button class="btn" onclick="restoreNew()">되살리기</button>`);
}
function restoreNew(){
  let d; try{ d=JSON.parse(val('rsT')); }catch(e){ return toast('백업 형식이 올바르지 않아요'); }
  if(!d || !Array.isArray(d.students) || !d.teacherPin || !d.code) return toast('경제나라 백업이 아니에요');
  const go=()=>{ DB.classes[d.code]=fillDefaults(d); save(); closeModal(); S=freshS(); S.code=d.code; S.screen='role'; render(); toast('학급을 되살렸어요! 🎉'); };
  if(DB.classes[d.code]){ closeModal(); ask(`이 기기에 이미 <b>${esc(d.code)}</b> 학급이 있어요. 백업으로 덮어쓸까요?`, go, '덮어쓰기'); }
  else go();
}
function enterCode(){
  const code=val('codeIn').toUpperCase();
  if(!code) return toast('학급 코드를 입력하세요');
  if(!DB.classes[code]) return toast(SYNC.on && !SYNC.ready ? '☁️ 아직 연결 중이에요. 잠시 후 다시 눌러 주세요' : '학급 코드를 찾을 수 없어요 😢');
  S.code=code; S.screen='role'; render();
}
function randCode(){ const a='ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; let s=''; for(let i=0;i<6;i++) s+=a[Math.floor(Math.random()*a.length)]; return DB.classes[s]?randCode():s; }
function openNewClass(){
  modal('🏫 새 학급 만들기', `
    <label class="f">학급 이름</label><input id="ncName" placeholder="예: 5학년 3반">
    <label class="f">학급 코드 (영어·숫자)</label><div class="row"><input id="ncCode" class="grow" value="${randCode()}" maxlength="12" style="text-transform:uppercase"><button class="btn sm sub" onclick="$('ncCode').value=randCode()">🎲 새로</button></div>
    <label class="f">선생님 비밀번호 (숫자 4자리)</label><input id="ncPin" type="password" inputmode="numeric" maxlength="4">
    <p class="sub">기본 직업·자격증·마트 상품·헌법이 미리 들어가 있어요. 언제든 바꿀 수 있어요.</p>`,
    `<button class="btn" onclick="createClass()">만들기</button>`);
}
function createClass(){
  const name=val('ncName'), code=val('ncCode').toUpperCase().replace(/[^A-Z0-9]/g,''), pin=val('ncPin');
  if(!name) return toast('학급 이름을 입력하세요');
  if(code.length<3) return toast('학급 코드는 3글자 이상이에요');
  if(DB.classes[code]) return toast('이미 있는 학급 코드예요');
  if(!/^\d{4}$/.test(pin)) return toast('비밀번호는 숫자 4자리예요');
  DB.classes[code]=seedClass(code,name,pin); save(); closeModal();
  S.code=code; S.screen='role'; render(); toast('학급이 만들어졌어요! 🎉');
}
function vRole(){
  const c=C();
  return `<div class="center-screen"><div class="card login-card">
    <div class="logo">🌷</div><h1>${esc(c.name)}</h1><p class="sub">누구인가요?</p>
    <div class="role-btns">
      <button class="role-btn" style="background:var(--yel)" onclick="S.role='student';S.screen='pick';render()"><span>🧒</span>학생</button>
      <button class="role-btn" style="background:var(--mint)" onclick="S.role='teacher';S.pin='';S.screen='pin';render()"><span>👩‍🏫</span>선생님</button>
    </div>
    <button class="link" onclick="S=freshS();render()">← 학급 코드 다시 입력</button>
  </div></div>`;
}
function vPick(){
  const list=sorted();
  return `<div class="center-screen"><div class="card login-card" style="max-width:560px">
    <div class="logo">🧒</div><h1>내 이름을 눌러요</h1>
    ${list.length?`<div class="pick-grid">${list.map(s=>`<button class="pick-btn" onclick="S.pick='${s.id}';S.pin='';S.screen='pin';render()"><small>${s.num}번</small>${esc(s.name)}</button>`).join('')}</div>`
      :`<p class="empty">아직 학생 계정이 없어요.<br>선생님께 계정을 만들어 달라고 해요!</p>`}
    <button class="link" onclick="S.screen='role';render()">← 뒤로</button>
  </div></div>`;
}
function vPin(){
  const who = S.role==='teacher' ? '👩‍🏫 선생님' : '🧒 ' + esc(stuName(S.pick));
  const keys=['1','2','3','4','5','6','7','8','9','←','0','✓'];
  return `<div class="center-screen"><div class="card login-card">
    <h1>${who}</h1><p class="sub">비밀번호 네 자리를 눌러요</p>
    <div class="dots" id="pinDots">${[0,1,2,3].map(i=>`<div class="dot ${i<S.pin.length?'on':''}"></div>`).join('')}</div>
    <div class="keypad">${keys.map(k=>`<button class="key" onclick="pinKey('${k}')">${k}</button>`).join('')}</div>
    <button class="link" onclick="S.pin='';S.screen=S.role==='teacher'?'role':'pick';render()">← 뒤로</button>
  </div></div>`;
}
function pinKey(k){
  if(k==='←') S.pin=S.pin.slice(0,-1);
  else if(k==='✓') return checkPin();
  else if(S.pin.length<4){ S.pin+=k; if(S.pin.length===4){ render(); setTimeout(checkPin,160); return; } }
  render();
}
function checkPin(){
  const c=C(); let ok=false;
  if(S.role==='teacher') ok = S.pin===c.teacherPin;
  else { const s=stuById(S.pick); ok = !!s && s.pin===S.pin; if(ok) S.sid=s.id; }
  if(ok){ S.pin=''; S.screen='home'; S.preview=false; S.broker=false; render(); toast('반가워요! 🎉'); }
  else { S.pin=''; render(); const d=$('pinDots'); if(d) d.classList.add('shake'); toast('비밀번호가 틀렸어요 😢'); }
}
function logout(){ const code=S.code; S=freshS(); S.code=code; S.screen='role'; render(); toast('로그아웃했어요 👋'); }

/* ---------- 상단바 / 홈 ---------- */
function topbar(title, back){
  const tbtn = S.role==='teacher' ? `<button class="btn sm ${S.preview?'':'sub'}" onclick="togglePreview()">${S.preview?'👩‍🏫 선생님 화면':'👀 학생 화면 보기'}</button>` : '';
  return `<div class="topbar">${back?`<button class="icon-btn" onclick="goHome()" title="홈">←</button>`:`<div class="brand">🏫</div>`}
    <div class="tb-title clip">${title}</div>${tbtn}</div>
    ${S.preview?`<div class="preview-banner">👀 지금은 학생들이 보는 화면이에요 (미리보기)</div>`:''}`;
}
function vHome(){
  const c=C(), s=me(), b=badges();
  let hero;
  if(s){
    const j=jobOf(s);
    hero=`<div class="card hero"><div class="hello">안녕하세요, <b>${esc(s.name)}</b>님! 👋</div>
      <div class="sub">내 통장 잔액</div><div class="money-big">${won(s.balance)}</div>
      <div><span class="chip">${j?j.emoji+' '+esc(j.name):'🙂 아직 직업 없음'}</span><span class="chip mint">🐷 예금 ${won(s.savings)}</span><span class="chip yel">💳 신용 ${grade(s)}등급</span></div></div>`;
  } else {
    const pend=(b.jobs||0)+(b.realty||0)+(b.ins||0)+(b.mart||0);
    hero=`<div class="card hero"><div class="hello">선생님, 오늘도 좋은 하루 보내세요! 🌷</div>
      <div class="stats3"><div class="stat"><div class="n">${c.students.length}명</div><div class="sub">학생</div></div>
      <div class="stat"><div class="n">${won(c.budget)}</div><div class="sub">정부 예산</div></div>
      <div class="stat"><div class="n">${pend}건</div><div class="sub">처리할 일</div></div></div>
      <div class="sub mt">학급 코드 <b>${esc(c.code)}</b> · 학생들에게 알려주세요</div>${storageNote()}
      ${(!c.lastBackup || Date.now()-new Date(c.lastBackup).getTime() > 2*864e5) ? `<div class="alert">💾 ${c.lastBackup?`마지막 백업이 ${Math.floor((Date.now()-new Date(c.lastBackup).getTime())/864e5)}일 전이에요.`:'아직 백업한 적이 없어요.'} 데이터를 잃지 않게 백업해 두세요! <button class="btn sm" onclick="backupFile()">지금 백업</button></div>` : ''}</div>`;
  }
  const n=c.notices[0];
  const notice = n ? `<div class="card notice" onclick="openApp('news','notice')"><b>📢 ${esc(n.title)}</b><div class="sub clip">${esc(n.body)}</div></div>` : '';
  const tiles = visibleApps().map(a=>`<button class="tile" style="background:${a.col}" onclick="openApp('${a.k}')">${b[a.k]?`<span class="badge">${b[a.k]}</span>`:''}<span class="ic">${a.e}</span><span>${esc(a.t)}</span>${a.tOnly?'<span class="tag">선생님 전용</span>':''}</button>`).join('');
  return topbar(esc(c.name)+' 경제나라', false) + hero + notice + `<div class="app-grid">${tiles}</div>`;
}
function vApp(){
  const a = allApps().find(x=>x.k===S.app);
  if(!a){ S.screen='home'; return vHome(); }
  let body;
  if(a.tOnly && !T()) body=`<div class="card empty">👀 이 메뉴는 선생님에게만 보여요.</div>`;
  else if(a.feat && !C().features[a.feat]) body=`<div class="card empty">아직 열리지 않은 기능이에요.</div>`;
  else body=a.fn();
  const rn = a.rename && T() ? `<div class="row end" style="margin:-4px 0 12px"><button class="btn sm sub" onclick="renameApp('${a.rename}')">✏️ 이름 바꾸기</button></div>` : '';
  return topbar(a.e+' '+esc(a.t), true) + rn + body;
}

/* =========================================================
   🏦 은행
   ========================================================= */
function appBank(){
  if(T()) return tabs([['pay','💸 월급 지급'],['acc','👛 학생 계좌'],['int','🐷 예금 이자']]) + ({pay:bankPay, acc:bankAcc, int:bankInt}[S.tab])();
  return tabs([['acc','📒 내 통장'],['slip','🧾 월급 명세서'],['save','🐷 저축·예금']]) + ({acc:bankMine, slip:bankSlip, save:bankSave}[S.tab])(me());
}
function txList(list, showName){
  if(!list.length) return `<p class="empty">아직 거래 내역이 없어요</p>`;
  return `<div class="tbl-wrap"><table class="t"><tr><th>날짜</th>${showName?'<th>이름</th>':''}<th>내용</th><th class="r">금액</th><th class="r">잔액</th></tr>
  ${list.map(t=>`<tr><td class="nowrap sub">${fdate(t.date)}</td>${showName?`<td>${esc(stuName(t.sid))}</td>`:''}<td><span class="chip" style="margin:0 6px 0 0">${esc(t.type)}</span>${esc(t.memo)}</td>
  <td class="r nowrap ${t.amount>=0?'plus':'minus'}">${signed(t.amount)}</td><td class="r nowrap sub">${won(t.bal)}</td></tr>`).join('')}</table></div>`;
}
function rentOf(sid){
  const c=C(); if(!c.features.realty) return 0;
  return c.seatReqs.filter(r=>r.sid===sid && r.status==='active').reduce((a,r)=>a+(r.rent||0),0);
}
function insPlanOf(sid){ const c=C(); return c.ins.plans.find(p=>p.id===c.ins.members[sid]) || basicPlan(c); }
function payCalc(s, royalty, allowance){
  const c=C(), j=jobOf(s);
  const salary=j?j.salary:0, rate=j?j.taxRate:0;
  royalty=Math.max(0, royalty||0); allowance=Math.max(0, allowance||0);
  const income=salary+royalty+allowance;
  const tax=Math.round(income*rate/100), rent=rentOf(s.id), electric=c.fees.electric||0, meal=c.fees.meal||0;
  const plan=insPlanOf(s.id), ins=plan?plan.premium:0;
  return {job:j?j.name:'무직', salary, royalty, allowance, rate, tax, rent, electric, ins, meal, net:income-tax-rent-electric-ins-meal};
}
const PAY_ROWS = [['salary','월급',1],['royalty','저작권료',1],['allowance','국회의원 수당',1],['tax','세금',-1],['rent','자리임대료',-1],['electric','전기요금',-1],['ins','건강보험료',-1],['meal','급식비',-1]];
function payKv(p){
  return PAY_ROWS.map(([k,l,sg])=>`<div class="kv"><span>${l}${k==='tax'?` (${p.rate}%)`:''}</span><b class="${sg<0&&p[k]?'minus':''}">${sg<0&&p[k]?'−':''}${won(p[k]||0)}</b></div>`).join('')
    + `<div class="kv"><span><b>실수령</b></span><b class="${p.net>=0?'plus':'minus'} big">${won(p.net)}</b></div>`;
}
function bankMine(s){
  const c=C(), j=jobOf(s), p=payCalc(s, 0, s.allowance||0);
  const unpaid=c.taxBills.filter(b=>b.sid===s.id && !b.paid), uSum=unpaid.reduce((a,b)=>a+b.amount,0);
  return `<div class="two">
    <div class="card hero"><div class="sub">현재 잔액</div><div class="money-big">${won(s.balance)}</div>
      <div class="sub">예금 통장 ${won(s.savings)} · 신용 ${grade(s)}등급</div>
      ${unpaid.length?`<div class="alert">🧾 내지 않은 세금 ${unpaid.length}건 (${won(uSum)}) <button class="btn sm" onclick="openApp('tax','bill')">납부하기</button></div>`:''}</div>
    <div class="card"><h3>💼 다음 월급 예상 (${j?esc(j.emoji+' '+j.name):'직업 없음'})</h3>
      ${payKv(p)}<p class="sub">저작권료는 선생님이 월급날에 정해요.</p>
    </div></div>
    <div class="card mt"><h3>📜 입출금 내역</h3>${txList(c.tx.filter(t=>t.sid===s.id).slice(0,80))}</div>`;
}
function bankSlip(s){
  const list=C().payslips.filter(p=>p.sid===s.id);
  if(!list.length) return `<div class="card empty">아직 받은 월급이 없어요 🌱</div>`;
  return `<div class="grid2">${list.slice(0,40).map(p=>`<div class="card"><div class="row between"><b class="jua">🧾 ${esc(p.memo)}</b><span class="sub">${fday(p.date)}</span></div>
    <div class="kv"><span>직업</span><b>${esc(p.job)}</b></div>${payKv(Object.assign({salary:p.gross, royalty:0, allowance:0, rent:0, electric:0, ins:0, meal:0}, p))}</div>`).join('')}</div>`;
}
function bankSave(s){
  const c=C(), r=c.creditRules.find(x=>x.id==='save_streak');
  return `<div class="two"><div class="card hero"><div class="sub">🐷 내 예금 통장</div><div class="money-big">${won(s.savings)}</div>
    <p class="sub">예금에 넣어 두면 선생님이 이자를 줄 때마다 <b>${c.savingsRate}%</b>씩 늘어나요!${r&&r.on?`<br>💳 ${r.n}달 연속 적금하면 신용 점수 <b>+${r.pts}점</b>!`:''}</p></div>
    <div class="card"><h3>저금하기 · 찾기</h3><div class="sub">지금 통장 잔액: ${won(s.balance)}</div>
      <label class="f">금액</label><input id="saveAmt" type="number" min="1" placeholder="얼마를 옮길까요?">
      <div class="row mt"><button class="btn mint grow" onclick="doSave(1)">🐷 예금에 넣기</button><button class="btn sub grow" onclick="doSave(-1)">💰 예금에서 찾기</button></div></div></div>`;
}
function doSave(dir){
  if(guard()) return;
  const s=me(), a=num(val('saveAmt'));
  if(a<=0) return toast('금액을 입력하세요');
  if(dir>0){ if(s.balance<a) return toast('통장 잔액이 부족해요 😢'); addTx(s,-a,'저축','예금 통장으로 옮김'); s.savings+=a; saveStreakCheck(s); toast('예금에 넣었어요 🐷'); }
  else { if(s.savings<a) return toast('예금이 부족해요'); s.savings-=a; addTx(s,a,'예금 인출','예금 통장에서 찾음'); ruleFire(s,'save_break'); toast('예금에서 찾았어요 💰'); }
  save(); render();
}
function bankPay(){
  const c=C(), list=sorted(), bp=basicPlan(c);
  let initTot=0;
  const rows=list.map(s=>{ const j=jobOf(s), p=payCalc(s, s.royalty||0, s.allowance||0); if(j) initTot+=p.net;
    return `<tr><td><input type="checkbox" id="pay_${s.id}" ${j?'checked':''} onchange="payTotals()"></td><td>${s.num}</td><td class="nowrap">${esc(s.name)}</td><td class="nowrap">${j?esc(j.emoji+' '+j.name):'<span class="sub">무직</span>'}</td>
      <td class="r">${won(p.salary)}</td>
      <td><input class="sm num" id="roy_${s.id}" type="number" min="0" value="${p.royalty}" oninput="payRow('${s.id}')"></td>
      <td><input class="sm num" id="alw_${s.id}" type="number" min="0" value="${p.allowance}" oninput="payRow('${s.id}')"></td>
      <td class="r nowrap minus" id="ptax_${s.id}">${p.rate}% (${won(p.tax)})</td><td class="r minus">${won(p.rent)}</td><td class="r minus">${won(p.electric)}</td><td class="r minus">${won(p.ins)}</td><td class="r minus">${won(p.meal)}</td>
      <td class="r jua" id="pnet_${s.id}"><span class="${p.net>=0?'plus':'minus'}">${won(p.net)}</span></td></tr>`; }).join('');
  const d=new Date();
  return `<div class="card"><h3>🧾 매달 빠지는 돈 (모든 학생 같음)</h3>
    <div class="row"><div class="grow"><label class="f">⚡ 전기요금</label><input id="feeE" type="number" min="0" value="${c.fees.electric}"></div>
    <div class="grow"><label class="f">🍚 급식비</label><input id="feeM" type="number" min="0" value="${c.fees.meal}"></div>
    <div class="grow"><label class="f">🏥 기본 건강보험료</label><input id="feeI" type="number" min="0" value="${bp?bp.premium:0}"></div>
    <button class="btn sub" style="align-self:flex-end" onclick="saveFees()">저장</button></div>
    <p class="sub">세금은 (월급+저작권료+국회의원 수당) × 직업별 세율이에요. 자리임대료는 국토교통부에서 자리를 빌린 학생만 내요.</p></div>
  <div class="card"><h3>💸 월급 지급하기</h3><p class="sub">체크된 학생에게 월급을 주고 세금·공과금을 떼어요. 저작권료는 이번 한 번만, 국회의원 수당은 다음에도 그대로 기억해요.</p>
    <div class="row"><input id="payMemo" class="grow" value="${d.getMonth()+1}월 월급"><button class="btn" onclick="paySalary()">💸 월급 지급</button></div>
    <div class="tbl-wrap mt"><table class="t"><tr><th><input type="checkbox" onchange="document.querySelectorAll('[id^=pay_]').forEach(x=>x.checked=this.checked);payTotals()"></th><th>번호</th><th>이름</th><th>직업</th><th class="r">월급</th><th>저작권료</th><th>국회의원 수당</th><th class="r">세금(%)</th><th class="r">자리임대료</th><th class="r">전기요금</th><th class="r">건강보험료</th><th class="r">급식비</th><th class="r">실수령</th></tr>${rows||'<tr><td colspan="13" class="empty">학생이 없어요</td></tr>'}
    <tr><td colspan="12" class="jua">체크된 학생 실수령 합계</td><td class="r jua" id="payTot">${won(initTot)}</td></tr></table></div></div>
    <div class="card"><h3>📜 최근 월급 지급 기록</h3>${c.payslips.length?`<div class="tbl-wrap"><table class="t"><tr><th>날짜</th><th>이름</th><th>내용</th><th class="r">실수령</th></tr>${c.payslips.slice(0,30).map(p=>`<tr><td class="sub">${fdate(p.date)}</td><td>${esc(stuName(p.sid))}</td><td>${esc(p.memo)}</td><td class="r">${won(p.net)}</td></tr>`).join('')}</table></div>`:'<p class="empty">아직 기록이 없어요</p>'}</div>`;
}
function payInputs(sid){ return [num(val('roy_'+sid)), num(val('alw_'+sid))]; }
function payRow(sid){
  const s=stuById(sid); if(!s) return; const [r,a]=payInputs(sid), p=payCalc(s,r,a);
  $('ptax_'+sid).textContent=`${p.rate}% (${won(p.tax)})`;
  $('pnet_'+sid).innerHTML=`<span class="${p.net>=0?'plus':'minus'}">${won(p.net)}</span>`;
  payTotals();
}
function payTotals(){
  const e=$('payTot'); if(!e) return; let t=0;
  C().students.forEach(s=>{ const cb=$('pay_'+s.id); if(cb&&cb.checked){ const [r,a]=payInputs(s.id); t+=payCalc(s,r,a).net; } });
  e.textContent=won(t);
}
function saveFees(){
  if(guard()) return;
  const c=C(), bp=basicPlan(c);
  c.fees.electric=Math.max(0,num(val('feeE'))); c.fees.meal=Math.max(0,num(val('feeM')));
  if(bp) bp.premium=Math.max(0,num(val('feeI')));
  save(); render(); toast('저장했어요 ✅');
}
function paySalary(){
  if(guard()) return;
  const c=C(), memo=val('payMemo')||'월급'; let cnt=0;
  const sum={tax:0, rent:0, electric:0, meal:0, ins:0};
  const picked=c.students.filter(s=>{ const cb=$('pay_'+s.id); return cb&&cb.checked; });
  if(!picked.length) return toast('월급을 받을 학생을 체크하세요');
  picked.forEach(s=>{
    const [roy,alw]=payInputs(s.id), p=payCalc(s,roy,alw);
    const income=p.salary+p.royalty+p.allowance, ded=income-p.net;
    if(income) addTx(s, income, '월급', `${memo} (${p.job}${p.royalty?` · 저작권료 ${p.royalty}`:''}${p.allowance?` · 수당 ${p.allowance}`:''})`);
    if(ded) addTx(s, -ded, '세금·공과금', [['세금',p.tax],['자리',p.rent],['전기',p.electric],['보험',p.ins],['급식',p.meal]].filter(x=>x[1]).map(x=>x[0]+' '+x[1]).join(' · '));
    c.payslips.unshift(Object.assign({id:uid(), sid:s.id, date:now(), memo, gross:income}, p));
    for(const k in sum) sum[k]+=p[k];
    s.allowance=p.allowance; s.royalty=0;
    if(jobOf(s)){ s.payStreak=(s.payStreak||0)+1; const r=rule('pay_streak'); if(r && r.n>0 && s.payStreak%r.n===0) ruleFire(s,'pay_streak','p'+s.payStreak); }
    else s.payStreak=0;
    cnt++;
  });
  if(c.payslips.length>3000) c.payslips.length=3000;
  if(sum.tax) budgetAdd(sum.tax, `소득세 (${memo})`);
  if(sum.rent) budgetAdd(sum.rent, `자리 임대료 (${memo})`);
  if(sum.electric) budgetAdd(sum.electric, `전기요금 (${memo})`);
  if(sum.meal) budgetAdd(sum.meal, `급식비 (${memo})`);
  if(sum.ins) c.ins.fund += sum.ins;
  save(); render(); toast(`${cnt}명에게 월급을 줬어요 💸`);
}
function bankAcc(){
  const c=C();
  return `<div class="card"><h3>👛 학생 계좌</h3><p class="sub">상금·벌금 등은 [입출금]으로 직접 반영할 수 있어요.</p><div class="tbl-wrap"><table class="t">
    <tr><th>번호</th><th>이름</th><th class="r">잔액</th><th class="r">예금</th><th>신용</th><th></th></tr>
    ${sorted().map(s=>`<tr><td>${s.num}</td><td>${esc(s.name)}</td><td class="r">${won(s.balance)}</td><td class="r">${won(s.savings)}</td><td>${grade(s)}등급</td>
    <td class="nowrap"><button class="btn sm" onclick="adjustModal('${s.id}')">입출금</button> <button class="btn sm sub" onclick="histModal('${s.id}')">내역</button></td></tr>`).join('')||'<tr><td colspan="6" class="empty">학생이 없어요</td></tr>'}
  </table></div></div>
  <div class="card"><h3>📜 전체 거래 내역</h3>${txList(c.tx.slice(0,60),true)}</div>`;
}
function adjustModal(sid){
  const s=stuById(sid);
  modal(`👛 ${esc(s.name)} 계좌`, `<div class="sub">현재 잔액 ${won(s.balance)}</div><label class="f">금액</label><input id="adjAmt" type="number" min="1">
    <label class="f">사유</label><input id="adjMemo" placeholder="예: 발표 상금, 규칙 위반 벌금">`,
    `<button class="btn mint" onclick="adjust('${sid}',1)">입금 +</button><button class="btn danger" onclick="adjust('${sid}',-1)">출금 −</button>`);
}
function adjust(sid,d){
  if(guard()) return;
  const s=stuById(sid), a=num(val('adjAmt'));
  if(a<=0) return toast('금액을 입력하세요');
  addTx(s, d*a, d>0?'입금':'출금', val('adjMemo')||'선생님 조정');
  save(); closeModal(); render(); toast('반영했어요 ✅');
}
function histModal(sid){ const s=stuById(sid); modal(`📜 ${esc(s.name)} 거래 내역`, txList(C().tx.filter(t=>t.sid===sid).slice(0,100)), ''); }
function bankInt(){
  const c=C(), tot=c.students.reduce((a,s)=>a+s.savings,0);
  return `<div class="two"><div class="card"><h3>🐷 예금 이자율</h3><label class="f">이자율 (%)</label>
    <div class="row"><input id="intRate" class="grow" type="number" min="0" value="${c.savingsRate}"><button class="btn sub" onclick="saveRate()">저장</button></div>
    <p class="sub">학생들의 예금 총액: <b>${won(tot)}</b><br>지금 이자를 주면 약 <b>${won(c.students.reduce((a,s)=>a+Math.round(s.savings*c.savingsRate/100),0))}</b>이 예금에 더해져요.</p>
    <button class="btn wide" onclick="payInterest()">🎁 이자 지급하기</button></div>
    <div class="card"><h3>📋 학생별 예금</h3>${sorted().map(s=>`<div class="kv"><span>${s.num}. ${esc(s.name)}</span><b>${won(s.savings)}</b></div>`).join('')||'<p class="empty">학생이 없어요</p>'}</div></div>`;
}
function saveRate(){ if(guard()) return; C().savingsRate=Math.max(0,num(val('intRate'))); save(); render(); toast('이자율을 저장했어요'); }
function payInterest(){
  if(guard()) return;
  const c=C(); let cnt=0;
  c.students.forEach(s=>{ const it=Math.round(s.savings*c.savingsRate/100); if(it>0){ s.savings+=it; c.tx.unshift({id:uid(),sid:s.id,amount:0,type:'예금 이자',memo:`예금 통장에 ${won(it)} 이자`,date:now(),bal:s.balance}); cnt++; } });
  save(); render(); toast(cnt?`${cnt}명에게 이자를 줬어요 🎁`:'이자를 받을 예금이 없어요');
}

/* =========================================================
   🛒 마트
   ========================================================= */
function appMart(){
  if(T()) return tabs([['prod','🍭 상품 관리'],['ord','📦 주문 확인']]) + (S.tab==='prod'?martManage():martOrders());
  return tabs([['shop','🛒 장보기'],['my','🧺 내 주문']]) + (S.tab==='shop'?martShop():martMy());
}
function martShop(){
  const c=C(), s=me();
  return `<div class="card hero row between"><div><div class="sub">내 잔액</div><div class="money-big">${won(s.balance)}</div></div><div class="sub">물건을 사면 선생님(마트 직원)께 받아가요 🎁</div></div>
  <div class="grid2">${c.products.map(p=>`<div class="card prod"><div class="emo">${esc(p.emoji)}</div><div class="jua big">${esc(p.name)}</div>
    <div class="price">${won(p.price)}</div><div class="sub">남은 수량 ${p.stock}개</div>
    ${p.stock>0?`<div class="stepper"><button onclick="step('q_${p.id}',-1)">−</button><input id="q_${p.id}" type="number" value="1" min="1"><button onclick="step('q_${p.id}',1)">+</button></div>
    <button class="btn" onclick="buy('${p.id}')">🛒 사기</button>`:`<button class="btn" disabled>품절</button>`}</div>`).join('')||'<div class="card empty">아직 상품이 없어요</div>'}</div>`;
}
function step(id,d){ const e=$(id); e.value=Math.max(1,num(e.value)+d); }
function buy(pid){
  if(guard()) return;
  const c=C(), p=c.products.find(x=>x.id===pid), s=me(), q=Math.max(1,num(val('q_'+pid)));
  if(!p) return;
  if(p.stock<q) return toast('남은 수량이 부족해요');
  const cost=p.price*q;
  if(s.balance<cost) return toast('잔액이 부족해요 😢');
  ask(`${esc(p.emoji)} <b>${esc(p.name)}</b> ${q}개를 <b>${won(cost)}</b>에 살까요?`, ()=>{
    p.stock-=q; addTx(s,-cost,'마트 구매',`${p.name} ×${q}`); budgetAdd(cost,`마트 판매 (${p.name})`);
    c.orders.unshift({id:uid(), sid:s.id, emoji:p.emoji, name:p.name, qty:q, total:cost, date:now(), done:false});
    save(); render(); toast('구매 완료! 선생님께 받아가세요 🎁');
  }, '살래요');
}
function martMy(){
  const list=C().orders.filter(o=>o.sid===S.sid);
  if(!list.length) return `<div class="card empty">아직 산 물건이 없어요</div>`;
  return `<div class="card">${list.map(o=>`<div class="item"><span class="emo">${esc(o.emoji)}</span><div class="grow"><b>${esc(o.name)} ×${o.qty}</b><div class="meta">${fdate(o.date)} · ${won(o.total)}</div></div>
    <span class="status ${o.done?'st-approved':'st-pending'}">${o.done?'받았어요':'받을 예정'}</span></div>`).join('')}</div>`;
}
function martManage(){
  const c=C();
  return `<div class="row end" style="margin-bottom:12px"><button class="btn" onclick="prodForm('')">➕ 새 상품</button></div>
  <div class="card"><div class="tbl-wrap"><table class="t"><tr><th></th><th>상품</th><th class="r">가격</th><th class="r">재고</th><th></th></tr>
  ${c.products.map(p=>`<tr><td style="font-size:1.6rem">${esc(p.emoji)}</td><td><b>${esc(p.name)}</b></td><td class="r">${won(p.price)}</td>
   <td class="r"><span class="${p.stock<=3?'minus':''}">${p.stock}개</span></td>
   <td class="nowrap"><button class="btn sm sub" onclick="restock('${p.id}')">+5</button> <button class="btn sm sub" onclick="prodForm('${p.id}')">수정</button> <button class="btn sm danger" onclick="delProd('${p.id}')">삭제</button></td></tr>`).join('')||'<tr><td colspan="5" class="empty">상품이 없어요</td></tr>'}
  </table></div></div>`;
}
function prodForm(id){
  const p=id?C().products.find(x=>x.id===id):{emoji:'🍭',name:'',price:100,stock:10};
  modal(id?'🍭 상품 수정':'🍭 새 상품', `<div class="row"><div style="width:84px"><label class="f">이모지</label><input id="pE" value="${esc(p.emoji)}"></div><div class="grow"><label class="f">상품 이름</label><input id="pN" value="${esc(p.name)}"></div></div>
    <div class="row"><div class="grow"><label class="f">가격</label><input id="pP" type="number" min="0" value="${p.price}"></div><div class="grow"><label class="f">재고</label><input id="pS" type="number" min="0" value="${p.stock}"></div></div>`,
    `<button class="btn" onclick="saveProd('${id}')">저장</button>`);
}
function saveProd(id){
  if(guard()) return;
  const c=C(), d={emoji:val('pE')||'🎁', name:val('pN'), price:Math.max(0,num(val('pP'))), stock:Math.max(0,num(val('pS')))};
  if(!d.name) return toast('상품 이름을 입력하세요');
  if(id) Object.assign(c.products.find(x=>x.id===id), d); else c.products.push({id:uid(),...d});
  save(); closeModal(); render(); toast('저장했어요 ✅');
}
function restock(id){ if(guard()) return; C().products.find(x=>x.id===id).stock+=5; save(); render(); }
function delProd(id){ ask('이 상품을 삭제할까요?', ()=>{ const c=C(); c.products=c.products.filter(x=>x.id!==id); save(); render(); }, '삭제'); }
function martOrders(){
  const c=C(), list=[...c.orders].sort((a,b)=>(a.done-b.done));
  return `<div class="card"><h3>📦 학생 주문 (${c.orders.filter(o=>!o.done).length}건 전달 대기)</h3>
  ${list.slice(0,80).map(o=>`<div class="item"><span class="emo">${esc(o.emoji)}</span><div class="grow"><b>${esc(stuName(o.sid))}</b> · ${esc(o.name)} ×${o.qty}<div class="meta">${fdate(o.date)} · ${won(o.total)}</div></div>
   <button class="btn sm ${o.done?'sub':'mint'}" onclick="toggleOrder('${o.id}')">${o.done?'↩ 취소':'✅ 전달 완료'}</button></div>`).join('')||'<p class="empty">주문이 없어요</p>'}</div>`;
}
function toggleOrder(id){ if(guard()) return; const o=C().orders.find(x=>x.id===id); o.done=!o.done; save(); render(); }

/* =========================================================
   💼 직업·자격증 협회
   ========================================================= */
function appJobs(){
  const c=C();
  if(T()){ const p=c.apps.filter(a=>a.status==='pending').length;
    return tabs([['job','💼 직업 관리'],['cert','📜 자격증 관리'],['app','📮 지원 승인'+(p?` (${p})`:'')]]) + ({job:jobsManage, cert:certsManage, app:jobsApprove}[S.tab])(); }
  return tabs([['job','💼 직업 목록'],['cert','📜 자격증'],['my','📮 내 지원 현황']]) + ({job:jobsList, cert:certsList, my:jobsMine}[S.tab])();
}
const holders = jid => C().students.filter(s=>s.jobId===jid);
const SPECIAL = {reporter:'✍️ 기사 작성', broker:'📈 증권사'};
function jobInfo(j){
  const cert=certById(j.certId);
  return `<div class="row between"><div class="jua big">${esc(j.emoji)} ${esc(j.name)}</div>${j.special?`<span class="chip lav">${SPECIAL[j.special]||''}</span>`:''}</div>
    <p>${esc(j.desc)}</p><div class="kv"><span>월급</span><b>${won(j.salary)}</b></div><div class="kv"><span>세율</span><b>${j.taxRate}%</b></div>
    <div class="kv"><span>필요 자격증</span><b>${cert?esc(cert.emoji+' '+cert.name):'없음'}</b></div><div class="kv"><span>모집 인원</span><b>${holders(j.id).length} / ${j.slots}명</b></div>`;
}
function jobsList(){
  const c=C(), s=me();
  return `<div class="grid2">${c.jobs.map(j=>{
    const has=!j.certId||s.certs.includes(j.certId), mine=s.jobId===j.id, full=holders(j.id).length>=j.slots;
    const pend=c.apps.some(a=>a.sid===s.id&&a.kind==='job'&&a.target===j.id&&a.status==='pending');
    const btn = mine?'<span class="chip mint">✅ 내 직업</span>':pend?'<span class="chip yel">⏳ 심사 중</span>':!has?'<span class="chip pink">🔒 자격증이 필요해요</span>':full?'<span class="chip">자리가 없어요</span>':`<button class="btn sm" onclick="applyJob('${j.id}')">📮 지원하기</button>`;
    return `<div class="card">${jobInfo(j)}<div class="row end mt">${btn}</div></div>`; }).join('')||'<div class="card empty">아직 직업이 없어요</div>'}</div>`;
}
function applyJob(jid){ if(guard()) return; C().apps.unshift({id:uid(), sid:S.sid, kind:'job', target:jid, status:'pending', date:now()}); save(); render(); toast('지원서를 냈어요! 📮'); }
function certsList(){
  const c=C(), s=me();
  return `<div class="grid2">${c.certs.map(x=>{ const has=s.certs.includes(x.id), pend=c.apps.some(a=>a.sid===s.id&&a.kind==='cert'&&a.target===x.id&&a.status==='pending');
    return `<div class="card"><div class="jua big">${esc(x.emoji)} ${esc(x.name)}</div><p>${esc(x.desc)}</p>
    <div class="sub">이 자격증이 필요한 직업: ${c.jobs.filter(j=>j.certId===x.id).map(j=>esc(j.name)).join(', ')||'없음'}</div>
    <div class="row end mt">${has?'<span class="chip mint">🏅 가지고 있어요</span>':pend?'<span class="chip yel">⏳ 심사 중</span>':`<button class="btn sm" onclick="applyCert('${x.id}')">✏️ 시험 신청</button>`}</div></div>`; }).join('')||'<div class="card empty">아직 자격증이 없어요</div>'}</div>`;
}
function applyCert(id){ if(guard()) return; C().apps.unshift({id:uid(), sid:S.sid, kind:'cert', target:id, status:'pending', date:now()}); save(); render(); toast('시험을 신청했어요! 선생님이 확인할 거예요 ✏️'); }
function appLabel(a){ const t=a.kind==='job'?jobById(a.target):certById(a.target); return (a.kind==='job'?'💼 직업 ':'📜 자격증 ')+(t?esc(t.name):'(삭제됨)'); }
const STATUS = {pending:'⏳ 기다리는 중', approved:'✅ 승인', rejected:'❌ 거절', active:'🔑 사용 중', ended:'🏁 끝남', cancelled:'↩ 취소'};
function jobsMine(){
  const list=C().apps.filter(a=>a.sid===S.sid), s=me();
  return `<div class="card"><h3>🏅 내 자격증</h3>${s.certs.length?s.certs.map(id=>{const x=certById(id);return x?`<span class="chip mint">${esc(x.emoji)} ${esc(x.name)}</span>`:''}).join(''):'<p class="sub">아직 자격증이 없어요</p>'}</div>
  <div class="card"><h3>📮 지원 기록</h3>${list.map(a=>`<div class="item"><div class="grow">${appLabel(a)}<div class="meta">${fdate(a.date)}</div></div><span class="status st-${a.status}">${STATUS[a.status]}</span></div>`).join('')||'<p class="empty">아직 지원한 기록이 없어요</p>'}</div>`;
}
function jobsManage(){
  const c=C();
  return `<div class="row end" style="margin-bottom:12px"><button class="btn" onclick="jobForm('')">➕ 새 직업</button></div>
  <div class="grid2">${c.jobs.map(j=>`<div class="card">${jobInfo(j)}<div class="sub mt">👤 ${holders(j.id).map(s=>esc(s.name)).join(', ')||'아직 없음'}</div>
    <div class="row end mt"><button class="btn sm sub" onclick="jobForm('${j.id}')">수정</button><button class="btn sm danger" onclick="delJob('${j.id}')">삭제</button></div></div>`).join('')||'<div class="card empty">직업이 없어요</div>'}</div>`;
}
function jobForm(id){
  const c=C(), j=id?jobById(id):{emoji:'💼',name:'',salary:1000,taxRate:10,slots:2,certId:'',special:'',desc:''};
  modal(id?'💼 직업 수정':'💼 새 직업', `
    <div class="row"><div style="width:84px"><label class="f">이모지</label><input id="jE" value="${esc(j.emoji)}"></div><div class="grow"><label class="f">직업 이름</label><input id="jN" value="${esc(j.name)}"></div></div>
    <div class="row"><div class="grow"><label class="f">월급</label><input id="jS" type="number" min="0" value="${j.salary}"></div><div class="grow"><label class="f">세율(%)</label><input id="jT" type="number" min="0" max="100" value="${j.taxRate}"></div><div class="grow"><label class="f">모집 인원</label><input id="jSl" type="number" min="1" value="${j.slots}"></div></div>
    <label class="f">필요 자격증</label><select id="jC"><option value="">없음</option>${c.certs.map(x=>`<option value="${x.id}" ${x.id===j.certId?'selected':''}>${esc(x.emoji+' '+x.name)}</option>`).join('')}</select>
    <label class="f">특별 권한</label><select id="jSp"><option value="">없음</option><option value="reporter" ${j.special==='reporter'?'selected':''}>✍️ 기자 (뉴스 기사 작성 가능)</option><option value="broker" ${j.special==='broker'?'selected':''}>📈 증권사 직원</option></select>
    <label class="f">하는 일</label><textarea id="jD" rows="3">${esc(j.desc)}</textarea>`,
    `<button class="btn" onclick="saveJob('${id}')">저장</button>`);
}
function saveJob(id){
  if(guard()) return;
  const c=C(), d={emoji:val('jE')||'💼', name:val('jN'), salary:Math.max(0,num(val('jS'))), taxRate:Math.min(100,Math.max(0,num(val('jT')))), slots:Math.max(1,num(val('jSl'))), certId:val('jC'), special:val('jSp'), desc:val('jD')};
  if(!d.name) return toast('직업 이름을 입력하세요');
  if(id) Object.assign(jobById(id), d); else c.jobs.push({id:uid(),...d});
  save(); closeModal(); render(); toast('저장했어요 ✅');
}
function delJob(id){ ask('이 직업을 삭제할까요?<br>이 직업을 가진 학생은 무직이 돼요.', ()=>{ const c=C(); c.students.forEach(s=>{ if(s.jobId===id) s.jobId=''; }); c.jobs=c.jobs.filter(j=>j.id!==id); save(); render(); }, '삭제'); }
function certsManage(){
  const c=C();
  return `<div class="row end" style="margin-bottom:12px"><button class="btn" onclick="certForm('')">➕ 새 자격증</button></div>
  <div class="grid2">${c.certs.map(x=>`<div class="card"><div class="jua big">${esc(x.emoji)} ${esc(x.name)}</div><p>${esc(x.desc)}</p>
    <div class="sub">🏅 ${c.students.filter(s=>s.certs.includes(x.id)).map(s=>esc(s.name)).join(', ')||'가진 학생 없음'}</div>
    <div class="row end mt"><button class="btn sm mint" onclick="grantForm('${x.id}')">🏅 수여하기</button><button class="btn sm sub" onclick="certForm('${x.id}')">수정</button><button class="btn sm danger" onclick="delCert('${x.id}')">삭제</button></div></div>`).join('')||'<div class="card empty">자격증이 없어요</div>'}</div>`;
}
function certForm(id){
  const x=id?certById(id):{emoji:'📜',name:'',desc:''};
  modal(id?'📜 자격증 수정':'📜 새 자격증', `<div class="row"><div style="width:84px"><label class="f">이모지</label><input id="cE" value="${esc(x.emoji)}"></div><div class="grow"><label class="f">자격증 이름</label><input id="cN" value="${esc(x.name)}"></div></div>
    <label class="f">설명 / 따는 방법</label><textarea id="cD" rows="3">${esc(x.desc)}</textarea>`, `<button class="btn" onclick="saveCert('${id}')">저장</button>`);
}
function saveCert(id){
  if(guard()) return;
  const c=C(), d={emoji:val('cE')||'📜', name:val('cN'), desc:val('cD')};
  if(!d.name) return toast('이름을 입력하세요');
  if(id) Object.assign(certById(id), d); else c.certs.push({id:uid(),...d});
  save(); closeModal(); render();
}
function delCert(id){ ask('이 자격증을 삭제할까요?', ()=>{ const c=C(); c.students.forEach(s=>s.certs=s.certs.filter(x=>x!==id)); c.jobs.forEach(j=>{ if(j.certId===id) j.certId=''; }); c.certs=c.certs.filter(x=>x.id!==id); save(); render(); }, '삭제'); }
function grantForm(id){
  const x=certById(id);
  modal(`🏅 ${esc(x.name)} 수여`, `<p class="sub">자격증을 가질 학생을 체크하세요.</p>${sorted().map(s=>`<label class="item" style="cursor:pointer"><input type="checkbox" id="gc_${s.id}" ${s.certs.includes(id)?'checked':''}><span class="grow">${s.num}. ${esc(s.name)}</span></label>`).join('')||'<p class="empty">학생이 없어요</p>'}`,
    `<button class="btn" onclick="saveGrant('${id}')">저장</button>`);
}
function saveGrant(id){
  if(guard()) return;
  C().students.forEach(s=>{ const cb=$('gc_'+s.id); if(!cb) return; const has=s.certs.includes(id); if(cb.checked&&!has) s.certs.push(id); if(!cb.checked&&has) s.certs=s.certs.filter(x=>x!==id); });
  save(); closeModal(); render(); toast('저장했어요 🏅');
}
function jobsApprove(){
  const c=C(), pend=c.apps.filter(a=>a.status==='pending'), done=c.apps.filter(a=>a.status!=='pending').slice(0,20);
  return `<div class="card"><h3>📮 기다리는 신청 (${pend.length})</h3>${pend.map(a=>{ const s=stuById(a.sid), cur=jobOf(s);
    return `<div class="item"><div class="grow"><b>${esc(stuName(a.sid))}</b> · ${appLabel(a)}<div class="meta">${fdate(a.date)}${a.kind==='job'?` · 지금 직업: ${cur?esc(cur.name):'없음'}`:''}</div></div>
    <button class="btn sm mint" onclick="decideApp('${a.id}',1)">승인</button><button class="btn sm sub" onclick="decideApp('${a.id}',0)">거절</button></div>`; }).join('')||'<p class="empty">기다리는 신청이 없어요 🌱</p>'}</div>
  <div class="card"><h3>📜 처리한 기록</h3>${done.map(a=>`<div class="item"><div class="grow">${esc(stuName(a.sid))} · ${appLabel(a)}<div class="meta">${fdate(a.date)}</div></div><span class="status st-${a.status}">${STATUS[a.status]}</span></div>`).join('')||'<p class="empty">기록이 없어요</p>'}</div>`;
}
function decideApp(id,ok){
  if(guard()) return;
  const c=C(), a=c.apps.find(x=>x.id===id), s=stuById(a.sid);
  a.status = ok?'approved':'rejected';
  if(ok && s){
    if(a.kind==='job'){ if(!jobById(a.target)) return toast('직업이 삭제되었어요'); s.jobId=a.target; c.apps.forEach(x=>{ if(x!==a&&x.sid===s.id&&x.kind==='job'&&x.status==='pending') x.status='rejected'; }); }
    else if(!s.certs.includes(a.target)) s.certs.push(a.target);
  }
  save(); render(); toast(ok?'승인했어요 ✅':'거절했어요');
}

/* =========================================================
   🧾 국세청
   ========================================================= */
function appTax(){
  if(T()) return tabs([['rate','📊 직업별 세율'],['bill','🧾 세금 고지'],['stat','✅ 납부 현황'],['notice','📢 세금 공지']]) + ({rate:taxRates, bill:taxIssue, stat:taxStat, notice:taxNoticeManage}[S.tab])();
  return tabs([['notice','📢 세금 공지'],['bill','🧾 내 고지서'],['hist','📜 납부 내역']]) + ({notice:taxNoticeView, bill:taxBillsMine, hist:taxHist}[S.tab])();
}
function taxNoticeView(){
  const c=C(), s=me(), j=jobOf(s);
  return `<div class="card hero"><h3>💼 내가 내야 하는 세금</h3>${j?`<p>${esc(j.emoji+' '+j.name)}는 월급 <b>${won(j.salary)}</b>의 <b>${j.taxRate}%</b>인 <b class="minus">${won(Math.round(j.salary*j.taxRate/100))}</b>을 세금으로 내요.<br><span class="sub">월급을 받을 때 자동으로 빠져나가요.</span></p>`:'<p class="sub">직업이 생기면 월급에서 세금을 내게 돼요.</p>'}</div>
  ${c.taxNotices.map(n=>`<div class="card"><div class="row between"><b class="jua big">📢 ${esc(n.title)}</b><span class="meta">${fday(n.date)}</span></div><div class="body">${esc(n.body)}</div></div>`).join('')||'<div class="card empty">공지가 없어요</div>'}`;
}
function taxBillsMine(){
  const list=C().taxBills.filter(b=>b.sid===S.sid && !b.paid);
  return `<div class="card"><h3>🧾 내야 할 세금 고지서</h3>${list.map(b=>`<div class="item"><span class="emo">🧾</span><div class="grow"><b>${esc(b.title)}</b><div class="meta">${fday(b.date)} 발급${b.memo?' · '+esc(b.memo):''}</div></div><b class="minus">${won(b.amount)}</b><button class="btn sm" onclick="payBill('${b.id}')">납부</button></div>`).join('')||'<p class="empty">낼 세금이 없어요 👍</p>'}</div>`;
}
function payBill(id){
  if(guard()) return;
  const b=C().taxBills.find(x=>x.id===id), s=me();
  if(s.balance<b.amount) return toast('잔액이 부족해요 😢');
  ask(`<b>${esc(b.title)}</b> ${won(b.amount)}을 낼까요?`, ()=>{ addTx(s,-b.amount,'세금 납부',b.title); budgetAdd(b.amount,`${b.title} (${s.name})`); b.paid=true; b.paidDate=now(); const r=rule('tax_pay'); if(r && !b.late) ruleFire(s,'tax_pay'); save(); render(); toast(r && !b.late ? `세금을 냈어요! 신용 점수 ${r.pts>0?'+':''}${r.pts} ✨` : '세금을 냈어요! 고마워요 💛'); }, '납부하기');
}
function taxHist(){
  const c=C();
  const a=c.payslips.filter(p=>p.sid===S.sid && p.tax>0).map(p=>({date:p.date, t:`소득세 (${p.memo})`, amt:p.tax}));
  const b=c.taxBills.filter(x=>x.sid===S.sid && x.paid).map(x=>({date:x.paidDate||x.date, t:x.title, amt:x.amount}));
  const list=[...a,...b].sort((x,y)=>y.date.localeCompare(x.date)), tot=list.reduce((s,x)=>s+x.amt,0);
  return `<div class="card hero"><div class="sub">지금까지 낸 세금</div><div class="money-big">${won(tot)}</div><div class="sub">고마워요! 이 돈은 우리 반 모두를 위해 쓰여요 💛</div></div>
  <div class="card">${list.map(x=>`<div class="item"><div class="grow">${esc(x.t)}<div class="meta">${fdate(x.date)}</div></div><b>${won(x.amt)}</b></div>`).join('')||'<p class="empty">아직 낸 세금이 없어요</p>'}</div>`;
}
function taxRates(){
  const c=C();
  return `<div class="card"><h3>📊 직업별 월급과 세율</h3><p class="sub">숫자를 바꾸고 [모두 저장]을 누르세요.</p><div class="tbl-wrap"><table class="t">
  <tr><th>직업</th><th>월급</th><th>세율(%)</th><th class="r">세금</th><th class="r">실수령</th></tr>
  ${c.jobs.map(j=>{ const tax=Math.round(j.salary*j.taxRate/100); return `<tr><td>${esc(j.emoji+' '+j.name)}</td><td><input class="sm num" id="ts_${j.id}" type="number" value="${j.salary}"></td><td><input class="sm num" id="tr_${j.id}" type="number" value="${j.taxRate}"></td><td class="r minus">${won(tax)}</td><td class="r plus">${won(j.salary-tax)}</td></tr>`; }).join('')||'<tr><td colspan="5" class="empty">직업이 없어요</td></tr>'}
  </table></div><div class="row end mt"><button class="btn" onclick="saveRates()">💾 모두 저장</button></div></div>`;
}
function saveRates(){
  if(guard()) return;
  C().jobs.forEach(j=>{ const s=$('ts_'+j.id), r=$('tr_'+j.id); if(s) j.salary=Math.max(0,num(s.value)); if(r) j.taxRate=Math.min(100,Math.max(0,num(r.value))); });
  save(); render(); toast('저장했어요 ✅');
}
function taxIssue(){
  return `<div class="card"><h3>🧾 세금 고지서 보내기</h3><p class="sub">예: 전기세, 환경 부담금, 자리세 등 추가 세금을 학생들에게 보내요.</p>
    <label class="f">세금 이름</label><input id="bT" placeholder="예: 11월 전기세">
    <div class="row"><div class="grow"><label class="f">금액 (1인당)</label><input id="bA" type="number" min="1"></div>
    <div class="grow"><label class="f">받는 학생</label><select id="bW"><option value="all">모든 학생</option><option value="job">직업이 있는 학생</option></select></div></div>
    <label class="f">메모 (선택)</label><input id="bM" placeholder="예: 금요일까지 내요">
    <div class="row end mt"><button class="btn" onclick="issueBill()">📮 고지서 보내기</button></div></div>`;
}
function issueBill(){
  if(guard()) return;
  const c=C(), title=val('bT'), amt=num(val('bA')), who=val('bW'), memo=val('bM');
  if(!title||amt<=0) return toast('세금 이름과 금액을 입력하세요');
  const list=c.students.filter(s=>who==='all'||jobOf(s));
  if(!list.length) return toast('받을 학생이 없어요');
  const gid=uid(), d=now();
  list.forEach(s=>c.taxBills.unshift({id:uid(), gid, sid:s.id, title, amount:amt, memo, date:d, paid:false}));
  save(); S.tab='stat'; render(); toast(`${list.length}명에게 고지서를 보냈어요 🧾`);
}
function taxStat(){
  const c=C(), groups={};
  c.taxBills.forEach(b=>{ (groups[b.gid]=groups[b.gid]||{title:b.title, amount:b.amount, date:b.date, list:[]}).list.push(b); });
  const gs=Object.entries(groups).sort((a,b)=>b[1].date.localeCompare(a[1].date));
  return gs.map(([gid,g])=>{ const paid=g.list.filter(b=>b.paid), unpaid=g.list.filter(b=>!b.paid);
    return `<div class="card"><div class="row between"><b class="jua big">🧾 ${esc(g.title)}</b><span class="meta">${fday(g.date)} · 1인당 ${won(g.amount)}</span></div>
    <div class="bar-row"><span class="nm">납부율</span><div class="bt"><div class="bf" style="width:${Math.round(paid.length/g.list.length*100)}%"></div></div><span class="vv">${paid.length}/${g.list.length}명</span></div>
    ${unpaid.length?`<div class="sub">아직 안 낸 학생: ${unpaid.map(b=>esc(stuName(b.sid))).join(', ')}</div><div class="row end mt"><button class="btn sm sub" onclick="cancelBills('${gid}')">안 낸 고지서 취소</button></div>`:'<div class="plus">모두 냈어요! 🎉</div>'}</div>`; }).join('') || '<div class="card empty">보낸 고지서가 없어요</div>';
}
function cancelBills(gid){ ask('아직 내지 않은 고지서를 취소할까요?', ()=>{ const c=C(); c.taxBills=c.taxBills.filter(b=>!(b.gid===gid&&!b.paid)); save(); render(); }); }
function taxNoticeManage(){ return postManager('taxNotices','세금 공지'); }

/* 공지 공통 */
function postManager(key,label){
  const c=C();
  return `<div class="card"><h3>✏️ ${label} 쓰기</h3><label class="f">제목</label><input id="npT"><label class="f">내용</label><textarea id="npB" rows="4"></textarea>
    <div class="row end mt"><button class="btn" onclick="addPost('${key}')">📢 올리기</button></div></div>
    ${c[key].map(n=>`<div class="card"><div class="row between"><b class="jua big">📢 ${esc(n.title)}</b><div class="row"><span class="meta">${fday(n.date)}</span><button class="btn sm danger" onclick="delPost('${key}','${n.id}')">삭제</button></div></div><div class="body">${esc(n.body)}</div></div>`).join('')}`;
}
function addPost(key){ if(guard()) return; const t=val('npT'), b=val('npB'); if(!t) return toast('제목을 입력하세요'); C()[key].unshift({id:uid(), title:t, body:b, date:now()}); save(); render(); toast('올렸어요 📢'); }
function delPost(key,id){ ask('삭제할까요?', ()=>{ const c=C(); c[key]=c[key].filter(n=>n.id!==id); save(); render(); }, '삭제'); }

/* =========================================================
   ⚖️ 헌법재판소
   ========================================================= */
function appLaw(){ return T() ? lawEdit() : lawView(); }
function lawView(){
  const L=C().law;
  return `<div class="card center"><div style="font-size:54px">⚖️</div><h2 style="margin:4px 0">${esc(C().name)} 헌법</h2></div>
  ${L.preamble?`<div class="card"><h3>📜 전문</h3><div class="preamble">${esc(L.preamble)}</div></div>`:''}
  <div class="card">${L.articles.map((a,i)=>`<div class="article"><div class="no">제${i+1}조${a.head?` (${esc(a.head)})`:''}</div><div class="body" style="margin-top:4px">${esc(a.body)}</div></div>`).join('')||'<p class="empty">아직 헌법이 없어요</p>'}</div>`;
}
function lawEdit(){
  const L=C().law;
  return `<div class="card"><h3>📜 전문 (헌법의 머리말)</h3><textarea id="lwP" rows="3">${esc(L.preamble)}</textarea><div class="row end mt"><button class="btn sub" onclick="savePreamble()">저장</button></div></div>
  <div class="card"><h3>📖 조항</h3>${L.articles.map((a,i)=>`<div class="article"><div class="row between"><div class="no">제${i+1}조${a.head?` (${esc(a.head)})`:''}</div>
    <div class="row"><button class="btn sm sub" onclick="moveArt(${i},-1)">↑</button><button class="btn sm sub" onclick="moveArt(${i},1)">↓</button><button class="btn sm sub" onclick="artForm('${a.id}')">수정</button><button class="btn sm danger" onclick="delArt('${a.id}')">삭제</button></div></div>
    <div class="body">${esc(a.body)}</div></div>`).join('')||'<p class="empty">조항이 없어요</p>'}
    <div class="row end mt"><button class="btn" onclick="artForm('')">➕ 조항 추가</button></div></div>`;
}
function savePreamble(){ if(guard()) return; C().law.preamble=val('lwP'); save(); toast('저장했어요 ✅'); }
function artForm(id){
  const a=id?C().law.articles.find(x=>x.id===id):{head:'',body:''};
  modal(id?'✏️ 조항 수정':'➕ 조항 추가', `<label class="f">제목 (예: 평등, 납세)</label><input id="aH" value="${esc(a.head)}"><label class="f">내용</label><textarea id="aB" rows="4">${esc(a.body)}</textarea>`, `<button class="btn" onclick="saveArt('${id}')">저장</button>`);
}
function saveArt(id){
  if(guard()) return;
  const L=C().law, d={head:val('aH'), body:val('aB')};
  if(!d.body) return toast('내용을 입력하세요');
  if(id) Object.assign(L.articles.find(x=>x.id===id), d); else L.articles.push({id:uid(),...d});
  save(); closeModal(); render();
}
function moveArt(i,d){ if(guard()) return; const A=C().law.articles, j=i+d; if(j<0||j>=A.length) return; [A[i],A[j]]=[A[j],A[i]]; save(); render(); }
function delArt(id){ ask('이 조항을 삭제할까요?', ()=>{ const L=C().law; L.articles=L.articles.filter(x=>x.id!==id); save(); render(); }, '삭제'); }

/* =========================================================
   📰 뉴스
   ========================================================= */
const isReporter = s => { const j=jobOf(s); return !!j && j.special==='reporter'; };
function appNews(){
  if(T()) return tabs([['news','📰 뉴스 관리'],['notice','📢 공지사항']]) + (S.tab==='news'?newsList(true):postManager('notices','공지사항'));
  const t=[['news','📰 뉴스'],['notice','📢 공지사항']];
  if(isReporter(me())) t.push(['write','✍️ 기사 쓰기']);
  return tabs(t) + ({news:()=>newsList(false), notice:noticeList, write:newsWrite}[S.tab])();
}
function newsList(admin){
  const c=C();
  return (admin?`<div class="card sub">💡 학생 기자(특별 권한이 '기자'인 직업)가 쓴 기사가 여기에 올라와요. 지나친 기사는 삭제할 수 있어요.</div>`:'') +
  (c.news.map(n=>{ const liked=(n.likes||[]).includes(S.sid), mine=S.role==='student'&&n.sid===S.sid;
    return `<div class="card"><div><span class="cat">${esc(n.cat||'학급')}</span><b class="jua big">${esc(n.title)}</b></div>
    <div class="meta">✍️ ${esc(stuName(n.sid))} 기자 · ${fdate(n.date)}</div><div class="body">${esc(n.body)}</div>
    <div class="row between mt"><button class="btn sm ${liked?'':'sub'}" onclick="likeNews('${n.id}')">👍 ${(n.likes||[]).length}</button>
    ${admin||mine?`<button class="btn sm danger" onclick="delNews('${n.id}')">🗑 삭제</button>`:''}</div></div>`; }).join('') || '<div class="card empty">아직 뉴스가 없어요 📰</div>');
}
function likeNews(id){
  if(guard()) return;
  if(S.role!=='student') return toast('학생만 누를 수 있어요');
  const n=C().news.find(x=>x.id===id); n.likes=n.likes||[];
  n.likes = n.likes.includes(S.sid) ? n.likes.filter(x=>x!==S.sid) : [...n.likes, S.sid];
  save(); render();
}
function delNews(id){ ask('이 기사를 삭제할까요?', ()=>{ const c=C(); c.news=c.news.filter(n=>n.id!==id); save(); render(); toast('삭제했어요'); }, '삭제'); }
function noticeList(){ return C().notices.map(n=>`<div class="card"><div class="row between"><b class="jua big">📢 ${esc(n.title)}</b><span class="meta">${fday(n.date)}</span></div><div class="body">${esc(n.body)}</div></div>`).join('') || '<div class="card empty">공지사항이 없어요</div>'; }
function newsWrite(){
  return `<div class="card"><h3>✍️ 기사 쓰기</h3><p class="sub">사실만, 친구를 배려하는 말로 써요 💛</p>
    <label class="f">분류</label><select id="nwC">${['학급','경제','생활','스포츠','인터뷰','날씨'].map(x=>`<option>${x}</option>`).join('')}</select>
    <label class="f">제목</label><input id="nwT" maxlength="60"><label class="f">내용</label><textarea id="nwB" rows="8"></textarea>
    <div class="row end mt"><button class="btn" onclick="postNews()">📰 기사 올리기</button></div></div>`;
}
function postNews(){
  if(guard()) return;
  if(!isReporter(me())) return toast('기자만 기사를 쓸 수 있어요');
  const t=val('nwT'), b=val('nwB');
  if(!t||!b) return toast('제목과 내용을 입력하세요');
  C().news.unshift({id:uid(), sid:S.sid, cat:val('nwC'), title:t, body:b, date:now(), likes:[]});
  save(); S.tab='news'; render(); toast('기사를 올렸어요 📰');
}

/* =========================================================
   📈 증권사
   ========================================================= */
function seedStocks(c){
  [['🍦','아이스크림나라',100,'여름이 다가오면 인기가 많아지는 회사예요.'],['🎮','즐거운게임',150,'새 게임을 만들고 있다는 소문이 있어요.'],['🌱','초록농장',80,'친환경 채소를 키우는 회사예요.']].forEach(([e,n,p,i])=>{
    const hist=[]; let x=p; for(let k=0;k<8;k++){ hist.push({d:now(),p:x}); x=Math.max(10,Math.round(x*(0.9+Math.random()*0.2))); } hist.push({d:now(),p});
    c.stocks.push({id:uid(), emoji:e, name:n, price:p, info:i, hist});
  });
}
function appStock(){
  if(T()) return tabs([['market','📈 주식 관리'],['code','🔑 증권사 비밀번호'],['hold','👛 투자 현황']]) + ({market:stockAdmin, code:stockCodes, hold:stockHold}[S.tab])();
  return tabs([['market','📈 주식 시장'],['mine','👛 내 주식'],['broker','🏢 증권사 직원']]) + ({market:stockMarket, mine:stockMine, broker:stockBroker}[S.tab])();
}
function chart(hist){
  const w=320, h=100, ps=hist.slice(-20).map(x=>x.p); if(ps.length<2) ps.unshift(ps[0]||0);
  const mn=Math.min(...ps), mx=Math.max(...ps), rg=(mx-mn)||1;
  const pts=ps.map((p,i)=>[(i*(w-16)/(ps.length-1)+8).toFixed(1), (h-10-(p-mn)/rg*(h-22)).toFixed(1)]);
  const line=pts.map(p=>p.join(',')).join(' '), col=ps[ps.length-1]>=ps[ps.length-2]?'#F08A7E':'#7EAEF0', last=pts[pts.length-1];
  return `<svg class="chart" viewBox="0 0 ${w} ${h}"><polygon points="8,${h} ${line} ${w-8},${h}" fill="${col}" opacity=".18"/><polyline points="${line}" fill="none" stroke="${col}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/><circle cx="${last[0]}" cy="${last[1]}" r="5" fill="${col}"/></svg>`;
}
function stockHead(st){
  const prev=st.hist.length>1?st.hist[st.hist.length-2].p:st.price, d=st.price-prev, pct=prev?(d/prev*100).toFixed(1):'0.0';
  return `<div class="row between"><b class="jua big">${esc(st.emoji)} ${esc(st.name)}</b><div class="center"><div class="price-big">${won(st.price)}</div>
    <div class="${d>0?'up':d<0?'down':'sub'}">${d>0?'▲':d<0?'▼':'−'} ${Math.abs(d).toLocaleString()} (${pct}%)</div></div></div>${chart(st.hist)}`;
}
function myHold(id){ const h=(C().holdings[S.sid]||{})[id]; return h||{qty:0,cost:0}; }
function stockMarket(){
  const c=C(), s=me();
  return `<div class="card hero row between"><div><div class="sub">내 잔액</div><div class="money-big">${won(s.balance)}</div></div><div class="sub">빨간색 ▲ 올랐어요 · 파란색 ▼ 내렸어요</div></div>
  <div class="grid2">${c.stocks.map(st=>{ const h=myHold(st.id);
    return `<div class="card">${stockHead(st)}<p class="sub">ℹ️ ${esc(st.info||'정보가 없어요')}</p><div class="sub">내가 가진 주식: <b>${h.qty}주</b></div>
    <div class="row mt"><div class="stepper"><button onclick="step('sq_${st.id}',-1)">−</button><input id="sq_${st.id}" type="number" value="1" min="1"><button onclick="step('sq_${st.id}',1)">+</button></div>
    <button class="btn sm" style="background:#F08A7E;box-shadow:0 3px 0 #D86D60" onclick="trade('${st.id}',1)">사기</button><button class="btn sm" style="background:#7EAEF0;box-shadow:0 3px 0 #5E90D4" onclick="trade('${st.id}',-1)">팔기</button></div></div>`; }).join('')||'<div class="card empty">아직 주식이 없어요</div>'}</div>`;
}
function trade(id,dir){
  if(guard()) return;
  const c=C(), st=c.stocks.find(x=>x.id===id), s=me(), q=Math.max(1,num(val('sq_'+id)));
  c.holdings[s.id]=c.holdings[s.id]||{}; const h=c.holdings[s.id][id]=c.holdings[s.id][id]||{qty:0,cost:0};
  const amt=st.price*q;
  if(dir>0){
    if(s.balance<amt) return toast('잔액이 부족해요 😢');
    ask(`${esc(st.emoji+' '+st.name)} ${q}주를 ${won(amt)}에 살까요?`, ()=>{ addTx(s,-amt,'주식 매수',`${st.name} ${q}주`); h.qty+=q; h.cost+=amt; save(); render(); toast('주식을 샀어요 📈'); }, '사기');
  } else {
    if(h.qty<q) return toast('가진 주식이 부족해요');
    ask(`${esc(st.emoji+' '+st.name)} ${q}주를 ${won(amt)}에 팔까요?`, ()=>{ const avg=h.cost/h.qty; h.cost=Math.round(h.cost-avg*q); h.qty-=q; if(h.qty===0) h.cost=0; addTx(s,amt,'주식 매도',`${st.name} ${q}주`); save(); render(); toast('주식을 팔았어요 💰'); }, '팔기');
  }
}
function stockMine(){
  const c=C(); let tv=0, tc=0;
  const rows=c.stocks.map(st=>{ const h=myHold(st.id); if(!h.qty) return ''; const v=h.qty*st.price, p=v-h.cost; tv+=v; tc+=h.cost;
    return `<tr><td>${esc(st.emoji+' '+st.name)}</td><td class="r">${h.qty}주</td><td class="r">${won(Math.round(h.cost/h.qty))}</td><td class="r">${won(st.price)}</td><td class="r">${won(v)}</td><td class="r ${p>0?'up':p<0?'down':''}">${p>0?'+':''}${p.toLocaleString()}</td></tr>`; }).join('');
  return `<div class="card hero"><div class="sub">내 주식 가치</div><div class="money-big">${won(tv)}</div><div class="${tv-tc>0?'up':tv-tc<0?'down':'sub'}">수익 ${tv-tc>0?'+':''}${(tv-tc).toLocaleString()}</div></div>
  <div class="card">${rows?`<div class="tbl-wrap"><table class="t"><tr><th>주식</th><th class="r">수량</th><th class="r">산 가격(평균)</th><th class="r">지금 가격</th><th class="r">가치</th><th class="r">수익</th></tr>${rows}</table></div>`:'<p class="empty">아직 가진 주식이 없어요</p>'}</div>`;
}
function stockBroker(){
  if(!S.broker) return `<div class="card login-card" style="margin:0 auto"><div class="logo">🏢</div><h3>증권사 직원 전용</h3><p class="sub">선생님께 받은 증권사 비밀번호를 입력하세요</p>
    <input id="bkCode" class="big-input" type="password" inputmode="numeric" maxlength="6" onkeydown="if(event.key==='Enter')brokerLogin()"><button class="btn wide" onclick="brokerLogin()">들어가기</button></div>`;
  return `<div class="card row between"><b class="jua">🏢 증권사 직원 모드</b><button class="btn sm sub" onclick="S.broker=false;render()">나가기</button></div>` + stockEditList(false);
}
function brokerLogin(){
  if(guard()) return;
  const code=val('bkCode');
  const me_=me(), b=C().brokerCodes.find(x=>x.code===code);
  if(!b || (b.sid ? b.sid!==me_.id : false)) return toast('비밀번호가 틀렸어요');
  if(!isBroker(me_)) return toast('증권사 직원만 들어갈 수 있어요');
  S.broker=true; render(); toast('증권사 직원으로 들어왔어요 🏢');
}
function stockEditList(admin){
  const c=C();
  return `<div class="grid2">${c.stocks.map(st=>`<div class="card">${stockHead(st)}
    <label class="f">새 가격</label><div class="row"><input id="np_${st.id}" class="grow" type="number" min="1" placeholder="${st.price}"><button class="btn sm" onclick="setStockPrice('${st.id}')">가격 바꾸기</button></div>
    <label class="f">주식 정보</label><textarea id="ni_${st.id}" rows="2">${esc(st.info)}</textarea>
    <div class="row end mt"><button class="btn sm sub" onclick="saveStockInfo('${st.id}')">정보 저장</button>${admin?`<button class="btn sm danger" onclick="delStock('${st.id}')">삭제</button>`:''}</div></div>`).join('')||'<div class="card empty">주식이 없어요</div>'}</div>`;
}
const canEditStock = () => T() || (S.role==='student' && S.broker);
function setStockPrice(id){
  if(guard()||!canEditStock()) return;
  const st=C().stocks.find(x=>x.id===id), p=num(val('np_'+id));
  if(p<=0) return toast('가격을 입력하세요');
  st.price=p; st.hist.push({d:now(),p}); if(st.hist.length>60) st.hist.shift();
  save(); render(); toast('가격을 바꿨어요 📈');
}
function saveStockInfo(id){ if(guard()||!canEditStock()) return; C().stocks.find(x=>x.id===id).info=val('ni_'+id); save(); toast('정보를 저장했어요'); }
function stockAdmin(){ return `<div class="row end" style="margin-bottom:12px"><button class="btn" onclick="stockForm()">➕ 새 주식</button></div>` + stockEditList(true); }
function stockForm(){
  modal('📈 새 주식', `<div class="row"><div style="width:84px"><label class="f">이모지</label><input id="skE" value="🏢"></div><div class="grow"><label class="f">회사 이름</label><input id="skN"></div></div>
    <label class="f">처음 가격</label><input id="skP" type="number" value="100"><label class="f">회사 정보</label><textarea id="skI" rows="2"></textarea>`, `<button class="btn" onclick="addStock()">추가</button>`);
}
function addStock(){
  if(guard()) return;
  const n=val('skN'), p=num(val('skP'));
  if(!n||p<=0) return toast('이름과 가격을 입력하세요');
  C().stocks.push({id:uid(), emoji:val('skE')||'🏢', name:n, price:p, info:val('skI'), hist:[{d:now(),p}]});
  save(); closeModal(); render();
}
function delStock(id){
  ask('이 주식을 삭제할까요?<br>학생들이 가진 주식은 지금 가격으로 돌려줘요.', ()=>{
    const c=C(), st=c.stocks.find(x=>x.id===id);
    c.students.forEach(s=>{ const h=(c.holdings[s.id]||{})[id]; if(h&&h.qty){ addTx(s,h.qty*st.price,'주식 정산',`${st.name} ${h.qty}주`); delete c.holdings[s.id][id]; } });
    c.stocks=c.stocks.filter(x=>x.id!==id); save(); render();
  }, '삭제');
}
const isBroker = s => { const j=jobOf(s); return !!j && j.special==='broker'; };
function stockCodes(){
  const c=C(), brokers=sorted().filter(isBroker);
  return `<div class="card"><h3>🔑 증권사 비밀번호 만들기</h3><p class="sub">비밀번호는 <b>증권사 직원</b>(직업 특별 권한이 '증권사'인 학생)에게만 줄 수 있어요. 받은 학생만 그 비밀번호로 증권사 직원 화면에 들어갈 수 있어요.</p>
    ${brokers.length?`<div class="row"><div class="grow"><label class="f">누구에게 줄까요?</label><select id="bkS">${brokers.map(s=>`<option value="${s.id}">${s.num}. ${esc(s.name)} (${esc(jobOf(s).name)})</option>`).join('')}</select></div>
    <div class="grow"><label class="f">비밀번호 (숫자 4~6자리)</label><div class="row"><input id="bkC" class="grow" inputmode="numeric" maxlength="6" placeholder="예: 2580"><button class="btn sm sub" onclick="$('bkC').value=rand4()" title="자동으로 만들기">🎲</button></div></div></div>
    <div class="row end mt"><button class="btn" onclick="addCode()">🔑 비밀번호 주기</button></div>`
    :`<div class="alert">아직 증권사 직원이 없어요. 학생 관리에서 직업을 '증권사 직원'으로 정해 주세요.</div>`}</div>
    <div class="card"><h3>📋 만든 비밀번호</h3>${c.brokerCodes.map(b=>{ const s=b.sid?stuById(b.sid):null, ok=s&&isBroker(s);
      return `<div class="item"><span class="emo">🔑</span><div class="grow"><span class="code-show" style="font-size:1.4rem">${esc(b.code)}</span><div class="meta">${s?esc(s.name):esc(b.label||'이름 없음')} · ${fday(b.date)}${b.sid&&!ok?' · ⚠️ 지금은 증권사 직원이 아니라 쓸 수 없어요':''}</div></div><button class="btn sm danger" onclick="delCode('${esc(b.code)}')">삭제</button></div>`; }).join('')||'<p class="empty">아직 만든 비밀번호가 없어요</p>'}</div>`;
}
function addCode(){
  if(guard()) return;
  const c=C(), sid=val('bkS'), code=val('bkC'), s=stuById(sid);
  if(!s || !isBroker(s)) return toast('증권사 직원만 고를 수 있어요');
  if(!/^\d{4,6}$/.test(code)) return toast('비밀번호는 숫자 4~6자리로 정해 주세요');
  if(c.brokerCodes.some(b=>b.code===code)) return toast('이미 쓰고 있는 비밀번호예요');
  c.brokerCodes=c.brokerCodes.filter(b=>b.sid!==sid);
  c.brokerCodes.push({code, sid, label:s.name, date:now()}); save(); render(); toast(`${s.name} 학생에게 비밀번호를 줬어요 🔑`);
}
function delCode(code){ ask('이 비밀번호를 삭제할까요?', ()=>{ const c=C(); c.brokerCodes=c.brokerCodes.filter(b=>b.code!==code); save(); render(); }, '삭제'); }
function stockHold(){
  const c=C();
  return `<div class="card"><div class="tbl-wrap"><table class="t"><tr><th>이름</th>${c.stocks.map(st=>`<th class="r">${esc(st.emoji)}</th>`).join('')}<th class="r">주식 가치</th></tr>
  ${sorted().map(s=>`<tr><td>${esc(s.name)}</td>${c.stocks.map(st=>`<td class="r">${((c.holdings[s.id]||{})[st.id]||{}).qty||0}</td>`).join('')}<td class="r">${won(stockValue(s.id))}</td></tr>`).join('')}</table></div></div>`;
}

/* =========================================================
   🏠 국토교통부 (자리 부동산)
   ========================================================= */
function genSeats(c){ c.seats=[]; for(let r=1;r<=c.seatCfg.rows;r++) for(let k=1;k<=c.seatCfg.cols;k++) c.seats.push({id:uid(), r, c:k, price:c.seatCfg.price, owner:''}); }
const todayStr = (d=new Date()) => `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;
function addDays(str,n){ const d=new Date(str+'T00:00:00'); d.setDate(d.getDate()+n); return todayStr(d); }
const mmdd = str => { const [,m,d]=String(str).split('-'); return `${+m}/${+d}`; };
const seatOf = sid => C().seats.find(x=>x.owner===sid);
const seatName = st => st ? `${st.r}-${st.c}` : '(없어진 자리)';
const OPEN_REQ = ['pending','approved','active'];
function seatSweep(){
  const c=C(); if(!c || !c.features.realty) return false;
  const t=todayStr(); let changed=false;
  c.seatReqs.forEach(r=>{
    if(r.status==='approved' && r.to<t){ r.status='ended'; changed=true; return; }
    if(r.status==='approved' && r.from<=t){
      const A=c.seats.find(x=>x.id===r.seatId); if(!A){ r.status='cancelled'; changed=true; return; }
      const B=seatOf(r.sid), O=A.owner;
      if(O!==r.sid){ A.owner=r.sid; if(B) B.owner=O||''; }
      r.orig=O||''; r.swapSeat=B?B.id:''; r.status='active'; changed=true;
    } else if(r.status==='active' && r.to<t){
      const A=c.seats.find(x=>x.id===r.seatId), B=c.seats.find(x=>x.id===r.swapSeat);
      if(A && A.owner===r.sid){ A.owner=r.orig||''; if(B && B.owner===r.orig) B.owner=r.sid; }
      r.status='ended'; changed=true;
    }
  });
  return changed;
}
function appRealty(){
  const c=C();
  if(T()){ const p=c.seatReqs.filter(r=>r.status==='pending').length;
    return tabs([['map','🗺️ 자리 지도'],['req','📮 자리 요청'+(p?` (${p})`:'')],['set','⚙️ 자리 설정·랜덤 배정']]) + ({map:seatMap, req:realtyReq, set:realtySet}[S.tab])(); }
  const r=c.seatReqs.filter(x=>x.status==='pending' && x.owner===S.sid && x.ownerOk===null).length;
  return tabs([['map','🗺️ 자리 보기'],['my','📮 내가 보낸 요청'],['recv','📬 받은 요청'+(r?` (${r})`:'')]]) + ({map:seatMap, my:realtyMy, recv:realtyRecv}[S.tab])();
}
function seatMap(){
  const c=C(), myId=S.role==='student'?S.sid:'';
  const rented=new Set(c.seatReqs.filter(r=>r.status==='active').map(r=>r.seatId));
  const pend=new Set(c.seatReqs.filter(r=>r.status==='pending'&&(T()||r.sid===myId||r.owner===myId)).map(r=>r.seatId));
  const empty=c.seats.filter(x=>!x.owner).length, need=c.students.filter(s=>!seatOf(s.id)).length;
  return `${T()&&need?`<div class="alert" style="margin:0 0 14px">🪑 자리가 없는 학생이 ${need}명 있어요. <button class="btn sm" onclick="setTab('set')">🎲 랜덤 배정하러 가기</button></div>`:''}
  <div class="card"><p class="sub">${T()?'자리를 누르면 가격을 바꾸거나 앉을 학생을 직접 정할 수 있어요 (돈은 오가지 않아요).':'친구 자리를 누르면 그 친구와 선생님께 자리를 빌려 달라고 요청할 수 있어요.'}
    <span class="chip yel">내 자리</span><span class="chip lav">친구 자리</span><span class="chip">빈 자리</span> 🔑 빌린 자리</p>
  <div class="desk">🧑‍🏫 교탁 · 칠판</div>
  <div class="seatmap" style="grid-template-columns:repeat(${c.seatCfg.cols},1fr)">${c.seats.map(st=>`<button class="seat ${st.owner?(st.owner===myId?'mine':'taken'):''} ${pend.has(st.id)?'req':''}" onclick="seatClick('${st.id}')"><b>${seatName(st)}${rented.has(st.id)?' 🔑':''}</b>${st.owner?esc(stuName(st.owner)):'빈 자리'}<br><span class="sub">${won(st.price)}</span></button>`).join('')}</div>
  ${empty&&!T()?'':''}</div>`;
}
function seatClick(id){
  const c=C(), st=c.seats.find(x=>x.id===id);
  if(T()) return seatEdit(id);
  if(st.owner===S.sid) return toast('내 자리예요 😊');
  if(guard()) return;
  if(!seatOf(S.sid)) return toast('아직 내 자리가 없어요. 선생님께 자리를 받은 뒤에 요청할 수 있어요');
  if(c.seatReqs.some(r=>r.sid===S.sid && OPEN_REQ.includes(r.status))) return toast('이미 진행 중인 자리 요청이 있어요. [내가 보낸 요청]을 확인해 주세요');
  const t=todayStr(), owner=st.owner?stuName(st.owner):'';
  modal(`🪑 ${seatName(st)} 자리 빌리기`, `<p>${owner?`<b>${esc(owner)}</b> 친구의 자리예요.`:'지금은 빈 자리예요.'}</p>
    <div class="row"><div class="grow"><label class="f">언제부터</label><input id="srF" type="date" value="${t}" min="${t}"></div><div class="grow"><label class="f">언제까지</label><input id="srT" type="date" value="${addDays(t,(c.seatCfg.cycle||14)-1)}" min="${t}"></div></div>
    <div class="kv mt"><span>임대료 (월급날마다)</span><b class="minus">${won(st.price)}</b></div>
    <p class="sub">${owner?`${esc(owner)} 친구와 선생님이 <b>둘 다</b> 허락하면, 시작하는 날 서로 자리를 바꿔요. 끝나는 날이 지나면 원래 자리로 돌아가요.`:'선생님이 허락하면 시작하는 날 이 자리로 옮겨요.'}</p>`,
    `<button class="btn" onclick="sendSeatReq('${id}')">📮 요청 보내기</button>`);
}
function sendSeatReq(id){
  if(guard()) return;
  const c=C(), st=c.seats.find(x=>x.id===id), from=val('srF'), to=val('srT');
  if(!from||!to) return toast('날짜를 골라 주세요');
  if(to<from) return toast('끝나는 날이 시작하는 날보다 빨라요');
  if(from<todayStr()) return toast('지난 날짜는 고를 수 없어요');
  c.seatReqs.unshift({id:uid(), sid:S.sid, seatId:id, owner:st.owner||'', from, to, rent:st.price,
    ownerOk: st.owner ? null : true, teacherOk:null, status:'pending', date:now()});
  save(); closeModal(); render(); toast(st.owner?'친구와 선생님께 요청했어요 📮':'선생님께 요청했어요 📮');
}
const OKMARK = v => v===true?'✅':v===false?'❌':'⏳';
function reqLine(r, extra){
  const c=C(), st=c.seats.find(x=>x.id===r.seatId);
  return `<div class="item"><div class="grow"><b>${esc(stuName(r.sid))}</b> → 🪑 ${seatName(st)}${r.owner?` (주인 ${esc(stuName(r.owner))})`:''}
    <div class="meta">📅 ${mmdd(r.from)} ~ ${mmdd(r.to)} · 월급날마다 ${won(r.rent)} · 주인 ${r.owner?OKMARK(r.ownerOk):'—'} 선생님 ${OKMARK(r.teacherOk)}</div></div>
    <span class="status st-${r.status}">${STATUS[r.status]||r.status}</span>${extra||''}</div>`;
}
function realtyMy(){
  const c=C(), mine=seatOf(S.sid), list=c.seatReqs.filter(r=>r.sid===S.sid && r.from!==undefined);
  const act=c.seatReqs.find(r=>r.sid===S.sid && r.status==='active');
  return `<div class="card hero"><div class="sub">지금 내 자리</div><div class="money-big">${mine?seatName(mine):'없음'}</div>
    ${act?`<div class="sub">🔑 ${mmdd(act.to)}까지 빌린 자리예요 · 월급날마다 ${won(act.rent)}</div>`:''}</div>
  <div class="card">${list.map(r=>reqLine(r, r.status==='pending'?`<button class="btn sm sub" onclick="cancelSeatReq('${r.id}')">취소</button>`:'')).join('')||'<p class="empty">보낸 요청이 없어요</p>'}</div>`;
}
function realtyRecv(){
  const c=C(), list=c.seatReqs.filter(r=>r.owner===S.sid && r.from!==undefined);
  return `<div class="card"><h3>📬 내 자리를 빌려 달라는 요청</h3><p class="sub">허락하면 그 기간 동안 친구와 자리를 서로 바꿔요. 선생님도 허락해야 바뀌어요.</p>
    ${list.map(r=>reqLine(r, r.status==='pending'&&r.ownerOk===null?`<button class="btn sm mint" onclick="decideSeatReq('${r.id}','owner',1)">허락</button><button class="btn sm sub" onclick="decideSeatReq('${r.id}','owner',0)">거절</button>`:'')).join('')||'<p class="empty">받은 요청이 없어요</p>'}</div>`;
}
function cancelSeatReq(id){ if(guard()) return; const r=C().seatReqs.find(x=>x.id===id); if(r && r.status==='pending'){ r.status='cancelled'; save(); render(); } }
function decideSeatReq(id, who, ok){
  if(guard()) return;
  const c=C(), r=c.seatReqs.find(x=>x.id===id);
  if(!r || r.status!=='pending') return;
  if(who==='owner'){ if(S.role!=='student' || r.owner!==S.sid) return; r.ownerOk=!!ok; }
  else r.teacherOk=!!ok;
  if(r.ownerOk===false || r.teacherOk===false) r.status='rejected';
  else if(r.ownerOk===true && r.teacherOk===true){
    if(c.seatReqs.some(x=>x!==r && ['approved','active'].includes(x.status) && (x.seatId===r.seatId || x.sid===r.sid || x.sid===r.owner))){
      r.teacherOk=null; save(); render(); return toast('이 자리나 학생이 이미 다른 자리 계약 중이에요. 그 계약이 끝난 뒤에 승인해 주세요');
    }
    r.status='approved'; seatSweep();
  }
  save(); render(); toast(ok?'허락했어요 ✅':'거절했어요');
}
function realtyReq(){
  const c=C(), list=c.seatReqs.filter(r=>r.from!==undefined), pend=list.filter(r=>r.status==='pending'), rest=list.filter(r=>r.status!=='pending').slice(0,30);
  return `<div class="card"><h3>📮 기다리는 요청 (${pend.length})</h3>${pend.map(r=>reqLine(r, r.teacherOk===null?`<button class="btn sm mint" onclick="decideSeatReq('${r.id}','teacher',1)">승인</button><button class="btn sm sub" onclick="decideSeatReq('${r.id}','teacher',0)">거절</button>`:'')).join('')||'<p class="empty">요청이 없어요 🌱</p>'}</div>
  <div class="card"><h3>📜 계약 기록</h3>${rest.map(r=>reqLine(r, r.status==='active'||r.status==='approved'?`<button class="btn sm sub" onclick="endSeatReq('${r.id}')">계약 끝내기</button>`:'')).join('')||'<p class="empty">기록이 없어요</p>'}</div>`;
}
function endSeatReq(id){
  ask('이 자리 계약을 지금 끝낼까요?<br><span class="sub">빌린 자리였다면 원래 자리로 돌아가요.</span>', ()=>{
    const c=C(), r=c.seatReqs.find(x=>x.id===id); if(!r) return;
    if(r.status==='active'){ r.to=addDays(todayStr(),-1); seatSweep(); } else r.status='ended';
    save(); render();
  }, '끝내기');
}
function seatEdit(id){
  const st=C().seats.find(x=>x.id===id);
  modal(`🪑 ${seatName(st)} 자리`, `<label class="f">임대료 (월급날마다)</label><input id="seP" type="number" min="0" value="${st.price}">
    <label class="f">이 자리에 앉을 학생</label><select id="seO"><option value="">빈 자리</option>${sorted().map(s=>`<option value="${s.id}" ${s.id===st.owner?'selected':''}>${s.num}. ${esc(s.name)}${seatOf(s.id)&&s.id!==st.owner?` (지금 ${seatName(seatOf(s.id))})`:''}</option>`).join('')}</select>
    <p class="sub">다른 자리에 있던 학생을 고르면, 지금 이 자리 학생과 서로 자리를 바꿔요. 선생님이 정하는 자리는 돈이 오가지 않아요.</p>`, `<button class="btn" onclick="saveSeat('${id}')">저장</button>`);
}
function saveSeat(id){
  if(guard()) return;
  const c=C(), st=c.seats.find(x=>x.id===id), o=val('seO');
  st.price=Math.max(0,num(val('seP')));
  if(o!==st.owner){
    const prev=st.owner, from=o?seatOf(o):null;
    if(from) from.owner=prev||'';
    st.owner=o;
  }
  save(); closeModal(); render(); toast('바꿨어요 🪑');
}
function shuffle(a){ for(let i=a.length-1;i>0;i--){ const j=Math.floor(Math.random()*(i+1)); [a[i],a[j]]=[a[j],a[i]]; } return a; }
function randomSeats(){
  const c=C();
  if(c.seats.length<c.students.length) return toast(`자리(${c.seats.length}개)가 학생 수(${c.students.length}명)보다 적어요. 줄·칸을 늘려 주세요`);
  ask('🎲 모든 학생의 자리를 랜덤으로 다시 정할까요?<br><span class="sub">돈은 오가지 않고, 진행 중인 자리 요청과 계약은 모두 끝나요.</span>', ()=>{
    c.seats.forEach(x=>x.owner='');
    const seats=shuffle([...c.seats]);
    shuffle([...c.students]).forEach((s,i)=>{ seats[i].owner=s.id; });
    c.seatReqs.forEach(r=>{ if(r.status==='pending') r.status='cancelled'; else if(['approved','active'].includes(r.status)) r.status='ended'; });
    c.seatRound=now(); save(); S.tab='map'; render(); toast('자리를 새로 정했어요! 🎲');
  }, '랜덤 배정');
}
function realtySet(){
  const c=C(), g=c.seatCfg, next=c.seatRound?addDays(todayStr(new Date(c.seatRound)), g.cycle||14):'';
  return `<div class="card hero"><h3>🎲 자리 랜덤 배정</h3>
    <p class="sub">모든 학생에게 자리를 랜덤으로 무료 배정해요.${c.seatRound?` 마지막 배정: <b>${fday(c.seatRound)}</b> · 다음 예정: <b>${mmdd(next)}</b>${next<=todayStr()?' <span class="minus">(자리 바꿀 때가 됐어요!)</span>':''}`:''}</p>
    <div class="row"><label class="f" style="margin:0">자리 바꾸는 주기</label><input id="rsCy" class="sm num" type="number" min="1" value="${g.cycle||14}"><span class="sub">일마다</span><button class="btn sm sub" onclick="saveCycle()">저장</button></div>
    <button class="btn wide mt" onclick="randomSeats()">🎲 지금 랜덤 배정하기</button></div>
  <div class="two"><div class="card"><h3>🪑 자리 배치 다시 만들기</h3>
    <div class="row"><div class="grow"><label class="f">줄 (세로)</label><input id="rsR" type="number" min="1" max="10" value="${g.rows}"></div><div class="grow"><label class="f">칸 (가로)</label><input id="rsC" type="number" min="1" max="10" value="${g.cols}"></div></div>
    <label class="f">기본 임대료</label><input id="rsP" type="number" min="0" value="${g.price}">
    <p class="sub">⚠️ 다시 만들면 자리가 새로 생기고 랜덤으로 다시 배정돼요.</p><button class="btn wide" onclick="regenSeats()">다시 만들기</button></div>
    <div class="card"><h3>💰 임대료 한꺼번에 바꾸기</h3><label class="f">임대료 (월급날마다)</label><input id="rsAll" type="number" min="0" value="${g.price}">
    <div class="row mt"><button class="btn sub grow" onclick="bulkPrice('all')">모든 자리</button><button class="btn sub grow" onclick="bulkPrice('front')">앞줄만</button></div>
    <p class="sub">자리를 빌린 학생만 월급날 임대료를 내요. 랜덤 배정이나 선생님이 정한 자리는 무료예요.</p></div></div>`;
}
function saveCycle(){ if(guard()) return; C().seatCfg.cycle=Math.max(1,num(val('rsCy'))); save(); render(); toast('저장했어요'); }
function regenSeats(){
  const rows=Math.min(10,Math.max(1,num(val('rsR')))), cols=Math.min(10,Math.max(1,num(val('rsC')))), price=Math.max(0,num(val('rsP')));
  const c=C();
  if(rows*cols<c.students.length) return toast(`자리(${rows*cols}개)가 학생 수(${c.students.length}명)보다 적어요`);
  ask('자리를 다시 만들까요? 모든 학생의 자리가 랜덤으로 다시 정해져요.', ()=>{
    c.seatCfg=Object.assign(c.seatCfg,{rows, cols, price}); genSeats(c);
    const seats=shuffle([...c.seats]); shuffle([...c.students]).forEach((s,i)=>{ seats[i].owner=s.id; });
    c.seatReqs.forEach(r=>{ if(r.status==='pending') r.status='cancelled'; else if(['approved','active'].includes(r.status)) r.status='ended'; });
    c.seatRound=now(); save(); S.tab='map'; render(); toast('자리를 새로 만들었어요 🪑');
  });
}
function bulkPrice(which){ if(guard()) return; const c=C(), p=Math.max(0,num(val('rsAll'))); c.seats.forEach(x=>{ if(which==='all'||x.r===1) x.price=p; }); save(); render(); toast('임대료를 바꿨어요'); }

/* =========================================================
   🏥 국민건강보험
   ========================================================= */
function appIns(){
  if(T()){ const p=C().ins.claims.filter(x=>x.status==='pending').length;
    return tabs([['plan','📋 보험 상품'],['mem','👥 가입자·보험료'],['claim','🩹 보험금 청구'+(p?` (${p})`:'')]]) + ({plan:()=>insPlans(true), mem:insMembers, claim:insClaims}[S.tab])(); }
  return tabs([['plan','📋 보험 상품'],['claim','🩹 보험금 청구']]) + (S.tab==='plan'?insPlans(false):insClaimStudent());
}
function insPlans(admin){
  const c=C(), myPlan=S.role==='student'?c.ins.members[S.sid]:'';
  return `${admin?`<div class="card hero row between"><div><div class="sub">보험 기금</div><div class="money-big">${won(c.ins.fund)}</div></div><button class="btn" onclick="planForm('')">➕ 새 보험</button></div>`
    :`<div class="card hero"><b class="jua big">🏥 보험이란?</b><p>매달 조금씩 보험료를 모아 두었다가, 아프거나 어려운 일이 생긴 친구에게 보험금을 주는 제도예요. 모든 학생은 <b>기본 건강보험</b>에 꼭 가입해야 하고, 보험료는 월급날 자동으로 빠져요.</p></div>`}
  <div class="grid2">${c.ins.plans.map(p=>`<div class="card"><div class="jua big">🩺 ${esc(p.name)} ${p.basic?'<span class="chip pink">필수</span>':''}</div><p>${esc(p.desc)}</p>
    <div class="kv"><span>보험료 (한 번에)</span><b>${won(p.premium)}</b></div><div class="kv"><span>보험금 (청구 1번)</span><b>${won(p.coverage)}</b></div>
    ${admin?`<div class="kv"><span>가입자</span><b>${Object.values(c.ins.members).filter(x=>x===p.id).length}명</b></div><div class="row end mt"><button class="btn sm sub" onclick="planForm('${p.id}')">수정</button>${p.basic?'':`<button class="btn sm danger" onclick="delPlan('${p.id}')">삭제</button>`}</div>`
     :`<div class="row end mt">${myPlan===p.id?`<span class="chip mint">✅ 지금 내 보험</span>`:`<button class="btn sm" onclick="joinIns('${p.id}')">이 보험으로 바꾸기</button>`}</div>`}</div>`).join('')||'<div class="card empty">보험 상품이 없어요</div>'}</div>`;
}
function joinIns(pid){ if(guard()) return; C().ins.members[S.sid]=pid; save(); render(); toast('보험을 바꿨어요 🏥 다음 월급날부터 적용돼요'); }
function planForm(id){
  const p=id?C().ins.plans.find(x=>x.id===id):{name:'',premium:100,coverage:500,desc:''};
  modal(id?'보험 수정':'새 보험', `<label class="f">이름</label><input id="ipN" value="${esc(p.name)}"><div class="row"><div class="grow"><label class="f">보험료</label><input id="ipP" type="number" value="${p.premium}"></div><div class="grow"><label class="f">보험금</label><input id="ipC" type="number" value="${p.coverage}"></div></div><label class="f">설명</label><textarea id="ipD" rows="2">${esc(p.desc)}</textarea>`, `<button class="btn" onclick="savePlan('${id}')">저장</button>`);
}
function savePlan(id){
  if(guard()) return;
  const c=C(), d={name:val('ipN'), premium:Math.max(0,num(val('ipP'))), coverage:Math.max(0,num(val('ipC'))), desc:val('ipD')};
  if(!d.name) return toast('이름을 입력하세요');
  if(id) Object.assign(c.ins.plans.find(x=>x.id===id), d); else c.ins.plans.push({id:uid(),...d});
  save(); closeModal(); render();
}
function delPlan(id){ ask('이 보험을 삭제할까요? 가입자는 기본 건강보험으로 옮겨져요.', ()=>{ const c=C(), bp=basicPlan(c); c.ins.plans=c.ins.plans.filter(x=>x.id!==id||x.basic); for(const k in c.ins.members) if(c.ins.members[k]===id) c.ins.members[k]=bp.id; save(); render(); }, '삭제'); }
function insMembers(){
  const c=C(), list=Object.entries(c.ins.members);
  return `<div class="card hero"><div class="sub">보험 기금</div><div class="money-big">${won(c.ins.fund)}</div><div class="sub">보험료는 은행에서 월급을 줄 때 자동으로 걷혀요.</div></div>
  <div class="card"><h3>👥 가입자 (${list.length}명)</h3>${list.map(([sid,pid])=>{ const p=c.ins.plans.find(x=>x.id===pid), s=stuById(sid); return s?`<div class="kv"><span>${esc(s.name)}</span><b>${p?esc(p.name)+' · '+won(p.premium):'-'}</b></div>`:''; }).join('')||'<p class="empty">가입자가 없어요</p>'}</div>`;
}
function insClaimStudent(){
  const c=C(), pid=c.ins.members[S.sid], p=c.ins.plans.find(x=>x.id===pid), list=c.ins.claims.filter(x=>x.sid===S.sid);
  return `${p?`<div class="card"><h3>🩹 보험금 청구하기</h3><p class="sub">가입한 보험: ${esc(p.name)} · 보험금 ${won(p.coverage)}</p><label class="f">어떤 일이 있었나요?</label><textarea id="clR" rows="3" placeholder="예: 감기에 걸려 병원에 다녀왔어요"></textarea><div class="row end mt"><button class="btn" onclick="claimIns()">청구하기</button></div></div>`
   :`<div class="card empty">보험에 가입해야 보험금을 청구할 수 있어요</div>`}
  <div class="card"><h3>📜 청구 기록</h3>${list.map(x=>`<div class="item"><div class="grow">${esc(x.reason)}<div class="meta">${fdate(x.date)}</div></div><span class="status st-${x.status}">${STATUS[x.status]}</span></div>`).join('')||'<p class="empty">기록이 없어요</p>'}</div>`;
}
function claimIns(){ if(guard()) return; const r=val('clR'); if(!r) return toast('내용을 입력하세요'); C().ins.claims.unshift({id:uid(), sid:S.sid, reason:r, status:'pending', date:now()}); save(); render(); toast('청구했어요! 선생님이 확인할 거예요 🩹'); }
function insClaims(){
  const c=C(), pend=c.ins.claims.filter(x=>x.status==='pending'), done=c.ins.claims.filter(x=>x.status!=='pending').slice(0,20);
  return `<div class="card"><h3>🩹 기다리는 청구 (${pend.length})</h3>${pend.map(x=>{ const p=c.ins.plans.find(y=>y.id===c.ins.members[x.sid]);
    return `<div class="item"><div class="grow"><b>${esc(stuName(x.sid))}</b> · ${esc(x.reason)}<div class="meta">${fdate(x.date)} · ${p?`보험금 ${won(p.coverage)}`:'가입 해지됨'}</div></div><button class="btn sm mint" onclick="decideClaim('${x.id}',1)">지급</button><button class="btn sm sub" onclick="decideClaim('${x.id}',0)">거절</button></div>`; }).join('')||'<p class="empty">청구가 없어요</p>'}</div>
  <div class="card"><h3>📜 처리한 기록</h3>${done.map(x=>`<div class="item"><div class="grow">${esc(stuName(x.sid))} · ${esc(x.reason)}</div><span class="status st-${x.status}">${STATUS[x.status]}</span></div>`).join('')||'<p class="empty">기록이 없어요</p>'}</div>`;
}
function decideClaim(id,ok){
  if(guard()) return;
  const c=C(), x=c.ins.claims.find(y=>y.id===id), s=stuById(x.sid), p=c.ins.plans.find(y=>y.id===c.ins.members[x.sid]);
  if(ok){ if(!s||!p) return toast('가입 정보가 없어요'); addTx(s,p.coverage,'보험금',p.name); c.ins.fund-=p.coverage; }
  x.status=ok?'approved':'rejected'; save(); render(); toast(ok?'보험금을 지급했어요 🏥':'거절했어요');
}

/* =========================================================
   💳 신용평가원
   ========================================================= */
function appCredit(){
  if(T()) return tabs([['list','📋 학생 신용'],['rule','⚙️ 자동 규칙·설정'],['item','✍️ 직접 주는 항목'],['log','📜 기록']]) + ({list:crList, rule:crRules, item:crItems, log:()=>crLog(null)}[S.tab])();
  return tabs([['mine','💳 내 신용'],['rule','📋 신용 규칙']]) + (S.tab==='mine'?crMine(me()):crRuleView());
}
function gradeBoxes(g){ return `<div class="grade-boxes">${[1,2,3,4,5,6,7,8,9,10].map(i=>`<div class="gb ${i===g?'on':''}">${i}</div>`).join('')}</div>`; }
function crMine(s){
  return `<div class="card hero center"><div class="sub">나의 신용 등급</div><div class="money-big">${grade(s)}등급</div>
    <div class="sub">신용 점수 ${s.credit}점 / ${creditMax()}점</div>${gradeBoxes(grade(s))}<div class="sub">1등급이 가장 좋아요 ✨</div></div>` + crLog(s.id);
}
function crRuleView(){
  const c=C(), on=c.creditRules.filter(r=>r.on);
  const line=(pts,txt,auto)=>`<div class="item"><span class="emo">${pts>0?'⬆️':'⬇️'}</span><div class="grow">${esc(txt)}${auto?' <span class="chip mint" style="margin:0">자동</span>':''}</div><b class="${pts>0?'plus':'minus'} nowrap">${pts>0?'+':''}${pts}점</b></div>`;
  return `<div class="card"><h3>⬆️ 점수가 오르는 경우</h3>${on.filter(r=>r.pts>0).map(r=>line(r.pts,RULE_TEXT[r.id](r),1)).join('')}${c.creditItems.filter(i=>i.pts>0).map(i=>line(i.pts,i.label)).join('')||''}</div>
    <div class="card"><h3>⬇️ 점수가 내려가는 경우</h3>${on.filter(r=>r.pts<0).map(r=>line(r.pts,RULE_TEXT[r.id](r),1)).join('')}${c.creditItems.filter(i=>i.pts<0).map(i=>line(i.pts,i.label)).join('')}</div>
    <p class="sub center">'자동'은 조건을 채우면 저절로 바뀌고, 나머지는 선생님이 직접 정해 줘요. 만점은 ${creditMax()}점이에요.</p>`;
}
function crList(){
  const c=C();
  return `<div class="card"><h3>🎯 선택한 학생 점수 바꾸기</h3>
    <div class="row"><select id="crItem" class="grow" onchange="const o=this.selectedOptions[0];if(o.value){$('crAmt').value=o.dataset.p;$('crWhy').value=o.dataset.l;}">
      <option value="">직접 입력하기</option>${c.creditItems.map(i=>`<option value="${i.id}" data-p="${i.pts}" data-l="${esc(i.label)}">${esc(i.label)} (${i.pts>0?'+':''}${i.pts})</option>`).join('')}</select></div>
    <div class="row mt"><div style="width:110px"><label class="f">점수 (+/−)</label><input id="crAmt" type="number" value="5"></div><div class="grow"><label class="f">이유</label><input id="crWhy" placeholder="예: 발표를 잘했어요"></div></div>
    <div class="row end mt"><button class="btn sm sub" onclick="document.querySelectorAll('[id^=crs_]').forEach(x=>x.checked=true)">전체 선택</button><button class="btn" onclick="crApply()">✅ 체크한 학생에게 적용</button></div></div>
  <div class="card"><div class="tbl-wrap"><table class="t"><tr><th></th><th>번호</th><th>이름</th><th class="r">점수</th><th>등급</th><th>빠른 조정</th></tr>
    ${sorted().map(s=>`<tr><td><input type="checkbox" id="crs_${s.id}"></td><td>${s.num}</td><td>${esc(s.name)}</td><td class="r">${s.credit} / ${creditMax()}</td><td><b>${grade(s)}등급</b></td>
      <td class="nowrap"><button class="btn sm danger" onclick="crQuick('${s.id}',-1)">−</button> <button class="btn sm mint" onclick="crQuick('${s.id}',1)">+</button></td></tr>`).join('')||'<tr><td colspan="6" class="empty">학생이 없어요</td></tr>'}
  </table></div><p class="sub">[−][+]는 위의 '점수' 칸 숫자만큼 바로 바꿔요.</p></div>`;
}
function crQuick(sid,d){
  if(guard()) return;
  const n=Math.abs(num(val('crAmt')))||1, s=stuById(sid);
  addCredit(s, d*n, val('crWhy')||'선생님이 직접 조정'); save(); render(); toast(`${s.name} ${d>0?'+':'−'}${n}점`);
}
function crApply(){
  if(guard()) return;
  const n=num(val('crAmt')), why=val('crWhy')||'선생님이 직접 조정';
  if(!n) return toast('점수를 입력하세요');
  const list=C().students.filter(s=>{ const e=$('crs_'+s.id); return e&&e.checked; });
  if(!list.length) return toast('학생을 체크하세요');
  list.forEach(s=>addCredit(s,n,why)); save(); render(); toast(`${list.length}명에게 적용했어요 💳`);
}
function crRules(){
  const c=C(), cfg=c.creditCfg;
  const row=r=>`<div class="item"><input type="checkbox" id="ron_${r.id}" ${r.on?'checked':''}><div class="grow">
      ${r.n?RULE_TEXT[r.id]({n:`<input class="sm num" style="width:62px" id="rn_${r.id}" type="number" min="1" value="${r.n}">`}):RULE_TEXT[r.id](r)}</div>
      <input class="sm num" style="width:76px" id="rp_${r.id}" type="number" value="${r.pts}"><span class="sub">점</span></div>`;
  return `<div class="card"><h3>⚙️ 기본 설정</h3>
    <div class="row"><div class="grow"><label class="f">신용 점수 만점</label><input id="cfMax" type="number" min="10" value="${cfg.max}"></div>
    <div class="grow"><label class="f">새 학생의 처음 점수</label><input id="cfStart" type="number" min="0" value="${cfg.start}"></div></div>
    <p class="sub">만점의 10%마다 1등급씩 나뉘어요. (만점 ${cfg.max}점이면 ${Math.round(cfg.max*0.9)}점 넘으면 1등급)</p>
    <div class="row"><input id="cfAll" class="grow" type="number" min="0" placeholder="모든 학생 점수를 몇 점으로?"><button class="btn sm sub" onclick="crSetAll()">모든 학생 일괄 설정</button></div></div>
  <div class="card"><h3>🤖 자동 규칙</h3><p class="sub">체크한 규칙만 작동해요. 조건이 채워지면 점수가 저절로 바뀌어요. 숫자는 마음대로 바꿀 수 있어요.</p>
    <b class="jua">⬆️ 오르는 경우</b>${c.creditRules.filter(r=>r.up).map(row).join('')}
    <b class="jua" style="display:block;margin-top:12px">⬇️ 내려가는 경우</b>${c.creditRules.filter(r=>!r.up).map(row).join('')}
    <div class="row end mt"><button class="btn" onclick="crSaveRules()">💾 설정 저장</button></div></div>`;
}
function crSaveRules(){
  if(guard()) return;
  const c=C(), mx=Math.max(10,num(val('cfMax')));
  c.creditCfg.max=mx; c.creditCfg.start=Math.min(mx,Math.max(0,num(val('cfStart'))));
  c.creditRules.forEach(r=>{ r.on=$('ron_'+r.id).checked; r.pts=num(val('rp_'+r.id)); if($('rn_'+r.id)) r.n=Math.max(1,num(val('rn_'+r.id))); });
  c.students.forEach(s=>{ if(s.credit>mx) s.credit=mx; });
  save(); render(); toast('저장했어요 ✅');
}
function crSetAll(){
  const v=val('cfAll'); if(v==='') return toast('점수를 입력하세요');
  const n=Math.min(creditMax(),Math.max(0,num(v)));
  ask(`모든 학생의 신용 점수를 <b>${n}점</b>으로 바꿀까요?`, ()=>{ C().students.forEach(s=>addCredit(s, n-s.credit, '선생님 일괄 설정')); save(); render(); toast('모두 바꿨어요'); });
}
function crItems(){
  const c=C();
  return `<div class="card"><h3>✍️ 선생님이 직접 주는 항목</h3><p class="sub">자동으로 알 수 없는 일(발표, 도움, 약속 등)은 여기에 항목을 만들어 두고 [학생 신용] 탭에서 골라 적용해요. 학생들도 목록을 볼 수 있어요.</p>
    ${c.creditItems.map(i=>`<div class="item"><span class="emo">${i.pts>0?'⬆️':'⬇️'}</span><div class="grow">${esc(i.label)}</div><b class="${i.pts>0?'plus':'minus'}">${i.pts>0?'+':''}${i.pts}점</b><button class="btn sm danger" onclick="crDelItem('${i.id}')">삭제</button></div>`).join('')||'<p class="empty">항목이 없어요</p>'}
    <div class="row mt"><input id="ciL" class="grow" placeholder="예: 숙제를 빠짐없이 냈어요"><input id="ciP" class="sm num" type="number" value="3"><button class="btn" onclick="crAddItem()">추가</button></div>
    <p class="sub">내려가는 항목은 점수에 −를 붙여요. (예: −5)</p></div>`;
}
function crAddItem(){ if(guard()) return; const l=val('ciL'), p=num(val('ciP')); if(!l||!p) return toast('내용과 점수를 입력하세요'); C().creditItems.push({id:uid(), label:l, pts:p}); save(); render(); }
function crDelItem(id){ if(guard()) return; const c=C(); c.creditItems=c.creditItems.filter(i=>i.id!==id); save(); render(); }
function crLog(sid){
  const list=C().creditLog.filter(l=>!sid||l.sid===sid).slice(0,80);
  return `<div class="card"><h3>📜 신용 점수 기록</h3>${list.map(l=>`<div class="item"><div class="grow">${sid?'':`<b>${esc(stuName(l.sid))}</b> · `}${esc(l.reason)}<div class="meta">${fdate(l.date)}</div></div><b class="${l.delta>0?'plus':'minus'} nowrap">${l.delta>0?'+':''}${l.delta}점</b></div>`).join('')||'<p class="empty">아직 기록이 없어요</p>'}</div>`;
}

/* =========================================================
   👥 학생 관리 (선생님)
   ========================================================= */
function appStudents(){
  const c=C();
  return `<div class="two"><div class="card"><h3>➕ 학생 한 명 추가</h3>
    <div class="row"><div style="width:90px"><label class="f">번호</label><input id="nsN" type="number" value="${(c.students.reduce((m,s)=>Math.max(m,s.num),0))+1}"></div><div class="grow"><label class="f">이름</label><input id="nsName"></div></div>
    <div class="row"><div class="grow"><label class="f">첫 비밀번호</label><input id="nsPin" inputmode="numeric" maxlength="4" value="1004"></div>
    <div class="grow"><label class="f">첫 신용 점수</label><input id="nsCr" type="number" min="0" max="${c.creditCfg.max}" value="${c.creditCfg.start}"></div></div>
    <div class="row end mt"><button class="btn" onclick="addStudent()">추가</button></div></div>
    <div class="card"><h3>📋 여러 명 한꺼번에</h3><textarea id="bulk" rows="5" placeholder="한 줄에 한 명씩&#10;1 김하늘&#10;2 이바다"></textarea>
    <label class="f">모두의 첫 신용 점수 (만점 ${c.creditCfg.max}점)</label><input id="bulkCr" type="number" min="0" max="${c.creditCfg.max}" value="${c.creditCfg.start}">
    <p class="sub">🔑 첫 비밀번호는 모두 <b>1004</b>예요. 🏥 기본 건강보험에 자동으로 가입돼요.</p><div class="row end"><button class="btn" onclick="bulkAdd()">모두 추가</button></div></div></div>
  <div class="card mt"><div class="row between"><h3>👥 학생 목록 (${c.students.length}명)</h3><button class="btn sm sub" onclick="showPins()">🔑 비밀번호 목록</button></div>
  <div class="tbl-wrap"><table class="t"><tr><th>번호</th><th>이름</th><th>직업</th><th class="r">잔액</th><th>신용</th><th></th></tr>
  ${sorted().map(s=>`<tr><td>${s.num}</td><td><b>${esc(s.name)}</b></td><td><select class="sm" onchange="setJob('${s.id}',this.value)"><option value="">무직</option>${c.jobs.map(j=>`<option value="${j.id}" ${s.jobId===j.id?'selected':''}>${esc(j.emoji+' '+j.name)}</option>`).join('')}</select></td>
   <td class="r">${won(s.balance)}</td><td>${grade(s)}등급</td><td class="nowrap"><button class="btn sm sub" onclick="editStudent('${s.id}')">수정</button> <button class="btn sm sub" onclick="resetPin('${s.id}')">비번 초기화</button> <button class="btn sm danger" onclick="delStudent('${s.id}')">삭제</button></td></tr>`).join('')||'<tr><td colspan="6" class="empty">학생을 추가해 주세요</td></tr>'}
  </table></div></div>`;
}
function addStudent(){
  if(guard()) return;
  const name=val('nsName'), pin=val('nsPin')||'1004', n=num(val('nsN'));
  if(!name) return toast('이름을 입력하세요');
  if(!/^\d{4}$/.test(pin)) return toast('비밀번호는 숫자 4자리예요');
  const s=newStudent(n,name,pin,Math.min(creditMax(),Math.max(0,num(val('nsCr'))))); C().students.push(s); save(); render();
  modal('🎉 학생 추가 완료', `<p><b>${esc(name)}</b> 학생의 첫 비밀번호는</p><div class="code-show center">${s.pin}</div><p class="sub">학생에게 알려주세요. 설정에서 바꿀 수 있어요.</p>`, '');
}
function bulkAdd(){
  if(guard()) return;
  const c=C(); let next=c.students.reduce((m,s)=>Math.max(m,s.num),0)+1; const made=[];
  const cr=Math.min(creditMax(),Math.max(0,num(val('bulkCr'))));
  val('bulk').split('\n').map(l=>l.trim()).filter(Boolean).forEach(l=>{ const m=l.match(/^(\d+)[\s.,)]*(.+)$/); const n=m?num(m[1]):next; const name=(m?m[2]:l).trim(); if(!name) return; const s=newStudent(n,name,'1004',cr); c.students.push(s); made.push(s); next=Math.max(next,n)+1; });
  if(!made.length) return toast('이름을 입력하세요');
  save(); render();
  modal(`🎉 ${made.length}명 추가`, pinTable(made), '');
}
function pinTable(list){ return `<table class="t"><tr><th>번호</th><th>이름</th><th>비밀번호</th></tr>${list.map(s=>`<tr><td>${s.num}</td><td>${esc(s.name)}</td><td class="jua">${s.pin}</td></tr>`).join('')}</table>`; }
function showPins(){ modal('🔑 학생 비밀번호 목록', `<p class="sub">학생들이 보지 않도록 주의하세요.</p>${pinTable(sorted())}`, ''); }
function setJob(sid,jid){ if(guard()) return; stuById(sid).jobId=jid; save(); render(); toast('직업을 바꿨어요'); }
function editStudent(sid){
  const s=stuById(sid), c=C();
  modal(`✏️ ${esc(s.name)}`, `<div class="row"><div style="width:90px"><label class="f">번호</label><input id="esN" type="number" value="${s.num}"></div><div class="grow"><label class="f">이름</label><input id="esName" value="${esc(s.name)}"></div></div>
    <label class="f">신용 점수 (0~${creditMax()}) · 지금 ${grade(s)}등급</label><input id="esCr" type="number" min="0" max="${creditMax()}" value="${s.credit}">
    <label class="f">자격증</label>${c.certs.map(x=>`<label class="item" style="cursor:pointer;padding:6px 0"><input type="checkbox" id="esc_${x.id}" ${s.certs.includes(x.id)?'checked':''}><span class="grow">${esc(x.emoji+' '+x.name)}</span></label>`).join('')||'<p class="sub">자격증이 없어요</p>'}`,
    `<button class="btn" onclick="saveStudent('${sid}')">저장</button>`);
}
function saveStudent(sid){
  if(guard()) return;
  const s=stuById(sid), name=val('esName');
  if(!name) return toast('이름을 입력하세요');
  s.name=name; s.num=num(val('esN')); const cr=Math.max(0,Math.min(creditMax(),num(val('esCr')))); if(cr!==s.credit) addCredit(s, cr-s.credit, '선생님이 직접 수정');
  s.certs=C().certs.filter(x=>{ const e=$('esc_'+x.id); return e&&e.checked; }).map(x=>x.id);
  save(); closeModal(); render(); toast('저장했어요 ✅');
}
function resetPin(sid){
  ask('이 학생의 비밀번호를 처음 비밀번호(1004)로 되돌릴까요?', ()=>{ const s=stuById(sid); s.pin='1004'; save(); render();
    modal('🔑 비밀번호 초기화', `<p><b>${esc(s.name)}</b> 학생의 새 비밀번호는</p><div class="code-show center">${s.pin}</div>`, ''); }, '초기화');
}
function delStudent(sid){
  ask(`<b>${esc(stuName(sid))}</b> 학생 계정을 삭제할까요?<br><span class="sub">통장, 주식, 자리 정보가 모두 사라져요.</span>`, ()=>{
    const c=C(); c.students=c.students.filter(s=>s.id!==sid); c.seats.forEach(x=>{ if(x.owner===sid) x.owner=''; }); delete c.holdings[sid]; delete c.ins.members[sid];
    c.apps=c.apps.filter(a=>a.sid!==sid); c.seatReqs=c.seatReqs.filter(r=>r.sid!==sid && r.owner!==sid); c.taxBills=c.taxBills.filter(b=>b.sid!==sid);
    save(); render(); toast('삭제했어요');
  }, '삭제');
}

/* =========================================================
   📊 정부 예산·통계 (선생님)
   ========================================================= */
function appStats(){
  const c=C(), ss=c.students, n=ss.length;
  const assets=s=>s.balance+s.savings+stockValue(s.id);
  const tot=ss.reduce((a,s)=>a+assets(s),0), avg=n?Math.round(ss.reduce((a,s)=>a+s.balance,0)/n):0;
  const emp=n?Math.round(ss.filter(s=>jobOf(s)).length/n*100):0, income=c.budgetLog.filter(l=>l.amount>0).reduce((a,l)=>a+l.amount,0);
  const list=[...ss].sort((a,b)=>assets(b)-assets(a)), mx=Math.max(1,...list.map(assets));
  return `<div class="card hero"><div class="sub">🏛️ 정부 예산 (세금·임대료·마트 수입)</div><div class="money-big">${won(c.budget)}</div>
    <div class="row mt"><button class="btn" onclick="grantForm2()">🎁 전체 학생 지원금</button><button class="btn sub" onclick="spendForm()">🏗️ 예산 사용 기록</button></div></div>
  <div class="grid2" style="grid-template-columns:repeat(auto-fill,minmax(150px,1fr))">
    <div class="card stat"><div class="n">${n}명</div><div class="sub">학생 수</div></div>
    <div class="card stat"><div class="n">${emp}%</div><div class="sub">취업률</div></div>
    <div class="card stat"><div class="n">${won(avg)}</div><div class="sub">평균 잔액</div></div>
    <div class="card stat"><div class="n">${won(tot)}</div><div class="sub">학급 전체 자산</div></div>
    <div class="card stat"><div class="n">${won(income)}</div><div class="sub">정부 총 수입</div></div>
    <div class="card stat"><div class="n">${c.orders.length}건</div><div class="sub">마트 주문</div></div></div>
  <div class="two"><div class="card"><h3>💰 학생별 자산 (잔액+예금+주식)</h3>${list.map(s=>`<div class="bar-row"><span class="nm clip">${esc(s.name)}</span><div class="bt"><div class="bf" style="width:${Math.max(2,Math.round(assets(s)/mx*100))}%"></div></div><span class="vv">${won(assets(s))}</span></div>`).join('')||'<p class="empty">학생이 없어요</p>'}</div>
  <div class="card"><h3>📒 정부 예산 기록</h3>${c.budgetLog.slice(0,40).map(l=>`<div class="item"><div class="grow">${esc(l.memo)}<div class="meta">${fdate(l.date)}</div></div><b class="${l.amount>=0?'plus':'minus'}">${signed(l.amount)}</b></div>`).join('')||'<p class="empty">기록이 없어요</p>'}</div></div>`;
}
function grantForm2(){ modal('🎁 전체 학생 지원금', `<p class="sub">정부 예산에서 모든 학생에게 같은 금액을 줘요. (지금 예산 ${won(C().budget)})</p><label class="f">1인당 금액</label><input id="gA" type="number" min="1"><label class="f">사유</label><input id="gM" placeholder="예: 학급 목표 달성 축하금">`, `<button class="btn" onclick="grantAll()">지급</button>`); }
function grantAll(){
  if(guard()) return;
  const c=C(), a=num(val('gA')), m=val('gM')||'정부 지원금', tot=a*c.students.length;
  if(a<=0) return toast('금액을 입력하세요');
  if(tot>c.budget) return toast(`예산이 부족해요 (필요: ${won(tot)})`);
  c.students.forEach(s=>addTx(s,a,'지원금',m)); budgetAdd(-tot,m); save(); closeModal(); render(); toast('지원금을 줬어요 🎁');
}
function spendForm(){ modal('🏗️ 예산 사용 기록', `<p class="sub">학급 행사, 간식 파티 등에 쓴 예산을 기록해요.</p><label class="f">금액</label><input id="spA" type="number" min="1"><label class="f">어디에 썼나요?</label><input id="spM" placeholder="예: 생일 파티 간식">`, `<button class="btn" onclick="spend()">기록</button>`); }
function spend(){ if(guard()) return; const a=num(val('spA')), m=val('spM'); if(a<=0||!m) return toast('금액과 내용을 입력하세요'); budgetAdd(-a,m); save(); closeModal(); render(); toast('기록했어요'); }

/* =========================================================
   ➕ 기능 추가하기 (선생님)
   ========================================================= */
const FEATS = [
  {k:'stock', e:'📈', t:'주식시장 (증권사)', d:'학생들이 주식을 사고팔며 투자를 배워요. 증권사 직원 학생이 선생님께 받은 비밀번호로 가격을 정해요.'},
  {k:'realty', e:'🏠', t:'국토교통부 (부동산)', d:'교실 자리에 가격을 매기고, 학생들이 원하는 자리를 임대해요. 임대료는 정부 예산이 돼요.'},
];
function appFeatures(){
  const c=C();
  return FEATS.map(f=>`<div class="card feat"><div class="emo">${f.e}</div><div class="grow" style="flex:1"><div class="jua big">${f.t}</div><p class="sub" style="margin:4px 0">${f.d}</p></div>
    ${c.features[f.k]?`<div class="center"><span class="chip mint">✅ 추가됨</span><br><button class="link" onclick="toggleFeature('${f.k}')">끄기</button></div>`:`<button class="btn" onclick="toggleFeature('${f.k}')">➕ 기능 추가하기</button>`}</div>`).join('');
}
function toggleFeature(k){
  if(guard()) return;
  const c=C();
  if(c.features[k]) return ask('이 기능을 끌까요?<br><span class="sub">데이터는 남아 있어서 다시 켜면 그대로예요.</span>', ()=>{ c.features[k]=false; save(); render(); }, '끄기');
  c.features[k]=true;
  if(k==='stock' && !c.stocks.length) seedStocks(c);
  if(k==='realty'){ if(!c.seats.length || c.seats.length<c.students.length){ c.seatCfg.rows=Math.max(c.seatCfg.rows, Math.ceil(c.students.length/c.seatCfg.cols)); genSeats(c); }
    if(c.students.some(s=>!seatOf(s.id))){ const free=shuffle(c.seats.filter(x=>!x.owner)); shuffle(c.students.filter(s=>!seatOf(s.id))).forEach((s,i)=>{ if(free[i]) free[i].owner=s.id; }); c.seatRound=now(); } }
  save(); render(); toast('기능을 추가했어요! 홈 화면에 생겼어요 🎉');
}

/* =========================================================
   ⚙️ 설정
   ========================================================= */
function appSettings(){
  const p=prefs(), c=C();
  let h=`<div class="two">
  <div class="card"><h3>🔒 비밀번호 변경</h3><label class="f">지금 비밀번호</label><input id="pw0" type="password" inputmode="numeric" maxlength="4">
    <label class="f">새 비밀번호 (숫자 4자리)</label><input id="pw1" type="password" inputmode="numeric" maxlength="4"><label class="f">새 비밀번호 한 번 더</label><input id="pw2" type="password" inputmode="numeric" maxlength="4">
    <div class="row end mt"><button class="btn" onclick="changePin()">변경하기</button></div></div>
  <div class="card"><h3>🎨 화면 꾸미기</h3>
    <label class="f">화면 밝기 <b id="brv">${p.bright||100}%</b></label><input type="range" min="40" max="100" value="${p.bright||100}" oninput="setPref('bright',+this.value);$('brv').textContent=this.value+'%'">
    <label class="f">글자 크기</label><div class="row">${[['작게',14],['보통',16],['크게',18],['아주 크게',20]].map(([l,v])=>`<button class="btn sm ${(p.font||16)===v?'':'sub'}" onclick="setPref('font',${v},1)">${l}</button>`).join('')}</div>
    <label class="f">배경 테마</label><div class="row">${THEMES.map(t=>`<button class="swatch ${(p.theme||'peach')===t.k?'on':''}" style="background:${t.c}" title="${t.n}" onclick="setPref('theme','${t.k}',1)"></button>`).join('')}</div></div></div>`;
  if(T()){
    h+=`<div class="two mt">
    <div class="card"><h3>🏫 학급 정보</h3><label class="f">학급 이름</label><input id="clN" value="${esc(c.name)}">
      <label class="f">화폐 단위</label><input id="clCur" value="${esc(c.currency)}" maxlength="6" placeholder="예: 원, 미소, 별">
      <div class="row end mt"><button class="btn sub" onclick="saveClassInfo()">저장</button></div>
      <label class="f">학급 코드</label><div class="code-show">${esc(c.code)}</div>
      <div class="row"><input id="clCode" class="grow" placeholder="새 학급 코드" style="text-transform:uppercase"><button class="btn sm sub" onclick="$('clCode').value=randCode()">🎲</button><button class="btn sm" onclick="changeCode()">코드 바꾸기</button></div></div>
    <div class="card"><h3>🏷️ 앱 이름 바꾸기</h3>
      ${[['bank','은행'],['mart','마트'],['news','뉴스'],['securities','증권']].map(([k,s])=>`<label class="f">${s}</label><div class="row"><input id="an_${k}" class="grow" value="${esc(c.names[k])}" maxlength="10"><span class="jua">${s}</span></div>`).join('')}
      <div class="row end mt"><button class="btn sub" onclick="saveNames()">저장</button></div></div></div>
    <div class="card mt"><div class="row between"><h3>👥 학생 계정</h3><button class="btn sm" onclick="openApp('students')">학생 계정 만들기·관리 ➜</button></div>
      <p class="sub">학생이 비밀번호를 잊어버렸다면 [초기화]를 눌러 새 비밀번호를 알려주세요.</p>
      ${sorted().map(s=>`<div class="kv"><span>${s.num}. ${esc(s.name)}</span><button class="btn sm sub" onclick="resetPin('${s.id}')">🔑 비번 초기화</button></div>`).join('')||'<p class="empty">학생이 없어요</p>'}</div>
    <div class="card"><h3>💾 데이터 관리</h3><p class="sub">데이터는 이 기기의 브라우저에 저장돼요. 기기를 바꾸거나 기록을 지우기 전에 꼭 백업하세요.</p>
      <div class="row"><button class="btn sub" onclick="backupFile()">⬇️ 백업 파일 받기</button><button class="btn sub" onclick="backupText()">📋 백업 글자로 보기</button><button class="btn sub" onclick="restoreForm()">⬆️ 백업 불러오기</button><button class="btn danger" onclick="deleteClass()">${S.code===DEMO?'🔄 체험 학급 처음으로':'🗑 학급 삭제'}</button></div></div>`;
  }
  h+=`<div class="card mt"><button class="btn danger wide" onclick="logout()">🚪 로그아웃</button></div>`;
  return h;
}
function changePin(){
  if(guard()) return;
  const c=C(), a=val('pw0'), b=val('pw1'), d=val('pw2');
  const cur = S.role==='teacher' ? c.teacherPin : me().pin;
  if(a!==cur) return toast('지금 비밀번호가 틀렸어요');
  if(!/^\d{4}$/.test(b)) return toast('새 비밀번호는 숫자 4자리예요');
  if(b!==d) return toast('새 비밀번호가 서로 달라요');
  if(S.role==='teacher') c.teacherPin=b; else me().pin=b;
  save(); render(); toast('비밀번호를 바꿨어요 🔒');
}
function saveClassInfo(){ if(guard()) return; const c=C(), n=val('clN'); if(!n) return toast('학급 이름을 입력하세요'); c.name=n; c.currency=val('clCur')||'원'; save(); render(); toast('저장했어요 ✅'); }
function saveNames(){ if(guard()) return; const c=C(); ['bank','mart','news','securities'].forEach(k=>{ const v=val('an_'+k); if(v) c.names[k]=v; }); save(); render(); toast('이름을 바꿨어요 ✨'); }
function changeCode(){
  if(guard()) return;
  const code=val('clCode').toUpperCase().replace(/[^A-Z0-9]/g,'');
  if(S.code===DEMO) return toast('체험용 학급의 코드는 바꿀 수 없어요');
  if(code.length<3) return toast('코드는 영어·숫자 3글자 이상이에요');
  if(DB.classes[code]) return toast('이미 쓰는 코드예요');
  ask(`학급 코드를 <b>${code}</b>(으)로 바꿀까요?<br><span class="sub">학생들에게 새 코드를 알려주세요.</span>`, ()=>{ const c=C(); delete DB.classes[c.code]; c.code=code; DB.classes[code]=c; S.code=code; save(); render(); toast('학급 코드를 바꿨어요'); });
}
function backupFile(){
  C().lastBackup=now(); save(); if(S.screen==='home') render();
  const data=JSON.stringify(C(),null,1), name=`경제나라_${C().code}_${fday(now()).replace(/\./g,'-')}.json`;
  try{ const a=document.createElement('a'); a.href=URL.createObjectURL(new Blob([data],{type:'application/json'})); a.download=name; document.body.appendChild(a); a.click(); a.remove(); toast('백업 파일을 받았어요 💾'); }
  catch(e){ backupText(); }
}
function backupText(){ C().lastBackup=now(); save(); modal('📋 백업 데이터', `<p class="sub">아래 글자를 모두 복사해서 메모장 등에 저장해 두세요.</p><textarea rows="10" readonly onclick="this.select()">${esc(JSON.stringify(C()))}</textarea>`, ''); }
function restoreForm(){ modal('⬆️ 백업 불러오기', `<p class="sub">백업 파일을 고르거나, 백업 글자를 붙여 넣으세요. <b class="minus">지금 학급 데이터가 바뀌어요!</b></p><input type="file" accept=".json,application/json" onchange="readBackup(this)"><label class="f">또는 붙여넣기</label><textarea id="rsT" rows="6"></textarea>`, `<button class="btn danger" onclick="restore()">불러오기</button>`); }
function readBackup(inp){ const f=inp.files[0]; if(!f) return; const r=new FileReader(); r.onload=()=>{ $('rsT').value=r.result; toast('파일을 읽었어요. [불러오기]를 누르세요'); }; r.readAsText(f); }
function restore(){
  if(guard()) return;
  let d; try{ d=JSON.parse(val('rsT')); }catch(e){ return toast('백업 형식이 올바르지 않아요'); }
  if(!d || !Array.isArray(d.students) || !d.teacherPin) return toast('경제나라 백업이 아니에요');
  d.code=S.code; DB.classes[S.code]=fillDefaults(d); save(); closeModal(); render(); toast('불러왔어요 ✅');
}
const DEMO='SUNNY';
function ensureDemo(){ if(DB && DB.classes && !DB.classes[DEMO]){ makeDemo(); return true; } return false; }
function deleteClass(){
  if(S.code===DEMO) return ask('🌟 체험용 학급(SUNNY)은 지울 수 없어요.<br>대신 <b>처음 상태로 되돌릴까요?</b><br><span class="sub">체험하며 바꾼 내용이 모두 처음으로 돌아가요.</span>', ()=>{ delete DB.classes[DEMO]; makeDemo(); S=freshS(); render(); toast('체험용 학급을 처음 상태로 되돌렸어요 🌟'); }, '처음으로 되돌리기');
  ask('정말 이 학급을 삭제할까요?<br><b class="minus">모든 데이터가 사라지고 되돌릴 수 없어요.</b>', ()=>{ delete DB.classes[S.code]; save(); S=freshS(); render(); toast('학급을 삭제했어요'); }, '삭제');
}

/* =========================================================
   시작
   ========================================================= */
(function init(){
  try{ DB=JSON.parse(lsGet(STORE)||'null'); }catch(e){ DB=null; }
  if(!DB || !DB.classes) DB={classes:{}};
  try{ if(navigator.storage && navigator.storage.persist) navigator.storage.persist(); }catch(e){}
  ensureDemo();
  Object.values(DB.classes).forEach(fillDefaults);
  try{ const ss=sessionStorage.getItem('ce_session'); if(ss) S=Object.assign(freshS(), JSON.parse(ss)); }catch(e){}
  S.pin='';
  if(S.screen==='pin') S.screen = S.code ? 'role' : 'code';
  document.addEventListener('keydown', e=>{
    if(S.screen!=='pin' || $('modal-root').innerHTML) return;
    if(/^[0-9]$/.test(e.key)) pinKey(e.key);
    else if(e.key==='Backspace') pinKey('←');
  });
  render();
  syncStart();
})();
</script>
</body>
</html>
"""


def _secret(name, default=""):
    try:
        v = st.secrets.get(name, None)
        if v:
            return str(v)
    except Exception:
        pass
    return os.environ.get(name, default)


class Store:
    """모든 기기가 함께 쓰는 학급 데이터 (서버 메모리 + 깃허브 자동 저장)."""

    SAVE_EVERY = 15  # 초

    def __init__(self):
        self.lock = threading.Lock()
        self.db_json = '{"classes":{}}'
        self.ver = 0
        self.fresh = True
        self.seen, self.acc = {}, {}
        self.dirty = False
        self.sha = None
        self.err = ""
        invisible = dict.fromkeys(map(ord, "​‌‍﻿ \"'“”‘’<>"), None)
        self.token = _secret("GITHUB_TOKEN").translate(invisible).strip()
        repo = _secret("GITHUB_REPO").translate(invisible).strip()
        for prefix in ("https://", "http://", "github.com/", "www.github.com/"):
            if repo.lower().startswith(prefix):
                repo = repo[len(prefix):]
        if repo.endswith(".git"):
            repo = repo[:-4]
        self.repo = repo.strip("/")
        self.path = _secret("GITHUB_PATH", "class_economy_data.json").strip()
        self.api = _secret("GITHUB_API", "https://api.github.com").rstrip("/")
        self.mode = "github" if (self.token and self.repo) else "memory"
        self.ready = self.mode == "memory"
        if self.mode == "github":
            threading.Thread(target=self._loop, daemon=True).start()

    # ---------- 깃허브 ----------
    def _http(self, method, url, body=None, accept="application/vnd.github+json"):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {
            "Authorization": "Bearer " + self.token,
            "Accept": accept,
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "class-economy-app",
        }
        if data is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read()

    def _file_url(self):
        return "%s/repos/%s/contents/%s" % (self.api, self.repo, urllib.parse.quote(self.path))

    def _check_settings(self):
        if not self.token.isascii() or " " in self.token:
            return "GITHUB_TOKEN에 한글·띄어쓰기·특수문자가 섞여 있어요. 따옴표 안에 github_pat_로 시작하는 토큰만 넣어 주세요."
        if not self.token.startswith(("github_pat_", "ghp_")):
            return "GITHUB_TOKEN이 github_pat_로 시작하지 않아요. 토큰을 다시 복사해 넣어 주세요."
        if not self.repo.isascii() or self.repo.count("/") != 1:
            return "GITHUB_REPO는 '아이디/저장소이름' 형태여야 해요. 예: Hye-um/class-economy-data"
        return ""

    def _load(self):
        bad = self._check_settings()
        if bad:
            self.err = bad
            return False
        try:
            self._http("GET", "%s/repos/%s" % (self.api, self.repo))
        except urllib.error.HTTPError as e:
            if e.code == 401:
                self.err = "깃허브 토큰이 올바르지 않거나 만료됐어요. 새 토큰을 Secrets에 넣어 주세요."
            elif e.code in (403, 404):
                self.err = "깃허브 저장소(%s)를 찾을 수 없어요. 저장소 이름과 토큰 권한을 확인해 주세요." % self.repo
            else:
                self.err = "깃허브 오류 %s" % e.code
            return False
        except Exception as e:
            self.err = "깃허브에 연결할 수 없어요 (%s)" % e.__class__.__name__
            return False
        try:
            meta = json.loads(self._http("GET", self._file_url()))
            raw = self._http("GET", self._file_url(), accept="application/vnd.github.raw")
            db = json.loads(raw.decode("utf-8"))
            if not isinstance(db, dict) or not isinstance(db.get("classes"), dict):
                raise ValueError("bad data")
            with self.lock:
                self.sha = meta.get("sha")
                self.db_json = json.dumps(db, ensure_ascii=False, separators=(",", ":"))
                self.ver, self.fresh, self.ready, self.err = 1, False, True, ""
        except urllib.error.HTTPError as e:
            if e.code != 404:
                self.err = "데이터 파일을 읽지 못했어요 (오류 %s)" % e.code
                return False
            with self.lock:  # 아직 데이터 파일이 없음 → 처음 시작
                self.sha, self.ready, self.fresh, self.err = None, True, True, ""
        except Exception as e:
            self.err = "데이터 파일을 읽지 못했어요 (%s)" % e.__class__.__name__
            return False
        return True

    def _push(self):
        with self.lock:
            if not self.dirty:
                return
            body, self.dirty = self.db_json, False
        payload = {
            "message": "학급 데이터 자동 저장",
            "content": base64.b64encode(body.encode("utf-8")).decode("ascii"),
        }
        for attempt in range(2):
            if self.sha:
                payload["sha"] = self.sha
            else:
                payload.pop("sha", None)
            try:
                res = json.loads(self._http("PUT", self._file_url(), payload))
                self.sha = (res.get("content") or {}).get("sha")
                self.err = ""
                return
            except urllib.error.HTTPError as e:
                if e.code in (409, 422) and attempt == 0:
                    try:
                        self.sha = json.loads(self._http("GET", self._file_url())).get("sha")
                    except urllib.error.HTTPError as e2:
                        if e2.code == 404:
                            self.sha = None
                    except Exception:
                        pass
                    continue
                self.err = "온라인 저장에 실패했어요 (오류 %s)" % e.code
            except Exception as e:
                self.err = "온라인 저장에 실패했어요 (%s)" % e.__class__.__name__
            break
        with self.lock:
            self.dirty = True  # 다음에 다시 시도

    def _loop(self):
        while True:
            try:
                if not self.ready:
                    if not self._load():
                        time.sleep(10)
                        continue
                self._push()
            except Exception as e:
                self.err = "저장 오류 (%s)" % e.__class__.__name__
            time.sleep(self.SAVE_EVERY)

    # ---------- 기기와 주고받기 ----------
    def handle(self, msg):
        msg = msg if isinstance(msg, dict) else {}
        cid = str(msg.get("cid") or "")[:64]
        with self.lock:
            sv = msg.get("save")
            if self.ready and cid and isinstance(sv, dict):
                try:
                    seq, base = int(sv.get("seq", 0)), int(sv.get("base", -1))
                except (TypeError, ValueError):
                    seq, base = 0, -1
                if seq > self.seen.get(cid, 0):
                    self.seen[cid] = seq
                    db = sv.get("db")
                    if base == self.ver and isinstance(db, dict) and isinstance(db.get("classes"), dict):
                        self.db_json = json.dumps(db, ensure_ascii=False, separators=(",", ":"))
                        self.ver += 1
                        self.fresh = False
                        self.acc[cid] = seq
                        self.dirty = True
            out = {
                "ready": self.ready, "ver": self.ver, "fresh": self.fresh,
                "storage": self.mode, "err": self.err,
                "seen": self.seen.get(cid, 0), "acc": self.acc.get(cid, 0),
            }
            if self.ready and msg.get("baseVer") != self.ver:
                out["db"] = self.db_json
        return out


@st.cache_resource
def get_store():
    return Store()


@st.cache_resource
def get_component():
    folder = os.path.join(
        tempfile.gettempdir(),
        "class_economy_" + hashlib.md5(APP_HTML.encode("utf-8")).hexdigest()[:10],
    )
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "index.html"), "w", encoding="utf-8") as f:
        f.write(APP_HTML)
    return components.declare_component("class_economy", path=folder)


store = get_store()
economy = get_component()
economy(sync=store.handle(st.session_state.get("economy")), key="economy", default=None)
