import streamlit as st
from openai import OpenAI
from pypdf import PdfReader
from supabase import create_client, Client
import json
import re

# 화면 및 환경 설정
st.set_page_config(page_title="인공지능 튜터", page_icon="🏛️", layout="wide")

st.title("🏛️ 인공지능 튜터 (v3.0)")
st.markdown("나만의 맞춤형 문제를 풀고, 튜터와 대화하며 완벽하게 이해해보세요.")

# 측면 메뉴: 새로고침
with st.sidebar:
    st.markdown("### 현재 판본: v3.0")
    if st.button("🔄 화면 새로고침", use_container_width=True):
        st.rerun()

# 서버 비밀 금고(Secrets)에서 열쇠 꺼내기
try:
    api_key = st.secrets["UPSTAGE_API_KEY"]
    supa_url = st.secrets["SUPABASE_URL"]
    supa_key = st.secrets["SUPABASE_KEY"]
except KeyError:
    st.error("서버에 API 열쇠가 등록되지 않았습니다. 관리자 설정(Secrets)을 확인하세요.")
    st.stop()

# 인공지능 및 데이터베이스 연결
client = OpenAI(
    api_key=api_key,
    base_url="https://api.upstage.ai/v1/solar",
    timeout=30.0
)

try:
    supabase: Client = create_client(supa_url, supa_key)
except Exception as e:
    st.error(f"데이터베이스 연결에 실패했습니다: {e}")
    st.stop()

# 상태 저장 설정 (v3.0 추가 상태 포함)
if "question_data" not in st.session_state:
    st.session_state.question_data = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "context_data" not in st.session_state:
    st.session_state.context_data = ""
if "first_attempt_saved" not in st.session_state:
    st.session_state.first_attempt_saved = False  # 첫 답변이 DB에 저장되었는지 여부
if "is_correct" not in st.session_state:
    st.session_state.is_correct = False  # 정답을 맞혔는지 여부
if "user" not in st.session_state:
    st.session_state.user = None

# 로그인 화면 구현
if st.session_state.user is None:
    st.subheader("🔒 사용자 접속 (로그인)")
    st.markdown("학습 기록을 영구적으로 저장하고 오답 노트를 활용하기 위해 로그인이 필요합니다.")
    
    login_email = st.text_input("이메일")
    login_password = st.text_input("비밀번호", type="password")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("로그인", use_container_width=True):
            try:
                auth_response = supabase.auth.sign_in_with_password({"email": login_email, "password": login_password})
                st.session_state.user = auth_response.user
                st.success("접속에 성공했습니다!")
                st.rerun()
            except Exception as e:
                st.error("접속 실패: 이메일과 비밀번호를 확인해주세요.")
    with col2:
        if st.button("새로 가입하기", use_container_width=True):
            try:
                auth_response = supabase.auth.sign_up({"email": login_email, "password": login_password})
                st.success("가입이 완료되었습니다. 이제 로그인 단추를 눌러 접속하세요.")
            except Exception as e:
                st.error(f"가입 실패: {e}")
    st.stop()

