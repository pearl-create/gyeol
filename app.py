# app.py
# -*- coding: utf-8 -*-
"""
결(結) — 멘티 전용 매칭 데모 앱 (대화 신청 + 안정 통합판)
"""

import io, base64
from pathlib import Path
from typing import Set, Dict
import pandas as pd
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from streamlit_image_select import image_select

# ==============================
# 1. 상수
# ==============================
GENDERS = ["남", "여", "기타"]
AGE_BANDS = [
    "만 13세~19세", "만 20세~29세", "만 30세~39세", "만 40세~49세",
    "만 50세~59세", "만 60세~69세", "만 70세~79세", "만 80세~89세", "만 90세 이상"
]
COMM_MODES = ["대면 만남", "화상채팅", "일반 채팅"]
TIME_SLOTS = ["오전", "오후", "저녁", "밤"]
DAYS = ["월", "화", "수", "목", "금", "토", "일"]
STYLES = ["연두부형", "분위기메이커형", "효율추구형", "댕댕이형", "감성 충만형", "냉철한 조언자형"]
OCCUPATION_MAJORS = [
    "교육", "법률/행정", "연구개발/ IT", "예술/디자인", "의학/보건", "기타"
]
PURPOSES = ["진로 / 커리어 조언", "학업 / 전문지식 조언", "사회, 인생 경험 공유", "정서적 지지와 대화"]
TOPIC_PREFS = ["진로·직업", "학업·전문 지식", "인생 경험·삶의 가치관", "대중문화·취미", "사회 문제·시사", "건강·웰빙"]

# ==============================
# 2. UI 스타일
# ==============================
def inject_style():
    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at 20% 20%, #eef3fb, #dde5f3, #cfd8e8);
    }
    [data-testid="stHeader"] {background: transparent;}
    .block-container {max-width: 900px; padding-top: 2rem;}
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

# ==============================
# 3. 데이터 로딩
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
                        st.session_state["mentor_csv_path"] = str(f)
                        return df
                except Exception:
                    continue
    return pd.DataFrame([{
        "name": "김샘", "gender": "남", "age_band": "만 40세~49세",
        "occupation_major": "교육", "comm_modes": "대면 만남, 일반 채팅",
        "comm_time": "오전, 오후", "comm_days": "월, 수, 금", "style": "연두부형",
        "interests": "독서, 인문학, 건강/웰빙",
        "purpose": "사회, 인생 경험 공유, 정서적 지지와 대화",
        "topic_prefs": "인생 경험·삶의 가치관, 건강·웰빙",
        "intro": "경청 중심의 상담을 합니다."
    }])

# ==============================
# 4. 아바타 로더 (안전 + 기본 제공)
# ==============================
def load_fixed_avatars():
    exts = {".png", ".jpg", ".jpeg", ".webp"}
    paths = []

    # avatars 폴더 탐색
    avatars_dir = Path.cwd() / "avatars"
    if avatars_dir.exists() and avatars_dir.is_dir():
        for p in sorted(avatars_dir.iterdir()):
            if p.is_file() and p.suffix.lower() in exts:
                paths.append(str(p))
    else:
        print(f"[INFO] avatars 폴더가 없거나 폴더가 아닙니다. ({avatars_dir})")

    # 루트 폴더 탐색
    root = Path.cwd()
    if root.exists() and root.is_dir():
        for p in sorted(root.iterdir()):
            if p.is_file() and p.suffix.lower() in exts:
                paths.append(str(p))

    # 중복 제거
    seen, uniq = set(), []
    for p in paths:
        if p not in seen:
            uniq.append(p)
            seen.add(p)

    # 없을 경우 기본 아바타 생성
    if not uniq:
        st.warning("사용 가능한 아바타 이미지가 없어 기본 아바타를 표시합니다.")
        default_svg = """
        <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
          <circle cx="100" cy="100" r="90" fill="#e0e7ff" stroke="#93c5fd" stroke-width="5"/>
          <circle cx="100" cy="85" r="35" fill="#bfdbfe"/>
          <path d="M35,180 a65,65 0 0,1 130,0" fill="#93c5fd"/>
        </svg>
        """
        b64 = base64.b64encode(default_svg.encode("utf-8")).decode("utf-8")
        placeholder_path = f"data:image/svg+xml;base64,{b64}"
        return [placeholder_path]
    return uniq

