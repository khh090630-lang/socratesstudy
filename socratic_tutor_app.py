import streamlit as st
from openai import OpenAI
from pypdf import PdfReader
import json

# 화면 및 환경 설정
st.set_page_config(page_title="소크라테스 인공지능 튜터", page_icon="🏛️", layout="wide")

st.title("🏛️ 소크라테스 인공지능 튜터")
st.markdown("텍스트나 PDF를 업로드하면 깊이 있는 질문을 던집니다.")

# 측면 메뉴: 설정
with st.sidebar:
    st.header("⚙️ 환경 설정")
    api_key = st.text_input("Upstage API Key를 입력하세요", type="password")
    
    st.divider()
    if st.button("🔄 대화 초기화", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

if not api_key:
    st.warning("👈 측면 메뉴에 Upstage API Key를 입력해야 시작할 수 있습니다.")
    st.stop()

# 업스테이지 연결 설정
client = OpenAI(
    api_key=api_key,
    base_url="https://api.upstage.ai/v1/solar"
)

# 상태 저장 설정
if "question_data" not in st.session_state:
    st.session_state.question_data = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "context_data" not in st.session_state:
    st.session_state.context_data = ""

# 학습 자료 입력부
st.subheader("첫 번째 단계. 학습 자료 입력")
input_type = st.radio("자료 형태를 선택하세요", ["텍스트 붙여넣기", "PDF 업로드"], horizontal=True)

context_text = ""

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
        st.success("✅ PDF 텍스트 추출을 완료했습니다.")
        with st.expander("추출된 텍스트 확인"):
            st.write(context_text[:1000] + "... (생략)")

# 질문 및 힌트 생성
if st.button("🧠 질문 생성하기 (개념 점검)", type="primary"):
    if not context_text.strip():
        st.error("학습 자료를 먼저 입력해야 합니다.")
    else:
        with st.spinner("자료를 분석하여 핵심 질문을 만들고 있습니다..."):
            system_instruction = """
            당신은 학습 자료를 바탕으로 학생의 이해도를 점검하는 출제자이다.
            주어진 학습 자료를 읽고, 핵심 개념을 묻는 서술형 질문 1개와 그에 대한 빈칸 채우기 형식의 힌트를 생성한다.
            
            [출제 규칙]
            * 질문(question): 단답형이 아닌, 원리나 이유를 묻는 논리적 서술형 질문을 1개 작성한다. 서론이나 부연 설명 없이 질문 내용만 즉시 출력한다. (예: "~하는 이유를 설명한다.")
            * 힌트(hint): 질문에 대한 완성된 모범 답안 문장을 작성하되, 핵심 키워드 3~5개를 밑줄(______)로 비워둔 형태로 만든다.
            * 핵심 키워드 목록(keywords): 모범 답안에 포함되어야 할 필수 키워드를 배열 형태로 제공한다.
            
            반드시 아래의 JSON 형식만 출력한다. 다른 설명은 절대 추가하지 않는다.
            {
                "question": "핵심 개념을 묻는 서술형 질문 내용만 기재",
                "hint": "_______가 발생하여 _______에 영향을 미치기 때문이다. 와 같은 빈칸 포함 모범 답안",
                "keywords": ["키워드1", "키워드2", "키워드3"]
            }
            """
            
            user_content = f"[학습 자료 텍스트]\n{context_text}"
            st.session_state.context_data = context_text
            
            try:
                response = client.chat.completions.create(
                    model="solar-1-mini-chat",
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": user_content}
                    ],
                    response_format={"type": "json_object"}
                )
                
                # 응답 결과 해석 및 저장
                result = json.loads(response.choices[0].message.content)
                st.session_state.question_data = result
                st.session_state.messages = [] 
                
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")

# 문답 진행 및 평가
if st.session_state.question_data:
    q_data = st.session_state.question_data
    
    st.divider()
    st.subheader("두 번째 단계. 개념 검증 문답")
    
    # 질문 출력 (서론 없이 깔끔하게)
    st.info(f"🧑‍🏫 **질문:**\n\n{q_data['question']}")
    
    # 힌트 기능 (클릭 시 펼쳐짐)
    with st.expander("💡 힌트 보기 (핵심어 빈칸 채우기)"):
        st.markdown(q_data['hint'])

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_answer = st.chat_input("질문에 대한 답변을 서술하세요...")
    
    if user_answer:
        st.session_state.messages.append({"role": "user", "content": user_answer})
        with st.chat_message("user"):
            st.markdown(user_answer)
            
        with st.chat_message("assistant"):
            with st.spinner("답변을 분석하여 평가를 작성 중입니다..."):
                keywords_str = ", ".join(q_data['keywords'])
                evaluation_instruction = f"""
                당신은 학생의 서술형 답변을 평가하는 튜터이다.
                
                * 원래 던진 질문: {q_data['question']}
                * 학생이 작성한 답변: {user_answer}
                * 정답에 반드시 포함되어야 할 핵심 키워드: {keywords_str}
                
                [평가 규칙]
                * 먼저 첫 줄에 **[평가 결과: 정답 / 오답 / 부분점수]** 중 하나를 명확히 선언한다. 이 판단은 학생 답변에 필수 키워드가 얼마나 논리적으로 포함되었는지를 기준으로 한다.
                * 두 번째 줄부터 피드백을 시작한다. 학생이 잘 파악한 키워드는 확인해준다.
                * 학생이 빠뜨린 키워드나 논리적 오류가 있다면, 힌트나 꼬리 질문을 통해 스스로 생각해보도록 유도한다. (정답을 바로 주지 않는다.)
                * 친절한 평서문 말투로 작성한다.
                """
                
                try:
                    feedback_response = client.chat.completions.create(
                        model="solar-1-mini-chat",
                        messages=[
                            {"role": "system", "content": evaluation_instruction}
                        ]
                    )
                    feedback_text = feedback_response.choices[0].message.content
                    st.markdown(feedback_text)
                    st.session_state.messages.append({"role": "assistant", "content": feedback_text})
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {e}")