# 로그인 성공 후 우측 상단 로그아웃 기능 및 기록 불러오기 (오답 다시 풀기 기능 추가)
with st.sidebar:
    st.divider()
    st.write(f"👤 **{st.session_state.user.email}**님 접속 중")
    if st.button("로그아웃", use_container_width=True):
        st.session_state.user = None
        supabase.auth.sign_out()
        st.rerun()
        
    st.divider()
    st.header("📝 나의 학습 기록 (오답 노트)")
    
    try:
        db_response = supabase.table("qa_history").select("*").eq("user_id", st.session_state.user.id).order("created_at", desc=True).execute()
        qa_history = db_response.data
    except Exception as e:
        st.error(f"기록을 불러오지 못했습니다: {e}")
        qa_history = []
        
    if not qa_history:
        st.info("아직 풀이한 문제가 없습니다.")
    else:
        correct_list = [item for item in qa_history if item['result'] == "정답"]
        partial_list = [item for item in qa_history if item['result'] == "부분점수"]
        incorrect_list = [item for item in qa_history if item['result'] == "오답"]
        
        with st.expander(f"🟢 정답 ({len(correct_list)}개)"):
            for item in correct_list:
                st.markdown(f"**Q:** {item['question']}")
                st.caption(f"A: {item['user_answer']}")
                st.divider()
                
        with st.expander(f"🟡 부분점수 ({len(partial_list)}개)"):
            for item in partial_list:
                st.markdown(f"**Q:** {item['question']}")
                st.caption(f"A: {item['user_answer']}")
                if st.button("🔄 이 문제 다시 풀기", key=f"retry_{item['id']}"):
                    st.session_state.question_data = {
                        "type": "retry",
                        "question": item['question'],
                        "keywords": ["(AI가 문맥을 파악하여 자동 채점합니다)"],
                        "hint_step1": ["복습 모드에서는 제공되지 않습니다."],
                        "hint_step2": "이전에 아쉽게 부분 점수를 받았던 문제입니다. 기억을 되살려 완벽한 답을 적어보세요!"
                    }
                    st.session_state.messages = []
                    st.session_state.first_attempt_saved = False
                    st.session_state.is_correct = False
                    st.rerun()
                st.divider()
                
        with st.expander(f"🔴 오답 ({len(incorrect_list)}개)"):
            for item in incorrect_list:
                st.markdown(f"**Q:** {item['question']}")
                st.caption(f"A: {item['user_answer']}")
                if st.button("🔄 이 문제 다시 풀기", key=f"retry_wrong_{item['id']}"):
                    st.session_state.question_data = {
                        "type": "retry",
                        "question": item['question'],
                        "keywords": ["(AI가 문맥을 파악하여 자동 채점합니다)"],
                        "hint_step1": ["복습 모드에서는 제공되지 않습니다."],
                        "hint_step2": "이전에 틀렸던 문제입니다. 배운 내용을 적용하여 다시 도전해 보세요!"
                    }
                    st.session_state.messages = []
                    st.session_state.first_attempt_saved = False
                    st.session_state.is_correct = False
                    st.rerun()
                st.divider()

