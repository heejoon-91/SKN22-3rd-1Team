"""OpenFDA API 응답을 LLM 컨텍스트용 텍스트로 포맷"""
from typing import Optional, List, Tuple


# 라벨 데이터에서 추출할 필드와 라벨 매핑
LABEL_FIELD_MAP = {
    "brand_name": "Brand Name",
    "generic_name": "Generic Name",
    "manufacturer_name": "Manufacturer",
    "purpose": "Purpose",
    "indications_and_usage": "Indications and Usage",
    "dosage_and_administration": "Dosage and Administration",
    "warnings": "Warnings",
    "do_not_use": "Do Not Use",
    "stop_use": "Stop Use When",
    "drug_interactions": "Drug Interactions",
    "contraindications": "Contraindications",
    "pregnancy_or_breast_feeding": "Pregnancy/Breastfeeding",
    "active_ingredient": "Active Ingredients",
    "storage_and_handling": "Storage and Handling",
}


def _extract_value(data: dict, key: str) -> Optional[str]:
    """딕셔너리에서 값 추출 (리스트면 첫 번째 요소, 중첩 openfda 필드 처리)"""
    # openfda 중첩 필드 확인
    if key in ["brand_name", "generic_name", "manufacturer_name"]:
        openfda = data.get("openfda") or {}
        value = openfda.get(key, [])
    else:
        value = data.get(key, [])

    if isinstance(value, list) and value:
        # 리스트의 첫 번째 요소 또는 여러 개 합치기
        if len(value) == 1:
            return value[0]
        else:
            return "; ".join(str(v) for v in value[:3])
    elif isinstance(value, str):
        return value
    return None


def extract_ingredients(fda_results: List[dict]) -> List[str]:
    """FDA 검색 결과에서 성분명 리스트 추출
    
    복합 성분명(쉼표로 구분)을 개별 성분으로 분리합니다.
    예: "acetaminophen, ibuprofen" → ["acetaminophen", "ibuprofen"]
    
    Args:
        fda_results: OpenFDA API 검색 결과 리스트
    
    Returns:
        성분명 리스트 (중복 제거, 소문자 변환)
    """
    ingredients = set()
    for result in fda_results:
        openfda = result.get("openfda", {})
        generic_names = openfda.get("generic_name", [])
        
        for name in generic_names:
            # 쉼표로 구분된 복합 성분명 분리
            parts = [p.strip() for p in name.split(',')]
            for part in parts:
                # "and" 키워드로 구분된 성분도 분리
                sub_parts = [sp.strip() for sp in part.split(' and ')]
                for sub_part in sub_parts:
                    # 정규화: 소문자 변환, 공백 제거
                    cleaned = sub_part.strip().lower()
                    # 빈 문자열이나 숫자만 있는 경우 제외
                    if cleaned and not cleaned.replace('mg', '').replace('/', '').strip().isdigit():
                        ingredients.add(cleaned)
    
    return list(ingredients)


def format_drug_label(label: dict) -> str:
    """단일 의약품 라벨 데이터를 포맷"""
    lines = []
    for field, display_name in LABEL_FIELD_MAP.items():
        value = _extract_value(label, field)
        if value:
            # 너무 긴 텍스트는 잘라내기 (토큰 절약)
            if len(value) > 800:
                value = value[:800] + "..."
            lines.append(f"[{display_name}] {value}")
    return "\n".join(lines) if lines else "(No data available)"


def format_label_results(results: List[dict]) -> Tuple[str, List[str]]:
    """여러 라벨 검색 결과를 하나의 컨텍스트로 포맷
    
    Args:
        results: OpenFDA API 검색 결과 리스트
    
    Returns:
        (formatted_context, ingredient_list) 튜플
    """
    if not results:
        return "(No search results found)", []

    # 성분 추출
    ingredients = extract_ingredients(results)

    # 컨텍스트 포맷팅
    parts = []
    for i, label in enumerate(results[:5], 1):  # 최대 5개
        header = f"── Result {i} ──"
        body = format_drug_label(label)
        parts.append(f"{header}\n{body}")
    
    formatted_context = "\n\n".join(parts)
    
    return formatted_context, ingredients
