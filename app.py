# app.py
# -*- coding: utf-8 -*-
"""
결(結) — 멘티 전용 매칭 데모 (대화 주제 제거 + 신청 시 채팅 바로 연결)
"""

from pathlib import Path
from typing import Dict, Set
import pandas as pd
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from base64 import b64encode
import mimetypes
from datetime import datetime

# ==============================
# 1) 기본 상수
# ==============================
GENDERS = ["남", "여", "기타"]
AGE_BANDS = [
    "만 13세~19세", "만 20세~29세", "만 30세~39세", "만 40세~49세",
    "만 50세~59세", "만 60세~69세", "만 70세~79세", "만 80세~89세", "만 90세 이상"
]

PURPOSES = ["진로 / 커리어 조언", "학업 / 전문지식 조언", "사회, 인생 경험 공유", "정서적 지지와 대화"]
CURRENT_OCCUPATIONS = [
    "경영자(CEO / 사업주 / 임원 / 부서장)",
    "행정관리(공공기관 관리자 / 기업 행정팀장 / 프로젝트 매니저)",
    "보건(의사 / 치과의사 / 약사 / 간호사 / 한의사 / 물리치료사 / 간호조무사 / 재활치료사 / 요양보호사)",
    "법률/행정(변호사 / 판사 / 검사 / 세무사 / 행정사)",
    "교육(교수 / 교사 / 학원강사 / 연구원)",
    "연구개발/ IT(엔지니어 / 연구원 / 소프트웨어 개발자 / 데이터 분석가)",
    "예술/디자인(디자이너 / 예술가 / 작가 / 사진작가)",
    "기술(기술자 / 공학 기술자 / 실험실 기술자 / 회계사 / 건축기사)",
    "서비스 전문(상담사 / 심리치료사 / 사회복지사 / 코디네이터)",
    "일반 사무 (사무직원 / 경리 / 비서 / 고객 상담 / 문서 관리)",
    "영업(영업사원 / 마케팅 지원 / 고객 관리)",
    "판매(점원 / 슈퍼 / 편의점 직원 / 백화점 직원)",
    "생산/제조(공장 생산직 / 조립공 / 기계조작원 / 용접공)",
    "시설(배관공 / 전기공 / 건설노무자 / 목수)",
    "농림수산업(농부 / 축산업 / 어부 / 임업 종사자)",
    "운송/기계(트럭기사 / 버스기사 / 지게차 운전 / 기계조작원)",
    "청소 / 경비(경비원 / 환경미화원)",
    "학생 (초·중·고·대학생 / 대학원생)",
    "전업주부",
    "구직자 / 최근 퇴사자 / 프리랜서",
    "기타",
]
HOBBIES = ["독서", "음악 감상", "영화/드라마 감상", "게임 (PC/콘솔/모바일)", "운동/스포츠 관람",
           "미술·전시 감상", "여행", "요리/베이킹", "사진/영상 제작", "춤/노래"]
OCCUPATION_MAJORS = ["교육", "법률/행정", "연구개발/ IT", "예술/디자인", "의학/보건", "기타"]
OCC_TO_MAJOR = {
    "경영자(CEO / 사업주 / 임원 / 부서장)": "기타",
    "행정관리(공공기관 관리자 / 기업 행정팀장 / 프로젝트 매니저)": "법률/행정",
    "보건(의사 / 치과의사 / 약사 / 간호사 / 한의사 / 물리치료사 / 간호조무사 / 재활치료사 / 요양보호사)": "의학/보건",
    "법률/행정(변호사 / 판사 / 검사 / 세무사 / 행정사)": "법률/행정",
    "교육(교수 / 교사 / 학원강사 / 연구원)": "교육",
    "연구개발/ IT(엔지니어 / 연구원 / 소프트웨어 개발자 / 데이터 분석가)": "연구개발/ IT",
    "예술/디자인(디자이너 / 예술가 / 작가 / 사진작가)": "예술/디자인",
}

# ==============================
# 2) 기본 UI 스타일
# ==============================
BACKGROUND_FILE = "logo_gyeol.png"
@st.cache_data(show_spinner=False)
def get_background_data_url() -> str | None:
    p = Path(__file__).resolve().parent / BACKGROUND_FILE
    if not p.is_file(): return None
    mime, _ = mimetypes.guess_type(p.name)
    mime = mime or "image/png"
    data = p.read_bytes()
    b64 = b64encode(data).decode("ascii")
    return f"data:{mime};base64,{b64}"

def inject_style():
    data_url = get_background_data_url()
    bg_style = f"background-image: url('{data_url}'); background-size: cover; background-position: center; background-attachment: fixed;" if data_url \
               else "background: radial-gradient(circle at 30% 30%, #14193F, #1B1F4B 25%, #10142C 60%, #080A1A 100%);"
    st.markdown(f"""
    <style>
      [data-testid="stAppViewContainer"] {{ {bg_style} }}
      [data-testid="stHeader"] {{ background: transparent; }}
      .block-container {{
        max-width: 900px;
        padding: 2.25rem 2rem 3rem;
        background: rgba(255,255,255,0.72);
