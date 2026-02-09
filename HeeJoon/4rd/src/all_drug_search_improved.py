"""
개선된 FDA API 약물 검색 스크립트
- 에러 처리 강화
- URL 인코딩 추가
- 프로젝트 구조와 일관성 유지
"""
import requests
from urllib.parse import quote
from typing import Dict, Optional

# 모든 약물을 검사 후 해당 약물에 boxed_warning 또는 contraindications가 있는 경우만 추출

def extract_drug_safety_info(drug_name: str) -> Dict:
    """
    FDA API를 호출하여 특정 약물의 안전성 정보를 추출하는 함수
    
    Args:
        drug_name: 검색할 약물의 성분명 (영문)
    
    Returns:
        약물 안전성 정보 딕셔너리
    """
    # URL 인코딩 적용
    search_term = f'openfda.generic_name:"{drug_name}"'
    encoded_search = quote(search_term)
    url = f"https://api.fda.gov/drug/label.json?search={encoded_search}&limit=1"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        results = data.get('results', [])
        
        if not results:
            return {
                "error": f"'{drug_name}' 검색 결과가 없습니다.",
                "주성분": drug_name,
                "안전성_등급": "UNKNOWN",
                "경고_사항": []
            }
        
        drug_data = results[0]
        
        # 주성분 추출
        ingredient = drug_data.get('openfda', {}).get('generic_name', [drug_name])[0]
        
        # 안전성 경고 수집
        safety_warnings = []
        
        # 1. Boxed Warning (가장 심각한 경고)
        boxed_warning = drug_data.get('boxed_warning', [])
        if boxed_warning:
            warning_text = boxed_warning[0][:300] + "..." if len(boxed_warning[0]) > 300 else boxed_warning[0]
            safety_warnings.append({
                "유형": "BOXED_WARNING",
                "심각도": "CRITICAL",
                "내용": warning_text
            })
        
        # 2. Contraindications (절대 금기)
        contraindications = drug_data.get('contraindications', [])
        if contraindications:
            contra_text = contraindications[0][:300] + "..." if len(contraindications[0]) > 300 else contraindications[0]
            safety_warnings.append({
                "유형": "CONTRAINDICATION",
                "심각도": "HIGH",
                "내용": contra_text
            })
        
        # 3. Warnings and Cautions (일반 경고)
        warnings = drug_data.get('warnings_and_cautions', [])
        if warnings:
            warning_text = warnings[0][:200] + "..." if len(warnings[0]) > 200 else warnings[0]
            safety_warnings.append({
                "유형": "WARNING",
                "심각도": "MODERATE",
                "내용": warning_text
            })
        
        # 안전성 등급 결정
        if boxed_warning:
            safety_grade = "GRADE_A"  # 가장 심각
        elif contraindications:
            safety_grade = "GRADE_B"  # 심각
        elif warnings:
            safety_grade = "GRADE_C"  # 주의
        else:
            safety_grade = "GRADE_D"  # 일반
        
        return {
            "주성분": ingredient,
            "안전성_등급": safety_grade,
            "경고_사항": safety_warnings,
            "브랜드명": drug_data.get('openfda', {}).get('brand_name', []),
            "제조사": drug_data.get('openfda', {}).get('manufacturer_name', [])
        }
        
    except requests.exceptions.Timeout:
        return {"error": "API 요청 시간 초과"}
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP 오류: {e}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"API 호출 실패: {e}"}
    except (KeyError, IndexError) as e:
        return {"error": f"데이터 파싱 오류: {e}"}


def print_drug_info(result: Dict):
    """검색 결과를 보기 좋게 출력"""
    print("\n" + "=" * 80)
    print("FDA 약물 안전성 정보")
    print("=" * 80)
    
    if "error" in result:
        print(f"❌ 오류: {result['error']}")
        return
    
    print(f"\n📋 주성분: {result['주성분']}")
    print(f"⚠️  안전성 등급: {result['안전성_등급']}")
    
    if result.get('브랜드명'):
        print(f"💊 브랜드명: {', '.join(result['브랜드명'][:3])}")
    
    if result.get('제조사'):
        print(f"🏭 제조사: {', '.join(result['제조사'][:2])}")
    
    print(f"\n📢 경고 사항 ({len(result['경고_사항'])}개):")
    for i, warning in enumerate(result['경고_사항'], 1):
        print(f"\n  [{i}] {warning['유형']} (심각도: {warning['심각도']})")
        print(f"      {warning['내용'][:150]}...")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    # 실행 예시
    test_drugs = ["sildenafil", "warfarin", "acetaminophen"]
    
    for drug in test_drugs:
        result = extract_drug_safety_info(drug)
        print_drug_info(result)
        print("\n")
