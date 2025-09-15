import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import io

# ----------------------------------------------------
# 1. 멘토 데이터 정의
# ----------------------------------------------------
mentor_data = """
id,name,age,experience,interests,personality
1,김현수,72,전직 경영인,"스타트업,경영,골프",진지함,경험중심,사려깊음
2,박영희,68,전직 교사,"상담,심리,독서",따뜻함,경청,격려형
3,이민호,75,전직 엔지니어,"기술,취미,여행",유머러스,친절함,자유분방
4,최은정,65,전직 요리사,"요리,음식,일상,정원",섬세함,유쾌함,포용력
5,강우진,70,전직 기자,"글쓰기,사회,역사",논리적,사색가,호기심
"""
mentor_df = pd.read_csv(io.StringIO(mentor_data))

# ----------------------------------------------------
# 2. 유틸리티 함수
# ----------------------------------------------------
def preprocess_data(df, columns):
    """텍스트 데이터를 매칭에 사용하기 위해 전처리합니다."""
    df['combined_features'] = df[columns].apply(lambda x: ','.join(x.astype(str).str.strip()), axis=1)
    return df

def find_best_match(mentee_profile, mentor_df):
    """멘티 프로필과 가장 유사한 멘토를 찾습니다."""
    mentee_text = f"{mentee_profile['interests']},{mentee_profile['personality']}"

    # TF-IDF 벡터화
    vectorizer = TfidfVectorizer()
    all_texts = mentor_df['combined_features'].tolist() + [mentee_text]
    tfidf_matrix = vectorizer.fit_transform(all_texts)
    
    mentee_vector = tfidf_matrix[-1]
    mentor_vectors = tfidf_matrix[:-1]
    
    # 코사인 유사도 계산
    cosine_sim = cosine_similarity(mentee_vector, mentor_vectors).flatten()
    
    # 유사도가 높은 순으로 정렬하여 추천
    top_matches_indices = cosine_sim.argsort()[::-1]
    top_matches = mentor_df.iloc[top_matches_indices]
    
    return top_matches.head(3)

def get_gpt_analysis(user_input):
    """
    (실제로는 OpenAI API를 호출하는 함수)
    사용자의 답변을 GPT에게 분석 요청하여 키워드와 성향을 추출하는 역할.
    현재는 예시 더미 데이터를 반환합니다.
    """
    if "코딩" in user_input or "개발" in user_input:
        return {"interests": "코딩,개발,기술", "personality": "진지함,논리적"}
    elif "여행" in user_input or "사진" in user_input:
        return {"interests": "여행,사진,일상", "personality": "자유분방,사려깊음"}
    elif "요리" in user_input or "음식" in user_input:
        return {"interests": "요리,음식,일상", "personality": "섬세함,포용력"}
    else:
        return {"interests": "일상,소통,취미", "personality": "보통,친절함"}

# ----------------------------------------------------
# 3. Streamlit 앱 UI 및 챗봇 로직
# ----------------------------------------------------
st.set_page_config(page_title="세대 연결 멘토링 플랫폼", page_icon="🤝")

st.title("🤝 세대 연결 멘토링 챗봇")
st.markdown("당신의 이야기를 들려주시면, 가장 잘 맞는 시니어 멘토님을 찾아드릴게요.")

# 세션 상태 초기화
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    st.session_state.step = "start"
    st.session_state.mentee_data = {}
    st.session_state.chat_history.append({"role": "bot", "text": "안녕하세요! 멘토링을 통해 어떤 것을 얻고 싶으신가요?"})

# 챗봇 대화 출력
for chat in st.session_state.chat_history:
    with st.chat_message(chat["role"]):
        st.write(chat["text"])

# 챗봇 대화 흐름 제어
if st.session_state.step == "start":
    if user_input := st.chat_input("하고 싶은 말을 입력해주세요."):
        st.session_state.chat_history.append({"role": "user", "text": user_input})
        st.session_state.chat_history.append({"role": "bot", "text": "네, 좋은 목표네요! 혹시 평소에 관심 있는 분야나 취미는 무엇인가요?"})
        st.session_state.step = "interests"
        st.experimental_rerun()

elif st.session_state.step == "interests":
    if user_input := st.chat_input("관심사/취미를 자유롭게 말씀해주세요."):
        st.session_state.chat_history.append({"role": "user", "text": user_input})
        
        # GPT 분석 (더미)
        analysis_result = get_gpt_analysis(user_input)
        st.session_state.mentee_data = analysis_result

        st.session_state.chat_history.append({"role": "bot", "text": "알겠습니다. 이제 당신에게 맞는 멘토님을 찾아볼게요! 잠시만 기다려주세요..."})
        st.session_state.step = "matching"
        st.experimental_rerun()

elif st.session_state.step == "matching":
    # 멘토 데이터 전처리
    preprocessed_mentor_df = preprocess_data(mentor_df, ['interests', 'personality', 'experience'])
    top_matches = find_best_match(st.session_state.mentee_data, preprocessed_mentor_df)
    
    st.session_state.chat_history.append({"role": "bot", "text": "✨ 가장 잘 맞는 멘토님들을 찾았어요!"})
    
    # 추천 멘토 정보 출력
    for index, mentor in top_matches.iterrows():
        st.session_state.chat_history.append({"role": "bot", "text": 
            f"""
            ---
            **멘토님 이름:** {mentor['name']} (나이: {mentor['age']}세)
            **경력:** {mentor['experience']}
            **관심사:** {mentor['interests']}
            **성향:** {mentor['personality']}
            ---
            """
        })
    st.session_state.chat_history.append({"role": "bot", "text": "매칭이 완료되었습니다. 추천된 멘토님들과 연결을 시도해 보세요!"})
    st.session_state.step = "complete"
    st.experimental_rerun()
