import streamlit as st
from openai import OpenAI
from pypdf import PdfReader
from supabase import create_client, Client
import json
import re

# 화면 및 환경 설정
st.set_page_config(page_title="인공지능 튜터", page_icon="🏛️", layout="wide")

# 세련되고 간결한 모던 라이트(Modern Light) CSS 강제 주입
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
  /* Surface */
  --color-canvas: #fafafa;
  --color-surface-1: #ffffff;
  --color-surface-2: #f3f4f6;
  --color-hairline: #e5e7eb;
  --color-hairline-strong: #d1d5db;
  
  /* Brand Accent (Sleek Dark Slate) */
  --color-primary: #0f172a;
  --color-primary-hover: #1e293b;
  --color-primary-focus: rgba(15, 23, 42, 0.15);
  
  /* Typography Colors */
  --color-ink: #111827;
  --color-ink-muted: #374151;
  --color-ink-subtle: #6b7280;
  
  /* Border Radius */
  --rounded-xs: 4px;
  --rounded-sm: 6px;
  --rounded-md: 8px;
  --rounded-lg: 12px;
  --rounded-xl: 16px;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
}

/* 기본 글꼴 강제 설정 및 전체 배경 */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif !important;
    color: var(--color-ink) !important;
    background-color: var(--color-canvas) !important;
    line-height: 1.6 !important;
}

.stApp {
    background-color: var(--color-canvas) !important;
}

/* 측면 메뉴 배경 */
[data-testid="stSidebar"] {
    background-color: var(--color-surface-2) !important;
    border-right: 1px solid var(--color-hairline) !important;
}
[data-testid="stSidebar"] * {
    color: var(--color-ink-muted) !important;
    text-shadow: none !important;
}

/* 제목 꾸밈 (깔끔하고 단단하게) */
h1, h2, h3, h4, h5, h6 {
    color: var(--color-ink) !important;
    font-weight: 700 !important;
    letter-spacing: -0.5px !important;
    -webkit-text-stroke: 0px !important;
    text-shadow: none !important;
}

/* 정답 제출 등 주요 액션 단추 (시크한 다크 슬레이트) */
button[kind="primary"] {
    background-color: var(--color-primary) !important;
    color: #ffffff !important;
    font-weight: 500 !important;
    border-radius: var(--rounded-md) !important;
    border: none !important;
    padding: 8px 16px !important;
    box-shadow: var(--shadow-sm) !important;
    transition: all 0.2s ease;
}
button[kind="primary"]:active, button[kind="primary"]:hover {
    background-color: var(--color-primary-hover) !important;
    box-shadow: var(--shadow-md) !important;
    transform: translateY(-1px);
}

/* 보조 단추 (흰색 바탕, 옅은 테두리) */
button[kind="secondary"] {
    background-color: var(--color-surface-1) !important;
    color: var(--color-ink) !important;
    font-weight: 500 !important;
    border-radius: var(--rounded-md) !important;
    border: 1px solid var(--color-hairline-strong) !important;
    padding: 8px 16px !important;
    box-shadow: var(--shadow-sm) !important;
    transition: all 0.2s ease;
}
button[kind="secondary"]:hover {
    background-color: var(--color-surface-2) !important;
    border: 1px solid #9ca3af !important;
}

/* 입력창 및 패널 */
.stTextInput input, .stTextArea textarea, [data-testid="stSelectbox"] div[data-baseweb="select"] {
    background-color: var(--color-surface-1) !important;
    border: 1px solid var(--color-hairline-strong) !important;
    border-radius: var(--rounded-md) !important;
    color: var(--color-ink) !important;
    padding: 8px 12px !important;
    box-shadow: var(--shadow-sm) !important;
    transition: all 0.2s ease;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border: 1px solid var(--color-primary) !important;
    box-shadow: 0 0 0 3px var(--color-primary-focus) !important;
    outline: none !important;
}

