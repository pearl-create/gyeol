import streamlit as st
import time
from datetime import date

# --- 1. 기본 설정 및 데이터 초기화 (Session State) ---

def initialize_session_state():
    """앱의 상태를 초기화합니다."""
    # 로그인 상태
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'current_name' not in st.session_state:
        st.session_state.current_name = None
    if 'current_age_band' not in st.session_state:
        st.session_state.current_age_band = None
        
    # 수정 모드 상태
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    if 'edit_answer_id' not in st.session_state:
        st.session_state.edit_answer_id = None
    if 'edit_answer_text' not in st.session_state:
        st.session_state.edit_answer_text = None

    # 질문/답변 데이터 (더미 데이터)
    if 'daily_question' not in st.session_state:
        st.session_state.daily_question = "당신의 20대 시절, 가장 큰 고민은 무엇이었나요?"
    if 'daily_answers' not in st.session_state:
        st.session_state.daily_answers = [
            {'id': 1, 'name': '김철수', 'age_band': '30대', 'answer': '회사의 복지나 연봉에 만족하지 못했어요. 이직만이 답일까 고민했습니다.', 'timestamp': time.time() - 3600},
            {'id': 2, 'name': '이지영', 'age_band': '40대', 'answer': '육아와 커리어 사이에서 균형을 잡는 것이 너무 힘들었습니다.', 'timestamp': time.time() - 1800},
            {'id': 3, 'name': '관리자', 'age_band': '20대', 'answer': '졸업 후 무엇을 해야 할지, 진로에 대한 고민이 가장 컸습니다.', 'timestamp': time.time()},
        ]

def delete_answer(answer_id):
    """답변을 삭제하고 상태를 업데이트합니다."""
    st.session_state.daily_answers = [
        ans for ans in st.session_state.daily_answers if ans['id'] != answer_id
    ]
    st.success("답변이 삭제되었습니다.")

# --- 2. CSS 스타일 정의 및 UI 버그 수정 ---
def load_css():
    """Streamlit UI 커스터마이징 및 버그 해결 CSS를 로드합니다."""
    st.markdown("""
        <style>
        /* [핵심 수정] 숨겨진 Streamlit 버튼을 강제로 숨김 (UX 버그 해결) */
        button[kind="secondary"],
        button[kind="secondary"][disabled] {
            display: none !important;
        }

        /* 답변 버블 스타일 */
        .bubble-container {
            border: 1px solid #ddd;
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 10px;
            background-color: #f9f9f9;
        }
        .bubble-info {
            font-size: 0.9em;
            color: #555;
            margin-bottom: 8px;
            border-bottom: 1px dashed #eee;
            padding-bottom: 5px;
        }
        .bubble-info span {
            font-weight: bold;
            color: #333;
        }
        .bubble-answer {
            margin: 0;
            padding-top: 5px;
            white-space: pre-wrap;
        }
        
        /* 수정/삭제 버튼 Wrapper (HTML 버튼 스타일) */
        .action-button-wrapper {
            margin-top: 10px;
            text-align: right;
        }
        .action-button-wrapper button {
            border: none;
            background: none;
            color: #888;
            cursor: pointer;
            margin-left: 10px;
            font-size: 0.8em;
            transition: color 0.2s;
        }
        .action-button-wrapper button:hover {
            color: #000;
        }
        </style>
        """, unsafe_allow_html=True)

