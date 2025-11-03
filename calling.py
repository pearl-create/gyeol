# -*- coding: utf-8 -*-
import os
import time
import queue
import av
import numpy as np
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase

from tflite_support.task import audio as audio_task
from tflite_support.task import core as core_task

MODEL_PATH = "soundclassifier_with_metadata.tflite"
LABELS_PATH = "labels.txt"

st.set_page_config(
    page_title="Meet-Style Profanity Monitor",
    page_icon="🎙️",
    layout="wide",
)

# ====== 스타일 (Meet 느낌) ======
st.markdown("""
<style>
:root{
  --bg:#0b0f14; --panel:#121820; --card:#1b2430; --text:#e9eef5; --muted:#9fb3c8; --accent:#5b9bff;
  --danger:#ff4d4f; --ok:#28c76f;
}
.stApp { background: linear-gradient(135deg,#0b0f14,#121820); color: var(--text); }
.block-container { padding-top: 0 !important; }
.meet-top { display:flex; justify-content:space-between; align-items:center; padding:10px 16px; background:rgba(0,0,0,.35); border-bottom:1px solid rgba(255,255,255,.08); border-radius:12px; }
.badge { background:rgba(255,255,255,.08); padding:6px 10px; border-radius:12px; font-size:12px; color:var(--muted); margin-right:8px;}
.room { font-weight:600; letter-spacing:.3px }
.stage { position:relative; height:65vh; background:#000; border-radius:18px; border:1px solid rgba(255,255,255,.08); overflow:hidden; box-shadow:0 10px 30px rgba(0,0,0,.35); }
.tm-mini {
  position:absolute; right:14px; bottom:14px; width:320px; background:var(--card);
  border:1px solid rgba(255,255,255,.12); border-radius:16px; box-shadow: 0 8px 24px rgba(0,0,0,.45); overflow:hidden; z-index:10;
}
.tm-head{ display:flex; align-items:center; justify-content:space-between; padding:8px 10px; background:rgba(0,0,0,.3); border-bottom:1px solid rgba(255,255,255,.08); }
.tm-body{ padding:10px; max-height:220px; overflow:auto;}
.row{ display:grid; grid-template-columns: 1fr 64px; gap:8px; align-items:center; margin:10px 0;}
.row label{ font-size:13px; color:#cfe0f5;}
.row .pct{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size:12px; color:#a8c3e8; text-align:right}
.bar{ height:8px; background:rgba(255,255,255,.1); border-radius:6px; overflow:hidden; }
.bar > span{ display:block; height:100%; width:0%; background:linear-gradient(90deg,var(--accent),#72ffa5); transition: width .2s ease; }
.tm-foot{ display:flex; align-items:center; justify-content:space-between; gap:8px; padding:8px 10px; border-top:1px solid rgba(255,255,255,.08); background:rgba(0,0,0,.25); font-size:12px; color:var(--muted) }
.dot{ width:8px; height:8px; border-radius:50%; display:inline-block; margin-right:6px; background:var(--danger)}
.dot.on{ background:var(--ok)}
.alert { background: rgba(255,77,79,.15); border:1px solid rgba(255,77,79,.4); color:#ffb3b3; padding:6px 10px; border-radius:10px; font-size:13px; margin-bottom:8px;}
</style>
""", unsafe_allow_html=True)

# ====== 상단 바 ======
st.markdown("""
<div class="meet-top">
  <div>
    <span class="badge">🔒 보호된 회의</span>
    <span class="room">회의: demo-room</span>
  </div>
  <div><span class="badge">미리보기</span></div>
</div>
""", unsafe_allow_html=True)

left, right = st.columns([3, 1])

