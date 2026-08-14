import streamlit as st
from openai import OpenAI
from pypdf import PdfReader
from supabase import create_client, Client
import json
import re

# 화면 및 환경 설정
st.set_page_config(page_title="인공지능 튜터", page_icon="■", layout="wide")

# 라이트 앱 쉘(Light App Shell) / 테크니컬 대시보드 CSS 강제 주입
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&family=JetBrains+Mono:wght@400;700&display=swap');

:root {
  /* Light Brutalist / App Shell Colors */
  --bg-color: #ffffff;
  --panel-bg: #ffffff;
  --border-color: #e5e5e5;
  --border-focus: #000000;
  
  --text-main: #000000;
  --text-muted: #666666;
  
  /* High Contrast Accents */
  --accent-bg: #000000;
  --accent-text: #ffffff;
  
  /* Sharp Edges Only */
  --radius: 0px;
}

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, sans-serif !important;
    color: var(--text-main) !important;
    background-color: var(--bg-color) !important;
    line-height: 1.6 !important;
}

.stApp {
    background-color: var(--bg-color) !important;
}

/* 측면 메뉴: 얇은 회색 우측 테두리 */
[data-testid="stSidebar"] {
    background-color: var(--bg-color) !important;
    border-right: 1px solid var(--border-color) !important;
}
[data-testid="stSidebar"] * {
    color: var(--text-muted) !important;
}

/* 제목 꾸밈: 아주 두껍고 강조 */
h1, h2, h3, h4, h5, h6 {
    color: var(--text-main) !important;
    font-weight: 900 !important;
    letter-spacing: -0.5px !important;
}

/* 정답 제출 등 주요 액션 단추 (Black block, White text + 세련된 애니메이션) */
button[kind="primary"] {
    background-color: var(--accent-bg) !important;
    color: var(--accent-text) !important;
    font-weight: 900 !important;
    border-radius: var(--radius) !important;
    border: 1px solid var(--accent-bg) !important;
    padding: 10px 24px !important;
    box-shadow: none !important;
    transition: transform 0.15s cubic-bezier(0.2, 0.8, 0.2, 1), box-shadow 0.15s ease, background-color 0.15s ease !important;
}
button[kind="primary"]:hover {
    background-color: #333333 !important;
    border-color: #333333 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
}
button[kind="primary"]:active {
    transform: translateY(1px) scale(0.98) !important;
    box-shadow: none !important;
}

/* 보조 단추 (투명 바탕, 얇은 테두리 + 세련된 애니메이션) */
button[kind="secondary"] {
    background-color: transparent !important;
    color: var(--text-main) !important;
    font-weight: 600 !important;
    border-radius: var(--radius) !important;
    border: 1px solid var(--border-color) !important;
    padding: 10px 24px !important;
    box-shadow: none !important;
    transition: transform 0.15s cubic-bezier(0.2, 0.8, 0.2, 1), box-shadow 0.15s ease, background-color 0.15s ease !important;
}
button[kind="secondary"]:hover {
    background-color: #f9f9f9 !important;
    border: 1px solid var(--text-main) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
}
button[kind="secondary"]:active {
    transform: translateY(1px) scale(0.98) !important;
    box-shadow: none !important;
}

/* 입력창 및 패널 */
.stTextInput input, .stTextArea textarea, [data-testid="stSelectbox"] div[data-baseweb="select"] {
    background-color: var(--bg-color) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: var(--radius) !important;
    color: var(--text-main) !important;
    padding: 12px !important;
    transition: border 0.2s ease !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border: 2px solid var(--border-focus) !important;
    box-shadow: none !important;
}

/* 묶음 패널 (완벽한 사각형 박스) */
[data-testid="stExpander"], div[data-testid="stContainer"] {
    background-color: var(--panel-bg) !important;
    border-radius: var(--radius) !important;
    border: 1px solid var(--border-color) !important;
    padding: 24px !important;
    box-shadow: none !important;
}
[data-testid="stExpander"] * {
    color: var(--text-main) !important;
}

/* 대시보드 통계 위젯(Metric) */
[data-testid="stMetric"] {
    background-color: var(--panel-bg) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: var(--radius) !important;
    padding: 20px !important;
    box-shadow: none !important;
}
[data-testid="stMetricValue"] {
    color: var(--text-main) !important;
    font-weight: 900 !important;
}

/* 탭(Tabs) 테크니컬 스타일링 (검은 배경 제거, 하단 밑줄로 깔끔하게 처리) */
.stTabs [data-baseweb="tab-list"] {
    gap: 24px;
    margin-bottom: 32px;
    border-bottom: 1px solid var(--border-color);
}
.stTabs [data-baseweb="tab"] {
    padding: 12px 0px;
    border-radius: 0px;
    background-color: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    font-weight: 700 !important;
    color: var(--text-muted) !important;
    transition: color 0.2s ease;
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--text-main) !important;
}
.stTabs [aria-selected="true"] {
    background-color: transparent !important;
    color: var(--text-main) !important;
    border-bottom: 2px solid var(--text-main) !important;
}

/* 채팅창 말풍선 */
.stChatMessage {
    background-color: var(--panel-bg) !important;
    border-radius: var(--radius) !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-main) !important;
    padding: 20px !important;
}

/* 안내 및 경고 상자 */
.stAlert {
    background-color: var(--panel-bg) !important;
    border: 1px solid var(--border-color) !important;
    border-left: 4px solid var(--text-main) !important;
    border-radius: var(--radius) !important;
    color: var(--text-main) !important;
}

/* 메타 텍스트(캡션 등) 모노스페이스 적용 */
small, .stCaption {
    font-family: 'JetBrains Mono', monospace !important;
    letter-spacing: 0px;
    color: var(--text-muted) !important;
}

label {
    color: var(--text-muted) !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    letter-spacing: 0.5px;
}

