import streamlit as st
import pandas as pd
import random
import time
import os
import json
import html  # 텍스트 안전 출력

# =========================================================
# 페이지 설정
# =========================================================
st.set_page_config(
    page_title="세대 간 멘토링 플랫폼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# 상수
# =========================================================
MENTOR_CSV_PATH = "멘토더미.csv"
USERS_FILE_PATH = "users.json"
ANSWERS_FILE_PATH = "daily_answers.json"
GOOGLE_MEET_URL = "https://meet.google.com/urw-iods-puy"

GENDERS = ["남", "여", "기타"]
COMM_METHODS = ["대면 만남", "화상채팅", "일반 채팅"]
WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]
TIMES = ["오전", "오후", "저녁"]
AGE_BANDS = [
    "만 13세~19세", "만 20세~29세", "만 30세~39세",
    "만 40세~49세", "만 50세~59세", "만 60세~69세",
    "만 70세~79세", "만 80세~89세", "만 90세 이상"
]
OCCUPATION_GROUPS = [
    "경영·사무·금융·보험직",
    "연구직 및 공학기술직",
    "교육·법률·사회복지·경찰·소방직 및 군인",
    "보건·의료직",
    "예술·디자인·방송·스포츠직",
    "미용·여행·숙박·음식·경비·청소직",
    "영업·판매·운전·운송직",
    "건설·채굴직",
    "설치·정비·생산직",
    "농림어업직",
    "학생", "전업주부", "구직/이직", "프리랜서", "기타"
]
TOPIC_PREFS = [
    "진로·직업", "학업·전문 지식", "인생 경험·삶의 가치관",
    "대중문화·취미", "사회 문제·시사", "건강·웰빙"
]
COMM_STYLES = {
    "연두부형": "조용하고 차분하게, 상대방 얘기를 경청하며 공감해 주는 편이에요.",
    "분위기메이커형": "활발하고 에너지가 넘쳐 대화를 이끌어가는 편이에요.",
    "효율추구형": "주제를 체계적으로 정리하고 목표 지향적으로 대화하는 편이에요.",
    "댕댕이형": "자유롭고 편안하게, 즉흥적으로 대화를 이어가는 편이에요.",
    "감성 충만형": "감성적인 대화를 좋아하고 위로와 지지를 주는 편이에요.",
    "냉철한 조언자형": "논리적이고 문제 해결 중심으로 조언을 주는 편이에요."
}

# =========================================================
# 파일 I/O
# =========================================================
def load_json_data(file_path, default_value):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.warning(f"데이터 파일 로드 오류 ({file_path}): {e}. 기본값으로 시작합니다.")
            return default_value
    return default_value

def save_json_data(data, file_path):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"데이터 파일 저장 오류 ({file_path}): {e}")

