import streamlit as st
from openai import OpenAI
from pypdf import PdfReader

# 1. 화면 및 환경 설정
st.set_page_config(page_title="소크라테스 AI 튜터", page_icon="🏛️", layout="wide")

st.title("🏛️ 소크라테스 AI 튜터")
st.markdown("텍스트나 PDF를 업로드하면 인공지능이 깊이 있는 질문을 던진다.")

# 사이드바: API 키 설정
with st.sidebar:
    st.header("⚙️ 환경 설정")
    api_key = st.text_input("Upstage API Key를 입력한다", type="password")
    
    st.divider()
    if st.button("🔄 대화 초기화", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

if not api_key:
    st.warning("👈 사이드바에 Upstage API Key를 입력해야 시작할 수 있다.")
    st.stop()

# 업스테이지 API 연결 설정
client = OpenAI(
    api_key=api_key,
    base_url="https://api.upstage.ai/v1/solar"
)

# 2. 상태 저장 설정
if "question" not in st.session_state:
    st.session_state.question = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "context_data" not in st.session_state:
    st.session_state.context_data = ""

# 3. 학습 자료 입력부
st.subheader("Step 1. 학습 자료 입력")
input_type = st.radio("자료 형태를 선택한다", ["텍스트 붙여넣기", "PDF 업로드"], horizontal=True)

context_text = ""

if input_type == "텍스트 붙여넣기":
    context_text = st.text_area("공부한 개념이나 텍스트를 붙여넣는다", height=150)
elif input_type == "PDF 업로드":
    uploaded_pdf = st.file_uploader("PDF 문서를 업로드한다", type=["pdf"])
    if uploaded_pdf:
        reader = PdfReader(uploaded_pdf)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                context_text += extracted + "\n"
        st.success("✅ PDF 텍스트 추출을 완료했다.")
        with st.expander("추출된 텍스트 확인"):
            st.write(context_text[:1000] + "... (생략)")

# 4. 질문 생성
if st.button("🧠 질문 생성하기 (개념 검증)", type="primary"):
    if not context_text.strip():
        st.error("학습 자료를 먼저 입력해야 한다.")
    else:
        with st.spinner("자료를 분석하여 핵심 질문을 만들고 있다..."):
            system_instruction = """
            당신은 소크라테스식 교육법을 구사하는 튜터이다.
            제공된 학습 자료를 분석하여, 학생이 핵심 개념을 정확히 이해했는지 확인하기 위한 '서술형 질문'을 딱 1개만 생성한다.
            단순 암기나 단답형 질문은 금지한다.
            논리적 설명을 요구하는 깊이 있는 질문을 한다.
            문장은 간결하고 명확하게 작성한다.
            """
            
            user_content = f"[학습 자료 텍스트]\n{context_text}"
            st.session_state.context_data = context_text
            
            try:
                response = client.chat.completions.create(
                    model="solar-1-mini-chat",
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": user_content}
                    ]
                )
                st.session_state.question = response.choices[0].message.content
                st.session_state.messages = [] 
            except Exception as e:
                st.error(f"오류가 발생했다: {e}")

# 5. 문답 진행 및 평가
if st.session_state.question:
    st.divider()
    st.subheader("Step 2. 개념 검증 문답")
    
    st.info(f"🧑‍🏫 **튜터의 질문:**\n\n{st.session_state.question}")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_answer = st.chat_input("질문에 대한 답변을 서술한다...")
    
    if user_answer:
        st.session_state.messages.append({"role": "user", "content": user_answer})
        with st.chat_message("user"):
            st.markdown(user_answer)
            
        with st.chat_message("assistant"):
            with st.spinner("답변을 분석하여 평가를 작성 중이다..."):
                feedback_instruction = f"""
                당신은 소크라테스식 튜터이다.
                원래 던진 질문: {st.session_state.question}
                학생의 답변: {user_answer}
                원본 학습 자료: {st.session_state.context_data}
                
                학생의 답변을 평가하고 의견을 작성한다.
                정확히 이해한 부분은 확인해준다.
                부족한 부분이나 오류가 있다면 정답을 바로 알려주지 않는다.
                힌트나 꼬리 질문을 던져서 학생 스스로 유추할 수 있도록 유도한다.
                친절한 말투로 3~4문장 이내로 작성한다.
                """
                
                try:
                    feedback_response = client.chat.completions.create(
                        model="solar-1-mini-chat",
                        messages=[
                            {"role": "system", "content": feedback_instruction}
                        ]
                    )
                    feedback_text = feedback_response.choices[0].message.content
                    st.markdown(feedback_text)
                    st.session_state.messages.append({"role": "assistant", "content": feedback_text})
                except Exception as e:
                    st.error(f"오류가 발생했다: {e}")
