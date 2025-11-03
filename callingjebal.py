import streamlit as st

st.set_page_config(page_title="실시간 감지 데모", page_icon="🎙️", layout="centered")

# HTML 파일을 읽어서 삽입
with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# HTML을 Streamlit에 렌더링
st.components.v1.html(html, height=640, scrolling=True)
