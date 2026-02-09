"""
간단한 DUR 클라이언트 테스트
"""
import sys
import os

# HeeJoon/4rd를 Python path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

print("=" * 60)
print("DUR 클라이언트 간단 테스트")
print("=" * 60)

try:
    from src.api.dur_client import search_dur_by_ingredient, format_dur_results
    
    # 테스트 1: 단일 성분 검색
    print("\n[테스트 1] 'acetaminophen' 검색")
    results = search_dur_by_ingredient("acetaminophen")
    print(f"결과: {len(results)}건")
    
    if results:
        print("\n첫 번째 결과:")
        first = results[0]
        print(f"  - 성분(한글): {first.get('INGR_KOR_NAME', 'N/A')}")
        print(f"  - 성분(영문): {first.get('INGR_ENG_NAME', 'N/A')}")
        print(f"  - 병용금기 성분: {first.get('MIXTURE_INGR_KOR_NAME', 'N/A')}")
        print(f"  - 사유: {first.get('PROHBT_CONTENT', 'N/A')[:100]}...")
    
    # 테스트 2: 포맷팅
    if results:
        print("\n[테스트 2] 포맷팅")
        dur_data = {"acetaminophen": results}
        formatted = format_dur_results(dur_data)
        print(formatted[:500])
    
    print("\n" + "=" * 60)
    print("✅ 테스트 완료")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()
