import streamlit as st
import pandas as pd
import random
import time
import os
import json 

# --- 1. 데이터 로드 및 상수 정의 ---

MENTOR_CSV_PATH = "멘토더미.csv"
USERS_FILE_PATH = "users.json" # 사용자 계정 정보를 저장할 파일 경로
ANSWERS_FILE_PATH = "daily_answers.json" # 오늘의 질문 답변을 저장할 파일 경로
# 가상의 화상 채팅 연결 URL (실제 연결될 URL)
GOOGLE_MEET_URL = "https://meet.google.com/urw-iods-puy"

# --- 상수 및 옵션 정의 ---
GENDERS = ["남", "여", "기타"]
COMM_METHODS = ["대면 만남", "화상채팅", "일반 채팅"]
WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]
TIMES = ["오전", "오후", "저녁"]
AGE_BANDS = [
    "만 13세~19세", "만 20세~29세", "만 30세~39세",
    "만 40세~49세", "만 50세~59세", "만 60세~69세",
    "만 70세~79세", "만 80세~89세", "만 90세 이상"
]

# 직종 그룹: 대분류 리스트로 최종 변경
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
    # 특수 상황군
    "학생",
    "전업주부",
    "구직/이직",
    "프리랜서",
    "기타"
]

INTERESTS = {
    "여가/취미 관련": ["독서", "음악 감상", "영화/드라마 감상", "게임 (PC/콘솔/모바일)", "운동/스포츠 관람", "미술·전시 감상", "여행", "요리/베이킹", "사진/영상 제작", "춤/노래"],
    "학문/지적 관심사": ["인문학 (철학, 역사, 문학 등)", "사회과학 (정치, 경제, 사회, 심리 등)", "자연과학 (물리, 화학, 생명과학 등)", "수학/논리 퍼즐", "IT/테크놀로지 (AI, 코딩, 로봇 등)", "환경/지속가능성"],
    "라이프스타일": ["패션/뷰티", "건강/웰빙", "자기계발", "사회참여/봉사활동", "재테크/투자", "반려동물"],
    "대중문화": ["K-POP", "아이돌/연예인", "유튜브/스트리밍", "웹툰/웹소설", "스포츠 스타"],
    "취향/성향": ["혼자 보내는 시간 선호", "친구들과 어울리기 선호", "실내 활동 선호", "야외 활동 선호", "새로움 추구 vs 안정감 추구"]
}
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

# --- 2. 데이터 초기화 및 로드 ---

def load_mentor_data():
    if os.path.exists(MENTOR_CSV_PATH):
        try:
            df = pd.read_csv(MENTOR_CSV_PATH, encoding='utf-8')
            df.columns = df.columns.str.strip()
            # 'style'을 필수 컬럼으로 가정
            required_cols = ['name', 'age_band', 'occupation_major', 'topic_prefs', 'style', 'intro']

            # 파일 컬럼 이름이 'communication_style'이면 'style'로 변경하여 호환성 확보
            if 'communication_style' in df.columns and 'style' not in df.columns:
                df = df.rename(columns={'communication_style': 'style'})

            missing_cols = [col for col in required_cols if col not in df.columns]

            if missing_cols:
                st.error(f"멘토 CSV 파일에 다음 컬럼이 누락되었습니다: {', '.join(missing_cols)}")
                st.info(f"현재 파일의 컬럼 목록: {', '.join(df.columns)}")
                return pd.DataFrame()
            return df
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(MENTOR_CSV_PATH, encoding='cp949')
                df.columns = df.columns.str.strip()
                # 파일 컬럼 이름이 'communication_style'이면 'style'로 변경하여 호환성 확보
                if 'communication_style' in df.columns and 'style' not in df.columns:
                    df = df.rename(columns={'communication_style': 'style'})
                return df
            except Exception as e:
                st.error(f"CSV 파일 로드 중 심각한 오류 발생: {e}")
                return pd.DataFrame()
        except Exception as e:
            st.error(f"CSV 파일 로드 중 예상치 못한 오류 발생: {e}")
            return pd.DataFrame()
    else:
        st.error(f"Error: 멘토 데이터 파일 '{MENTOR_CSV_PATH}'을(를) 찾을 수 없습니다.")
        return pd.DataFrame()


