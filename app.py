# app.py
# -*- coding: utf-8 -*-
"""
결(結) — 멘티 전용 매칭/검색 + 오늘의 질문 + 신고 시스템 (MVP)
- 프레임워크: Streamlit (단일 파일)
- 저장: SQLite (/mnt/data/gyeol.db)
- 멘토 데이터: /mnt/data/멘토더미.csv (UTF-8-SIG 우선, CP949 폴백)
- 핵심 기능:
  1) 멘티 회원가입(필드: 성별에 "밝히고 싶지 않음" 포함, 다중 태그 입력)
  2) 멘토 검색(필터 + 키워드) → <연결> → "잠시만 기다려주세요" → 고정 미트 링크 이동
  3) 오늘의 질문(매일 09:00 KST 자동 생성/로테이션) + 답변 + 공감 + 신고
  4) 신고 시스템(멘토 카드/답변 신고, 관리자 검토 전제 — 자동 블러 없음)
- 톤: 따뜻한 연결

주의: 배포 환경에서 외부 링크 자동 이동은 브라우저 보안정책에 따라 팝업 허용이 필요할 수 있습니다.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, date, time, timedelta
from pathlib import Path

import pandas as pd
import pytz
import streamlit as st
from typing import List, Dict, Any, Optional, Tuple

# =========================
# 0) 상수/유틸
# =========================
DB_PATH = Path("/mnt/data/gyeol.db")
MENTOR_CSV = Path("/mnt/data/멘토더미.csv")
KST = pytz.timezone("Asia/Seoul")
MEET_LINK = "https://meet.google.com/urw-iods-puy"  # 고정 링크 유지

GENDERS = ["남", "여", "기타", "밝히고 싶지 않음"]
AGE_BANDS = [
    "만 13세~19세",
    "만 20세~29세",
    "만 30세~39세",
    "만 40세~49세",
    "만 50세~59세",
    "만 60세~69세",
    "만 70세~79세",
    "만 80세~89세",
    "만 90세 이상",
]
CHANNELS = ["대면 만남", "화상채팅", "일반 채팅"]
DAYS = ["월", "화", "수", "목", "금", "토", "일"]
TIMES = ["오전", "오후", "저녁", "밤"]

# 직업군(대분류)
OCCUP_MAIN = [
    "경영자",
    "행정관리",
    "의학/보건",
    "법률/행정",
    "교육",
    "연구개발/ IT",
    "예술/디자인",
    "기술/기능",
    "서비스 전문",
    "일반 사무",
    "영업 원",
    "판매",
    "서비스",
    "의료/보건 서비스",
    "생산/제조",
    "건설/시설",
    "농림수산업",
    "운송/기계",
    "운송 관리",
    "청소 / 경비",
    "단순노무",
    "학생",
    "전업주부",
    "구직자 / 최근 퇴사자 / 프리랜서(임시)",
    "기타 (직접 입력)",
]

# 관심사 태그 (카테고리별)
INTEREST_TAGS = {
    "여가/취미": [
        "독서", "음악 감상", "영화/드라마 감상", "게임", "운동/스포츠 관람",
        "미술·전시 감상", "여행", "요리/베이킹", "사진/영상 제작", "춤/노래",
    ],
    "학문/지적": [
        "인문학", "사회과학", "자연과학", "수학/논리 퍼즐", "IT/테크놀로지", "환경/지속가능성",
    ],
    "라이프스타일": [
        "패션/뷰티", "건강/웰빙", "자기계발", "사회참여/봉사활동", "재테크/투자", "반려동물",
    ],
    "대중문화": [
        "K-POP", "아이돌/연예인", "유튜브/스트리밍", "웹툰/웹소설", "스포츠 스타",
    ],
    "성향": [
        "혼자 보내는 시간 선호", "친구들과 어울리기 선호", "실내 활동 선호", "야외 활동 선호",
        "새로움 추구", "안정감 추구",
    ],
}

TOPIC_CHOICES = [
    "진로·직업", "학업·전문 지식", "인생 경험·삶의 가치관", "대중문화·취미", "사회 문제·시사", "건강·웰빙",
]

STYLE_TYPES = [
    "연두부형", "분위기메이커형", "효율추구형", "댕댕이형", "감성 충만형", "냉철한 조언자형",
]

DAILY_QUESTION_SEED = [
    "요즘 당신에게 가장 필요한 한 마디는 무엇인가요?",
    "10년 전의 나에게 한 문장 조언을 보낸다면?",
    "가장 기억에 남는 멘토의 한마디는 무엇이었나요?",
    "최근에 작게나마 용기 냈던 순간을 들려주세요.",
    "마음이 힘들 때 당신을 버티게 하는 루틴은?",
]

# =========================
# 1) DB 초기화
# =========================
def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                gender TEXT,
                age_band TEXT,
                preferred_channels TEXT,
                available_days TEXT,
                available_times TEXT,
                occupations_main TEXT,
                occupations_detail TEXT,
                occupation_other TEXT,
                interests TEXT,
                topics TEXT,
                style_primary TEXT,
                help_text TEXT,
                created_at TEXT,
                status TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS mentors (
                mentor_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                headline TEXT,
                photo_url TEXT,
                occupations_main TEXT,
                occupations_detail TEXT,
                channels TEXT,
                available_days TEXT,
                available_times TEXT,
                interests TEXT,
                style_tags TEXT,
                bio TEXT,
                meet_link TEXT,
                is_published INTEGER,
                updated_at TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS connect_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                mentor_id INTEGER,
                created_at TEXT,
                search_context TEXT,
                redirect_link TEXT,
                status TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                qdate TEXT,
                text TEXT,
                author TEXT,
                status TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER,
                user_id INTEGER,
                age_band TEXT,
                text TEXT,
                likes INTEGER DEFAULT 0,
                reports INTEGER DEFAULT 0,
                visibility TEXT DEFAULT 'ok',
                created_at TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_type TEXT,  -- 'mentor' | 'answer'
                target_id INTEGER,
                user_id INTEGER,
                reason TEXT,
                created_at TEXT,
                status TEXT DEFAULT 'pending'
            )
            """
        )
        conn.commit()


