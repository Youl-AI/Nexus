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

# 스타일 커스텀: 탭 디자인 및 채팅창 간격 조정
st.markdown("""
<style>
    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; white-space: pre-wrap; background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px; gap: 1px; padding-top: 10px; padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff; border-bottom: 2px solid #ff4b4b;
    }
    /* 채팅 메시지 간격 */
    .stChatMessage { margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# API 키 설정 (Streamlit Secrets 사용 권장)
if "GOOGLE_API_KEY" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]

DATA_FOLDER = "data"

# ==========================================
# 2. 데이터 로딩 및 AI 설정
# ==========================================
@st.cache_resource(show_spinner="Nexus가 데이터를 분류하여 학습 중입니다...")
def load_split_knowledge():
    """
    data 폴더의 파일을 읽어 LoL과 TFT용 컨텍스트로 분리합니다.
    """
    lol_context = ""
    tft_context = ""
    
    # 폴더가 없으면 빈 값 반환
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
                
                # 파일명에 따른 데이터 분배
                if "lol" in filename:
                    lol_context += formatted
                    lol_count += 1
                elif "tft" in filename:
                    tft_context += formatted
                    tft_count += 1
                else:
                    # 분류 안 된 파일은 양쪽에 모두 포함
                    lol_context += formatted
                    tft_context += formatted
        except Exception:
            pass
            
    return lol_context, tft_context, lol_count, tft_count

# 데이터 로드
lol_data, tft_data, lol_files, tft_files = load_split_knowledge()

def get_chain(mode="lol"):
    """
    mode에 따라 AI의 말투와 지식을 완전히 분리합니다.
    """
    # [중요] 사용하시려던 gemini-2.5-flash 모델 사용
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)
    
    if mode == "lol":
        role_desc = """
        당신은 'Nexus'입니다. **소환사의 협곡(LoL) 전문 분석가**입니다.
        사용자를 **'소환사님'**이라고 부르세요.
        TFT(전략적 팀 전투) 관련 내용은 모른다고 답하세요.
        챔피언의 스킬, 룬, 아이템 빌드를 협곡 기준으로 설명하세요.
        """
    else:
        role_desc = """
        당신은 'Nexus'입니다. **전략적 팀 전투(TFT) 전문 분석가**입니다.
        사용자를 **'전략가님'**이라고 부르세요. (절대 '소환사'라고 부르지 마세요)
        소환사의 협곡(LoL) 관련 내용은 무시하세요.
        챔피언을 '기물' 또는 '유닛'으로 칭하고, 덱 구성, 증강체, 배치를 중심으로 설명하세요.
        징크스, 가렌 같은 캐릭터가 나와도 **반드시 TFT 시즌 데이터**를 기준으로 설명하세요.
        """

    system_instruction = f"""
    {role_desc}
    
    [행동 지침]
    [말투 및 행동 지침]
    1. 당신은 'Nexus'입니다. 아래 제공된 [데이터]를 기반으로 답변하세요.
    2. 이전 대화 흐름을 기억하고, 문맥에 맞게 자연스럽게 대화하세요.
    3. 분석가답게 논리적으로 말하되, 게이머들이 쓰는 용어(너프, 버프, 떡상, 떡락, OP, 삼신기, 순방 등)를 자연스럽게 섞어 쓰세요.
    4. 수치 변화(데미지, 쿨타임 등)는 매우 중요하므로 정확하게 언급하세요.
    5. 질문에 대한 답이 데이터에 없다면, 어설프게 지어내지 말고 "그건 데이터에 없는데? 라이엇이 아직 안 알려줬나 봐."라고 솔직하게 말하세요.
    6. 답변 끝에는 항상 도움이 될만한 '한 줄 꿀팁'을 덧붙이세요.
    7. 사용자를 '소환사님'이라고 부르세요.
    
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
    st.title("🎮 Nexus System")
    st.markdown("---")
    st.success("System Online")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="LoL Data", value=f"{lol_files}개")
    with col2:
        st.metric(label="TFT Data", value=f"{tft_files}개")
        
    st.markdown("---")
    st.caption("Tip: 질문하려는 게임 탭을 선택하세요.")


