import streamlit as st
import pandas as pd
import random

# --- 데이터 정의 (예시) ---
# 노인 멘토 데이터
mentors_data = {
    'ID': [101, 102, 103, 104],
    '이름': ['김철수', '이영희', '박민수', '정숙자'],
    '나이': [65, 72, 68, 75],
    '전문 분야': ['요리', '목공', '컴퓨터 활용', '뜨개질'],
    '희망 멘티 수': [2, 1, 3, 2],
    '현재 멘티 수': [0, 0, 0, 0]
}
mentors_df = pd.DataFrame(mentors_data)

# 청년 멘티 데이터
mentees_data = {
    'ID': [201, 202, 203, 204, 205, 206],
    '이름': ['최지훈', '한예슬', '강태오', '윤아름', '서준영', '오민지'],
    '나이': [24, 28, 22, 30, 25, 27],
    '희망 분야': ['요리', '컴퓨터 활용', '목공', '뜨개질', '요리', '컴퓨터 활용'],
    '매칭 상태': ['대기', '대기', '대기', '대기', '대기', '대기']
}
mentees_df = pd.DataFrame(mentees_data)

# 세션 상태에 데이터 초기화
if 'mentors_df' not in st.session_state:
    st.session_state.mentors_df = mentors_df.copy()
if 'mentees_df' not in st.session_state:
    st.session_state.mentees_df = mentees_df.copy()
if 'matches' not in st.session_state:
    st.session_state.matches = [] # 매칭 결과 저장 리스트: [(멘토ID, 멘티ID, 분야), ...]

# --- 매칭 로직 함수 ---
def perform_matching():
    """조건에 맞는 멘토-멘티를 매칭하고 결과를 업데이트합니다."""
    
    # 멘토/멘티 DataFrame을 최신 상태로 가져옵니다.
    current_mentors = st.session_state.mentors_df
    current_mentees = st.session_state.mentees_df
    
    new_matches = []
    
    # 매칭 가능한 멘티만 필터링합니다.
    available_mentees = current_mentees[current_mentees['매칭 상태'] == '대기'].copy()
    
    # 멘토를 순회하며 멘티를 매칭합니다.
    for index, mentor in current_mentors.iterrows():
        mentor_id = mentor['ID']
        required_field = mentor['전문 분야']
        available_slots = mentor['희망 멘티 수'] - mentor['현재 멘티 수']
        
        if available_slots > 0:
            # 멘토의 전문 분야와 멘티의 희망 분야가 일치하는 멘티를 찾습니다.
            potential_mentees = available_mentees[available_mentees['희망 분야'] == required_field]
            
            # 무작위로 멘티를 선택하여 매칭합니다. (랜덤성을 부여하여 매칭)
            if not potential_mentees.empty:
                # 필요한 멘티 수와 실제 가능한 멘티 수 중 작은 값을 선택
                match_count = min(available_slots, len(potential_mentees))
                
                # 무작위로 멘티 선택
                mentees_to_match = potential_mentees.sample(n=match_count, random_state=42)
                
                for _, mentee in mentees_to_match.iterrows():
                    mentee_id = mentee['ID']
                    
                    # 매칭 결과 추가
                    new_matches.append((mentor_id, mentee_id, required_field))
                    
                    # DataFrame 업데이트: 멘토 현재 멘티 수 증가
                    current_mentors.loc[current_mentors['ID'] == mentor_id, '현재 멘티 수'] += 1
                    
                    # DataFrame 업데이트: 멘티 매칭 상태 변경
                    current_mentees.loc[current_mentees['ID'] == mentee_id, '매칭 상태'] = '매칭 완료'
                    
                    # 매칭된 멘티는 다음 멘토에게는 매칭되지 않도록 available_mentees에서 제거
                    available_mentees = available_mentees[available_mentees['ID'] != mentee_id]

    st.session_state.mentors_df = current_mentors
    st.session_state.mentees_df = current_mentees
    st.session_state.matches.extend(new_matches)
    
    return len(new_matches)

# --- Streamlit UI 구성 ---
st.title("👵👴 세대 간 멘토-멘티 매칭 플랫폼 🧑‍💻")
st.caption("노인 멘토와 청년 멘티를 위한 매칭 시뮬레이션")

st.markdown("""
<style>
.stButton>button {
    font-size: 1.2rem;
    padding: 10px 20px;
}
</style>
""", unsafe_allow_html=True)


## 📊 현황 대시보드

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("총 멘토 수", len(st.session_state.mentors_df))

with col2:
    st.metric("총 멘티 수", len(st.session_state.mentees_df))

with col3:
    st.metric("총 매칭 건수", len(st.session_state.matches))

st.divider()

## 🛠️ 매칭 기능

st.header("멘토-멘티 매칭")
st.write("아래 버튼을 누르면, **전문 분야**와 **희망 분야**가 일치하고 **멘토의 여유 슬롯**이 있는 경우에 한하여 매칭을 시도합니다.")

if st.button("🔄 매칭 실행하기"):
    matched_count = perform_matching()
    if matched_count > 0:
        st.success(f"✅ 새로운 매칭 **{matched_count}건**이 완료되었습니다!")
    else:
        st.info("⚠️ 현재 조건에서 추가로 매칭 가능한 건이 없습니다.")

st.divider()

## 📝 데이터 현황

st.header("데이터 현황")

tab1, tab2, tab3 = st.tabs(["노인 멘토 목록", "청년 멘티 목록", "매칭 결과"])

with tab1:
    st.subheader("노인 멘토 목록")
    st.dataframe(st.session_state.mentors_df, use_container_width=True)
    
with tab2:
    st.subheader("청년 멘티 목록")
    st.dataframe(st.session_state.mentees_df, use_container_width=True)

with tab3:
    st.subheader("매칭 결과")
    if st.session_state.matches:
        # 매칭 결과를 DataFrame으로 변환하여 표시
        matches_df = pd.DataFrame(st.session_state.matches, columns=['멘토 ID', '멘티 ID', '매칭 분야'])
        
        # 멘토/멘티 이름을 매핑하여 가독성을 높입니다.
        mentor_map = st.session_state.mentors_df.set_index('ID')['이름'].to_dict()
        mentee_map = st.session_state.mentees_df.set_index('ID')['이름'].to_dict()
        
        matches_df['멘토 이름'] = matches_df['멘토 ID'].map(mentor_map)
        matches_df['멘티 이름'] = matches_df['멘티 ID'].map(mentee_map)
        
        # 표시 순서 조정
        display_df = matches_df[['멘토 이름', '멘티 이름', '매칭 분야', '멘토 ID', '멘티 ID']]
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("아직 매칭 결과가 없습니다. '매칭 실행하기' 버튼을 눌러주세요.")