hr {
    border-bottom: 1px solid var(--border-color) !important;
    margin: 32px 0 !important;
}
</style>
""", unsafe_allow_html=True)

st.title("■ 인공지능 튜터 (v12.0)")

# 서버 비밀 금고에서 열쇠 꺼내기
try:
    api_key = st.secrets["UPSTAGE_API_KEY"]
    supa_url = st.secrets["SUPABASE_URL"]
    supa_key = st.secrets["SUPABASE_KEY"]
except KeyError:
    st.error("서버에 통신 열쇠가 등록되지 않았습니다. 관리자 설정을 확인하세요.")
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

# 상태 저장 설정
if "question_data" not in st.session_state:
    st.session_state.question_data = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "context_data" not in st.session_state:
    st.session_state.context_data = ""
if "topics" not in st.session_state:
    st.session_state.topics = []
if "document_title" not in st.session_state:
    st.session_state.document_title = ""
if "first_attempt_saved" not in st.session_state:
    st.session_state.first_attempt_saved = False
if "is_correct" not in st.session_state:
    st.session_state.is_correct = False
if "user" not in st.session_state:
    st.session_state.user = None

# 로그인 화면 구현
if st.session_state.user is None:
    st.subheader("사용자 접속 (로그인)")
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

# 측면 메뉴 (프로필 및 간소화)
with st.sidebar:
    user_name = st.session_state.user.email.split('@')[0]
    st.markdown(f"### ◇ 내 계정\n**{user_name}**")
    st.caption(f"{st.session_state.user.email}")
    st.divider()
    if st.button("로그아웃", use_container_width=True):
        st.session_state.user = None
        supabase.auth.sign_out()
        st.rerun()
    st.divider()
    st.caption("현재 판본: v12.0 (생명과학 예시 적용)")

# --- 공통 함수 ---

def parse_history_question(raw_text):
    match = re.search(r'\n\s*1\.', raw_text)
    if match:
        idx = match.start()
        q_text = raw_text[:idx].strip()
        opts_text = raw_text[idx:].strip()
        opts = [o.strip() for o in opts_text.split('\n') if o.strip()]
        return "multiple_choice", q_text, opts
    return "subjective", raw_text, []

def delete_record(record_id):
    try:
        supabase.table("qa_history").delete().eq("id", record_id).execute()
        st.toast("기록이 성공적으로 삭제되었습니다.")
    except Exception as e:
        st.error(f"삭제 오류: {e}")

def delete_all_by_result(result_type):
    try:
        supabase.table("qa_history").delete().eq("user_id", st.session_state.user.id).eq("result", result_type).execute()
        st.toast(f"{result_type} 기록이 모두 삭제되었습니다.")
    except Exception as e:
        st.error(f"삭제 오류: {e}")

def reset_learning_state():
    """문제 풀이 상태를 초기화하고 대시보드로 돌아가는 함수"""
    st.session_state.question_data = None
    st.session_state.messages = []
    st.session_state.first_attempt_saved = False
    st.session_state.is_correct = False

def analyze_topics(text):
    with st.spinner("문서의 구조와 지문 제목을 분석하고 있습니다..."):
        sys_instruction = """
        주어진 학습 자료를 분석하여 다음 사항을 추출하라.
        * document_title: 제시된 자료가 문학 작품(시, 소설 등), 비문학 독해 지문, 영어 지문 등 특정한 '본문'을 바탕으로 한다면 그 작품의 제목이나 핵심 소재(예: '윤동주 - 서시', '두 편의 시(길, 장래희망)')를 구체적으로 추출하라. 단순한 이론이나 과학 개념 설명문인 경우에만 '일반 학습 자료'라고 작성하라.
        * topics: 전체 내용을 아우르는 핵심 목차(카테고리) 3~5개를 배열 형태로 추출하라.
        
        [최고 수준의 경고: JSON 파싱 에러 방지 규칙]
        1. 시의 연 구분, 문단 나누기 등 어떤 이유로든 텍스트 값 내부에 줄바꿈(Enter/Newline) 문자를 절대 넣지 마라.
        2. 인용구, 대화, 강조 표현에 큰따옴표(") 대신 반드시 작은따옴표(')만 사용하라.
        
        반드시 아래 JSON 형식으로 출력하라.
        {
            "document_title": "작품 제목 또는 일반 학습 자료",
            "topics": ["서론 및 배경", "주요 원리", "한계점"]
        }
        """
        try:
            response = client.chat.completions.create(
                model="solar-1-mini-chat",
                messages=[{"role": "system", "content": sys_instruction}, {"role": "user", "content": text[:12000]}],
                response_format={"type": "json_object"},
                max_tokens=2048
            )
            raw_content = response.choices[0].message.content.strip().replace("```json", "").replace("```", "")
            result = json.loads(raw_content, strict=False)
            return result.get("document_title", "일반 학습 자료"), result.get("topics", [])
        except Exception as e:
            st.error(f"분석 오류: {e}")
            return "일반 학습 자료", []

def generate_new_question(q_type, mode="initial", prev_question="", topic=""):
    with st.spinner(f"'{topic}' 부분에 집중하여 문제를 출제 중입니다..."):
        mode_instruction = f"* 출제 범위: 학습 자료 전체 내용 중 반드시 '{topic}' 카테고리와 관련된 내용을 핵심으로 삼아 출제한다."
        if mode == "similar":
            mode_instruction += f"\n* 이전 질문('{prev_question}')과 유사한 개념을 묻되, 묻는 방식을 바꾼다."
        elif mode == "new":
            mode_instruction += f"\n* 이전 질문('{prev_question}')에서 다룬 내용은 배제한다."
            
        if q_type == "서술형 (논리적 글쓰기)":
            type_instruction = """
            [서술형 출제 규칙]
            * 질문: 원리나 이유를 묻는 논리적 서술형 질문 1개 작성.
            * [발문 작성 핵심 규칙]: 질문 문장 안에 대상이 되는 작품명이나 지문의 소재를 명시할 것. 절대 '이 시에서', '위 지문에서'처럼 모호하게 지칭하지 말 것.
            * hint_step1: 모범 답안에 들어갈 핵심 단어 3~4개의 배열.
            * hint_step2: 질문 조건에 맞는 모범 답안 문장에서 주요 명사 4~6개를 밑줄(______)로 완벽히 교체한 문장. 
            * keywords: 정답 채점을 위한 핵심어 배열.
            
            [최고 수준의 경고: JSON 파싱 에러 방지 규칙]
            1. 시의 구절을 인용하거나 선지를 길게 쓸 때, 데이터 값 내부에 줄바꿈(Enter/Newline)을 절대 넣지 마라. 모두 띄어쓰기로 이어 붙여라.
            2. 인용구, 대화, 작품명 표기 시 큰따옴표(") 대신 무조건 작은따옴표(')만 사용하라.
            
            반드시 아래의 JSON 형식만 출력한다.
            {
                "type": "subjective",
                "question": "서술형 질문 내용 (작품명 반드시 포함)",
                "hint_step1": ["단어1", "단어2", "단어3"],
                "hint_step2": "_______가 발생하여 _______에 영향을 미치기 때문이다.",
                "keywords": ["단어1", "단어2", "단어3"]
            }
            """
        else:
            type_instruction = """
            [객관식 출제 규칙]
            * 질문: 단순 암기가 아닌, 본문 내용을 바탕으로 한 추론, 인과관계 파악을 묻는 발문 작성.
            * [발문 작성 핵심 규칙]: 질문 문장 안에 대상이 되는 작품명이나 지문의 소재를 명시할 것. 절대 '이 시에서', '위 지문에서'처럼 모호하게 지칭하지 말 것.
            * options: 1번부터 5번까지의 선택지 내용. 반드시 5개의 독립된 문자열 원소를 가진 배열 형태로 출력할 것.
            * answer_key: 정답 선택지의 번호(정수형).
            * hint_step1: 문제를 푸는 데 필요한 핵심 개념 핵심어 2~3개 배열.
            * hint_step2: 직접적인 정답이 아닌, 추론의 방향을 잡아주는 짧은 조언.
            
            [최고 수준의 경고: JSON 파싱 에러 방지 규칙]
            1. 시의 구절을 인용하거나 선지를 길게 쓸 때, 데이터 값 내부에 줄바꿈(Enter/Newline)을 절대 넣지 마라. 모두 띄어쓰기로 이어 붙여 한 줄로 작성하라.
            2. 인용구, 대화, 작품명 표기 시 큰따옴표(") 대신 무조건 작은따옴표(')만 사용하라.
            
            반드시 아래의 JSON 형식만 출력한다.
            {
                "type": "multiple_choice",
                "question": "추론형 객관식 질문 내용 (작품명 반드시 포함)",
                "options": [
                    "1. 첫 번째 선택지 내용", "2. 두 번째 선택지 내용", "3. 세 번째 선택지 내용", "4. 네 번째 선택지 내용", "5. 다섯 번째 선택지 내용"
                ],
                "answer_key": 3,
                "hint_step1": ["개념1", "개념2"],
                "hint_step2": "조언 문장",
                "keywords": []
            }
            """
            
        system_instruction = f"당신은 학습 자료를 바탕으로 학생의 사고력을 기르는 출제자이다.\n아래의 규칙에 따라 문제를 생성한다.\n{mode_instruction}\n{type_instruction}"
        safe_context = st.session_state.context_data[:12000]
        user_content = f"[학습 자료 내용]\n{safe_context}"
        
        try:
            response = client.chat.completions.create(
                model="solar-1-mini-chat",
                messages=[{"role": "system", "content": system_instruction}, {"role": "user", "content": user_content}],
                response_format={"type": "json_object"},
                max_tokens=2048
            )
            raw_content = response.choices[0].message.content.strip().replace("```json", "").replace("```", "")
            st.session_state.question_data = json.loads(raw_content, strict=False)
            st.session_state.messages = [] 
            st.session_state.first_attempt_saved = False
            st.session_state.is_correct = False
            st.rerun()
        except Exception as e:
            st.error(f"연결 오류가 발생했습니다. (상세 오류: {e})")

def process_answer(user_answer, q_data):
    st.session_state.messages.append({"role": "user", "content": user_answer})
    with st.chat_message("user"):
        st.markdown(user_answer)
        
    with st.chat_message("assistant"):
        with st.spinner("튜터가 답변을 읽고 생각 중입니다..."):
            if q_data.get('type') == 'multiple_choice':
                eval_rules = """
                [평가 규칙]
                * 사용자의 최근 답변이 정답인지 파악한다. 객관식은 번호나 내용만 말해도 인정한다.
                * 객관식 문제이므로 첫 줄에 반드시 **[평가 결과: 정답]**, **[평가 결과: 오답]** 중 하나만 출력한다. (부분점수는 절대 부여하지 않는다.)
                * [정답]인 경우: 해설 후 대화를 마무리한다.
                * [오답]인 경우: 정답을 직접 주지 말고, 스스로 깨달을 수 있는 꼬리 질문을 던진다.
                """
            else:
                eval_rules = """
                [평가 규칙]
                * 사용자의 최근 답변이 정답인지 파악한다. 
                * 첫 줄에 반드시 **[평가 결과: 정답]**, **[평가 결과: 오답]**, **[평가 결과: 부분점수]** 중 하나를 출력한다.
                * [정답]인 경우: 해설 후 대화를 마무리한다.
                * [오답/부분점수]인 경우: 정답을 직접 주지 말고, 스스로 깨달을 수 있는 꼬리 질문을 던진다.
                """
                
            eval_sys_instruction = f"""
            당신은 학생의 사고력을 길러주는 튜터이다.
            [문제 정보]
            문제 유형: {q_data.get('type')}
            질문: {q_data['question']}
            객관식 선지: {q_data.get('options', '없음')}
            정답 기준: {q_data.get('answer_key', q_data.get('keywords', '인공지능이 문맥 파악'))}
            {eval_rules}
            """
            
            api_messages = [{"role": "system", "content": eval_sys_instruction}]
            for m in st.session_state.messages:
                api_messages.append({"role": m["role"], "content": m["content"]})
                
            try:
                feedback_response = client.chat.completions.create(
                    model="solar-1-mini-chat",
                    messages=api_messages,
                    max_tokens=2048
                )
                feedback_text = feedback_response.choices[0].message.content
                st.markdown(feedback_text)
                st.session_state.messages.append({"role": "assistant", "content": feedback_text})
                
                match = re.search(r"\[평가 결과:\s*(정답|오답|부분점수)\]", feedback_text)
                eval_result = match.group(1) if match else "미분류"
                
                if eval_result == "정답":
                    st.session_state.is_correct = True
                
                if not st.session_state.first_attempt_saved and not q_data.get('is_retry'):
                    save_q = q_data['question']
                    if q_data.get('type') == 'multiple_choice':
                        save_q += "\n" + "\n".join(q_data.get('options', []))
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
                        st.error(f"기록 저장 중 오류: {db_err}")
                st.rerun()
            except Exception as e:
                st.error(f"통신 오류가 발생했습니다: {e}")

# --- DB 내역 불러오기 ---
try:
    db_response = supabase.table("qa_history").select("*").eq("user_id", st.session_state.user.id).order("created_at", desc=True).execute()
    qa_history = db_response.data
except Exception as e:
    st.error(f"기록을 불러오지 못했습니다: {e}")
    qa_history = []

correct_list = [item for item in qa_history if item['result'] == "정답"]
partial_list = [item for item in qa_history if item['result'] == "부분점수"]
incorrect_list = [item for item in qa_history if item['result'] == "오답"]

# --- 생명과학 예시 텍스트 적용 ---
example_text = r"""- 31 -
대단원 Ⅱ. 항상성과 몸의 조절 2026학년도 창원북면고등학교 생명과학
소단원 04. 우리 몸의 방어작용 p98~107 2학년 반 번 이름: 학습
목표
‣ 병원체의 종류와 특징을 설명할 수 있다. ‣ 우리 몸의 방어작용을 선천성면역과 후천성면역으로 구분하여 설명할 수 있다. ❶ 감염성질환과 비감염성질환
1. 비감염성질환 : 유전, 환경 요인, 생활 방식 등 여러 가지 원인이 복합적으로 작용하여 발생하는 질병으로, 병원체가 관여하지 않으므로 타인에게 전염되지 않는다. (고혈압, 당뇨병, 뇌졸중, 혈우병 등)
2. 감염성질환 : 병원체에 감염되어 발생하는 질병으로, 공기나 음식물, 체액, 접촉 등 다양한 경로로 타인에게 
전염될 수 있다. (결핵, 독감, 말라리아 등)
❷ 병원체의 종류
1. [ 세 균 ](=박테리아)
1) 특징
 Ÿ 핵막과 막으로 둘러싸인 세포소기관이 없는 단세포 원핵생물
 Ÿ 핵막이 없어 하나로 연결된 원형의 염색체(DNA)가 세포질에 있다.
 Ÿ 대부분 세포막 바깥쪽에 펩티도글리칸 성분의 [ 세 포 벽 ]이 있다.
 Ÿ 물질대사 관련 효소가 있어 스스로 물질대사를 한다.
 Ÿ 다양한 환경에서 서식하며, 대부분 [ 분 열 법 ]으로 빠르게 증식한다.
 Ÿ 모양에 따라 공 모양의 구균, 막대기 모양의 간균, 꼬인 실 모양의 나선균으로 구분한다. 2) 질병 및 치료
 Ÿ 대부분의 세균은 해롭지 않거나 이로운 작용을 하기도 하지만, 일부 세균은 호흡기나 상처 부위를 통해 몸속으로
침입하여 조직을 파괴하거나 물질대사를 방해하는 독소를 방출하여 질병을 일으킨다. 
 Ÿ  결핵, 콜레라, 파상풍, 위궤양, 세균성 식중독, 세균성 폐렴, 피부염, 충치 등
 Ÿ 치료: [ 항 생 제 ]를 사용하여 세균을 죽이거나 세균의 증식을 억제
2. [ 바 이 러 스 ]
1) 특징
 Ÿ 세균보다 크기가 작아 세균 여과기를 통과한다.
 Ÿ 세포의 구조를 갖추고 있지 않고, 유전물질과 단백질 껍질로 구성된다.
 Ÿ 물질대사에 관여하는 효소가 없어 스스로 물질대사를 하지 못해 숙주세포 밖에서는 
