import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from PIL import Image
import io

# 1. 페이지 및 환경 설정
st.set_page_config(page_title="소크라테스 AI 튜터", page_icon="🏛️", layout="wide")

st.title("🏛️ 소크라테스 AI 튜터")
st.markdown("텍스트, PDF, 사진을 업로드하면 AI가 스스로 생각하게 만드는 깊이 있는 질문을 던집니다.")

# 사이드바: API 키 설정
with st.sidebar:
    st.header("⚙️ 환경 설정")
    api_key = st.text_input("Gemini API Key를 입력하세요", type="password")
    st.markdown("[API Key 발급받기 (무료)](https://aistudio.google.com/app/apikey)")
    
    st.divider()
    if st.button("🔄 대화 초기화", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

if not api_key:
    st.warning("👈 사이드바에 Gemini API Key를 입력해야 앱을 시작할 수 있습니다.")
    st.stop()

# Gemini 모델 설정 (멀티모달 처리를 위해 1.5-flash 사용)
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. 세션 상태(Session State) 초기화 (앱이 재실행되어도 상태 유지)
if "question" not in st.session_state:
    st.session_state.question = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "context_data" not in st.session_state:
    st.session_state.context_data = None  # 텍스트 또는 이미지 객체 저장

# 3. 학습 자료 입력부
st.subheader("Step 1. 학습 자료 입력")
input_type = st.radio("자료 형태를 선택하세요", ["텍스트 붙여넣기", "PDF 업로드", "사진(이미지) 업로드"], horizontal=True)

context_text = ""
context_image = None

if input_type == "텍스트 붙여넣기":
    context_text = st.text_area("공부한 개념이나 텍스트를 붙여넣으세요", height=150)
elif input_type == "PDF 업로드":
    uploaded_pdf = st.file_uploader("PDF 문서를 업로드하세요", type=["pdf"])
    if uploaded_pdf:
        reader = PdfReader(uploaded_pdf)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                context_text += extracted + "\n"
        st.success("✅ PDF 텍스트 추출 완료!")
        with st.expander("추출된 텍스트 확인"):
            st.write(context_text[:1000] + "... (생략)")
elif input_type == "사진(이미지) 업로드":
    uploaded_img = st.file_uploader("교재나 필기 사진을 업로드하세요", type=["jpg", "jpeg", "png"])
    if uploaded_img:
        context_image = Image.open(uploaded_img)
        st.image(context_image, caption="업로드된 학습 자료", width=500)

# 4. 소크라테스식 질문 생성
if st.button("🧠 질문 생성하기 (개념 검증)", type="primary"):
    if not context_text.strip() and context_image is None:
        st.error("학습 자료를 먼저 입력해주세요!")
    else:
        with st.spinner("AI가 자료를 분석하여 핵심 질문을 만들고 있습니다..."):
            prompt = """
            당신은 소크라테스식 교육법을 완벽하게 구사하는 최고의 튜터입니다.
            제공된 학습 자료를 분석하여, 학생이 핵심 개념을 정확히 이해했는지 확인하기 위한 '서술형 질문'을 **딱 1개**만 생성하세요.
            
            [질문 작성 규칙]
            1. 단순 암기나 단답형(O/X, 용어 맞추기) 질문은 절대 금지합니다.
            2. '왜 그런 현상이 발생하는지', '어떤 원리인지', '이 과정이 의미하는 바가 무엇인지' 등 논리적 설명을 요구하는 깊이 있는 질문을 하세요.
            3. 문장은 간결하고 명확하게 작성하여 학생이 부담 없이 생각할 수 있게 하세요.
            """
            
            inputs = [prompt]
            if context_text:
                inputs.append(f"\n\n[학습 자료 텍스트]\n{context_text}")
                st.session_state.context_data = context_text
            if context_image:
                inputs.append(context_image)
                st.session_state.context_data = context_image
            
            try:
                response = model.generate_content(inputs)
                st.session_state.question = response.text
                st.session_state.messages = [] # 새 질문이 생성되면 이전 대화 기록 초기화
            except Exception as e:
                st.error(f"API 호출 중 오류가 발생했습니다: {e}")

# 5. 문답 진행 및 피드백 (대화 UI)
if st.session_state.question:
    st.divider()
    st.subheader("Step 2. 개념 검증 문답")
    
    # AI 튜터의 최초 질문 출력
    st.info(f"🧑‍🏫 **튜터의 질문:**\n\n{st.session_state.question}")

    # 이전 채팅 히스토리 출력 (사용자 답변과 AI 피드백)
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 사용자 답변 입력
    user_answer = st.chat_input("질문에 대한 답변을 서술해보세요...")
    
    if user_answer:
        # 1. 사용자 메시지 화면에 즉시 표시 및 저장
        st.session_state.messages.append({"role": "user", "content": user_answer})
        with st.chat_message("user"):
            st.markdown(user_answer)
            
        # 2. AI 피드백 생성
        with st.chat_message("assistant"):
            with st.spinner("답변을 분석하여 피드백을 작성 중입니다..."):
                feedback_prompt = f"""
                당신은 소크라테스식 튜터입니다.
                - 원래 튜터가 던진 질문: {st.session_state.question}
                - 학생의 답변: {user_answer}
                
                학생의 답변을 꼼꼼하게 평가하고 피드백을 작성하세요.
                
                [피드백 작성 규칙]
                1. (칭찬 및 확인): 학생이 정확히 이해한 부분은 명확히 짚어주며 칭찬하세요.
                2. (소크라테스식 교정): 부족한 부분이나 논리적 비약, 오개념이 있다면 **절대로 정답을 바로 알려주지 마세요.** 
                   대신 관련된 '힌트'나 '가벼운 꼬리 질문(Follow-up Question)'을 던져서 학생이 스스로 정답을 유추할 수 있도록 유도하세요.
                3. 친절하고 격려하는 말투로 3~4문장 이내로 핵심만 전달하세요.
                """
                
                # 피드백 생성 시에도 원본 문맥을 유지하기 위해 컨텍스트(텍스트 또는 이미지) 같이 전달
                feedback_inputs = [feedback_prompt]
                if isinstance(st.session_state.context_data, str):
                     feedback_inputs.append(f"\n[참고용 원본 학습 자료]\n{st.session_state.context_data}")
                elif isinstance(st.session_state.context_data, Image.Image):
                     feedback_inputs.append(st.session_state.context_data)
                
                try:
                    feedback_response = model.generate_content(feedback_inputs)
                    st.markdown(feedback_response.text)
                    st.session_state.messages.append({"role": "assistant", "content": feedback_response.text})
                except Exception as e:
                    st.error(f"피드백 생성 중 오류가 발생했습니다: {e}")