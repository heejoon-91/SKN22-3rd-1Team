"""
병용금기 성분 추출 스크립트
- boxed_warning 또는 contraindications가 있는 약물의 주성분 추출
- 병용금지 성분 자동 추출
"""
import requests
import pandas as pd
import re
from urllib.parse import quote
from typing import Dict, List, Optional


def extract_contraindicated_pair(drug_name: str) -> Optional[Dict]:
    """
    FDA API를 호출하여 특정 약물의 병용금기 정보를 추출
    
    Args:
        drug_name: 검색할 약물의 성분명 (영문)
    
    Returns:
        병용금기 정보 딕셔너리 또는 None (오류 시)
    """
    # URL 인코딩 적용
    search_term = f'openfda.generic_name:"{drug_name}"'
    encoded_search = quote(search_term)
    url = f"https://api.fda.gov/drug/label.json?search={encoded_search}&limit=1"
    
    try:
        # 타임아웃 설정
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        results = data.get('results', [])
        
        # 빈 결과 처리
        if not results:
            return {
                "error": f"'{drug_name}' 검색 결과가 없습니다.",
                "주성분": drug_name,
                "병용금기_성분": [],
                "원문": ""
            }
        
        drug_data = results[0]
        
        # 주성분 확인
        openfda = drug_data.get('openfda', {})
        generic_names = openfda.get('generic_name', [drug_name])
        main_ingredient = generic_names[0] if generic_names else drug_name
        
        # 금기사항 및 블랙박스 경고 텍스트 병합
        contraindications = drug_data.get('contraindications', [])
        boxed_warnings = drug_data.get('boxed_warning', [])
        drug_interactions = drug_data.get('drug_interactions', [])
        
        # 모든 관련 텍스트 병합
        full_text = " ".join(contraindications + boxed_warnings + drug_interactions)
        
        if not full_text:
            return {
                "주성분": main_ingredient,
                "병용금기_성분": [],
                "원문": "금기사항 정보 없음",
                "브랜드명": openfda.get('brand_name', [])
            }
        
        # 병용 금기 성분 추출
        contraindicated_drugs = extract_drug_names_from_text(full_text)
        
        return {
            "주성분": main_ingredient,
            "병용금기_성분": contraindicated_drugs,
            "원문_샘플": full_text[:500] + "..." if len(full_text) > 500 else full_text,
            "브랜드명": openfda.get('brand_name', []),
            "제조사": openfda.get('manufacturer_name', [])
        }
        
    except requests.exceptions.Timeout:
        return {"error": "API 요청 시간 초과 (10초)"}
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP 오류: {e}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"API 호출 실패: {e}"}
    except (KeyError, IndexError) as e:
        return {"error": f"데이터 파싱 오류: {e}"}


def extract_drug_names_from_text(text: str) -> List[Dict[str, str]]:
    """
    텍스트에서 병용금기 약물명 추출
    
    Args:
        text: 금기사항 텍스트
    
    Returns:
        추출된 약물 정보 리스트
    """
    contraindicated_drugs = []
    
    # 패턴 1: "contraindicated with [약물명]"
    pattern1 = r"contraindicated\s+(?:with|in\s+patients\s+(?:receiving|taking))\s+([a-zA-Z\s\-]+?)(?:\s+(?:or|and|,|\.|;))"
    matches1 = re.findall(pattern1, text, re.IGNORECASE)
    
    # 패턴 2: "do not use with [약물명]"
    pattern2 = r"do\s+not\s+(?:use|administer|give)\s+with\s+([a-zA-Z\s\-]+?)(?:\s+(?:or|and|,|\.|;))"
    matches2 = re.findall(pattern2, text, re.IGNORECASE)
    
    # 패턴 3: "co-administration with [약물명]"
    pattern3 = r"co-administration\s+with\s+([a-zA-Z\s\-]+?)(?:\s+(?:is|was|are|,|\.|;))"
    matches3 = re.findall(pattern3, text, re.IGNORECASE)
    
    # 패턴 4: "concomitant use with [약물명]"
    pattern4 = r"concomitant\s+use\s+(?:of|with)\s+([a-zA-Z\s\-]+?)(?:\s+(?:is|and|,|\.|;))"
    matches4 = re.findall(pattern4, text, re.IGNORECASE)
    
    # 패턴 5: 특정 약물 클래스 (예: "MAO inhibitors", "nitrates")
    pattern5 = r"(?:with|of)\s+((?:[A-Z][a-z]+\s+)?(?:inhibitors?|antagonists?|agonists?|blockers?|nitrates?|anticoagulants?))"
    matches5 = re.findall(pattern5, text)
    
    # 모든 매칭 결과 병합
    all_matches = matches1 + matches2 + matches3 + matches4 + matches5
    
    # 중복 제거 및 정리
    seen = set()
    for match in all_matches:
        # 공백 정리
        drug_name = match.strip()
        
        # 너무 짧거나 긴 것 제외
        if len(drug_name) < 3 or len(drug_name) > 50:
            continue
        
        # 소문자로 변환하여 중복 체크
        drug_name_lower = drug_name.lower()
        if drug_name_lower not in seen:
            seen.add(drug_name_lower)
            contraindicated_drugs.append({
                "약물명": drug_name.title(),  # 첫 글자 대문자
                "원문": drug_name
            })
    
    return contraindicated_drugs


def print_contraindication_info(result: Optional[Dict]):
    """검색 결과를 보기 좋게 출력"""
    print("\n" + "=" * 80)
    print("FDA 병용금기 정보")
    print("=" * 80)
    
    if result is None:
        print("❌ 결과 없음")
        return
    
    if "error" in result:
        print(f"❌ 오류: {result['error']}")
        if "주성분" in result:
            print(f"   검색어: {result['주성분']}")
        return
    
    print(f"\n📋 주성분: {result['주성분']}")
    
    if result.get('브랜드명'):
        print(f"💊 브랜드명: {', '.join(result['브랜드명'][:3])}")
    
    contraindicated = result.get('병용금기_성분', [])
    print(f"\n⚠️  병용금기 성분 ({len(contraindicated)}개):")
    
    if contraindicated:
        for i, drug in enumerate(contraindicated, 1):
            print(f"  [{i}] {drug['약물명']}")
    else:
        print("  - 자동 추출된 병용금기 성분 없음")
        print("  - 원문을 직접 확인하세요")
    
    if result.get('원문_샘플'):
        print(f"\n📄 원문 샘플:")
        print(f"  {result['원문_샘플'][:200]}...")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    # 실행 예시
    test_drugs = ["sildenafil", "warfarin", "metformin"]
    
    for drug in test_drugs:
        result = extract_contraindicated_pair(drug)
        print_contraindication_info(result)
        print("\n")