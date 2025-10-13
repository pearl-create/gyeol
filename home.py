# home.py — 결(結) 랜딩 / AI 오로라 배경 + 로고 폭에 맞는 초대형 버튼
from pathlib import Path
import streamlit as st

MENTOR_URL = "https://appapppy-qcagtlkwzwevbmcmwc56rw.streamlit.app/"
MENTEE_URL = "https://37mokmtxhvt8uxwgdamw7y.streamlit.app/"

st.set_page_config(page_title="결(結) — Home", page_icon="✨", layout="centered")

# ===================== CSS =====================
st.markdown("""
<style>
/* ===== ✨ AI 오로라 배경 ===== */
.stApp, [data-testid="stAppViewContainer"] {
  background: radial-gradient(circle at 30% 30%, #14193F, #1B1F4B 25%, #10142C 60%, #080A1A 100%);
  background-size: 200% 200%;
  animation: aurora 12s ease-in-out infinite alternate;
  color: #fff;
}
@keyframes aurora {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

/* ===== 화면 정중앙 정렬 ===== */
[data-testid="stAppViewContainer"] > .main {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center; /* 수직 중앙 */
  align-items: center;     /* 수평 중앙 */
  text-align: center;
}

/* ===== 로고 ===== */
.logo-wrap {
  display: flex;
  justify-content: center;
  margin-bottom: 3rem;
  animation: popIn 1s ease-out both;
}
@keyframes popIn {
  0% { transform: scale(0.8); opacity: 0; filter: blur(6px); }
  60% { transform: scale(1.05); opacity: 1; filter: blur(0); }
  100% { transform: scale(1); }
}
.logo-wrap img {
  width: min(600px, 85vw);     /* 로고 폭 */
  max-width: 680px;            /* 최대 폭 */
}

/* ===== 부제 (슬로건) ===== */
.subtitle {
  font-size: 3rem;
  font-weight: 800;
  color: #DDE4FF;
  text-shadow: 0 4px 16px rgba(90,130,255,0.5);
  margin-bottom: 4rem;
  line-height: 1.5;
}

/* ===== 버튼 그룹 ===== */
.big-btns {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2.4rem;
}

/* ===== st.link_button 왕버튼 ===== */
div[data-testid="stLinkButton"] > a {
  display: inline-block !important;
  width: min(85vw, 600px) !important;    /* 로고 폭에 자동 맞춤 */
  padding: 3.2rem 2.2rem !important;     /* 버튼 높이 */
  font-size: 10rem !important;          /* 로고 크기에 비례한 폰트 */
  font-weight: 900 !important;
  border-radius: 2rem !important;
  color: #fff !important;
  text-align: center !important;
  background: linear-gradient(135deg, #5161E8, #7C8FFF, #A5B3FF) !important;
  border: none !important;
  box-shadow: 0 20px 60px rgba(80,100,255,0.45) !important;
  transition: all .35s ease-in-out !important;
}
div[data-testid="stLinkButton"] > a:hover {
  transform: translateY(-10px) scale(1.04);
  box-shadow: 0 30px 90px rgba(80,100,255,0.6) !important;
  background: linear-gradient(135deg, #8CA3FF, #B5C3FF, #C6D0FF) !important;
}

/* ===== 모바일 반응형 ===== */
@media (max-width: 480px) {
  .subtitle { font-size: 2.2rem; margin-bottom: 2.5rem; }
  div[data-testid="stLinkButton"] > a {
    font-size: 2.0rem !important;
    padding: 2.4rem 1.6rem !important;
    width: 90vw !important;
  }
}
</style>
""", unsafe_allow_html=True)

# ===================== 로고 렌더 =====================
def render_logo(width_px: int = 600):
    base = Path(__file__).resolve().parent
    for name in ["logo_gyeol.jpg", "logo_gyeol.png"]:
        p = base / name
        if p.is_file():
            st.markdown('<div class="logo-wrap">', unsafe_allow_html=True)
            st.image(p.read_bytes(), use_container_width=False)
            st.markdown('</div>', unsafe_allow_html=True)
            return
    st.markdown(f"""
    <div class="logo-wrap">
      <svg width="{width_px}" height="{int(width_px*0.25)}" viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg">
        <text x="0" y="100" fill="#9DAEFF" style="font: 900 100px 'Pretendard', sans-serif;">결</text>
        <text x="130" y="100" fill="#C9D4FF" style="font: 700 48px 'Pretendard', sans-serif;">Mentor–Mentee</text>
      </svg>
    </div>
    """, unsafe_allow_html=True)

# ===================== 본문 =====================
render_logo()

st.markdown(
    '<div class="subtitle">청춘과 지혜를 연결하다,<br><b style="color:#AEBBFF;">결(結)</b></div>',
    unsafe_allow_html=True
)

st.markdown('<div class="big-btns">', unsafe_allow_html=True)

st.link_button("👩‍🏫 멘토 버전으로 이동", MENTOR_URL)
st.link_button("🧑‍🎓 멘티 버전으로 이동", MENTEE_URL)

st.markdown('</div>', unsafe_allow_html=True)
