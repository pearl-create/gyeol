import streamlit as st
import pandas as pd
import random
import time
import os

# --- 1. 데이터 로드 및 상수 정의 ---

# 멘토 데이터 파일 경로 (사용자 업로드 파일)
MENTOR_CSV_PATH = "멘토더미.csv"
# 가상의 화상 채팅 연결 URL (실제 연결될 URL)
GOOGLE_MEET_URL = "https://meet.google.com/urw-iods-puy" 

# --- 상수 및 옵션 정의 (이전과 동일) ---
GENDERS = ["남", "여", "기타"]
COMM_METHODS = ["대면 만남", "화상채팅", "일반 채팅"]
WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]
TIMES = ["오전", "오후", "저녁", "밤"]
AGE_BANDS = [
    "만 13세~19세", "만 20세~29세", "만 30세~39세", 
    "만 40세~49세", "만 50세~59세", "만 60세~69세", 
    "만 70세~79세", "만 80세~89세", "만 90세 이상"
]
OCCUPATION_GROUPS = {
    "경영자": "CEO / 사업주 / 임원 / 부서장", "행정관리": "공공기관 관리자 / 기업 행정팀장 / 프로젝트 매니저", 
    "의학/보건": "의사 / 치과의사 / 약사 / 간호사 / 한의사 / 물리치료사", "법률/행정": "변호사 / 판사 / 검사 / 세무사 / 행정사", 
    "교육": "교수 / 교사 / 학원강사 / 연구원", "연구개발/ IT": "엔지니어 / 연구원 / 소프트웨어 개발자 / 데이터 분석가", 
    "예술/디자인": "디자이너 / 예술가 / 작가 / 사진작가", "기술/기능": "기술자 / 공학 기술자 / 실험실 기술자 / 회계사 / 건축기사", 
    "서비스 전문": "상담사 / 심리치료사 / 사회복지사 / 코디네이터", "일반 사무": "사무직원 / 경리 / 비서 / 고객 상담 / 문서 관리", 
    "영업 원": "영업사원 / 마케팅 지원 / 고객 관리", "판매": "점원 / 슈퍼 / 편의점 직원 / 백화점 직원", 
    "서비스": "접객원 / 안내원 / 호텔리어 / 미용사 / 요리사", "의료/보건 서비스": "간호조무사 / 재활치료사 / 요양보호사", 
    "생산/제조": "공장 생산직 / 조립공 / 기계조작원 / 용접공", "건설/시설": "배관공 / 전기공 / 건설노무자 / 목수", 
    "농림수산업": "농부 / 축산업 / 어부 / 임업 종사자", "운송/기계": "트럭기사 / 버스기사 / 지게차 운전 / 기계조작원", 
    "운송 관리": "물류 관리자 / 항만·공항 직원", "청소 / 경비": "청소원 / 경비원 / 환경미화원", 
    "단순노무": "일용직 / 공장 단순노무 / 배달원", "학생": "(초·중·고·대학생 / 대학원생)", 
    "전업주부": "전업주부", "구직자 / 최근 퇴사자 / 프리랜서(임시)": "구직자 / 최근 퇴사자 / 프리랜서(임시)", "기타": "기타 (직접 입력)"
}
INTERESTS = {
    "여가/취미 관련": ["독서", "음악 감상", "영화/드라마 감상", "게임 (PC/콘솔/모바일)", "운동/스포츠 관람", "미술·전시 감상", "여행", "요리/베이킹", "사진/영상 제작", "춤/노래"],
    "학문/지적 관심사": ["인문학 (철학, 역사, 문학 등)", "사회과학 (정치, 경제, 사회, 심리 등)", "자연과학 (물리, 화학, 생명과학 등)", "수학/논리 퍼즐", "IT/테크놀로지 (AI, 코딩, 로봇 등)", "환경/지속가능성"],
    "라이프스타일": ["패션/뷰티", "건강/웰빙", "자기계발", "사회참여/봉사활동", "재테크/투자", "반려동물"],
    "대중문화": ["K-POP", "아이돌/연예인", "유튜브/스트리밍", "웹툰/웹소설", "스포츠 스타"],
    "특별한 취향/성향": ["혼자 보내는 시간 선호", "친구들과 어울리기 선호", "실내 활동 선호", "야외 활동 선호", "새로움 추구 vs 안정감 추구"]
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

@st.cache_data
def load_mentor_data():
    """CSV 파일에서 멘토 데이터를 로드하고 컬럼명을 정리합니다."""
    if os.path.exists(MENTOR_CSV_PATH):
        try:
            df = pd.read_csv(MENTOR_CSV_PATH, encoding='utf-8')
            df.columns = df.columns.str.strip() 
            required_cols = ['name', 'age_band', 'occupation_major', 'topic_prefs', 'style', 'intro'] 
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

def initialize_session_state():
    mentors_df = load_mentor_data()
    st.session_state.mentors_df = mentors_df
    
    # --- 로그인 및 사용자 관리 관련 상태 ---
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = {}
    if 'all_users' not in st.session_state:
        st.session_state.all_users = {}
    
    # --- Q&A 누적 관련 상태 ---
    if 'daily_answers' not in st.session_state:
        initial_answers = [
            {"name": "진오", "age_band": "만 90세 이상", "answer": "너무 서두르지 말고, 꾸준함이 기적을 만든다는 것을 기억해라. 건강이 최고다."},
            {"name": "다온", "age_band": "만 70세~79세", "answer": "돈보다 경험에 투자하고, 사랑하는 사람들에게 지금 당장 마음을 표현하렴. 후회는 순간이 아닌 나중에 온단다."},
        ]
        st.session_state.daily_answers = initial_answers
        
    if 'recommendations' not in st.session_state:
        st.session_state.recommendations = pd.DataFrame()
    
initialize_session_state()

if st.session_state.mentors_df.empty and not st.session_state.logged_in:
    st.stop()
    
# --- 3. 멘토 추천 로직 함수 (이전과 동일) ---

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
        mentors['score'] += mentors['style'].apply(lambda x: 1 if search_style in x else 0)
    
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
    st.header("👤 회원 가입 (멘티/멘토 등록)")
    
    with st.form("registration_form"):
        st.subheader("기본 정보")
        name = st.text_input("이름 (로그인 시 사용됩니다)", placeholder="홍길동")
        gender = st.radio("성별", GENDERS, index=1, horizontal=True)
        age_band = st.selectbox("나이대", AGE_BANDS)
        
        st.subheader("소통 환경")
        comm_method = st.radio("선호하는 소통 방법", COMM_METHODS, horizontal=True)
        
        col_day, col_time = st.columns(2)
        with col_day:
            available
