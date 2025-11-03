import html  # 파일 상단에 추가: 텍스트 이스케이프용

def show_daily_question():
    st.header("💬 오늘의 질문: 세대 공감 창구")
    st.write("매일 올라오는 질문에 대해 다양한 연령대의 답변을 공유하는 공간입니다.")

    # ⬇️ 새로고침 시 파일 최신 상태로 반영
    st.session_state.daily_answers = load_json_data(ANSWERS_FILE_PATH, st.session_state.get("daily_answers", []))

    # 🔧 f 제거: CSS에 중괄호가 많으므로 f-string 사용 금지
    st.markdown("""
        <style>
        .bubble-container {
            position: relative; 
            background: #ffffff; 
            border-radius: 16px; 
            padding: 18px 16px;
            min-height: 120px; 
            margin: 8px 0 5px 0; 
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.12);
            border: 1px solid #e9ecf3;
        }
        .bubble-info {
            font-size: 13px;
            font-weight: 600;
            color: #445071;
            margin-bottom: 8px;
        }
        .bubble-answer {
            font-size: 15px;
            line-height: 1.6;
            color: #222;
            margin: 0;
        }
        </style>
    """, unsafe_allow_html=True)

    daily_q = "🤔 **'나와 전혀 다른 세대의 삶을 하루만 살아볼 수 있다면, 어떤 세대의 삶을 살아보고 싶은지 이유와 함께 알려주세요!'**"
    st.subheader(daily_q)

    # ===== 답변 그리드 (3열) =====
    if st.session_state.daily_answers:
        cols = st.columns(3)
        current_name = st.session_state.user_profile.get('name')

        for i, ans in enumerate(st.session_state.daily_answers):
            with cols[i % 3]:
                # 안전 이스케이프
                safe_text = html.escape(ans.get('answer', '')).replace("\n", "<br>")
                name = html.escape(ans.get('name', '익명'))
                age  = html.escape(ans.get('age_band', '미등록'))
                is_owner = (name == (current_name or ""))

                st.markdown(
                    f"""
                    <div class="bubble-container">
                        <div class="bubble-info">[{age}] <strong>{name}</strong></div>
                        <p class="bubble-answer">{safe_text}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # ✅ JS 없이 진짜 Streamlit 버튼 사용
                if is_owner:
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("✏️ 수정", key=f"edit_{i}"):
                            st.session_state.editing_index = i
                            st.rerun()
                    with b2:
                        if st.button("🗑️ 삭제", key=f"delete_{i}"):
                            # 삭제 확인 한번 더
                            st.session_state.confirming_delete_index = i
                            st.rerun()

        # 삭제 확인 UI
        if st.session_state.confirming_delete_index != -1:
            idx = st.session_state.confirming_delete_index
            st.warning("정말 삭제하시겠어요? 되돌릴 수 없습니다.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ 예, 삭제"):
                    del st.session_state.daily_answers[idx]
                    save_json_data(st.session_state.daily_answers, ANSWERS_FILE_PATH)
                    st.session_state.confirming_delete_index = -1
                    st.rerun()
            with c2:
                if st.button("❌ 취소"):
                    st.session_state.confirming_delete_index = -1
                    st.rerun()

        # 수정 UI
        if st.session_state.editing_index != -1:
            idx = st.session_state.editing_index
            st.subheader("✏️ 답변 수정")
            with st.form("edit_form"):
                new_text = st.text_area("내용", st.session_state.daily_answers[idx]['answer'], height=140)
                s1, s2 = st.columns(2)
                with s1:
                    save_ok = st.form_submit_button("💾 저장")
                with s2:
                    cancel_ok = st.form_submit_button("취소")
            if save_ok:
                st.session_state.daily_answers[idx]['answer'] = new_text.strip()
                save_json_data(st.session_state.daily_answers, ANSWERS_FILE_PATH)
                st.session_state.editing_index = -1
                st.rerun()
            if cancel_ok:
                st.session_state.editing_index = -1
                st.rerun()
    else:
        st.info("아직 등록된 답변이 없습니다. 첫 번째 답변을 남겨보세요!")

    st.divider()

    # ===== 작성 폼 =====
    st.subheader("나의 답변 작성")
    current_name = st.session_state.user_profile.get('name', '익명')
    current_age = st.session_state.user_profile.get('age_band', '미등록')
    with st.form("answer_form"):
        answer_text = st.text_area("", max_chars=500, height=150, placeholder="여기에 당신의 생각을 자유롭게 적어주세요...")
        submitted = st.form_submit_button("답변 제출", type="primary")
    if submitted:
        if answer_text.strip():
            st.session_state.daily_answers.append({
                "name": current_name,
                "age_band": current_age,
                "answer": answer_text.strip()
            })
            save_json_data(st.session_state.daily_answers, ANSWERS_FILE_PATH)
            st.success("✅ 제출 완료! 목록에 바로 반영됐어요.")
            st.rerun()
        else:
            st.warning("답변 내용을 입력해 주세요.")