# --- 2-1. 영구 저장(Persistence) 헬퍼 함수 ---
def load_json_data(file_path, default_value):
    """JSON 파일에서 데이터를 로드하거나, 파일이 없으면 기본값을 반환합니다."""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.warning(f"데이터 파일 로드 오류 ({file_path}): {e}. 기본값으로 시작합니다.")
            return default_value
    return default_value

def save_json_data(data, file_path):
    """데이터를 JSON 파일에 저장합니다."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            # ensure_ascii=False: 한글 깨짐 방지, indent=4: 가독성 높임
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"데이터 파일 저장 오류 ({file_path}): {e}")
# ---------------------------------------------


def initialize_session_state():
    mentors_df = load_mentor_data()
    st.session_state.mentors_df = mentors_df

    # 🌟 수정: 영구 저장된 사용자 데이터를 로드
    st.session_state.all_users = load_json_data(USERS_FILE_PATH, {})

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = {}

    # 🌟 수정: 영구 저장된 답변 데이터를 로드하거나, 없으면 초기 답변을 생성
    daily_answers_from_file = load_json_data(ANSWERS_FILE_PATH, None)

    if daily_answers_from_file is not None:
        st.session_state.daily_answers = daily_answers_from_file
    else:
        # 초기 답변 생성 로직 (파일이 없을 경우)
        initial_answers = []
        st.session_state.daily_answers = initial_answers
        # 초기 답변이 생성되면 파일에 저장 (최초 1회)
        save_json_data(st.session_state.daily_answers, ANSWERS_FILE_PATH)
        
    # 수정/삭제 기능 관련 상태 초기화. -1은 수정 중인 답변이 없음을 의미합니다.
    if 'editing_index' not in st.session_state:
        st.session_state.editing_index = -1

    if 'recommendations' not in st.session_state:
        st.session_state.recommendations = pd.DataFrame()

initialize_session_state()

if st.session_state.mentors_df.empty and not st.session_state.logged_in:
    st.stop()

# --- 3. 멘토 추천 로직 함수 ---

def recommend_mentors(search_field, search_topic, search_style):
    mentors = st.session_state.mentors_df.copy()
    mentors['score'] = 0

    if search_field:
        mentors['score'] += mentors['occupation_major'].apply(lambda x: 3 if x == search_field else 0)

    if search_topic:
        mentors['score'] += mentors['topic_prefs'].astype(str).apply(
            lambda x: 2 if search_topic in x else 0
        )

    if search_style:
        # 'style' 컬럼 사용 가정
        mentors['score'] += mentors['style'].apply(lambda x: 1 if x == search_style else 0)

    if search_field or search_topic or search_style:
        recommended_mentors = mentors[mentors['score'] > 0].sort_values(by='score', ascending=False)
    else:
        recommended_mentors = mentors.sort_values(by='name', ascending=True)

    return recommended_mentors.reset_index(drop=True)


# --- 4. 인증/회원가입/UI 함수 정의 ---

def show_login_form():
    """로그인 폼을 표시합니다."""
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
    """회원 가입 폼을 표시합니다."""
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
        selected_topics = st.multiselect(
            "멘토링에서 주로 어떤 주제에 대해 이야기하고 싶으신가요?",
            TOPIC_PREFS
        )

        st.subheader("선호하는 소통 스타일")
        comm_style_options = [f"{k}: {v}" for k, v in COMM_STYLES.items()]
        selected_style_full = st.radio(
            "평소 대화 시 본인과 비슷하거나 선호하는 스타일을 선택해주세요",
            comm_style_options,
            key="comm_style_radio"
        )
        selected_style = selected_style_full.split(':')[0]

        submitted = st.form_submit_button("가입 완료 및 서비스 시작")

        if submitted:
            if not name or not available_days or not available_times or not selected_topics or not selected_style:
                st.error("이름, 소통 가능 요일/시간, 주제, 소통 스타일은 필수 입력 항목입니다.")
            elif name in st.session_state.all_users:
                st.error(f"'{name}' 이미 등록된 이름입니다.")
            else:
                user_profile_data = {
                    "name": name,
                    "gender": gender,
                    "age_band": age_band,
                    "comm_method": comm_method,
                    "available_days": available_days,
                    "available_times": available_times,
                    "occupation_group": occupation_key,
                    "topic_prefs": selected_topics,
                    "comm_style": selected_style
                }

                st.session_state.all_users[name] = user_profile_data
                st.session_state.user_profile = user_profile_data
                st.session_state.logged_in = True

                # 🌟 수정: 사용자 데이터 영구 저장
                save_json_data(st.session_state.all_users, USERS_FILE_PATH)

                st.success(f"🎉 {name}님, 성공적으로 가입 및 로그인되었습니다!")
                st.rerun()

def show_mentor_search_and_connect():
    """멘토 검색 및 연결 기능을 표시합니다."""
    st.header("🔍 멘토 찾기 및 연결")

    mentors = st.session_state.mentors_df

    # --- 검색 조건 입력 ---
    st.subheader("나에게 맞는 멘토 검색하기")

    with st.form("mentor_search_form"):
        col_f, col_t, col_s = st.columns(3)

        available_topics = sorted([t for t in set(t.strip() for items in mentors['topic_prefs'].astype(str).str.split('[,;]') for t in items if t.strip())])

        # 'style' 컬럼을 사용하도록 가정하고, 해당 컬럼의 고유값을 스타일 옵션으로 사용
        if 'style' in mentors.columns:
            available_styles = sorted(list(mentors['style'].dropna().unique()))
        else:
            available_styles = sorted(list(COMM_STYLES.keys())) # fallback

        available_fields_clean = sorted(OCCUPATION_GROUPS)

        with col_f:
            search_field = st.selectbox("💼 전문 분야 (직종 분류)", options=['(전체)'] + available_fields_clean)

        with col_t:
            search_topic = st.selectbox("💬 주요 대화 주제", options=['(전체)'] + available_topics)

        with col_s:
            search_style = st.selectbox("🗣️ 선호 대화 스타일", options=['(전체)'] + available_styles)

        submitted = st.form_submit_button("🔎 검색 시작")

    if submitted:
        field = search_field if search_field != '(전체)' else ''
        topic = search_topic if search_topic != '(전체)' else ''
        style = search_style if search_style != '(전체)' else ''

        with st.spinner("최적의 멘토를 찾는 중..."):
            recommendation_results = recommend_mentors(field, topic, style)
            st.session_state.recommendations = recommendation_results

        if recommendation_results.empty and (field or topic or style):
            st.info("⚠️ 선택하신 조건에 맞는 멘토를 찾지 못했습니다. 조건을 변경해 보세요.")
        elif recommendation_results.empty:
            st.info("멘토 데이터가 비어있습니다. 데이터를 확인해 주세요.")

    # --- 검색 결과 표시 ---
    if not st.session_state.recommendations.empty:
        st.subheader(f"총 {len(st.session_state.recommendations)}명의 멘토가 검색되었습니다.")
        if 'score' in st.session_state.recommendations.columns:
            st.caption("(추천 점수 또는 이름순)")

        for index, row in st.session_state.recommendations.iterrows():
            with st.container(border=True):
                col_name, col_score = st.columns([3, 1])
                with col_name:
                    st.markdown(f"#### 👤 {row['name']} ({row['age_band']})")
                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    st.markdown(f"**전문 분야:** {row['occupation_major']}")
                with col_m2:
                    st.markdown(f"**주요 주제:** {row['topic_prefs']}")
                with col_m3:
                    # 'style' 컬럼 값 출력 가정
                    st.markdown(f"**소통 스타일:** {row['style']}")

                st.markdown(f"**멘토 한마디:** _{row['intro']}_")

                connect_button_key = f"connect_btn_{row['name']}_{index}"
                if st.button("🔗 연결", key=connect_button_key):
                    st.session_state.connecting = True
                    st.session_state.connect_mentor_name = row['name']
                    st.rerun()

    elif not submitted:
        st.info("검색 조건을 입력하고 '🔎 검색 시작' 버튼을 눌러 멘토를 찾아보세요.")


def show_daily_question():
    st.header("💬 오늘의 질문: 세대 공감 창구")
    st.write("매일 올라오는 질문에 대해 다양한 연령대의 답변을 공유하는 공간입니다.")

    # 1. 디자인: 말풍선 모양 및 색상, 배경 그라데이션, 움직임 제거 Custom CSS
    st.markdown(f"""
        <style>
        /* 앱 전체 배경 강렬한 마젠타-퍼플 그라데이션 (첨부된 이미지 색상 기반) */
        .stApp {{
            background: linear-gradient(135deg, #FF69B4 0%, #8A2BE2 100%); /* Hot Pink to Blue Violet */
            background-attachment: fixed; /* 스크롤 시에도 배경 고정 */
        }}

        /* Streamlit 기본 텍스트 색상 및 헤더 색상 조정 */
        h1, h2, h3, h4, h5, h6, .stMarkdown, .stSubheader, label {{
            color: #FFFFFF !important; /* 헤더 및 라벨 텍스트를 밝은 색으로 변경 */
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
        }}
        div[data-testid="stText"] {{
             color: #EEEEEE !important;
        }}
        /* 사이드바 텍스트 색상 */
        .css-vk3ghm, .css-1dp54x6, .css-1aumw6k {{
            color: #FFFFFF !important;
        }}

        /* 2. 말풍선 컨테이너 (st.container) 스타일링 */
        .bubble-container {{
            position: relative;
            background: #ffffff; /* 모든 말풍선 흰색 */
            border-radius: 1.5em; /* 둥근 사각형 */
            padding: 20px;
            padding-top: 40px; /* 옵션 버튼 공간 확보를 위해 위쪽 패딩 증가 */
            margin: 20px 0 5px 0; 
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.25); /* 그림자 강화 및 입체감 추가 */
            transition: all 0.2s ease-in-out;
            border: 1px solid rgba(255, 255, 255, 0.8); 
        }}
        
        .bubble-container:hover {{
            transform: translateY(-5px); 
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.4); 
        }}
        
        /* 3. 답변 텍스트 스타일 */
        .bubble-answer {{
            font-size: 1.1em;
            line-height: 1.6;
            color: #333333;
            margin-top: 10px;
        }}

        /* 4. 이름/나이대 정보 스타일 */
        .bubble-info {{
            font-size: 1em; 
            font-weight: bold; 
            color: #6A0DAD; /* 이름 정보를 퍼플 계열로 강조 */
            border-bottom: 1px solid rgba(0,0,0,0.1); 
            padding-bottom: 8px;
            margin-bottom: 12px;
            position: absolute; /* 옵션 버튼과 겹치지 않도록 절대 위치 지정 */
            top: 15px;
            left: 20px;
        }}
        
        /* 5. 폼 배경색을 흰색으로 설정하여 가독성 높임 */
        div[data-testid="stForm"] {{
            background-color: rgba(255, 255, 255, 0.9);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }}
        div[data-testid="stForm"] label {{
            color: #333333 !important; 
            text-shadow: none;
        }}

        /* 6. 수정/삭제 메뉴 버튼 (점 세 개 역할) 스타일: 답변 박스 오른쪽 상단에 위치시키기 */
        /* st.expander가 생성하는 최상위 div를 타겟팅 */
        div[data-testid^="stExpander"] {{
            /* st.expander를 .bubble-container의 영역으로 끌어올리기 위해 마진 조정 */
            margin-top: -65px !important; 
            margin-bottom: 0px !important; 
            /* 내부에서 절대 위치를 사용하므로 z-index는 높게 유지 */
            z-index: 10; 
        }}
        
        /* st.expander의 버튼 부분 (타이틀 '...')을 오른쪽 상단에 고정 */
        div[data-testid^="stExpander"] > div[role="button"] {{
            position: absolute;
            top: 20px; /* .bubble-container의 상단에서 20px 아래로 배치 */
            right: 20px; /* 오른쪽에서 20px 간격으로 배치 */
            padding: 5px; 
            background-color: transparent !important;
            color: #6A0DAD !important; /* 점 색상을 보라색으로 */
            font-size: 1.5em; /* 점 세 개 아이콘 크기 */
            text-align: right;
            border-radius: 50%;
            cursor: pointer;
            width: auto; /* 너비를 내용에 맞게 조정 */
        }}

        /* Expander 컨텐츠 (Edit/Delete 버튼) 스타일 조정 */
        div[data-testid^="stExpander"] .stExpanderDetails {{
            position: absolute; /* 버튼 아래로 드롭다운 메뉴 위치 */
            right: 20px; 
            top: 45px; /* 버튼 바로 아래로 드롭다운 */
            background-color: #ffffff; 
            border: 1px solid #ccc;
            border-radius: 8px;
            padding: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            width: 150px;
            z-index: 20;
        }}

        </style>
    """, unsafe_allow_html=True)


    daily_q = "🤔 **'나와 전혀 다른 세대의 삶을 하루만 살아볼 수 있다면, 어떤 세대의 삶을 살아보고 싶은지 이유와 함께 알려주세요!'**"
    st.subheader(daily_q)

    # --- 답변 리스트 (세션 상태에 누적된 답변 사용) ---
    if st.session_state.daily_answers:
        # 원본 리스트를 직접 수정하기 위해 정렬하지 않고 사용합니다. (인덱스 유지)
        sorted_answers = st.session_state.daily_answers 
        current_name = st.session_state.user_profile.get('name')
        
        cols = st.columns(3)
        
        for i, ans in enumerate(sorted_answers):
            # 답변 하나당 하나의 컬럼 컨테이너에 들어갑니다.
            with cols[i % 3]: 
                is_owner = (ans['name'] == current_name)
                
                # ---------------------- 수정 모드 --------------------------
                if st.session_state.editing_index == i:
                    # 수정 모드일 때는 일반 말풍선 대신 수정 폼을 표시합니다.
                    with st.form(f"edit_form_{i}", clear_on_submit=False):
                        st.markdown(f"**답변 수정 [{ans['age_band']}]**", unsafe_allow_html=True)
                        edited_text = st.text_area("수정 내용", ans['answer'], height=100, key=f"edit_text_{i}")
                        col_save, col_cancel = st.columns(2)
                        
                        with col_save:
                            if st.form_submit_button("저장", type="primary", use_container_width=True):
                                if edited_text:
                                    st.session_state.daily_answers[i]['answer'] = edited_text
                                    st.session_state.editing_index = -1
                                    save_json_data(st.session_state.daily_answers, ANSWERS_FILE_PATH)
                                    st.success("✅ 답변이 성공적으로 수정되었습니다!")
                                    st.rerun()
                                else:
                                    st.error("수정할 내용을 입력해 주세요.")
                        with col_cancel:
                            if st.form_submit_button("취소", use_container_width=True):
                                st.session_state.editing_index = -1
                                st.rerun()
                
                # ---------------------- 일반 표시 모드 --------------------------
                else:
                    # 마크다운을 사용하여 말풍선 및 내용 표시
                    st.markdown(
                        f"""
                        <div class='bubble-container'>
                            <p class='bubble-info'>
                                [{ans['age_band']}] <span>{ans['name']}</span>님의 생각
                            </p>
                            <p class='bubble-answer'>
                                {ans['answer']}
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    # 소유자에게만 수정/삭제 메뉴 표시 (점 세 개 역할)
                    if is_owner:
                        # Streamlit Expander를 점 세 개 메뉴처럼 사용하여 옵션 제공
                        # 레이블을 '...'로 줄이고 CSS로 위치를 조정하여 말풍선 안에 있는 것처럼 보이게 합니다.
                        with st.expander("...", expanded=False): 
                            col_e, col_d = st.columns(2)
                            
                            with col_e:
                                if st.button("✏️ 수정", key=f"edit_{i}", use_container_width=True):
                                    st.session_state.editing_index = i
                                    st.rerun()
                            
                            with col_d:
                                # 삭제 버튼을 누르면 바로 삭제되지 않고 확인 절차를 거칩니다.
                                if st.button("🗑️ 삭제", key=f"delete_{i}", use_container_width=True, type="secondary"):
                                    # 삭제 확인 메시지 표시
                                    st.warning(f"정말로 답변을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.", icon="⚠️")
                                    col_confirm, col_cancel = st.columns(2)
                                    with col_confirm:
                                        if st.button("✅ 예, 삭제합니다.", key=f"confirm_delete_{i}", use_container_width=True):
                                            del st.session_state.daily_answers[i]
                                            save_json_data(st.session_state.daily_answers, ANSWERS_FILE_PATH)
                                            st.toast("🗑️ 답변이 삭제되었습니다.")
                                            st.session_state.editing_index = -1 # 수정 모드 해제
                                            st.rerun()
                                    with col_cancel:
                                        if st.button("❌ 취소", key=f"cancel_delete_{i}", use_container_width=True):
                                            # 아무 동작도 하지 않거나, 메시지를 지우고 싶다면 다시 렌더링
                                            st.session_state.editing_index = -1 # 수정 모드 해제
                                            st.rerun()


    st.divider()

    # --- 답변 작성 폼 ---
    st.subheader("나의 답변 작성")
    current_name = st.session_state.user_profile.get('name', '익명')
    current_age = st.session_state.user_profile.get('age_band', '미등록')

    with st.form("answer_form"):
        # "질문에 대한 당신의 생각을 적어주세요." 텍스트 삭제, placeholder로 대체
        answer_text = st.text_area("", max_chars=500, height=150, placeholder="여기에 당신의 생각을 자유롭게 적어주세요...")
        submitted = st.form_submit_button("답변 제출", type="primary")

        if submitted:
            if answer_text:
                new_answer = {
                    "name": current_name,
                    "age_band": current_age,
                    "answer": answer_text
                }
                st.session_state.daily_answers.append(new_answer)

                # 🌟 수정: 답변 데이터 영구 저장
                save_json_data(st.session_state.daily_answers, ANSWERS_FILE_PATH)

                st.success("✅ 답변이 성공적으로 제출되었습니다! 이제 목록에서 바로 확인하실 수 있습니다.")
                st.rerun() 
            else:
                st.warning("답변 내용을 입력해 주세요.")


