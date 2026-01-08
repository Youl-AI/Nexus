import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# 데이터 저장 폴더
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def get_dynamic_content(url):
    print(f"🌍 접속 중... {url}")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless") # 화면 없이 실행
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # 봇 탐지 우회용 헤더
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        driver.get(url)
        time.sleep(5) # 데이터 로딩 대기
        return driver.page_source
    except Exception as e:
        print(f"❌ 접속 실패: {e}")
        return None
    finally:
        driver.quit()

def parse_exp_gold_data(html):
    if not html: return

    soup = BeautifulSoup(html, 'html.parser')
    
    # 롤체지지 가이드 페이지의 본문 영역 찾기
    # (일반적으로 main 태그나 특정 클래스 안에 있음)
    guide_content = soup.find('div', {'class': 'guide-exp'}) # 클래스명은 바뀔 수 있어 전체 텍스트 기반으로 찾음
    
    # 만약 특정 div를 못 찾으면 전체 body에서 텍스트 추출 (안전장치)
    target_area = guide_content if guide_content else soup.body

    # 불필요한 스크립트 제거
    for tag in target_area(["script", "style", "nav", "footer", "header", "iframe", "svg"]):
        tag.decompose()

    # 텍스트 정제 (표 구조를 유지하기 위해 줄바꿈 처리)
    text_content = target_area.get_text(separator="\n", strip=True)

    # 파일 저장
    save_path = os.path.join(DATA_DIR, "base_tft_economy.txt")
    
    with open(save_path, "w", encoding="utf-8") as f:
        f.write("=== [TFT 경제 시스템: 경험치 및 골드] ===\n")
        f.write(f"출처: https://lolchess.gg/guide/exp (수집일: {time.strftime('%Y-%m-%d')})\n")
        f.write("이 데이터는 레벨업 타이밍과 이자 관리에 대한 핵심 규칙입니다.\n")
        f.write("-" * 40 + "\n\n")
        
        # 긁어온 텍스트를 그대로 넣되, 보기 좋게 정리
        # (롤체지지는 텍스트가 순서대로 잘 나열되어 있어 그대로 써도 무방합니다)
        f.write(text_content)

    print(f"✅ 저장 완료: {save_path}")
    print("   이제 Nexus가 '8렙 가려면 경험치 얼마 필요해?' 같은 질문에 답할 수 있습니다!")

if __name__ == "__main__":
    url = "https://lolchess.gg/guide/exp"
    html = get_dynamic_content(url)
    parse_exp_gold_data(html)