/* 묶음 패널 (부드러운 그림자와 깔끔한 카드 레이아웃) */
[data-testid="stExpander"], div[data-testid="stContainer"] {
    background-color: var(--color-surface-1) !important;
    border-radius: var(--rounded-lg) !important;
    border: 1px solid var(--color-hairline) !important;
    padding: 24px !important;
    box-shadow: var(--shadow-sm) !important;
}
[data-testid="stExpander"] * {
    color: var(--color-ink) !important;
}

/* 측면 메뉴 내 묶음 패널 예외 처리 */
[data-testid="stSidebar"] [data-testid="stExpander"] {
    background-color: transparent !important;
    border: none !important;
    border-bottom: 1px solid var(--color-hairline) !important;
    border-radius: 0 !important;
    padding: 12px 0 !important;
    box-shadow: none !important;
}

/* 채팅창 말풍선 */
.stChatMessage {
    background-color: var(--color-surface-1) !important;
    border-radius: var(--rounded-lg) !important;
    border: 1px solid var(--color-hairline) !important;
    color: var(--color-ink) !important;
    box-shadow: var(--shadow-sm) !important;
    padding: 16px !important;
}

/* 안내 및 경고 상자 */
.stAlert {
    background-color: var(--color-surface-1) !important;
    border: 1px solid var(--color-hairline) !important;
    border-radius: var(--rounded-lg) !important;
    color: var(--color-ink) !important;
    box-shadow: var(--shadow-sm) !important;
}

/* 라벨 및 보조 텍스트 스타일 */
label {
    color: var(--color-ink-muted) !important;
    font-weight: 500 !important;
    font-size: 14px !important;
}

