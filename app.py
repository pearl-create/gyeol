import streamlit as st
import pandas as pd
import random

# --- 1. 데이터 로드 및 정의 ---

# 멘토 데이터 로드 (사용자가 제공한 CSV 파일 활용)
# 파일 이름을 직접 사용합니다. Streamlit Cloud나 Jupyter 환경이 아닌 경우,
# 해당 파일이 app.py와 같은 폴더에 있어야 합니다.
try:
    mentor_csv_path = "멘토더미.csv"
    mentors_df = pd.read_csv(mentor_csv_path)
    
    # 추천 로직에 사용할 주요 컬럼 이름을 명확히 합니다.
    # mentor_df의 컬럼: name, gender, age_band, current_occupation, occupation_major, interests, purpose, topic_prefs, communication_style, intro
    
    # 예시로 사용할 멘티 데이터
    mentees_data = {
        'ID': [201, 202, 203],
        '이름': ['청년 멘티 A', '청년 멘티 B', '청년 멘티 C'],
        '희망 분야': ['연구개발/ IT', '예술/디자인', '일반 사무'], # occupation_major와 매칭
        '희망 주제': ['IT·테크', '예술·문화', '진로·직업'], # topic_prefs와 매칭
        '희망 대화 스타일': ['효율추구형', '댕댕이형', '연두부형'] # communication_style와 매칭
    }
    mentees_df = pd.DataFrame(mentees_data)

except FileNotFoundError:
    st.error(f"Error: 멘토 데이터 파일 '{mentor_csv_path}'을(를) 찾을 수 없습니다. 파일 경로를 확인해 주세요.")
    st.stop()
except Exception as e:
    st.error(f"멘토 데이터 로드 중 오류 발생: {e}")
    st.stop()


# 세션 상태에 데이터 초기화
if 'mentors_df' not in st.session_state:
    # 추천 로직을 위한 전처리: topic_prefs와 communication_style은 여러 값이 있을 수 있으므로
    # 이후 매칭 로직에서 이를 고려해야 합니다.
    st.session_state.mentors_df = mentors_df.copy()
if 'mentees_df' not in st.session_state:
    st.session_state.mentees_df = mentees_df.copy()
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = [] # 추천 결과 저장

# --- 2. 멘토 추천 로직 함수 ---

def recommend_mentors(field, topic, style):
    """
    멘티의 희망 조건에 따라 멘토를 점수 기반으로 추천합니다.
    - 점수 부여 기준: 분야(3점) > 주제(2점) > 대화 스타일(1점)
    """
    
    mentors = st.session_state.mentors_df.copy()
    mentors['score'] = 0
    
    # 1. 희망 분야 (occupation_major) 매칭: 3점
    mentors['score'] += mentors['occupation_major'].apply(lambda x: 3 if x == field else 0)
    
    # 2. 희망 주제 (topic_prefs) 매칭: 2점
    # topic_prefs는 콤마로 구분된 여러 값일 수 있습니다.
    mentors['score'] += mentors['topic_prefs'].astype(str).apply(
        lambda x: 2 if topic in x else 0
    )
    
    # 3. 희망 대화 스타일 (communication_style) 매칭: 1점
    mentors['score'] += mentors['communication_style'].apply(lambda x: 1 if x == style else 0)
    
    # 점수가 0점 이상인 멘토만 필터링하고 점수 순으로 정렬
    recommended_mentors = mentors[mentors['score'] > 0].sort_values(by='score', ascending=False)
    
    # 상위 5명 (또는 그 이하) 추천
    return recommended_mentors.head(5).reset_index(drop=True)


# --- 3. Streamlit UI 구성 ---

st.title("👵👴 세대 간 멘토 추천 플랫폼 🧑‍💻")
st.caption("청년 멘티의 조건에 가장 적합한 노인 멘토를 추천합니다.")

## 🛠️ 멘티 조건 검색 및 멘토 추천