# --- 3. 핵심 기능 함수: 질문 표시 및 답변 목록 출력 ---
def show_daily_question():
    """질문을 표시하고, 답변 목록을 출력하며, 수정/삭제 로직을 구현합니다."""
    
    st.title(f"🗓️ {date.today()}의 데일리 질문")
    st.header(st.session_state.daily_question)
    st.markdown("---")
    
    # 답변 목록을 최신 순으로 정렬
    sorted_answers = sorted(st.session_state.daily_answers, key=lambda x: x['timestamp'], reverse=True)
    
    st.subheader(f"총 {len(sorted_answers)}개의 답변이 등록되었습니다.")
    
    # 답변 표시 영역
    answer_container = st.container()

    with answer_container:
        for i, ans in enumerate(sorted_answers):
            # 현재 로그인된 사용자와 답변 작성자가 동일한지 확인
            is_owner = (ans['name'] == st.session_state.current_name)
            
            # --- [핵심 수정] HTML 코드 노출 오류 해결: 버튼 HTML 분리 구성 ---
            action_buttons_html = "" 
            if is_owner:
                # HTML 코드를 별도 변수로 안전하게 구성
                action_buttons_html = f"""
                    <div class="action-button-wrapper">
                        <button class="edit-button" 
                            onclick="document.querySelector('button[key=edit_btn_{ans['id']}]').click()">
                            수정 ✏️
                        </button>
                        <button class="delete-button" 
                            onclick="document.querySelector('button[key=delete_btn_{ans['id']}]').click()">
                            삭제 🗑️
                        </button>
                    </div>
                    """

            # 최종 HTML 마크다운 구성
            answer_display_html = f"""
                <div class='bubble-container'>
                    <div class='bubble-info'>
                        [{ans['age_band']}] <span>{ans['name']}</span>님의 생각
                    </div>
                    <p class='bubble-answer'>
                        {ans['answer']}
                    </p>
                    
                    {action_buttons_html}  </div>
                """
            
            # HTML 렌더링
            st.markdown(answer_display_html, unsafe_allow_html=True)

            # --- HTML 버튼 클릭을 위한 숨겨진 Streamlit 버튼 ---
            if is_owner:
                # 버튼을 Columns에 넣어 정렬을 돕고, CSS로 숨김 처리함
                col_edit, col_delete = st.columns(2) 
                
                with col_edit:
                    # 수정 버튼: type="secondary"로 CSS를 통해 숨겨짐
                    if st.button("수정 로직 실행", key=f"edit_btn_{ans['id']}", type="secondary"):
                        # 버튼이 클릭되면 수정 모드 활성화 및 데이터 저장
                        st.session_state.edit_mode = True
                        st.session_state.edit_answer_id = ans['id']
                        st.session_state.edit_answer_text = ans['answer']
                        st.rerun()
                with col_delete:
                    # 삭제 버튼: type="secondary"로 CSS를 통해 숨겨짐
                    if st.button("삭제 로직 실행", key=f"delete_btn_{ans['id']}", type="secondary"):
                        delete_answer(ans['id'])
                        st.rerun()
    
    st.markdown("---")
    
    # 답변 작성/수정 폼 표시
    if st.session_state.logged_in:
        answer_form()
    else:
        st.info("답변을 작성하려면 먼저 로그인해 주세요.")


# --- 4. 로그인 및 답변 작성/수정 폼 ---

def login_form():
    """간단한 로그인 폼을 사이드바에 표시합니다."""
    with st.sidebar.form("login_form"):
        st.subheader("👨‍💻 로그인")
        name = st.text_input("사용자 이름", key="login_name")
        age_band = st.selectbox("나이대", ['20대', '30대', '40대', '50대 이상'], key="login_age")
        submit_button = st.form_submit_button("로그인")

        if submit_button and name:
            st.session_state.logged_in = True
            st.session_state.current_name = name
            st.session_state.current_age_band = age_band
            st.rerun()

def answer_form():
    """답변을 작성하거나 수정하는 폼을 표시합니다."""
    
    is_editing = st.session_state.edit_mode
    if is_editing:
        form_title = "✏️ 답변 수정하기"
        default_text = st.session_state.edit_answer_text
        submit_label = "답변 수정 완료"
    else:
        form_title = "✍️ 나의 생각 남기기"
        default_text = ""
        submit_label = "답변 등록"

    with st.form("answer_form", clear_on_submit=not is_editing):
        st.subheader(form_title)
        
        new_answer = st.text_area("당신의 생각을 적어주세요:", value=default_text, height=150)
        
        col_submit, col_cancel = st.columns([1, 4])
        
        with col_submit:
            submitted = st.form_submit_button(submit_label)
        
        with col_cancel:
            if is_editing:
                if st.button("수정 취소", type="secondary"):
                    st.session_state.edit_mode = False
                    st.rerun()
        
        if submitted and new_answer:
            if is_editing:
                # 수정 로직
                for i, ans in enumerate(st.session_state.daily_answers):
                    if ans['id'] == st.session_state.edit_answer_id:
                        st.session_state.daily_answers[i]['answer'] = new_answer
                        st.session_state.daily_answers[i]['timestamp'] = time.time()
                        break
                st.session_state.edit_mode = False
                st.session_state.edit_answer_id = None
                st.success("답변이 성공적으로 수정되었습니다.")
            else:
                # 새 답변 등록 로직
                new_id = max([ans['id'] for ans in st.session_state.daily_answers]) + 1 if st.session_state.daily_answers else 1
                new_answer_data = {
                    'id': new_id,
                    'name': st.session_state.current_name,
                    'age_band': st.session_state.current_age_band,
                    'answer': new_answer,
                    'timestamp': time.time()
                }
                st.session_state.daily_answers.append(new_answer_data)
                st.success("답변이 성공적으로 등록되었습니다!")
                
            st.rerun()

# --- 5. 메인 앱 실행 ---
def main():
    st.set_page_config(layout="wide", page_title="데일리 질문 앱")
    initialize_session_state()
    load_css()
    
    # 사이드바 로그인/로그아웃 처리
    if not st.session_state.logged_in:
        login_form()
    else:
        st.sidebar.success(f"환영합니다, {st.session_state.current_name}님 ({st.session_state.current_age_band})")
        if st.sidebar.button("로그아웃"):
            st.session_state.logged_in = False
            st.session_state.current_name = None
            st.session_state.current_age_band = None
            st.rerun()

    show_daily_question()

if __name__ == "__main__":
    main()
