import streamlit as st
import os
import glob
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser

# 1. 페이지 설정
st.set_page_config(page_title="Nexus AI", page_icon="🎮", layout="wide")

# ==========================================
# 🔐 [중요] API 키 보안 설정 (Streamlit Cloud용)
# ==========================================
# 로컬에서 돌릴 때나 서버에서 돌릴 때나 알아서 키를 찾도록 설정합니다.
if "GOOGLE_API_KEY" in st.secrets:
    # 서버(Streamlit Cloud)에 저장된 비밀키를 가져옵니다.
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
else:
    # 로컬 환경 변수나 다른 설정이 없다면 경고
    if "GOOGLE_API_KEY" not in os.environ:
        st.warning("⚠️ API 키가 설정되지 않았습니다. Streamlit Secrets에 'GOOGLE_API_KEY'를 등록해주세요.")
        st.stop() # 키 없으면 실행 중단

# 데이터 폴더 경로
DATA_FOLDER = "data"

# ==========================================
# ⚙️ 함수 정의
# ==========================================
@st.cache_resource(show_spinner="Nexus가 데이터를 학습하는 중...")
def load_nexus_knowledge():
    """data 폴더의 모든 txt 파일을 읽어옵니다."""
    combined_text = ""
    file_list = []
    
    # 폴더가 없으면 생성 (에러 방지)
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
        return None, []

    txt_files = glob.glob(os.path.join(DATA_FOLDER, "*.txt"))
    
    for file_path in txt_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                filename = os.path.basename(file_path)
                combined_text += f"\n--- [문서: {filename}] ---\n{f.read()}\n"
                file_list.append(filename)
        except Exception:
            pass
            
    return combined_text, file_list

def get_nexus_chain():
    # 모델 설정
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)
    
    # 페르소나 설정
    system_instruction = """
    당신은 'Nexus'입니다. 리그 오브 레전드 데이터 분석 전문가이자 챌린저 티어 플레이어입니다.
    
    [말투 및 행동 지침]
    1. 당신은 'Nexus'입니다. 아래 제공된 [데이터]를 기반으로 답변하세요.
    2. 이전 대화 흐름을 기억하고, 문맥에 맞게 자연스럽게 대화하세요.
    3. 분석가답게 논리적으로 말하되, 게이머들이 쓰는 용어(너프, 버프, 떡상, 떡락, OP 등)를 자연스럽게 섞어 쓰세요.
    4. 수치 변화(데미지, 쿨타임 등)는 매우 중요하므로 정확하게 언급하세요.
    5. 질문에 대한 답이 데이터에 없다면, 어설프게 지어내지 말고 "그건 데이터에 없는데? 라이엇이 아직 안 알려줬나 봐."라고 솔직하게 말하세요.
    6. 답변 끝에는 항상 도움이 될만한 '한 줄 꿀팁'을 덧붙이세요.
    7. 사용자를 '소환사님'이라고 부르세요.    
    [학습된 데이터]
    {context}
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_instruction),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ])
    
    return prompt | llm | StrOutputParser()

# ==========================================
# 🖥️ 화면 구성
# ==========================================
st.title("🎮 Nexus AI : LoL 패치 분석기")
st.markdown("### 24시간 깨어있는 당신만의 챌린저 코치")

# 사이드바
with st.sidebar:
    st.header("📂 Nexus 지식 저장소")
    context_data, loaded_files = load_nexus_knowledge()
    
    if loaded_files:
        st.success(f"현재 {len(loaded_files)}개의 패치 노트를 분석했습니다.")
        with st.expander("학습된 파일 목록 보기"):
            for f in loaded_files:
                st.caption(f"📄 {f}")
    else:
        st.error("데이터가 없습니다! GitHub 저장소의 'data' 폴더를 확인하세요.")

# 채팅 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "어서와, 소환사! 이번 패치에서 궁금한 게 뭐야?"}]

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [] 

# 대화 내용 출력
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 사용자 입력
if user_input := st.chat_input("질문 입력 (예: 카이사 너프 심해?)"):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        chain = get_nexus_chain()
        with st.spinner("Nexus가 두뇌 풀가동 중..."):
            try:
                response = chain.invoke({
                    "context": context_data if context_data else "데이터 없음",
                    "chat_history": st.session_state.chat_history,
                    "question": user_input
                })
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.chat_history.append(HumanMessage(content=user_input))
                st.session_state.chat_history.append(AIMessage(content=response))
            except Exception as e:
                st.error(f"오류 발생: {e}")