st.header("멘토 추천받기")
st.write("청년 멘티가 희망하는 조건을 선택하여 적합한 멘토를 찾아보세요.")

# 멘토 데이터에서 사용 가능한 옵션 추출
available_fields = sorted(mentors_df['occupation_major'].unique().tolist())
# topic_prefs는 여러 값이 있으므로, 모든 유니크한 값을 추출
all_topics = set()
mentors_df['topic_prefs'].astype(str).str.split('[,;]').apply(lambda x: all_topics.update([t.strip() for t in x if t.strip()]))
available_topics = sorted([t for t in all_topics if t])
available_styles = sorted(mentors_df['communication_style'].unique().tolist())


with st.form("mentor_recommendation_form"):
    
    col_f, col_t, col_s = st.columns(3)
    
    with col_f:
        selected_field = st.selectbox(
            "💼 1. 희망 멘토 분야 (가장 중요)",
            options=['선택 안 함'] + available_fields
        )
    
    with col_t:
        selected_topic = st.selectbox(
            "💬 2. 희망 대화 주제",
            options=['선택 안 함'] + available_topics
        )
        
    with col_s:
        selected_style = st.selectbox(
            "🗣️ 3. 희망 대화 스타일",
            options=['선택 안 함'] + available_styles
        )

    submitted = st.form_submit_button("🌟 추천 멘토 찾기")
    
    if submitted:
        # '선택 안 함'을 제외하고 실제 값만 전달
        search_field = selected_field if selected_field != '선택 안 함' else ''
        search_topic = selected_topic if selected_topic != '선택 안 함' else ''
        search_style = selected_style if selected_style != '선택 안 함' else ''
        
        if not search_field and not search_topic and not search_style:
            st.warning("⚠️ 멘토 추천을 위해 최소한 하나의 조건을 선택해 주세요.")
        else:
            with st.spinner("최적의 멘토를 찾는 중..."):
                recommendation_results = recommend_mentors(search_field, search_topic, search_style)
                st.session_state.recommendations = recommendation_results
            
            if not recommendation_results.empty:
                st.success(f"✅ 조건에 가장 적합한 멘토 **{len(recommendation_results)}명**을 찾았습니다!")
            else:
                st.info("⚠️ 현재 선택하신 조건에 맞는 멘토가 없습니다. 조건을 바꿔서 다시 검색해 보세요.")

st.divider()

## 📝 추천 결과 표시

st.header("추천 멘토 리스트")

if st.session_state.recommendations is not None and not st.session_state.recommendations.empty:
    
    recommended_df = st.session_state.recommendations.rename(columns={
        'name': '멘토 이름',
        'age_band': '연령대',
        'occupation_major': '전문 분야',
        'topic_prefs': '주요 관심 주제',
        'communication_style': '대화 스타일',
        'intro': '멘토 소개글',
        'score': '추천 점수'
    })
    
    # 보여줄 컬럼 선택 및 순서 조정
    display_cols = [
        '멘토 이름', '추천 점수', '전문 분야', '주요 관심 주제', 
        '대화 스타일', '연령대', '멘토 소개글'
    ]
    
    # 멘토 카드 형식으로 표시
    for index, row in recommended_df.iterrows():
        st.subheader(f"{index + 1}. {row['멘토 이름']} (추천 점수: {int(row['추천 점수'])}점)")
        
        # 메트릭스 형태로 핵심 정보 요약
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("전문 분야", row['전문 분야'])
        with col_m2:
            st.metric("대화 스타일", row['대화 스타일'])
        with col_m3:
            st.metric("연령대", row['연령대'])
            
        st.markdown(f"**주요 관심 주제:** `{row['주요 관심 주제']}`")
        st.markdown(f"**멘토 소개:** _{row['멘토 소개글']}_")
        st.markdown("---")
        
else:
    st.info("조건을 선택하고 '🌟 추천 멘토 찾기' 버튼을 눌러 추천을 시작해 주세요.")
