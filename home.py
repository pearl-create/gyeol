# home.py — 결(結) 랜딩 (정중앙 + 초초대형 버튼)
from pathlib import Path
import streamlit as st

MENTOR_URL = "https://appapppy-qcagtlkwzwevbmcmwc56rw.streamlit.app/"
MENTEE_URL = "https://37mokmtxhvt8uxwgdamw7y.streamlit.app/"

st.set_page_config(page_title="결(結) — Home", page_icon="✨", layout="centered")

# ===================== CSS =====================
st.markdown("""
<style>
html, body, [class^="block-container"] {
  height: 100%;
  margin: 0;
  padding: 0;
}

/* 중앙 정렬 (화면 정중앙) */
.main {
  display: flex;
  flex-direction: column;
  justify-content: center;   /* 수직 중앙 */
  align-items: center;       /* 수평 중앙 */
  height: 100vh;             /* 전체 화면 높이 */
  text-align: center;
}

/* 로고 */
.logo-wrap {
  display: flex;
  justify-content: center;
  animation: popIn 1s ease-in-out both;
  margin-bottom: 3rem;
}
@keyframes popIn {
  0% { transform: scale(0.8); opacity: 0; filter: blur(4px); }
  60% { transform: scale(1.05); opacity: 1; filter: blur(0); }
  100% { transform: scale(1); }
}
.logo-wrap img {
  width: min(500px, 80vw);
  max-width: 600px;
}

/* 부제 */
.subtitle {
  font-size: 2.8rem;
  font-weight: 800;
  color: rgba(0,0,0,0.88);
  margin-bottom: 4rem;
  line-height: 1.5;
}

/* 버튼 전체 래퍼 */
.big-btns {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3rem;
}

/* 🔹 초초대형 버튼 */
.big-btn a, .big-btn button {
  display: inline-block;
  width: min(95vw, 720px) !important;    /* 폭 더 넓게 */
  padding: 3.6rem 2.4rem !important;     /* 높이 3배 키움 */
  font-size: 3.2rem !important;          /* 글자 크기도 3배 */
  font-weight: 900 !important;
  border-radius: 2.2rem !important;
  color: #fff !important;
  background: linear-gradient(135deg, #1B284A, #2F4E8A) !important;
  border: none !important;
  box-shadow: 0 22px 60px rgba(0,0,0,0.25);
  text-align: center;
  transition: all 0.3s ease-in-out;
}
.big-btn a:hover, .big-btn button:hover {
  transform: translateY(-10px) scale(1.04);
  box-shadow: 0 30px 80px rgba(0,0,0,0.3);
  background: linear-gradient(135deg, #2A3E6A, #3F64B5) !important;
}

/* 모바일 반응형 */
@media (max-width: 480px) {
  .subtitle { font-size: 2.2rem; margin-bottom: 3rem; }
  .big-btn a, .big-btn button { font-size: 2.4rem !important; padding: 3rem 2rem !important; }
}
</style>
""", unsafe_allow_html=True)

# ===================== 안전 로고 로더 =====================
def render_logo(width_px: int = 520):
    base = Path(__file__).resolve().parent
    candidates = [
        base / "logo_gyeol.jpg",
        base / "logo_gyeol.png",
        Path("logo_gyeol.jpg"),
        Path("logo_gyeol.png"),
    ]
    for p in candidates:
        if p.is_file():
            st.markdown('<div class="logo-wrap">', unsafe_allow_html=True)
            st.image(p.read_bytes(), use_container_width=False)
            st.markdown('</div>', unsafe_allow_html=True)
            return
    # 없을 시 텍스트 로고
    st.markdown(f"""
    <div class="logo-wrap">
      <svg width="{width_px}" height="{int(width_px*0.25)}" viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg">
        <text x="0" y="100" fill="#2E4A7D" style="font: 900 96px 'Pretendard', sans-serif;">결</text>
        <text x="120" y="98" fill="#2E4A7D" style="font: 700 48px 'Pretendard', sans-serif;">Mentor–Mentee</text>
      </svg>
    </div>
    """, unsafe_allow_html=True)

# ===================== 본문 =====================
render_logo()

st.markdown(
    '<div class="subtitle">청춘과 지혜를 연결하다,<br><b style="color:#2E4A7D;">결(結)</b></div>',
    unsafe_allow_html=True
)

st.markdown('<div class="big-btns">', unsafe_allow_html=True)

st.markdown('<div class="big-btn">', unsafe_allow_html=True)
st.link_button("👩‍🏫 멘토 버전으로 이동", MENTOR_URL)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="big-btn">', unsafe_allow_html=True)
st.link_button("🧑‍🎓 멘티 버전으로 이동", MENTEE_URL)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