단백질 결정체로 존재하고, 숙주세포 안에서는 숙주세포의 효소와 라이보솜을 이용해
증식할 수 있다. 2) 질병 및 치료
 Ÿ 숙주세포에 침투하여 증식하는 과정에서 숙주세포에 손상을 입히거나 파괴하여 질병을 일으킨다.
 Ÿ  감기, 독감, 홍역, 수두, 소아마비, 수족구병, 구순포진, 후천성면역결핍증(AIDS), 코로나바이러스감염증
-19(COVID-19), 에볼라 출혈열, 한국형 유행성 출혈열 등
 Ÿ 치료 : [ 항 바 이 러 스 제 ]가 바이러스의 증식을 억제하지만, 바이러스의 변이 속도가 빨라 개발이 어려움
3. [ 원 생 생 물 ]
1) 특징
 Ÿ 핵막과 막성 세포소기관을 갖는 진핵생물 중 동물, 식물, 균계를 제외한 생물
 Ÿ 질병을 일으키는 원생생물은 대부분 단세포 진핵생물로, 독립적으로 생활하거나 다른 생물에 기생한다. 2) 질병 및 치료
 Ÿ 오염된 음식이나 쥐, 모기, 파리와 같은 매개 생물을 통해 감염된다.
 Ÿ  말라리아, 수면병, 아메바성 이질, 아메바성 수막뇌염 등
 Ÿ 치료 : 질병에 따라 다양한 종류의 치료제가 사용되는데, 원생생물은 사람과 같은 진핵생물이므로 치료제를 