# 문제 출제 기능 (유형 분리 및 고도화)
def generate_new_question(q_type, mode="initial", prev_question=""):
    with st.spinner("자료를 깊이 있게 분석하여 질 높은 문제를 출제 중입니다... (최대 30초 소요)"):
        mode_instruction = ""
        if mode == "similar":
            mode_instruction = f"* 이전 질문('{prev_question}')에서 다룬 핵심 개념을 똑같이 다루되, 묻는 방식이나 관점을 바꾸어 새로운 질문을 생성한다."
        elif mode == "new":
            mode_instruction = f"* 이전 질문('{prev_question}')에서 다룬 개념은 철저히 배제하고, 제공된 학습 자료의 전혀 다른 부분이나 다른 개념에서 새로운 질문을 생성한다."
            
        if q_type == "서술형 (논리적 글쓰기)":
            type_instruction = """
            [서술형 출제 규칙]
            * 질문: 단답형이 아닌, 원리나 이유를 묻는 논리적 서술형 질문 1개 작성.
            * hint_step1: 모범 답안에 들어갈 핵심 단어 3~4개의 배열.
            * hint_step2: 질문 조건에 맞는 모범 답안 문장에서 주요 명사 4~6개를 밑줄(______)로 완벽히 교체한 문장. 정답 스포일러 절대 금지.
            * keywords: 정답 채점을 위한 핵심어 배열.
            
            반드시 아래의 JSON 형식만 출력한다.
            {
                "type": "subjective",
                "question": "핵심 개념을 묻는 서술형 질문 내용",
                "hint_step1": ["단어1", "단어2", "단어3"],
                "hint_step2": "_______가 발생하여 _______에 영향을 미치기 때문이다.",
                "keywords": ["단어1", "단어2", "단어3"]
            }
            """
        else:
            type_instruction = """
            [객관식 출제 규칙]
            * 질문: 단순 암기가 아닌, 본문 내용을 바탕으로 한 추론, 인과관계 파악, 적용 능력을 묻는 발문 작성. (예: "다음 글을 바탕으로 추론한 내용으로 가장 적절한 것은?")
            * options: 1번부터 5번까지의 선택지 배열. 오답 선지(매력적인 오답)는 본문에 나오는 단어를 섞어 교묘하게 인과관계를 바꾸거나 흔한 오개념을 반드시 포함할 것.
            * answer_key: 정답 선택지의 번호(정수형).
            * hint_step1: 문제를 푸는 데 필요한 핵심 개념 키워드 2~3개 배열.
            * hint_step2: 직접적인 정답이 아닌, 추론의 방향을 잡아주는 짧은 조언. (예: "A와 B의 관계를 다시 한 번 생각해보세요.")
            
            반드시 아래의 JSON 형식만 출력한다.
            {
                "type": "multiple_choice",
                "question": "추론형 객관식 질문 내용",
                "options": ["1. 선지내용", "2. 선지내용", "3. 선지내용", "4. 선지내용", "5. 선지내용"],
                "answer_key": 3,
                "hint_step1": ["개념1", "개념2"],
                "hint_step2": "조언 문장",
                "keywords": []
            }
            """
            
        system_instruction = f"""
        당신은 학습 자료를 바탕으로 학생의 사고력을 기르는 최고의 출제자이다.
        주어진 학습 자료를 읽고, 아래의 규칙에 따라 문제를 생성한다.
        {mode_instruction}
        {type_instruction}
        """
        
        safe_context = st.session_state.context_data[:4000]
        user_content = f"[학습 자료 내용]\n{safe_context}"
        
        try:
            response = client.chat.completions.create(
                model="solar-1-mini-chat",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            st.session_state.question_data = result
            st.session_state.messages = [] 
            st.session_state.first_attempt_saved = False
            st.session_state.is_correct = False
            st.rerun()
            
        except Exception as e:
            st.error(f"시간 초과 혹은 연결 오류가 발생했습니다. (상세 오류: {e})")

# 학습 자료 입력부
st.subheader("첫 번째 단계. 학습 자료 및 유형 선택")
col_input1, col_input2 = st.columns([2, 1])

with col_input1:
    input_type = st.radio("자료 형태", ["글 붙여넣기", "PDF 문서 올리기"], horizontal=True)
with col_input2:
    q_type_select = st.radio("출제 유형", ["서술형 (논리적 글쓰기)", "객관식 (5지 선다 추론형)"], horizontal=True)

context_text = ""
if input_type == "글 붙여넣기":
    context_text = st.text_area("공부한 개념이나 글을 붙여넣으세요", height=150)
elif input_type == "PDF 문서 올리기":
    uploaded_pdf = st.file_uploader("PDF 문서를 올리세요", type=["pdf"])
    if uploaded_pdf:
        reader = PdfReader(uploaded_pdf)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                context_text += extracted + "\n"
        st.success("✅ 문서 글자 추출 완료")
        with st.expander("추출된 글자 확인"):
            st.write(context_text[:1000] + "... (생략)")

if st.button("🧠 맞춤형 문제 생성하기", type="primary"):
    if not context_text.strip():
        st.error("학습 자료를 먼저 입력해야 합니다.")
    else:
        st.session_state.context_data = context_text
        generate_new_question(q_type=q_type_select, mode="initial")

# 문답 진행 및 평가 (소크라테스 튜터링)
if st.session_state.question_data:
    q_data = st.session_state.question_data
    
    st.divider()
    st.subheader("두 번째 단계. 개념 검증 문답 (소크라테스 대화)")
    
    # 문제 출력
    if q_data.get('type') == 'multiple_choice':
        st.info(f"🧑‍🏫 **객관식 질문:**\n\n{q_data['question']}\n\n" + "\n\n".join(q_data['options']))
    else:
        st.info(f"🧑‍🏫 **서술형 질문:**\n\n{q_data['question']}")
    
    # 단계별 힌트 출력
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        with st.expander("💡 1단계 힌트 (핵심어 찾기)"):
            st.write(", ".join(q_data.get('hint_step1', ["힌트가 제공되지 않는 모드입니다."])))
    with col_h2:
        with st.expander("💡 2단계 힌트 (방향 및 문장 틀)"):
            st.write(q_data.get('hint_step2', "힌트가 제공되지 않는 모드입니다."))

    # 채팅 기록 출력
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 아직 정답을 맞히지 않았다면 입력창 활성화
    if not st.session_state.is_correct:
        user_answer = st.chat_input("답변이나 궁금한 점을 튜터에게 말해보세요...")
        
        if user_answer:
            st.session_state.messages.append({"role": "user", "content": user_answer})
            with st.chat_message("user"):
                st.markdown(user_answer)
                
            with st.chat_message("assistant"):
                with st.spinner("튜터가 답변을 읽고 생각 중입니다..."):
                    
                    # API에 전달할 대화 맥락 구성
                    eval_sys_instruction = f"""
                    당신은 학생의 사고력을 길러주는 친절한 소크라테스식 튜터이다.
                    
                    [현재 문제 정보]
                    문제 유형: {q_data.get('type')}
                    질문: {q_data['question']}
                    객관식 선지(해당 시): {q_data.get('options', '없음')}
                    정답 기준: {q_data.get('answer_key', q_data.get('keywords', 'AI가 문맥으로 파악'))}
                    
                    [평가 및 대화 규칙]
                    1. 사용자의 최근 답변이 정답인지 파악한다. 객관식일 경우 번호만 말해도 정답으로 인정한다.
                    2. 응답의 첫 줄에는 반드시 **[평가 결과: 정답]**, **[평가 결과: 오답]**, **[평가 결과: 부분점수]** 중 하나를 괄호와 함께 정확히 출력한다.
                    3. [평가 결과: 정답]인 경우: 크게 칭찬하고, 왜 그것이 정답인지 명확히 해설한 뒤 대화를 훈훈하게 마무리한다.
                    4. [평가 결과: 오답 / 부분점수]인 경우: 
                       - 틀린 이유나 정답을 직접적으로 떠먹여주지 않는다.
                       - 학생이 스스로 깨달을 수 있도록 핵심 개념에 대한 '꼬리 질문(Follow-up Question)'을 하나만 던지며 대화를 유도한다.
                       - 따뜻하고 격려하는 말투를 사용한다.
                    """
                    
                    api_messages = [{"role": "system", "content": eval_sys_instruction}]
                    for m in st.session_state.messages:
                        api_messages.append({"role": m["role"], "content": m["content"]})
                        
                    try:
                        feedback_response = client.chat.completions.create(
                            model="solar-1-mini-chat",
                            messages=api_messages
                        )
                        feedback_text = feedback_response.choices[0].message.content
                        st.markdown(feedback_text)
                        st.session_state.messages.append({"role": "assistant", "content": feedback_text})
                        
                        # 평가 결과 추출
                        match = re.search(r"\[평가 결과:\s*(정답|오답|부분점수)\]", feedback_text)
                        eval_result = match.group(1) if match else "미분류"
                        
                        # 정답을 맞히면 상태 업데이트
                        if eval_result == "정답":
                            st.session_state.is_correct = True
                        
                        # 첫 시도일 때만 데이터베이스에 기록 전송 (재시도 모드가 아닐 때만)
                        if not st.session_state.first_attempt_saved and q_data.get('type') != 'retry':
                            save_q = q_data['question']
                            if q_data.get('type') == 'multiple_choice':
                                save_q += "\n" + "\n".join(q_data['options'])
                                
                            try:
                                supabase.table("qa_history").insert({
                                    "user_id": st.session_state.user.id,
                                    "question": save_q,
                                    "user_answer": user_answer,
                                    "result": eval_result,
                                    "feedback": feedback_text
                                }).execute()
                                st.session_state.first_attempt_saved = True
                            except Exception as db_err:
                                st.error(f"기록 저장 중 오류가 발생했습니다: {db_err}")
                                
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"통신 오류가 발생했습니다: {e}")

    # 다음 문제로 넘어가기 행동 선택 (정답을 맞혔거나, 한 번 이상 시도했을 때 표시)
    if st.session_state.first_attempt_saved or st.session_state.is_correct:
        st.divider()
        if not st.session_state.is_correct:
            st.info("💡 튜터의 꼬리 질문에 계속 답변하며 스스로 정답을 찾아보세요! (또는 아래 단추를 눌러 다음 문제로 넘어갈 수 있습니다)")
            
        st.markdown("### 다음 학습을 선택하세요")
        col_next1, col_next2 = st.columns(2)
        
        with col_next1:
            if st.button("🔄 같은 개념을 다른 문제로 다시 풀기", use_container_width=True):
                generate_new_question(q_type=q_type_select, mode="similar", prev_question=q_data['question'])
                
        with col_next2:
            if st.button("➡️ 새로운 개념의 문제 풀기", use_container_width=True):
                generate_new_question(q_type=q_type_select, mode="new", prev_question=q_data['question'])
