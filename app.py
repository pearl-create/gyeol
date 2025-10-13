# app.py
# -*- coding: utf-8 -*-
"""
결(結) — 멘티 전용 박람회 체험용 매칭 데모 앱 (통합 완성판)

통합 변경사항
1. CSV 파일명: '멘토더미.csv' (UTF-8/CP949/utf-8-sig 자동 인식)
2. CSV 구분자: ',', ';', '\t' 자동 감지
3. 로드 상태 표시 (경로·인코딩·구분자·명수)
4. 캐시 초기화 버튼 ("데이터 다시 불러오기")
5. 아바타 선택 시 파일명 숨김
6. 프로페셔널 UI 테마 적용 (그라데이션 + 유리효과)
"""

import io
from pathlib import Path
from typing import Set, Dict
import pandas as pd
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from streamlit_image_select import image_select

# =========================
# 상수
# =========================
GENDERS = ["남", "여", "기타"]
AGE_BANDS = [
    "만 13세~19세", "만 20세~29세", "만 30세~39세", "만 40세~49세",
    "만 50세~59세", "만 60세~69세", "만 70세~79세", "만 80세~89세", "만 90세 이상"
]
COMM_MODES  = ["대면 만남", "화상채팅", "일반 채팅"]
TIME_SLOTS  = ["오전", "오후", "저녁", "밤"]
DAYS        = ["월", "화", "수", "목", "금", "토", "일"]
STYLES = ["연두부형", "분위기메이커형", "효율추구형", "댕댕이형", "감성 충만형", "냉철한 조언자형"]
OCCUPATION_MAJORS = [
    "경영자","행정관리","의학/보건","법률/행정","교육","연구개발/ IT","예술/디자인","기술/기능",
    "서비스 전문","일반 사무","영업 원","판매","서비스","의료/보건 서비스","생산/제조",
    "건설/시설","농림수산업","운송/기계","운송 관리","청소 / 경비","단순노무","학생","전업주부",
    "구직자 / 최근 퇴사자 / 프리랜서(임시)","기타"
]
INTERESTS = {
    "여가/취미": ["독서","음악 감상","영화/드라마 감상","게임","운동/스포츠 관람","미술·전시 감상","여행","요리/베이킹","사진/영상 제작","춤/노래"],
    "학문/지적 관심사": ["인문학","사회과학","자연과학","수학/논리 퍼즐","IT/테크놀로지","환경/지속가능성"],
    "라이프스타일": ["패션/뷰티","건강/웰빙","자기계발","사회참여/봉사활동","재테크/투자","반려동물"],
    "대중문화": ["K-POP","아이돌/연예인","유튜브/스트리밍","웹툰/웹소설","스포츠 스타"],
    "성향": ["혼자 보내는 시간 선호","친구들과 어울리기 선호","실내 활동 선호","야외 활동 선호","새로움 추구","안정감 추구"],
}
PURPOSES   = ["진로 / 커리어 조언","학업 / 전문지식 조언","사회, 인생 경험 공유","정서적 지지와 대화"]
TOPIC_PREFS= ["진로·직업","학업·전문 지식","인생 경험·삶의 가치관","대중문화·취미","사회 문제·시사","건강·웰빙"]

COMPLEMENT_PAIRS = {
    ("연두부형","분위기메이커형"),("연두부형","냉철한 조언자형"),
    ("감성 충만형","효율추구형"),("댕댕이형","효율추구형"),
    ("분위기메이커형","냉철한 조언자형")
}
SIMILAR_MAJORS = {
    ("의학/보건","의료/보건 서비스"),("영업 원","판매"),("서비스","서비스 전문"),
    ("기술/기능","건설/시설"),("운송/기계","운송 관리"),("행정관리","일반 사무")
}

