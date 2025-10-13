# Home.py  (Streamlit 1.30+)
import streamlit as st

# -------------------------
# 설정: 각 버전의 URL 입력
# -------------------------
MENTOR_URL = "https://www.youtube.com/watch?v=Ov9AqrQW-Pk"  # 멘토 사이트 주소
MENTEE_URL = "https://37mokmtxhvt8uxwgdamw7y.streamlit.app/#98fee39c"  # 멘티 사이트 주소

st.set_page_config(
    page_title="결(結) — 홈",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ------------- 스타일 -------------
st.markdown("""
<style>
/* 전체 레이아웃 정리 */
.main > div { padding-top: 2.5rem; }

/* 로고 애니메이션 */
@keyframes popIn {
  0%   { transform: scale(0.85); opacity: 0; filter: blur(3px); }
  60%  { transform: scale(1.05); opacity: 1; filter: blur(0); }
  100% { transform: scale(1.0); }
}
.logo-wrap img {
  width: min(300px, 60vw);
  max-width: 340px;
  display:block;
  margin: 0 auto 0.75rem auto;
  animation: popIn 900ms cubic-bezier(.2,.9,.2,1) both;
}

/* 서브 타이틀 살짝 페이드 */
.subtitle {
  text-align:center;
  font-size: 0.98rem;
  opacity: 0.8;
  margin-top: 0.25rem;
  margin-bottom: 1.5rem;
}

/* 버튼을 큼직하게 */
.big-btn button, .big-btn a {
  width: 100% !important;
  padding: 0.95rem 1.25rem !important;
  font-size: 1.05rem !important;
  border-radius: 0.9rem !important;
}

/* 좌우 버튼 구분감 */
button[kind="secondary"] { border: 1px solid rgba(0,0,0,0.15) !important; }
</style>
""", unsafe_allow_html=True)

# ------------- 로고 영역 -------------
# 로고 파일이 repo에 있다면 경로만 바꿔서 st.image 사용
# e.g., st.image("assets/logo_gyeol.png")
st.markdown('<div class="logo-wrap">', unsafe_allow_html=True)
st.image("assets/logo_gyeol.png", caption=None, use_container_width=False)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="subtitle">멘토-멘티가 서로를 찾는 가장 따뜻한 방법, <b>결(結)</b></div>', unsafe_allow_html=True)

# ------------- 버튼 영역 -------------
c1, c2 = st.columns(2, vertical_alignment="center")

with c1:
    st.markdown('<div class="big-btn">', unsafe_allow_html=True)
    st.link_button("👩‍🏫 멘토 버전으로 이동", MENTOR_URL)
    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    st.markdown('<div class="big-btn">', unsafe_allow_html=True)
    st.link_button("🧑‍🎓 멘티 버전으로 이동", MENTEE_URL)
    st.markdown('</div>', unsafe_allow_html=True)

# ------------- (선택) 푸터 안내 -------------
st.write("")
st.caption("Tip: 상단 사이드바는 각 버전에서 필요 메뉴만 보이도록 구성하세요.")
