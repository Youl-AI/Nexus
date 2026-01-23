import requests
from bs4 import BeautifulSoup
import os
import re

# 1. 데이터 저장 폴더
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def clean_filename(title):
    # 윈도우 파일명 금지 문자 제거
    cleaned = re.sub(r'[\\/*?:"<>|]', "", title)
    
    # 양쪽 공백 제거 후, 중간 공백(띄어쓰기, 탭 등)을 모두 언더바(_)로 변경
    # \s+ 는 "하나 이상의 공백"을 의미합니다.
    cleaned = re.sub(r'\s+', '_', cleaned.strip())
    
    return cleaned

def crawl_url(target_url):    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(target_url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 제목 가져오기
        raw_title = soup.title.string if soup.title else "untitled_page"
        
        # 본문 추출 전 불필요한 태그 제거
        for script in soup(["script", "style", "nav", "footer", "header", "iframe"]):
            script.decompose()
            
        text_content = soup.get_text(separator="\n", strip=True)

        # 파일명 변환 적용
        safe_title = clean_filename(raw_title)
        
        # 파일 저장
        file_path = os.path.join(DATA_DIR, f"{safe_title}.txt")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"URL: {target_url}\n")
            f.write(f"Original Title: {raw_title}\n")
            f.write("-" * 30 + "\n")
            f.write(text_content)
            
        print(f"저장 완료 -> {file_path}")

    except Exception as e:
        print(f"크롤링 실패: {e}")

if __name__ == "__main__":
    print("=== Nexus Web Crawler===")
    print("URL을 입력하면 내용을 '제목_공백_제거.txt'로 저장합니다.")
    print("('q' 입력 시 종료)")
    
    while True:
        url = input("\nURL 입력 >> ")
        
        if url.lower() in ['q', 'quit', 'exit']:
            break
            
        if not url.startswith("http"):
            print("URL은 http/https로 시작해야 합니다.")
            continue
            
        crawl_url(url)
