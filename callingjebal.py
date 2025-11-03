# callingjebal.py (수정된 코드)

import streamlit as st
import base64
import numpy as np
import io
import librosa
from tflite_runtime.interpreter import Interpreter # tflite-runtime 사용 가정

# TFLite 모델 및 라벨 로딩 함수 (이전에 정의했던 함수 사용)
@st.cache_resource
def load_tflite_model(model_path, labels_path):
    # ... TFLite Interpreter 로드 및 라벨 로드 ...
    interpreter = Interpreter(model_path=model_path)
    interpreter.allocate_tensors()
    # ... 라벨 로드 로직 ...
    return interpreter, labels

# HTML 파일을 읽어 Streamlit 컴포넌트로 만드는 함수
def record_audio_component(html_file_path):
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_code = f.read()
    
    # st.components.v1.html을 사용하여 HTML 코드 삽입
    # 이 함수가 JavaScript로부터 반환된 값 (Base64 오디오)을 받습니다.
    # height는 사용자 인터페이스 크기에 맞게 조정하세요.
    audio_data_base64 = st.components.v1.html(
        html_code, 
        height=150, 
        scrolling=False
    )
    return audio_data_base64

# 메인 함수
def main():
    st.title("🎤 HTML 임베딩 오디오 분류기")
    
    # 1. 모델 로드
    interpreter, labels = load_tflite_model("soundclassifier_with_metadata.tflite", "labels.txt")
    st.sidebar.success("✅ TFLite 모델 로드 완료")
    
    # 2. HTML 컴포넌트 삽입 및 Base64 데이터 받기
    # HTML 파일 경로가 GitHub 저장소 루트에 있다고 가정
    base64_audio = record_audio_component("microphone_recorder.html") 

    if base64_audio:
        st.info("오디오 데이터 수신 완료. 분류를 시작합니다.")
        
        # 3. Base64 데이터를 오디오 파일로 변환
        audio_bytes = base64.b64decode(base64_audio)
        audio_stream = io.BytesIO(audio_bytes)
        
        # 확인용 오디오 플레이어 (wav 포맷 가정)
        st.audio(audio_bytes, format='audio/wav')

        # 4. 오디오 처리 및 추론 (Librosa 및 TFLite 사용)
        with st.spinner('모델 추론 중...'):
            try:
                # Librosa로 오디오 로드 및 리샘플링 (모델 학습 시 SR 사용)
                audio_data, sr = librosa.load(audio_stream, sr=16000) 
                
                # run_inference 함수 호출 (이 로직은 사용자가 구현해야 함)
                # 예: run_inference(interpreter, audio_data, sr, labels)
                
                # 임시 결과 출력
                predicted_label = labels[np.random.randint(0, len(labels))]
                st.success(f"분류 결과: **{predicted_label}**")
                
            except Exception as e:
                st.error(f"오디오 처리 중 오류 발생: {e}")
                st.warning("오디오 전처리 로직(리샘플링, 멜 스펙트로그램 생성)을 확인하세요.")

if __name__ == "__main__":
    # st.set_page_config(layout="wide") # 전체 화면 설정 (선택 사항)
    main()
