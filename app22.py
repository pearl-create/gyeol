def show_daily_question():
    # --- 0) 스타일(CSS)만 사용: 전역이 아닌 래퍼 div에만 적용 ---
    st.markdown("""
        <style>
            /* 섹션 배경을 감싸는 래퍼 */
            #dq-wrap {
                position: relative;
                padding: 16px;
                border-radius: 16px;
                overflow: hidden;
            }
            #dq-wrap::before {
                content: "";
                position: absolute;
                inset: 0;
                background: linear-gradient(120deg, #1f1c2c, #928DAB, #355C7D, #6C5B7B, #C06C84);
                background-size: 400% 400%;
                animation: dqBgShift 16s ease infinite;
                z-index: 0;
                opacity: 0.35;
            }
            @keyframes dqBgShift {
                0% { background-position: 0% 50%; }
                50% { background-position: 100% 50%; }
                100% { background-position: 0% 50%; }
            }

            .dq-card {
                position: relative;
                z-index: 1;
                background: rgba(0,0,0,0.35);
                border: 1px solid rgba(255,255,255,0.15);
                border-radius: 16px;
                padding: 20px;
                margin-bottom: 10px;
                box-shadow: 0 6px 18px rgba(0,0,0,0.25);
            }
            .dq-title {
                color: #fff;
                text-shadow: 0 1px 8px rgba(0,0,0,0.3);
            }

            .bubble-box {
                position: relative;
                z-index: 1;
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                align-items: flex-start;
            }
            .floating-bubble {
                position: relative;
                display: inline-block;
                max-width: min(90%, 560px);
                padding: 14px 18px;
                border-radius: 18px;
                background: rgba(255,255,255,0.15);
                backdrop-filter: blur(6px);
                -webkit-backdrop-filter: blur(6px);
                color: #F7F7FF;
                box-shadow: 0 10px 25px rgba(0,0,0,0.15);
                border: 1px solid rgba(255,255,255,0.25);
                animation-name: dqFloatY;
                animation-timing-function: ease-in-out;
                animation-iteration-count: infinite;
            }
            .floating-bubble:after {
                content: "";
                position: absolute;
                bottom: -10px; left: 26px;
                border-width: 10px 10px 0 10px;
                border-style: solid;
                border-color: rgba(255,255,255,0.15) transparent transparent transparent;
                filter: drop-shadow(0 -2px 2px rgba(0,0,0,0.05));
            }
            .bubble-header {
                font-weight: 700;
                font-size: 0.95rem;
                opacity: 0.95;
                margin-bottom: 6px;
            }
            .bubble-body {
                white-space: pre-wrap;
                line-height: 1.6;
                font-size: 0.95rem;
            }
            @keyframes dqFloatY {
                0%   { transform: translateY(0px); }
                50%  { transform: translateY(-12px); }
                100% { transform: translateY(0px); }
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div id="dq-wrap">', unsafe_allow_html=True)

    st.header("💬 오늘의 질문: 세대 공감 창구")
    st.markdown('<div class="dq-card">', unsafe_allow_html=True)
    st.write("매일 올라오는 질문에 대해 다양한 연령대의 답변을 공유하는 공간입니다.")
    daily_q = "🤔 **'나와 전혀 다른 세대의 삶을 하루만 살아볼 수 있다면, 어떤 세대의 삶을 살아보고 싶은지 이유와 함께 알려주세요!'**"
    st.subheader(daily_q)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 1) 답변 리스트: 말풍선(순수 CSS) ---
    if st.session_state.daily_answers:
        sorted_answers = sorted(st.session_state.daily_answers, key=lambda x: x['name'], reverse=False)
        st.markdown('<div class="bubble-box">', unsafe_allow_html=True)

        for i, ans in enumerate(sorted_answers):
            # 풍선마다 살짝 다른 리듬/지연/수평 오프셋
            delay = (i % 5) * 0.25          # 0, 0.25, 0.5, 0.75, 1.0
            duration = 4.0 + (i % 4) * 0.6  # 4.0, 4.6, 5.2, 5.8
            xshift = (i % 6) * 6 - 12       # -12, -6, 0, 6, 12, 18

            header = f"[{ans.get('age_band','-')}] {ans.get('name','익명')}"
            body = ans.get('answer', '')

            html = f"""
            <div class="floating-bubble"
                 style="animation-duration:{duration}s; animation-delay:{delay}s; transform: translateX({xshift}px);">
                <div class="bubble-header">{header}</div>
                <div class="bubble-body">{body}</div>
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("아직 등록된 답변이 없습니다. 첫 번째 답변을 남겨주세요!")

    st.divider()

    # --- 2) 답변 작성 폼: 제출 즉시 파일 저장 + rerun 로 즉시 반영 ---
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
                save_json_data(st.session_state.daily_answers, ANSWERS_FILE_PATH)
                st.success("답변이 제출되었습니다. 새로고침 없이도 바로 반영됐어요!")
                st.rerun()
            else:
                st.warning("답변 내용을 입력해 주세요.")

    st.markdown('</div>', unsafe_allow_html=True)
