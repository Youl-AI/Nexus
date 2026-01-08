import streamlit as st
import os
import glob
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser

# ==========================================
# 1. 페이지 설정 및 스타일
# ==========================================
st.set_page_config(page_title="Nexus AI", page_icon="🎮", layout="wide")

# 스타일 커스텀 (탭 디자인)
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff;
        border-bottom: 2px solid #ff4b4b;
    }
</style>
""", unsafe_allow_html=True)

# API 키 설정
if "GOOGLE_API_KEY" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]

DATA_FOLDER = "data"

# ==========================================
# 2. 데이터 로딩 (버그 수정 포함)
# ==========================================
@st.cache_resource(show_spinner="Nexus가 데이터를 분류하여 학습 중입니다...")
def load_split_knowledge():
    """
    data 폴더의 파일들을 'lol'과 'tft' 키워드로 분류하여 로드합니다.
    """
    lol_context = ""
    tft_context = ""
    
    if not os.path.exists(DATA_FOLDER):
        # [수정됨] 받는 변수가 4개이므로, 리턴값도 4개로 맞춰야 에러가 안 납니다.
        return "", "", 0, 0 

    txt_files = glob.glob(os.path.join(DATA_FOLDER, "*.txt"))
    
    lol_count = 0
    tft_count = 0

    for file_path in txt_files:
        filename = os.path.basename(file_path).lower()
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                formatted_content = f"\n--- [문서: {filename}] ---\n{content}\n"
                
                if "lol" in filename:
                    lol_context += formatted_content
                    lol_count += 1
                elif "tft" in filename:
                    tft_context += formatted_content
                    tft_count += 1
                else:
                    lol_context += formatted_content
                    tft_context += formatted_content
        except Exception:
            pass
            
    return lol_context, tft_context, lol_count, tft_count

lol_data, tft_data, lol_files, tft_files = load_split_knowledge()

def get_chain(mode="lol"):
    """
    mode에 따라 페르소나를 설정하여 체인을 반환합니다.
    """
    # [복구 완료] 사용자님이 원하신 2.5 버전
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)
    
    if mode == "lol":
        role_desc = "당신은 'Nexus'입니다. 소환사의 협곡(LoL) 전문 분석가이자 챌린저입니다."
    else:
        role_desc = "당신은 'Nexus'입니다. 전략적 팀 전투(TFT) 전문 분석가이자 랭커입니다."

    system_instruction = f"""
    {role_desc}
    
    [말투 및 행동 지침]
    1. 당신은 'Nexus'입니다. 아래 제공된 [데이터]를 기반으로 답변하세요.
    2. 이전 대화 흐름을 기억하고, 문맥에 맞게 자연스럽게 대화하세요.
    3. 분석가답게 논리적으로 말하되, 게이머들이 쓰는 용어(너프, 버프, 떡상, 떡락, OP 등)를 자연스럽게 섞어 쓰세요.
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
# 3. 사이드바 UI (사용자 스타일 복구)
# ==========================================
with st.sidebar:
    st.title("🎮 Nexus System")
    st.markdown("---")
    
    # [복구 완료] 사용자님이 작성하신 st.success 유지
    st.success("System Online")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="LoL Data", value=f"{lol_files}개")
    with col2:
        st.metric(label="TFT Data", value=f"{tft_files}개")
        
    st.markdown("---")
    st.caption("Tip: 질문하려는 게임 탭을 선택하세요.")


# ==========================================
# 4. 메인 채팅 UI (잔상/레이아웃 해결 로직 적용)
# ==========================================
st.title("Nexus AI Analysis")

tab1, tab2 = st.tabs(["⚔️ League of Legends", "♟️ Teamfight Tactics"])

# --- [Tab 1] LoL 채팅 ---
with tab1:
    st.subheader("소환사의 협곡 분석실")
    
    if "messages_lol" not in st.session_state:
        st.session_state.messages_lol = [{"role": "assistant", "content": "협곡에 오신 것을 환영합니다! 챔피언, 아이템, 룬 무엇이든 물어보세요."}]
    if "history_lol" not in st.session_state:
        st.session_state.history_lol = []

    # 1. 대화 기록 먼저 출력
    for msg in st.session_state.messages_lol:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 2. 입력창 하단 고정
    if prompt_lol := st.chat_input("LoL 질문 입력 (예: 가렌 버프됨?)", key="input_lol"):
        with st.chat_message("user"):
            st.markdown(prompt_lol)
        st.session_state.messages_lol.append({"role": "user", "content": prompt_lol})

        with st.chat_message("assistant"):
            chain = get_chain(mode="lol")
            with st.spinner("미니언 데이터 분석 중..."):
                try:
                    response = chain.invoke({
                        "context": lol_data,
                        "chat_history": st.session_state.history_lol,
                        "question": prompt_lol
                    })
                    st.markdown(response)
                    st.session_state.messages_lol.append({"role": "assistant", "content": response})
                    st.session_state.history_lol.append(HumanMessage(content=prompt_lol))
                    st.session_state.history_lol.append(AIMessage(content=response))
                except Exception as e:
                    st.error(f"분석 실패: {e}")


# --- [Tab 2] TFT 채팅 ---
with tab2:
    st.subheader("전략적 팀 전투 연구소")

    if "messages_tft" not in st.session_state:
        st.session_state.messages_tft = [{"role": "assistant", "content": "반갑습니다, 전략가님! 이번 시즌 꿀덱이나 증강체가 궁금하신가요?"}]
    if "history_tft" not in st.session_state:
        st.session_state.history_tft = []

    # 1. 대화 기록 먼저 출력
    for msg in st.session_state.messages_tft:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 2. 입력창 하단 고정
    if prompt_tft := st.chat_input("TFT 질문 입력 (예: 16시즌 4코스트 기물 알려줘)", key="input_tft"):
        with st.chat_message("user"):
            st.markdown(prompt_tft)
        st.session_state.messages_tft.append({"role": "user", "content": prompt_tft})

        with st.chat_message("assistant"):
            chain = get_chain(mode="tft")
            with st.spinner("리롤 확률 계산 중..."):
                try:
                    response = chain.invoke({
                        "context": tft_data,
                        "chat_history": st.session_state.history_tft,
                        "question": prompt_tft
                    })
                    st.markdown(response)
                    st.session_state.messages_tft.append({"role": "assistant", "content": response})
                    st.session_state.history_tft.append(HumanMessage(content=prompt_tft))
                    st.session_state.history_tft.append(AIMessage(content=response))
                except Exception as e:
                    st.error(f"분석 실패: {e}")
