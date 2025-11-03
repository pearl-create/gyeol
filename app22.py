def show_daily_question():
    st.header("💬 오늘의 질문: 세대 공감 창구")
    st.write("매일 올라오는 질문에 대해 다양한 연령대의 답변을 공유하는 공간입니다.")

    daily_q = "🤔 **'나와 전혀 다른 세대의 삶을 하루만 살아볼 수 있다면, 어떤 세대의 삶을 살아보고 싶은지 이유와 함께 알려주세요!'**"
    st.subheader(daily_q)

    # 항상 디스크 최신 동기화
    refresh_answers_from_disk()

    # ====== 말풍선 + 그리드 CSS ======
    st.markdown("""
    <style>
      /* 전체 레이아웃: 반응형 그리드 */
      .bubble-grid{
        display:grid;
        grid-template-columns:repeat(auto-fill, minmax(280px, 1fr));
        gap:16px;
        align-items:start;
      }
      /* 말풍선 기본 */
      .bubble-card{
        position:relative;
        background:#ffffff;
        border:1px solid #e6e8ef;
        border-radius:22px;
        padding:14px 16px 12px 16px;
        box-shadow:0 6px 16px rgba(20,22,30,0.06);
        transition:transform .05s ease;
        min-height:80px;
      }
      .bubble-card:hover{ transform:translateY(-1px); }
      /* 말풍선 꼬리 (왼쪽 아래) */
      .bubble-card:after{
        content:"";
        position:absolute;
        left:26px;
        bottom:-10px;
        width:0;height:0;
        border:12px solid transparent;
        border-top-color:#ffffff;  /* 말풍선 배경색 */
        border-bottom:0;
        filter:drop-shadow(0 -2px 2px rgba(20,22,30,0.05));
      }
      /* 본인 배경 살짝 차등 */
      .bubble-owner{
        background:#f7fbff;
        border-color:#cfe3ff;
      }
      .bubble-owner:after{ border-top-color:#f7fbff; }

      .meta{
        font-size:12px;color:#5a5f7a;margin-bottom:6px;
        display:flex;gap:8px;align-items:center;flex-wrap:wrap;
      }
      .owner-badge{
        font-size:11px;padding:2px 6px;border-radius:8px;
        background:#eefcf1;color:#147d3f;border:1px solid #c8f3d2;
      }
      .bubble-text{ line-height:1.65; word-break:break-word; }
      .bubble-actions{ margin-top:8px; display:flex; gap:8px; }
      .bubble-actions > div{ flex:0 0 auto; }
    </style>
    """, unsafe_allow_html=True)

    # 로그인 사용자
    current_name = st.session_state.user_profile.get('name', '')
    current_age = st.session_state.user_profile.get('age_band', '미등록')

    # ===== 작성 폼 =====
    st.divider()
    st.subheader("나의 답변 작성하기")
    if st.session_state.editing_answer_id is None:
        with st.form("answer_form"):
            answer_text = st.text_area("질문에 대한 당신의 생각을 적어주세요.", max_chars=500, height=150)
            submitted = st.form_submit_button("답변 제출")

        if submitted:
            if not current_name:
                st.warning("로그인 후 작성할 수 있습니다.")
            elif answer_text.strip():
                new_answer = {
                    "id": int(time.time() * 1000) + random.randint(0, 999),
                    "name": current_name,
                    "age_band": current_age,
                    "answer": answer_text.strip()
                }
                upsert_answer(new_answer)
                st.success("답변이 제출되었습니다.")
                st.rerun()
            else:
                st.warning("답변 내용을 입력해 주세요.")

    # ===== 리스트 (처음부터 펼쳐짐 + 그리드) =====
    st.divider()
    st.subheader(f"📬 누적 답변 ({len(st.session_state.daily_answers)}명)")
    if not st.session_state.daily_answers:
        st.info("아직 등록된 답변이 없습니다. 첫 번째 답변을 남겨보세요!")
        return

    # 정렬: 이름순 (최신순 원하면 id 기준 reverse=True로 변경 가능)
    answers_sorted = sorted(st.session_state.daily_answers, key=lambda x: x.get('name', ''))

    # 그리드 시작
    st.markdown('<div class="bubble-grid">', unsafe_allow_html=True)

    for a in answers_sorted:
        a_id = a.get('id')
        a_name = a.get('name', '익명')
        a_age = a.get('age_band', '미등록')
        a_text = a.get('answer', '')
        is_owner = (current_name and a_name == current_name)
        editing_this = (st.session_state.editing_answer_id == a_id)

        # 카드 열기
        card_cls = "bubble-card bubble-owner" if is_owner else "bubble-card"
        st.markdown(f'<div class="{card_cls}">', unsafe_allow_html=True)

        # 메타
        owner_badge = '<span class="owner-badge">내 답변</span>' if is_owner else ''
        st.markdown(
            f'<div class="meta">[{html.escape(str(a_age))}] '
            f'<strong>{html.escape(str(a_name))}</strong> {owner_badge}</div>',
            unsafe_allow_html=True
        )

        if editing_this:
            # 수정폼
            with st.form(f"edit_form_{a_id}"):
                new_text = st.text_area("내용 수정", a_text, max_chars=500, height=140, key=f"edit_text_{a_id}")
                c1, c2 = st.columns(2)
                with c1:
                    ok = st.form_submit_button("💾 저장")
                with c2:
                    cancel = st.form_submit_button("취소")
            if ok:
                if new_text.strip():
                    a['answer'] = new_text.strip()
                    upsert_answer(a)
                    st.session_state.editing_answer_id = None
                    st.success("수정되었습니다.")
                    st.rerun()
                else:
                    st.warning("내용이 비어 있습니다.")
            if cancel:
                st.session_state.editing_answer_id = None
                st.rerun()
        else:
            # 본문
            safe_text = html.escape(a_text).replace("\n", "<br>")
            st.markdown(f'<div class="bubble-text">{safe_text}</div>', unsafe_allow_html=True)

            # 본인만 버튼
            if is_owner:
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✏️ 수정", key=f"btn_edit_{a_id}"):
                        st.session_state.editing_answer_id = a_id
                        st.rerun()
                with c2:
                    if st.button("🗑️ 삭제", key=f"btn_del_{a_id}"):
                        delete_answer_by_id(a_id)
                        st.success("삭제되었습니다.")
                        st.rerun()

        # 카드 닫기
        st.markdown('</div>', unsafe_allow_html=True)

    # 그리드 닫기
    st.markdown('</div>', unsafe_allow_html=True)
