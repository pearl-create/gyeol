# -*- coding: utf-8 -*-
"""
결(結) — 멘티 전용 박람회 체험용 매칭 데모 앱 (전체 코드)

변경 요약
- 멘토 데이터 입력 UI 제거(기본 CSV 자동 로드)
- "2) 멘티 설문" → "2) 연결될 준비" 제목 변경
- 나이대 선택 직후 아바타(사전 제공 6장) 선택 UI 추가
- style selectbox의 help를 삼중 따옴표로 교정(문법 오류 해결)
- 추천 카드 상단에 선택한 아바타 표시
- 간단한 **내부 테스트 패널(debug)** 추가: 점수 계산이 0~100인지 확인

실행
    streamlit run gyeol_mentee_demo_app.py
"""

import io
from typing import Set, Dict
import os

import pandas as pd
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# -----------------------------
# 상수/어휘 정의
# -----------------------------
GENDERS = ["남", "여", "기타"]
AGE_BANDS = [
    "만 13세~19세", "만 20세~29세", "만 30세~39세", "만 40세~49세",
    "만 50세~59세", "만 60세~69세", "만 70세~79세", "만 80세~89세", "만 90세 이상"
]

COMM_MODES = ["대면 만남", "화상채팅", "일반 채팅"]
TIME_SLOTS = ["오전", "오후", "저녁", "밤"]
DAYS = ["월", "화", "수", "목", "금", "토", "일"]

# 스타일 6종
STYLES = [
    "연두부형", "분위기메이커형", "효율추구형", "댕댕이형", "감성 충만형", "냉철한 조언자형"
]

# 직군(대분류)
OCCUPATION_MAJORS = [
    "경영자", "행정관리", "의학/보건", "법률/행정", "교육", "연구개발/ IT",
    "예술/디자인", "기술/기능", "서비스 전문", "일반 사무", "영업 원",
    "판매", "서비스", "의료/보건 서비스", "생산/제조", "건설/시설",
    "농림수산업", "운송/기계", "운송 관리", "청소 / 경비", "단순노무",
    "학생", "전업주부", "구직자 / 최근 퇴사자 / 프리랜서(임시)", "기타"
]

# 관심사 카테고리
INTERESTS = {
    "여가/취미": ["독서", "음악 감상", "영화/드라마 감상", "게임", "운동/스포츠 관람", "미술·전시 감상", "여행", "요리/베이킹", "사진/영상 제작", "춤/노래"],
    "학문/지적 관심사": ["인문학", "사회과학", "자연과학", "수학/논리 퍼즐", "IT/테크놀로지", "환경/지속가능성"],
    "라이프스타일": ["패션/뷰티", "건강/웰빙", "자기계발", "사회참여/봉사활동", "재테크/투자", "반려동물"],
    "대중문화": ["K-POP", "아이돌/연예인", "유튜브/스트리밍", "웹툰/웹소설", "스포츠 스타"],
    "성향": ["혼자 보내는 시간 선호", "친구들과 어울리기 선호", "실내 활동 선호", "야외 활동 선호", "새로움 추구", "안정감 추구"],
}

PURPOSES = ["진로 / 커리어 조언", "학업 / 전문지식 조언", "사회, 인생 경험 공유", "정서적 지지와 대화"]
TOPIC_PREFS = ["진로·직업", "학업·전문 지식", "인생 경험·삶의 가치관", "대중문화·취미", "사회 문제·시사", "건강·웰빙"]

# 스타일 상호 보완관계(가산점)
COMPLEMENT_PAIRS = {
    ("연두부형", "분위기메이커형"),
    ("연두부형", "냉철한 조언자형"),
    ("감성 충만형", "효율추구형"),
    ("댕댕이형", "효율추구형"),
    ("분위기메이커형", "냉철한 조언자형"),
}

# 직군 유사군(정확 일치가 아니어도 부분 가점)
SIMILAR_MAJORS = {
    ("의학/보건", "의료/보건 서비스"),
    ("영업 원", "판매"),
    ("서비스", "서비스 전문"),
    ("기술/기능", "건설/시설"),
    ("운송/기계", "운송 관리"),
    ("행정관리", "일반 사무"),
}

# -----------------------------
# 유틸 함수
# -----------------------------

