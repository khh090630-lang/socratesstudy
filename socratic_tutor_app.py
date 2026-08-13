import streamlit as st
from openai import OpenAI
from pypdf import PdfReader
import json
import re

# 화면 및 환경 설정
st.set_page_config(page_title="소크라테스 인공지능 튜터", page_icon="🏛️", layout="wide")

st.title("🏛️ 소크라테스 인공지능 튜터 (v1.3)")
st.markdown("학습 자료를 올리고 문제를 풀며 이해도를 점검합니다.")

# 상태 저장 설정
if "question_data" not in st.session_state:
    st.session_state.question_data = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "context_data" not in st.session_state:
    st.session_state.context_data = ""
if "qa_history" not in st.session_state:
    st.session_state.qa_history = [] 
if "evaluation_done" not in st.session_state:
    st.session_state.evaluation_done = False 

# 측면 메뉴: 설정 및 오답 노트
with st.sidebar:
    st.markdown("### 현재 판본: v1.3")
    st.header("⚙️ 환경 설정")
    api_key = st.text_input("Upstage API Key를 입력하세요", type="password")
    
    st.divider()
    if st.button("🔄 대화 및 기록 초기화", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
        
    st.divider()
    st.header("📝 학습 기록 (오답 노트)")
    
    if not st.session_state.qa_history:
        st.info("아직 풀이한 문제가 없습니다.")
    else:
        correct_list = [item for item in st.session_state.qa_history if item['result'] == "정답"]
        partial_list = [item for item in st.session_state.qa_history if item['result'] == "부분점수"]
        incorrect_list = [item for item in st.session_state.qa_history if item['result'] == "오답"]
        
        with st.expander(f"🟢 정답 ({len(correct_list)}개)"):
            for idx, item in enumerate(correct_list):
                st.markdown(f"**Q:** {item['question']}")
                st.caption(f"A: {item['user_answer']}")
                st.divider()
                
        with st.expander(f"🟡 부분점수 ({len(partial_list)}개)"):
            for idx, item in enumerate(partial_list):
                st.markdown(f"**Q:** {item['question']}")
                st.caption(f"A: {item['user_answer']}")
                st.divider()
                
        with st.expander(f"🔴 오답 ({len(incorrect_list)}개)"):
            for idx, item in enumerate(incorrect_list):
                st.markdown(f"**Q:** {item['question']}")
                st.caption(f"A: {item['user_answer']}")
                st.divider()

if not api_key:
    st.warning("👈 측면 메뉴에 Upstage API Key를 입력해야 시작할 수 있습니다.")
    st.stop()

# 업스테이지 연결 설정
client = OpenAI(
    api_key=api_key,
    base_url="https://api.upstage.ai/v1/solar"
)

# 인공지능에 질문 생성을 요청하는 함수
def generate_new_question(mode="initial", prev_question=""):
    with st.spinner("자료를 분석하여 질문을 만들고 있습니다..."):
        mode_instruction = ""
        if mode == "similar":
            mode_instruction = f"* 이전 질문('{prev_question}')에서 다룬 핵심 개념을 똑같이 다루되, 묻는 방식이나 관점을 바꾸어 새로운 질문을 생성한다."
        elif mode == "new":
            mode_instruction = f"* 이전 질문('{prev_question}')에서 다룬 개념은 철저히 배제하고, 제공된 학습 자료의 전혀 다른 부분이나 다른 개념에서 새로운 질문을 생성한다."
            
        system_instruction = f"""
        당신은 학습 자료를 바탕으로 학생의 이해도를 점검하는 출제자이다.
        주어진 학습 자료를 읽고, 핵심 개념을 묻는 서술형 질문 1개와 그에 대한 빈칸 채우기 형식의 힌트를 생성한다.
        
        [출제 규칙]
        * 질문: 단답형이 아닌, 원리나 이유를 묻는 논리적 서술형 질문을 1개 작성한다. 서론이나 부연 설명 없이 질문 내용만 즉시 출력한다.
        * 질문 조건 준수: 질문에 특정 제한 조건이 있다면, 힌트와 핵심어에도 반드시 그 조건을 완벽하게 적용하여 배제한다.
        * 힌트: 질문 조건에 맞는 완성된 모범 답안을 먼저 생각한 뒤, 그 문장에서 주요 명사 및 핵심 단어 4~6개를 찾아 반드시 밑줄(______)로 완벽하게 교체하여 출력한다. 
        * 금지 사항: 힌트 문장 안에 정답 단어가 그대로 노출되어서는 절대 안 된다. 또한 괄호 안의 부가적인 설명이나 안내 문구는 절대 출력하지 않는다. 오직 빈칸이 포함된 문제 문장만 출력한다.
        * 핵심어 목록: 모범 답안에 포함되어야 할 빈칸의 정답 단어들을 배열 형태로 제공한다.
        {mode_instruction}
        
        반드시 아래의 JSON 형식만 출력한다. 다른 설명은 추가하지 않는다.
        {{
            "question": "핵심 개념을 묻는 서술형 질문 내용만 기재",
            "hint": "_______가 발생하여 _______에 영향을 미치기 때문이다.",
            "keywords": ["핵심어1", "핵심어2", "핵심어3"]
        }}
        """
        
        user_content = f"[학습 자료 내용]\n{st.session_state.context_data}"
        
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
            st.session_state.evaluation_done = False
            st.rerun()
            
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")

# 학습 자료 입력부
st.subheader("첫 번째 단계. 학습 자료 입력")
input_type = st.radio("자료 형태를 선택하세요", ["글 붙여넣기", "PDF 문서 올리기"], horizontal=True)

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
        st.success("✅ 문서 글자 추출을 완료했습니다.")
        with st.expander("추출된 글자 확인"):
            st.write(context_text[:1000] + "... (생략)")

# 질문 최초 생성 단추
if st.button("🧠 학습 시작하기 (최초 질문 생성)", type="primary"):
    if not context_text.strip():
        st.error("학습 자료를 먼저 입력해야 합니다.")
    else:
        st.session_state.context_data = context_text
        generate_new_question(mode="initial")

# 문답 진행 및 평가
if st.session_state.question_data:
    q_data = st.session_state.question_data
    
    st.divider()
    st.subheader("두 번째 단계. 개념 검증 문답")
    
    st.info(f"🧑‍🏫 **질문:**\n\n{q_data['question']}")
    
    with st.expander("💡 힌트 보기 (핵심어 빈칸 채우기)"):
        st.markdown(q_data['hint'])

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if not st.session_state.evaluation_done:
        user_answer = st.chat_input("질문에 대한 답변을 서술하세요...")
        
        if user_answer:
            st.session_state.messages.append({"role": "user", "content": user_answer})
            with st.chat_message("user"):
                st.markdown(user_answer)
                
            with st.chat_message("assistant"):
                with st.spinner("답변을 분석하여 평가 의견을 작성 중입니다..."):
                    keywords_str = ", ".join(q_data['keywords'])
                    evaluation_instruction = f"""
                    당신은 학생의 서술형 답변을 평가하는 튜터이다.
                    
                    * 원래 던진 질문: {q_data['question']}
                    * 학생이 작성한 답변: {user_answer}
                    * 정답에 반드시 포함되어야 할 핵심어: {keywords_str}
                    
                    [평가 규칙]
                    * 먼저 첫 줄에 **[평가 결과: 정답]**, **[평가 결과: 오답]**, **[평가 결과: 부분점수]** 중 하나를 괄호와 함께 정확하게 선언한다.
                    * 평가 기준: 학생의 답변을 주의 깊게 읽고, 제시된 핵심어가 모두 문맥에 맞게 포함되어 있다면 '정답'으로 처리한다. 학생이 핵심어를 분명히 적었음에도 누락되었다고 잘못 평가하는 일이 없도록 철저히 대조한다.
                    * 두 번째 줄부터 평가 의견을 시작한다. 학생이 잘 파악한 핵심어는 확인해준다.
                    * 학생이 빠뜨린 핵심어나 논리적 오류를 교정해주며, 추가적인 질문은 하지 않고 깔끔하게 마무리한다.
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
                        
                        match = re.search(r"\[평가 결과:\s*(정답|오답|부분점수)\]", feedback_text)
                        eval_result = match.group(1) if match else "미분류"
                        
                        st.session_state.qa_history.append({
                            "question": q_data['question'],
                            "user_answer": user_answer,
                            "result": eval_result,
                            "feedback": feedback_text
                        })
                        
                        st.session_state.evaluation_done = True
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {e}")
                        
    else:
        st.divider()
        st.markdown("### 다음 학습을 선택하세요")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 같은 개념을 다른 문제로 다시 풀기", use_container_width=True):
                generate_new_question(mode="similar", prev_question=q_data['question'])
                
        with col2:
            if st.button("➡️ 새로운 개념의 문제 풀기", use_container_width=True):
                generate_new_question(mode="new", prev_question=q_data['question'])
