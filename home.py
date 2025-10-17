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
  font-size: 50rem !important;          /* 로고 크기에 비례한 폰트 */
  font-weight: 1800 !important;
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

from pathlib import Path
import streamlit as st

# ===================== 로고 렌더 (GitHub 리포 내 파일 버전) =====================
def render_logo(width_px: int = 600):
    """
    Streamlit이 동일 폴더(또는 하위 폴더)의 로고 파일을 직접 읽어 렌더링.
    GitHub repo에 logo_gyeol.png 또는 logo_gyeol.jpg가 포함되어야 함.
    """
    base = Path(__file__).resolve().parent
    logo_path = None

    # 파일 자동 탐색 (png > jpg 우선)
    for name in ["logo_gyeol.png", "logo_gyeol.jpg"]:
        p = base / name
        if p.is_file():
            logo_path = p
            break

    if logo_path:
        st.markdown('<div class="logo-wrap">', unsafe_allow_html=True)
        st.image(str(logo_path), use_container_width=False, width=width_px)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # 예비: 로고가 없을 때 SVG 대체 출력
        st.markdown(f"""
        <div class="logo-wrap">
          <svg width="{width_px}" height="{int(width_px*0.25)}" viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" rx="18" fill="#1F2759"/>
            <text x="32" y="110" fill="#9DAEFF" style="font: 900 72px 'Pretendard', sans-serif;">결</text>
            <text x="120" y="110" fill="#C9D4FF" style="font: 700 36px 'Pretendard', sans-serif;">Mentor–Mentee</text>
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

st.markdown("""
<style>
/* 🔹 Streamlit 내부 버튼 구조 직접 타겟 */
div[data-testid="stLinkButton"] a, 
div[data-testid="stLinkButton"] a span,
div[data-testid="stButton"] button, 
div[data-testid="stButton"] button span {
  font-size: 3rem !important;         /* 🔸 진짜로 커짐 */
  font-weight: 900 !important;
  letter-spacing: -0.02em;
  color: white !important;
}

/* 🔹 버튼 전체 */
div[data-testid="stLinkButton"] > a {
  width: min(85vw, 600px) !important; 
  padding: 3.5rem 2.5rem !important;   /* 높이 크게 */
  border-radius: 2rem !important;
  background: linear-gradient(135deg, #5161E8, #7C8FFF, #A5B3FF) !important;
  box-shadow: 0 20px 60px rgba(80,100,255,0.45) !important;
  transition: all .35s ease-in-out !important;
}
div[data-testid="stLinkButton"] > a:hover {
  transform: translateY(-10px) scale(1.04);
  box-shadow: 0 30px 90px rgba(80,100,255,0.6) !important;
  background: linear-gradient(135deg, #8CA3FF, #B5C3FF, #C6D0FF) !important;
}

/* 🔹 모바일 대응 */
@media (max-width: 480px) {
  div[data-testid="stLinkButton"] a,
  div[data-testid="stLinkButton"] a span {
    font-size: 2.2rem !important;
  }
}
</style>
""", unsafe_allow_html=True)

