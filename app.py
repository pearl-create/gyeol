# app.py
# ------------------------------------------------------------
# 노인 멘토 - 청년 멘티 매칭 플랫폼 (Streamlit 단일 통합 버전)
# ------------------------------------------------------------
import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer

# -----------------------------
# 전역 상수 & 선택지
# -----------------------------
DATA_DIR = "data"
USERS_CSV = os.path.join(DATA_DIR, "users.csv")
MATCHES_CSV = os.path.join(DATA_DIR, "matches.csv")

ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin123")

ROLES = ["멘토", "멘티"]

AREAS = [
    "진로상담", "취업/이력서", "창업", "재무/돈관리", "인간관계", "건강/생활습관",
    "학습법", "해외경험", "공무원/공기업", "연구/석박사", "예술/창작", "IT/개발"
]

MENTORING_STYLE = ["질문응답(Q&A)", "정기 커리큘럼", "프로젝트 동행", "독서/세미나", "자유 대화"]
COMM_PREF = ["채팅", "전화", "화상", "대면"]
SLOTS = ["평일 저녁", "평일 낮", "주말 오전", "주말 오후/저녁", "유동적"]

TRAIT_QUESTIONS = [
    ("구체적 조언을 선호합니다", "concrete"),
    ("긴 호흡의 장기 목표를 선호합니다", "longterm"),
    ("과제/숙제를 주고받고 싶습니다", "homework"),
    ("격려/공감 중심을 선호합니다", "empathy"),
    ("엄격한 피드백을 선호합니다", "strict"),
]

# -----------------------------
# 유틸
# -----------------------------
def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(USERS_CSV):
        pd.DataFrame(columns=[
            "user_id","role","name","email","pass_hash","age","gender","region",
            "areas","topics","style","comm_pref","slots","experience_years",
            "intro","goals","created_at","updated_at"
        ]).to_csv(USERS_CSV, index=False, encoding="utf-8")
    if not os.path.exists(MATCHES_CSV):
        pd.DataFrame(columns=["match_id","src_user","tgt_user","score","created_at"]).to_csv(
            MATCHES_CSV, index=False, encoding="utf-8"
        )

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def load_users() -> pd.DataFrame:
    ensure_dirs()
    try:
        df = pd.read_csv(USERS_CSV, encoding="utf-8")
    except:
        df = pd.read_csv(USERS_CSV)
    for col in ["areas","topics","style","comm_pref","slots"]:
        if col in df.columns:
            df[col] = df[col].fillna("").apply(
                lambda x: json.loads(x) if isinstance(x, str) and x.startswith("[") or x.startswith("{")
                else ([] if x=="" else [x])
            )
    return df

def save_users(df: pd.DataFrame):
    df2 = df.copy()
    for col in ["areas","topics","style","comm_pref","slots"]:
        df2[col] = df2[col].apply(
            lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (list, dict))
            else json.dumps([x], ensure_ascii=False) if x!="" else "[]"
        )
    df2.to_csv(USERS_CSV, index=False, encoding="utf-8")

def load_matches() -> pd.DataFrame:
    ensure_dirs()
    try:
        return pd.read_csv(MATCHES_CSV, encoding="utf-8")
    except:
        return pd.read_csv(MATCHES_CSV)

def save_matches(df: pd.DataFrame):
    df.to_csv(MATCHES_CSV, index=False, encoding="utf-8")

def new_user_id(df: pd.DataFrame) -> int:
    if len(df)==0: return 1
    return int(df["user_id"].max()) + 1

def new_match_id(df: pd.DataFrame) -> int:
    if len(df)==0: return 1
    return int(df["match_id"].max()) + 1

def deserialize_list(x):
    if isinstance(x, list): return x
    if isinstance(x, str):
        try:
            return json.loads(x)
        except:
            return [s.strip() for s in x.split(",") if s.strip()]
    return []

def serialize_traits(d: Dict[str,int]) -> str:
    return json.dumps(d, ensure_ascii=False)

def deserialize_traits(s: str) -> Dict[str,int]:
    try:
        d = json.loads(s) if isinstance(s, str) else s
        return {k:int(v) for k,v in d.items()}
    except:
        return {}

