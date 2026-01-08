import requests
from bs4 import BeautifulSoup
import os
import re
import time

# 데이터 저장 경로
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# 1. 수집할 위키 페이지 목록 (더 필요한 내용이 있으면 여기에 추가하면 됩니다)
TARGET_URLS = {
    "미니언 (Minions)": "https://leagueoflegends.fandom.com/wiki/Minion_(League_of_Legends)",
    "정글링 (Jungling)": "https://leagueoflegends.fandom.com/wiki/Jungling",
    "포탑 (Turrets)": "https://leagueoflegends.fandom.com/wiki/Turret",
    "억제기 (Inhibitor)": "https://leagueoflegends.fandom.com/wiki/Inhibitor",
    "방어구 관통력 (Armor Penetration)": "https://leagueoflegends.fandom.com/wiki/Armor_penetration",
    "마법 관통력 (Magic Penetration)": "https://leagueoflegends.fandom.com/wiki/Magic_penetration",
    "스킬 가속 (Ability Haste)": "https://leagueoflegends.fandom.com/wiki/Ability_Haste",
    "이동 속도 (Movement Speed)": "https://leagueoflegends.fandom.com/wiki/Movement_speed",
    "몬스터 (Monsters)": "https://leagueoflegends.fandom.com/wiki/Monster"
}

def clean_wiki_text(soup):
    """
    Fandom 위키의 지저분한 요소(광고, 네비게이션, 편집 버튼)를 제거하고 
    본문 텍스트만 깔끔하게 추출합니다.
    """
    # 본문 영역 찾기 (Fandom 위키의 본문 클래스)
    content = soup.find('div', {'class': 'mw-parser-output'})
    
    if not content:
        return "본문을 찾을 수 없습니다."

    # 불필요한 태그 제거 (광고, 표의 불필요한 행, 주석 등)
    for tag in content(["script", "style", "nav", "figure", "aside", "noscript"]):
        tag.decompose()
        
    # '편집' 버튼 텍스트 제거 ([Edit])
    for tag in content.find_all(class_="mw-editsection"):
        tag.decompose()

    # 텍스트 추출 및 공백 정리
    text = content.get_text(separator="\n")
    
    # 너무 많은 빈 줄 제거 (3줄 이상 빈 줄은 2줄로)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

def fetch_mechanics():
    print("📚 LoL 게임 메커니즘(Wiki) 데이터 수집 시작...")
    
    save_path = os.path.join(DATA_DIR, "base_lol_mechanics.txt")
    
    # 헤더 작성 (브라우저인 척 속이기)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    with open(save_path, "w", encoding="utf-8") as f:
        f.write("=== [LoL 게임 메커니즘 및 공식 모음] ===\n")
        f.write("출처: League of Legends Fandom Wiki\n")
        f.write("이 데이터는 게임의 규칙, 공식, AI(미니언/포탑) 행동 패턴을 담고 있습니다.\n\n")

        total = len(TARGET_URLS)
        count = 0

        for title, url in TARGET_URLS.items():
            count += 1
            print(f"[{count}/{total}] 🕸️ 수집 중: {title}...")
            
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                cleaned_text = clean_wiki_text(soup)
                
                # 파일에 기록
                f.write(f"\n{'='*40}\n")
                f.write(f"## {title}\n")
                f.write(f"원본 링크: {url}\n")
                f.write(f"{'='*40}\n\n")
                f.write(cleaned_text)
                f.write("\n\n")
                
                print(f"   ✅ 완료 ({len(cleaned_text)}자)")
                
                # 너무 빠르게 요청하면 차단될 수 있으니 1초 휴식
                time.sleep(1)

            except Exception as e:
                print(f"   ❌ 실패: {e}")
                f.write(f"\n## {title} (수집 실패)\n에러: {e}\n\n")

    print(f"\n🎉 모든 메커니즘 데이터 저장 완료: {save_path}")
    print("   이제 Nexus가 '방관 30%면 방어력 얼마 무시해?' 같은 질문을 이해합니다!")

if __name__ == "__main__":
    fetch_mechanics()
