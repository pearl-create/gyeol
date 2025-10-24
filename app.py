# show_daily_question 함수 수정
def show_daily_question():
    """오늘의 질문 게시판을 표시하고, 답변을 누적하여 보여줍니다."""
    st.header("💬 오늘의 질문: 세대 공감 창구")
    st.write("매일 올라오는 질문에 대해 다양한 연령대의 답변을 공유하는 공간입니다.")
    
    daily_q = "🤔 **'내가 만약 20대로 돌아간다면, 지금의 나에게 가장 해주고 싶은 조언은 무엇인가요?'**"
    st.subheader(daily_q)
    
    # --- 답변 리스트 (세션 상태에 누적된 답변 사용) ---
    if st.session_state.daily_answers:
        # 🌟 수정된 부분: key=lambda x: 1, reverse=True로 깔끔하게 수정
        sorted_answers = sorted(st.session_state.daily_answers, key=lambda x: 1, reverse=True) 
        
        for ans in sorted_answers:
            with st.expander(f"[{ans['age_band']}] **{ans['name']}**님의 답변"):
                st.write(ans['answer'])
            
    st.divider()
    
    # --- 답변 작성 폼 ---
    st.subheader("나의 답변 작성하기")
    current_name = st.session_state.user_profile.get('name', '익명')
    current_age = st.session_state.user_profile.get('age_band', '미등록')
    
    with st.form("answer_form"):
        answer_text = st.text_area("질문에 대한 당신의 생각을 적어주세요.", max_chars=500, height=150)
        submitted = st.form_submit_button("답변 제출")
        
        if submitted:
            if answer_text:
                new_answer = {
                    "name": current_name,
                    "age_band": current_age,
                    "answer": answer_text
                }
                st.session_state.daily_answers.append(new_answer)
                
                st.success("답변이 제출되었습니다. 페이지를 새로고침하면(R 키) 누적된 답변을 볼 수 있습니다.")
                st.rerun() 
            else:
                st.warning("답변 내용을 입력해 주세요.")
