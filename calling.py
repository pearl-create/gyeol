import streamlit as st
import numpy as np
import soundfile as sf
import tempfile
import pathlib
import base64
import time

st.set_page_config(page_title="실시간 비속어 감지 데모", page_icon="🎤")

# 1) 라벨 로드
def load_labels(path: str):
    labels = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            idx, name = line.strip().split(" ", 1)
            labels[int(idx)] = name
    return labels

LABELS = load_labels("labels.txt")  # 0 깔라만씨 / 1 배경 소음 / 2 수박씨 / 3 아이씨

# 2) TFLite 로드 (tensorflow로)
import tensorflow as tf

@st.cache_resource
def load_model():
    model_path = pathlib.Path("soundclassifier_with_metadata.tflite")
    interpreter = tf.lite.Interpreter(model_path=str(model_path))
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    return interpreter, input_details, output_details

interpreter, input_details, output_details = load_model()

def classify_audio_array(audio_arr: np.ndarray):
    input_shape = input_details[0]["shape"]  # [1, N]
    req_len = input_shape[1]

    # mono로 맞추기
    if audio_arr.ndim > 1:
        audio_arr = audio_arr[:, 0]

    # 길이 맞추기
    if audio_arr.shape[0] < req_len:
        padded = np.zeros(req_len, dtype=np.float32)
        padded[:audio_arr.shape[0]] = audio_arr
        audio_arr = padded
    else:
        audio_arr = audio_arr[:req_len]

    audio_arr = np.expand_dims(audio_arr.astype(np.float32), axis=0)
    interpreter.set_tensor(input_details[0]["index"], audio_arr)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]["index"])[0]
    idx = int(np.argmax(output_data))
    label = LABELS.get(idx, f"class_{idx}")
    score = float(output_data[idx])
    return label, score

st.title("🎤 실시간 비속어 감지 (브라우저 녹음형)")
st.write("아래 버튼을 누르면 브라우저에서 1초마다 음성을 보내고, 모델이 곧바로 분류한 결과를 위에 띄워요.")
st.write("모델 라벨: 0 깔라만씨 / 1 배경 소음 / 2 수박씨 / 3 아이씨")

placeholder = st.empty()
alert_box = st.empty()

# 3) 프런트에 넣을 녹음용 JS
#    -> 1초마다 녹음해서 base64로 파이썬에 보내도록 한다
record_js = """
<script>
let mediaRecorder;
let chunks = [];
let sending = false;

async function startRecording() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);
  mediaRecorder.ondataavailable = e => {
    chunks.push(e.data);
  };
  mediaRecorder.onstop = async e => {
    const blob = new Blob(chunks, { 'type' : 'audio/webm; codecs=opus' });
    chunks = [];

    // blob -> base64
    const reader = new FileReader();
    reader.readAsDataURL(blob);
    reader.onloadend = () => {
      const base64data = reader.result;
      const input = document.getElementById("audio_data_input");
      input.value = base64data;
      const form = document.getElementById("audio_form");
      form.requestSubmit();
    };
  };

  // 1초마다 녹음 stop/start
  setInterval(() => {
    if (mediaRecorder.state === "recording") {
      mediaRecorder.stop();
    }
    mediaRecorder.start();
  }, 1200);
}

window.addEventListener('load', function() {
  const btn = document.getElementById("start_btn");
  btn.onclick = () => {
    if (!sending) {
      sending = true;
      startRecording();
      btn.innerText = "녹음 중... (말해보세요)";
    }
  };
});
</script>
"""

st.markdown("""
<form id="audio_form" method="post">
  <input id="audio_data_input" name="audio_data" type="hidden" />
</form>
<button id="start_btn" type="button">🎙️ 실시간 감지 시작</button>
""", unsafe_allow_html=True)

st.markdown(record_js, unsafe_allow_html=True)

# 4) Streamlit이 POST로 받은 base64 오디오 처리
#    Streamlit은 기본적으로 컴포넌트가 아니면 완전한 POST 훅이 없어서
#    여기서는 세션 상태에 저장하는 식으로 처리
if "last_label" not in st.session_state:
    st.session_state.last_label = None
    st.session_state.last_score = 0.0

# Streamlit은 위의 폼 submit이 되면 rerun되니까,
# 그때 request body를 직접 읽을 수는 없고, s
