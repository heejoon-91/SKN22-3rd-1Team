import requests
import pandas as pd

# 모든 약물을 검사 후 해당 약물에 boxed_warning 또는 contraindications가 있는 경우만 추출

def extract_grade_a_info(drug_name):
    """
    FDA API를 호출하여 특정 약물의 Grade A(절대 금기) 정보를 추출하는 함수
    """
    url = f"https://api.fda.gov/drug/label.json?search=openfda.generic_name:\"{drug_name}\"&limit=1"
    response = requests.get(url)
    
    if response.status_code != 200:
        return {"error": "데이터를 찾을 수 없거나 API 호출에 실패했습니다."}
    
    data = response.json()['results'][0]
    
    # 1. 주성분 추출
    ingredient = data.get('openfda', {}).get('generic_name', [drug_name])[0]
    
    # 2. Grade A 판단 및 사유 추출
    grade_a_reasons = []
    
    # [Boxed Warning] 치명적 경고 확인
    if 'boxed_warning' in data:
        grade_a_reasons.append(f"[치명적 경고] {data['boxed_warning'][0][:200]}...")
        
    # [Contraindications] 절대 금기 필드 확인
    if 'contraindications' in data:
        grade_a_reasons.append(f"[절대 금기] {data['contraindications'][0][:200]}...")
        
    # [Pregnancy Category X] 임부 금기 확인
    if 'teratogenic_effects' in data:
        if "Category X" in data['teratogenic_effects'][0]:
            grade_a_reasons.append("[임부 절대 금기] 이 약물은 임부 금기 등급 X(기형 유발)에 해당합니다.")

    return {
        "주성분": ingredient,
        "Grade_A_여부": "YES" if grade_a_reasons else "NO",
        "금기_사유": " | ".join(grade_a_reasons) if grade_a_reasons else "특이사항 없음"
    }

# 실행 예시: 'Sildenafil'(비아그라 성분) 검색
result = extract_grade_a_info("sildenafil")
print(f"성분명: {result['주성분']}")
print(f"사유: {result['금기_사유']}")