def jaccard(a: List[str], b: List[str]) -> float:
    sa, sb = set(a), set(b)
    if len(sa)==0 and len(sb)==0: return 0.0
    inter = len(sa & sb)
    union = len(sa | sb)
    return inter/union if union>0 else 0.0

def overlap_score(a: List[str], b: List[str]) -> float:
    sa, sb = set(a), set(b)
    if len(sa)==0 or len(sb)==0: return 0.0
    return len(sa & sb) / min(len(sa), len(sb))

def likert_distance(a: Dict[str,int], b: Dict[str,int]) -> float:
    if not a or not b: return 0.0
    keys = set(a.keys()) & set(b.keys())
    if not keys: return 0.0
    sims = [(5 - abs(a.get(k,3)-b.get(k,3)))/5 for k in keys]
    return float(np.mean(sims)) if sims else 0.0

def text_overlap(a: str, b: str) -> float:
    texts = [a or "", b or ""]
    if texts[0]=="" and texts[1]=="": return 0.0
    vec = TfidfVectorizer(min_df=1, ngram_range=(1,2))
    X = vec.fit_transform(texts)
    num = (X[0].multiply(X[1])).sum()
    den = (np.linalg.norm(X[0].toarray()) * np.linalg.norm(X[1].toarray()) + 1e-9)
    return float(num/den)

def parse_trait_answers(prefix: str) -> Dict[str,int]:
    out = {}
    for label, key in TRAIT_QUESTIONS:
        out[key] = int(st.session_state.get(f"{prefix}_{key}", 3))
    return out

# -----------------------------
# 매칭 점수
# -----------------------------
def compute_match_score(mentee: Dict[str,Any], mentor: Dict[str,Any]) -> float:
    s_area = jaccard(mentee.get("areas",[]), mentor.get("areas",[]))
    s_topic = overlap_score(mentee.get("topics",[]), mentor.get("topics",[]))
    s_comm = jaccard(mentee.get("comm_pref",[]), mentor.get("comm_pref",[]))
    s_slot = jaccard(mentee.get("slots",[]), mentor.get("slots",[]))

    s_region = 0.1 if (mentee.get("region","")==mentor.get("region","") and mentee.get("region","")!="") else 0.0

    s_trait = likert_distance(
        deserialize_traits(mentee.get("style","{}")),
        deserialize_traits(mentor.get("style","{}"))
    )

    s_text = max(
        text_overlap(mentee.get("goals",""), mentor.get("intro","")),
        text_overlap(mentee.get("goals",""), mentor.get("goals",""))
    )

    exp = mentor.get("experience_years", 0)
    try:
        exp = int(exp)
    except:
        exp = 0
    s_exp = min(float(exp)/10.0, 1.0)*0.1

    score = (
        0.25*s_area + 0.15*s_topic + 0.15*s_trait +
        0.10*s_comm + 0.10*s_slot + 0.10*s_text +
        s_region + s_exp
    )
    return round(float(score), 4)

# -----------------------------
# UI
# -----------------------------
def header():
    st.markdown("## 👵🧓 노인 멘토 – 👩‍🎓👨‍🎓 청년 멘티 매칭 플랫폼")
    st.caption("가입 설문을 바탕으로 맞춤형 멘토-멘티를 추천합니다.")

def sidebar():
    st.sidebar.header("메뉴")
    page = st.sidebar.radio("이동", ["홈", "회원가입/로그인", "프로필 설문", "매칭 찾기", "내 매칭", "관리자 대시보드"])
    st.sidebar.divider()
    st.sidebar.caption("※ 데모용: 로컬 CSV에 저장됩니다.")
    return page

