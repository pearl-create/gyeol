# app.py
# -*- coding: utf-8 -*-
"""
결(結) — 멘티 전용 박람회 체험용 매칭 데모 앱 (수정 반영판)

변경 요약
1) CSV 파일명: '멘토더미.csv' 사용 (CWD와 /mnt/data에서 탐색)
2) 아바타 선택: 파일명/캡션 숨김 (이미지 클릭만으로 선택)
3) UI: 전문적인 커스텀 테마(CSS) 적용 — 그라데이션 배경, 카드/버튼/태그 스타일

실행
- streamlit run app.py
- (권장) requirements.txt: streamlit-image-select==0.6.0
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
    "경영자", "행정관리", "의학/보건", "법률/행정", "교육", "연구개발/ IT",
    "예술/디자인", "기술/기능", "서비스 전문", "일반 사무", "영업 원",
    "판매", "서비스", "의료/보건 서비스", "생산/제조", "건설/시설",
    "농림수산업", "운송/기계", "운송 관리", "청소 / 경비", "단순노무",
    "학생", "전업주부", "구직자 / 최근 퇴사자 / 프리랜서(임시)", "기타"
]
INTERESTS = {
    "여가/취미": ["독서", "음악 감상", "영화/드라마 감상", "게임", "운동/스포츠 관람", "미술·전시 감상", "여행", "요리/베이킹", "사진/영상 제작", "춤/노래"],
    "학문/지적 관심사": ["인문학", "사회과학", "자연과학", "수학/논리 퍼즐", "IT/테크놀로지", "환경/지속가능성"],
    "라이프스타일": ["패션/뷰티", "건강/웰빙", "자기계발", "사회참여/봉사활동", "재테크/투자", "반려동물"],
    "대중문화": ["K-POP", "아이돌/연예인", "유튜브/스트리밍", "웹툰/웹소설", "스포츠 스타"],
    "성향": ["혼자 보내는 시간 선호", "친구들과 어울리기 선호", "실내 활동 선호", "야외 활동 선호", "새로움 추구", "안정감 추구"],
}
PURPOSES   = ["진로 / 커리어 조언", "학업 / 전문지식 조언", "사회, 인생 경험 공유", "정서적 지지와 대화"]
TOPIC_PREFS= ["진로·직업", "학업·전문 지식", "인생 경험·삶의 가치관", "대중문화·취미", "사회 문제·시사", "건강·웰빙"]

COMPLEMENT_PAIRS = {
    ("연두부형", "분위기메이커형"),
    ("연두부형", "냉철한 조언자형"),
    ("감성 충만형", "효율추구형"),
    ("댕댕이형", "효율추구형"),
    ("분위기메이커형", "냉철한 조언자형"),
}
SIMILAR_MAJORS = {
    ("의학/보건", "의료/보건 서비스"),
    ("영업 원", "판매"),
    ("서비스", "서비스 전문"),
    ("기술/기능", "건설/시설"),
    ("운송/기계", "운송 관리"),
    ("행정관리", "일반 사무"),
}

# =========================
# 스타일: 전문 테마 적용
# =========================
def inject_pro_style():
    st.markdown("""
    <style>
    /* 배경 (은은한 그라데이션) */
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(1200px 800px at 20% 0%, #f7fbff 0%, #eef3f9 40%, #e9eef6 70%, #e8ecf4 100%);
    }
    /* 사이드/헤더 크롬 톤 통일 */
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { background: rgba(255,255,255,0.7) !important; }

    /* 카드 느낌 컨테이너 */
    .stContainer, .stMarkdown, .stDataFrame {
        font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Apple SD Gothic Neo", "Noto Sans KR", "Helvetica Neue", Arial, "Apple Color Emoji", "Segoe UI Emoji";
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 4rem;
        max-width: 880px;
    }
    /* 기본 카드 테두리 */
    div[role="group"] > div, .stExpander, .stTabs, .stAlert {
        border-radius: 16px !important;
    }
    .st-emotion-cache-1r4qj8v, .st-emotion-cache-1r6slb0, .st-emotion-cache-1r6slb0, .st-emotion-cache-1jicfl2 {
        border-radius: 16px !important;
        box-shadow: 0 8px 24px rgba(28, 51, 84, 0.10);
        background: rgba(255,255,255, 0.72);
        backdrop-filter: blur(6px);
    }
    /* 버튼 (프라이머리) */
    .stButton > button {
        border-radius: 12px;
        padding: 0.7rem 1rem;
        font-weight: 600;
        border: 1px solid rgba(28,51,84,0.12);
        background: linear-gradient(180deg, #3b82f6 0%, #2563eb 100%);
        color: #fff;
        box-shadow: 0 8px 16px rgba(37, 99, 235, 0.25);
    }
    .stButton > button:hover { filter: brightness(1.04); }
    .stDownloadButton > button {
        border-radius: 12px;
        padding: 0.6rem 0.9rem;
        font-weight: 600;
        border: 1px solid rgba(28,51,84,0.12);
        background: linear-gradient(180deg, #0ea5e9 0%, #0284c7 100%);
        color: #fff;
        box-shadow: 0 8px 16px rgba(2, 132, 199, 0.22);
    }
    /* 멘토 카드 내부 타이포 */
    .mentor-card h3 { margin-bottom: 0.25rem; }
    .tag {
        display: inline-block; margin: 0 6px 6px 0; padding: 4px 10px;
        border-radius: 999px; background: #eef2ff; color: #3730a3; font-weight: 600; font-size: 12.5px;
        border: 1px solid rgba(55,48,163,0.15);
    }
    /* image-select 캡션 숨김 */
    .image-select__caption { display: none !important; }
    .image-select__container { gap: 12px; }
    .image-select__image { border-radius: 14px !important; }
    /* 선택된 아바타 강조(글로우) */
    .image-select__image--selected {
        box-shadow: 0 0 0 3px #60a5fa, 0 10px 24px rgba(96,165,250,.35) !important;
        transform: translateY(-1px);
    }
    /* 소제목 스타일 */
    h2, h3 { letter-spacing: -0.2px; }
    /* 푸터/메뉴 미니멀 */
    footer { visibility: hidden; height: 0; }
    #MainMenu { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# =========================
# 유틸
# =========================
def list_to_set(cell: str) -> Set[str]:
    if pd.isna(cell) or not str(cell).strip():
        return set()
    return {x.strip() for x in str(cell).replace(";", ",").split(",") if x.strip()}

def ratio_overlap(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)

def style_score(mentee_style: str, mentor_style: str) -> int:
    if mentee_style and mentor_style:
        if mentee_style == mentor_style:
            return 5
        if (mentee_style, mentor_style) in COMPLEMENT_PAIRS or (mentor_style, mentee_style) in COMPLEMENT_PAIRS:
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
    if "13" in s or "19" in s: return "만 13세~19세"
    if "20" in s: return "만 20세~29세"
    if "30" in s: return "만 30세~39세"
    if "40" in s: return "만 40세~49세"
    if "50" in s: return "만 50세~59세"
    if "60" in s: return "만 60세~69세"
    if "70" in s: return "만 70세~79세"
    if "80" in s: return "만 80세~89세"
    if "90" in s: return "만 90세 이상"
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

def compute_score(mentee: Dict, mentor_row: pd.Series) -> Dict:
    mentor_comm_modes = list_to_set(mentor_row.get("comm_modes", ""))
    mentor_comm_times = list_to_set(mentor_row.get("comm_time", ""))
    mentor_comm_days  = list_to_set(mentor_row.get("comm_days", ""))
    mentor_interests  = list_to_set(mentor_row.get("interests", ""))
    mentor_purposes   = list_to_set(mentor_row.get("purpose", ""))
    mentor_topics     = list_to_set(mentor_row.get("topic_prefs", ""))
    mentor_style      = str(mentor_row.get("style", "")).strip()
    mentor_major      = str(mentor_row.get("occupation_major", "")).strip()
    mentor_intro      = str(mentor_row.get("intro", "")).strip()
    mentor_age_band   = str(mentor_row.get("age_band", "")).strip()

    s_purpose_topics = round(ratio_overlap(mentee["purpose"], mentor_purposes) * 18
                             + ratio_overlap(mentee["topics"], mentor_topics) * 12)
    s_comm = round(ratio_overlap(mentee["comm_modes"], mentor_comm_modes) * 8
                   + ratio_overlap(mentee["time_slots"], mentor_comm_times) * 6
                   + ratio_overlap(mentee["days"], mentor_comm_days) * 6)
    s_interests = round(ratio_overlap(mentee["interests"], mentor_interests) * 20)
    s_fit  = major_score(mentee["wanted_majors"], mentor_major) + \
             age_preference_score(mentee["wanted_mentor_ages"], mentor_age_band)
    s_text = round(tfidf_similarity(mentee.get("note", ""), mentor_intro) * 10)
    s_style= style_score(mentee.get("style", ""), mentor_style)

    total = int(max(0, min(100, s_purpose_topics + s_comm + s_interests + s_fit + s_text + s_style)))
    return {"total": total, "breakdown": {
        "목적·주제": s_purpose_topics, "소통 선호": s_comm, "관심사/성향": s_interests,
        "멘토 적합도": s_fit, "텍스트": s_text, "스타일": s_style
    }}

# =========================
# 페이지 / 스타일
# =========================
st.set_page_config(page_title="결 — 멘토 추천 데모", page_icon="🤝", layout="centered")
inject_pro_style()
st.title("결 — 멘토 추천 체험(멘티 전용)")
st.caption("입력 데이터는 체험 종료 시 삭제됩니다. QR/다운로드 저장을 선택하지 않는 한 서버에 남지 않습니다.")

# =========================
# 데이터 로딩
# =========================
@st.cache_data(show_spinner=False)
def load_default_csv() -> pd.DataFrame:
    """
    1순위: ./멘토더미.csv
    2순위: /mnt/data/멘토더미.csv
    """
    for p in ["멘토더미.csv", "/mnt/data/멘토더미.csv"]:
        try:
            return pd.read_csv(p, encoding="utf-8-sig")
        except Exception:
            try:
                return pd.read_csv(p)  # fallback
            except Exception:
                pass
    # 최소 더미 1명
    return pd.DataFrame([{
        "name":"김샘","gender":"남","age_band":"만 40세~49세","occupation_major":"교육",
        "occupation_minor":"고등학교 교사","comm_modes":"대면 만남, 일반 채팅",
        "comm_time":"오전, 오후","comm_days":"월, 수, 금","style":"연두부형",
        "interests":"독서, 인문학, 건강/웰빙",
        "purpose":"사회, 인생 경험 공유, 정서적 지지와 대화",
        "topic_prefs":"인생 경험·삶의 가치관, 건강·웰빙",
        "intro":"경청 중심의 상담을 합니다."
    }])

# 최신 API
params = st.query_params
ADMIN_MODE = params.get("admin", "0") == "1"

if ADMIN_MODE:
    with st.expander("관리자 전용: 멘토 CSV 업로드", expanded=False):
        up = st.file_uploader("멘토 데이터 CSV 업로드", type=["csv"])
        mentors_df = pd.read_csv(up) if up is not None else load_default_csv()
else:
    mentors_df = load_default_csv()

st.caption(f"멘토 데이터 세트 로드됨: {len(mentors_df)}명")

# =========================
# 아바타(고정 세트) 로더 — 폴더/루트 모두 스캔 + 파일/디렉터리 안전 처리
# =========================
def load_fixed_avatars() -> list[str]:
    """
    - avatars가 '폴더'면 해당 폴더의 png/jpg/jpeg/webp 스캔
    - 폴더가 아니거나 없으면 리포지토리 **루트**에서 동일 확장자 스캔
    - 두 곳 모두 결과를 합쳐 중복 제거
    """
    exts = {".png", ".jpg", ".jpeg", ".webp"}
    paths: list[str] = []

    av = Path.cwd() / "avatars"
    if av.exists() and av.is_dir():
        for p in sorted(av.iterdir()):
            if p.is_file() and p.suffix.lower() in exts:
                paths.append(str(p))

    root = Path.cwd()
    for p in sorted(root.iterdir()):
        if p.is_file() and p.suffix.lower() in exts:
            paths.append(str(p))

    # 중복 제거, 순서 유지
    seen, uniq = set(), []
    for p in paths:
        if p not in seen:
            uniq.append(p)
            seen.add(p)
    return uniq

# =========================
# UI — 2) 연결될 준비
# =========================
st.markdown("---")
st.subheader("2) 연결될 준비")

# ---- 아바타: 폼 바깥 (즉시 반응형) ----
st.markdown("### 내 아바타 선택")
avatar_paths = load_fixed_avatars()
if not avatar_paths:
    st.warning("루트 또는 avatars/에서 이미지 파일(PNG/JPG/WEBP)을 찾지 못했습니다.")
else:
    # 파일명/캡션 숨김: captions=None, label="" 설정
    selected_path = image_select(
        label="",
        images=avatar_paths,
        captions=None,                  # ← 파일명 표시 안 함
        use_container_width=True,
        return_value="original",
        key="avatar_image_select",
    )
    if selected_path:
        try:
            with open(selected_path, "rb") as f:
                st.session_state["selected_avatar_bytes"] = f.read()
                st.session_state["selected_avatar_name"]  = Path(selected_path).name  # 저장만, 화면엔 표시 안 함
        except Exception:
            st.warning("선택한 아바타 이미지를 불러오지 못했습니다.")

# ---- 설문 입력: 폼 안 (Submit 버튼 필수) ----
with st.form("mentee_form"):
    name     = st.text_input("이름", value="")
    gender   = st.radio("성별", GENDERS, horizontal=True, index=0)
    age_band = st.selectbox("나이대", AGE_BANDS, index=0)

    st.markdown("### 소통 선호")
    comm_modes = st.multiselect("선호하는 소통 방법(복수)", COMM_MODES, default=["일반 채팅"])
    time_slots = st.multiselect("소통 가능한 시간대(복수)", TIME_SLOTS, default=["오후", "저녁"])
    days       = st.multiselect("소통 가능한 요일(복수)", DAYS,       default=["화", "목"])

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
        interests.extend(st.multiselect(f"{grp}", items, default=[]))

    st.markdown("### 멘토링 목적·주제")
    purpose = st.multiselect("멘토링을 통해 얻고 싶은 것(복수)", PURPOSES,
                             default=["진로 / 커리어 조언", "학업 / 전문지식 조언"])
    topics  = st.multiselect("주로 이야기하고 싶은 주제(복수)", TOPIC_PREFS,
                             default=["진로·직업", "학업·전문 지식"])

    st.markdown("### 희망 멘토 정보")
    wanted_majors      = st.multiselect("관심 멘토 직군(복수)", OCCUPATION_MAJORS,
                                        default=["연구개발/ IT", "교육", "법률/행정"])
    wanted_mentor_ages = st.multiselect("멘토 선호 나이대(선택)", AGE_BANDS, default=[])

    note = st.text_area("한 줄 요청사항(선택, 100자 이내)", max_chars=120,
                        placeholder="예: 데이터 분석 직무 이직 준비 중, 포트폴리오 피드백 받고 싶어요")

    submitted = st.form_submit_button("추천 멘토 보기", use_container_width=True)

if not submitted:
    st.info("왼쪽 설문을 입력하고 '추천 멘토 보기'를 눌러주세요.")
    st.stop()

# =========================
# 매칭 & 결과
# =========================
if mentors_df is None or mentors_df.empty:
    st.error("멘토 데이터가 없습니다. (?admin=1에서 CSV 업로드 또는 기본 CSV 배치)")
    st.stop()

mentee = {
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
    s = compute_score(mentee, row)
    scores.append({"idx": idx, "name": row.get("name", ""), **s})

ranked = sorted(scores, key=lambda x: x["total"], reverse=True)[:5]

st.markdown("---")
st.subheader("3) 추천 결과")

if not ranked:
    st.warning("추천 결과가 없습니다. 설문 입력을 다시 확인해 주세요.")
    st.stop()

for i, item in enumerate(ranked, start=1):
    r = mentors_df.loc[item["idx"]]
    with st.container(border=True):
        st.markdown(f"<div class='mentor-card'><h3>#{i}. {r.get('name','(이름없음)')}</h3></div>", unsafe_allow_html=True)
        st.write(f"**직군**: {str(r.get('occupation_major','')).strip()} · **나이대**: {str(r.get('age_band','')).strip()}")
        if "selected_avatar_bytes" in st.session_state:
            st.image(st.session_state["selected_avatar_bytes"], width=96)
        cols = st.columns(3)
        with cols[0]:
            bd = item["breakdown"]
            st.write(f"**총점**: {item['total']}점")
            st.write("- 목적·주제:", bd["목적·주제"])
            st.write("- 소통 선호:", bd["소통 선호"])
            st.write("- 관심사/성향:", bd["관심사/성향"])
            st.write("- 멘토 적합도:", bd["멘토 적합도"])
            st.write("- 텍스트:", bd["텍스트"])
            st.write("- 스타일:", bd["스타일"])
        with cols[1]:
            st.write("**소통 가능**")
            st.write("방법:", r.get("comm_modes", "-"))
            st.write("시간대:", r.get("comm_time", "-"))
            st.write("요일:", r.get("comm_days", "-"))
            st.write("스타일:", r.get("style", "-"))
        with cols[2]:
            st.write("**관심사/주제**")
            st.write("관심사:", r.get("interests", "-"))
            st.write("목적:", r.get("purpose", "-"))
            st.write("대화 주제:", r.get("topic_prefs", "-"))
        with st.expander("멘토 소개 보기"):
            st.write(r.get("intro", ""))

# 다운로드
export_cols = [
    "name", "gender", "age_band", "occupation_major", "occupation_minor",
    "comm_modes", "comm_time", "comm_days", "style", "interests",
    "purpose", "topic_prefs", "intro",
]
rec_df = mentors_df.loc[[x["idx"] for x in ranked], export_cols]
buf = io.StringIO(); rec_df.to_csv(buf, index=False, encoding="utf-8")
st.download_button(
    "추천 결과 5명 CSV 다운로드",
    data=buf.getvalue().encode("utf-8-sig"),
    file_name="gyeol_recommended_mentors.csv",
    mime="text/csv",
    use_container_width=True,
)

st.caption("※ 규칙 기반 + 경량 텍스트 유사도 점수 조합. 가중치/보완쌍은 상단 상수에서 쉽게 조정 가능합니다.")
