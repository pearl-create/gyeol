from pathlib import Path
import streamlit as st

MENTOR_URL = "https://appapppy-qcagtlkwzwevbmcmwc56rw.streamlit.app/"
MENTEE_URL = "https://jzrtrhjwcltrxshayj8vrv.streamlit.app/"

st.set_page_config(page_title="결(結) — Home", page_icon="✨", layout="centered")

# ===================== Consolidated CSS =====================
st.markdown("""
<style>
/* -------------------------------------------
          GLOBAL & BACKGROUND
------------------------------------------- */

/* ===== ✨ AI 오로라 배경 (Aurora Background) ===== */
.stApp, [data-testid="stAppViewContainer"] {
  /* Deep blue radial gradient */
  background: radial-gradient(circle at 30% 30%, #14193F, #1B1F4B 25%, #10142C 60%, #080A1A 100%);
  background-size: 200% 200%;
  /* Subtle, slow animation for the aurora effect */
  animation: aurora 12s ease-in-out infinite alternate;
  color: #fff;
}
@keyframes aurora {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

/* ===== 화면 정중앙 정렬 (Center Alignment) ===== */
[data-testid="stAppViewContainer"] > .main {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center; /* Vertical center */
  align-items: center;     /* Horizontal center */
  text-align: center;
}


/* -------------------------------------------
          CONTENT ELEMENTS
------------------------------------------- */

/* ===== 로고 (Logo) ===== */
.logo-wrap {
  display: flex;
  justify-content: center;
  margin-bottom: 3rem;
  /* Pop-in animation for a dramatic entry */
  animation: popIn 1s ease-out both;
}
@keyframes popIn {
  0% { transform: scale(0.8); opacity: 0; filter: blur(6px); }
  60% { transform: scale(1.05); opacity: 1; filter: blur(0); }
  100% { transform: scale(1); }
}
.logo-wrap img {
  width: min(600px, 85vw);     /* Responsive width: up to 600px or 85% viewport */
  max-width: 680px;
}

/* ===== 부제 (슬로건 / Subtitle) ===== */
.subtitle {
  font-size: 3rem;
  font-weight: 800;
  color: #DDE4FF;
  text-shadow: 0 4px 16px rgba(90,130,255,0.5);
  margin-bottom: 4rem;
  line-height: 1.5;
}

/* ===== 버튼 그룹 (Button Group) ===== */
.big-btns {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2.4rem;
}


/* -------------------------------------------
          STYLED COMPONENTS (Button Overrides)
------------------------------------------- */

/* 🔹 Streamlit Link Button Override (The Big Button) */
div[data-testid="stLinkButton"] > a {
  display: inline-block !important;
  /* Inherit responsive width from logo */
  width: min(85vw, 600px) !important;
  padding: 3.5rem 2.5rem !important;     /* Large padding for height */
  border-radius: 2rem !important;
  color: #fff !important;
  text-align: center !important;
  /* Gradient background */
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

/* 🔹 Button Text Sizing */
div[data-testid="stLinkButton"] a, 
div[data-testid="stLinkButton"] a span {
  font-size: 3rem !important;         /* Truly large font size */
  font-weight: 900 !important;
  letter-spacing: -0.02em;
  color: white !important;
}


/* -------------------------------------------
          MOBILE RESPONSIVENESS
------------------------------------------- */

@media (max-width: 480px) {
  /* Subtitle adjustment */
  .subtitle { font-size: 2.2rem; margin-bottom: 2.5rem; }

  /* Button text/height adjustment for mobile */
  div[data-testid="stLinkButton"] a {
    width: 90vw !important; /* Take up slightly more width on small screens */
    padding: 2.4rem 1.6rem !important;
  }
  div[data-testid="stLinkButton"] a,
  div[data-testid="stLinkButton"] a span {
    font-size: 2.2rem !important;
  }
}
</style>
""", unsafe_allow_html=True)


# ===================== 로고 렌더 (Logo Rendering Function) =====================
def render_logo(width_px: int = 600):
    """
    Streamlit이 동일 폴더(또는 하위 폴더)의 로고 파일을 직접 읽어 렌더링.
    GitHub repo에 logo_gyeol.png 또는 logo_gyeol.jpg가 포함되어야 함.
    """
    base = Path(__file__).resolve().parent
    logo_path = None
    logo_successfully_rendered = False

    # 파일 자동 탐색 (png > jpg 우선)
    for name in ["logo_gyeol.png", "logo_gyeol.jpg"]:
        p = base / name
        if p.is_file():
            logo_path = p
            break

    if logo_path:
        try:
            # FIX: Read image file as bytes instead of passing the string path.
            # This prevents TypeErrors when Streamlit's file serving is inconsistent.
            with open(logo_path, "rb") as f:
                image_data = f.read()
            
            st.markdown('<div class="logo-wrap">', unsafe_allow_html=True)
            st.image(image_data, use_container_width=False, width=width_px)
            st.markdown('</div>', unsafe_allow_html=True)
            logo_successfully_rendered = True
        except Exception as e:
            # If file reading or st.image still fails, fall back to SVG
            # This gracefully handles permission or IO errors.
            # st.error(f"Logo loading failed: {e}") # Debugging
            pass 

    if not logo_successfully_rendered:
        # 예비: 로고가 없을 때 SVG 대체 출력 (Fallback: SVG Text)
        st.markdown(f"""
        <div class="logo-wrap">
          <svg width="{width_px}" height="{int(width_px*0.25)}" viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" rx="18" fill="#1F2759"/>
            <text x="32" y="110" fill="#9DAEFF" style="font: 900 72px 'Pretendard', sans-serif;">결</text>
            <text x="120" y="110" fill="#C9D4FF" style="font: 700 36px 'Pretendard', sans-serif;">Mentor–Mentee</text>
          </svg>
        </div>
        """, unsafe_allow_html=True)


# ===================== 본문 (Main Content) =====================
render_logo()

st.markdown(
    '<div class="subtitle">청춘과 지혜를 연결하다,<br><b style="color:#AEBBFF;">결(結)</b></div>',
    unsafe_allow_html=True
)

st.markdown('<div class="big-btns">', unsafe_allow_html=True)

# The extra-large buttons are styled via the CSS above
st.link_button("👩‍🏫 멘토 버전으로 이동", MENTOR_URL)
st.link_button("🧑‍🎓 멘티 버전으로 이동", MENTEE_URL)

st.markdown('</div>', unsafe_allow_html=True)
