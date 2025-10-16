# app.py — 결(Gyeol) 클린 버전
# ------------------------------------------------------------
# ✅ 목표
# - 폴더/캐시 꼬임 없이 바로 실행되는 단일 파일(Streamlit)
# - 아바타 3x2 그리드 선택(특정 이미지 제외 필터)
# - 멘토/멘티 프로필 저장 & 불러오기(UTF-8-SIG)
# - 간단한 텍스트 유사도 기반 매칭(Jaccard)
# - 로컬 폴더가 없어도 안전하게 동작(원격 플레이스홀더 아바타 제공)
# - 한국어 UI, 에러 방지형 파일 I/O
# ------------------------------------------------------------

from __future__ import annotations
import os
from pathlib import Path
import json
import re
from typing import List, Dict, Tuple

import streamlit as st
import pandas as pd

# -----------------------------
# 전역 설정
# -----------------------------
st.set_page_config(
    page_title="결 (Gyeol) — 멘토·멘티 매칭 플랫폼",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# -----------------------------
# 상수 & 경로
# -----------------------------
BASE_DIR: Path = Path(__file__).resolve().parent
DATA_DIR: Path = BASE_DIR / "data"
AVATAR_DIR: Path = BASE_DIR / "avatars"

MENTOR_CSV = DATA_DIR / "mentors.csv"
MENTEE_CSV = DATA_DIR / "mentees.csv"

# 제외할 아바타 키워드 (파일명/URL에 포함되면 제외)
EXCLUDE_AVATAR_KEYWORDS = ["박명수", "parkmyungsoo", "myungsoo"]

# 로컬 폴더가 비어있거나 없을 때 사용할 플레이스홀더 이미지(저작권 걱정 적은 샘플)
FALLBACK_AVATARS = [
    "https://picsum.photos/id/1011/300/300",
    "https://picsum.photos/id/1027/300/300",
    "https://picsum.photos/id/1005/300/300",
    "https://picsum.photos/id/1001/300/300",
    "https://picsum.photos/id/1003/300/300",
    "https://picsum.photos/id/1021/300/300",
    "https://picsum.photos/id/1025/300/300",
]

# -----------------------------
# 유틸리티
# -----------------------------

def ensure_dirs() -> None:
    """필요한 폴더 생성."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass  # 권한 문제 등으로 실패해도 앱은 계속 작동


def read_csv_safe(path: Path) -> pd.DataFrame:
    """CSV 읽기. 없으면 빈 스키마 반환."""
    if not path.exists():
        return pd.DataFrame(
            columns=[
                "role",  # '멘토' or '멘티'
                "name",
                "email",
                "interests",   # 쉼표로 구분된 키워드
                "skills",      # 멘토: 제공 가능 역량 / 멘티: 배우고 싶은 역량
                "goals",       # 멘티 목표
                "intro",       # 소개(멘토/멘티 공통)
                "contact",     # 연락 수단
                "avatar",      # 선택한 아바타 URL
            ]
        )
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        # 인코딩이 달라 저장된 경우 대비
        return pd.read_csv(path, encoding="utf-8")


def write_csv_safe(df: pd.DataFrame, path: Path) -> None:
    try:
        df.to_csv(path, index=False, encoding="utf-8-sig")
    except Exception:
        # 드물게 파일 잠김/경로 문제 발생할 때 임시 파일로 우회
        tmp = path.with_suffix(".tmp.csv")
        df.to_csv(tmp, index=False, encoding="utf-8-sig")
        try:
            tmp.replace(path)
        except Exception:
            pass


def tokenize(text: str) -> List[str]:
    text = (text or "").lower()
    # 한글/영문/숫자 토큰 유지, 나머지 제거
    tokens = re.findall(r"[가-힣a-z0-9]+", text)
    # 의미 약한 짧은 토큰 제거
    return [t for t in tokens if len(t) >= 2]


def jaccard_similarity(text_a: str, text_b: str) -> float:
    set_a, set_b = set(tokenize(text_a)), set(tokenize(text_b))
    if not set_a and not set_b:
        return 0.0
    inter = len(set_a & set_b)
    union = len(set_a | set_b)
    return inter / union if union else 0.0


def compute_match_score(mentee: Dict, mentor: Dict) -> float:
    """간단한 가중 합산 기반 매칭 점수 (0~100). 외부 라이브러리 없이 동작."""
    weights = {
        "goals_intro": 0.35,       # 멘티 목표 vs 멘토 소개
        "interests": 0.35,         # 공통 관심사
        "skills": 0.30,            # 멘티가 배우고 싶은 것 vs 멘토가 가진 스킬
    }
    s1 = jaccard_similarity(mentee.get("goals", ""), mentor.get("intro", ""))
    s2 = jaccard_similarity(mentee.get("interests", ""), mentor.get("interests", ""))
    s3 = jaccard_similarity(mentee.get("skills", ""), mentor.get("skills", ""))
    score = (weights["goals_intro"] * s1 + weights["interests"] * s2 + weights["skills"] * s3) * 100
    return round(score, 2)


@st.cache_data(show_spinner=False)
def list_avatars() -> List[str]:
    """아바타 URL 리스트 반환. 로컬 폴더 없으면 플레이스홀더 사용.
    - 특정 키워드 포함 파일/URL은 제외(EXCLUDE_AVATAR_KEYWORDS)
    - 최대 60장 정도까지만 로드
    """
    urls: List[str] = []
    try:
        if AVATAR_DIR.exists() and AVATAR_DIR.is_dir():
            for p in AVATAR_DIR.iterdir():  # NotADirectoryError 방지: is_dir() 체크 완료
                if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                    name = p.name.lower()
                    if any(k in name for k in EXCLUDE_AVATAR_KEYWORDS):
                        continue
                    urls.append(p.as_posix())
    except Exception:
        # 폴더 접근 중 문제 생겨도 무시하고 플레이스홀더로 대체
        urls = []

    # 폴더가 비었거나 없을 때 — 플레이스홀더에서 보충
    if not urls:
        urls = [u for u in FALLBACK_AVATARS if not any(k in u for k in EXCLUDE_AVATAR_KEYWORDS)]

    return urls[:60]


def avatar_picker(key: str = "avatar_choice") -> str:
    """3x2 그리드로 아바타 선택 UI를 제공하고, 선택된 URL을 반환."""
    st.markdown("#### 아바타 선택 (3×2)")
    avatars = list_avatars()

    # 페이지네이션 (6개씩)
    page_size = 6
    page_max = max(1, (len(avatars) + page_size - 1) // page_size)
    pg = st.number_input("페이지", min_value=1, max_value=page_max, value=1, step=1, help="한 페이지에 6개씩 표시")

    start = (pg - 1) * page_size
    subset = avatars[start:start + page_size]

    cols = st.columns(3)
    selected = st.session_state.get(key, "")

    for i, url in enumerate(subset):
        col = cols[i % 3]
        with col:
            st.image(url, use_container_width=True)
            if st.button("선택", key=f"pick_{start+i}"):
                st.session_state[key] = url
                selected = url

        if (i % 3) == 2 and i != len(subset) - 1:
            st.write("")  # 줄바꿈 역할

    if selected:
        st.success("선택된 아바타가 적용되었습니다.")
        st.image(selected, caption="현재 선택", use_container_width=True)
    else:
        st.info("이미지를 선택해 주세요.")

    return selected


# -----------------------------
# 데이터 입출력
# -----------------------------

def upsert_profile(row: Dict) -> None:
    ensure_dirs()
    role = row.get("role")
    if role == "멘토":
        df = read_csv_safe(MENTOR_CSV)
        key_cols = ["role", "email"]  # 동일 이메일은 업데이트 처리
        df = _upsert_df(df, row, key_cols)
        write_csv_safe(df, MENTOR_CSV)
    elif role == "멘티":
        df = read_csv_safe(MENTEE_CSV)
        key_cols = ["role", "email"]
        df = _upsert_df(df, row, key_cols)
        write_csv_safe(df, MENTEE_CSV)


def _upsert_df(df: pd.DataFrame, row: Dict, key_cols: List[str]) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame([row])
    mask = pd.Series([True] * len(df))
    for k in key_cols:
        mask &= (df.get(k, "") == row.get(k, ""))
    if mask.any():
        df.loc[mask, list(row.keys())] = list(row.values())
        return df
    else:
        return pd.concat([df, pd.DataFrame([row])], ignore_index=True)


# -----------------------------
# UI 섹션
# -----------------------------

def page_home():
    st.title("결 (Gyeol)")
    st.caption("멘토와 멘티를 기분 좋게 이어주는 연결점 ✨")

    st.markdown(
        """
        **결**은 관심사·목표·역량 기반의 가벼운 프로필만으로도 충분히 좋은 연결을 만들 수 있게 설계했어요.
        좌측 상단의 메뉴(또는 아래 버튼)로 이동해 **프로필 등록 → 매칭 찾기** 흐름으로 사용해 보세요.
        """
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("멘티 프로필 만들기", use_container_width=True):
            st.session_state["nav"] = "멘티 등록"
            st.rerun()
    with c2:
        if st.button("멘토 프로필 만들기", use_container_width=True):
            st.session_state["nav"] = "멘토 등록"
            st.rerun()


def _profile_form(role: str):
    st.header(f"{role} 프로필 등록")

    name = st.text_input("이름")
    email = st.text_input("이메일 (고유 식별용)")

    if role == "멘토":
        interests = st.text_input("관심사 (쉼표로 구분)")
        skills = st.text_input("제공 가능 역량/분야 (쉼표)")
        intro = st.text_area("한 줄 소개/경력 요약", height=100)
        goals = ""  # 멘토는 목표 필드 비활성화
    else:
        interests = st.text_input("관심사 (쉼표로 구분)")
        skills = st.text_input("배우고 싶은 역량/분야 (쉼표)")
        goals = st.text_area("학습/성장 목표 (자유 기술)", height=100)
        intro = st.text_area("간단 소개", height=80)

    avatar_url = avatar_picker(key=f"avatar_{role}")
    contact = st.text_input("연락 수단 (오픈채팅/이메일/기타)")

    if st.button("저장하기", type="primary"):
        if not name or not email:
            st.error("이름과 이메일은 필수입니다.")
        else:
            row = {
                "role": role,
                "name": name,
                "email": email,
                "interests": interests,
                "skills": skills,
                "goals": goals,
                "intro": intro,
                "contact": contact,
                "avatar": avatar_url,
            }
            upsert_profile(row)
            st.success("저장 완료! 상단 메뉴 또는 아래 버튼으로 계속 진행하세요.")

    st.divider()
    if st.button("매칭 찾으러 가기 →", use_container_width=True):
        st.session_state["nav"] = "매칭 찾기"
        st.rerun()


def page_register_mentee():
    _profile_form("멘티")


def page_register_mentor():
    _profile_form("멘토")


def page_browse():
    st.header("프로필 목록")

    tab1, tab2 = st.tabs(["멘토", "멘티"])
    with tab1:
        mentors = read_csv_safe(MENTOR_CSV)
        st.caption(f"멘토 수: {len(mentors)}")
        st.dataframe(mentors)
    with tab2:
        mentees = read_csv_safe(MENTEE_CSV)
        st.caption(f"멘티 수: {len(mentees)}")
        st.dataframe(mentees)


def page_match():
    st.header("매칭 찾기")

    role_choice = st.radio("내 역할", ["멘티", "멘토"], horizontal=True)
    my_email = st.text_input("내 이메일 (등록된 프로필)")

    if st.button("매칭 계산하기", type="primary"):
        if not my_email:
            st.error("이메일을 입력해 주세요.")
            return

        mentors = read_csv_safe(MENTOR_CSV)
        mentees = read_csv_safe(MENTEE_CSV)

        if role_choice == "멘티":
            me = mentees[mentees["email"] == my_email]
            if me.empty:
                st.error("해당 이메일의 멘티 프로필이 없습니다. 먼저 등록해 주세요.")
                return
            me_row = me.iloc[0].to_dict()

            if mentors.empty:
                st.info("등록된 멘토가 없습니다.")
                return

            rows: List[Tuple[float, Dict]] = []
            for _, mentor in mentors.iterrows():
                score = compute_match_score(me_row, mentor.to_dict())
                rows.append((score, mentor.to_dict()))

            rows.sort(key=lambda x: x[0], reverse=True)
            _render_match_results(me_row, rows)

        else:  # 멘토
            me = mentors[mentors["email"] == my_email]
            if me.empty:
                st.error("해당 이메일의 멘토 프로필이 없습니다. 먼저 등록해 주세요.")
                return
            me_row = me.iloc[0].to_dict()

            if mentees.empty:
                st.info("등록된 멘티가 없습니다.")
                return

            rows: List[Tuple[float, Dict]] = []
            for _, mentee in mentees.iterrows():
                score = compute_match_score(mentee.to_dict(), me_row)
                rows.append((score, mentee.to_dict()))

            rows.sort(key=lambda x: x[0], reverse=True)
            _render_match_results(me_row, rows)


def _render_match_results(me_row: Dict, rows: List[Tuple[float, Dict]]):
    st.success("매칭 결과가 준비되었습니다.")

    for score, other in rows[:10]:
        with st.container(border=True):
            c1, c2 = st.columns([1, 3], vertical_alignment="center")
            with c1:
                if other.get("avatar"):
                    st.image(other["avatar"], use_container_width=True)
                else:
                    st.image("https://picsum.photos/seed/gyeol/200/200", use_container_width=True)
                st.metric("매칭 점수", f"{score}")
            with c2:
                st.markdown(f"**이름**: {other.get('name','-')}")
                st.markdown(f"**이메일**: {other.get('email','-')}")
                st.markdown(f"**관심사**: {other.get('interests','-')}")
                st.markdown(f"**역량/배우고싶은 것**: {other.get('skills','-')}")
                if other.get("goals"):
                    st.markdown(f"**목표**: {other.get('goals','-')}")
                if other.get("intro"):
                    st.markdown(f"**소개**: {other.get('intro','-')}")
                st.markdown(f"**연락**: {other.get('contact','-')}")


def page_admin():
    st.header("관리 도구 (선택)")
    st.caption("CSV 백업/복원, 수동 업로드 등")

    st.subheader("데이터 다운로드")
    mtr = read_csv_safe(MENTOR_CSV)
    mte = read_csv_safe(MENTEE_CSV)
    st.download_button("멘토 CSV 다운로드", data=mtr.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"), file_name="mentors.csv")
    st.download_button("멘티 CSV 다운로드", data=mte.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"), file_name="mentees.csv")

    st.divider()
    st.subheader("CSV 업로드(덮어쓰기)")
    up1 = st.file_uploader("멘토 CSV 업로드", type=["csv"], key="up_m")
    if up1:
        df = pd.read_csv(up1, encoding="utf-8-sig")
        write_csv_safe(df, MENTOR_CSV)
        st.success("멘토 CSV가 갱신되었습니다.")

    up2 = st.file_uploader("멘티 CSV 업로드", type=["csv"], key="up_t")
    if up2:
        df = pd.read_csv(up2, encoding="utf-8-sig")
        write_csv_safe(df, MENTEE_CSV)
        st.success("멘티 CSV가 갱신되었습니다.")


# -----------------------------
# 내비게이션 & 실행
# -----------------------------
NAV_ITEMS = ["홈", "멘티 등록", "멘토 등록", "프로필 보기", "매칭 찾기", "관리"]

def main():
    ensure_dirs()

    # 사이드바 네비 (모바일/작은 화면 대비)
    with st.sidebar:
        nav = st.radio("이동", NAV_ITEMS, index=0)
        st.session_state["nav"] = nav

    # 상단 퀵 네비
    st.markdown(
        """
        <style>
        .topnav {position: sticky; top: 0; background: rgba(255,255,255,0.8); backdrop-filter: blur(6px); padding: 0.5rem 0; z-index: 999;}
        .topnav .btn {display: inline-block; margin: 0 .25rem .25rem 0; padding: .4rem .8rem; border-radius: 9999px; border: 1px solid #e5e7eb; text-decoration: none;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(len(NAV_ITEMS))
    for i, label in enumerate(NAV_ITEMS):
        with cols[i]:
            if st.button(label, use_container_width=True):
                st.session_state["nav"] = label
                st.rerun()

    page = st.session_state.get("nav", "홈")

    if page == "홈":
        page_home()
    elif page == "멘티 등록":
        page_register_mentee()
    elif page == "멘토 등록":
        page_register_mentor()
    elif page == "프로필 보기":
        page_browse()
    elif page == "매칭 찾기":
        page_match()
    elif page == "관리":
        page_admin()
    else:
        page_home()


if __name__ == "__main__":
    main()
