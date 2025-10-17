# app.py
# -*- coding: utf-8 -*-
"""
결(結) — 멘티 전용 매칭 데모 (아바타 선택 제거 + URL 배경 이미지 + 대화신청)
- CSV: 멘토더미.csv (인코딩/구분자 자동 감지, /mnt/data 우선)
- 디자인: 페이지 전체 배경에 외부 이미지 URL 적용, 본문은 반투명 카드 처리
- 기능: 설문 → 점수 계산 → 상위 5명 카드 + "💬 대화 신청하기" + 신청 내역
"""

from pathlib import Path
from typing import Dict, Set

import pandas as pd
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ==============================
# 1) 기본 상수
# ==============================
GENDERS = ["남", "여", "기타"]
AGE_BANDS = [
    "만 13세~19세", "만 20세~29세", "만 30세~39세", "만 40세~49세",
    "만 50세~59세", "만 60세~69세", "만 70세~79세", "만 80세~89세", "만 90세 이상"
]
PURPOSES = ["진로 / 커리어 조언", "학업 / 전문지식 조언", "사회, 인생 경험 공유", "정서적 지지와 대화"]
TOPIC_PREFS = ["진로·직업", "학업·전문 지식", "인생 경험·삶의 가치관", "대중문화·취미", "사회 문제·시사", "건강·웰빙"]
OCCUPATION_MAJORS = ["교육", "법률/행정", "연구개발/ IT", "예술/디자인", "의학/보건", "기타"]

# ==============================
# 1) 기본 상수 (배경 파일 직접 로드)
# ==============================
from base64 import b64encode
import mimetypes

BACKGROUND_FILE = "logo_gyeol.png"  # ← 리포에 포함된 파일명

@st.cache_data(show_spinner=False)
def get_background_data_url() -> str | None:
    """logo_gyeol.png 파일을 base64 data URI로 변환"""
    p = Path(__file__).resolve().parent / BACKGROUND_FILE
    if not p.is_file():
        return None
    mime, _ = mimetypes.guess_type(p.name)
    mime = mime or "image/png"
    data = p.read_bytes()
    b64 = b64encode(data).decode("ascii")
    return f"data:{mime};base64,{b64}"

# ==============================
# 2) 스타일
# ==============================
# ==============================
# 2) 스타일
# ==============================
def inject_style():
    data_url = get_background_data_url()
    if data_url:
        bg_style = f"background-image: url('{data_url}'); background-size: cover; background-position: center; background-attachment: fixed;"
    else:
        bg_style = "background: radial-gradient(circle at 30% 30%, #14193F, #1B1F4B 25%, #10142C 60%, #080A1A 100%);"

    st.markdown(f"""
    <style>
      [data-testid="stAppViewContainer"] {{
        {bg_style}
      }}
      [data-testid="stHeader"] {{ background: transparent; }}
      .block-container {{
        max-width: 900px;
        padding: 2.25rem 2rem 3rem;
        background: rgba(255,255,255,0.72);
        border-radius: 20px;
        backdrop-filter: blur(4px);
        box-shadow: 0 6px 22px rgba(0,0,0,0.12);
      }}
      h1, h2, h3 {{ letter-spacing: .2px; }}
      .stButton>button {{
        background: linear-gradient(180deg, #3b82f6 0%, #2563eb 100%);
        color: #fff; border: none; border-radius: 12px; font-weight: 700;
        box-shadow: 0 6px 12px rgba(37,99,235,0.28);
      }}
      .stButton>button:hover {{ filter: brightness(1.05); }}
      .stDownloadButton>button {{
        background: linear-gradient(180deg, #0ea5e9 0%, #0284c7 100%);
        color: #fff; border: none; border-radius: 12px; font-weight: 700;
        box-shadow: 0 6px 12px rgba(2,132,199,0.25);
      }}
    </style>
    """, unsafe_allow_html=True)

    if not data_url:
        st.caption("💡 'logo_gyeol.png' 파일을 찾지 못했습니다. 같은 폴더에 넣어주세요.")


# ==============================
# 3) CSV 로딩 (강건)
# ==============================
@st.cache_data(show_spinner=False)
def load_default_csv() -> pd.DataFrame:
    """멘토더미.csv 자동 탐색 + 인코딩/구분자 자동 감지"""
    cand_paths = ["/mnt/data/멘토더미.csv", "멘토더미.csv"]
    encodings = ["utf-8-sig", "utf-8", "cp949"]
    seps = [",", ";", "\t"]
    for path in cand_paths:
        f = Path(path)
        if not f.exists():
            continue
        for enc in encodings:
            for sep in seps:
                try:
                    df = pd.read_csv(f, encoding=enc, sep=sep)
                    if not df.empty:
                        # 불필요 인덱스 열 제거
                        bad = [c for c in df.columns if str(c).lower().startswith("unnamed")]
                        if bad:
                            df = df.drop(columns=bad)
                        st.session_state["mentor_csv_path"] = str(f)
                        return df
                except Exception:
                    continue
    # 파일이 전혀 없을 때 최소 보장 더미
    return pd.DataFrame([{
        "name": "김샘", "gender": "남", "age_band": "만 40세~49세",
        "occupation_major": "교육",
        "interests": "독서, 인문학, 건강/웰빙",
        "purpose": "사회, 인생 경험 공유, 정서적 지지와 대화",
        "topic_prefs": "인생 경험·삶의 가치관, 건강·웰빙",
        "intro": "경청 중심의 상담을 합니다."
    }])