def login_box():
    st.subheader("로그인")
    email = st.text_input("이메일", key="login_email")
    pw = st.text_input("비밀번호", type="password", key="login_pw")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("로그인"):
            df = load_users()
            if email and pw:
                ph = hash_pw(pw)
                row = df[(df["email"]==email) & (df["pass_hash"]==ph)]
                if len(row)==1:
                    st.session_state["user_id"] = int(row.iloc[0]["user_id"])
                    st.session_state["role"] = row.iloc[0]["role"]
                    st.success("로그인 성공!")
                else:
                    st.error("이메일/비밀번호가 올바르지 않습니다.")
            else:
                st.warning("이메일과 비밀번호를 입력하세요.")
    with col2:
        if st.button("로그아웃"):
            st.session_state.pop("user_id", None)
            st.session_state.pop("role", None)
            st.info("로그아웃 되었습니다.")

def signup_box():
    st.subheader("회원가입")
    role = st.selectbox("역할 선택", ROLES, index=1)
    name = st.text_input("이름")
    email = st.text_input("이메일(로그인 ID)")
    pw = st.text_input("비밀번호", type="password")
    pw2 = st.text_input("비밀번호 확인", type="password")
    if st.button("회원가입 완료"):
        if not (name and email and pw and pw2):
            st.warning("모든 항목을 입력하세요.")
            return
        if pw != pw2:
            st.error("비밀번호 확인이 일치하지 않습니다.")
            return
        df = load_users()
        if (df["email"]==email).any():
            st.error("이미 존재하는 이메일입니다.")
            return
        uid = new_user_id(df)
        new_row = {
            "user_id": uid, "role": role, "name": name, "email": email,
            "pass_hash": hash_pw(pw), "age": "", "gender": "", "region": "",
            "areas": json.dumps([], ensure_ascii=False),
            "topics": json.dumps([], ensure_ascii=False),
            "style": json.dumps({}, ensure_ascii=False),
            "comm_pref": json.dumps([], ensure_ascii=False),
            "slots": json.dumps([], ensure_ascii=False),
            "experience_years": 0, "intro": "", "goals": "",
            "created_at": now_str(), "updated_at": now_str(),
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_users(df)
        st.success("가입 완료! 이제 로그인하세요.")

def trait_block(prefix: str, title: str):
    st.markdown(f"#### {title}")
    for label, key in TRAIT_QUESTIONS:
        st.slider(f"{label}", 1, 5, 3, key=f"{prefix}_{key}")

def profile_form():
    if "user_id" not in st.session_state:
        st.info("프로필 설문을 작성하려면 먼저 로그인하세요.")
        return
    df = load_users()
    user = df[df["user_id"]==st.session_state["user_id"]].iloc[0]
    st.subheader("프로필 설문")

    c1, c2, c3 = st.columns(3)
    with c1:
        age = st.text_input("나이(선택)", value=str(user.get("age","") if not pd.isna(user.get("age","")) else ""))
    with c2:
        gender = st.text_input("성별(선택)", value=str(user.get("gender","") if not pd.isna(user.get("gender","")) else ""))
    with c3:
        region = st.text_input("지역(예: 서울, 고양, 부산 등)", value=str(user.get("region","") if not pd.isna(user.get("region","")) else ""))

    areas = st.multiselect("관심/전문 분야 선택", AREAS, default=deserialize_list(user.get("areas")))
    topics_txt = st.text_area("관심 주제 키워드 (쉼표로 구분)", value=",".join(deserialize_list(user.get("topics"))))
    comms = st.multiselect("소통 선호", COMM_PREF, default=deserialize_list(user.get("comm_pref")))
    slots = st.multiselect("가능 요일/시간", SLOTS, default=deserialize_list(user.get("slots")))

    trait_block(prefix="trait", title="멘토링 성향/스타일")

    intro = st.text_area("자기소개 (멘토는 경력/강점 포함 권장)", value=str(user.get("intro","") if not pd.isna(user.get("intro","")) else ""))
    goals = st.text_area("목표/요청사항 (무엇을 얻고 싶은가?)", value=str(user.get("goals","") if not pd.isna(user.get("goals","")) else ""))

    exp_years = 0
    if user["role"] == "멘토":
        exp_years = st.number_input("멘토링 관련/직무 경력 (년)", 0, 50, int(user.get("experience_years",0) if not pd.isna(user.get("experience_years",0)) else 0))

    if st.button("저장"):
        idx = df[df["user_id"]==st.session_state["user_id"]].index[0]
        df.at[idx, "age"] = age
        df.at[idx, "gender"] = gender
        df.at[idx, "region"] = region
        df.at[idx, "areas"] = json.dumps(areas, ensure_ascii=False)
        df.at[idx, "topics"] = json.dumps([t.strip() for t in topics_txt.split(",") if t.strip()], ensure_ascii=False)
        df.at[idx, "comm_pref"] = json.dumps(comms, ensure_ascii=False)
        df.at[idx, "slots"] = json.dumps(slots, ensure_ascii=False)
        df.at[idx, "style"] = serialize_traits(parse_trait_answers("trait"))
        df.at[idx, "intro"] = intro
        df.at[idx, "goals"] = goals
        if user["role"] == "멘토":
            df.at[idx, "experience_years"] = int(exp_years)
        df.at[idx, "updated_at"] = now_str()
        save_users(df)
        st.success("프로필이 저장되었습니다.")

def row_to_userdict(row: pd.Series) -> Dict[str,Any]:
    return {
        "user_id": int(row["user_id"]),
        "role": row["role"],
        "name": row["name"],
        "email": row["email"],
        "age": row.get("age",""),
        "gender": row.get("gender",""),
        "region": row.get("region",""),
        "areas": deserialize_list(row.get("areas","[]")),
        "topics": deserialize_list(row.get("topics","[]")),
        "style": deserialize_traits(row.get("style","{}")),
        "comm_pref": deserialize_list(row.get("comm_pref","[]")),
        "slots": deserialize_list(row.get("slots","[]")),
        "experience_years": int(row.get("experience_years",0) if not pd.isna(row.get("experience_years",0)) else 0),
        "intro": row.get("intro",""),
        "goals": row.get("goals",""),
    }

def user_card(row: pd.Series, score: float=None):
    role_emoji = "🧓" if row["role"]=="멘토" else "🧑‍🎓"
    st.markdown(f"**{role_emoji} {row['name']}**  |  {row['role']}  |  {row.get('region','')}")
    st.caption(f"분야: {', '.join(deserialize_list(row.get('areas','[]')))}")
    st.write(row.get("intro",""))
    if row["role"]=="멘토":
        st.caption(f"경력(년): {int(row.get('experience_years',0))}")
    if score is not None:
        st.success(f"매칭 점수: {score:.3f}")
    with st.expander("연락처/상세 보기"):
        st.write(f"이메일: {row['email']}")
        st.markdown(f"*소통 선호*: {', '.join(deserialize_list(row.get('comm_pref','[]')))}")
        st.markdown(f"*가능 시간*: {', '.join(deserialize_list(row.get('slots','[]')))}")
        st.markdown(f"*관심 주제*: {', '.join(deserialize_list(row.get('topics','[]')))}")
        st.markdown(f"*목표*: {row.get('goals','')}")
    st.divider()

def find_matches():
    if "user_id" not in st.session_state:
        st.info("먼저 로그인하세요.")
        return

    df = load_users()
    me = df[df["user_id"]==st.session_state["user_id"]]
    if len(me)!=1:
        st.error("사용자 정보를 찾을 수 없습니다.")
        return
    me = me.iloc[0]

    st.subheader("맞춤형 매칭")
    topk = st.slider("추천 인원 수", 1, 20, 5)
    filter_region = st.checkbox("같은 지역 우선 보기", value=False)
    filter_area = st.multiselect("특정 분야 필터 (선택)", AREAS, default=[])

    pool = df[df["role"]==("멘토" if me["role"]=="멘티" else "멘티")].copy()
    if filter_region and me.get("region",""):
        pool = pool[pool["region"]==me.get("region","")]
    if filter_area:
        pool = pool[pool["areas"].apply(lambda x: any(a in deserialize_list(x) for a in filter_area))]

    if len(pool)==0:
        st.warning("조건에 맞는 대상이 없습니다. 필터를 완화해보세요.")
        return

    me_dict = row_to_userdict(me)
    scores = []
    for _, r in pool.iterrows():
        other = row_to_userdict(r)
        s = compute_match_score(me_dict, other) if me["role"]=="멘티" else compute_match_score(other, me_dict)
        scores.append(s)
    pool = pool.copy()
    pool["score"] = scores
    pool = pool.sort_values(by="score", ascending=False)

    for _, r in pool.head(topk).iterrows():
        user_card(r, score=r["score"])

    if st.button("위 추천 결과를 '내 매칭'에 저장"):
        mdf = load_matches()
        created = []
        for _, r in pool.head(topk).iterrows():
            match_row = {
                "match_id": new_match_id(mdf),
                "src_user": int(me["user_id"]),
                "tgt_user": int(r["user_id"]),
                "score": float(r["score"]),
                "created_at": now_str()
            }
            mdf = pd.concat([mdf, pd.DataFrame([match_row])], ignore_index=True)
            created.append(match_row["match_id"])
        save_matches(mdf)
        st.success(f"저장 완료! (매칭 ID: {created})")

def my_matches():
    if "user_id" not in st.session_state:
        st.info("먼저 로그인하세요.")
        return
    st.subheader("내 매칭")
    mdf = load_matches()
    df = load_users()
    mine = mdf[mdf["src_user"]==st.session_state["user_id"]].sort_values(by="score", ascending=False)
    if len(mine)==0:
        st.caption("아직 저장된 매칭이 없습니다. '매칭 찾기'에서 저장해보세요.")
        return
    for _, m in mine.iterrows():
        other = df[df["user_id"]==int(m["tgt_user"])]
        if len(other)==1:
            r = other.iloc[0]
            user_card(r, score=float(m["score"]))

def admin_dashboard():
    st.subheader("관리자 대시보드")
    pwd = st.text_input("관리자 비밀번호", type="password")
    if not st.button("접속") and "admin_ok" not in st.session_state:
        st.info("관리자 비밀번호를 입력하고 접속을 눌러주세요.")
        return
    if "admin_ok" not in st.session_state:
        if pwd == ADMIN_PASS:
            st.session_state["admin_ok"] = True
            st.success("관리자 접속 성공")
        else:
            st.error("비밀번호가 올바르지 않습니다.")
            return

    tab1, tab2, tab3 = st.tabs(["전체 사용자", "매칭 기록", "도구"])
    with tab1:
        df = load_users()
        st.dataframe(df, use_container_width=True)
        st.download_button(
            label="사용자 CSV 다운로드",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=f"users_export_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    with tab2:
        mdf = load_matches()
        st.dataframe(mdf, use_container_width=True)
        st.download_button(
            label="매칭 CSV 다운로드",
            data=mdf.to_csv(index=False).encode("utf-8"),
            file_name=f"matches_export_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    with tab3:
        if st.button("샘플 멘토/멘티 6명 생성"):
            seed_sample_data()
            st.success("샘플 데이터가 생성되었습니다.")
        if st.button("모든 데이터 초기화"):
            if os.path.exists(USERS_CSV): os.remove(USERS_CSV)
            if os.path.exists(MATCHES_CSV): os.remove(MATCHES_CSV)
            ensure_dirs()
            st.warning("초기화 완료. 페이지를 새로고침하세요.")

def seed_sample_data():
    df = load_users()
    base_id = new_user_id(df)
    mentors = [
        dict(role="멘토", name="김어르신", email="m1@example.com", pass_hash=hash_pw("1111"),
             region="서울", areas=["취업/이력서","재무/돈관리"], topics=["이직","포트폴리오"], comm_pref=["화상","채팅"],
             slots=["평일 저녁","주말 오후/저녁"], style={"concrete":5,"longterm":4,"homework":4,"empathy":3,"strict":3},
             experience_years=20, intro="인사팀 경력 20년, 이력서/면접 멘토링 전문", goals="젊은 세대와 지혜 나눔"),
        dict(role="멘토", name="박선배", email="m2@example.com", pass_hash=hash_pw("1111"),
             region="고양", areas=["학습법","연구/석박사"], topics=["유학","논문"], comm_pref=["화상","대면"],
             slots=["주말 오전","유동적"], style={"concrete":3,"longterm":5,"homework":4,"empathy":4,"strict":2},
             experience_years=12, intro="대학원 진학/연구계 커리어 상담", goals="후배 양성"),
        dict(role="멘토", name="이장로", email="m3@example.com", pass_hash=hash_pw("1111"),
             region="부산", areas=["창업","재무/돈관리","IT/개발"], topics=["스타트업","앱개발"], comm_pref=["채팅","전화"],
             slots=["평일 낮","유동적"], style={"concrete":4,"longterm":4,"homework":3,"empathy":3,"strict":2},
             experience_years=15, intro="핀테크 창업 2회, 실패/성공 스토리 공유", goals="창업가 멘토링"),
    ]
    mentees = [
        dict(role="멘티", name="홍청년", email="y1@example.com", pass_hash=hash_pw("2222"),
             region="서울", areas=["취업/이력서","IT/개발"], topics=["포트폴리오","코딩테스트"], comm_pref=["화상","채팅"],
             slots=["평일 저녁","주말 오후/저녁"], style={"concrete":4,"longterm":3,"homework":4,"empathy":3,"strict":3},
             intro="개발 취업 준비생", goals="이력서/포트폴리오 피드백"),
        dict(role="멘티", name="최대학생", email="y2@example.com", pass_hash=hash_pw("2222"),
             region="고양", areas=["학습법","연구/석박사"], topics=["대학원","논문"], comm_pref=["화상","대면"],
             slots=["주말 오전","유동적"], style={"concrete":3,"longterm":5,"homework":4,"empathy":4,"strict":2},
             intro="연구자로 성장하고 싶어요", goals="석사 진학 로드맵"),
        dict(role="멘티", name="장창업", email="y3@example.com", pass_hash=hash_pw("2222"),
             region="부산", areas=["창업","재무/돈관리","IT/개발"], topics=["스타트업","앱개발"], comm_pref=["채팅","전화"],
             slots=["평일 낮","유동적"], style={"concrete":4,"longterm":4,"homework":3,"empathy":3,"strict":2},
             intro="스타트업 준비", goals="MVP 피드백과 자금 계획"),
    ]
    rows = []
    t = now_str()
    for i, u in enumerate(mentors + mentees):
        rows.append({
            "user_id": base_id+i, "role": u["role"], "name": u["name"], "email": u["email"],
            "pass_hash": u["pass_hash"], "age": "", "gender": "", "region": u["region"],
            "areas": json.dumps(u["areas"], ensure_ascii=False),
            "topics": json.dumps(u["topics"], ensure_ascii=False),
            "style": json.dumps(u["style"], ensure_ascii=False),
            "comm_pref": json.dumps(u["comm_pref"], ensure_ascii=False),
            "slots": json.dumps(u["slots"], ensure_ascii=False),
            "experience_years": u["experience_years"] if u["role"]=="멘토" else 0,
            "intro": u["intro"], "goals": u["goals"],
            "created_at": t, "updated_at": t,
        })
    df = pd.concat([df, pd.DataFrame(rows)], ignore_index=True)
    save_users(df)

# -----------------------------
# 메인
# -----------------------------
def main():
    st.set_page_config(page_title="멘토-멘티 매칭", page_icon="🤝", layout="wide")
    ensure_dirs()
    header()
    page = sidebar()

    if page == "홈":
        st.markdown("""
        ### 어떻게 동작하나요?
        1) **회원가입/로그인**
        2) **프로필 설문** 작성
        3) **매칭 찾기**에서 맞춤 추천 확인 및 저장
        4) **내 매칭**에서 저장한 추천 확인
        """)
        st.info("관리자 비밀번호 기본값: admin123 (환경변수 ADMIN_PASS 로 변경 가능)")

    elif page == "회원가입/로그인":
        col1, col2 = st.columns(2)
        with col1: signup_box()
        with col2: login_box()

    elif page == "프로필 설문":
        profile_form()

    elif page == "매칭 찾기":
        find_matches()

    elif page == "내 매칭":
        my_matches()

    elif page == "관리자 대시보드":
        admin_dashboard()

if __name__ == "__main__":
    main()