# --- 5. 메인 앱 실행 함수 (디버그 패널 포함) ---

def main():
    st.set_page_config(
        page_title="세대 간 멘토링 플랫폼",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    if st.session_state.mentors_df.empty and not st.session_state.logged_in:
        st.title("👵👴 플랫폼 준비 중 🧑‍💻")
        st.error(f"⚠️ 멘토 데이터 파일 '{MENTOR_CSV_PATH}'을(를) 로드하지 못했습니다. 파일을 확인해 주세요.")
        st.stop()

    # --- 연결 프로세스 처리 ---
    if st.session_state.get('connecting'):
        mentor_name = st.session_state.connect_mentor_name

        st.info(f"🔗 **{mentor_name} 멘토**님과 화상 연결을 준비 중입니다. 잠시만 기다려주세요...")
        time.sleep(2)
        st.balloons()

        st.markdown(
            f"""
            <script>
                window.open('{GOOGLE_MEET_URL}', '_blank');
            </script>
            """,
            unsafe_allow_html=True
        )

        st.success(f"✅ **{mentor_name} 멘토**님과의 화상 채팅 연결이 새로운 탭에서 시작되었습니다.")
        st.markdown(f"**[Google Meet 연결 바로가기: {GOOGLE_MEET_URL}]({GOOGLE_MEET_URL})**")

        if st.button("⬅️ 다른 멘토 찾아보기"):
            st.session_state.connecting = False
            del st.session_state.connect_mentor_name
            st.rerun()

        st.stop()

    # --- 메인 페이지 흐름 제어 ---
    st.sidebar.title("메뉴")

    st.title("👵👴 결(멘티용)🧑‍💻")

    if not st.session_state.logged_in:
        # 로그인/회원가입 선택
        auth_option = st.sidebar.radio("서비스 시작", ["로그인", "회원 가입"], index=0, horizontal=True)
        if auth_option == "로그인":
            show_login_form()
        else:
            show_registration_form()

    else:
        # 로그인된 사용자용 메인 화면
        page = st.sidebar.radio(
            "페이지 이동",
            ["멘토 찾기", "오늘의 질문"],
            index=0
        )

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
        elif page == "오늘의 질문":
            show_daily_question()

if __name__ == "__main__":
    main()