개발하기 쉽지 않고, 부작용이 나타날 수 있어 주의가 필요함.  
- 32 -
4. [ 곰 팡 이 ](진균, 균류)
1) 특징
 Ÿ 몸이 실 모양의 균사로 이루어진 다세포 진핵생물로, 세포막 바깥쪽에 키틴질의 세포벽이 있다.
 Ÿ 습한 곳에서 서식하며, 포자로 번식한다. 2) 질병 및 치료
 Ÿ 공기 중의 곰팡이 포자가 호흡 기관을 통해 몸속으로 들어와 폐 질환을 일으키거나 피부, 점막 등에 번식하여 
염증을 일으킨다.
 Ÿ  무좀, 칸디다증, 습진, 앨러지, 진균성 폐렴, 곰팡이성 식중독 등
Ÿ 치료 : [ 항 진 균 제 ]를 이용하여 치료
#더 알아보기_바이러스보다 더 단순한 구조의 비세포성 감염원
Ÿ [ 변 형 프 라 이 온 ]
 - 동물 세포에서 발견되는 비병원성 단백질인 정상 프라이온이 잘못 접혀진
형태로, 체내에서 잘 분해되지 않고 여러 동물에서 퇴행성 뇌질환을 
일으키는 감염성 단백질
 - 변형 프라이온과 접촉한 정상 프라이온은 변형 프라이온으로 전환되어 
사슬 형태의 복합제를 형성하여 정상적인 세포 기능을 방해하고, 중추
신경계에 축적되면 뇌에 스펀지처럼 구멍이 뚫려 뇌 기능을 잃게 된다.
 -  사람의 크로이츠펠트·야코프병, 양의 진전병(스크래피), 소의 광우병 등
Ÿ 바이로이드
 - 단백질 껍질 없이 노출된 원형의 RNA만으로 구성된 병원성 감염 물질
 - 관다발 식물을 감염시켜 식물의 생명 활동에 필수적인 단백질을 생산하는 능력을 저해한다. 5. 감염성 질환의 감염 경로와 예방
1) 감염성 질환의 감염 경로
 Ÿ 호흡 기관을 통한 감염
 Ÿ 오염된 물이나 음식을 통한 감염
 Ÿ 매개 곤충에 의한 감염
 Ÿ 기타 접촉에 의한 감염
2) 감염성 질환의 예방
 Ÿ 마스크 착용, 손 자주 씻기, 신선한 음식물과 균형 잡힌 식사, 규칙적인 운동, 적절한 스트레스 관리 등 건강한 
생활습관 형성과 매개 생물 방제 작업, 적절한 예방접종으로 인체의 방어 능력 향상
❸ 우리 몽의 방어작용
1. [ 선 천 성 ] 면역(=[ 비 특 이 적 ] 방어작용, 자연면역) - 태어나면서부터 가지고 있는 방어작용으로, 병원체에 공통으로 존재하는 특징을 인식하여 병원체의 종류를 
구분하지 않고 신속하고 광범위하게 일어남
- 감염 초기에 중요한 역할을 하며, 후천성 면역을 촉진 
- 33 -
대단원 Ⅱ. 항상성과 몸의 조절 2026학년도 창원북면고등학교 생명과학
소단원 04. 우리 몸의 방어작용 p98~107 2학년 반 번 이름: 1) 방어벽
 Ÿ [ 피 부 ]
 - 우리 몸을 둘러싸고 있는 물리적 장벽으로, 가장 바깥쪽은 죽은 세포로 이루어진 [ 각 질 층 ]으로 덮여 
있어 해로운 외부 물질과 병원체의 침입을 막는다.
 - 피부로 분비되는 [ 땀 ]은 세균의 세포벽을 분해하는 효소인 [ 라 이 소 자 임 ]을 포함하고 있어 병원체의
침입을 막는 데 도움이 된다.
 Ÿ [ 점 막 ]
 - 눈, 콧속, 소화기관, 호흡기관의 내벽 등 피부가 없이 외부로 노출된 부위는 점막으로 덮여 있고, 점막은 끈끈한
점액을 분비하여 병원체나 작은 입자를 잡아 가둔다.
 - 숨관가지의 상피세포는 [ 섬 모 ]를 움직여 점액에 갇힌 병원체를 몸 밖으로 내보낸다.
 - 눈물, 콧물, 침 등 점액 분비물 역시 라이소자임을 포함하고 있어 세균의 증식을 억제하고, 위액 속의 위산, 피지샘이나 땀샘에서 나오는 산성의 분비물도 세균의 증식을 억제한다.
2) 내부 방어
 Ÿ [ 식 세 포 ]작용(=식균작용) : 백혈구의 일종인 [ 큰 포 식 세 포 ](=대식세포)와 호중구가 병원체, 암세포, 손상된 세포 등을 세포 안으로 들여와 라이소솜*에 들어 있는 효소를 이용하여 이를 분해하는 작용
*라이소솜 : 다양한 가수분해효소가 들어 있는 작은 주머니 모양의 막성 세포소기관으로, 세포 안으로 들어온 병원체나 
 손상된 세포소기관을 분해한다.
 - 일부 백혈구는 식세포작용으로 병원체를 제거하는 동시에 림프구가 병원체를 인식하도록 하여 후천성 면역을 
촉진한다. 
 Ÿ [ 염 증 ] 반응 : 상처나 화상을 입어 피부나 점막이 손상되어 병원체가 몸속으로 들어왔을 때 일어나는 방어 
작용으로, [ 발 열 ], [ 부 어 오 름 ], [ 붉 어 짐 ], [ 통 증 ] 등의 증상을 동반하는 현상
 - 상처 부위에서 병원체를 제거하는 과정에서 백혈구, 죽은 병원체, 손상된 조직 세포 잔해 등이 모여 고름이 
생기고, 이후 고름은 림프액으로 흡수되어 제거된다.
 - 상처 부위에서 일어나는 정상적인 방어작용이지만, 과도한 염증반응은 조직 손상, 호흡 곤란 등의 문제를 
