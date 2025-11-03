import streamlit as st
from streamlit.components.v1 import html

st.set_page_config(page_title="비속어 감지 화상 통화 (두 창)", layout="wide")

st.title("🗣️ 비속어 감지 화상 통화 — 두 창 분할 실행")

col_left, col_right = st.columns(2, gap="large")

with col_left:
    st.subheader("왼쪽: 카메라/마이크 데모")
    html(
        """
        <style>
          .wrap { display:flex; flex-direction:column; align-items:center; }
          video { width:100%; max-width:560px; height:auto; border-radius:16px; border:2px solid #333; background:#000; }
          .controls { margin-top:12px; display:flex; gap:10px; flex-wrap:wrap; }
          button { background:#333; color:#fff; border:none; border-radius:8px; padding:10px 16px; cursor:pointer; }
          button.muted { background:#b52d2d; }
        </style>
        <div class="wrap">
          <video id="video" autoplay playsinline muted></video>
          <div class="controls">
            <button id="camBtn">📷 카메라 켜기</button>
            <button id="micBtn">🎤 마이크 켜기</button>
            <button id="bothBtn">🧠 오른쪽에 TM 링크 열기</button>
          </div>
        </div>
        <script>
          const video = document.getElementById('video');
          const camBtn = document.getElementById('camBtn');
          const micBtn = document.getElementById('micBtn');
          const bothBtn = document.getElementById('bothBtn');
          let stream = null;
          let camOn = false;
          let micOn = false;

          async function getStream() {
            try {
              stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: micOn });
              video.srcObject = stream;
              camOn = true;
              camBtn.textContent = "📷 카메라 끄기";
            } catch (e) {
              alert("카메라/마이크 접근 실패: " + e.message);
            }
          }

          camBtn.addEventListener('click', async () => {
            if (!camOn) {
              await getStream();
            } else {
              if (stream) { stream.getTracks().forEach(t => t.stop()); }
              video.srcObject = null;
              camOn = false;
              camBtn.textContent = "📷 카메라 켜기";
            }
          });

          micBtn.addEventListener('click', async () => {
            micOn = !micOn;
            micBtn.textContent = micOn ? "🔇 음소거" : "🎤 마이크 켜기";
            micBtn.classList.toggle("muted", micOn);
            if (camOn) {
              // 오디오 설정 변경을 반영하려면 스트림 재요청
              if (stream) { stream.getTracks().forEach(t => t.stop()); }
              await getStream();
            }
          });

          bothBtn.addEventListener('click', () => {
            const url = "https://teachablemachine.withgoogle.com/models/gSHOySjax/";
            // 화면 오른쪽 절반에 TM 창 띄우기
            const w = Math.floor(window.screen.availWidth / 2);
            const h = Math.floor(window.screen.availHeight);
            window.open(url, "_blank",
              `popup=yes,width=${w},height=${h},left=${w},top=0`);
          });
        </script>
        """,
        height=520,
    )

with col_right:
    st.subheader("오른쪽: TM 링크 안내")
    st.markdown(
        """
        **버튼을 누르면 오른쪽 절반에 새 창으로 열립니다.**  
        팝업 차단이 켜져 있으면 허용해 주세요.
        
        - 모델 링크: https://teachablemachine.withgoogle.com/models/gSHOySjax/
        - *임베드가 아닌 별도 창으로 띄우는 방식입니다.*
        """
    )
