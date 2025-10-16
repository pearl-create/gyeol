# app.py
# -*- coding: utf-8 -*-
"""
결(結) — 멘티 전용 매칭 데모 앱 (아바타 3×2 그리드 + 파일명 숨김 + 대화신청 + 안정판)
- CSV 파일: 멘토더미.csv (자동 인코딩/구분자 감지, /mnt/data 우선)
- 아바타: 오직 ./avatars 폴더만 스캔, 3×2 그리드, 파일명/캡션 숨김, 선택 테두리
- 안전: avatars가 파일이거나 없을 때도 crash 없이 기본 아바타 표시
- 결과 카드에 "💬 대화 신청하기" 버튼 + 신청 내역 표시
"""

import io, base64
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Set

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
COMM_MODES = ["대면 만남", "화상채팅", "일반 채팅"]
TIME_SLOTS = ["오전", "오후", "저녁", "밤"]
DAYS = ["월", "화", "수", "목", "금", "토", "일"]
STYLES = ["연두부형", "분위기메이커형", "효율추구형", "댕댕이형", "감성 충만형", "냉철한 조언자형"]
PURPOSES = ["진로 / 커리어 조언", "학업 / 전문지식 조언", "사회, 인생 경험 공유", "정서적 지지와 대화"]
TOPIC_PREFS = ["진로·직업", "학업·전문 지식", "인생 경험·삶의 가치관", "대중문화·취미", "사회 문제·시사", "건강·웰빙"]
OCCUPATION_MAJORS = ["교육", "법률/행정", "연구개발/ IT", "예술/디자인", "의학/보건", "기타"]

