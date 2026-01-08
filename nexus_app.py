import streamlit as st
import os
import glob
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser

# ==========================================
# 1. 페이지 설정 및 CSS (사이드바 너비 조절 포함)
# ==========================================
st.set_page_config(page_title="Nexus AI", page_icon="✨", layout="wide")

st.markdown("""
<style>
    /* [핵심 추가] 사이드바 초기 너비 고정 */
    section[data-testid="stSidebar"] {
        min-width: 200px !important; /* 최소 너비를 350px로 강제 설정 (글자 안 짤리게) */
    }

    /* 1. 라디오 버튼의 '동그라미' 아이콘 숨기기 */
    div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }

    /* 2. 라디오 버튼 스타일 (목록 메뉴처럼) */
    div[role="radiogroup"] label {
        padding: 12px 15px !important;
        border-radius: 8px !important;
        margin-bottom: 8px !important;
        border: 1px solid transparent;
        transition: all 0.2s ease;
        white-space: nowrap; /* 글자가 절대 줄바꿈 되지 않게 설정 */
    }

    /* 3. 마우스 호버 효과 */
    div[role="radiogroup"] label:hover {
        background-color: #f0f2f6 !important;
        cursor: pointer;
    }

    /* 4. 선택된 항목 스타일 */
    div[role="radiogroup"] label:has(input:checked) {
        background-color: #e8f0fe !important;
        color: #1967d2 !important;
        font-weight: 600 !important;
    }

    /* 채팅 메시지 간격 */
    .stChatMessage { margin-bottom: 10px; }
    
    /* 헤더/푸터 숨김 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# API 키 설정
if "GOOGLE_API_KEY" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]

DATA_FOLDER = "data"

# ==========================================
# 2. 데이터 로딩 (기존 로직 유지)
# ==========================================
@st.cache_resource(show_spinner="Nexus 엔진 가동 중...")
def load_split_knowledge():
    lol_context = ""
    tft_context = ""
    
    if not os.path.exists(DATA_FOLDER):
        return "", "", 0, 0 

    txt_files = glob.glob(os.path.join(DATA_FOLDER, "*.txt"))
    lol_count = 0
    tft_count = 0

    for file_path in txt_files:
        filename = os.path.basename(file_path).lower()
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                formatted = f"\n--- [문서: {filename}] ---\n{content}\n"
                
                if "lol" in filename:
                    lol_context += formatted
                    lol_count += 1
                elif "tft" in filename:
                    tft_context += formatted
                    tft_count += 1
                else:
                    lol_context += formatted
                    tft_context += formatted
        except Exception:
            pass
            
    return lol_context, tft_context, lol_count, tft_count

lol_data, tft_data, lol_files, tft_files = load_split_knowledge()

def get_chain(mode="lol"):
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)
    
    if mode == "lol":
        role_desc = """
        당신은 'Nexus'입니다. **소환사의 협곡(LoL) 전문 분석가**입니다.
        사용자를 **'소환사님'**이라고 부르세요.
        TFT 관련 내용은 모른다고 답하세요.
        챔피언 스킬, 룬, 아이템 빌드를 협곡 기준으로 설명하세요.
        """
    else:
        role_desc = """
        당신은 'Nexus'입니다. **전략적 팀 전투(TFT) 전문 분석가**입니다.
        사용자를 **'전략가님'**이라고 부르세요.
        협곡(LoL) 관련 내용은 무시하세요.
        챔피언을 '기물'로 칭하고 덱 구성, 증강체, 배치를 중심으로 설명하세요.
        아이템 추천은 항상 '찬란한', '유물' 아이템을 제외한 기본 아이템으로 추천하세요.
        """

    system_instruction = f"""
    {role_desc}
    
    [행동 지침]
    1. 데이터를 기반으로 전문적이고 논리적인 답변을 하세요.
    2. 이전 대화 흐름을 기억하고, 문맥에 맞게 자연스럽게 대화하세요.
    3. 게이머 은어(너프, 버프, OP, 삼신기, 순방 등)를 자연스럽게 섞어 쓰세요.
    4. 수치 변화(데미지, 쿨타임 등)는 정확하게 언급하세요.
    5. 모르는 내용은 솔직하게 데이터에 없다고 말하세요.
    6. 답변 끝에 '한 줄 꿀팁'을 추가하세요.
    
    [학습된 데이터]
    {{context}}
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_instruction),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ])
    
    return prompt | llm | StrOutputParser()


# ==========================================
# 3. 사이드바 UI
# ==========================================
with st.sidebar:
    st.title("Nexus AI")
    st.caption("Game Data Analysis")
    st.markdown("---")
    
    # 메뉴 선택
    selected_mode = st.radio(
        "내 프로젝트",
        ["소환사의 협곡 (LoL)", "전략적 팀 전투 (TFT)"],
        index=0,
        key="navigation",
        label_visibility="collapsed"
    )
    
    # 여백 추가
    st.markdown("<br>" * 5, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown(f"**📂 데이터베이스**")
    st.caption(f"• LoL 문서: {lol_files}개")
    st.caption(f"• TFT 문서: {tft_files}개")


# ==========================================
# 4. 메인 화면 로직
# ==========================================

if "LoL" in selected_mode:
    current_mode = "lol"
    header_text = "⚔️ 소환사의 협곡 분석실"
    input_placeholder = "LoL 질문 입력 (예: 가렌 버프됨?)"
    context_data = lol_data
    msg_key = "messages_lol"
    hist_key = "history_lol"
    initial_msg = "협곡에 오신 것을 환영합니다, 소환사님! 무엇을 분석해 드릴까요?"

else: # TFT
    current_mode = "tft"
    header_text = "♟️ 전략적 팀 전투 연구소"
    input_placeholder = "TFT 질문 입력 (예: 징크스 3신기 알려줘)"
    context_data = tft_data
    msg_key = "messages_tft"
    hist_key = "history_tft"
    initial_msg = "반갑습니다, 전략가님! 이번 시즌 꿀덱을 찾아드릴까요?"


# 세션 초기화
if msg_key not in st.session_state:
    st.session_state[msg_key] = [{"role": "assistant", "content": initial_msg}]
if hist_key not in st.session_state:
    st.session_state[hist_key] = []


# 메인 UI
st.subheader(header_text)

# 채팅 기록 출력
for msg in st.session_state[msg_key]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 입력창
if prompt := st.chat_input(input_placeholder):
    
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state[msg_key].append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Nexus가 분석 중입니다..."):
            try:
                chain = get_chain(mode=current_mode)
                response = chain.invoke({
                    "context": context_data,
                    "chat_history": st.session_state[hist_key],
                    "question": prompt
                })
                st.markdown(response)
                
                st.session_state[msg_key].append({"role": "assistant", "content": response})
                st.session_state[hist_key].append(HumanMessage(content=prompt))
                st.session_state[hist_key].append(AIMessage(content=response))
                
            except Exception as e:
                st.error(f"오류 발생: {e}")
