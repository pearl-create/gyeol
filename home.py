# home.py (패치)
from pathlib import Path
import streamlit as st

MENTOR_URL = "https://mentor.example.com"
MENTEE_URL = "https://mentee.example.com"

st.set_page_config(page_title="결(結) — 홈", page_icon="✨", layout="centered", initial_sidebar_state="collapsed")

# ---------------- 스타일 & 애니메이션 ----------------
st.markdown("""
<style>
.main > div { padding-top: 2.5rem; }
@keyframes popIn { 0%{transform:scale(.85);opacity:0;filter:blur(3px)}
  60%{transform:scale(1.05);opacity:1;filter:blur(0)} 100%{transform:scale(1)} }
.logo-wrap { display:flex; justify-content:center; margin-bottom:0.75rem; }
.logo-wrap img { width:min(300px,60vw); max-width:340px; animation: popIn 900ms cubic-bezier(.2,.9,.2,1) both; }
.subtitle { text-align:center; opacity:.85; margin:.25rem 0 1.5rem; }
.big-btn button, .big-btn a { width:100% !important; padding:.95rem 1.25rem !important;
  font-size:1.05rem !important; border-radius:.9rem !important; }
button[kind="secondary"] { border:1px solid rgba(0,0,0,.15) !important; }
</style>
""", unsafe_allow_html=True)

def render_logo():
    """로고를 안전하게 렌더링(경로 문제 방지). 없으면 SVG 대체."""
    base = Path(__file__).resolve().parent
    candidates = [
        base / "assets" / "logo_gyeol.png",
        base / "static" / "logo_gyeol.png",
        base.parent / "assets" / "logo_gyeol.png",  # /gyeol/assets/...
        Path("assets/logo_gyeol.png"),               # 혹시모를 CWD 기준
    ]
    for p in candidates:
        if p.is_file():
            # 바이트로 읽어 media storage 경로 이슈 회피
            data = p.read_bytes()
            st.markdown('<div class="logo-wrap">', unsafe_allow_html=True)
            st.image(data, caption=None, use_container_width=False)
            st.markdown('</div>', unsafe_allow_html=True)
            return

    # 대체: 텍스트 SVG 로고(애니메이션)
    st.markdown(
        """
        <div class="logo-wrap">
          <svg width="320" height="90" viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <style>
                @keyframes fadeUp { from { opacity:0; transform: translateY(8px) }
                                    to   { opacity:1; transform: translateY(0) } }
                .w1, .w2 { font: 700 72px 'Pretendard', system-ui, -apple-system, 'Noto Sans KR', sans-serif; }
                .w2 { font-weight: 600; }
                .anim { animation: fadeUp .8s ease-out both; }
              </style>
            </defs>
            <text x="0" y="80" class="w1 anim">결</text>
            <text x="90" y="80" class="w2 anim" style="animation-delay:.1s">Mentor–Mentee</text>
          </svg>
        </div>
        """,
        unsafe_allow_html=True,
    )

render_logo()
st.markdown('<div class="subtitle">멘토-멘티가 서로를 찾는 가장 따뜻한 방법, <b>결(結)</b></div>', unsafe_allow_html=True)

# ---------------- 버튼 ----------------
c1, c2 = st.columns(2, vertical_alignment="center")
with c1:
    st.markdown('<div class="big-btn">', unsafe_allow_html=True)
    st.link_button("👩‍🏫 멘토 버전으로 이동", MENTOR_URL)
    st.markdown('</div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="big-btn">', unsafe_allow_html=True)
    st.link_button("🧑‍🎓 멘티 버전으로 이동", MENTEE_URL)
    st.markdown('</div>', unsafe_allow_html=True)

st.write("")
st.caption("Tip: 멘토/멘티는 각각 별도 URL로 배포해 두면 전환이 깔끔해요.")