def load_mentor_data():
    if not os.path.exists(MENTOR_CSV_PATH):
        st.error(f"Error: 멘토 데이터 파일 '{MENTOR_CSV_PATH}'을(를) 찾을 수 없습니다.")
        return pd.DataFrame()
    try:
        df = pd.read_csv(MENTOR_CSV_PATH, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(MENTOR_CSV_PATH, encoding="cp949")
    df.columns = df.columns.str.strip()
    if "communication_style" in df.columns and "style" not in df.columns:
        df = df.rename(columns={"communication_style": "style"})
    required_cols = ['name', 'age_band', 'occupation_major', 'topic_prefs', 'style', 'intro']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.error(f"멘토 CSV 파일에 다음 컬럼이 누락되었습니다: {', '.join(missing)}")
        st.info(f"현재 파일의 컬럼 목록: {', '.join(df.columns)}")
        return pd.DataFrame()
    return df

# =========================================================
# 오늘의 질문 헬퍼: 동기화/업서트/삭제
# =========================================================
def refresh_answers_from_disk():
    latest = load_json_data(ANSWERS_FILE_PATH, [])
    changed = False
    for a in latest:
        if "id" not in a:
            a["id"] = int(time.time() * 1000) + random.randint(0, 999)
            changed = True
    if changed:
        save_json_data(latest, ANSWERS_FILE_PATH)
    st.session_state.daily_answers = latest

def upsert_answer(answer_obj):
    data = load_json_data(ANSWERS_FILE_PATH, [])
    if "id" not in answer_obj:
        answer_obj["id"] = int(time.time() * 1000) + random.randint(0, 999)
    replaced = False
    for i, a in enumerate(data):
        if a.get("id") == answer_obj["id"]:
            data[i] = answer_obj
            replaced = True
            break
    if not replaced:
        data.append(answer_obj)
    save_json_data(data, ANSWERS_FILE_PATH)
    refresh_answers_from_disk()

def delete_answer_by_id(answer_id: int):
    data = load_json_data(ANSWERS_FILE_PATH, [])
    data = [a for a in data if a.get("id") != answer_id]
    save_json_data(data, ANSWERS_FILE_PATH)
    refresh_answers_from_disk()

# =========================================================
# 세션 초기화
# =========================================================
def initialize_session_state():
    st.session_state.mentors_df = load_mentor_data()
    st.session_state.all_users = load_json_data(USERS_FILE_PATH, {})
    st.session_state.logged_in = st.session_state.get("logged_in", False)
    st.session_state.user_profile = st.session_state.get("user_profile", {})
    st.session_state.daily_answers = load_json_data(ANSWERS_FILE_PATH, [])
    if not os.path.exists(ANSWERS_FILE_PATH):
        save_json_data(st.session_state.daily_answers, ANSWERS_FILE_PATH)
    st.session_state.recommendations = st.session_state.get("recommendations", pd.DataFrame())
    st.session_state.editing_answer_id = st.session_state.get("editing_answer_id", None)

initialize_session_state()
if st.session_state.mentors_df.empty and not st.session_state.logged_in:
    st.stop()

# =========================================================
# 추천 로직
# =========================================================
def recommend_mentors(search_field, search_topic, search_style):
    mentors = st.session_state.mentors_df.copy()
    mentors["score"] = 0
    if search_field:
        mentors["score"] += mentors["occupation_major"].apply(lambda x: 3 if x == search_field else 0)
    if search_topic:
        mentors["score"] += mentors["topic_prefs"].astype(str).apply(lambda x: 2 if search_topic in x else 0)
    if search_style:
        mentors["score"] += mentors["style"].apply(lambda x: 1 if search_style in x else 0)
    if search_field or search_topic or search_style:
        out = mentors[mentors["score"] > 0].sort_values(by="score", ascending=False)
    else:
        out = mentors.sort_values(by="name", ascending=True)
    return out.reset_index(drop=True)

# =========================================================
# 인증/회원가입 UI
# =========================================================
def show_login_form():
    st.header("🔑 로그인")
    with st.form("login_form"):
        name = st.text_input("이름을 입력하세요 (가입 시 사용한 이름)", placeholder="홍길동")
        submitted = st.form_submit_button("로그인")
        if submitted:
            if not name:
                st.error("이름을 입력해 주세요.")
            elif name in st.session_state.all_users:
                st.session_state.user_profile = st.session_state.all_users[name]
                st.session_state.logged_in = True
                st.success(f"🎉 {name}님, 환영합니다! 서비스를 시작합니다.")
                st.rerun()
            else:
                st.error(f"'{name}'으로 등록된 회원을 찾을 수 없습니다. 회원 가입을 해주세요.")

def show_registration_form():
    st.header("👤 회원 가입")
    with st.form("registration_form"):
        st.subheader("기본 정보")
        name = st.text_input("이름 (로그인 시 사용됩니다)", placeholder="홍길동")
        gender = st.radio("성별", GENDERS, index=1, horizontal=True)
        age_band = st.selectbox("나이대", AGE_BANDS)

        st.subheader("소통 환경")
        comm_method = st.radio("선호하는 소통 방법", COMM_METHODS, horizontal=True)

        col_day, col_time = st.columns(2)
        with col_day:
            available_days = st.multiselect("소통 가능한 요일", WEEKDAYS)
        with col_time:
            available_times = st.multiselect("소통 가능한 시간대", TIMES)

        st.subheader("현재 직종")
        occupation_key = st.selectbox("현재 직종 분류", OCCUPATION_GROUPS)

        st.subheader("선호하는 대화 주제")
        selected_topics = st.multiselect("멘토링에서 주로 어떤 주제에 대해 이야기하고 싶으신가요?", TOPIC_PREFS)

        st.subheader("선호하는 소통 스타일")
        comm_style_options = [f"{k}: {v}" for k, v in COMM_STYLES.items()]
        selected_style_full = st.radio("평소 대화 시 본인과 비슷하거나 선호하는 스타일을 선택해주세요",
                                       comm_style_options, key="comm_style_radio")
        selected_style = selected_style_full.split(":")[0]

        submitted = st.form_submit_button("가입 완료 및 서비스 시작")
        if submitted:
            if not name or not available_days or not available_times or not selected_topics or not selected_style:
                st.error("이름, 소통 가능 요일/시간, 주제, 소통 스타일은 필수 입력 항목입니다.")
            elif name in st.session_state.all_users:
                st.error(f"'{name}' 이미 등록된 이름입니다.")
            else:
                user_profile_data = {
                    "name": name, "gender": gender, "age_band": age_band,
                    "comm_method": comm_method, "available_days": available_days,
                    "available_times": available_times, "occupation_group": occupation_key,
                    "topic_prefs": selected_topics, "comm_style": selected_style
                }
                st.session_state.all_users[name] = user_profile_data
                st.session_state.user_profile = user_profile_data
                st.session_state.logged_in = True
                save_json_data(st.session_state.all_users, USERS_FILE_PATH)
                st.success(f"🎉 {name}님, 성공적으로 가입 및 로그인되었습니다!")
                st.rerun()

# =========================================================
# 멘토 찾기
# =========================================================
def show_mentor_search_and_connect():
    st.header("🔍 멘토 찾기 및 연결")
    mentors = st.session_state.mentors_df
    st.subheader("나에게 맞는 멘토 검색하기")
    with st.form("mentor_search_form"):
        col_f, col_t, col_s = st.columns(3)
        available_topics = sorted([
            t for t in set(
                t.strip()
                for items in mentors["topic_prefs"].astype(str).str.split("[,;]")
                for t in items if t.strip()
            )
        ])
        if "style" in mentors.columns:
            available_styles = sorted(list(mentors["style"].dropna().unique()))
        else:
            available_styles = sorted(list(COMM_STYLES.keys()))
        available_fields_clean = sorted(OCCUPATION_GROUPS)
        with col_f:
            search_field = st.selectbox("💼 전문 분야 (직종 분류)", ['(전체)'] + available_fields_clean)
        with col_t:
            search_topic = st.selectbox("💬 주요 대화 주제", ['(전체)'] + available_topics)
        with col_s:
            search_style = st.selectbox("🗣️ 선호 대화 스타일", ['(전체)'] + available_styles)
        submitted = st.form_submit_button("🔎 검색 시작")

    if submitted:
        field = search_field if search_field != '(전체)' else ''
        topic = search_topic if search_topic != '(전체)' else ''
        style = search_style if search_style != '(전체)' else ''
        with st.spinner("최적의 멘토를 찾는 중..."):
            st.session_state.recommendations = recommend_mentors(field, topic, style)
        if st.session_state.recommendations.empty and (field or topic or style):
            st.info("⚠️ 선택하신 조건에 맞는 멘토를 찾지 못했습니다. 조건을 변경해 보세요.")
        elif st.session_state.recommendations.empty:
            st.info("멘토 데이터가 비어있습니다. 데이터를 확인해 주세요.")

    if not st.session_state.recommendations.empty:
        st.subheader(f"총 {len(st.session_state.recommendations)}명의 멘토가 검색되었습니다.")
        if 'score' in st.session_state.recommendations.columns:
            st.caption("(추천 점수 또는 이름순)")
        for index, row in st.session_state.recommendations.iterrows():
            with st.container(border=True):
                col_name, _ = st.columns([3, 1])
                with col_name:
                    st.markdown(f"#### 👤 {row['name']} ({row['age_band']})")
                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1: st.markdown(f"**전문 분야:** {row['occupation_major']}")
                with col_m2: st.markdown(f"**주요 주제:** {row['topic_prefs']}")
                with col_m3: st.markdown(f"**소통 스타일:** {row['style']}")
                st.markdown(f"**멘토 한마디:** _{row['intro']}_")
                if st.button("🔗 연결", key=f"connect_btn_{row['name']}_{index}"):
                    st.session_state.connecting = True
                    st.session_state.connect_mentor_name = row['name']
                    st.rerun()
    elif not submitted:
        st.info("검색 조건을 입력하고 '🔎 검색 시작' 버튼을 눌러 멘토를 찾아보세요.")

# =========================================================
# 오늘의 질문 (둥근 모서리 사각형 카드 + 무색 구분)
# =========================================================
def show_daily_question():
    st.header("💬 오늘의 질문: 세대 공감 창구")
    st.write("매일 올라오는 질문에 대해 다양한 연령대의 답변을 공유하는 공간입니다.")

    daily_q = "🤔 **'나와 전혀 다른 세대의 삶을 하루만 살아볼 수 있다면, 어떤 세대의 삶을 살아보고 싶은지 이유와 함께 알려주세요!'**"
    st.subheader(daily_q)

    # 최신 동기화
    refresh_answers_from_disk()

    # 카드 스타일
    st.markdown("""
    <style>
      .answer-grid{
        display:grid;
        grid-template-columns:repeat(auto-fill, minmax(320px, 1fr));
        gap:20px; margin-top:16px;
      }
      .answer-card{
        background:#ffffff;
        border-radius:18px;
        border:1px solid #e6e9ef;
        box-shadow:0 2px 8px rgba(0,0,0,0.05);
        padding:16px 18px;
        word-break:break-word;
        transition:transform .08s ease, box-shadow .08s ease;
        min-height:90px;
      }
      .answer-card:hover{ transform:translateY(-2px); box-shadow:0 8px 18px rgba(0,0,0,0.06); }
      .answer-meta{ font-size:13px; color:#5a5f7a; margin-bottom:8px; }
      .answer-text{ font-size:15px; line-height:1.6; color:#222; margin-bottom:10px; }
    </style>
    """, unsafe_allow_html=True)

    # 로그인 사용자
    current_name = st.session_state.user_profile.get("name", "")
    current_age = st.session_state.user_profile.get("age_band", "미등록")

    # 작성 폼 (수정모드 아닐 때)
    st.divider()
    st.subheader("나의 답변 작성하기")
    if st.session_state.editing_answer_id is None:
        with st.form("answer_form"):
            answer_text = st.text_area("질문에 대한 당신의 생각을 적어주세요.", max_chars=500, height=150)
            submitted = st.form_submit_button("답변 제출")
        if submitted:
            if not current_name:
                st.warning("로그인 후 작성할 수 있습니다.")
            elif answer_text.strip():
                new_answer = {
                    "id": int(time.time()*1000) + random.randint(0,999),
                    "name": current_name,
                    "age_band": current_age,
                    "answer": answer_text.strip()
                }
                upsert_answer(new_answer)
                st.success("답변이 제출되었습니다.")
                st.rerun()
            else:
                st.warning("답변 내용을 입력해 주세요.")

    # 답변 리스트
    st.divider()
    st.subheader(f"📬 누적 답변 ({len(st.session_state.daily_answers)}명)")
    if not st.session_state.daily_answers:
        st.info("아직 등록된 답변이 없습니다. 첫 번째 답변을 남겨보세요!")
        return

    answers_sorted = sorted(st.session_state.daily_answers, key=lambda x: x.get("id", 0), reverse=True)

    st.markdown('<div class="answer-grid">', unsafe_allow_html=True)
    for a in answers_sorted:
        a_id   = a.get("id")
        a_name = a.get("name", "익명")
        a_age  = a.get("age_band", "미등록")
        a_text = a.get("answer", "")
        is_owner = (current_name and a_name == current_name)
        editing_this = (st.session_state.editing_answer_id == a_id)

        st.markdown('<div class="answer-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="answer-meta">[{html.escape(str(a_age))}] <strong>{html.escape(str(a_name))}</strong></div>', unsafe_allow_html=True)

        if editing_this:
            with st.form(f"edit_form_{a_id}"):
                new_text = st.text_area("내용 수정", a_text, max_chars=500, height=120, key=f"edit_text_{a_id}")
                c1, c2 = st.columns(2)
                with c1:
                    ok = st.form_submit_button("💾 저장")
                with c2:
                    cancel = st.form_submit_button("취소")
            if ok:
                if new_text.strip():
                    a["answer"] = new_text.strip()
                    upsert_answer(a)
                    st.session_state.editing_answer_id = None
                    st.success("수정되었습니다.")
                    st.rerun()
                else:
                    st.warning("내용이 비어 있습니다.")
            if cancel:
                st.session_state.editing_answer_id = None
                st.rerun()
        else:
            safe = html.escape(a_text).replace("\n", "<br>")
            st.markdown(f'<div class="answer-text">{safe}</div>', unsafe_allow_html=True)
            if is_owner:
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✏️ 수정", key=f"btn_edit_{a_id}"):
                        st.session_state.editing_answer_id = a_id
                        st.rerun()
                with c2:
                    if st.button("🗑️ 삭제", key=f"btn_del_{a_id}"):
                        delete_answer_by_id(a_id)
                        st.success("삭제되었습니다.")
                        st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)  # card
    st.markdown('</div>', unsafe_allow_html=True)      # grid

