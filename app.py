# app.py
# -*- coding: utf-8 -*-
"""
결(結) — 멘티 전용 매칭 데모 (URL/로컬 배경 + 가중치 매칭 + 대화신청)
- CSV: 멘토더미.csv (인코딩/구분자 자동 감지, /mnt/data 우선)
- 입력: 네가 준 리스트들로 폼 구성 (목적/현재 직종/취미/전공계열/주제/요청메모)
- 매칭: 목적·취미·주제 겹침 + 현재직종→전공계열 맵핑 + 선호 전공계열 일치 + 메모-소개 TF-IDF
- 출력: 상위 5명 카드 + "💬 대화 신청하기" + 신청 내역
"""

from pathlib import Path
from typing import Dict, Set

import pandas as pd
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ==============================
# 1) 리스트(변수)
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

OCCUPATION_MAJORS = ["경영자(CEO / 사업주 / 임원 / 부서장)",
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
    "기타"]

INTELLECTUAL_INTERESTS = [
    "인문학 (철학, 역사, 문학 등)",
    "사회과학 (정치, 경제, 사회, 심리 등)",
    "자연과학 (물리, 화학, 생명과학 등)",
    "수학/논리 퍼즐",
    "IT/테크놀로지 (AI, 코딩, 로봇 등)",
    "환경/지속가능성",
]

COMMUNICATION_STYLES = [
    "연두부형: 조용하고 차분하게, 상대방 얘기를 경청하며 공감해 주는 편이에요.",
    "분위기메이커형: 활발하고 에너지가 넘쳐 대화를 이끌어가는 편이에요.",
    "효율추구형 : 주제를 체계적으로 정리하고 목표 지향적으로 대화하는 편이에요.",
    "댕댕이형: 자유롭고 편안하게, 즉흥적으로 대화를 이어가는 편이에요.",
    "감성 충만형: 감성적인 대화를 좋아하고 위로와 지지를 주는 편이에요. ",
    "냉철한 조언자형: 논리적이고 문제 해결 중심으로 조언을 주고받는 편이에요.",
]


# 현재 직종 → 전공계열 간소 맵핑 (멘토 CSV의 occupation_major와 연결용)
OCC_TO_MAJOR = {
    "경영자(CEO / 사업주 / 임원 / 부서장)": "기타",
    "행정관리(공공기관 관리자 / 기업 행정팀장 / 프로젝트 매니저)": "법률/행정",
    "보건(의사 / 치과의사 / 약사 / 간호사 / 한의사 / 물리치료사 / 간호조무사 / 재활치료사 / 요양보호사)": "의학/보건",
    "법률/행정(변호사 / 판사 / 검사 / 세무사 / 행정사)": "법률/행정",
    "교육(교수 / 교사 / 학원강사 / 연구원)": "교육",
    "연구개발/ IT(엔지니어 / 연구원 / 소프트웨어 개발자 / 데이터 분석가)": "연구개발/ IT",
    "예술/디자인(디자이너 / 예술가 / 작가 / 사진작가)": "예술/디자인",
    "기술(기술자 / 공학 기술자 / 실험실 기술자 / 회계사 / 건축기사)": "기타",
    "서비스 전문(상담사 / 심리치료사 / 사회복지사 / 코디네이터)": "기타",
    "일반 사무 (사무직원 / 경리 / 비서 / 고객 상담 / 문서 관리)": "기타",
    "영업(영업사원 / 마케팅 지원 / 고객 관리)": "기타",
    "판매(점원 / 슈퍼 / 편의점 직원 / 백화점 직원)": "기타",
    "생산/제조(공장 생산직 / 조립공 / 기계조작원 / 용접공)": "기타",
    "시설(배관공 / 전기공 / 건설노무자 / 목수)": "기타",
    "농림수산업(농부 / 축산업 / 어부 / 임업 종사자)": "기타",
    "운송/기계(트럭기사 / 버스기사 / 지게차 운전 / 기계조작원)": "기타",
    "청소 / 경비(경비원 / 환경미화원)": "기타",
    "학생 (초·중·고·대학생 / 대학원생)": "기타",
    "전업주부": "기타",
    "구직자 / 최근 퇴사자 / 프리랜서": "기타",
    "기타": "기타",
}

