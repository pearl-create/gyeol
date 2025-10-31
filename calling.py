import streamlit as st
import numpy as np
import io
import time
from tflite_runtime.interpreter import Interpreter
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase

# --- 1. 설정 및 모델 로드 ---

# 파일명은 사용자가 업로드한 파일과 정확히 일치해야 합니다.
MODEL_PATH = "soundclassifier_with_metadata.tflite"
LABELS_PATH = "labels.txt"

# 티처블 머신 오디오 모델의 입력 요구사항 (보통 1초 오디오, 44100Hz)
TARGET_SAMPLE_RATE = 44100
AUDIO_CHUNK_SIZE = 1 * TARGET_SAMPLE_RATE # 1초 분량의 샘플

@st.cache_resource
def load_teachable_machine_model():
    """TFLite 모델과 라벨을 로드하고 캐싱합니다."""
    try:
        # TFLite Interpreter 로드
        interpreter = Interpreter(model_path=MODEL_PATH)
        interpreter.allocate_tensors()
        
        # 모델 입력/출력 정보 가져오기
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        
        # 라벨 로드
        with open(LABELS_PATH, 'r', encoding='utf-8') as f:
            # "0 클래스명", "1 클래스명" 형태에서 클래스명만 추출
            labels = [line.strip().split(' ', 1)[1] for line in f.readlines()]
            
        return interpreter, labels, input_details, output_details
    except Exception as e:
        st.error(f"모델 또는 라벨 파일 로드 오류: {e}")
        st.error(f"오류 상세: {e}")
        st.warning("TFLite 모델 실행 환경(tflite_runtime)이 올바르게 설정되었는지 확인하세요.")
        return None, None, None, None

INTERPRETER, LABELS, INPUT_DETAILS, OUTPUT_DETAILS = load_teachable_machine_model()

# --- 2. 실시간 오디오 처리 클래스 ---

class TFLiteAudioProcessor(AudioProcessorBase):
    """
    streamlit-webrtc를 통해 들어오는 오디오 데이터를 TFLite 모델로 처리합니다.
    """
    def __init__(self, interpreter, input_details, output_details, labels):
        self.interpreter = interpreter
        self.input_details = input_details
        self.output_details = output_details
        self.labels = labels
        self.audio_buffer = np.array([], dtype=np.float32)
        
        # Streamlit UI 업데이트를 위한 세션 상태
        st.session_state.current_result = "스트림 시작 대기 중..."
        st.session_state.detection_history = []

    def recv(self, frame):
        """WebRTC 오디오 프레임이 들어올 때마다 호출됩니다."""
        # 1. 오디오 데이터 추출 및 float32로 변환
        # frame.to_ndarray()는 int16 형식의 오디오 배열을 반환합니다.
        audio_int16 = np.frombuffer(frame.to_ndarray(), dtype=np.int16)
        audio_float32 = audio_int16.astype(np.float32) / 32768.0

        # 버퍼에 오디오 데이터 추가
        self.audio_buffer = np.concatenate([self.audio_buffer, audio_float32])

        # 2. 1초(44100 샘플) 분량의 데이터가 모였는지 확인
        if self.audio_buffer.size >= AUDIO_CHUNK_SIZE:
            
            # 모델에 입력할 1초 데이터 추출
            input_data = self.audio_buffer[:AUDIO_CHUNK_SIZE]
            
            # 버퍼에서 사용된 데이터 제거 (나머지 데이터는 다음 프레임과 합쳐짐)
            self.audio_buffer = self.audio_buffer[AUDIO_CHUNK_SIZE:]
            
            # 티처블 머신 TFLite 모델은 (1, 44100) 형태의 입력을 기대합니다.
            input_tensor = input_data.reshape(1, AUDIO_CHUNK_SIZE)

            # 3. 모델 예측 실행
            self.interpreter.set_tensor(self.input_details[0]['index'], input_tensor)
            self.interpreter.invoke()
            predictions = self.interpreter.get_tensor(self.output_details[0]['index'])[0]

            # 4. 결과 해석
            predicted_class_index = np.argmax(predictions)
            confidence = predictions[predicted_class_index]
            predicted_label = self.labels[predicted_class_index]
            
            # 5. 비속어 감지 및 기록 (라벨 이름에 따라 조건 수정)
            is_profanity = any(word in predicted_label for word in ["아이씨", "욕설_라벨", "비속어_라벨"]) # labels.txt 기반으로 수정
            
            if is_profanity and confidence > 0.7:
                detection_result = f"🚨 비속어 감지됨! ({predicted_label}: {confidence*100:.1f}%)"
            else:
                detection_result = f"✅ 정상 음성 감지 중... ({predicted_label}: {confidence*100:.1f}%)"

            # 6. Streamlit UI 업데이트 (세션 상태 사용)
            st.session_state.current_result = detection_result
            
            # 이력 업데이트
            history = st.session_state.get('detection_history', [])
            history.append(detection_result)
            st.session_state.detection_history = history[-5:] # 최신 5개만 유지

        # 오디오 프레임은 그대로 반환
        return frame

# --- 3. Streamlit UI 구성 ---

st.title("🗣️ AI 비속어 음성 감지 시스템 (Streamlit + TFLite)")
st.markdown("---")

if INTERPRETER is None:
    st.warning("모델 로드에 실패하여 감지기를 실행할 수 없습니다.")
else:
    st.info("🎤 아래 버튼을 클릭하고 마이크 접근을 허용하면 실시간 음성 감지가 시작됩니다.")

    # webrtc_streamer 설정 및 실행
    webrtc_ctx = webrtc_streamer(
        key="audio-detector",
        mode=WebRtcMode.SENDONLY,
        # AudioProcessorBase 클래스의 인스턴스를 생성하여 오디오 처리에 사용
        audio_processor_factory=lambda: TFLiteAudioProcessor(
            INTERPRETER, INPUT_DETAILS, OUTPUT_DETAILS, LABELS
        ),
        # 실시간 오디오 스트림만 필요하므로 비디오는 비활성화
        media_stream_constraints={"video": False, "audio": True}, 
    )

    # --- 4. 실시간 결과 표시 ---
    st.subheader("실시간 감지 결과")
    
    # UI는 매번 리런되므로 세션 상태의 최신 결과를 가져와 표시합니다.
    current_result = st.session_state.get('current_result', '스트림 시작 대기 중...')
    
    if "🚨 비속어" in current_result:
        st.error(current_result)
    elif "✅ 정상" in current_result:
        st.success(current_result)
    else:
        st.text(current_result)
        
    st.subheader("감지 이력")
    detection_history = st.session_state.get('detection_history', [])
    if detection_history:
        for i, result in enumerate(reversed(detection_history)):
            st.text(f"{len(detection_history) - i}: {result}")
