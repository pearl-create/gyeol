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
        border-radius: 20px;
        backdrop-filter: blur(4px);
        box-shadow: 0 6px 22px rgba(0,0,0,0.12);
      }}
    </style>
    """, unsafe_allow_html=True)

# ==============================
# 3) CSV 로딩
# ==============================
@st.cache_data(show_spinner=False)
def load_default_csv() -> pd.DataFrame:
    for path in ["/mnt/data/멘토더미.csv", "멘토더미.csv"]:
        for enc in ["utf-8-sig","utf-8","cp949"]:
            try:
                df = pd.read_csv(path, encoding=enc)
                if not df.empty: return df
            except: continue
    return pd.DataFrame([{
        "name":"김샘","gender":"남","age_band":"만 60세~69세",
        "occupation_major":"교육","purpose":"사회, 인생 경험 공유, 정서적 지지와 대화",
        "interests":"독서, 인문학","intro":"경청 중심의 상담을 합니다."
    }])

# ==============================
# 4) 매칭 계산
# ==============================
def list_to_set(s): return {x.strip() for x in str(s).replace(";",",").split(",") if x.strip()} if pd.notna(s) else set()
def ratio_overlap(a,b): return len(a & b)/len(a|b) if a and b else 0
def tfidf_similarity(a,b):
    a,b=(a or "").strip(),(b or "").strip()
    if not a or not b: return 0.0
    v=TfidfVectorizer(max_features=400,ngram_range=(1,2));X=v.fit_transform([a,b])
    return float(cosine_similarity(X[0],X[1])[0,0])
def map_occ_to_major(selected): return {OCC_TO_MAJOR.get(o,"기타") for o in selected}
def compute_score(mentee,m):
    s=lambda k:list_to_set(m.get(k,""));maj=(m.get("occupation_major","") or "").strip()
    return int(round(
        ratio_overlap(mentee["purpose"],s("purpose"))*30 +
        ratio_overlap(mentee["interests"],s("interests"))*25 +
        (25 if maj in mentee["pref_majors"] else 0) +
        (10 if maj in mentee["mapped_majors"] else 0) +
        tfidf_similarity(mentee["note"],m.get("intro",""))*10
    ))

# ==============================
# 5) 상태 초기화 & 라우팅
# ==============================
if "view" not in st.session_state: st.session_state["view"]="match"
if "chat_log" not in st.session_state: st.session_state["chat_log"]={}
def goto(view:str): st.session_state["view"]=view; st.rerun()

# ==============================
# 6) 멘토 자동 응답 생성
# ==============================
def mentor_autoreply(row, mentee_note=""):
    name=row.get("name","멘토")
    style=row.get("communication_style","편안한 대화")
    intro=row.get("intro","반가워요.")
    purp=row.get("purpose","")
    greet=f"안녕하세요, {name} 멘토입니다 😊\n\n{intro}"
    add=f"\n\n제가 주로 도와드릴 수 있는 분야는 '{purp}'예요." if purp else ""
    note=f"\n\n당신의 요청: “{mentee_note.strip()}” 확인했습니다." if mentee_note else ""
    end=f"\n\n({style})"
    return greet+add+note+end

# ==============================
# 7) 채팅 화면
# ==============================
def view_chat():
    partner = st.session_state.get("chat_partner","")
    if not partner:
        st.info("대화할 멘토를 선택해 주세요.")
        if st.button("← 추천으로 돌아가기"): goto("match")
        return
    st.title(f"💬 {partner} 님과의 대화")
    log = st.session_state["chat_log"].setdefault(partner,[])
    for role,text,ts in log:
        with st.chat_message("assistant" if role=="assistant" else "user"):
            st.markdown(text)
    msg = st.chat_input("메시지를 입력하세요")
    if msg:
        log.append(("user",msg,datetime.now().isoformat()))
        reply=f"{partner}: 흥미로운 말씀이에요! 좀 더 자세히 말씀해 주실래요?"
        log.append(("assistant",reply,datetime.now().isoformat()))
        st.session_state["chat_log"][partner]=log
        st.rerun()
    if st.button("← 추천으로 돌아가기", use_container_width=True): goto("match")

# ==============================
# 8) 매칭 & 결과 (기본 뷰)
# ==============================
def view_match():
    st.set_page_config(page_title="결: 멘티 데모", page_icon="🤝")
    inject_style()
    st.title("연결될 준비")
    df=load_default_csv()
    with st.form("mentee_form"):
        purpose=st.multiselect("멘토링 목적", PURPOSES)
        occ=st.multiselect("관심 있는 현재 직종", CURRENT_OCCUPATIONS)
        pref=st.multiselect("선호 전공계열(멘토 전공)", OCCUPATION_MAJORS)
        inter=st.multiselect("관심사/취미", HOBBIES)
        note=st.text_area("한 줄 요청사항", placeholder="예) 간호사 퇴직하신 선배님을 찾습니다!")
        submit=st.form_submit_button("추천 멘토 보기", use_container_width=True)
    if not submit: st.stop()

    mentee={"purpose":set(purpose),"interests":set(inter),"note":note,
            "pref_majors":set(pref),"mapped_majors":map_occ_to_major(set(occ))}
    scores=[{"idx":i,"score":compute_score(mentee,row)} for i,row in df.iterrows()]
    ranked=sorted(scores,key=lambda x:x["score"],reverse=True)[:5]

    st.markdown("---")
    st.subheader("추천 멘토 Top 5")
    if not ranked: st.warning("추천 결과가 없습니다."); st.stop()

    for i,it in enumerate(ranked,1):
        r=df.loc[it["idx"]]
        with st.container(border=True):
            st.markdown(f"### #{i}. {r.get('name','(이름없음)')} · {r.get('age_band','')}")
            st.write(f"**직종:** {r.get('current_occupation','(미기재)')} / {r.get('occupation_major','(미기재)')}")
            if "communication_style" in df.columns:
                st.write(f"**소통 스타일:** {r.get('communication_style','')}")
            st.write(f"**소개:** {r.get('intro','')}")
            if st.button(f"💬 {r.get('name','')} 님에게 대화 신청하기", key=f"chat_{i}", use_container_width=True):
                st.session_state["chat_partner"]=r.get("name","")
                log=st.session_state["chat_log"].setdefault(r.get("name",""),[])
                auto=mentor_autoreply(r,mentee["note"])
                log.append(("assistant",auto,datetime.now().isoformat()))
                st.session_state["chat_log"][r.get("name","")]=log
                goto("chat")

# ==============================
# 9) 실행
# ==============================
if st.session_state["view"]=="chat":
    view_chat()
else:
    view_match()
