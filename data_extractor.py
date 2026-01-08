import requests
import json
import os

# 데이터 저장 경로
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def fetch_tft_season_16_only():
    print("📥 TFT 16시즌(Set 16) 전용 데이터 추출 중...")
    
    url = "https://raw.communitydragon.org/latest/cdragon/tft/ko_kr.json"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        save_path = os.path.join(DATA_DIR, "season_tft_set16.txt")
        
        with open(save_path, "w", encoding="utf-8") as f:
            f.write("=== [TFT 16시즌(Set 16) 상세 데이터] ===\n")
            f.write("이 데이터는 오직 16시즌에 등장하는 챔피언과 시너지만 포함합니다.\n\n")

            sets = data.get('setData', [])
            target_season_found = False

            for game_set in sets:
                # ★ 핵심 필터링 로직
                # mutator(내부 코드명)에 '16'이나 'Set16'이 포함된지 확인
                # 보통 'TFTSet16' 형식을 씁니다.
                mutator = game_set.get('mutator', '')
                name = game_set.get('name', '')
                
                # '16'이라는 숫자가 시즌 코드에 포함되어 있다면 추출 (TFTSet16)
                if "16" in mutator or "Set16" in mutator:
                    target_season_found = True
                    print(f"🔎 16시즌 데이터 발견! (코드명: {mutator})")
                    
                    f.write(f"## [시즌 정보: {name} ({mutator})]\n\n")
                    
                    # 1. 시너지 (Traits)
                    traits = game_set.get('traits', [])
                    f.write(f"### 1. 시너지 (Traits)\n")
                    for trait in traits:
                        t_name = trait.get('name')
                        t_desc = (trait.get('desc') or "").replace('<br>', ' ')
                        
                        # 시너지 이름이 있는 경우만 저장
                        if t_name:
                            f.write(f"- {t_name}: {t_desc}\n")
                            
                            # 시너지 단계별 효과 (선택 사항)
                            effects = trait.get('effects', [])
                            if effects:
                                formatted_effects = []
                                for e in effects:
                                    min_units = e.get('minUnits')
                                    # 변수 치환 (@MinUnits@ 등)이 복잡하므로 간단히 구조만 저장
                                    formatted_effects.append(f"{min_units}유닛")
                                f.write(f"  (활성 구간: {', '.join(formatted_effects)})\n")

                    f.write("\n")

                    # 2. 챔피언 (Champions)
                    champions = game_set.get('champions', [])
                    f.write(f"### 2. 챔피언 (Champions)\n")
                    for champ in champions:
                        c_name = champ.get('name')
                        c_cost = champ.get('cost')
                        c_traits = champ.get('traits', [])
                        
                        # 스킬 정보 안전하게 가져오기
                        ability = champ.get('ability', {})
                        c_skill = (ability.get('desc') or "").replace('<br>', ' ')
                        
                        if c_name:
                            f.write(f"- {c_name} ({c_cost}코스트)\n")
                            f.write(f"  소속: {', '.join(c_traits)}\n")
                            f.write(f"  스킬: {c_skill}\n")
                            
                            # 기본 스탯 (체력, 마나 등)
                            stats = champ.get('stats', {})
                            hp = stats.get('hp', '?')
                            mana = stats.get('mana', '?')
                            start_mana = stats.get('initialMana', '?')
                            f.write(f"  스탯: 체력 {hp}, 마나 {start_mana}/{mana}\n\n")
            
            if not target_season_found:
                print("⚠️ 경고: 'Set16' 데이터를 찾지 못했습니다. 시즌 번호를 확인하세요.")
                f.write("\n[데이터 없음] 16시즌 데이터를 찾지 못했습니다.\n")

        print(f"✅ 저장 완료: {save_path}")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    fetch_tft_season_16_only()
