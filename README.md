# Teachable Machine Audio + Streamlit WebRTC

- Teachable Machine에서 export한 오디오 모델(`soundclassifier_with_metadata.tflite`)과
- 라벨 파일(`labels.txt`)
을 사용해서 브라우저 마이크 소리를 실시간으로 분류하는 데모입니다.

```bash
pip install -r requirements.txt
streamlit run app.py