# =========================================================
# 메인
# =========================================================
def main():
    if st.session_state.get("connecting"):
        mentor_name = st.session_state.connect_mentor_name
        st.info(f"🔗 **{mentor_name} 멘토**님과 화상 연결을 준비 중입니다. 잠시만 기다려주세요...")
        time.sleep(2); st.balloons()
        st.markdown(f"<script>window.open('{GOOGLE_MEET_URL}', '_blank');</script>", unsafe_allow_html=True)
        st.success(f"✅ **{mentor_name} 멘토**님과의 화상 채팅 연결이 새로운 탭에서 시작되었습니다.")
        st.markdown(f"**[Google Meet 연결 바로가기: {GOOGLE_MEET_URL}]({GOOGLE_MEET_URL})**")
        if st.button("⬅️ 다른 멘토 찾아보기"):
            st.session_state.connecting = False
            del st.session_state.connect_mentor_name
            st.rerun()
        st.stop()

    st.sidebar.title("메뉴")
    st.title("👵👴 결(멘티용)🧑‍💻")

    if not st.session_state.logged_in:
        auth_option = st.radio("서비스 시작", ["로그인", "회원 가입"], index=0, horizontal=True)
        if auth_option == "로그인": show_login_form()
        else: show_registration_form()
    else:
        page = st.sidebar.radio("페이지 이동", ["멘토 찾기", "오늘의 질문"], index=0)
        st.sidebar.divider()
        st.sidebar.markdown(f"**환영합니다, {st.session_state.user_profile.get('name')}님!**")
        st.sidebar.caption(f"나이대: {st.session_state.user_profile.get('age_band')}")
        if st.sidebar.button("🚪 로그아웃"):
            st.session_state.logged_in = False
            st.session_state.user_profile = {}
            st.info("로그아웃되었습니다.")
            st.rerun()
        if page == "멘토 찾기":
            show_mentor_search_and_connect()
        else:
            show_daily_question()

if __name__ == "__main__":
    main()
