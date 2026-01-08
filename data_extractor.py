import requests
import json
import os

# 데이터 저장 경로
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def fetch_tft_set16_exact_match():
    print("📥 TFT 데이터 요청 중...")
    
    url = "https://raw.communitydragon.org/latest/cdragon/tft/ko_kr.json"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        save_path = os.path.join(DATA_DIR, "season_tft_set16.txt")
        
        # 원하는 정확한 코드명 정의
        TARGET_MUTATOR = "TFTSet16"
        
        found_target = False

        with open(save_path, "w", encoding="utf-8") as f:
            f.write(f"=== [TFT {TARGET_MUTATOR} 전용 데이터] ===\n")
            f.write("이 파일은 16시즌 데이터만 포함합니다.\n\n")

            sets = data.get('setData', [])
            
            print(f"\n🔎 '{TARGET_MUTATOR}' 찾는 중...\n")
            
            for game_set in sets:
                mutator = game_set.get('mutator', '')
                name = game_set.get('name', '')
                
                # "TFTSet16" 글자와 똑같은지 비교
                if mutator == TARGET_MUTATOR:
                    found_target = True
                    print(f"✅ [저장함] 발견! 코드명: {mutator} (이름: {name})")
                    
                    f.write(f"## [세트 정보: {name}]\n")
                    f.write(f"코드명: {mutator}\n\n")
                    
                    # --- 1. 시너지 (Traits) ---
                    f.write(f"### 1. 시너지 (Traits)\n")
                    traits = game_set.get('traits', [])
                    for trait in traits:
                        t_name = trait.get('name')
                        t_desc = (trait.get('desc') or "").replace('<br>', ' ')
                        
                        if t_name:
                            f.write(f"- {t_name}: {t_desc}\n")
                            
                            # 활성 효과
                            effects = trait.get('effects', [])
                            if effects:
                                counts = [str(e.get('minUnits')) for e in effects]
                                if counts:
                                    f.write(f"  (구간: {', '.join(counts)})\n")
                    f.write("\n")

                    # --- 2. 챔피언 (Champions) ---
                    f.write(f"### 2. 챔피언 (Champions)\n")
                    champions = game_set.get('champions', [])
                    for champ in champions:
                        c_name = champ.get('name')
                        c_cost = champ.get('cost')
                        c_traits = champ.get('traits', [])
                        ability = champ.get('ability', {})
                        c_skill = (ability.get('desc') or "").replace('<br>', ' ')

                        if c_name:
                            f.write(f"- {c_name} ({c_cost}코스트)\n")
                            f.write(f"  계열/직업: {', '.join(c_traits)}\n")
                            f.write(f"  스킬: {c_skill}\n\n")
                            
                else:
                    print(f"❌ [제외함] 코드명: {mutator}")
                    continue

            if not found_data:
                print(f"\n⚠️ 경고: JSON 안에 '{TARGET_MUTATOR}'라는 코드명이 없습니다.")
                print("   (CommunityDragon 데이터가 업데이트 중이거나 코드명이 바뀌었을 수 있습니다.)")
            else:
                print(f"\n🎉 성공! '{save_path}'에 16시즌 데이터만 저장했습니다.")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    fetch_tft_set16_exact_match()