일으키며 심한 경우 사망에 이를 수 있다.
 - 염증반응 과정
 ① 상처 부위로 세균이 침입하면 백혈구의 일종인 [ 비 만 세 포 ]가 [ 히 스 타 민 ]을 분비한다.
 ② 히스타민에 의해 상처 부위 주변의 모세혈관이 [ 확 장 ]되어 혈류량과 혈관벽의 투과성이 [ 증 가 ]하고, 백혈구가 상처 부위로 모인다. 
 ③ 손상 부위에 모인 큰포식세포와 같은 여러 백혈구의 식세포작용으로 병원체와 손상된 세포가 제거되고, 모세혈관이 수축하며 조직이 재생된다.  
- 34 -
#더 알아보기_과도한 면역반응, 앨러지
Ÿ 앨러지 : 면역계가 민감하게 반응하여 인체에 해가 없는 물질을 과도하게 공격하는 질병
 - 앨러젠 : 앨러지를 일으키는 항원( 음식, 먼지, 진드기, 꽃가루, 털, 옻나무 등)
 - 앨러지 과정
Ÿ 아나필락시스 쇼크 : 호흡 곤란, 혈압 저하 등이 일어나는 전신 앨러지 반응
2. [ 후 천 성 ] 면역(=[ 특 이 적 ] 방어작용, 적응면역, 획득면역) - 태어난 후 병원체에 노출되면서 후천적으로 획득하는 방어작용으로, 특정 병원체에만 존재하는 특정 부위를 
인식하여 병원체의 종류에 따라 다르게 대응하므로 천천히 일어남
- 선천성 면역의 효과를 증가시키고, 세포성 면역과 체액성 면역으로 구분됨
1) 림프구의 생성과 성숙
 Ÿ 백혈구의 일종인 림프구는 [ 골 수 ]에서 생성되는데, 일부는 골수(Bone 
marrow)에 남아 계속 성숙하고 분화하여 [ B 림 프 구 ]가 되고, 다른 일부는
가슴샘(Thymus gland)으로 이동하여 성숙하고 분화하여 [ T 림 프 구 ]가 
된다. 이 과정에서 방어 작용에 효과적인 림프구만 성숙하고, 나머지는 제거된다. 
 Ÿ 분화된 T림프구와 B림프구는 면역 기관에 머물거나 이동하면서 병원체와 
같은 외부 물질의 침입에 대비한다.
 2) 항원과 항체
 Ÿ [ 항 원 ] : 우리 몸에 침입하여 면역 반응을 일으키는 물질
 - 몸속에 들어온 병원체뿐만 아니라 먼지, 꽃가루, 독성 물질 등도 항원으로 작용할 수 있다.
 Ÿ [ 항 체 ] : 항원에 대항하여 몸속에서 만들어지는 단백질로, 항원과 결합한다. 3) 후천성 면역 과정
 (1) 항원 인식
 ① 병원체가 침입하면 [ 큰 포 식 세 포 ]가 병원체를 세포 안으로 끌어들인 뒤 분해하여 [ 항 원 ]을 세포
표면에 제시한다.
 ② 큰포식세포가 항원을 제시하면 이 항원에 특이적으로 반응하는 [ 보 조 T 림 프 구 ]가 결합하여 항원의 
종류를 인식하고 빠르게 증식한다.
 ③ 활성화된 보조 T림프구는 다른 림프구의 활성화를 돕는다.
 (2) [ 세 포 성 ] 면역 : [ 세 포 독 성 T 림 프 구 ]가 병원체에 감염된 세포를 직접 공격하고 제거하는 면역
 Ÿ 보조 T림프구의 신호로 활성화된 세포독성 T림프구가 화학물질을 분비하여 바이러스나 세균에 감염된 세포, 손상된 세포, 암세포 등을 직접 공격하여 제거한다.  
- 35 -
대단원 Ⅱ. 항상성과 몸의 조절 2026학년도 창원북면고등학교 생명과학
소단원 04. 우리 몸의 방어작용 2학년 반 번 이름: 
 Ÿ 세포성 면역 과정
 ① 큰포식세포가 항원을 제시하면 보조 T림프구가 활성화된다.
 ② 활성화된 보조 T림프구는 세포독성 T림프구의 활성화를 돕는다.
 ③ 활성화된 세포독성 T림프구는 감염된 세포의 표면에 제시된 항원을 인식하고 직접 결합한다. 
 ④ 세포독성 T림프구는 세포막에 구멍을 내거나 세포의 주요 단백질을 분해하는 독성 물질을 분비하여 감염된 
세포를 파괴한다. 
 (3) [ 체 액 성 ] 면역 : 체액에 있는 [ 항 체 ]를 이용하여 병원체를 제거하는 면역
 Ÿ 체액성 면역 과정
 ① 큰포식세포가 항원을 제시하면 보조 T림프구가 활성화된다.
 ② 활성화된 보조 T림프구는 [ B 림 프 구 ]의 활성화를 돕는다.
 ③ 활성화된 B림프구는 증식하여 [ 형 질 세 포 ]와 [ 기 억 세 포 ]로 분화한다.
 ④ 형질세포는 항체를 생성하여 분비하고, 분비된 항체는 특정 항원과 결합하여 병원체의 활성을 억제한다.
 ⑤ 기억세포는 항원의 특성을 기억하여 동일한 항원이 재침입하면 빠르게 [ 형 질 세 포 ]로 분화하여 더 
빠르고 강한 체액성 면역 반응을 일으킨다.
 Ÿ 항체의 효과
 - 항원에 결합하여 세포 내로 침입하지 못하게 하고, 큰포식세포의 식세포 작용 촉진
 - 병원체의 세포막에 구멍을 만들어 세포의 파괴 유도
✿교과서 문제로 확인하기✿
p107 [나의 마무리 노트], 
p123 [개념 확인하기] 5~7번, p124 [개념 적용하기] 13~14번 
- 36 -
대단원 Ⅱ. 항상성과 몸의 조절
2026학년도 창원북면고등학교 생명과학
소단원 05. 항원항체반응 p108~111
학습
목표
‣ 항원항체반응의 특이성을 설명할 수 있다. ‣ 혈액의 응집반응의 원리를 이용하여 혈액형을 판정할 수 있다. ❶ 항원항체반응의 특이성
1. 항체의 구조 : 항원과 결합할 수 있는 [ Y ]자 모양의 혈장단백질 ⦁[ 항 원 결 합 부 위 ]가 2개 존재한다. ⦁항체의 종류마다 항원결합부위의 구조가 다르다. 2. [ 항 원 항 체 반 응 ] ⦁항원이 체내에 침입하면 면역반응이 일어나 항원을 제거하기 위한 항체가 생성되고, 생성된 항체는 항원과 결합하여 항원의 기능을 무력화시킨다. ⦁항원항체반응의 [ 특 이 성 ] : 항체는 항원결합부위와 구조적으로 맞는 특정 항원하고만 결합할 수 있다.
 
#해보기_항원과 항체의 반응
그림은 병원체 A~C와 항체 a~c의 구조를 나타낸 것이다.
1. 병원체 A와 결합할 수 있는 항체의 종류 : [ ]
2. 항체 c가 결합할 수 있는 병원체의 종류 : [ ]
❷ 항원항체반응의 활용
1. 항원 검사
∙ 항원항체반응은 항체나 항원의 존재 유무를 알아내는 데 활용된다. ( 감염병 진단 키트, 임신 진단 키트 등)
#해보기_항원항체반응의 특이성을 이용한 자가진단키트
[자료1]은 어떤 바이러스의 여부를 확인할 수 있는 자가진단 키트에 사용된 항원과 항체의 특징을 나타낸 
것이고, [자료2]는 바이러스 자가진단 키트의 원리를 설명한 것이다. 
- 37 -
대단원 Ⅱ. 항상성과 몸의 조절 2026학년도 창원북면고등학교 생명과학
소단원 05. 항원항체반응 2학년 반 번 이름: ∙ 검사 결과
- 항원이 없을 때 : 대조선(C)의 항체에만 항체 1이 결합하여 띠가 나타난다. - 항원이 있을 때 : 항체 1과 결합한 항원이 검사선(T)에 고정된 항체 2와 결합하여 띠가 나타나고, 항원과 
결합하지 않은 항체 1도 대조선(C)에 고정된 대조군 항체와 결합하여 띠가 나타난다. 구분 항원이 없을 때 항원이 있을 때
항원항체의
결합 모습
검사 결과
 
