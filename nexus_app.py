import streamlit as st
import os
import glob
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser

# ==========================================
# 1. 페이지 기본 설정
# ==========================================
st.set_page_config(page_title="Nexus AI", page_icon="🎮", layout="wide")

# 스타일 커스텀
st.markdown("""
<style>
    /* 채팅 메시지 가독성 확보 */
    .stChatMessage { margin-bottom: 10px; }
    /* 헤더 스타일 */
    .main-header { font-size: 2rem; font-weight: bold; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

# API 키 설정
if "GOOGLE_API_KEY" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]

DATA_FOLDER = "data"

# ==========================================
# 2. 데이터 로딩 및 AI 설정
# ==========================================
@st.cache_resource(show_spinner="Nexus가 데이터를 분류하여 학습 중입니다...")
def load_split_knowledge():
    """data 폴더의 파일을 읽어 LoL과 TFT용 컨텍스트로 분리"""
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
    """mode에 따라 AI의 페르소나 분리"""
    # 2.5 버전 사용
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
        사용자를 **'전략가님'**이라고 부르세요. ('소환사' 호칭 금지)
        협곡(LoL) 관련 내용은 무시하세요.
        챔피언을 '기물'로 칭하고 덱 구성, 증강체, 배치를 중심으로 설명하세요.
        """

    system_instruction = f"""
    {role_desc}
    
    [행동 지침]
    1. 당신은 'Nexus'입니다. 아래 [데이터]를 기반으로 답변하세요.
    2. 이전 대화 흐름을 기억하고 자연스럽게 대화하세요.
    3. '너프', '버프', 'OP', '순방' 등 게이머 용어를 적절히 사용하세요.
    4. 수치 변화는 정확하게 언급하세요.
    5. 데이터에 없는 내용은 "데이터에 없다"고 솔직히 말하세요.
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
# 3. 사이드바 UI (게임 모드 선택)
# ==========================================
with st.sidebar:
    st.title("🎮 Nexus System")
    st.markdown("---")
    
    # 탭 대신 라디오 버튼 사용 (잔상 해결의 핵심)
    selected_game = st.radio(
        "분석할 게임 모드",
        ["League of Legends", "Teamfight Tactics"],
        index=0
    )
    
    st.markdown("---")
    
    # 데이터 현황 표시
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="LoL Data", value=f"{lol_files}개")
    with col2:
        st.metric(label="TFT Data", value=f"{tft_files}개")
        
    st.success("System Online")


# ==========================================
# 4. 메인 UI 로직
# ==========================================
st.title("Nexus AI Analysis")

# ------------------------------------------
# CASE 1: League of Legends
# ------------------------------------------
if selected_game == "League of Legends":
    st.subheader("⚔️ 소환사의 협곡 분석실")
    
    # 세션 초기화
    if "messages_lol" not in st.session_state:
        st.session_state.messages_lol = [{"role": "assistant", "content": "협곡에 오신 것을 환영합니다, 소환사님! 무엇을 분석해 드릴까요?"}]
    if "history_lol" not in st.session_state:
        st.session_state.history_lol = []

    # 1. 채팅 컨테이너 (대화 기록 출력)
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages_lol:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # 2. 입력창 및 로직 (rerun 제거됨)
    if prompt := st.chat_input("LoL 질문 입력 (예: 가렌 버프됨?)", key="input_lol"):
        
        # (1) 사용자 메시지 즉시 표시
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
        st.session_state.messages_lol.append({"role": "user", "content": prompt})

        # (2) AI 답변 생성 및 표시
        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("미니언 데이터 분석 중..."):
                    try:
                        chain = get_chain(mode="lol")
                        response = chain.invoke({
                            "context": lol_data,
                            "chat_history": st.session_state.history_lol,
                            "question": prompt
                        })
                        st.markdown(response)
                        
                        # (3) 대화 기록 저장
                        st.session_state.messages_lol.append({"role": "assistant", "content": response})
                        st.session_state.history_lol.append(HumanMessage(content=prompt))
                        st.session_state.history_lol.append(AIMessage(content=response))
                        
                    except Exception as e:
                        st.error(f"오류 발생: {e}")

# ------------------------------------------
# CASE 2: Teamfight Tactics
# ------------------------------------------
else:
    st.subheader("♟️ 전략적 팀 전투 연구소")
    
    # 세션 초기화
    if "messages_tft" not in st.session_state:
        st.session_state.messages_tft = [{"role": "assistant", "content": "반갑습니다, 전략가님! 이번 시즌 꿀덱을 찾아드릴까요?"}]
    if "history_tft" not in st.session_state:
        st.session_state.history_tft = []

    # 1. 채팅 컨테이너
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages_tft:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # 2. 입력창 및 로직 (rerun 제거됨)
    if prompt := st.chat_input("TFT 질문 입력 (예: 징크스 3신기 알려줘)", key="input_tft"):
        
        # (1) 사용자 메시지 즉시 표시
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
        st.session_state.messages_tft.append({"role": "user", "content": prompt})

        # (2) AI 답변 생성 및 표시
        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("리롤 확률 계산 중..."):
                    try:
                        chain = get_chain(mode="tft")
                        response = chain.invoke({
                            "context": tft_data,
                            "chat_history": st.session_state.history_tft,
                            "question": prompt
                        })
                        st.markdown(response)
                        
                        # (3) 대화 기록 저장
                        st.session_state.messages_tft.append({"role": "assistant", "content": response})
                        st.session_state.history_tft.append(HumanMessage(content=prompt))
                        st.session_state.history_tft.append(AIMessage(content=response))
                        
                    except Exception as e:
                        st.error(f"오류 발생: {e}")