# ==============================
# 2) 배경 (로컬 파일 있으면 사용)
# ==============================
from base64 import b64encode
import mimetypes

BACKGROUND_FILE = "logo_gyeol.png"

@st.cache_data(show_spinner=False)
def get_background_data_url() -> str | None:
    p = Path(__file__).resolve().parent / BACKGROUND_FILE
    if not p.is_file():
        return None
    mime, _ = mimetypes.guess_type(p.name)
    mime = mime or "image/png"
    data = p.read_bytes()
    b64 = b64encode(data).decode("ascii")
    return f"data:{mime};base64,{b64}"

def inject_style():
    data_url = get_background_data_url()
    if data_url:
        bg_style = f"background-image: url('{data_url}'); background-size: cover; background-position: center; background-attachment: fixed;"
    else:
        # 로컬 이미지 없으면 그라디언트
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
    </style>
    """, unsafe_allow_html=True)

    if not data_url:
        st.caption("💡 'logo_gyeol.png' 파일을 찾지 못했습니다. 같은 폴더에 넣어주세요.")

# ==============================
# 3) CSV 로딩
# ==============================
@st.cache_data(show_spinner=False)
def load_default_csv() -> pd.DataFrame:
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
                        bad = [c for c in df.columns if str(c).lower().startswith("unnamed")]
                        if bad:
                            df = df.drop(columns=bad)
                        st.session_state["mentor_csv_path"] = str(f)
                        return df
                except Exception:
                    continue
    return pd.DataFrame([{
        "name": "김샘", "gender": "남", "age_band": "만 60세~69세",
        "occupation_major": "교육",
        "interests": "독서, 인문학",
        "purpose": "사회, 인생 경험 공유, 정서적 지지와 대화",
        "topic_prefs": "인생 경험·가치관, 건강·웰빙",
        "intro": "경청 중심의 상담을 합니다."
    }])

# ==============================
# 4) 매칭 유틸/스코어
# ==============================
def list_to_set(s) -> Set[str]:
    if pd.isna(s):
        return set()
    return {x.strip() for x in str(s).replace(";", ",").split(",") if x.strip()}

def ratio_overlap(a: Set[str], b: Set[str]) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0

def tfidf_similarity(a: str, b: str) -> float:
    a, b = (a or "").strip(), (b or "").strip()
    if not a or not b:
        return 0.0
    vec = TfidfVectorizer(max_features=400, ngram_range=(1, 2))
    X = vec.fit_transform([a, b])
    return float(cosine_similarity(X[0], X[1])[0, 0])

def map_current_occ_to_majors(selected_occs: Set[str]) -> Set[str]:
    """멘티가 고른 '현재 직종'들을 전공계열 세트로 변환"""
    majors = set()
    for occ in selected_occs:
        majors.add(OCC_TO_MAJOR.get(occ, "기타"))
    return majors

def compute_score(mentee: Dict, mentor_row: pd.Series) -> int:
    """
    가중치(총 100):
      - 목적 겹침 25
      - 취미/관심사 겹침 20
      - 대화 주제 겹침 10
      - 선호 전공계열 포함 20
      - 현재 직종→전공계열 매핑 일치 15
      - 요청 메모 vs 소개 TF-IDF 10
    """
    s = lambda k: list_to_set(mentor_row.get(k, ""))
    # mentor 단일 전공계열(문자열)과 멘티 선호/매핑 계열 비교
    mentor_major = (mentor_row.get("occupation_major", "") or "").strip()

    purpose_score = ratio_overlap(mentee["purpose"], s("purpose")) * 25
    hobby_score   = ratio_overlap(mentee["interests"], s("interests")) * 20
    topic_score   = ratio_overlap(mentee["topics"], s("topic_prefs")) * 10

    major_pref_score = 20.0 if mentor_major and mentor_major in mentee["pref_majors"] else 0.0

    mapped_majors = mentee["mapped_majors"]  # 현재직종 → 전공계열
    mapped_occ_score = 15.0 if mentor_major and mentor_major in mapped_majors else 0.0

    note_score = tfidf_similarity(mentee["note"], mentor_row.get("intro", "")) * 10

    total = purpose_score + hobby_score + topic_score + major_pref_score + mapped_occ_score + note_score
    return int(round(total))

# ==============================
# 5) 페이지 & 폼
# ==============================
st.set_page_config(page_title="결: 멘티 데모", page_icon="🤝", layout="centered", initial_sidebar_state="collapsed")
inject_style()

st.title("연결될 준비")
mentors_df = load_default_csv()
src = st.session_state.get("mentor_csv_path", "(기본 더미)")
st.caption(f"멘토 데이터 세트 로드됨: {len(mentors_df)}명 · 경로: {src}")

st.markdown("---")
st.subheader("1분만 투자하세요")

with st.form("mentee_form"):
    name = st.text_input("이름", "")
    gender = st.radio("성별", GENDERS, horizontal=True, index=0)
    age_band = st.selectbox("나이대", AGE_BANDS, index=0)

    # 핵심: 네가 준 리스트로 입력
    purpose = st.multiselect("멘토링 목적", PURPOSES, ["진로 / 커리어 조언"])
    desired_current_occ = st.multiselect("현재 직종", CURRENT_OCCUPATIONS)
    pref_majors = st.multiselect("원하는 멘토의 직종", OCCUPATION_MAJORS)
    interests = st.multiselect("취미", HOBBIES)

    # (선택) 지적 관심사/소통 스타일 입력만 받고 현재 점수에는 미사용
    intel = st.multiselect("지적 관심사", INTELLECTUAL_INTERESTS)
    comms = st.multiselect("소통 스타일", COMMUNICATION_STYLES)

    note = st.text_area("한 줄 요청사항", max_chars=120, placeholder="예) 간호사 퇴직하신 선배님을 찾습니다!")

    submitted = st.form_submit_button("추천 멘토 보기", use_container_width=True)

if not submitted:
    st.info("설문을 입력하고 '추천 멘토 보기'를 눌러주세요.")
    st.stop()

# 멘티 프로필 정리
mapped_majors = map_current_occ_to_majors(set(desired_current_occ))
mentee = {
    "purpose": set(purpose),
    "topics": set(topics),
    "interests": set(interests),
    "note": note,
    "pref_majors": set(pref_majors),
    "mapped_majors": mapped_majors,
}

# ==============================
# 6) 매칭 & 결과
# ==============================
scores = [{"idx": i, "score": compute_score(mentee, row)} for i, row in mentors_df.iterrows()]
ranked = sorted(scores, key=lambda x: x["score"], reverse=True)[:5]

st.markdown("---")
st.subheader("추천 결과 Top 5")

if "chat_requests" not in st.session_state:
    st.session_state["chat_requests"] = []

if not ranked:
    st.warning("추천 결과가 없습니다. 입력을 확인해 주세요.")
    st.stop()

for i, item in enumerate(ranked, start=1):
    r = mentors_df.loc[item["idx"]]
    with st.container(border=True):
        st.markdown(f"### #{i}. {r.get('name','(이름없음)')} · {r.get('age_band','')}")
        st.write(f"**현재 직종(전공계열):** {r.get('occupation_major','')}")
        st.write(f"**소개:** {r.get('intro','')}")
        st.write(f"**멘토 강점:** 목적({r.get('purpose','')}) · 관심사({r.get('interests','')}) · 주제({r.get('topic_prefs','')})")
        st.write(f"**매칭 점수:** {item['score']}")
        if mentee["pref_majors"] or mentee["mapped_majors"]:
            want = []
            if mentee["pref_majors"]:
                want.append("선호 전공계열: " + ", ".join(sorted(mentee['pref_majors'])))
            if mentee["mapped_majors"]:
                want.append("현재 직종(선택)→전공계열: " + ", ".join(sorted(mentee['mapped_majors'])))
            st.caption(" · ".join(want))
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
