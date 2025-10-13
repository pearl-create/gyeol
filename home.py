# home.py — 결(結) 랜딩 (초대형 중앙 버튼 + 안전 로고 로더)
from pathlib import Path
import streamlit as st

# ====== 외부 URL (오타 수정: mentor는 https:// 한 번만) ======
MENTOR_URL = "https://appapppy-qcagtlkwzwevbmcmwc56rw.streamlit.app/"
MENTEE_URL = "https://37mokmtxhvt8uxwgdamw7y.streamlit.app/"

st.set_page_config(
    page_title="결(結) — Home",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ====== CSS (중앙 정렬 + 초대형 버튼 + 로고 애니메이션 + 큰 부제) ======
st.markdown("""
<style>
/* 메인 컨테이너를 화면 가운데로 */
html, body, [class^="block-container"] { height: 100%; margin: 0; padding: 0; }
.main {
  display: flex; flex-direction: column;
  justify-content: center; align-items: center;
  height: 92vh;  /* 거의 전체 화면 */
}

/* 로고 애니메이션 */
@keyframes popIn {
  0% { transform: scale(0.82); opacity: 0; filter: blur(4px); }
  60% { transform: scale(1.06); opacity: 1; filter: blur(0); }
  100% { transform: scale(1); }
}
.logo-wrap { display:flex; justify-content:center; margin-bottom: 2.2rem; animation: popIn 900ms cubic-bezier(.2,.9,.2,1) both; }
.logo-wrap img { width: min(420px, 70vw); max-width: 480px; }

/* 슬로건(부제) — 크게, 굵게 */
.subtitle {
  text-align: center;
  font-size: 2.4rem;          /* 🔸 더 키우고 싶으면 2.6~2.8rem */
  font-weight: 800;
  letter-spacing: -0.02em;
  color: rgba(0,0,0,0.88);
  margin: 0 0 3rem 0;
  line-height: 1.45;
}

/* 버튼 스택 */
.big-btns { display:flex; flex-direction:column; align-items:center; gap: 2rem; }

/* 왕버튼 */
.big-btn a, .big-btn button {
  display: inline-block;
  width: min(92vw, 560px) !important;   /* 폭 크게 */
  padding: 2.4rem 1.8rem !important;    /* 높이 크게 */
  font-size: 2.0rem !important;         /* 글자 아주 큼 */
  font-weight: 800 !important;
  border-radius: 1.9rem !important;
  color: #fff !important;
  background: linear-gradient(135deg, #1C2947, #2F4E8A) !important;
  border: none !important;
  box-shadow: 0 16px 36px rgba(0,0,0,0.18);
  text-align: center;
  transition: transform .25s ease, box-shadow .25s ease, background .25s ease;
}
.big-btn a:hover, .big-btn button:hover {
  transform: translateY(-8px) scale(1.02);
  box-shadow: 0 22px 48px rgba(0,0,0,0.22);
  background: linear-gradient(135deg, #2A3E6A, #3F64B5) !important;
}

/* 작은 화면에서 간격 보정 */
@media (max-width: 420px) {
  .subtitle { font-size: 2.1rem; margin-bottom: 2.4rem; }
  .big-btn a, .big-btn button { font-size: 1.8rem !important; padding: 2.1rem 1.6rem !important; }
}
</style>
""", unsafe_allow_html=True)

# ====== 안전 로고 로더 (루트의 logo_gyeol.{jpg,png} 탐색, 없으면 SVG 대체) ======
def render_logo(width_px: int = 460) -> None:
    base = Path(__file__).resolve().parent
    candidates = [
        base / "logo_gyeol.jpg",
        base / "logo_gyeol.png",
        base.parent / "logo_gyeol.jpg",   # 혹시 상위 폴더에 있을 때
        base.parent / "logo_gyeol.png",
        Path("logo_gyeol.jpg"),            # CWD 대비
        Path("logo_gyeol.png"),
    ]
    for p in candidates:
        if p.is_file():
            st.markdown('<div class="logo-wrap">', unsafe_allow_html=True)
            st.image(p.read_bytes(), use_container_width=False)  # 바이트로 로드(경로 이슈 회피)
            st.markdown('</div>', unsafe_allow_html=True)
            return

    # 대체 SVG (파일이 없을 때도 깔끔하게 표시)
    st.markdown(f"""
    <div class="logo-wrap">
      <svg width="{width_px}" height="{int(width_px*0.28)}" viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#1C2947"/><stop offset="1" stop-color="#2F4E8A"/>
          </linearGradient>
        </defs>
        <text x="0" y="100" fill="url(#g)" style="font: 900 96px 'Pretendard', system-ui, -apple-system, 'Noto Sans KR', sans-serif;">결</text>
        <text x="120" y="98" fill="#2F4E8A" style="font: 700 48px 'Pretendard', system-ui, -apple-system, 'Noto Sans KR', sans-serif;">Mentor–Mentee</text>
      </svg>
    </div>
    """, unsafe_allow_html=True)

# ====== 화면 구성 ======
render_logo()

st.markdown(
    '<div class="subtitle">청춘과 지혜를 연결하다, '
    '<b style="color:#2E4A7D;">결(結)</b></div>',
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
