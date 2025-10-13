# home.py (패치)
from pathlib import Path
import streamlit as st

MENTOR_URL = "https://https://appapppy-qcagtlkwzwevbmcmwc56rw.streamlit.app/"
MENTEE_URL = "https://37mokmtxhvt8uxwgdamw7y.streamlit.app/"

st.set_page_config(page_title="결 Home", page_icon="✨", layout="centered", initial_sidebar_state="collapsed")

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
        base / "logo_gyeol.jpg",
        base /"logo_gyeol.jpg",
        base.parent / "logo_gyeol.jpg",  # /gyeol/assets/...
        Path("logo_gyeol.png"),               # 혹시모를 CWD 기준
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
st.markdown('<div class="subtitle"> 청춘과 지혜를 연결하다, <b>결(結)</b></div>', unsafe_allow_html=True)

# ---------------- 버튼 ----------------
st.markdown("""
<style>
.main > div { padding-top: 2.5rem; }

@keyframes popIn {
  0% { transform: scale(.85); opacity: 0; filter: blur(3px) }
  60% { transform: scale(1.05); opacity: 1; filter: blur(0) }
  100% { transform: scale(1) }
}

.logo-wrap { display:flex; justify-content:center; margin-bottom:1rem; }
.logo-wrap img { width:min(300px,60vw); max-width:340px; animation: popIn 900ms cubic-bezier(.2,.9,.2,1) both; }

.subtitle { text-align:center; opacity:.85; margin:.25rem 0 2rem; font-size:1.05rem; }

/* 버튼 커스터마이징 */
.big-btn button, .big-btn a {
  width: 300% !important;
  padding: 1.4rem 1.6rem !important;       /* ↑ padding 확대 */
  font-size: 3rem !important;            /* ↑ 글자 크기 확대 */
  border-radius: 1.2rem !important;        /* ↑ 모서리 둥글게 */
  font-weight: 600 !important;
  box-shadow: 0 6px 15px rgba(0,0,0,0.08);
  transition: all .2s ease-in-out;
}
.big-btn button:hover, .big-btn a:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(0,0,0,0.12);
}

/* 버튼 컬러 강조 (네이비 프리미엄 톤 예시) */
div[data-testid="stLinkButton"] > a {
  background: linear-gradient(135deg, #23395B, #1A2C47) !important;
  color: white !important;
  border: none !important;
}
</style>
""", unsafe_allow_html=True)
c1, c2 = st.columns(2, vertical_alignment="center")
with c1:
    st.markdown('<div class="big-btn">', unsafe_allow_html=True)
    st.link_button("👩‍🏫 멘토 버전으로 이동", MENTOR_URL)
    st.markdown('</div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="big-btn">', unsafe_allow_html=True)
    st.link_button("🧑‍🎓 멘티 버전으로 이동", MENTEE_URL)
    st.markdown('</div>', unsafe_allow_html=True)
