import streamlit as st
import numpy as np
import pathlib

# 1. 라벨 로드
def load_labels(path: str):
    labels = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            idx, name = line.strip().split(" ", 1)
            labels[int(idx)] = name
    return labels

LABELS = load_labels("labels.txt")

# 2. 모델 로드 (tensorflow로)
import tensorflow as tf

@st.cache_resource
def load_model():
    model_path = pathlib.Path("soundclassifier_with_metadata.tflite")
    # TFLite 모델을 TF 인터프리터로
    interpreter = tf.lite.Interpreter(model_path=str(model_path))
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    return interpreter, input_details, output_details

interpreter, input_details, output_details = load_model()

def classify_audio_array(audio_arr: np.ndarray):
    input_shape = input_details[0]["shape"]  # [1, N]
    req_len = input_shape[1]

    # mono 가정
    if audio_arr.ndim > 1:
        audio_arr = audio_arr[:, 0]

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

st.title("Teachable Machine 오디오 분류 (업로드 버전)")
st.write("wav/mp3 녹음파일을 올리면 0~3 레이블로 분류해줄게요. (0 깔라만씨 / 1 배경 소음 / 2 수박씨 / 3 아이씨)")

uploaded = st.file_uploader("음성 파일 업로드", type=["wav", "mp3", "ogg", "flac"])

if uploaded is not None:
    import soundfile as sf
    data, sr = sf.read(uploaded)
    label, score = classify_audio_array(data)
    st.success(f"예측: {label} ({score*100:.1f}%)")
    if label == "아이씨":
        st.error("🚨 비속어 감지! 여기서 이후 로직(차단/로그 등) 붙이면 됩니다.")