/* 구분선 */
hr {
    border-bottom-color: var(--color-hairline) !important;
    margin: 24px 0 !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🏛️ 인공지능 튜터 (v7.0)")
st.markdown("학습 자료를 목차별로 나누어 분석하고, 실전 같은 객관식과 서술형 문제를 풀어보세요.")

# 측면 메뉴: 새로고침
with st.sidebar:
    st.markdown("### 현재 판본: v7.0")
    if st.button("🔄 화면 새로고침", use_container_width=True):
        st.rerun()

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

# 기록에서 문제와 선택지를 분리해내는 해독 함수
def parse_history_question(raw_text):
    match = re.search(r'\n\s*1\.', raw_text)
    if match:
        idx = match.start()
        q_text = raw_text[:idx].strip()
        opts_text = raw_text[idx:].strip()
        opts = [o.strip() for o in opts_text.split('\n') if o.strip()]
        return "multiple_choice", q_text, opts
    return "subjective", raw_text, []

# 삭제 기능 함수
def delete_record(record_id):
    try:
        supabase.table("qa_history").delete().eq("id", record_id).execute()
    except Exception as e:
        st.sidebar.error(f"삭제 오류: {e}")

def delete_all_by_result(result_type):
    try:
        supabase.table("qa_history").delete().eq("user_id", st.session_state.user.id).eq("result", result_type).execute()
    except Exception as e:
        st.sidebar.error(f"삭제 오류: {e}")

# 로그아웃 및 오답 노트 불러오기
with st.sidebar:
    st.divider()
    st.write(f"👤 **{st.session_state.user.email}**님 접속 중")
    if st.button("로그아웃", use_container_width=True):
        st.session_state.user = None
        supabase.auth.sign_out()
        st.rerun()
        
    st.divider()
    st.header("나의 학습 기록")
    
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
            if correct_list:
                if st.button("정답 기록 모두 삭제", key="del_all_correct", use_container_width=True):
                    delete_all_by_result("정답")
                    st.rerun()
                st.divider()
            for item in correct_list:
                display_q = item['question'].split('\n')[0]
                col1, col2 = st.columns([5, 1])
                with col1:
                    if st.button(f"Q: {display_q}", key=f"retry_correct_{item['id']}", use_container_width=True):
                        q_type, q_text, q_opts = parse_history_question(item['question'])
                        st.session_state.question_data = {
                            "type": q_type,
                            "is_retry": True,
                            "question": q_text,
                            "options": q_opts,
                            "keywords": ["(인공지능이 문맥을 파악하여 자동 채점합니다)"],
                            "hint_step1": ["복습 모드에서는 힌트가 제공되지 않습니다."],
                            "hint_step2": "이전에 정답을 맞혔던 문제입니다. 기억을 되살려 다시 완벽하게 풀어보세요!"
                        }
                        st.session_state.messages = []
                        st.session_state.first_attempt_saved = False
                        st.session_state.is_correct = False
                        st.rerun()
                with col2:
                    if st.button("삭제", key=f"del_btn_correct_{item['id']}"):
                        delete_record(item['id'])
                        st.rerun()
                
        with st.expander(f"🟡 부분점수 ({len(partial_list)}개)"):
            if partial_list:
                if st.button("부분점수 기록 모두 삭제", key="del_all_partial", use_container_width=True):
                    delete_all_by_result("부분점수")
                    st.rerun()
                st.divider()
            for item in partial_list:
                display_q = item['question'].split('\n')[0]
                col1, col2 = st.columns([5, 1])
                with col1:
                    if st.button(f"Q: {display_q}", key=f"retry_partial_{item['id']}", use_container_width=True):
                        q_type, q_text, q_opts = parse_history_question(item['question'])
                        st.session_state.question_data = {
                            "type": q_type,
                            "is_retry": True,
                            "question": q_text,
                            "options": q_opts,
                            "keywords": ["(인공지능이 문맥을 파악하여 자동 채점합니다)"],
                            "hint_step1": ["복습 모드에서는 힌트가 제공되지 않습니다."],
                            "hint_step2": "이전에 아쉽게 부분 점수를 받았던 문제입니다. 완벽한 답을 적어보세요!"
                        }
                        st.session_state.messages = []
                        st.session_state.first_attempt_saved = False
                        st.session_state.is_correct = False
                        st.rerun()
                with col2:
                    if st.button("삭제", key=f"del_btn_partial_{item['id']}"):
                        delete_record(item['id'])
                        st.rerun()
                
        with st.expander(f"🔴 오답 ({len(incorrect_list)}개)"):
            if incorrect_list:
                if st.button("오답 기록 모두 삭제", key="del_all_incorrect", use_container_width=True):
                    delete_all_by_result("오답")
                    st.rerun()
                st.divider()
            for item in incorrect_list:
                display_q = item['question'].split('\n')[0]
                col1, col2 = st.columns([5, 1])
                with col1:
                    if st.button(f"Q: {display_q}", key=f"retry_wrong_{item['id']}", use_container_width=True):
                        q_type, q_text, q_opts = parse_history_question(item['question'])
                        st.session_state.question_data = {
                            "type": q_type,
                            "is_retry": True,
                            "question": q_text,
                            "options": q_opts,
                            "keywords": ["(인공지능이 문맥을 파악하여 자동 채점합니다)"],
                            "hint_step1": ["복습 모드에서는 힌트가 제공되지 않습니다."],
                            "hint_step2": "이전에 틀렸던 문제입니다. 배운 내용을 적용하여 다시 도전해 보세요!"
                        }
                        st.session_state.messages = []
                        st.session_state.first_attempt_saved = False
                        st.session_state.is_correct = False
                        st.rerun()
                with col2:
                    if st.button("삭제", key=f"del_btn_wrong_{item['id']}"):
                        delete_record(item['id'])
                        st.rerun()

# 목차 및 지문 제목 분석 기능
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
                messages=[
                    {"role": "system", "content": sys_instruction},
                    {"role": "user", "content": text[:12000]}
                ],
                response_format={"type": "json_object"},
                max_tokens=2048
            )
            raw_content = response.choices[0].message.content.strip()
            raw_content = raw_content.replace("```json", "").replace("```", "")
            result = json.loads(raw_content, strict=False)
            return result.get("document_title", "일반 학습 자료"), result.get("topics", [])
        except Exception as e:
            st.error(f"분석 오류: {e}")
            return "일반 학습 자료", []

