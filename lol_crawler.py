import requests
import json
import os
import re

# 데이터 저장 경로
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def clean_html(raw_html):
    """HTML 태그(<br>, <stats> 등)를 제거하고 텍스트만 남깁니다."""
    if not raw_html:
        return ""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, ' ', raw_html)
    # 연속된 공백 제거
    return re.sub(r'\s+', ' ', cleantext).strip()

def fetch_lol_full_data():
    print("📥 LoL 통합 데이터(챔피언/아이템/룬/스펠) 다운로드 중...")
    
    try:
        # 1. 최신 버전 확인
        ver_url = "https://ddragon.leagueoflegends.com/api/versions.json"
        version = requests.get(ver_url).json()[0]
        print(f"   - 감지된 최신 버전: {version}")

        # 저장할 파일 경로
        save_path = os.path.join(DATA_DIR, "base_lol_full_data.txt")
        
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(f"=== [LoL 통합 데이터 시스템] (Ver {version}) ===\n")
            f.write("이 파일은 챔피언, 아이템, 룬, 소환사 주문의 상세 스펙을 포함합니다.\n")
            f.write("모든 HTML 태그는 제거되었으며, AI가 읽기 최적화된 상태입니다.\n\n")

            # ==========================================
            # 1. 챔피언 상세 정보 (New!)
            # ==========================================
            print("   - 🦸‍♂️ 챔피언 상세 데이터 분석 중... (양이 많습니다)")
            f.write("## 1. 챔피언 (Champions)\n")
            
            # championFull.json을 써야 쿨타임, 계수 등 상세 정보가 나옵니다.
            champ_url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/ko_KR/championFull.json"
            champ_data = requests.get(champ_url).json()['data']
            
            for key, val in champ_data.items():
                name = val['name']
                title = val['title']
                stats = val['stats']
                spells = val['spells']
                passive = val['passive']
                
                # 챔피언 기본 정보
                f.write(f"### {name} ({title})\n")
                f.write(f"- 기본 스탯: 체력 {stats['hp']}, 공격력 {stats['attackdamage']}, 사거리 {stats['attackrange']}, 이속 {stats['movespeed']}\n")
                
                # 패시브
                p_desc = clean_html(passive['description'])
                f.write(f"- 패시브 [{passive['name']}]: {p_desc}\n")
                
                # 스킬 (Q, W, E, R)
                skill_keys = ['Q', 'W', 'E', 'R']
                for idx, spell in enumerate(spells):
                    if idx < 4:
                        s_name = spell['name']
                        s_desc = clean_html(spell['description'])
                        s_cool = "/".join(map(str, spell['cooldown'])) # 쿨타임
                        s_cost = "/".join(map(str, spell['cost']))     # 마나/기력 소모
                        
                        f.write(f"- {skill_keys[idx]} 스킬 [{s_name}]: {s_desc} (쿨타임: {s_cool}초, 소모: {s_cost})\n")
                f.write("\n")

            # ==========================================
            # 2. 아이템 정보
            # ==========================================
            print("   - 🎒 아이템 데이터 분석 중...")
            f.write("## 2. 아이템 (Items)\n")
            
            item_url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/ko_KR/item.json"
            item_data = requests.get(item_url).json()['data']
            
            for item_id, item in item_data.items():
                if item.get('maps', {}).get('11', False): # 협곡 아이템만
                    name = item.get('name', '이름 없음')
                    gold = item.get('gold', {}).get('total', 0)
                    plaintext = item.get('plaintext', '')
                    description = clean_html(item.get('description', ''))
                    
                    f.write(f"- {name} (가격: {gold}G)\n")
                    f.write(f"  설명: {plaintext} | {description}\n\n")

            # ==========================================
            # 3. 룬 정보
            # ==========================================
            print("   - 💎 룬(Runes) 데이터 분석 중...")
            f.write("## 3. 룬 (Runes)\n")
            
            rune_url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/ko_KR/runesReforged.json"
            rune_data = requests.get(rune_url).json()
            
            for style in rune_data:
                style_name = style['name']
                f.write(f"### [{style_name} 빌드]\n")
                for slot in style['slots']:
                    for rune in slot['runes']:
                        r_name = rune['name']
                        r_long = clean_html(rune.get('longDesc', ''))
                        f.write(f"- {r_name}: {r_long}\n")
                f.write("\n")

            # ==========================================
            # 4. 소환사 주문
            # ==========================================
            print("   - 🔥 소환사 주문(Spells) 분석 중...")
            f.write("## 4. 소환사 주문 (Summoner Spells)\n")
            
            spell_url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/ko_KR/summoner.json"
            spell_data = requests.get(spell_url).json()['data']
            
            for spell_id, spell in spell_data.items():
                modes = spell.get('modes', [])
                if "CLASSIC" in modes: # 협곡에서 쓰는 주문만
                    s_name = spell['name']
                    s_desc = clean_html(spell.get('description', ''))
                    s_cd = spell.get('cooldown', [0])[0]
                    
                    f.write(f"- {s_name} (쿨타임: {s_cd}초): {s_desc}\n")

        print(f"✅ 저장 완료: {save_path}")
        print("   이제 Nexus는 챔피언 스킬, 아이템, 룬, 스펠을 모두 마스터했습니다!")

    except Exception as e:
        print(f"❌ 다운로드 실패: {e}")

if __name__ == "__main__":
    fetch_lol_full_data()
