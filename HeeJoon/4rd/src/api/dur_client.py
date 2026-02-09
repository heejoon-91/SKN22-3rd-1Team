"""
DUR (Drug Utilization Review) 클라이언트
Supabase dur 테이블에서 병용금기 정보를 조회합니다.
"""
import os
from typing import List, Dict, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


def _get_client() -> Client:
    """Supabase 클라이언트 생성"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def _normalize_ingredient_name(name: str) -> str:
    """성분명에서 접미사를 제거하여 핵심 이름만 추출합니다.
    
    예: "슈도에페드린염산염" → "슈도에페드린"
        "겐타마이신황산염" → "겐타마이신"
    """
    # 일반적인 제약 접미사 목록 (긴 것부터 처리)
    suffixes = [
        "염산염수화물", "브롬화수소산염수화물", "오로트산염수화물",
        "염산염", "황산염", "수화물", "말레산염", "푸마르산염",
        "타르타르산염", "인산염", "질산염", "아세트산염",
    ]
    normalized = name
    for suffix in suffixes:
        if normalized.endswith(suffix):
            normalized = normalized[: -len(suffix)]
            break
    return normalized


def search_dur_by_ingredient(ingredient_name: str) -> List[Dict]:
    """성분명으로 dur 테이블에서 병용금기 약물을 검색합니다.
    한글(INGR_KOR_NAME)과 영문(INGR_ENG_NAME) 모두 검색합니다.
    
    Args:
        ingredient_name: 검색할 성분명 (한글 또는 영문)
    
    Returns:
        병용금기 정보 리스트
    """
    client = _get_client()

    try:
        # 원본 성분명으로 검색 (한글/영문 모두)
        res = (
            client.table("dur")
            .select("*")
            .or_(f"INGR_KOR_NAME.ilike.%{ingredient_name}%,INGR_ENG_NAME.ilike.%{ingredient_name}%")
            .eq("DEL_YN", False)
            .limit(20)
            .execute()
        )

        results = res.data or []

        # 결과가 없으면 정규화된 이름으로 재검색
        if not results:
            normalized = _normalize_ingredient_name(ingredient_name)
            if normalized != ingredient_name:
                res2 = (
                    client.table("dur")
                    .select("*")
                    .or_(f"INGR_KOR_NAME.ilike.%{normalized}%,INGR_ENG_NAME.ilike.%{normalized}%")
                    .eq("DEL_YN", False)
                    .limit(20)
                    .execute()
                )
                results = res2.data or []

        return results
    except Exception as e:
        print(f"[DUR 검색 오류] '{ingredient_name}' 검색 중 오류: {e}")
        return []


def search_dur_for_ingredients(ingredients: List[str]) -> Dict[str, List[Dict]]:
    """여러 성분에 대해 각각 DUR 병용금기 정보를 검색합니다.
    
    Args:
        ingredients: 성분명 리스트
    
    Returns:
        성분별 병용금기 정보 딕셔너리 {성분명: [병용금기 정보]}
    """
    result = {}
    for ingr in ingredients:
        dur_data = search_dur_by_ingredient(ingr)
        if dur_data:
            result[ingr] = dur_data
    return result


def _get_dur_field(row: Dict, field: str) -> str:
    """DUR 데이터에서 필드 값을 대소문자 구분 없이 가져옵니다."""
    return row.get(field) or row.get(field.lower(), "")


def format_dur_results(dur_data: Dict[str, List[Dict]]) -> str:
    """DUR 검색 결과를 LLM 컨텍스트용 텍스트로 포맷합니다.
    
    Args:
        dur_data: 성분별 병용금기 정보 딕셔너리
    
    Returns:
        포맷된 텍스트
    """
    if not dur_data:
        return "(병용금기 정보 없음)"

    parts = []
    for ingredient, contraindications in dur_data.items():
        lines = [f"[{ingredient}의 병용금기 약물 - 한국 DUR 데이터]"]
        seen = set()
        for item in contraindications:
            # 대소문자 모두 처리 (Supabase 컬럼명 호환)
            mixture_kor = item.get("MIXTURE_INGR_KOR_NAME") or item.get("mixture_ingr_kor_name", "")
            mixture_eng = item.get("MIXTURE_INGR_ENG_NAME") or item.get("mixture_ingr_eng_name", "")
            reason = item.get("PROHBT_CONTENT") or item.get("prohbt_content", "")
            
            # 한글 또는 영문 성분명 사용
            mixture = mixture_kor or mixture_eng
            
            if mixture and mixture not in seen:
                seen.add(mixture)
                lines.append(f"- {mixture}: {reason}")
        
        if len(lines) > 1:  # 헤더만 있는 경우 제외
            parts.append("\n".join(lines))

    return "\n\n".join(parts) if parts else "(병용금기 정보 없음)"


if __name__ == "__main__":
    # 테스트 코드
    print("=== DUR 클라이언트 테스트 ===\n")
    
    # 테스트 1: 단일 성분 검색
    test_ingredient = "acetaminophen"
    print(f"1. '{test_ingredient}' 검색:")
    results = search_dur_by_ingredient(test_ingredient)
    print(f"   결과: {len(results)}건\n")
    
    # 테스트 2: 여러 성분 검색
    test_ingredients = ["acetaminophen", "ibuprofen"]
    print(f"2. {test_ingredients} 검색:")
    dur_data = search_dur_for_ingredients(test_ingredients)
    print(f"   결과: {len(dur_data)}개 성분\n")
    
    # 테스트 3: 포맷팅
    if dur_data:
        print("3. 포맷된 결과:")
        formatted = format_dur_results(dur_data)
        print(formatted)