2. 혈액형 판정
1) 혈액의 [ 응 집 ] 반응 : 혈액형이 서로 다른 두 사람의 혈액이 섞이면 적혈구 막에 있는 항원과 혈장 속에 
있는 항체가 결합하여 서로 엉겨 붙어 덩어리가 형성되는 것
 ∙ [ 응 집 원 ] : 적혈구 세포막에 존재하는 항원
 ∙ [ 응 집 소 ] : 혈장에 존재하는 항체
2) ABO식 혈액형 : 적혈구 세포막에 있는 응집원 A와 응집원 B의 유무에 따라 A형, B형, AB형, O형으로 구분
 ∙ ABO식 혈액형의 응집원과 응집소
구분 A형 B형 AB형 O형
응집원
(적혈구)
응집소
(혈장)
 ∙ ABO식 혈액형의 판정
 - 항원항체반응의 특이성에 의해 응집원 A는 응집소 α와, 응집원 B는 응집소 β와 결합하여 응집한다. 구분 A형 B형 AB형 O형
항A 혈청* 항B 혈청*
(+:응집함, -:응집 안 함)
 *혈청 : 혈액의 액체 성분인 혈장에서 혈액 응고 성분을 제거한 것으로, 항A 혈청에는 응집소 α가, 항B 혈청에는 응집소 
β가 들어 있다. 
- 38 -
3) Rh식 혈액형 : 적혈구 세포막에 있는 Rh 응집원의 유무에 따라 Rh+형과 Rh-형으로 구분
 ∙ Rh식 혈액형의 응집원과 응집소
구분 Rh+형 Rh-형
Rh 응집원
(적혈구) 있음 없음
Rh 응집소
(혈장) 없음 없음
(단, Rh 응집원에 노출되면 생성됨)
 ∙ Rh식 혈액형의 판정
 
구분 항Rh 혈청
Rh+형
Rh-형
(+:응집함, -:응집 안 함)
#참고_태아적혈모구증
ABO식 혈액형의 응집소 α, β는 크기가 커서 태반을 통과하지 못하지만, Rh 응집소는 크기가 작아 태반을 
통과해서 태아에게 전달될 수 있다. 따라서 Rh-형인 여성이 Rh+형 첫째 아이를 임신하고 출산하면서 Rh 
응집원에 노출되면, 어머니의 혈장에 Rh 응집소가 형성된다. 이때는 산모와 태아의 건강에 별다른 이상이 
없지만, 이후 Rh+형인 둘째 아이를 임신하면 모체의 Rh 응집소가 태반을 통해 태아에게 전달되어 태아의 
적혈구가 파괴되는 태아적혈모구증이 발생할 수 있다. 
4) 수혈 관계
 ∙ 같은 혈액형 간의 수혈은 항원항체반응이 일어나지 않지만, 다른 혈액형 간의 수혈은 항원항체반응에 의한 
응집반응이 일어나 환자의 생명이 위험할 수 있다. 하지만 소량만 수혈하는 경우, 혈액을 제공하는 사람의 
응집원과 혈액을 제공받는 사람의 응집소가 응집반응을 일으키지 않으면 가능한데 이는 혈액을 제공하는
사람의 응집소가 받는 사람의 혈액에 희석되어 그 영향이 매우 적어지기 때문이다.  
- 39 -
대단원 Ⅰ. 생명 시스템의 구성 2026학년도 창원북면고등학교 생명과학
소단원 05. 항원항체반응 2학년 반 번 이름: [탐구활동] 혈액형 판정하기
포트폴리오6
확 인
Ÿ 목표 Ÿ 혈액의 응집반응원리를 이용하여 혈액형을 판정할 수 있다. Ÿ 준비물 Ÿ 채혈기, 채혈침, 이쑤시개, 소독용 알코올 솜, 항A 혈청, 항B 혈청, 항Rh 혈청
Ÿ 탐구 과정 Ÿ 
1. 채혈기에 채혈침을 끼운다. 2. 손가락 끝을 알코올 솜으로 소독한 뒤 채혈기로 살짝 찌른다. (한 번 사용한 채혈침은 재사용하지 않는다.)
3. 혈액 반응판에 혈액을 두 방울씩 떨어뜨린다. 4. 항A 혈청, 항B 혈청, 항Rh 혈청을 각각 한 방울씩 떨어뜨린다. 5. 이쑤시개로 잘 섞은 후 응집반응 여부를 확인한다. (단, 다른 혈청과 섞이지 않도록 서로 다른 이쑤시개를 사용한다.) 
Ÿ 탐구 결과 Ÿ 
1. 자신의 혈액 반응판에서 나타난 응집반응의 결과를 그리고, 응집반응 여부를 나타내 보자. 구분 항A 혈청 항B 혈청 항Rh 혈청
응집반응 그림
응집반응 여부 ( + , - ) ( + , - ) ( + , - )
2. 나의 ABO식 혈액형과 Rh식 혈액형을 설명해 보자.
 : 나의 ABO식 혈액형은 [ ]형, Rh식 혈액형은 [ ]형이다. 3. 그림은 응집소와 적혈구를 나타낸 것이다. 응집소의 모양을 참고하여 내가 가진 응집원을 적혈구의 세포막에
그려 보자.
 
4. 그림은 ABO식 혈액형이 서로 다른 두 사람의 혈액을 섞을 때 응집원과 
응집소를 나타낸 것이다. 두 사람의 ABO식 혈액형이 각각 무엇일까?
 : 혈액을 섞은 ABO식 혈액형은 각각 [ ]형과 [ ]형이다.
✿교과서 문제로 확인하기✿
p113 [나의 마무리 노트]
p124 [개념 적용하기] 15번 
- 40 -
대단원 Ⅱ. 항상성과 몸의 조절
2026학년도 창원북면고등학교 생명과학
소단원 06. 감염성질환의 예방 p114~121
학습
목표
‣ 감염성질환의 예방 방법을 이해하고, 백신의 필요성을 설명할 수 있다. ‣ 다양한 종류의 백신을 조사하고, 백신의 특징과 작용 원리를 설명할 수 있다. ❶ 백신을 통한 감염성 질환의 예방
1. 1차 면역반응과 2차 면역반응
1) 1차 면역반응 : 우리 몸에 특정 항원이 처음 침입했을 때 일어나는 면역 반응
 ∙ 항원이 우리 몸에 처음 노출되면 B림프구가 활성화되어 형질세포와 기억세포로 분화하고, 형질세포가 생성한 
항체가 항원을 제거한다. 항원의 종류를 인식하고 B림프구가 활성화되어 항체가 생성되기까지 시간이 걸린다. 2) 2차 면역반응 : 특정 항원이 재침입했을 때 일어나는 면역 반응
 ∙ 항원을 기억하는 기억세포가 형질세포와 기억세포로 빠르게 분화하여 1차 면역반응에 비해 훨씬 [ 빠 르 ]게 
