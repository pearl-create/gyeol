# home.py — 결(結) 랜딩 (AI 감성 배경 + 초거대 중앙 버튼)
from pathlib import Path
import streamlit as st

MENTOR_URL = "https://appapppy-qcagtlkwzwevbmcmwc56rw.streamlit.app/"
MENTEE_URL = "https://37mokmtxhvt8uxwgdamw7y.streamlit.app/"

st.set_page_config(page_title="결(結) — Home", page_icon="✨", layout="centered")

# ===================== CSS =====================
st.markdown("""
<style>
/* 🪶 배경: AI 감성 (은은한 그라데이션 + 빛 효과) */
html, body, [class^="block-container"] {
  height: 100%;
  margin: 0;
  padding: 0;
  background: radial-gradient(circle at 20% 30%, #E9ECF8 0%, #F3F6FA 25%, #C7D2F0 65%, #A9B6E6 100%);
  background-attachment: fixed;
  color: #1a1a1a;
}

/* 중앙 정렬 */
.main {
  display: flex;
  flex-direction: column;
  justify-content: center;   /* 세로 중앙 */
  align-items: center;       /* 가로 중앙 */
  height: 100vh;             /* 화면 전체 높이 */
  text-align: center;
}

/* 로고 애니메이션 */
@keyframes popIn {
  0% { transform: scale(0.8); opacity: 0; filter: blur(5px); }
  60% { transform: scale(1.05); opacity: 1; filter: blur(0); }
  100% { transform: scale(1); }
}
.logo-wrap {
  display: flex;
  justify-content: center;
  margin-bottom: 3rem;
  animation: popIn 1s cubic-bezier(.2,.9,.2,1) both;
}
.logo-wrap img {
  width: min(600px, 85vw);
  max-width: 700px;
}

/* 부제 */
.subtitle {
  font-size: 3rem;
  font-weight: 800;
  color: #0F1A3C;
  text-shadow: 0 2px 8px rgba(255,255,255,0.8);
  margin-bottom: 4rem;
  line-height: 1.5;
}

/* 버튼 전체 */
.big-btns {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3rem;
}

/* 🔹 초거대 버튼 */
.big-btn a, .big-btn button {
  display: inline-block;
  width: min(95vw, 900px) !important;    /* 🔸 폭 크게 */
  padding: 4.5rem 2.5rem !important;     /* 🔸 높이도 3배로 */
  font-size: 3.6rem !important;          /* 🔸 글자 크기도 대폭 확대 */
  font-weight: 900 !important;
  border-radius: 2.8rem !important;
  color: white !important;
  background: linear-gradient(135deg, #3A4FC4, #667DFF, #9EAFFF) !important;
  border: none !important;
  box-shadow: 0 25px 80px rgba(58, 79, 196, 0.4);
  text-align: center;
  transition: all 0.3s ease-in-out;
}
.big-btn a:hover, .big-btn button:hover {
  transform: translateY(-10px) scale(1.05);
  box-shadow: 0 35px 100px rgba(58, 79, 196, 0.55);
  background: linear-gradient(135deg, #4E65E0, #7C8FFF, #B4C0FF) !important;
}

/* 반응형 (모바일) */
@media (max-width: 480px) {
  .subtitle { font-size: 2.2rem; margin-bottom: 3rem; }
  .big-btn a, .big-btn button { font-size: 2.4rem !important; padding: 3.2rem 2rem !important; }
}
</style>
""", unsafe_allow_html=True)

# ===================== 로고 로더 =====================
def render_logo(width_px: int = 600):
    base = Path(__file__).resolve().parent
    for name in ["logo_gyeol.jpg", "logo_gyeol.png"]:
        p = base / name
        if p.is_file():
            st.markdown('<div class="logo-wrap">', unsafe_allow_html=True)
            st.image(p.read_bytes(), use_container_width=False)
            st.markdown('</div>', unsafe_allow_html=True)
            return
    # 대체 텍스트 로고
    st.markdown(f"""
    <div class="logo-wrap">
      <svg width="{width_px}" height="{int(width_px*0.25)}" viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg">
        <text x="0" y="100" fill="#3A4FC4" style="font: 900 100px 'Pretendard', sans-serif;">결</text>
        <text x="130" y="100" fill="#3A4FC4" style="font: 700 48px 'Pretendard', sans-serif;">Mentor–Mentee</text>
      </svg>
    </div>
    """, unsafe_allow_html=True)

# ===================== 본문 =====================
render_logo()

st.markdown(
    '<div class="subtitle">청춘과 지혜를 연결하다,<br><b style="color:#3A4FC4;">결(結)</b></div>',
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
