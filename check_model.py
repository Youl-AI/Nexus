# --- [긴급 패치] 한글 에러 방지 (이건 필수입니다) ---
import httpx._models
_original_normalize = httpx._models._normalize_header_value
def patched_normalize_header_value(value, encoding):
    try:
        return _original_normalize(value, encoding)
    except UnicodeEncodeError:
        return value.encode("utf-8")
httpx._models._normalize_header_value = patched_normalize_header_value
# --------------------------------------------------

import os
import google.generativeai as genai

# 1. 여기에 API 키를 넣어주세요
os.environ["GOOGLE_API_KEY"] = "AIzaSyByNojTOejCB6ylHAKdhJ9jiKHOlN7jvfk"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

print("📡 구글 서버에 접속하여 사용 가능한 모델을 조회합니다...\n")

try:
    # 모델 목록 조회
    count = 0
    for m in genai.list_models():
        # 'generateContent' (대화 기능)를 지원하는 모델만 출력
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ 발견된 모델: {m.name}")
            count += 1
            
    if count == 0:
        print("❌ 사용 가능한 모델이 하나도 없습니다! API 키 권한을 확인해주세요.")
    else:
        print(f"\n총 {count}개의 모델을 찾았습니다. 위 이름 중 하나를 골라 쓰면 됩니다!")

except Exception as e:
    print(f"❌ 접속 실패: {e}")
    print("\n[진단 팁]")
    print("1. 'API key not valid' -> 키를 잘못 복사했거나 삭제된 키입니다.")
    print("2. 'User location is not supported' -> 현재 국가(IP)에서 차단되었습니다.")