[ 많 은 ] 양의 항체를 만든다. 이렇게 만들어진 항체 농도가 오랫동안 높게 유지된다. 
2. 백신의 작용 원리
1) 백신의 작용
 ∙ 주로 병원성을 제거하거나 약화한 병원체, 병원체의 표면 단백질, 병원체가 생산한 동소 등을 이용하여 만든다.
 ∙ 인위적으로 1차 면역반응을 일으켜 [ 기 억 세 포 ]를 생성하게 함으로써 이후 같은 항원을 지닌 병원체가 
침입했을 때 2차 면역반응이 일어나므로 감염성 질환을 예방할 수 있다. 
 ∙ 백신을 접종하면 해당 질병의 증상이 가볍게 나타날 수도 있지만 대부분 특별한 증상을 겪지 않고 지나간다.
 ∙ 백신으로 예방할 수 있는 질병 : 결핵, 홍역, 파상풍, 간염, 유행성이하선염, 소아마비, 코로나바이러스감염증 등
2) [ 집 단 면 역 ] : 집단을 구성하는 대부분의 개체가 면역력을 가지게 되면 감염병 확산이 둔화되고 면역력이 
없는 개체도 감염될 확률이 낮아진 상태 
- 41 -
대단원 Ⅰ. 생명 시스템의 구성 2026학년도 창원북면고등학교 생명과학
소단원 06. 감염성질환의 예방 2학년 반 번 이름: 3. 백신의 종류
1) [ 생 백 신 ](=약독화 백신) : 병을 일으키지 않도록 독성을 약화한 병원체를 사용한 백신
 ∙ 일반적인 감염과 유사하게 병원체가 몸속에서 증식하여 면역반응을 일으킨다.
 ∙ 1회 접종만으로도 면역 효력을 유지할 수 있다.
 ∙ 면역력이 약한 사람은 질병을 앓을 수 있고, 약화한 병원체의 독성이 되살아나 감염될 위험이 있다.
 ∙  천연두, 홍역, 수두, 볼거리 등의 백신
2) [ 사 백 신 ](=불활성화 백신, 비활성화 백신) : 열이나 화학 약품으로 완전히 죽인 병원체를 사용한 백신
 ∙ 병원체가 몸속에서 증식할 수 없고, 대부분 체액성 면역을 일으킨다.
 ∙ 면역력이 약한 사람에게도 안전하지만, 효과가 약해 여러 번 접종해야 한다.
 ∙ 전세포 불활성화 백신 / 단백 백신(병원체의 독소를 이용한 톡소이드(변성 독소) 백신, 병원체를 부수어 일부
를 이용하는 소단위(아단위) 백신) / 다당 백신(병원체를 이루는 긴 사슬의 다당을 이용) 등이 있다.
 ∙  독감, 소아마비, A형 간염, 콜레라 / 백일해, 파상풍, B형 간염, 디프테리아 / 페렴구균, 수막구균 등의 백신
3) [ 재 조 합 백 신 ] : 유전자재조합기술을 이용하여 생산한 병원체의 항원이나 항원결정부위를 사용한 백신
 ∙ 바이러스에 병원체의 항원 유전자 일부를 삽입하여 만드는 바이러스 벡터 백신 / 바이러스의 표면 항원 단백
질을 바이러스의 유사한 모양으로 조립하여 만드는 바이러스 유사 입자 백신 등이 있다.
 ∙  장티푸스, 사람유두종 등의 백신
4) [ 핵 산 백 신 ] : 특정 항원이나 항원결정부위를 암호화하는 핵산(DNA나 RNA)을 사용하는 백신
 ∙ 짧은 시간에 많은 양을 생산할 수 있지만 접종을 위한 기술 및 장치가 필요하고, 유통과 보관이 까다롭다.
 ∙  코로나바이러스감염증-19의 백신
