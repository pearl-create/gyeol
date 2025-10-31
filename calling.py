import streamlit as st
import numpy as np
import soundfile as sf
import pathlib
import tensorflow as tf

st.set_page_config(page_title="화상통화형 비속어 감지 데모", layout="wide")

# -----------------------------
# 1. 라벨 로드
# -----------------------------
def load_labels(path: str):
    labels = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            idx, name = line.strip().split(" ", 1)
            labels[int(idx)] = name
    return labels

LABELS = load_labels("labels.txt")  # 0 깔라만씨 / 1 배경 소음 / 2 수박씨 / 3 아이씨
BAD_LABEL = "아이씨"  # 잡으면 경고

# -----------------------------
# 2. TFLite 모델 로드
# -----------------------------
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
    input_shape = input_details[0]["shape"]  # e.g. [1, 15600]
    req_len = input_shape[1]

    # mono 처리
    if audio_arr.ndim > 1:
        audio_arr = audio_arr[:, 0]

    # 길이 맞추기
    if audio_arr.shape[0] < req_len:
        padded = np.zeros(req_len, dtype=np.float32)
        padded[: audio_arr.shape[0]] = audio_arr
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

# -----------------------------
# 3. 레이아웃
# -----------------------------
left, right = st.columns([1.1, 0.9])

# -----------------------------
# 3-1. 왼쪽: "화상통화처럼 보이는" 영역
# -----------------------------
with left:
    st.markdown("### 👥 화상 통화")
    st.markdown("""
    <div style="background:#0f172a; border-radius:16px; padding:14px; color:white;">
      <div style="display:flex; gap:10px; align-items:center; margin-bottom:10px;">
        <div style="width:10px; height:10px; background:#f43f5e; border-radius:999px;"></div>
        <div style="width:10px; height:10px; background:#f97316; border-radius:999px;"></div>
        <div style="width:10px; height:10px; background:#22c55e; border-radius:999px;"></div>
        <div style="font-weight:600; margin-left:6px;">멘토-멘티 화상상담</div>
      </div>
      <div style="display:flex; gap:10px;">
        <video id="localVideo" autoplay playsinline style="width:58%; border-radius:12px; background:black; aspect-ratio:4/3; object-fit:cover;"></video>
        <div style="width:42%; display:flex; flex-direction:column; gap:10px;">
          <video id="remoteVideo" autoplay playsinline style="width:100%; border-radius:12px; background:#1f2937; aspect-ratio:4/3; object-fit:cover;"></video>
          <div style="background:#1f2937; border-radius:12px; padding:8px 10px;">
            <p style="margin:0; font-size:0.8rem; opacity:0.8;">대화 중 욕설은 자동으로 감지됩니다.</p>
            <p style="margin:0; font-size:0.75rem; opacity:0.5;">(체험용 데모 화면)</p>
          </div>
        </div>
      </div>
      <div style="margin-top:10px; display:flex; gap:12px; justify-content:center;">
        <button id="camBtn" style="background:#e2e8f0; border:none; border-radius:999px; padding:6px 16px; font-weight:600; cursor:pointer;">카메라 켜기</button>
        <button id="micBtn" style="background:#0f766e; color:white; border:none; border-radius:999px; padding:6px 16px; font-weight:600; cursor:pointer;">🎙️ 말하기 테스트</button>
        <button style="background:#f43f5e; color:white; border:none; border-radius:999px; padding:6px 16px; font-weight:600; cursor:pointer;">통화 종료</button>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # 실제로 캠을 켜는 JS
    st.markdown("""
    <script>
    let globalStream = null;
    const camBtn = document.getElementById("camBtn");
    const micBtn = document.getElementById("micBtn");
    const localVideo = document.getElementById("localVideo");

    camBtn.onclick = async () => {
      if (!globalStream) {
        globalStream = await navigator.mediaDevices.getUserMedia({video:true, audio:true});
        localVideo.srcObject = globalStream;
      }
    };

    // 말하기 테스트: audio만 2~3초 녹음해서 다운로드하게 해두면
    // 사용자가 그 파일을 오른쪽에 올릴 수 있음.
    // (진짜 자동 업로드까지 하려면 커스텀 컴포넌트 필요)
    </script>
    """, unsafe_allow_html=True)


# -----------------------------
# 3-2. 오른쪽: 분류 결과
# -----------------------------
with right:
    st.markdown("### 🎤 실시간 욕설 감지 결과")
    st.write("※ 지금은 '가짜 화상통화 UI'이기 때문에, 오른쪽에서 음성 파일을 올리면 바로 이 화면에 결과가 나옵니다.")
    st.write("※ 체험자에게는 '지금 말씀해 보세요 → 이걸로 들어왔어요'라고 설명하면 돼요.")
    audio_file = st.file_uploader("여기에 방금 말한 녹음 파일(webm/wav)을 올려보세요.", type=["wav", "ogg", "webm", "flac", "mp3"])

    if audio_file is not None:
        # 오디오 읽기
        data, sr = sf.read(audio_file)
        label, score = classify_audio_array(data)
        st.metric("분류 결과", label, f"{score*100:.1f}%")

        if label == BAD_LABEL:
            st.error("🚨 비속어 감지됨! (자동 차단/경고 로직 여기 연결)")
        elif label == "배경 소음":
            st.info("배경 소음으로 인식했어요.")
        else:
            st.success("비속어 아님 👍")

    else:
        st.info("녹음해서 올리면 여기 결과가 뜹니다.")