with left:
    st.markdown('<div class="stage" id="stage">', unsafe_allow_html=True)
    stage_placeholder = st.empty()

    # 우하단 TM 박스
    tm_head = st.markdown("""
    <div class="tm-mini" id="tmBox">
      <div class="tm-head">
        <b>Teachable Machine — Live Preview</b>
        <span id="micBtn">🎙️ 마이크</span>
      </div>
      <div class="tm-body" id="tmBody">
        <div style="color:#9fb3c8; font-size:13px; line-height:1.4">
          아래 '마이크 시작'을 누르면 실시간으로 분류 결과가 표시됩니다.<br/>
          (브라우저 권한 허용 필요)
        </div>
      </div>
      <div class="tm-foot">
        <div><span class="dot" id="micDot"></span><span id="micLabel">마이크 꺼짐</span></div>
        <div id="modelStatus">모델: 로드 대기</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

with right:
    st.subheader("설정")
    prob_threshold = st.slider("경고 임계치(%)", 0, 100, 85, 1)
    target_labels_input = st.tags_input("경고 대상 레이블", ["아이씨", "깔라만씨", "수박씨"])
    st.caption("위 레이블 중 하나가 임계치 이상일 때 경고를 띄웁니다.")

# ====== 오디오 분류기 래퍼 ======
class TMClassifier:
    def __init__(self, model_path: str, score_threshold: float = 0.0):
        base_options = core_task.BaseOptions(file_name=model_path)
        classifier_options = audio_task.AudioClassifierOptions(
            base_options=base_options,
            score_threshold=score_threshold,  # 0.0으로 두고 Streamlit에서 후처리
            max_results=5
        )
        self.classifier = audio_task.AudioClassifier.create_from_file_and_options(
            model_path, classifier_options
        )
        self.input_tensor_spec = self.classifier.create_input_tensor_audio_format()
        self.recorder = audio_task.AudioRecord.create(
            self.input_tensor_spec, self.input_tensor_spec.sample_rate
        )

    def classify_pcm(self, pcm16_mono: np.ndarray):
        """
        pcm16_mono: shape (N,), dtype=int16
        """
        # tflite-support의 AudioTensor 생성
        audio_data = audio_task.AudioData.create_from_array(
            pcm16_mono, self.input_tensor_spec
        )
        result = self.classifier.classify(audio_data)
        # 결과 파싱
        if not result.classifications:
            return []
        categories = result.classifications[0].categories
        return [(c.category_name, float(c.score)) for c in categories]

# ====== 오디오 프로세서 (webrtc 콜백) ======
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.sample_rate = 16000  # webrtc가 32000/48000일 수도 있지만, tflite-support가 내부 처리
        self.block_size = 1024
        self.q = queue.Queue()
        self.enabled = True

    def recv_audio(self, frame: av.AudioFrame) -> av.AudioFrame:
        if not self.enabled:
            return frame
        # mono로 변환
        pcm = frame.to_ndarray()
        if pcm.ndim > 1:
            pcm = pcm.mean(axis=0)
        # float32 → int16
        if pcm.dtype != np.int16:
            pcm = np.clip(pcm, -1.0, 1.0)
            pcm = (pcm * 32767.0).astype(np.int16)
        self.q.put(pcm)
        return frame

# ====== 모델/상태 ======
if not os.path.exists(MODEL_PATH):
    st.error("모델 파일이 없습니다. repo 루트에 'soundclassifier_with_metadata.tflite'를 넣어주세요.")
    st.stop()

tm = TMClassifier(MODEL_PATH, score_threshold=0.0)
st.session_state.setdefault("last_scores", {})
st.session_state.setdefault("alert_texts", [])

# ====== WebRTC 시작 ======
st.markdown("### 🎙️ 마이크")
webrtc_ctx = webrtc_streamer(
    key="audio-only",
    mode=WebRtcMode.SENDRECV,
    audio_receiver_size=256,
    media_stream_constraints={"audio": True, "video": False},
)

# ====== 실시간 루프 ======
placeholder_rows = st.empty()

def render_rows(scores_dict):
    # 작은 바 UI
    body = []
    for label, p in scores_dict.items():
        pct = f"{p*100:.2f}"
        width = int(p*100)
        body.append(f"""
        <div class="row"><label>{label}</label><div class="pct">{pct}%</div></div>
        <div class="bar"><span style="width:{width}%"></span></div>
        """)
    st.markdown(
        f"""<div class="tm-body" id="tmBody">{''.join(body)}</div>""",
        unsafe_allow_html=True
    )

def render_footer(mic_on: bool, status: str):
    st.markdown(
        f"""
        <div class="tm-foot">
          <div><span class="dot {'on' if mic_on else ''}" id="micDot"></span><span id="micLabel">{'마이크 켜짐' if mic_on else '마이크 꺼짐'}</span></div>
          <div id="modelStatus">{status}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

if webrtc_ctx and webrtc_ctx.state.playing:
    st.success("마이크 수신 중")
    render_footer(True, "모델: 로드 완료")
    processor: AudioProcessor = webrtc_ctx.audio_receiver  # type: ignore
    if processor:
        while True:
            try:
                pcm = processor.q.get(timeout=0.1)
            except queue.Empty:
                break
            # 분류
            results = tm.classify_pcm(pcm)
            # dict로 정리
            scores = {label: score for label, score in results}
            st.session_state["last_scores"] = scores
            # 경고 로직
            alerts = []
            for label in target_labels_input:
                sc = scores.get(label, 0.0)
                if sc * 100 >= prob_threshold:
                    alerts.append(f"⚠️ '{label}' {sc*100:.1f}%")
            if alerts:
                st.session_state["alert_texts"] = alerts

# 결과 표시(우하단 미니박스)
scores = st.session_state.get("last_scores", {})
if scores:
    render_rows(scores)
else:
    st.caption("TM 결과 대기 중…")

# 경고
alerts = st.session_state.get("alert_texts", [])
for a in alerts[-3:]:   # 최근 3개만
    st.markdown(f'<div class="alert">{a}</div>', unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)  # .stage 닫기