# ==============================
# 4) 점수 계산
# ==============================
def list_to_set(s) -> Set[str]:
    return {x.strip() for x in str(s).replace(";", ",").split(",") if x.strip()} if pd.notna(s) else set()

def ratio_overlap(a: Set[str], b: Set[str]) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0

def tfidf_similarity(a: str, b: str) -> float:
    a, b = (a or "").strip(), (b or "").strip()
    if not a or not b:
        return 0.0
    vec = TfidfVectorizer(max_features=400, ngram_range=(1, 2))
    X = vec.fit_transform([a, b])
    return float(cosine_similarity(X[0], X[1])[0, 0])

def compute_score(mentee: Dict, mentor_row: pd.Series) -> int:
    s = lambda k: list_to_set(mentor_row.get(k, ""))
    return int(
        ratio_overlap(mentee["purpose"], s("purpose")) * 20
        + ratio_overlap(mentee["topics"], s("topic_prefs")) * 10
        + ratio_overlap(mentee["interests"], s("interests")) * 20
        + tfidf_similarity(mentee["note"], mentor_row.get("intro", "")) * 10
    )

# ==============================
# 5) 페이지 기본
# ==============================
st.set_page_config(page_title="결: 멘티 데모", page_icon="🤝", layout="centered", initial_sidebar_state="collapsed")
inject_style()

st.title("연결될 준비")
mentors_df = load_default_csv()
src = st.session_state.get("mentor_csv_path", "(기본 더미)")
st.caption("멘토 데이터 세트 로드됨: {len(mentors_df)}명 · 경로: {src}")

# ==============================
# 6) 설문 입력
# ==============================
st.markdown("---")
st.subheader("")

with st.form("mentee_form"):
    name = st.text_input("이름", "")
    gender = st.radio("성별", GENDERS, horizontal=True)
    age_band = st.selectbox("나이대", AGE_BANDS)
    interests = st.multiselect("관심사", ["독서", "영화", "게임", "음악", "여행"])
    purpose = st.multiselect("멘토링 목적", PURPOSES, ["진로 / 커리어 조언"])
    topics = st.multiselect("대화 주제", TOPIC_PREFS, ["진로·직업", "학업·전문 지식"])
    note = st.text_area("한 줄 요청사항", max_chars=120, placeholder="예) 디자인 포트폴리오 피드백 부탁드려요!")
    submitted = st.form_submit_button("추천 멘토 보기", use_container_width=True)

if not submitted:
    st.info("설문을 입력하고 '추천 멘토 보기'를 눌러주세요.")
    st.stop()

mentee = {
    "purpose": set(purpose),
    "topics": set(topics),
    "interests": set(interests),
    "note": note,
}

# ==============================
# 7) 매칭 & 결과
# ==============================
scores = [{"idx": i, "score": compute_score(mentee, row)} for i, row in mentors_df.iterrows()]
ranked = sorted(scores, key=lambda x: x["score"], reverse=True)[:5]

st.markdown("---")
st.subheader("2) 추천 결과")

if "chat_requests" not in st.session_state:
    st.session_state["chat_requests"] = []

if not ranked:
    st.warning("추천 결과가 없습니다. 입력을 확인해 주세요.")
    st.stop()

for i, item in enumerate(ranked, start=1):
    r = mentors_df.loc[item["idx"]]
    with st.container(border=True):
        st.markdown(f"### #{i}. {r.get('name','(이름없음)')} ({r.get('occupation_major','')}, {r.get('age_band','')})")
        st.write(f"**소개:** {r.get('intro','')}")
        st.write(f"**점수:** {item['score']}")
        if st.button(f"💬 {r.get('name','')} 님에게 대화 신청하기", key=f"chat_{i}", use_container_width=True):
            if any(req["mentor"] == r.get("name","") for req in st.session_state["chat_requests"]):
                st.warning("이미 신청한 멘토입니다.")
            else:
                st.session_state["chat_requests"].append({"mentor": r.get("name",""), "status": "대기중"})
                st.success(f"{r.get('name','')} 님에게 대화 신청이 전송되었습니다!")

if st.session_state["chat_requests"]:
    st.markdown("---")
    st.subheader("📬 내 대화 신청 내역")
    for req in st.session_state["chat_requests"]:
        st.write(f"- {req['mentor']} 님 → {req['status']}")