✿교과서 문제로 확인하기✿
p121 [나의 마무리 노트], p124 [개념 적용하기] 16번
[ 04. 우리 몸의 방어 작용]
✿2025년도 고2 9월 생명과학Ⅰ
✿2025년도 고2 9월 생명과학Ⅰ 
- 42 -
대단원 Ⅱ. 항상성과 몸의 조절
2026학년도 창원북면고등학교 생명과학
소단원 04. 우리 몸의 방어작용 ~ 06. 감염성질환의 예방
✿2025년도 고2 10월 모고
[ 05. 항원항체반응 ]
✿2024년 고3 6월 생명과학Ⅰ
✿2022년 고3 9월 생명과학Ⅰ
✿2023년 고3 수능 생명과학Ⅰ
[ 06. 감염성질환의 예방 ]
✿2025년 고3 3월 생명과학Ⅰ"""

# --- 메인 화면 렌더링 분기 ---
if st.session_state.question_data is None:
    # 1. 대시보드 / 학습 / 관리 탭 모드
    tab_dash, tab_learn, tab_review = st.tabs(["❖ 대시보드", "＋ 새로운 학습", "◩ 오답 노트"])
    
    # 탭 1: 대시보드
    with tab_dash:
        st.subheader("나의 학습 현황 요약")
        
        total_q = len(qa_history)
        correct_n = len(correct_list)
        partial_n = len(partial_list)
        wrong_n = len(incorrect_list)
        accuracy = (correct_n / total_q * 100) if total_q > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("총 학습 문제", f"{total_q}개")
        col2.metric("정답률", f"{accuracy:.1f}%")
        col3.metric("● 완벽한 정답", f"{correct_n}개")
        col4.metric("◐ 복습 필요", f"{partial_n + wrong_n}개")
        
        st.divider()
        if total_q == 0:
            st.info("아직 학습 기록이 없습니다. '새로운 학습' 탭에서 첫 문제를 풀어보세요!")
        else:
            st.markdown("#### 최근 푼 문제")
            for item in qa_history[:5]:
                with st.container(border=True):
                    res_emoji = "●" if item['result'] == "정답" else ("◐" if item['result'] == "부분점수" else "○")
                    display_q = item['question'].split('\n')[0]
                    st.markdown(f"**{res_emoji} {item['result']}** | {display_q}")
                    
    # 탭 2: 새로운 학습
    with tab_learn:
        st.subheader("학습 자료 입력")
        
        col_input1, col_input2 = st.columns([2, 1])
        with col_input1:
            input_type = st.radio("자료 형태", ["글 붙여넣기", "PDF 문서 올리기"], horizontal=True)
            st.download_button("⤓ 예시 지문 파일(.txt) 다운로드", data=example_text, file_name="생명과학_2단원(2)_학습지.txt")
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
                st.success("문서 글자 추출 완료")
        
        if context_text:
            with st.expander("≣ 입력된 전체 텍스트 확인 및 수정"):
                context_text = st.text_area("원문 데이터", value=context_text, height=300, label_visibility="collapsed")
        
        if st.button("문서 분석 및 목차 추출", type="primary"):
            if not context_text.strip():
                st.error("학습 자료를 먼저 입력해야 합니다.")
            else:
                st.session_state.context_data = context_text
                doc_title, doc_topics = analyze_topics(context_text)
                st.session_state.document_title = doc_title
                st.session_state.topics = doc_topics
        
        if st.session_state.topics:
            st.divider()
            selected_topic = st.selectbox("어떤 부분의 문제를 풀어볼까요?", st.session_state.topics)
            if st.button("해당 목차로 문제 생성하기", type="primary"):
                q_type_mapped = "서술형 (논리적 글쓰기)" if q_type_select == "서술형 (논리적 글쓰기)" else "객관식 (5지 선다 추론형)"
                generate_new_question(q_type=q_type_mapped, mode="initial", topic=selected_topic)

    # 탭 3: 오답 노트
    with tab_review:
        st.subheader("나의 학습 기록 (오답 노트)")
        if total_q == 0:
            st.info("아직 풀이한 문제가 없습니다.")
        else:
            with st.expander(f"● 정답 ({len(correct_list)}개)", expanded=False):
                if correct_list:
                    if st.button("정답 기록 모두 삭제", key="del_all_correct", use_container_width=True):
                        delete_all_by_result("정답")
                        st.rerun()
                    st.divider()
                for item in correct_list:
                    display_q = item['question'].split('\n')[0]
                    col1, col2 = st.columns([7, 1])
                    with col1:
                        if st.button(f"Q: {display_q}", key=f"retry_correct_{item['id']}", use_container_width=True):
                            q_type, q_text, q_opts = parse_history_question(item['question'])
                            st.session_state.question_data = {
                                "type": q_type, "is_retry": True, "question": q_text, "options": q_opts,
                                "keywords": ["(인공지능이 문맥 파악)"], "hint_step1": ["복습 모드에서는 제공되지 않습니다."], "hint_step2": "이전에 정답을 맞혔던 문제입니다."
                            }
                            st.session_state.messages = []
                            st.session_state.first_attempt_saved = False
                            st.session_state.is_correct = False
                            st.rerun()
                    with col2:
                        if st.button("삭제", key=f"del_btn_correct_{item['id']}"):
                            delete_record(item['id'])
                            st.rerun()
                    
            with st.expander(f"◐ 부분점수 ({len(partial_list)}개)", expanded=True):
                if partial_list:
                    if st.button("부분점수 기록 모두 삭제", key="del_all_partial", use_container_width=True):
                        delete_all_by_result("부분점수")
                        st.rerun()
                    st.divider()
                for item in partial_list:
                    display_q = item['question'].split('\n')[0]
                    col1, col2 = st.columns([7, 1])
                    with col1:
                        if st.button(f"Q: {display_q}", key=f"retry_partial_{item['id']}", use_container_width=True):
                            q_type, q_text, q_opts = parse_history_question(item['question'])
                            st.session_state.question_data = {
                                "type": q_type, "is_retry": True, "question": q_text, "options": q_opts,
                                "keywords": ["(인공지능이 문맥 파악)"], "hint_step1": ["복습 모드에서는 제공되지 않습니다."], "hint_step2": "아쉽게 부분 점수를 받았던 문제입니다."
                            }
                            st.session_state.messages = []
                            st.session_state.first_attempt_saved = False
                            st.session_state.is_correct = False
                            st.rerun()
                    with col2:
                        if st.button("삭제", key=f"del_btn_partial_{item['id']}"):
                            delete_record(item['id'])
                            st.rerun()
                    
            with st.expander(f"○ 오답 ({len(incorrect_list)}개)", expanded=True):
                if incorrect_list:
                    if st.button("오답 기록 모두 삭제", key="del_all_incorrect", use_container_width=True):
                        delete_all_by_result("오답")
                        st.rerun()
                    st.divider()
                for item in incorrect_list:
                    display_q = item['question'].split('\n')[0]
                    col1, col2 = st.columns([7, 1])
                    with col1:
                        if st.button(f"Q: {display_q}", key=f"retry_wrong_{item['id']}", use_container_width=True):
                            q_type, q_text, q_opts = parse_history_question(item['question'])
                            st.session_state.question_data = {
                                "type": q_type, "is_retry": True, "question": q_text, "options": q_opts,
                                "keywords": ["(인공지능이 문맥 파악)"], "hint_step1": ["복습 모드에서는 제공되지 않습니다."], "hint_step2": "이전에 틀렸던 문제입니다."
                            }
                            st.session_state.messages = []
                            st.session_state.first_attempt_saved = False
                            st.session_state.is_correct = False
                            st.rerun()
                    with col2:
                        if st.button("삭제", key=f"del_btn_wrong_{item['id']}"):
                            delete_record(item['id'])
                            st.rerun()

else:
    # 2. 문제 풀이 튜터링 모드
    q_data = st.session_state.question_data
    
    col_title, col_btn = st.columns([4, 1])
    with col_title:
        st.subheader("개념 검증 문답")
    with col_btn:
        if st.button("↵ 대시보드로 돌아가기", use_container_width=True):
            reset_learning_state()
            st.rerun()
    st.divider()

    if st.session_state.document_title and st.session_state.document_title != "일반 학습 자료":
        st.info(f"분석된 지문 출처/제목: {st.session_state.document_title}")
    
    with st.container(border=True):
        display_q = q_data['question'].split('\n')[0]
        if q_data.get('type') == 'multiple_choice':
            st.markdown(f"**[객관식]**\n\n### {display_q}")
        else:
            st.markdown(f"**[서술형]**\n\n### {display_q}")
    
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        with st.expander("⚑ 1단계 힌트 (핵심어 찾기)"):
            st.write(", ".join(q_data.get('hint_step1', ["복습 모드에서는 제공되지 않습니다."])))
    with col_h2:
        with st.expander("⚑ 2단계 힌트 (방향 및 문장 틀)"):
            st.write(q_data.get('hint_step2', "복습 모드에서는 제공되지 않습니다."))

    if q_data.get('type') == 'multiple_choice' and not st.session_state.first_attempt_saved:
        raw_options = q_data.get('options', [])
        cleaned_options = []
        for opt in raw_options:
            if isinstance(opt, str) and "1." in opt and "2." in opt:
                split_opts = re.split(r'(?=[1-5]\.)', opt)
                cleaned_options.extend([o.strip() for o in split_opts if o.strip()])
            else:
                cleaned_options.append(opt)
        
        q_data['options'] = cleaned_options
        
        mc_answer = st.radio("아래에서 정답을 선택하세요.", q_data.get('options', []), index=None)
        if st.button("정답 제출", type="primary"):
            if mc_answer:
                process_answer(mc_answer, q_data)
            else:
                st.warning("선택지를 먼저 고르세요.")
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if st.session_state.first_attempt_saved or st.session_state.is_correct:
        st.divider()
        if not st.session_state.is_correct:
            st.info("튜터의 꼬리 질문에 계속 답변하며 스스로 정답을 찾아보세요!")
            
        st.markdown("### 다음 학습을 선택하세요")
        col_next1, col_next2 = st.columns(2)
        
        with col_next1:
            if st.button("현재 목차에서 다른 문제 다시 풀기", use_container_width=True):
                q_type_str = "서술형 (논리적 글쓰기)" if q_data.get('type')=='subjective' else "객관식 (5지 선다 추론형)"
                generate_new_question(q_type=q_type_str, mode="similar", prev_question=q_data['question'], topic=st.session_state.get('selected_topic', ''))
                
        with col_next2:
            if st.button("현재 목차에서 새로운 개념 문제 풀기", use_container_width=True):
                q_type_str = "서술형 (논리적 글쓰기)" if q_data.get('type')=='subjective' else "객관식 (5지 선다 추론형)"
                generate_new_question(q_type=q_type_str, mode="new", prev_question=q_data['question'], topic=st.session_state.get('selected_topic', ''))

    if not st.session_state.is_correct:
        if q_data.get('type') != 'multiple_choice' or st.session_state.first_attempt_saved:
            user_answer = st.chat_input("답변이나 궁금한 점을 튜터에게 말해보세요...")
            if user_answer:
                process_answer(user_answer, q_data)
