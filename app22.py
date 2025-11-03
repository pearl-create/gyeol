def show_daily_question():
    # ----- 0) 자동 로그인 훅 (쿼리파라미터 → 세션 로그인) -----
    # 새로고침(F5) 시 세션이 초기화되어도, localStorage에 저장된 이름으로 자동 로그인되도록 함.
    # ?auto_login=이름 이 붙어 있으면 해당 이름으로 로그인 처리
    qp = st.query_params if hasattr(st, "query_params") else {}
    auto_name = None
    if isinstance(qp, dict) and "auto_login" in qp:
        auto_name = qp.get("auto_login")
        # Streamlit 버전에 따라 list/str일 수 있으니 정규화
        if isinstance(auto_name, list):
            auto_name = auto_name[0] if auto_name else None

    if (not st.session_state.get("logged_in")) and auto_name:
        if auto_name in st.session_state.all_users:
            st.session_state.user_profile = st.session_state.all_users[auto_name]
            st.session_state.logged_in = True
            st.rerun()

    # ----- 1) 배경/말풍선 CSS & JS (페이지 내에서만 적용) -----
    st.markdown("""
        <style>
            /* 전체 배경에 그라디언트 + 은은한 애니메이션 */
            html, body, [data-testid="stAppViewContainer"] {
                background: linear-gradient(120deg, #1f1c2c, #928DAB, #355C7D, #6C5B7B, #C06C84);
                background-size: 400% 400%;
                animation: bgShift 16s ease infinite;
            }
            @keyframes bgShift {
                0% { background-position: 0% 50%; }
                50% { background-position: 100% 50%; }
                100% { background-position: 0% 50%; }
            }

            /* 말풍선 공통 스타일 */
            .floating-bubble {
                position: relative;
                display: inline-block;
                max-width: 90%;
                padding: 14px 18px;
                margin: 12px 8px;
                border-radius: 18px;
                background: rgba(255,255,255,0.15);
                backdrop-filter: blur(6px);
                -webkit-backdrop-filter: blur(6px);
                color: #F7F7FF;
                box-shadow: 0 10px 25px rgba(0,0,0,0.15);
                border: 1px solid rgba(255,255,255,0.25);
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

            /* 말풍선 둥둥 애니메이션(세부 속성은 inline-style에서 각 풍선별로 다르게) */
            @keyframes floatUpDown {
                0%   { transform: translateY(0px); }
                50%  { transform: translateY(-12px); }
                100% { transform: translateY(0px); }
            }

            /* 이름/나이대 라벨 */
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

            /* 섹션 카드 느낌 */
            .dq-card {
                background: rgba(0,0,0,0.25);
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 16px;
                padding: 20px;
                margin-top: 6px;
                box-shadow: 0 6px 18px rgba(0,0,0,0.25);
            }
            .dq-title {
                color: #fff;
                text-shadow: 0 1px 8px rgba(0,0,0,0.3);
            }
        </style>

        <script>
        // 초기 1회: localStorage에 저장된 이름으로 auto_login 쿼리파라미터 부착
        (function(){
            try {
                const params = new URLSearchParams(window.location.search);
                const hasAuto = params.has('auto_login');
                const stored = localStorage.getItem('gyeol_user_name');
                if (!hasAuto && stored) {
                    // 쿼리파라미터에 auto_login 추가하고 한 번만 새로고침
                    params.set('auto_login', stored);
                    const newUrl = window.location.pathname + "?" + params.toString();
                    window.history.replaceState({}, "", newUrl);
                    // Streamlit이 쿼리 변경을 감지해서 rerun
                }
            } catch(e) {}
        })();
        </script>
    """, unsafe_allow_html=True)

    st.header("💬 오늘의 질문: 세대 공감 창구", anchor=False)
    st.markdown('<div class="dq-card">', unsafe_allow_html=True)
    st.write("매일 올라오는 질문에 대해 다양한 연령대의 답변을 공유하는 공간입니다.")
    daily_q = "🤔 **'나와 전혀 다른 세대의 삶을 하루만 살아볼 수 있다면, 어떤 세대의 삶을 살아보고 싶은지 이유와 함께 알려주세요!'**"
    st.subheader(daily_q)
    st.markdown('</div>', unsafe_allow_html=True)

    # ----- 2) 답변 리스트 (말풍선으로 둥둥) -----
    if st.session_state.daily_answers:
        sorted_answers = sorted(st.session_state.daily_answers, key=lambda x: x['name'], reverse=False)

        # 말풍선의 개별 애니메이션 속성(지연/기간/수평오프셋)을 조금씩 다르게
        for i, ans in enumerate(sorted_answers):
            # 풍선 개별 애니메이션 파라미터
            delay = (i % 5) * 0.25          # 0, 0.25, 0.5, 0.75, 1.0s
            duration = 4.0 + (i % 4) * 0.6  # 4.0, 4.6, 5.2, 5.8s
            xshift = (i % 6) * 6 - 12       # -12, -6, 0, 6, 12, 18 px

            header = f"[{ans.get('age_band','-')}] {ans.get('name','익명')}"
            body = ans.get('answer', '')

            html = f"""
            <div class="floating-bubble"
                 style="animation: floatUpDown {duration}s ease-in-out {delay}s infinite;
                        transform: translateX({xshift}px);">
                <div class="bubble-header">{header}</div>
                <div class="bubble-body">{body}</div>
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)
    else:
        st.info("아직 등록된 답변이 없습니다. 첫 번째 답변을 남겨주세요!")

    st.divider()

    # ----- 3) 답변 작성 폼 -----
    st.subheader("나의 답변 작성하기", anchor=False)
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
                # 파일에 즉시 반영
                save_json_data(st.session_state.daily_answers, ANSWERS_FILE_PATH)

                # 브라우저에 사용자 이름 저장 → 새로고침 시 자동 로그인 유도
                st.markdown(f"""
                    <script>
                        try {{
                            localStorage.setItem('gyeol_user_name', {json.dumps(current_name)});
                        }} catch(e) {{}}
                    </script>
                """, unsafe_allow_html=True)

                st.success("답변이 제출되었습니다. 새로고침(F5)해도 바로 반영된 답변을 볼 수 있어요!")
                # 서버 사이드 즉시 반영도 위해 rerun
                st.rerun()
            else:
                st.warning("답변 내용을 입력해 주세요.")
