import streamlit as st
import pandas as pd
import random
import time
import os
import json 

# --- 1. 데이터 로드 및 상수 정의 (변경 없음) ---

MENTOR_CSV_PATH = "멘토더미.csv"
USERS_FILE_PATH = "users.json" # 사용자 계정 정보를 저장할 파일 경로
ANSWERS_FILE_PATH = "daily_answers.json" # 오늘의 질문 답변을 저장할 파일 경로
# 가상의 화상 채팅 연결 URL (실제 연결될 URL)
GOOGLE_MEET_URL = "https://meet.google.com/urw-iods-puy"

# --- 상수 및 옵션 정의 (변경 없음) ---
GENDERS = ["남", "여", "기타"]
COMM_METHODS = ["대면 만남", "화상채팅", "일반 채팅"]
WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]
TIMES = ["오전", "오후", "저녁"]
AGE_BANDS = [
    "만 13세~19세", "만 20세~29세", "만 30세~39세",
    "만 40세~49세", "만 50세~59세", # 50-59세 수정
    "만 60세~69세",
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

# --- 2. 데이터 초기화 및 로드 (변경 없음) ---
# (load_mentor_data, load_json_data, save_json_data, initialize_session_state 함수는 내용이 길어 생략하고 그대로 사용됨을 가정합니다.)

def load_mentor_data():
    if os.path.exists(MENTOR_CSV_PATH):
        try:
            df = pd.read_csv(MENTOR_CSV_PATH, encoding='utf-8')
            df.columns = df.columns.str.strip()
            required_cols = ['name', 'age_band', 'occupation_major', 'topic_prefs', 'style', 'intro']

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


def load_json_data(file_path, default_value):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.warning(f"데이터 파일 로드 오류 ({file_path}): {e}. 기본값으로 시작합니다.")
            return default_value
    return default_value

def save_json_data(data, file_path):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"데이터 파일 저장 오류 ({file_path}): {e}")


def initialize_session_state():
    mentors_df = load_mentor_data()
    st.session_state.mentors_df = mentors_df

    # 영구 저장된 사용자 데이터를 로드
    st.session_state.all_users = load_json_data(USERS_FILE_PATH, {})

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = {}

    # 영구 저장된 답변 데이터를 로드하거나, 없으면 초기 답변을 생성
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
        
    # 삭제 확인 상태 (답변 인덱스)
    if 'confirming_delete_index' not in st.session_state:
        st.session_state.confirming_delete_index = -1 


    if 'recommendations' not in st.session_state:
        st.session_state.recommendations = pd.DataFrame()

initialize_session_state()

if st.session_state.mentors_df.empty and not st.session_state.logged_in:
    st.stop()


# --- 3. 멘토 추천 로직 함수 (변경 없음) ---
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


# --- 4. 인증/회원가입/UI 함수 정의 (로그인, 회원가입, 멘토 검색은 UI 개선이 없어 함수 전체를 생략합니다. main 함수에서 호출됨을 가정합니다.) ---

def show_login_form():
    # 기존 코드 유지 (보안 문제는 이번 개선 범위 제외)
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
                st.success(f"🎉 {name}님, 환