# =========================
# 2) 멘토 CSV 로드 (초기 로딩 전용)
# =========================
def safe_read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        try:
            return pd.read_csv(path, encoding="cp949")
        except Exception:
            return pd.read_csv(path, engine="python")


def seed_mentors_if_empty():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS c FROM mentors")
        c = cur.fetchone()[0]
        if c > 0:
            return

    df = safe_read_csv(MENTOR_CSV)
    if df.empty:
        return

    # 컬럼 추정(유연하게 매핑)
    colmap = {
        'name': None,
        'headline': None,
        'photo_url': None,
        'occupations_main': None,
        'occupations_detail': None,
        'channels': None,
        'available_days': None,
        'available_times': None,
        'interests': None,
        'style_tags': None,
        'bio': None,
        'meet_link': None,
    }
    # 가능한 한국어 컬럼 후보들
    candidates = {
        'name': ["이름", "name", "성명"],
        'headline': ["한줄소개", "소개", "headline"],
        'photo_url': ["사진", "이미지", "photo_url", "image"],
        'occupations_main': ["직업대분류", "직업군", "occupations_main"],
        'occupations_detail': ["직무", "세부직무", "occupations_detail"],
        'channels': ["소통채널", "채널", "channels"],
        'available_days': ["가능요일", "요일", "available_days"],
        'available_times': ["가능시간대", "시간대", "available_times"],
        'interests': ["관심사", "태그", "interests"],
        'style_tags': ["스타일", "style_tags"],
        'bio': ["자기소개", "bio"],
        'meet_link': ["미트링크", "meet_link"],
    }

    for k, cand in candidates.items():
        for c in cand:
            if c in df.columns:
                colmap[k] = c
                break

    records = []
    for _, row in df.iterrows():
        rec = {
            'name': str(row.get(colmap['name'], '') or ''),
            'headline': str(row.get(colmap['headline'], '') or ''),
            'photo_url': str(row.get(colmap['photo_url'], '') or ''),
            'occupations_main': str(row.get(colmap['occupations_main'], '') or ''),
            'occupations_detail': str(row.get(colmap['occupations_detail'], '') or ''),
            'channels': str(row.get(colmap['channels'], '') or ''),
            'available_days': str(row.get(colmap['available_days'], '') or ''),
            'available_times': str(row.get(colmap['available_times'], '') or ''),
            'interests': str(row.get(colmap['interests'], '') or ''),
            'style_tags': str(row.get(colmap['style_tags'], '') or ''),
            'bio': str(row.get(colmap['bio'], '') or ''),
            'meet_link': str(row.get(colmap['meet_link'], '') or ''),
        }
        records.append(rec)

    with get_conn() as conn:
        cur = conn.cursor()
        for r in records:
            cur.execute(
                """
                INSERT INTO mentors (
                    name, headline, photo_url, occupations_main, occupations_detail,
                    channels, available_days, available_times, interests, style_tags,
                    bio, meet_link, is_published, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (
                    r['name'], r['headline'], r['photo_url'], r['occupations_main'], r['occupations_detail'],
                    r['channels'], r['available_days'], r['available_times'], r['interests'], r['style_tags'],
                    r['bio'], r['meet_link'] or MEET_LINK, datetime.now(KST).isoformat(),
                ),
            )
        conn.commit()


# =========================
# 3) 헬퍼: 직렬화/역직렬화
# =========================
def to_json(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False)
    except Exception:
        return "{}"


def from_json(s: Optional[str]) -> Any:
    if not s:
        return None
    try:
        return json.loads(s)
    except Exception:
        return None


# =========================
# 4) UI 스타일
# =========================
WARM_CSS = f"""
<style>
    .stApp {{
        background: linear-gradient(180deg, #fffaf7 0%, #fff 100%);
        font-family: 'Pretendard', ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto;
    }}
    .warm-card {{
        background: rgba(255, 255, 255, 0.75);
        backdrop-filter: blur(6px);
        border: 1px solid #f3e6df;
        border-radius: 18px;
        padding: 16px 18px;
        box-shadow: 0 8px 24px rgba(119, 60, 20, 0.06);
        margin-bottom: 12px;
    }}
    .warm-title {{
        color: #7b3e19;
        font-weight: 700;
    }}
    .muted {{ color: #8e705f; }}
    .tag {{
        display:inline-block; padding:4px 10px; border-radius:12px; margin: 2px; font-size:12px;
        background:#fff2ea; color:#7b3e19; border:1px solid #f3e6df;
    }}
    .pill {{
        display:inline-block; padding:4px 10px; border-radius:999px; margin: 2px; font-size:12px;
        background:#eaf6f1; color:#1f6b54; border:1px solid #d5eee4;
    }}
</style>
"""

# =========================
# 5) 페이지 구성
# =========================

def nav():
    st.sidebar.title("결 · 멘티")
    pg = st.sidebar.radio(
        "이동",
        ["홈", "회원가입", "멘토 검색", "오늘의 질문", "신고"],
    )
    return pg


# ---------- 회원가입 ----------

def page_signup():
    st.markdown("<h2 class='warm-title'>당신의 이야기가 누군가의 길잡이가 됩니다</h2>", unsafe_allow_html=True)
    st.write("아래 정보를 한 번만 입력하면, 언제든 수정할 수 있어요.")

    with st.form("signup_form", clear_on_submit=False):
        name = st.text_input("이름", max_chars=50)
        gender = st.selectbox("성별", GENDERS, index=0)
        age = st.selectbox("나이대", AGE_BANDS, index=0)

        st.markdown("---")
        st.subheader("소통 선호 & 가능 시간")
        ch = st.multiselect("선호하는 소통 방법", CHANNELS, default=["일반 채팅"])  # 다중
        days = st.multiselect("소통 가능한 요일", DAYS)
        times = st.multiselect("소통 가능한 시간대", TIMES)

        st.markdown("---")
        st.subheader("현재 직종")
        occ_main = st.multiselect("대분류(복수 선택 가능)", OCCUP_MAIN)
        occ_detail = st.text_input("세부 직무(쉼표로 복수 입력)")
        occ_other = st.text_input("기타(자유 입력)")

        st.markdown("---")
        st.subheader("관심사/취향 (태그)")
        selected_tags: List[str] = []
        for cat, tags in INTEREST_TAGS.items():
            sel = st.multiselect(f"{cat}", tags)
            selected_tags.extend(sel)

        st.markdown("---")
        st.subheader("선호하는 대화 주제")
        topics = st.multiselect("멘토링에서 주로 어떤 주제를 다루고 싶으신가요?", TOPIC_CHOICES)
        help_text = st.text_area("지금 가장 받고 싶은 도움(선택)", max_chars=500)

        st.markdown("---")
        st.subheader("소통 스타일")
        style = st.selectbox("본인과 가장 비슷한 유형 하나를 골라주세요", STYLE_TYPES)

        agree = st.checkbox("커뮤니티 가이드, 개인정보 처리, 외부 링크 안내를 확인했습니다.")

        submitted = st.form_submit_button("저장")
        if submitted:
            if not name or not agree:
                st.error("이름과 약관 동의는 필수입니다.")
            else:
                with get_conn() as conn:
                    conn.execute(
                        """
                        INSERT INTO users (
                            name, gender, age_band, preferred_channels, available_days, available_times,
                            occupations_main, occupations_detail, occupation_other, interests, topics,
                            style_primary, help_text, created_at, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            name, gender, age, to_json(ch), to_json(days), to_json(times),
                            to_json(occ_main), occ_detail, occ_other, to_json(selected_tags), to_json(topics),
                            style, help_text, datetime.now(KST).isoformat(), "active",
                        ),
                    )
                    conn.commit()
                st.success("저장되었습니다. 환영해요! ✨")


# ---------- 멘토 검색 ----------

def parse_filter_list(s: str) -> List[str]:
    if not s:
        return []
    # CSV에서 세퍼레이터가 섞일 수 있어 유연 파싱
    parts = []
    for sep in ["|", ",", "/", ";", " "]:
        if sep in s:
            parts = [p.strip() for p in s.split(sep) if str(p).strip()]
            break
    return parts or [s]


def search_mentors(keyword: str, filters: Dict[str, List[str]]) -> List[sqlite3.Row]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM mentors WHERE is_published = 1")
        rows = [dict(r) for r in cur.fetchall()]

    def match(row: Dict[str, Any]) -> bool:
        text_blob = " ".join([
            str(row.get("name", "")),
            str(row.get("headline", "")),
            str(row.get("bio", "")),
            str(row.get("occupations_detail", "")),
            str(row.get("interests", "")),
        ])
        if keyword and (keyword.lower() not in text_blob.lower()):
            return False

        # 채널/요일/시간/직업/관심사 필터
        def includes_any(field: str, wanted: List[str]) -> bool:
            if not wanted:
                return True
            vals = parse_filter_list(str(row.get(field, "")))
            return any(w in vals for w in wanted)

        if not includes_any("channels", filters.get("channels", [])):
            return False
        if not includes_any("available_days", filters.get("days", [])):
            return False
        if not includes_any("available_times", filters.get("times", [])):
            return False
        if not includes_any("occupations_main", filters.get("occ_main", [])):
            return False
        if not includes_any("interests", filters.get("interests", [])):
            return False
        return True

    return [sqlite3.Row(dict(zip(rows[0].keys(), r.values()))) if rows else r for r in filter(match, rows)]


def log_connect(user_id: Optional[int], mentor_id: int, search_ctx: Dict[str, Any], status: str):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO connect_logs (user_id, mentor_id, created_at, search_context, redirect_link, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id, mentor_id, datetime.now(KST).isoformat(), to_json(search_ctx), MEET_LINK, status,
            ),
        )
        conn.commit()


def connect_and_redirect(mentor_id: int, user_id: Optional[int], search_ctx: Dict[str, Any]):
    log_connect(user_id, mentor_id, search_ctx, status="redirected")
    with st.spinner("잠시만 기다려주세요… 따뜻한 만남을 준비하고 있어요."):
        # 1~2초 대기 후 리다이렉트 (JS)
        st.session_state["_ready_to_redirect"] = True
        st.session_state["_redirect_url"] = MEET_LINK
    st.experimental_rerun()


def page_search():
    st.markdown("<h2 class='warm-title'>딱 맞는 인연, 지금 찾아볼까요?</h2>", unsafe_allow_html=True)
    keyword = st.text_input("검색(이름/직무/소개 키워드)")

    with st.expander("필터"):
        f_channels = st.multiselect("소통 채널", CHANNELS)
        f_days = st.multiselect("가능 요일", DAYS)
        f_times = st.multiselect("가능 시간대", TIMES)
        f_occ = st.multiselect("직업 대분류", OCCUP_MAIN)

        # 관심사 태그 묶어서 다중 선택
        all_tags = sum(INTEREST_TAGS.values(), [])
        f_interests = st.multiselect("관심사 태그", all_tags)

    if st.button("검색"):
        st.session_state["_search_filters"] = {
            "channels": f_channels,
            "days": f_days,
            "times": f_times,
            "occ_main": f_occ,
            "interests": f_interests,
        }
        st.session_state["_search_keyword"] = keyword

    kw = st.session_state.get("_search_keyword", "")
    flt = st.session_state.get("_search_filters", {
        "channels": [], "days": [], "times": [], "occ_main": [], "interests": []
    })

    results = search_mentors(kw, flt)

    st.caption(f"검색 결과: {len(results)}명")

    for r in results:
        with st.container():
            st.markdown("<div class='warm-card'>", unsafe_allow_html=True)
            cols = st.columns([1, 3, 1])
            with cols[0]:
                if r["photo_url"]:
                    st.image(r["photo_url"], use_container_width=True)
                else:
                    st.image("https://picsum.photos/200/200?blur=2", use_container_width=True)
            with cols[1]:
                st.markdown(f"**{r['name']}**")
                if r["headline"]:
                    st.write(r["headline"])
                # 키태그 3개 노출
                tags = []
                for fld in ["occupations_detail", "interests", "style_tags"]:
                    vals = parse_filter_list(str(r.get(fld, "")))
                    for v in vals:
                        if v and len(tags) < 6:
                            tags.append(v)
                if tags:
                    st.markdown(" ".join([f"<span class='tag'>{t}</span>" for t in tags]), unsafe_allow_html=True)

                # 신고 버튼(멘토)
                with st.popover("신고"):
                    reason = st.text_area("신고 사유")
                    if st.button("제출", key=f"rep_mentor_{r['mentor_id']}"):
                        with get_conn() as conn:
                            conn.execute(
                                "INSERT INTO reports (target_type, target_id, user_id, reason, created_at) VALUES (?, ?, ?, ?, ?)",
                                ("mentor", r["mentor_id"], None, reason, datetime.now(KST).isoformat())
                            )
                            conn.commit()
                        st.success("접수되었습니다. 검토 후 조치하겠습니다.")

            with cols[2]:
                if st.button("🔗 연결", key=f"conn_{r['mentor_id']}"):
                    search_ctx = {"keyword": kw, **flt}
                    connect_and_redirect(r["mentor_id"], None, search_ctx)
            st.markdown("</div>", unsafe_allow_html=True)


# ---------- 오늘의 질문 ----------

def ensure_today_question() -> Tuple[int, str]:
    today = datetime.now(KST).date()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, text FROM daily_questions WHERE qdate = ?", (today.isoformat(),))
        row = cur.fetchone()
        if row:
            return row[0], row[1]

    # 오전 9시 이후에만 자동 생성
    now = datetime.now(KST)
    if now.time() >= time(9, 0):
        qtext = DAILY_QUESTION_SEED[now.toordinal() % len(DAILY_QUESTION_SEED)]
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO daily_questions (qdate, text, author, status) VALUES (?, ?, ?, ?)",
                (today.isoformat(), qtext, "system", "open")
            )
            conn.commit()
            return cur.lastrowid, qtext
    else:
        # 9시 전이면 플레이스홀더 반환
        return -1, "오늘의 질문은 오전 9시에 공개됩니다. 잠시만 기다려주세요."


def page_daily():
    st.markdown("<h2 class='warm-title'>오늘의 질문</h2>", unsafe_allow_html=True)
    qid, qtext = ensure_today_question()
    st.info(qtext)

    if qid > 0:
        with st.form("ans_form", clear_on_submit=True):
            st.write("당신의 한 문장을 남겨주세요.")
            age = st.selectbox("나이대", AGE_BANDS, index=0)
            text = st.text_area("답변(글자 수 제한 없음)")
            submitted = st.form_submit_button("등록")
            if submitted:
                if not text.strip():
                    st.error("내용을 입력해주세요.")
                else:
                    with get_conn() as conn:
                        conn.execute(
                            """
                            INSERT INTO daily_answers (question_id, user_id, age_band, text, created_at)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (qid, None, age, text.strip(), datetime.now(KST).isoformat())
                        )
                        conn.commit()
                    st.success("감사합니다. 세대를 잇는 한 문장이 모이고 있어요.")

        # 리스트
        st.subheader("답변 모아보기")
        sel_age = st.multiselect("나이대 필터", AGE_BANDS)
        order = st.selectbox("정렬", ["최신순", "공감순", "무작위"], index=0)
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM daily_answers WHERE question_id = ? AND visibility = 'ok'", (qid,))
            rows = [dict(r) for r in cur.fetchall()]

        # 필터/정렬
        if sel_age:
            rows = [r for r in rows if r["age_band"] in sel_age]
        if order == "최신순":
            rows.sort(key=lambda r: r["created_at"], reverse=True)
        elif order == "공감순":
            rows.sort(key=lambda r: r["likes"], reverse=True)
        else:
            rows = sorted(rows, key=lambda r: (hash(r["id"]) % 1000))

        for r in rows:
            with st.container():
                st.markdown("<div class='warm-card'>", unsafe_allow_html=True)
                st.markdown(f"**{r['age_band']}** · {r['created_at']}")
                st.write(r["text"])
                cols = st.columns([1,1,4])
                with cols[0]:
                    if st.button(f"공감 {r['likes']}", key=f"like_{r['id']}"):
                        with get_conn() as conn:
                            conn.execute("UPDATE daily_answers SET likes = likes + 1 WHERE id = ?", (r["id"],))
                            conn.commit()
                        st.experimental_rerun()
                with cols[1]:
                    with st.popover("신고"):
                        reason = st.text_input("신고 사유", key=f"rep_reason_{r['id']}")
                        if st.button("제출", key=f"rep_ans_{r['id']}"):
                            with get_conn() as conn:
                                conn.execute(
                                    "INSERT INTO reports (target_type, target_id, user_id, reason, created_at) VALUES (?, ?, ?, ?, ?)",
                                    ("answer", r["id"], None, reason, datetime.now(KST).isoformat())
                                )
                                conn.commit()
                            st.success("접수되었습니다. 검토 후 조치하겠습니다.")
                st.markdown("</div>", unsafe_allow_html=True)


# ---------- 신고 ----------

def page_reports():
    st.markdown("<h2 class='warm-title'>신고 현황(요약)</h2>", unsafe_allow_html=True)
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM reports ORDER BY created_at DESC LIMIT 200")
        rows = cur.fetchall()
    if not rows:
        st.info("아직 접수된 신고가 없습니다.")
        return
    for r in rows:
        r = dict(r)
        st.markdown("<div class='warm-card'>", unsafe_allow_html=True)
        st.write(f"대상: **{r['target_type']}** #{r['target_id']} · 접수시각: {r['created_at']}")
        st.write(f"사유: {r['reason'] or '(미기재)'}")
        st.caption(f"상태: {r['status']}")
        st.markdown("</div>", unsafe_allow_html=True)


# ---------- 홈 ----------

def page_home():
    st.markdown("<h1 class='warm-title'>결 · 멘티</h1>", unsafe_allow_html=True)
    st.caption("따뜻한 연결이 길이 됩니다.")

    # 오늘의 질문 요약 카드
    qid, qtext = ensure_today_question()
    st.markdown("<div class='warm-card'>", unsafe_allow_html=True)
    st.subheader("오늘의 질문")
    st.write(qtext)
    if st.button("바로 참여하기") and qid != -1:
        st.session_state["_nav"] = "오늘의 질문"
        st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # 바로가기
    c1, c2, c3 = st.columns(3)
    with c1:
        st.link_button("회원가입", "#회원가입")
    with c2:
        st.link_button("멘토 검색", "#멘토-검색")
    with c3:
        st.link_button("신고하기", "#신고")


# =========================
# 6) 앱 실행
# =========================

def main():
    st.set_page_config(page_title="결 · 멘티", page_icon="💠", layout="wide")
    st.markdown(WARM_CSS, unsafe_allow_html=True)

    init_db()
    seed_mentors_if_empty()

    # JS 리다이렉트 처리 (상단 전역 처리)
    if st.session_state.get("_ready_to_redirect"):
        url = st.session_state.get("_redirect_url", MEET_LINK)
        st.components.v1.html(
            f"""
            <html><head><meta http-equiv='refresh' content='1; URL={url}' /></head>
            <body>
                <p>잠시 후 이동합니다. 이동하지 않으면 <a href='{url}' target='_self'>여기를 클릭</a>하세요.</p>
                <script>setTimeout(function(){{ window.location.href = '{url}'; }}, 1200);</script>
            </body></html>
            """,
            height=80,
        )
        # 한 번만 실행
        st.session_state["_ready_to_redirect"] = False

    # 사이드 내비
    page = nav()
    st.markdown("<div id='홈'></div>", unsafe_allow_html=True)

    if page == "홈":
        page_home()
    elif page == "회원가입":
        st.markdown("<div id='회원가입'></div>", unsafe_allow_html=True)
        page_signup()
    elif page == "멘토 검색":
        st.markdown("<div id='멘토-검색'></div>", unsafe_allow_html=True)
        page_search()
    elif page == "오늘의 질문":
        page_daily()
    elif page == "신고":
        st.markdown("<div id='신고'></div>", unsafe_allow_html=True)
        page_reports()


if __name__ == "__main__":
    main()