# =========================
# 스타일: 전문 테마 적용
# =========================
def inject_style():
    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at 20% 20%, #eef3fb, #dde5f3, #cfd8e8);
    }
    [data-testid="stHeader"] {background: transparent;}
    [data-testid="stSidebar"] {background: rgba(255,255,255,0.6);}
    .block-container {max-width: 900px; padding-top:2rem;}
    .stButton>button {
        background: linear-gradient(180deg, #3b82f6 0%, #2563eb 100%);
        color:white; border:none; border-radius:12px; font-weight:600;
        box-shadow:0 6px 12px rgba(37,99,235,0.3);
    }
    .stDownloadButton>button {
        background: linear-gradient(180deg, #0ea5e9 0%, #0284c7 100%);
        color:white; border:none; border-radius:12px; font-weight:600;
        box-shadow:0 6px 12px rgba(2,132,199,0.25);
    }
    .image-select__caption {display:none!important;}
    .image-select__image--selected {
        box-shadow: 0 0 0 3px #60a5fa, 0 8px 20px rgba(96,165,250,.4)!important;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================
# 데이터 로딩 (강건판)
# =========================
@st.cache_data(show_spinner=False)
def load_default_csv() -> pd.DataFrame:
    cand_paths = ["/mnt/data/멘토더미.csv","멘토더미.csv"]
    encodings = ["utf-8-sig","utf-8","cp949"]
    seps = [",",";","\t"]
    last_err=None
    for p in cand_paths:
        f = Path(p)
        if not f.exists(): continue
        for enc in encodings:
            for sep in seps:
                try:
                    df=pd.read_csv(f,encoding=enc,sep=sep)
                    if df.empty: continue
                    bad=[c for c in df.columns if str(c).lower().startswith("unnamed")]
                    if bad: df=df.drop(columns=bad)
                    for c in df.select_dtypes(include=["object"]).columns:
                        df[c]=df[c].astype(str).str.strip()
                    if "name" not in df.columns and "이름" in df.columns:
                        df=df.rename(columns={"이름":"name"})
                    st.session_state["mentor_csv_path"]=str(f)
                    st.session_state["mentor_csv_encoding"]=enc
                    st.session_state["mentor_csv_sep"]=sep
                    return df
                except Exception as e:
                    last_err=e; continue
    if last_err:
        st.info(f"CSV 파싱 실패로 기본 더미 사용 (오류: {type(last_err).__name__})")
    return pd.DataFrame([{
        "name":"김샘","gender":"남","age_band":"만 40세~49세","occupation_major":"교육",
        "occupation_minor":"고등학교 교사","comm_modes":"대면 만남, 일반 채팅",
        "comm_time":"오전, 오후","comm_days":"월, 수, 금","style":"연두부형",
        "interests":"독서, 인문학, 건강/웰빙",
        "purpose":"사회, 인생 경험 공유, 정서적 지지와 대화",
        "topic_prefs":"인생 경험·삶의 가치관, 건강·웰빙",
        "intro":"경청 중심의 상담을 합니다."
    }])

# =========================
# 함수 (점수 계산)
# =========================
def list_to_set(s:str)->Set[str]:
    if pd.isna(s) or not str(s).strip(): return set()
    return {x.strip() for x in str(s).replace(";",",").split(",") if x.strip()}

def ratio_overlap(a:Set[str],b:Set[str])->float:
    return len(a&b)/len(a|b) if a and b else 0.0

def style_score(ms,mt):
    if ms and mt:
        if ms==mt: return 5
        if (ms,mt) in COMPLEMENT_PAIRS or (mt,ms) in COMPLEMENT_PAIRS: return 10
        return 3
    return 0

def major_score(wanted:Set[str],mentor:str)->int:
    if not mentor: return 0
    if mentor in wanted: return 12
    for a,b in SIMILAR_MAJORS:
        if (a in wanted and mentor==b) or (b in wanted and mentor==a): return 6
    return 0

def age_preference_score(preferred:Set[str],band:str)->int:
    if not preferred or not band: return 0
    idx={k:i for i,k in enumerate(AGE_BANDS)}
    band=next((b for b in AGE_BANDS if b in band),band)
    if band in preferred: return 6
    if band in idx:
        for p in preferred:
            if p in idx and abs(idx[p]-idx[band])==1: return 2
    return 0

def tfidf_similarity(a,b):
    a,b=(a or "").strip(),(b or "").strip()
    if not a or not b: return 0.0
    v=TfidfVectorizer(max_features=500,ngram_range=(1,2))
    X=v.fit_transform([a,b])
    return float(cosine_similarity(X[0],X[1])[0,0])

def compute_score(mentee,mentor):
    mc=lambda k:set(list_to_set(mentor.get(k,"")))
    s_p=round(ratio_overlap(mentee["purpose"],mc("purpose"))*18+ratio_overlap(mentee["topics"],mc("topic_prefs"))*12)
    s_c=round(ratio_overlap(mentee["comm_modes"],mc("comm_modes"))*8+ratio_overlap(mentee["time_slots"],mc("comm_time"))*6+ratio_overlap(mentee["days"],mc("comm_days"))*6)
    s_i=round(ratio_overlap(mentee["interests"],mc("interests"))*20)
    s_f=major_score(mentee["wanted_majors"],str(mentor.get("occupation_major","")).strip())+age_preference_score(mentee["wanted_mentor_ages"],str(mentor.get("age_band","")).strip())
    s_t=round(tfidf_similarity(mentee.get("note",""),str(mentor.get("intro","")))*10)
    s_s=style_score(mentee.get("style",""),str(mentor.get("style","")))
    tot=int(max(0,min(100,s_p+s_c+s_i+s_f+s_t+s_s)))
    return {"total":tot,"breakdown":{"목적·주제":s_p,"소통 선호":s_c,"관심사/성향":s_i,"멘토 적합도":s_f,"텍스트":s_t,"스타일":s_s}}

# =========================
# 페이지 세팅
# =========================
st.set_page_config(page_title="결 — 멘토 추천 데모",page_icon="🤝",layout="centered")
inject_style()
st.title("결 — 멘토 추천 체험(멘티 전용)")
st.caption("입력 데이터는 체험 종료 시 삭제됩니다. 다운로드/QR저장 외엔 서버에 남지 않습니다.")

# =========================
# CSV 로드 및 상태 표시
# =========================
mentors_df = load_default_csv()
src=st.session_state.get("mentor_csv_path","(기본 더미)")
enc=st.session_state.get("mentor_csv_encoding","-")
sep=st.session_state.get("mentor_csv_sep","-")
st.caption(f"멘토 데이터 세트 로드됨: {len(mentors_df)}명 · 경로: {src} · 인코딩: {enc} · 구분자: {sep}")
if st.button("데이터 다시 불러오기",use_container_width=True):
    load_default_csv.clear()
    st.rerun()

# =========================
# 아바타 선택
# =========================
def load_fixed_avatars():
    exts={".png",".jpg",".jpeg",".webp"}
    paths=[]
    for base in [Path.cwd()/ "avatars",Path.cwd()]:
        if base.exists():
            for p in base.iterdir():
                if p.is_file() and p.suffix.lower() in exts: paths.append(str(p))
    seen=set(); uniq=[]
    for p in paths:
        if p not in seen: uniq.append(p); seen.add(p)
    return uniq

st.markdown("---")
st.subheader("2) 연결될 준비")

avatars=load_fixed_avatars()
if avatars:
    selected=image_select(label="",images=avatars,captions=None,use_container_width=True,return_value="original",key="avatar")
    if selected:
        with open(selected,"rb") as f:
            st.session_state["selected_avatar_bytes"]=f.read()
else:
    st.warning("avatars 폴더 또는 루트에서 이미지 파일을 찾지 못했습니다.")

# =========================
# 입력 폼
# =========================
with st.form("mentee_form"):
    name=st.text_input("이름","")
    gender=st.radio("성별",GENDERS,horizontal=True,index=0)
    age=st.selectbox("나이대",AGE_BANDS,index=0)
    st.markdown("### 소통 선호")
    comm_modes=st.multiselect("소통 방법",COMM_MODES,["일반 채팅"])
    time_slots=st.multiselect("가능 시간",TIME_SLOTS,["오후","저녁"])
    days=st.multiselect("가능 요일",DAYS,["화","목"])
    style=st.selectbox("소통 스타일",STYLES)
    st.markdown("### 관심사·취향")
    interests=[]
    for g,it in INTERESTS.items(): interests.extend(st.multiselect(g,it))
    st.markdown("### 멘토링 목적·주제")
    purpose=st.multiselect("얻고 싶은 것",PURPOSES,["진로 / 커리어 조언"])
    topics=st.multiselect("대화 주제",TOPIC_PREFS,["진로·직업","학업·전문 지식"])
    st.markdown("### 희망 멘토 정보")
    wanted_majors=st.multiselect("관심 직군",OCCUPATION_MAJORS,["교육","법률/행정"])
    wanted_ages=st.multiselect("멘토 나이대",AGE_BANDS)
    note=st.text_area("요청사항(선택)",max_chars=120)
    submit=st.form_submit_button("추천 멘토 보기",use_container_width=True)

if not submit:
    st.info("설문을 입력하고 '추천 멘토 보기'를 눌러주세요.")
    st.stop()

# =========================
# 매칭
# =========================
mentee={"name":name.strip(),"gender":gender,"age_band":age,"comm_modes":set(comm_modes),
"time_slots":set(time_slots),"days":set(days),"style":style,"interests":set(interests),
"purpose":set(purpose),"topics":set(topics),"wanted_majors":set(wanted_majors),
"wanted_mentor_ages":set(wanted_ages),"note":note.strip()}

scores=[{"idx":i,"name":r.get("name",""),**compute_score(mentee,r)} for i,r in mentors_df.iterrows()]
ranked=sorted(scores,key=lambda x:x["total"],reverse=True)[:5]

st.markdown("---"); st.subheader("3) 추천 결과")
if not ranked: st.warning("추천 결과 없음."); st.stop()

for i,it in enumerate(ranked,start=1):
    r=mentors_df.loc[it["idx"]]
    with st.container(border=True):
        st.markdown(f"### #{i}. {r.get('name','(이름없음)')} — {r.get('occupation_major','')} ({r.get('age_band','')})")
        if "selected_avatar_bytes" in st.session_state: st.image(st.session_state["selected_avatar_bytes"],width=96)
        cols=st.columns(3)
        bd=it["breakdown"]
        with cols[0]:
            st.write(f"**총점:** {it['total']}점")
            for k,v in bd.items(): st.write(f"- {k}: {v}")
        with cols[1]:
            st.write("**소통 가능**")
            st.write(r.get("comm_modes","-")); st.write(r.get("comm_time","-")); st.write(r.get("comm_days","-"))
        with cols[2]:
            st.write("**관심사/주제**")
            st.write(r.get("interests","-")); st.write(r.get("purpose","-")); st.write(r.get("topic_prefs","-"))
        with st.expander("멘토 소개 보기"):
            st.write(r.get("intro",""))

buf=io.StringIO(); mentors_df.loc[[x["idx"] for x in ranked]].to_csv(buf,index=False,encoding="utf-8")
st.download_button("추천 결과 CSV 다운로드",buf.get
