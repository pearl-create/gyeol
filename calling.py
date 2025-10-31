

import streamlit as st
import numpy as np
import av
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import pathlib

# ---------------------
# 1. 레이블 불러오기
# ---------------------
def load_labels(path: str):
    labels = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            idx, name = line.strip().split(" ", 1)
            labels[int(idx)] = name
    return labels

LABELS = load_labels("labels.txt")  # 0~3 -> 한글 레이블 맵
BAD_LABEL = "아이씨"  # 잡으면 경고 띄울 단어

# ---------------------
# 2. TFLite 모델 로더
# ---------------------
# tflite-runtime 이 있으면 그걸 쓰고, 없으면 tensorflow.lite 로 떨어지게
try:
    from tflite_runtime.interpreter import Interpreter
except ImportError:
    from tensorflow.lite import Interpreter


@st.cache_resource
def load_model():
    model_path = pathlib.Path("soundclassifier_with_metadata.tflite")
    interpreter = Interpreter(model_path=str(model_path))
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    return interpreter, input_details, output_details


interpreter, input_details, output_details = load_model()


# ---------------------
# 3. 오디오 → 모델 추론 함수
#    (여기서는 아주 단순하게: 들어온 버퍼를 잘라서 첫번째 채널만 씀)
# ---------------------
def classify_audio(audio_chunk: np.ndarray):
    """
    audio_chunk: np.float32, mono, [samples]
    모델이 요구하는 shape에 맞춰 넣어줘야 함.
    Teachable Machine 오디오 모델은 보통 [1, N] float32 기대함.
    """
    # 1) 모델 입력 shape 확인
    input_shape = input_details[0]["shape"]  # e.g. [1, 15600]
    required_len = input_shape[1]

    # 2) 길이 맞추기 (부족하면 0패딩, 길면 자르기)
    if audio_chunk.shape[0] < required_len:
        padded = np.zeros(required_len, dtype=np.float32)
        padded[: audio_chunk.shape[0]] = audio_chunk
        audio_chunk = padded
    else:
        audio_chunk = audio_chunk[:required_len]

    # 3) 배치 차원 붙이기
    audio_chunk = np.expand_dims(audio_chunk, axis=0).astype(np.float32)

    # 4) 인터프리터에 넣기
    interpreter.set_tensor(input_details[0]["index"], audio_chunk)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]["index"])
    # output_data shape: [1, num_classes]
    scores = output_data[0]
    pred_idx = int(np.argmax(scores))
    pred_label = LABELS.get(pred_idx, f"class_{pred_idx}")
    pred_score = float(scores[pred_idx])
    return pred_label, pred_score


# ---------------------
# 4. WebRTC 오디오 프로세서
# ---------------------
class AudioProcessor(AudioProcessorBase):
    def __init__(self) -> None:
        self.last_label = None
        self.last_score = 0.0

    def recv_audio(self, frame: av.AudioFrame) -> av.AudioFrame:
        # av.AudioFrame -> np.ndarray (samples, channels)
        pcm = frame.to_ndarray()
        # stereo일 수도 있으니까 첫 번째 채널만 사용
        if pcm.ndim == 2:
            pcm = pcm[:, 0]
        pcm = pcm.astype(np.float32)

        # 16bit PCM으로 들어오면 scale 필요할 수도 있음
        # 여기서는 대충 정규화
        if pcm.max() > 0:
            pcm = pcm / np.abs(pcm).max()

        label, score = classify_audio(pcm)
        self.last_label = label
        self.last_score = score

        # 여기서 바로 음소거 하고 싶으면
        # return av.AudioFrame.from_ndarray(np.zeros_like(frame.to_ndarray()), layout=frame.layout)
        return frame


st.set_page_config(page_title="음성 욕설 감지 데모", page_icon="🎤")

st.title("🎤 Teachable Machine 음성 분류 + Streamlit WebRTC 데모")
st.write("마이크 허용을 눌러서 소리를 내보면, 아래에 예측 라벨이 나옵니다.")
st.write("모델 라벨: 0 깔라만씨 / 1 배경 소음 / 2 수박씨 / 3 아이씨")  # :contentReference[oaicite:3]{index=3}

webrtc_ctx = webrtc_streamer(
    key="audio-demo",
    mode=WebRtcMode.SENDONLY,  # 내 마이크만 보내는 모드
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=True,
)

# 화면에 예측값 띄우기
if webrtc_ctx and webrtc_ctx.audio_processor:
    label = webrtc_ctx.audio_processor.last_label
    score = webrtc_ctx.audio_processor.last_score
    if label:
        st.metric("현재 감지된 라벨", f"{label}", f"{score*100:.1f}%")
        if label == BAD_LABEL:
            st.error("🚨 비속어(아이씨) 감지! 통화 제한/경고 처리하세요.")
else:
    st.info("마이크 연결을 기다리는 중입니다.")