# ==========================================
# 4. 메인 UI (레이아웃 문제 해결 적용)
# ==========================================
st.title("Nexus AI Analysis")

tab1, tab2 = st.tabs(["⚔️ League of Legends", "♟️ Teamfight Tactics"])

# --- [Tab 1] LoL 채팅 ---
with tab1:
    st.subheader("소환사의 협곡 분석실")
    
    if "messages_lol" not in st.session_state:
        st.session_state.messages_lol = [{"role": "assistant", "content": "협곡에 오신 것을 환영합니다, 소환사님! 무엇을 분석해 드릴까요?"}]
    if "history_lol" not in st.session_state:
        st.session_state.history_lol = []

    # [핵심 변경 1] 채팅창 컨테이너를 미리 만듭니다. (입력창보다 무조건 위에 위치함)
    chat_container_lol = st.container()

    # [핵심 변경 2] 기존 대화 내용을 컨테이너 안에 그립니다.
    with chat_container_lol:
        for msg in st.session_state.messages_lol:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # [핵심 변경 3] 입력창은 컨테이너 밖(아래)에 배치
    if prompt_lol := st.chat_input("LoL 질문 입력 (예: 가렌 버프됨?)", key="input_lol"):
        
        # 1. 사용자 질문 표시 (컨테이너 안에)
        with chat_container_lol:
            with st.chat_message("user"):
                st.markdown(prompt_lol)
        st.session_state.messages_lol.append({"role": "user", "content": prompt_lol})

        # 2. AI 답변 생성 (컨테이너 안에)
        with chat_container_lol:
            with st.chat_message("assistant"):
                with st.spinner("미니언 데이터 분석 중..."):
                    try:
                        chain = get_chain(mode="lol")
                        response = chain.invoke({
                            "context": lol_data,
                            "chat_history": st.session_state.history_lol,
                            "question": prompt_lol
                        })
                        st.markdown(response)
                        
                        # 기록 저장
                        st.session_state.messages_lol.append({"role": "assistant", "content": response})
                        st.session_state.history_lol.append(HumanMessage(content=prompt_lol))
                        st.session_state.history_lol.append(AIMessage(content=response))
                    except Exception as e:
                        st.error(f"분석 중 오류 발생: {e}")


# --- [Tab 2] TFT 채팅 ---
with tab2:
    st.subheader("전략적 팀 전투 연구소")

    if "messages_tft" not in st.session_state:
        st.session_state.messages_tft = [{"role": "assistant", "content": "반갑습니다, 전략가님! 이번 시즌 꿀덱을 찾아드릴까요?"}]
    if "history_tft" not in st.session_state:
        st.session_state.history_tft = []

    # [핵심 변경] TFT용 채팅 컨테이너 생성
    chat_container_tft = st.container()

    # 대화 내용 출력
    with chat_container_tft:
        for msg in st.session_state.messages_tft:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # 입력창
    if prompt_tft := st.chat_input("TFT 질문 입력 (예: 징크스 3신기 알려줘)", key="input_tft"):
        
        # 1. 사용자 질문
        with chat_container_tft:
            with st.chat_message("user"):
                st.markdown(prompt_tft)
        st.session_state.messages_tft.append({"role": "user", "content": prompt_tft})

        # 2. AI 답변
        with chat_container_tft:
            with st.chat_message("assistant"):
                with st.spinner("리롤 확률 계산 중..."):
                    try:
                        # [핵심] mode="tft"를 확실하게 전달
                        chain = get_chain(mode="tft")
                        response = chain.invoke({
                            "context": tft_data,
                            "chat_history": st.session_state.history_tft,
                            "question": prompt_tft
                        })
                        st.markdown(response)
                        
                        # 기록 저장
                        st.session_state.messages_tft.append({"role": "assistant", "content": response})
                        st.session_state.history_tft.append(HumanMessage(content=prompt_tft))
                        st.session_state.history_tft.append(AIMessage(content=response))
                    except Exception as e:
                        st.error(f"분석 중 오류 발생: {e}")