# ==============================
# 2) 전문 스타일
# ==============================
def inject_style():
    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(1100px 700px at 18% 8%, #eef3fb 0%, #dde5f3 45%, #cfd8e8 100%);
    }
    [data-testid="stHeader"] { background: transparent; }
    .block-container { max-width: 920px; padding-top: 2rem; }
    .stButton>button {
        background: linear-gradient(180deg, #3b82f6 0%, #2563eb 100%);
        color: #fff; border: none; border-radius: 12px; font-weight: 600;
        box-shadow: 0 6px 12px rgba(37,99,235,0.28);
    }
    .stButton>button:hover { filter: brightness(1.05); }
    .stDownloadButton>button {
        background: linear-gradient(180deg, #0ea5e9 0%, #0284c7 100%);
        color: #fff; border: none; border-radius: 12px; font-weight: 600;
        box-shadow: 0 6px 12px rgba(2,132,199,0.25);
    }
    /* 아바타 타일 */
    .gyeol-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
    .gyeol-avatar {
        width: 100%; border-radius: 14px; display:block;
        box-shadow: 0 2px 8px rgba(0,0,0,.06);
        border: 2px solid rgba(255,255,255,0.6);
    }
    .gyeol-card { padding: 6px; border-radius: 16px; background: rgba(255,255,255,0.72); backdrop-filter: blur(6px); }
    .gyeol-avatar.selected { outline: 3px solid #60a5fa; box-shadow: 0 12px 26px rgba(96,165,250,.35); }
    .gyeol-pick { margin-top: .35rem; }
    .gyeol-ghost { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

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
                        # 불필요 인덱스 컬럼 제거
                        bad = [c for c in df.columns if str(c).lower().startswith("unnamed")]
                        if bad:
                            df = df.drop(columns=bad)
                        st.session_state["mentor_csv_path"] = str(f)
                        return df
                except Exception:
                    continue
    # 기본 한 명 (앱 보장)
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
# 4) 아바타 로더 (./avatars만, 완전 안전)
# ==============================
def _img_to_data_url(p: Path) -> Tuple[str, Optional[bytes]]:
    """로컬 이미지 파일을 data URL로 변환 (파일명/캡션 숨김에 유용)"""
    mime = "image/png"
    ext = p.suffix.lower()
    if ext in [".jpg", ".jpeg"]:
        mime = "image/jpeg"
    elif ext == ".webp":
        mime = "image/webp"
    b = p.read_bytes()
    b64 = base64.b64encode(b).decode("utf-8")
    return f"data:{mime};base64,{b64}", b

def load_fixed_avatars() -> List[Tuple[str, Optional[bytes]]]:
    """
    반환: [(data_url, raw_bytes or None), ...]
    - 오직 ./avatars 폴더의 png/jpg/jpeg/webp만 사용
    - 폴더가 없거나 비어있으면 기본 SVG 아바타 1개 제공
    - 절대 NotADirectoryError가 발생하지 않음
    """
    exts = {".png", ".jpg", ".jpeg", ".webp"}
    items: List[Tuple[str, Optional[bytes]]] = []

    avatars_dir = Path.cwd() / "avatars"
    if avatars_dir.exists() and avatars_dir.is_dir():
        for p in sorted(avatars_dir.iterdir()):
            if p.is_file() and p.suffix.lower() in exts:
                try:
                    items.append(_img_to_data_url(p))
                except Exception:
                    continue  # 손상 파일은 건너뜀

    if not items:
        # 기본 SVG 아바타 1개
        default_svg = """
        <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
          <circle cx="100" cy="100" r="90" fill="#e0e7ff" stroke="#93c5fd" stroke-width="5"/>
          <circle cx="100" cy="85" r="35" fill="#bfdbfe"/>
          <path d="M35,180 a65,65 0 0,1 130,0" fill="#93c5fd"/>
        </svg>
        """
        b64 = base64.b64encode(default_svg.encode("utf-8")).decode("utf-8")
        items = [(f"data:image/svg+xml;base64,{b64}", None)]

    return items

# ==============================
# 5) 점수 계산
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
# 6) 페이지 기본
# ==============================
st.set_page_config(page_title="결 — 멘토 추천 데모", page_icon="🤝", layout="centered")
inject_style()
st.title("결 — 멘토 추천 체험(멘티 전용)")
mentors_df = load_default_csv()
src = st.session_state.get("mentor_csv_path", "(기본 더미)")
st.caption(f"멘토 데이터 세트 로드됨: {len(mentors_df)}명 · 경로: {src}")

# ==============================
# 7) 아바타 선택 (3×2, 파일명 숨김)
# ==============================
st.markdown("---")
st.subheader("2) 연결될 준비")

avatars = load_fixed_avatars()        # [(data_url, bytes/None), ...]
MAX_SHOW = 6
SHOW = min(len(avatars), MAX_SHOW)

if "selected_avatar_index" not in st.session_state:
    st.session_state["selected_avatar_index"] = 0

# 그리드 렌더 (3×2)
st.markdown("<div class='gyeol-card'><div class='gyeol-grid'>", unsafe_allow_html=True)

def _avatar_tile(data_url: str, idx: int, selected: bool):
    cls = "gyeol-avatar selected" if selected else "gyeol-avatar"
    st.markdown(f"<img src='{data_url}' class='{cls}'/>", unsafe_allow_html=True)
    # 라벨 없이 클릭 버튼 (시각적 높이 맞춤 위해 'ghost' 클래스 사용)
    if st.button(" ", key=f"pick_{idx},btn", use_container_width=True):
        st.session_state["selected_avatar_index"] = idx
        # 선택 bytes 저장
        st.session_state["avatar_bytes"] = avatars[idx][1]
    else:
        st.markdown("<div class='gyeol-ghost'>.</div>", unsafe_allow_html=True)

# 6개까지만 출력 (위 3개 + 아래 3개)
for idx in range(SHOW):
    col = st.columns(1)[0]  # grid는 CSS로, 버튼은 각 셀에서 렌더
    with col:
        data_url, _bytes = avatars[idx]
        sel = (st.session_state["selected_avatar_index"] == idx)
        _avatar_tile(data_url, idx, sel)

st.markdown("</div></div>", unsafe_allow_html=True)

# 초기 bytes 세팅(최초 로드 시)
if "avatar_bytes" not in st.session_state and SHOW:
    st.session_state["avatar_bytes"] = avatars[st.session_state["selected_avatar_index"]][1]

# ==============================
# 8) 설문 입력
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
# 9) 매칭 & 결과
# ==============================
scores = [{"idx": i, "score": compute_score(mentee, row)} for i, row in mentors_df.iterrows()]
ranked = sorted(scores, key=lambda x: x["score"], reverse=True)[:5]

st.markdown("---")
st.subheader("3) 추천 결과")

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
        if st.session_state.get("avatar_bytes"):
            st.image(st.session_state["avatar_bytes"], width=96)
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
