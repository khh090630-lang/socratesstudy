import streamlit as st
from openai import OpenAI
from pypdf import PdfReader
from supabase import create_client, Client
import json
import re

# 화면 및 환경 설정
st.set_page_config(page_title="인공지능 튜터", page_icon="🏛️", layout="wide")

# 다크 브루탈리스트(Dark Brutalist) / 테크니컬 대시보드 CSS 강제 주입
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&family=JetBrains+Mono:wght@400;700&display=swap');

:root {
  /* Dark Brutalist Colors */
  --bg-color: #050505;
  --panel-bg: #0a0a0a;
  --border-color: #333333;
  --border-focus: #ffffff;
  
  --text-main: #f4f4f5;
  --text-muted: #888888;
  
  /* High Contrast Accents */
  --accent-bg: #ffffff;
  --accent-text: #000000;
  
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

/* 측면 메뉴: 날카로운 우측 테두리 */
[data-testid="stSidebar"] {
    background-color: var(--bg-color) !important;
    border-right: 1px solid var(--border-color) !important;
}
[data-testid="stSidebar"] * {
    color: var(--text-muted) !important;
}

/* 제목 꾸밈: 아주 두껍고 대문자 강조 */
h1, h2, h3, h4, h5, h6 {
    color: var(--text-main) !important;
    font-weight: 900 !important;
    letter-spacing: -0.5px !important;
    text-transform: uppercase !important;
}

/* 정답 제출 등 주요 액션 단추 (White block, Black text) */
button[kind="primary"] {
    background-color: var(--accent-bg) !important;
    color: var(--accent-text) !important;
    font-weight: 900 !important;
    text-transform: uppercase !important;
    border-radius: var(--radius) !important;
    border: 1px solid var(--accent-bg) !important;
    padding: 10px 24px !important;
    box-shadow: none !important;
    transition: all 0.1s ease;
}
button[kind="primary"]:active, button[kind="primary"]:hover {
    background-color: #dddddd !important;
    border-color: #dddddd !important;
}

/* 보조 단추 (투명 바탕, 얇은 테두리) */
button[kind="secondary"] {
    background-color: transparent !important;
    color: var(--text-main) !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    border-radius: var(--radius) !important;
    border: 1px solid var(--border-color) !important;
    padding: 10px 24px !important;
    box-shadow: none !important;
}
button[kind="secondary"]:hover {
    background-color: #111111 !important;
    border: 1px solid var(--text-muted) !important;
}

/* 입력창 및 패널 */
.stTextInput input, .stTextArea textarea, [data-testid="stSelectbox"] div[data-baseweb="select"] {
    background-color: var(--bg-color) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: var(--radius) !important;
    color: var(--text-main) !important;
    padding: 12px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border: 1px solid var(--border-focus) !important;
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

/* 대시보드 통계 위젯(Metric) */
[data-testid="stMetric"] {
    background-color: var(--panel-bg) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: var(--radius) !important;
    padding: 20px !important;
    box-shadow: none !important;
}

/* 탭(Tabs) 테크니컬 스타일링 (선과 면의 강렬한 대비) */
.stTabs [data-baseweb="tab-list"] {
    gap: 0px;
    margin-bottom: 32px;
    border-bottom: 1px solid var(--border-color);
}
.stTabs [data-baseweb="tab"] {
    padding: 12px 24px;
    border-radius: var(--radius);
    background-color: transparent;
    border: 1px solid transparent;
    border-bottom: none;
    font-weight: 700 !important;
    text-transform: uppercase;
    color: var(--text-muted) !important;
}
.stTabs [aria-selected="true"] {
    background-color: var(--accent-bg) !important;
    color: var(--accent-text) !important;
    border: 1px solid var(--accent-bg) !important;
    border-bottom: none !important;
}

/* 채팅창 말풍선 */
.stChatMessage {
    background-color: var(--panel-bg) !important;
    border-radius: var(--radius) !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-main) !important;
    padding: 20px !important;
}

/* 안내 및 경고 상자 (좌측 굵은 테두리로 포인트) */
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
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

label {
    color: var(--text-muted) !important;
    font-family: 'JetBrains Mono', monospace !important;
    text-transform: uppercase;
    font-size: 12px !important;
    letter-spacing: 1px;
}

hr {
    border-bottom: 1px solid var(--border-color) !important;
    margin: 32px 0 !important;
}
</style>
""", unsafe_allow_html=True)

st.title("APP SHELL / AI TUTOR (v9.0)")

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
    st.subheader("USER AUTHENTICATION")
    st.markdown("학습 기록을 영구적으로 저장하고 오답 노트를 활용하기 위해 로그인이 필요합니다.")
    
    login_email = st.text_input("EMAIL ADDRESS")
    login_password = st.text_input("PASSWORD", type="password")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("SIGN IN", use_container_width=True):
            try:
                auth_response = supabase.auth.sign_in_with_password({"email": login_email, "password": login_password})
                st.session_state.user = auth_response.user
                st.success("접속에 성공했습니다!")
                st.rerun()
            except Exception as e:
                st.error("접속 실패: 이메일과 비밀번호를 확인해주세요.")
    with col2:
        if st.button("REGISTER NEW ACCOUNT", use_container_width=True):
            try:
                auth_response = supabase.auth.sign_up({"email": login_email, "password": login_password})
                st.success("가입이 완료되었습니다. 이제 로그인 단추를 눌러 접속하세요.")
            except Exception as e:
                st.error(f"가입 실패: {e}")
    st.stop()

# 측면 메뉴 (프로필 및 간소화)
with st.sidebar:
    user_name = st.session_state.user.email.split('@')[0]
    st.markdown(f"### /MY ACCOUNT\n**{user_name}**")
    st.caption(f"{st.session_state.user.email}")
    st.divider()
    if st.button("SIGN OUT", use_container_width=True):
        st.session_state.user = None
        supabase.auth.sign_out()
        st.rerun()
    st.divider()
    st.caption("VERSION: 9.0 (DARK BRUTALIST)")

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
    with st.spinner("ANALYZING DOCUMENT STRUCTURE..."):
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
    with st.spinner(f"GENERATING QUESTION FOR TOPIC: '{topic}'..."):
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
        with st.spinner("PROCESSING ANSWER..."):
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

# --- 메인 화면 렌더링 분기 ---
if st.session_state.question_data is None:
    # 1. 대시보드 / 학습 / 관리 탭 모드
    tab_dash, tab_learn, tab_review = st.tabs(["[DASHBOARD]", "[NEW SESSION]", "[ERROR LOGS]"])
    
    # 탭 1: 대시보드
    with tab_dash:
        st.subheader("PERFORMANCE METRICS")
        
        total_q = len(qa_history)
        correct_n = len(correct_list)
        partial_n = len(partial_list)
        wrong_n = len(incorrect_list)
        accuracy = (correct_n / total_q * 100) if total_q > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("TOTAL ATTEMPTS", f"{total_q}")
        col2.metric("ACCURACY", f"{accuracy:.1f}%")
        col3.metric("PERFECT SCORES", f"{correct_n}")
        col4.metric("NEEDS REVIEW", f"{partial_n + wrong_n}")
        
        st.divider()
        if total_q == 0:
            st.info("NO DATA AVAILABLE. START A NEW SESSION.")
        else:
            st.markdown("#### RECENT LOGS")
            for item in qa_history[:5]:
                with st.container(border=True):
                    res_emoji = "✅" if item['result'] == "정답" else ("⚠️" if item['result'] == "부분점수" else "❌")
                    display_q = item['question'].split('\n')[0]
                    st.markdown(f"**{res_emoji} {item['result']}** | {display_q}")
                    
    # 탭 2: 새로운 학습
    with tab_learn:
        st.subheader("INPUT DATA SOURCE")
        example_text = """[예시 지문] 윤동주 - 서시\n\n죽는 날까지 하늘을 우러러\n한 점 부끄럼이 없기를,\n잎새에 이는 바람에도\n나는 괴로워했다.\n별을 노래하는 마음으로\n모든 죽어가는 것을 사랑해야지.\n그리고 나한테 주어진 길을\n걸어가야겠다.\n\n오늘 밤에도 별이 바람에 스치운다."""
        
        col_input1, col_input2 = st.columns([2, 1])
        with col_input1:
            input_type = st.radio("DATA TYPE", ["TEXT INPUT", "PDF UPLOAD"], horizontal=True)
            st.download_button("DOWNLOAD SAMPLE (.TXT)", data=example_text, file_name="sample_text.txt")
        with col_input2:
            q_type_select = st.radio("QUESTION FORMAT", ["SUBJECTIVE", "MULTIPLE CHOICE"], horizontal=True)
        
        context_text = ""
        if input_type == "TEXT INPUT":
            context_text = st.text_area("PASTE CONTEXT HERE", height=150)
        elif input_type == "PDF UPLOAD":
            uploaded_pdf = st.file_uploader("UPLOAD PDF", type=["pdf"])
            if uploaded_pdf:
                reader = PdfReader(uploaded_pdf)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        context_text += extracted + "\n"
                st.success("PDF EXTRACTION COMPLETE.")
        
        if context_text:
            with st.expander("REVIEW & EDIT EXTRACTED TEXT"):
                context_text = st.text_area("RAW DATA", value=context_text, height=300, label_visibility="collapsed")
        
        if st.button("INITIALIZE ANALYSIS", type="primary"):
            if not context_text.strip():
                st.error("NO CONTEXT PROVIDED.")
            else:
                st.session_state.context_data = context_text
                doc_title, doc_topics = analyze_topics(context_text)
                st.session_state.document_title = doc_title
                st.session_state.topics = doc_topics
        
        if st.session_state.topics:
            st.divider()
            selected_topic = st.selectbox("SELECT TARGET TOPIC", st.session_state.topics)
            if st.button("GENERATE ASSESSMENT", type="primary"):
                q_type_mapped = "서술형 (논리적 글쓰기)" if q_type_select == "SUBJECTIVE" else "객관식 (5지 선다 추론형)"
                generate_new_question(q_type=q_type_mapped, mode="initial", topic=selected_topic)

    # 탭 3: 오답 노트
    with tab_review:
        st.subheader("ERROR & REVIEW LOGS")
        if total_q == 0:
            st.info("NO LOGS AVAILABLE.")
        else:
            with st.expander(f"✅ PASSED ({len(correct_list)})", expanded=False):
                if correct_list:
                    if st.button("PURGE PASSED LOGS", key="del_all_correct", use_container_width=True):
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
                                "keywords": ["(AI EVALUATION)"], "hint_step1": ["UNAVAILABLE IN REVIEW MODE."], "hint_step2": "PREVIOUSLY PASSED."
                            }
                            st.session_state.messages = []
                            st.session_state.first_attempt_saved = False
                            st.session_state.is_correct = False
                            st.rerun()
                    with col2:
                        if st.button("DEL", key=f"del_btn_correct_{item['id']}"):
                            delete_record(item['id'])
                            st.rerun()
                    
            with st.expander(f"⚠️ PARTIAL ({len(partial_list)})", expanded=True):
                if partial_list:
                    if st.button("PURGE PARTIAL LOGS", key="del_all_partial", use_container_width=True):
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
                                "keywords": ["(AI EVALUATION)"], "hint_step1": ["UNAVAILABLE IN REVIEW MODE."], "hint_step2": "PREVIOUSLY PARTIAL."
                            }
                            st.session_state.messages = []
                            st.session_state.first_attempt_saved = False
                            st.session_state.is_correct = False
                            st.rerun()
                    with col2:
                        if st.button("DEL", key=f"del_btn_partial_{item['id']}"):
                            delete_record(item['id'])
                            st.rerun()
                    
            with st.expander(f"❌ FAILED ({len(incorrect_list)})", expanded=True):
                if incorrect_list:
                    if st.button("PURGE FAILED LOGS", key="del_all_incorrect", use_container_width=True):
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
                                "keywords": ["(AI EVALUATION)"], "hint_step1": ["UNAVAILABLE IN REVIEW MODE."], "hint_step2": "PREVIOUSLY FAILED."
                            }
                            st.session_state.messages = []
                            st.session_state.first_attempt_saved = False
                            st.session_state.is_correct = False
                            st.rerun()
                    with col2:
                        if st.button("DEL", key=f"del_btn_wrong_{item['id']}"):
                            delete_record(item['id'])
                            st.rerun()

else:
    # 2. 문제 풀이 튜터링 모드
    q_data = st.session_state.question_data
    
    col_title, col_btn = st.columns([4, 1])
    with col_title:
        st.subheader("ACTIVE SESSION")
    with col_btn:
        if st.button("RETURN TO DASHBOARD", use_container_width=True):
            reset_learning_state()
            st.rerun()
    st.divider()

    if st.session_state.document_title and st.session_state.document_title != "일반 학습 자료":
        st.info(f"SOURCE DOC: {st.session_state.document_title}")
    
    with st.container(border=True):
        display_q = q_data['question'].split('\n')[0]
        if q_data.get('type') == 'multiple_choice':
            st.markdown(f"**[MULTIPLE CHOICE]**\n\n### {display_q}")
        else:
            st.markdown(f"**[SUBJECTIVE]**\n\n### {display_q}")
    
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        with st.expander("HINT 1: KEYWORDS"):
            st.write(", ".join(q_data.get('hint_step1', ["UNAVAILABLE."])))
    with col_h2:
        with st.expander("HINT 2: STRUCTURE"):
            st.write(q_data.get('hint_step2', "UNAVAILABLE."))

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
        
        mc_answer = st.radio("SELECT ANSWER:", q_data.get('options', []), index=None)
        if st.button("SUBMIT ANSWER", type="primary"):
            if mc_answer:
                process_answer(mc_answer, q_data)
            else:
                st.warning("SELECTION REQUIRED.")
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if st.session_state.first_attempt_saved or st.session_state.is_correct:
        st.divider()
        if not st.session_state.is_correct:
            st.info("SESSION REMAINS OPEN FOR FOLLOW-UP QUESTIONS.")
            
        st.markdown("### NEXT ACTIONS")
        col_next1, col_next2 = st.columns(2)
        
        with col_next1:
            if st.button("REGENERATE (SAME TOPIC)", use_container_width=True):
                q_type_str = "서술형 (논리적 글쓰기)" if q_data.get('type')=='subjective' else "객관식 (5지 선다 추론형)"
                generate_new_question(q_type=q_type_str, mode="similar", prev_question=q_data['question'], topic=st.session_state.get('selected_topic', ''))
                
        with col_next2:
            if st.button("GENERATE (NEW TOPIC)", use_container_width=True):
                q_type_str = "서술형 (논리적 글쓰기)" if q_data.get('type')=='subjective' else "객관식 (5지 선다 추론형)"
                generate_new_question(q_type=q_type_str, mode="new", prev_question=q_data['question'], topic=st.session_state.get('selected_topic', ''))

    if not st.session_state.is_correct:
        if q_data.get('type') != 'multiple_choice' or st.session_state.first_attempt_saved:
            user_answer = st.chat_input("ENTER COMMAND OR RESPONSE...")
            if user_answer:
                process_answer(user_answer, q_data)