def ratio_overlap(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def list_to_set(cell: str) -> Set[str]:
    if pd.isna(cell) or not str(cell).strip():
        return set()
    return {x.strip() for x in str(cell).replace(";", ",").split(",") if x.strip()}


def style_score(mentee_style: str, mentor_style: str) -> int:
    if mentee_style and mentor_style:
        if mentee_style == mentor_style:
            return 5  # 동일형 가점
        pair = (mentee_style, mentor_style)
        rev_pair = (mentor_style, mentee_style)
        if pair in COMPLEMENT_PAIRS or rev_pair in COMPLEMENT_PAIRS:
            return 10
        return 3
    return 0


def major_score(wanted_majors: Set[str], mentor_major: str) -> int:
    if not mentor_major:
        return 0
    if mentor_major in wanted_majors:
        return 12
    for a, b in SIMILAR_MAJORS:
        if (a in wanted_majors and mentor_major == b) or (b in wanted_majors and mentor_major == a):
            return 6
    return 0


def age_band_normalize(label: str) -> str:
    s = str(label).strip()
    if s.startswith("20") or "20" in s:
        return "만 20세~29세"
    if s.startswith("30") or "30" in s:
        return "만 30세~39세"
    if s.startswith("40") or "40" in s:
        return "만 40세~49세"
    if s.startswith("50") or "50" in s:
        return "만 50세~59세"
    if s.startswith("60") or "60" in s:
        return "만 60세~69세"
    if s.startswith("70") or "70" in s:
        return "만 70세~79세"
    if s.startswith("80") or "80" in s:
        return "만 80세~89세"
    if "90" in s:
        return "만 90세 이상"
    if "13" in s or "19" in s:
        return "만 13세~19세"
    return s


def age_preference_score(preferred: Set[str], mentor_age_band: str) -> int:
    if not preferred or not mentor_age_band:
        return 0
    mentor_age = age_band_normalize(mentor_age_band)
    if mentor_age in preferred:
        return 6
    idx_map = {k: i for i, k in enumerate(AGE_BANDS)}
    if mentor_age in idx_map:
        m_idx = idx_map[mentor_age]
        if any(abs(m_idx - idx_map[p]) == 1 for p in preferred if p in idx_map):
            return 2
    return 0


def tfidf_similarity(text_a: str, text_b: str) -> float:
    a = (text_a or "").strip()
    b = (text_b or "").strip()
    if not a or not b:
        return 0.0
    vec = TfidfVectorizer(max_features=500, ngram_range=(1, 2))
    X = vec.fit_transform([a, b])
    return float(cosine_similarity(X[0], X[1])[0, 0])


# -----------------------------
# 점수 계산
# -----------------------------

def compute_score(mentee: Dict, mentor_row: pd.Series) -> Dict:
    mentor_comm_modes = list_to_set(mentor_row.get("comm_modes", ""))
    mentor_comm_times = list_to_set(mentor_row.get("comm_time", ""))
    mentor_comm_days = list_to_set(mentor_row.get("comm_days", ""))
    mentor_interests = list_to_set(mentor_row.get("interests", ""))
    mentor_purposes = list_to_set(mentor_row.get("purpose", ""))
    mentor_topics = list_to_set(mentor_row.get("topic_prefs", ""))
    mentor_style = str(mentor_row.get("style", "")).strip()
    mentor_major = str(mentor_row.get("occupation_major", "")).strip()
    mentor_intro = str(mentor_row.get("intro", "")).strip()
    mentor_age_band = str(mentor_row.get("age_band", "")).strip()

    purpose_ratio = ratio_overlap(mentee["purpose"], mentor_purposes)
    topics_ratio = ratio_overlap(mentee["topics"], mentor_topics)
    s_purpose_topics = round(purpose_ratio * 18 + topics_ratio * 12)

    modes_ratio = ratio_overlap(mentee["comm_modes"], mentor_comm_modes)
    times_ratio = ratio_overlap(mentee["time_slots"], mentor_comm_times)
    days_ratio = ratio_overlap(mentee["days"], mentor_comm_days)
    s_comm = round(modes_ratio * 8 + times_ratio * 6 + days_ratio * 6)

    interest_ratio = ratio_overlap(mentee["interests"], mentor_interests)
    s_interests = round(interest_ratio * 20)

    s_major = major_score(mentee["wanted_majors"], mentor_major)
    s_age = age_preference_score(mentee["wanted_mentor_ages"], mentor_age_band)
    s_fit = s_major + s_age

    sim = tfidf_similarity(mentee.get("note", ""), mentor_intro)
    s_text = round(sim * 10)

    s_style = style_score(mentee.get("style", ""), mentor_style)

    total = s_purpose_topics + s_comm + s_interests + s_fit + s_text + s_style
    total = int(max(0, min(100, total)))

    return {
        "total": total,
        "breakdown": {
            "목적·주제": s_purpose_topics,
            "소통 선호": s_comm,
            "관심사/성향": s_interests,
            "멘토 적합도": s_fit,
            "텍스트": s_text,
            "스타일": s_style,
        }
    }


# -----------------------------
# UI
# -----------------------------
st.set_page_config(page_title="결 — 멘토 추천 데모", page_icon="🤝", layout="centered")

st.title("결 — 멘토 추천 체험(멘티 전용)")
st.caption("입력 데이터는 체험 종료 시 삭제됩니다. QR/다운로드 저장을 선택하지 않는 한 서버에 남지 않습니다.")

# 멘토 데이터 로딩 (입력 UI 숨김)
@st.cache_data(show_spinner=False)
def load_default_csv() -> pd.DataFrame:
    paths = [
        "gyeol_dummy_mentors_20.csv",
        "/mnt/data/gyeol_dummy_mentors_20.csv",
    ]
    for p in paths:
        try:
            return pd.read_csv(p)
        except Exception:
            continue
    return pd.DataFrame([
        {"name": "김샘", "gender": "남", "age_band": "40–49", "occupation_major": "교육",
         "occupation_minor": "고등학교 교사", "comm_modes": "대면 만남, 일반 채팅",
         "comm_time": "오전, 오후", "comm_days": "월, 수, 금", "style": "연두부형",
         "interests": "독서, 인문학, 건강/웰빙", "purpose": "사회, 인생 경험 공유, 정서적 지지와 대화",
         "topic_prefs": "인생 경험·삶의 가치관, 건강·웰빙", "intro": "경청 중심의 상담을 합니다."}
    ])

# 관리자(운영자) 전용 업로드: URL에 ?admin=1 이 있으면 보임
params = st.experimental_get_query_params()
ADMIN_MODE = params.get("admin", ["0"])[0] == "1"

if ADMIN_MODE:
    with st.expander("관리자 전용: 멘토 CSV 업로드", expanded=False):
        admin_up = st.file_uploader("멘토 데이터 CSV 업로드 (columns: name, gender, age_band, ...)", type=["csv"], key="admin_csv")
        if admin_up is not None:
            mentors_df = pd.read_csv(admin_up)
        else:
            mentors_df = load_default_csv()
else:
    mentors_df = load_default_csv()

st.caption(f"멘토 데이터 세트 로드됨: {len(mentors_df)}명")

st.markdown("---")
st.subheader("2) 연결될 준비")

# ---- 설문 입력 ----
with st.form("mentee_form"):
    name = st.text_input("이름", value="")
    gender = st.radio("성별", GENDERS, horizontal=True, index=0)
    age_band = st.selectbox("나이대", AGE_BANDS, index=0)

    # 아바타 선택 (사전 제공된 이미지 목록에서 선택)
    st.markdown("### 내 아바타 선택")
    AVATAR_PATHS = [
        "/mnt/data/KakaoTalk_20250919_142949391.png",
        "/mnt/data/KakaoTalk_20250919_142949391_01.png",
        "/mnt/data/KakaoTalk_20250919_142949391_02.png",
        "/mnt/data/KakaoTalk_20250919_142949391_03.png",
        "/mnt/data/KakaoTalk_20250919_142949391_04.png",
        "/mnt/data/KakaoTalk_20250919_142949391_05.png",
    ]

    # 존재하는 파일만 사용
    AVATAR_PATHS = [p for p in AVATAR_PATHS if os.path.exists(p)]

    # 만약 사전 제공 아바타가 하나도 없으면, 사용자 업로드로 대체
    uploaded_avatars = None
    if not AVATAR_PATHS:
        uploaded_avatars = st.file_uploader(
            "아바타 이미지 업로드 (여러 장 가능)",
            type=["png","jpg","jpeg","webp"],
            accept_multiple_files=True,
            key="avatar_uploader_backup",
            help="사전 제공 이미지가 없을 때만 노출됩니다.")
        if uploaded_avatars:
            AVATAR_PATHS = []  # 표시용 경로는 비우고, 아래에서 bytes 기반으로 처리

    # 썸네일 프리뷰(파일 경로가 있을 때만)
    avatar_labels = []
    if AVATAR_PATHS:
        cols_ava = st.columns(3)
        for i, p in enumerate(AVATAR_PATHS):
            with cols_ava[i % 3]:
                try:
                    st.image(p, caption=f"아바타 {i+1}", use_container_width=True)
                    avatar_labels.append(f"아바타 {i+1}")
                except Exception:
                    # 이미지 로드 실패 시 건너뜀
                    pass
    elif uploaded_avatars:
        cols_ava = st.columns(3)
        for i, f in enumerate(uploaded_avatars):
            with cols_ava[i % 3]:
                st.image(f, caption=f.name, use_container_width=True)
        avatar_labels = [f.name for f in uploaded_avatars]

    if avatar_labels:
        selected = st.selectbox("사용할 아바타 선택", avatar_labels, index=0)
        if AVATAR_PATHS:
            # 아바타 1..N 라벨을 경로에 매핑
            sel_idx = avatar_labels.index(selected)
            try:
                with open(AVATAR_PATHS[sel_idx], "rb") as f:
                    st.session_state['selected_avatar_bytes'] = f.read()
                    st.session_state['selected_avatar_name'] = selected
            except Exception:
                st.warning("선택한 아바타 이미지를 불러오지 못했습니다.")
        else:
            # 업로드 객체에서 직접 바이트 사용
            sel_idx = avatar_labels.index(selected)
            st.session_state['selected_avatar_bytes'] = uploaded_avatars[sel_idx].getvalue()
            st.session_state['selected_avatar_name'] = selected
    else:
        st.info("사용 가능한 아바타 이미지가 없습니다. 관리자에게 문의해주세요.")

    st.markdown("### 소통 선호")
    comm_modes = st.multiselect("선호하는 소통 방법(복수)", COMM_MODES, default=["일반 채팅"])
    time_slots = st.multiselect("소통 가능한 시간대(복수)", TIME_SLOTS, default=["오후", "저녁"])
    days = st.multiselect("소통 가능한 요일(복수)", DAYS, default=["화", "목"])

    style = st.selectbox(
        "소통 스타일 — 평소 대화 시 본인과 비슷한 유형",
        STYLES,
        help="""연두부형: 조용하고 차분, 경청·공감
분위기메이커형: 활발·주도
효율추구형: 목표·체계
댕댕이형: 자유롭고 즉흥
감성 충만형: 위로·지지 지향
냉철한 조언자형: 논리·문제 해결""",
    )

    st.markdown("### 관심사·취향")
    interests = []
    for grp, items in INTERESTS.items():
        interests.extend(
            st.multiselect(f"{grp}", items, default=[])
        )

    st.markdown("### 멘토링 목적·주제")
    purpose = st.multiselect(
        "멘토링을 통해 얻고 싶은 것(복수)",
        PURPOSES,
        default=["진로 / 커리어 조언", "학업 / 전문지식 조언"],
    )
    topics = st.multiselect(
        "주로 이야기하고 싶은 주제(복수)",
        TOPIC_PREFS,
        default=["진로·직업", "학업·전문 지식"],
    )

    st.markdown("### 희망 멘토 정보")
    wanted_majors = st.multiselect(
        "관심 멘토 직군(복수)", OCCUPATION_MAJORS,
        default=["연구개발/ IT", "교육", "법률/행정"],
    )
    wanted_mentor_ages = st.multiselect("멘토 선호 나이대(선택)", AGE_BANDS, default=[])

    note = st.text_area(
        "한 줄 요청사항(선택, 100자 이내)",
        max_chars=120,
        placeholder="예: 데이터 분석 직무 이직 준비 중, 포트폴리오 피드백 받고 싶어요",
    )

    submitted = st.form_submit_button("추천 멘토 보기", use_container_width=True)

if not submitted:
    st.info("왼쪽 설문을 입력하고 '추천 멘토 보기'를 눌러주세요.")
    st.stop()

# ---- 매칭 계산 ----
mentee_payload = {
    "name": (name or "").strip(),
    "gender": gender,
    "age_band": age_band,
    "comm_modes": set(comm_modes),
    "time_slots": set(time_slots),
    "days": set(days),
    "style": style,
    "interests": set(interests),
    "purpose": set(purpose),
    "topics": set(topics),
    "wanted_majors": set(wanted_majors),
    "wanted_mentor_ages": set(wanted_mentor_ages),
    "note": (note or "").strip(),
}

scores = []
for idx, row in mentors_df.iterrows():
    s = compute_score(mentee_payload, row)
    scores.append({"idx": idx, "name": row.get("name", ""), **s})

ranked = sorted(scores, key=lambda x: x["total"], reverse=True)[:5]

st.markdown("---")
st.subheader("3) 추천 결과")

if not ranked:
    st.warning("추천 결과가 없습니다. 설문 입력을 다시 확인해 주세요.")
    st.stop()

# 카드 표시
for i, item in enumerate(ranked, start=1):
    r = mentors_df.loc[item["idx"]]
    with st.container(border=True):
        st.markdown(
            f"### #{i}. {r.get('name','(이름없음)')} · {str(r.get('occupation_major','')).strip()} · {str(r.get('age_band','')).strip()}"
        )
        # 아바타 표시 (선택된 경우)
        if 'selected_avatar_bytes' in st.session_state:
            st.image(st.session_state['selected_avatar_bytes'], width=96)
        cols = st.columns(3)
        with cols[0]:
            st.write(f"**총점**: {item['total']}점")
            bd = item["breakdown"]
            st.write("- 목적·주제: ", bd['목적·주제'])
            st.write("- 소통 선호: ", bd['소통 선호'])
            st.write("- 관심사/성향: ", bd['관심사/성향'])
            st.write("- 멘토 적합도: ", bd['멘토 적합도'])
            st.write("- 텍스트: ", bd['텍스트'])
            st.write("- 스타일: ", bd['스타일'])
        with cols[1]:
            st.write("**소통 가능**")
            st.write("방법: ", r.get("comm_modes", "-"))
            st.write("시간대: ", r.get("comm_time", "-"))
            st.write("요일: ", r.get("comm_days", "-"))
            st.write("스타일: ", r.get("style", "-"))
        with cols[2]:
            st.write("**관심사/주제**")
            st.write("관심사: ", r.get("interests", "-"))
            st.write("목적: ", r.get("purpose", "-"))
            st.write("대화 주제: ", r.get("topic_prefs", "-"))
        with st.expander("멘토 소개 보기"):
            st.write(r.get("intro", ""))

# 결과 다운로드 (CSV)
export_cols = [
    "name", "gender", "age_band", "occupation_major", "occupation_minor",
    "comm_modes", "comm_time", "comm_days", "style", "interests",
    "purpose", "topic_prefs", "intro"
]
rec_df = mentors_df.loc[[x["idx"] for x in ranked], export_cols]
rec_buf = io.StringIO()
rec_df.to_csv(rec_buf, index=False)

st.download_button(
    label="추천 결과 5명 CSV 다운로드",
    data=rec_buf.getvalue().encode("utf-8-sig"),
    file_name="gyeol_recommended_mentors.csv",
    mime="text/csv",
    use_container_width=True,
)

# -----------------------------
# 내부 테스트(간단) — 앱 우측 하단에 표시
# -----------------------------
with st.expander("내부 테스트(디버그)"):
    try:
        if len(mentors_df) > 0:
            _dummy_mentee = {
                "purpose": {"진로 / 커리어 조언"},
                "topics": {"진로·직업"},
                "comm_modes": {"일반 채팅"},
                "time_slots": {"오후"},
                "days": {"화"},
                "interests": {"독서", "여행"},
                "wanted_majors": {"연구개발/ IT"},
                "wanted_mentor_ages": {"만 30세~39세"},
                "style": "연두부형",
                "note": "데이터 분야 진로 상담"
            }
            test_score = compute_score(_dummy_mentee, mentors_df.iloc[0])
            ok_range = 0 <= test_score["total"] <= 100
            st.write("테스트1 — 점수 범위(0~100):", "PASS" if ok_range else "FAIL", test_score)
        # 스타일 보완형 테스트
        from types import SimpleNamespace
        fake_row = SimpleNamespace(
            **{"comm_modes":"","comm_time":"","comm_days":"","interests":"",
               "purpose":"","topic_prefs":"","style":"분위기메이커형","occupation_major":"",
               "intro":"","age_band":"만 30세~39세"}
        )
        st.write("테스트2 — 스타일 보완 가산점:", compute_score({
            "purpose": set(),
            "topics": set(),
            "comm_modes": set(),
            "time_slots": set(),
            "days": set(),
            "interests": set(),
            "wanted_majors": set(),
            "wanted_mentor_ages": set(),
            "style": "연두부형",
            "note": ""
        }, pd.Series(vars(fake_row))))
    except Exception as e:
        st.error(f"내부 테스트 실패: {e}")

st.caption("※ 본 데모는 설명 가능한 규칙 + 경량 텍스트 유사도를 사용합니다. 가중치 조정 및 유사군 확장은 코드 상단 상수에서 쉽게 변경 가능합니다.")
