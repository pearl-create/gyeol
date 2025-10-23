import streamlit as st
import pandas as pd
import random
import time

# --- 1. 데이터 로드 및 정의 ---

MENTOR_CSV_PATH = "멘토더미.csv"
GOOGLE_MEET_URL = "https://meet.google.com/urw-iods-puy"

try:
    # 멘토 데이터 로드 (사용자가 제공한 CSV 파일 활용)
    mentors_df = pd.read_csv(MENTOR_CSV_PATH)
    
    # 세션 상태에 데이터 초기화
    if 'mentors_df' not in st.session_state:
        st.session_state.mentors_df = mentors_df.copy()
    if 'is_registered' not in st.session_state:
        st.session_state.is_registered = False # 회원 가입 상태
    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = {} # 사용자 프로필 저장
        
except FileNotFoundError:
    st.error(f"Error: 멘토 데이터 파일 '{MENTOR_CSV_PATH}'을(를) 찾을 수 없습니다. 파일 경로를 확인해 주세요.")
    st.stop()
except Exception as e:
    st.error(f"멘토 데이터 로드 중 오류 발생: {e}")
    st.stop()

# --- 2. 상수 및 옵션 정의 (회원가입 폼에 사용) ---

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
    "경영자": "CEO / 사업주 / 임원 / 부서장",
    "행정관리": "공공기관 관리자 / 기업 행정팀장 / 프로젝트 매니저",
    "의학/보건": "의사 / 치과의사 / 약사 / 간호사 / 한의사 / 물리치료사",
    "법률/행정": "변호사 / 판사 / 검사 / 세무사 / 행정사",
    "교육": "교수 / 교사 / 학원강사 / 연구원",
    "연구개발/ IT": "엔지니어 / 연구원 / 소프트웨어 개발자 / 데이터 분석가",
    "예술/디자인": "디자이너 / 예술가 / 작가 / 사진작가",
    "기술/기능": "기술자 / 공학 기술자 / 실험실 기술자 / 회계사 / 건축기사",
    "서비스 전문": "상담사 / 심리치료사 / 사회복지사 / 코디네이터",
    "일반 사무": "사무직원 / 경리 / 비서 / 고객 상담 / 문서 관리",
    "영업 원": "영업사원 / 마케팅 지원 / 고객 관리",
    "판매": "점원 / 슈퍼 / 편의점 직원 / 백화점 직원",
    "서비스": "접객원 / 안내원 / 호텔리어 / 미용사 / 요리사",
    "의료/보건 서비스": "간호조무사 / 재활치료사 / 요양보호사",
    "생산/제조": "공장 생산직 / 조립공 / 기계조작원 / 용접공",
    "건설/시설": "배관공 / 전기공 / 건설노무자 / 목수",
    "농림수산업": "농부 / 축산업 / 어부 / 임업 종사자",
    "운송/기계": "트럭기사 / 버스기사 / 지게차 운전 / 기계조작원",
    "운송 관리": "물류 관리자 / 항만·공항 직원",
    "청소 / 경비": "청소원 / 경비원 / 환경미화원",
    "단순노무": "일용직 / 공장 단순노무 / 배달원",
    "학생": "(초·중·고·대학생 / 대학원생)",
    "전업주부": "전업주부",
    "구직자 / 최근 퇴사자 / 프리랜서(임시)": "구직자 / 최근 퇴사자 / 프리랜서(임시)",
    "기타 (직접 입력)": "기타 (직접 입력)"
}

