pip install tflite-support sounddevice numpy
import numpy as np
import time
import sys
# TensorFlow Lite Task Library의 오디오 분류 모듈 임포트
try:
    from tflite_support.task import audio
    from tflite_support.task import core
    from tflite_support.task import processor
except ImportError:
    print("오류: 'tflite-support' 라이브러리가 설치되지 않았습니다.")
    print("터미널/CMD에서 다음 명령어를 실행하여 설치하세요: pip install tflite-support sounddevice numpy")
    sys.exit(1)

# --- 설정 변수 ---
# 사용자가 올린 TFLite 모델 파일 이름
MODEL_PATH = 'soundclassifier_with_metadata.tflite'
# 추론(Inference) 결과를 출력할 최소 확률 임계값 (예: 50% 미만은 무시)
PROBABILITY_THRESHOLD = 0.01  
# 실시간 감지하려는 특정 단어 (labels.txt에 있는 단어여야 함)
TARGET_LABEL = "아이씨" 
# 감지 결과를 화면에 얼마나 자주 업데이트할지 (초 단위)
UPDATE_INTERVAL_SEC = 0.5 
# ------------------

def run_audio_classification():
    """마이크 입력을 받아 TFLite 모델로 실시간 음성 분류를 수행합니다."""
    
    print("=" * 50)
    print(f"✨ TFLite 모델을 이용한 실시간 음성 분류 시스템")
    print(f"🚀 대상 모델: {MODEL_PATH}")
    print(f"🎯 특정 감지 단어: '{TARGET_LABEL}'")
    print("=" * 50)

    try:
        # 1. 모델 옵션 설정 및 분류기 생성
        base_options = core.BaseOptions(file_name=MODEL_PATH)
        # 분류 옵션: 최소 임계값 설정
        options = audio.AudioClassifierOptions(
            base_options=base_options,
            classification_options=processor.ClassificationOptions(
                score_threshold=PROBABILITY_THRESHOLD
            )
        )
        classifier = audio.AudioClassifier.create_from_options(options)
    
    except Exception as e:
        print(f"❌ 모델 로드 중 오류 발생: {e}")
        print("💡 힌트: 파일 이름이 정확한지, 라이브러리가 모두 설치되었는지 확인하세요.")
        return

    # 2. 오디오 입력 설정 및 녹음 시작
    input_buffer_size = classifier.required_input_buffer_size
    audio_record = classifier.create_audio_record()

    try:
        audio_record.start_recording()
        print("\n✅ 마이크 녹음 및 실시간 감지 시작됨...")
        print("    마이크에 대고 '아이씨' 또는 다른 레이블 단어들을 말해보세요.")
        print("-" * 50)

        while True:
            # 3. 오디오 데이터 로드 및 추론
            tensor_audio = audio.TensorAudio.create_from_audio_record(
                audio_record, input_buffer_size
            )
            classification_result = classifier.classify(tensor_audio)

            # 4. 결과 파싱 및 출력
            if classification_result.classifications:
                categories = classification_result.classifications[0].categories
                
                # 모든 레이블의 확률을 저장
                scores = {category.label: category.score * 100 for category in categories}
                
                # 특정 단어의 확률
                target_score = scores.get(TARGET_LABEL, 0.0)

                # 출력 문자열 생성
                output_str = f"⏰ {time.strftime('%H:%M:%S')} | "
                
                # 모든 감지된 레이블 출력
                all_labels_str = ", ".join([
                    f"{label}: {scores.get(label, 0.0):.1f}%" 
                    for label in classifier.get_labels() if scores.get(label, 0.0) >= PROBABILITY_THRESHOLD * 100
                ])

                print(f"{output_str} 감지된 항목: {all_labels_str}")
                
                # 특정 단어 임계값 초과 시 경고
                if target_score > 70.0:
                    print(f"    🚨🚨 경고: '{TARGET_LABEL}' 감지 확률이 {target_score:.1f}%로 높습니다! 🚨🚨")

            # 5. 다음 분석까지 대기
            time.sleep(UPDATE_INTERVAL_SEC)
            
    except KeyboardInterrupt:
        print("\n\n👋 사용자 요청으로 실시간 감지 종료.")
    
    except Exception as e:
        print(f"\n\n❌ 예기치 않은 오류 발생: {e}")

    finally:
        # 6. 리소스 정리
        if 'audio_record' in locals() and audio_record:
            audio_record.stop_recording()

if __name__ == "__main__":
    run_audio_classification()