# 문제 출제 기능
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
                    "1. 첫 번째 선택지 내용", 
                    "2. 두 번째 선택지 내용", 
                    "3. 세 번째 선택지 내용", 
                    "4. 네 번째 선택지 내용", 
                    "5. 다섯 번째 선택지 내용"
                ],
                "answer_key": 3,
                "hint_step1": ["개념1", "개념2"],
                "hint_step2": "조언 문장",
                "keywords": []
            }
            """
            
        system_instruction = f"""
        당신은 학습 자료를 바탕으로 학생의 사고력을 기르는 출제자이다.
        아래의 규칙에 따라 문제를 생성한다.
        {mode_instruction}
        {type_instruction}
        """
        
        safe_context = st.session_state.context_data[:12000]
        user_content = f"[학습 자료 내용]\n{safe_context}"
        
        try:
            response = client.chat.completions.create(
                model="solar-1-mini-chat",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"},
                max_tokens=2048
            )
            
            raw_content = response.choices[0].message.content.strip()
            raw_content = raw_content.replace("```json", "").replace("```", "")
            result = json.loads(raw_content, strict=False)
            
            st.session_state.question_data = result
            st.session_state.messages = [] 
            st.session_state.first_attempt_saved = False
            st.session_state.is_correct = False
            st.rerun()
            
        except Exception as e:
            st.error(f"연결 오류가 발생했습니다. (상세 오류: {e})")

# 답변 처리 및 튜터 평가 기능
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
                * 객관식 문제이므로 첫 줄에 반드시 **[평가 결과: 정답]**, **[평가 결과: 오답]** 중 하나만 출력한다. (부분점수는 절대 부여하지 않는다. 정답이 아니면 무조건 오답이다.)
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

# 학습 자료 입력부
st.subheader("학습 자료 입력 및 목차 추출")
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
        st.success("문서 글자 추출 완료")

if st.button("문서 분석 및 목차 추출", type="primary"):
    if not context_text.strip():
        st.error("학습 자료를 먼저 입력해야 합니다.")
    else:
        st.session_state.context_data = context_text
        doc_title, doc_topics = analyze_topics(context_text)
        st.session_state.document_title = doc_title
        st.session_state.topics = doc_topics

# 목차가 추출되었을 때 선택 기능 제공
if st.session_state.topics:
    st.divider()
    selected_topic = st.selectbox("어떤 부분의 문제를 풀어볼까요?", st.session_state.topics)
    
    if st.button("해당 목차로 문제 생성하기"):
        generate_new_question(q_type=q_type_select, mode="initial", topic=selected_topic)

# 문답 진행 및 평가
if st.session_state.question_data:
    q_data = st.session_state.question_data
    
    st.divider()
    st.subheader("개념 검증 문답")
    
    # 지문의 출처/제목 띄움
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
        with st.expander("1단계 힌트 (핵심어 찾기)"):
            st.write(", ".join(q_data.get('hint_step1', ["힌트가 제공되지 않는 모드입니다."])))
    with col_h2:
        with st.expander("2단계 힌트 (방향 및 문장 틀)"):
            st.write(q_data.get('hint_step2', "힌트가 제공되지 않는 모드입니다."))

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
            st.info("튜터의 꼬리 질문에 계속 답변하며 스스로 정답을 찾아보세요! (또는 아래 단추를 눌러 넘어갈 수 있습니다)")
            
        st.markdown("### 다음 학습을 선택하세요")
        col_next1, col_next2 = st.columns(2)
        
        with col_next1:
            if st.button("현재 목차에서 다른 문제 다시 풀기", use_container_width=True):
                generate_new_question(q_type=q_type_select, mode="similar", prev_question=q_data['question'], topic=st.session_state.get('selected_topic', ''))
                
        with col_next2:
            if st.button("현재 목차에서 새로운 개념 문제 풀기", use_container_width=True):
                generate_new_question(q_type=q_type_select, mode="new", prev_question=q_data['question'], topic=st.session_state.get('selected_topic', ''))

    if not st.session_state.is_correct:
        if q_data.get('type') != 'multiple_choice' or st.session_state.first_attempt_saved:
            user_answer = st.chat_input("답변이나 궁금한 점을 튜터에게 말해보세요...")
            if user_answer:
                process_answer(user_answer, q_data)