INTERESTS = {
    "여가/취미 관련": [
        "독서", "음악 감상", "영화/드라마 감상", "게임 (PC/콘솔/모바일)", 
        "운동/스포츠 관람", "미술·전시 감상", "여행", "요리/베이킹", 
        "사진/영상 제작", "춤/노래"
    ],
    "학문/지적 관심사": [
        "인문학 (철학, 역사, 문학 등)", "사회과학 (정치, 경제, 사회, 심리 등)", 
        "자연과학 (물리, 화학, 생명과학 등)", "수학/논리 퍼즐", 
        "IT/테크놀로지 (AI, 코딩, 로봇 등)", "환경/지속가능성"
    ],
    "라이프스타일": [
        "패션/뷰티", "건강/웰빙", "자기계발", "사회참여/봉사활동", 
        "재테크/투자", "반려동물"
    ],
    "대중문화": [
        "K-POP", "아이돌/연예인", "유튜브/스트리밍", "웹툰/웹소설", 
        "스포츠 스타"
    ],
    "특별한 취향/성향": [
        "혼자 보내는 시간 선호", "친구들과 어울리기 선호", "실내 활동 선호", 
        "야외 활동 선호", "새로움 추구 vs 안정감 추구"
    ]
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

# --- 3. UI 컴포넌트 함수 정의 ---

def show_registration_form():
    """회원 가입 폼을 표시합니다."""
    st.header("👤 회원 가입 (멘티/멘토 등록)")
    
    with st.form("registration_form"):
        st.subheader("기본 정보")
        name = st.text_input("이름", placeholder="홍길동")
        gender = st.radio("성별", GENDERS, index=1)
        age_band = st.selectbox("나이대", AGE_BANDS)
        
        st.subheader("소통 환경")
        comm_method = st.radio("선호하는 소통 방법", COMM_METHODS, horizontal=True)
        
        col_day, col_time = st.columns(2)
        with col_day:
            available_days = st.multiselect("소통 가능한 요일", WEEKDAYS)
        with col_time:
            available_times = st.multiselect("소통 가능한 시간대", TIMES)
        
        st.subheader("현재 직종")
        occupation_key = st.selectbox("현재 직종 분류", list(OCCUPATION_GROUPS.keys()))
        occupation_detail = OCCUPATION_GROUPS[occupation_key]
        st.caption(f"상세 직무: {occupation_detail}")
        
        st.subheader("관심사, 취향")
        selected_interests = []
        for group, interests in INTERESTS.items():
            st.markdown(f"**{group}**")
            cols = st.columns(3)
            for i, interest in enumerate(interests):
                if cols[i % 3].checkbox(interest, key=f"interest_{interest}"):
                    selected_interests.append(interest)

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
        # 키워드만 추출
        selected_style = selected_style_full.split(':')[0]
        
        submitted = st.form_submit_button("가입 완료 및 서비스 시작")
        
        if submitted:
            if not name or not available_days or not available_times or not selected_topics or not selected_style:
                st.error("이름, 소통 가능 요일/시간, 주제, 소통 스타일은 필수 입력 항목입니다.")
            else:
                st.session_state.is_registered = True
                st.session_state.user_profile = {
                    "name": name,
                    "gender": gender,
                    "age_band": age_band,
                    "comm_method": comm_method,
                    "available_days": available_days,
                    "available_times": available_times,
                    "occupation_group": occupation_key,
                    "interests": selected_interests,
                    "topic_prefs": selected_topics,
                    "comm_style": selected_style # 멘토 데이터의 communication_style과 매칭
                }
                st.success(f"🎉 {name}님, 성공적으로 가입되었습니다! 이제 멘토를 찾아보세요.")
                st.experimental_rerun() # 가입 후 메인 페이지로 이동

def show_mentor_search_and_connect():
    """멘토 검색 및 연결 기능을 표시합니다."""
    st.header("🔍 멘토 찾기 및 연결")
    
    mentors = st.session_state.mentors_df.copy()
    
    # --- 검색 조건 입력 ---
    st.subheader("나에게 맞는 멘토 검색하기")
    
    with st.form("mentor_search_form"):
        col_f, col_t, col_s = st.columns(3)
        
        # 멘토 데이터에서 사용 가능한 옵션 추출
        available_fields = sorted(mentors['occupation_major'].unique().tolist())
        all_topics = set()
        mentors['topic_prefs'].astype(str).str.split('[,;]').apply(lambda x: all_topics.update([t.strip() for t in x if t.strip()]))
        available_topics = sorted([t for t in all_topics if t])
        available_styles = sorted(mentors['communication_style'].unique().tolist())
        
        with col_f:
            search_field = st.selectbox(
                "💼 전문 분야",
                options=['(전체)'] + available_fields
            )
        
        with col_t:
            search_topic = st.selectbox(
                "💬 주요 대화 주제",
                options=['(전체)'] + available_topics
            )
            
        with col_s:
            search_style = st.selectbox(
                "🗣️ 선호 대화 스타일",
                options=['(전체)'] + available_styles
            )

        submitted = st.form_submit_button("🔎 검색 시작")
        
    if submitted:
        # --- 검색 로직 ---
        # 1. 멘토 점수 계산 (이전 버전의 추천 로직을 검색 필터와 점수 기준으로 활용)
        
        mentors['score'] = 0
        
        # 1-1. 분야 (occupation_major) 매칭: 3점
        if search_field != '(전체)':
            mentors['score'] += mentors['occupation_major'].apply(lambda x: 3 if x == search_field else 0)
        
        # 1-2. 주제 (topic_prefs) 매칭: 2점
        if search_topic != '(전체)':
            mentors['score'] += mentors['topic_prefs'].astype(str).apply(
                lambda x: 2 if search_topic in x else 0
            )
        
        # 1-3. 대화 스타일 (communication_style) 매칭: 1점
        if search_style != '(전체)':
            mentors['score'] += mentors['communication_style'].apply(lambda x: 1 if x == search_style else 0)
            
        # 2. 필터링 및 정렬
        # '전체'가 아닌 검색 조건을 하나라도 선택했다면, 점수가 0점 이상인 멘토만 추천
        if search_field != '(전체)' or search_topic != '(전체)' or search_style != '(전체)':
            filtered_mentors = mentors[mentors['score'] > 0].sort_values(by='score', ascending=False)
        else:
            # 모든 조건이 '전체'일 경우, 모든 멘토를 랜덤하게 보여줌 (점수 0)
            filtered_mentors = mentors.sort_values(by='name', key=lambda x: [random.random() for _ in x], ascending=True)

        st.session_state.recommendations = filtered_mentors.reset_index(drop=True)

    # --- 검색 결과 표시 ---
    if 'recommendations' in st.session_state and not st.session_state.recommendations.empty:
        
        st.subheader(f"총 {len(st.session_state.recommendations)}명의 멘토가 검색되었습니다. (추천 점수 순)")
        
        for index, row in st.session_state.recommendations.iterrows():
            with st.container(border=True):
                col_name, col_score = st.columns([3, 1])
                with col_name:
                    st.markdown(f"#### 👤 {row['name']} ({row['age_band']})")
                with col_score:
                    if 'score' in row and row['score'] > 0:
                        st.markdown(f"**🌟 추천 점수: {int(row['score'])}점**")
                
                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    st.markdown(f"**전문 분야:** {row['occupation_major']}")
                with col_m2:
                    st.markdown(f"**주요 주제:** {row['topic_prefs']}")
                with col_m3:
                    st.markdown(f"**소통 스타일:** {row['communication_style']}")
                    
                st.markdown(f"**멘토 한마디:** _{row['intro']}_")
                
                # <연결> 버튼 로직
                connect_button_key = f"connect_btn_{row['name']}_{index}"
                if st.button("🔗 연결", key=connect_button_key):
                    st.session_state.connecting = True
                    st.session_state.connect_mentor_name = row['name']
                    st.experimental_rerun() # 연결 프로세스 시작을 위해 리런

    elif submitted:
        st.info("⚠️ 선택하신 조건에 맞는 멘토를 찾지 못했습니다. 조건을 변경해 보세요.")
    else:
        st.info("검색 조건을 입력하고 멘토를 찾아보세요.")

def show_daily_question():
    """오늘의 질문 게시판을 표시합니다."""
    st.header("💬 오늘의 질문: 세대 공감 창구")
    st.write("매일 올라오는 하나의 질문에 대해 다양한 연령대의 답변을 공유하는 공간입니다.")
    
    # 예시 질문 (매일 바뀐다고 가정)
    daily_q = "🤔 **'내가 만약 20대로 돌아간다면, 지금의 나에게 가장 해주고 싶은 조언은 무엇인가요?'**"
    st.subheader(daily_q)
    
    # --- 답변 리스트 (더미 데이터) ---
    sample_answers = [
        {"나이대": "만 90세 이상", "이름": "진오", "답변": "너무 서두르지 말고, 꾸준함이 기적을 만든다는 것을 기억해라. 건강이 최고다."},
        {"나이대": "만 20세~29세", "이름": st.session_state.user_profile.get('name', '청년 멘티'), "답변": "남들이 간다고 무조건 따라가지 말고, 나만의 속도를 찾는 용기가 필요하다고 말해주고 싶어요."},
        {"나이대": "만 70세~79세", "이름": "다온", "답변": "돈보다 경험에 투자하고, 사랑하는 사람들에게 지금 당장 마음을 표현하렴. 후회는 순간이 아닌 나중에 온단다."},
        {"나이대": "만 40세~49세", "이름": "관리자", "답변": "직장 상사에게 너무 목매지 말고, 이직이든 창업이든 계속해서 자기계발을 멈추지 않는 것이 중요하다고 조언할 것 같습니다."}
    ]
    
    # 답변 표시
    for ans in sample_answers:
        with st.expander(f"[{ans['나이대']}] {ans['이름']}님의 답변"):
            st.write(ans['답변'])
            
    st.divider()
    
    # --- 답변 작성 폼 ---
    st.subheader("나의 답변 작성하기")
    with st.form("answer_form"):
        answer_text = st.text_area("질문에 대한 당신의 생각을 적어주세요.", max_chars=500, height=150)
        submitted = st.form_submit_button("답변 제출")
        
        if submitted:
            if answer_text:
                st.success("답변이 제출되었습니다. 다른 분들의 답변도 확인해 보세요!")
                # 실제 앱에서는 이 답변을 데이터베이스에 저장해야 합니다.
            else:
                st.warning("답변 내용을 입력해 주세요.")
            

# --- 4. 메인 앱 흐름 제어 ---

def main():
    st.set_page_config(
        page_title="세대 간 멘토링 플랫폼",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.sidebar.title("메뉴")
    
    # 연결 프로세스
    if 'connecting' in st.session_state and st.session_state.connecting:
        mentor_name = st.session_state.connect_mentor_name
        st.info(f"🔗 {mentor_name} 멘토와 연결 중입니다. 잠시만 기다려주세요...")
        
        # 가상의 지연 시간
        time.sleep(2) 
        
        st.balloons()
        
        # HTML을 사용하여 새 창/탭으로 이동 (Streamlit 자체로는 직접적인 새 탭 이동이 어려움)
        st.markdown(
            f"""
            <script>
                window.open('{GOOGLE_MEET_URL}', '_blank');
            </script>
            """, 
            unsafe_allow_html=True
        )
        
        st.success(f"✅ {mentor_name} 멘토와의 화상 채팅이 새로운 탭으로 시작되었습니다.")
        
        # 상태 초기화
        st.session_state.connecting = False
        del st.session_state.connect_mentor_name
        st.stop() # 페이지 갱신 중단

    # 페이지 선택
    if not st.session_state.is_registered:
        page = "회원 가입"
    else:
        page = st.sidebar.radio(
            "페이지 이동",
            ["멘토 찾기", "오늘의 질문"],
            index=0
        )
        
        # 사이드바에 사용자 정보 요약
        st.sidebar.divider()
        st.sidebar.markdown(f"**환영합니다, {st.session_state.user_profile.get('name')}님!**")
        st.sidebar.caption(f"나이대: {st.session_state.user_profile.get('age_band')}")


    # 페이지 렌더링
    if page == "회원 가입":
        show_registration_form()
    elif page == "멘토 찾기":
        show_mentor_search_and_connect()
    elif page == "오늘의 질문":
        show_daily_question()

if __name__ == "__main__":
    main()
