# TensorFlow Lite 모델을 쉽게 다루기 위한 라이브러리
pip install tflite-support

# 실시간 마이크 입력을 처리하기 위한 라이브러리
# PortAudio 설치가 필요할 수 있습니다. (Linux: sudo apt-get install libportaudio2)
pip install sounddevice numpy

# tflite-support 라이브러리가 PortAudio에 의존하므로, PortAudio 설치가 필요한 경우 다음 단계를 따릅니다.
# (Windows 및 Mac에서는 tflite-support 설치 시 자동 설치되는 경우가 많습니다.)
import numpy as np
import time
# TFLite AudioClassifier를 사용하기 위한 라이브러리
from tflite_support.task import audio
from tflite_support.task import core
from tflite_support.task import processor

# 1. 모델 설정
MODEL_PATH = 'soundclassifier_with_metadata.tflite'
# 모델 설정 옵션
base_options = core.BaseOptions(file_name=MODEL_PATH)
options = audio.AudioClassifierOptions(base_options=base_options)

# 2. 오디오 분류기 생성 및 마이크 녹음 시작
# 이 단계에서 labels.txt를 포함한 메타데이터가 자동 로드됩니다.
classifier = audio.AudioClassifier.create_from_options(options)

# 모델이 요구하는 오디오 입력 버퍼 크기 확인
input_buffer_size = classifier.required_input_buffer_size

# 마이크에서 실시간으로 녹음을 시작합니다.
# 이 함수는 PortAudio에 의존합니다.
audio_record = classifier.create_audio_record()
audio_record.start_recording()

print("🌟 실시간 비속어 감지 시작 (마이크에 대고 말해주세요)...")
print("-" * 30)

# 3. 실시간 추론(Inference) 실행
# 특정 주기(모델의 요구 사항에 따라 다름)마다 오디오를 분석합니다.
while True:
    # 3.1. 오디오 데이터 로드
    # 현재 오디오 버퍼에 있는 데이터를 텐서로 로드합니다.
    tensor_audio = audio.TensorAudio.create_from_audio_record(
        audio_record, input_buffer_size
    )

    # 3.2. 분류 실행 (추론)
    # 모델을 실행하여 결과를 ClassificationResult 객체로 받습니다.
    classification_result = classifier.classify(tensor_audio)

    # 3.3. 결과 파싱 및 출력
    if classification_result.classifications:
        # 가장 첫 번째 분류 헤드(head)의 결과를 가져옴
        categories = classification_result.classifications[0].categories
        
        # 특정 단어('아이씨')의 확률을 찾기
        target_label = "아이씨"
        target_score = 0.0
        
        # 모든 레이블(깔라만씨, 배경 소음, 수박씨, 아이씨)의 점수 확인
        print("모든 레이블 점수:")
        
        all_scores = {}
        for category in categories:
            label = category.label
            score = category.score * 100 # 확률을 %로 변환
            all_scores[label] = score
            print(f"  - {label}: {score:.2f}%")
            
            if label == target_label:
                target_score = score
        
        print(f"\n✨ '{target_label}' 감지 확률: {target_score:.2f}%")
        
        # 감지 임계값 설정 및 특정 액션 수행 (선택 사항)
        if target_score > 70.0:
            print("🚨 경고: '아이씨' 감지 확률이 높습니다!")
            
        print("-" * 30)
    
    # 3.4. 분석 주기 조절 (너무 빠르지 않게)
    # 모델의 성능에 따라 지연 시간을 조절합니다.
    time.sleep(0.5)

# 4. 종료 시 정리
# (Ctrl+C로 종료 시 실행)
audio_record.stop_recording()
print("실시간 감지 종료.")