# ==============================
# 5. 점수 계산 유틸
# ==============================
def list_to_set(s): return {x.strip() for x in str(s).replace(";", ",").split(",") if x.strip()} if pd.notna(s) else set()
def ratio_overlap(a,b): return len(a&b)/len(a|b) if a and b else 0
def tfidf_similarity(a,b):
    a,b=(a or "").strip(),(b or "").strip()
    if not a or not b: return 0
    vec=TfidfVectorizer(max_features=400,ngram_range=(1,2))
    X=vec.fit_transform([a,b])
    return float(cosine_similarity(X[0],X[1])[0,0])

def compute_score(mentee,mentor):
    def s(k): return list_to_set(mentor.get(k,""))
    return int(
        ratio_overlap(mentee["purpose"], s("purpose"))*20 +
        ratio_overlap(mentee["topics"], s("topic_prefs"))*10 +
        ratio_overlap(mentee["interests"], s("interests"))*20 +
        tfidf_similarity(mentee["note"], mentor.get("intro",""))*10
    )

# ==============================
# 6. 메인 페이지
# ==============================
st.set_page_config(page_title="결 — 멘토 추천 데모", page_icon="🤝", layout="centered")
inject_style()
st.title("결 — 멘토 추천 체험(멘티 전용)")
st.caption("입력 데이터는 체험 종료 시 삭제됩니다. QR/다운로드 저장 외엔 서버에 남지 않습니다.")

mentors_df = load_default_csv()
st.caption(f"멘토 데이터 세트 로드됨: {len(mentors_df)}명")

# ==============================
# 7. 아바타 선택
# ==============================
st.markdown("---")
st.subheader("2) 연결될 준비")

avatars = load_fixed_avatars()
if avatars:
    selected = image_select("", images=avatars, captions=None, use_container_width=True, return_value="original", key="avatar_select")
    if selected:
        with open(selected, "rb") as f:
            st.session_state["avatar_bytes"] = f.read()

# ==============================
# 8. 설문 입력 폼
# ==============================
with st.form("mentee_form"):
    name = st.text_input("이름", "")
    gender = st.radio("성별", GENDERS, horizontal=True)
    age_band = st.selectbox("나이대", AGE_BANDS)
    interests = st.multiselect("관심사", ["독서", "영화", "게임", "음악", "여행"])
    purpose = st.multiselect("멘토링 목적", PURPOSES, ["진로 / 커리어 조언"])
    topics = st.multiselect("대화 주제", TOPIC_PREFS, ["진로·직업", "학업·전문 지식"])
    note = st.text_area("한 줄 요청사항", max_chars=120)
    submitted = st.form_submit_button("추천 멘토 보기", use_container_width=True)

if not submitted: st.stop()

mentee = {"purpose": set(purpose), "topics": set(topics), "interests": set(interests), "note": note}

# ==============================
# 9. 추천 결과
# ==============================
scores = [{"idx": i, "score": compute_score(mentee, row)} for i, row in mentors_df.iterrows()]
ranked = sorted(scores, key=lambda x: x["score"], reverse=True)[:5]

st.markdown("---")
st.subheader("3) 추천 결과")

if "chat_requests" not in st.session_state:
    st.session_state["chat_requests"] = []

for i, item in enumerate(ranked, start=1):
    r = mentors_df.loc[item["idx"]]
    with st.container(border=True):
        st.markdown(f"### #{i}. {r['name']} ({r['occupation_major']}, {r['age_band']})")
        st.write(f"**소개:** {r['intro']}")
        st.write(f"**점수:** {item['score']}")
        if "avatar_bytes" in st.session_state:
            st.image(st.session_state["avatar_bytes"], width=96)
        if st.button(f"💬 {r['name']} 님에게 대화 신청하기", key=f"chat_{i}", use_container_width=True):
            if any(req["mentor"] == r["name"] for req in st.session_state["chat_requests"]):
                st.warning("이미 신청한 멘토입니다.")
            else:
                st.session_state["chat_requests"].append({"mentor": r["name"], "status": "대기중"})
                st.success(f"{r['name']} 님에게 대화 신청이 전송되었습니다!")

if st.session_state["chat_requests"]:
    st.markdown("---")
    st.subheader("📬 내 대화 신청 내역")
    for req in st.session_state["chat_requests"]:
        st.write(f"- {req['mentor']} 님 → {req['status']}")
