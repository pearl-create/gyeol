# app.py (핵심 부분 수정)
from tflite_support.task import audio
from tflite_support.task import core

# 모델 및 라벨 파일 경로 (GitHub 저장소의 루트 경로에 있다고 가정)
TFLITE_MODEL_PATH = "soundclassifier_with_metadata.tflite"
LABELS_PATH = "labels.txt" # 이 파일에는 '0 깔라만씨\n1 배경 소음\n...' 와 같이 있어야 합니다.

# 모델 로드 및 분류기 초기화
@st.cache_resource
def load_classifier(model_path):
    # TFLite Task Library의 AudioClassifier를 사용하여 모델 로드
    base_options = core.BaseOptions(file_name=model_path)
    options = audio.AudioClassifierOptions(base_options=base_options, max_results=4)
    classifier = audio.AudioClassifier.create_from_options(options)
    
    # 모델의 샘플링 레이트와 버퍼 크기 등을 메타데이터에서 얻을 수 있습니다.
    # classifier.get_required_sample_rate()
    # classifier.get_required_input_buffer_size()
    
    return classifier

# TFLiteAudioProcessor 클래스 수정
class TFLiteAudioProcessor(AudioProcessorBase):
    def __init__(self, classifier):
        self.classifier = classifier
        # 모델이 요구하는 길이만큼 오디오 데이터를 모으기 위한 버퍼
        self.audio_record = audio.AudioData.create_from_array(
            np.zeros(classifier.get_required_input_buffer_size()), 
            classifier.get_required_sample_rate()
        )
        self.result = "대기 중..."

    def recv(self, frame):
        # 1. WebRTC 프레임을 numpy 배열로 변환
        audio_array = frame.to_ndarray(format="s16le")
        
        # 2. 버퍼에 현재 프레임의 오디오 데이터를 추가 (tflite-support 활용)
        # WebRTC 스트림의 샘플 레이트가 모델과 다르면 리샘플링이 필요합니다.
        # (AudioData 클래스가 내부적으로 처리할 수 있도록 코드를 작성해야 합니다)

        # 실제 로직: WebRTC의 오디오 프레임을 AudioData 객체에 계속 추가합니다.
        # 이 부분이 가장 까다로우므로, 공식 예시를 참고하여 구현해야 합니다.
        
        # 임의의 추론 결과 업데이트 (실제 코드와 대체되어야 함)
        if np.random.rand() > 0.8:
            classification_result = self.classifier.classify(self.audio_record)
            
            top_category = classification_result.classifications[0].categories[0]
            self.result = f"{top_category.category_name} ({top_category.score:.2f})"
        
        return frame
    
# main 함수 수정
def main():
    st.title("🎤 실시간 음성 분류기 (Streamlit + WebRTC)")
    
    # 분류기 로드
    classifier = load_classifier(TFLITE_MODEL_PATH)
    st.sidebar.success("✅ TFLite 분류기 로드 완료")
    
    # webrtc_streamer 컴포넌트 실행
    webrtc_ctx = webrtc_streamer(
        key="sound-classifier",
        mode=WebRtcMode.SENDONLY,
        audio_processor_factory=lambda: TFLiteAudioProcessor(classifier),
        media_stream_constraints={"video": False, "audio": True}
    )

    if webrtc_ctx.state.playing and webrtc_ctx.audio_processor:
        st.success("🟢 마이크 활성화됨: 말해보세요!")
        st.write(f"현재 분류 결과: **{webrtc_ctx.audio_processor.result}**")
