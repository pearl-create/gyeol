# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="통화 화면 (TM 연결)", layout="centered")

st.title("📞 통화 화면 — Teachable Machine 오디오 모델 연결 데모")

# 👉 Teachable Machine 오디오 모델 URL (끝에 / 포함)
tm_base_url = st.text_input(
    "Teachable Machine 모델 URL (마지막에 `/` 포함)",
    value="https://teachablemachine.withgoogle.com/models/XXXXX/",
    help="예) https://teachablemachine.withgoogle.com/models/gSHOySjax/"
)

accent = "#5B8DEF"
danger = "#E55353"
ok = "#2EBD85"

html_code = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>통화 화면 (TM 연결)</title>
<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
<style>
  :root {{
    --accent: "{accent}";
    --danger: "{danger}";
    --ok: "{ok}";
    --bg: #0f172a;
    --card: #111827;
    --muted: #475569;
    --text: #e5e7eb;
    --text-dim: #94a3b8;
    --ring: rgba(91,141,239,0.35);
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: radial-gradient(1200px 800px at 50% -200px, #1f2937, var(--bg));
    font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
    color: var(--text);
  }}
  .wrap {{
    max-width: 520px; margin: 24px auto; padding: 12px 16px 28px;
    background: linear-gradient(180deg, rgba(17,24,39,0.9), rgba(17,24,39,0.75));
    border: 1px solid #1f2937; border-radius: 18px; box-shadow: 0 8px 40px rgba(0,0,0,.45);
  }}
  .topbar {{
    display: flex; align-items: center; justify-content: space-between; gap: 8px;
    padding: 8px 6px 16px; border-bottom: 1px solid #1f2937;
  }}
  .status-dot {{
    width: 10px; height: 10px; border-radius: 50%;
    background: #9ca3af; margin-right: 8px; box-shadow: 0 0 0 2px rgba(156,163,175,.2);
  }}
  .status.ok {{ background: var(--ok); }}
  .status.err {{ background: var(--danger); }}
  .title {{
    display:flex; align-items:center; gap:10px; font-weight:600; letter-spacing:.1px;
  }}
  .small {{ color: var(--text-dim); font-size: 12px; }}
  .avatars {{
    display:grid; grid-template-columns: 1fr 1fr; gap: 18px; padding: 24px 6px 8px;
  }}
  .avatar {{
    background: #0b1220; border: 1px solid #101828; border-radius: 18px; padding: 18px;
    display:flex; align-items:center; gap:14px; box-shadow: inset 0 0 0 1px rgba(255,255,255,.02);
  }}
  .avatar .pic {{
    width: 56px; height: 56px; border-radius: 50%;
    background: linear-gradient(135deg, #334155, #0f172a);
    border: 2px solid #1f2937; box-shadow: 0 0 0 6px rgba(59,130,246,0.05);
  }}
  .name {{ font-weight:600; }}
  .controls {{
    display:flex; align-items:center; justify-content:center; gap: 14px;
    padding: 16px 0 6px;
  }}
  button {{
    appearance:none; border:none; cursor:pointer; font-weight:600;
    padding: 12px 16px; border-radius: 14px; color:#0b1220;
    background: var(--text); transition: transform .06s ease, box-shadow .2s ease;
  }}
  button:hover {{ transform: translateY(-1px); }}
  .btn-main {{ background: var(--accent); color:#0b1220; box-shadow: 0 10px 30px var(--ring); }}
  .btn-end  {{ background: var(--danger); color: #fff; }}
  .btn-mute {{ background: #e5e7eb; }}
  .meter {{
    margin-top: 10px; width: 100%; height: 8px; background: #0b1220; border-radius: 8px; overflow: hidden;
    border: 1px solid #0f172a;
  }}
  .fill {{
    height:100%; width:0%; background: linear-gradient(90deg, var(--accent), #8b5cf6);
    transition: width .15s ease;
  }}
  .panel {{
    margin-top: 18px; padding: 14px; border-radius: 14px; background: #0b1220; border:1px solid #0f172a;
  }}
  .prob {{ display:flex; align-items:center; justify-content:space-between; gap:12px; margin:6px 0; }}
  .prob .bar {{
    flex:1; height:8px; border-radius:10px; background:#0f172a; overflow:hidden;
  }}
  .prob .bar > span {{
    display:block; height:100%; width:0%; background: linear-gradient(90deg,#22c55e,#84cc16);
    transition: width .12s ease;
  }}
  .prob .label {{ min-width: 120px; font-size:13px; color:#cbd5e1; }}
  .alert {{
    margin-top: 10px; padding: 10px 12px; border-radius: 12px; font-weight:600;
    background: rgba(229,83,83,.12); border:1px solid rgba(229,83,83,.35); color:#fecaca;
    display:none;
  }}
  .row {{
    display:flex; align-items:center; justify-content:space-between; gap:12px;
  }}
</style>
</head>
<body>
<div class="wrap">
  <div class="topbar">
    <div class="title">
      <span class="status-dot" id="statusDot"></span>
      <span>통화 연결</span>
      <span class="small" id="tmStatus">모델 준비 중…</span>
    </div>
    <div class="small" id="timer">00:00</div>
  </div>

  <div class="avatars">
    <div class="avatar">
      <div class="pic"></div>
      <div>
        <div class="name">나</div>
        <div class="small">마이크 온</div>
        <div class="meter"><div class="fill" id="vu"></div></div>
      </div>
    </div>
    <div class="avatar">
      <div class="pic"></div>
      <div>
        <div class="name">상대</div>
        <div class="small">연결됨</div>
        <div class="meter"><div class="fill" style="width:35%"></div></div>
      </div>
    </div>
  </div>

  <div class="controls">
    <button class="btn-main" id="btnStart">통화 시작</button>
    <button class="btn-mute" id="btnMute">마이크 끄기</button>
    <button class="btn-end"  id="btnEnd">통화 종료</button>
  </div>

  <div class="panel">
    <div class="row">
      <div style="font-weight:700;">실시간 감지 (Teachable Machine)</div>
      <div class="small" id="modelUrlDisp"></div>
    </div>
    <div id="probs"></div>
    <div id="alert" class="alert">⚠️ 경고: 민감·부적절 표현이 감지되었습니다.</div>
  </div>

  <audio id="localAudio" autoplay muted playsinline></audio>
</div>

<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@4"></script>
<script src="https://cdn.jsdelivr.net/npm/@teachablemachine/audio@0.8/dist/teachablemachine-audio.min.js"></script>
<script>
const TM_BASE = "{tm_base_url}";
const modelURL = TM_BASE.endsWith("/") ? TM_BASE + "model.json" : TM_BASE + "/model.json";
const metadataURL = TM_BASE.endsWith("/") ? TM_BASE + "metadata.json" : TM_BASE + "/metadata.json";

const statusDot = document.getElementById("statusDot");
const tmStatus  = document.getElementById("tmStatus");
const modelUrlDisp = document.getElementById("modelUrlDisp");
const probsWrap = document.getElementById("probs");
const alertBox = document.getElementById("alert");
const vu = document.getElementById("vu");
const audioEl = document.getElementById("localAudio");

const btnStart = document.getElementById("btnStart");
const btnEnd   = document.getElementById("btnEnd");
const btnMute  = document.getElementById("btnMute");
const timerEl  = document.getElementById("timer");

let model, maxClasses = 0;
let listening = false;
let stream, audioContext, analyser, dataArray, rafId;
let muted = false;
let startAt = 0, timerId;

const BAD_KEYWORDS = ["욕", "비속", "욕설", "offensive", "abuse", "profanity", "toxic"];

function setStatus(ok, msg) {{
  statusDot.classList.remove("ok","err");
  if (ok) statusDot.classList.add("ok");
  else statusDot.classList.add("err");
  if (msg) tmStatus.textContent = msg;
}}

function showAlert(show) {{
  alertBox.style.display = show ? "block" : "none";
}}

function updateTimer() {{
  const s = Math.floor((Date.now() - startAt) / 1000);
  const mm = String(Math.floor(s/60)).padStart(2,"0");
  const ss = String(s%60)).padStart(2,"0"); // <-- NOTE: we will fix this typo below
  timerEl.textContent = mm + ":" + ss;
}}
</script>
</body>
</html>
"""

# ↑ 위에서 JS에 괄호 실수 하나 발견(교육용 주석 남김). 바로 아래에서 올바른 코드로 다시 렌더합니다.
html_code = html_code.replace("const ss = String(s%60)).padStart(2,\"0\");", "const ss = String(s%60).padStart(2,\"0\");")

if tm_base_url.strip() == "" or "XXXXX" in tm_base_url:
    st.warning("위 입력창에 **Teachable Machine 오디오 모델 URL**을 입력하세요. (예: `https://teachablemachine.withgoogle.com/models/gSHOySjax/`)")

components.html(html_code, height=740, scrolling=False)
