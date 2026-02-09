"""
FDA-DUR 통합 시스템 테스트 스크립트
HeeJoon/4rd 폴더에서 실행
"""
import sys
import os

# HeeJoon/4rd를 Python path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from src.chain.rag_chain import prepare_context, generate_answer


def test_fda_dur_integration():
    """FDA-DUR 통합 테스트"""
    print("=" * 80)
    print("FDA-DUR 통합 시스템 테스트")
    print("=" * 80)
    
    # 테스트 질문들
    test_questions = [
        "Tylenol의 효능과 병용금기는?",
        "ibuprofen의 부작용은?",
        "acetaminophen 성분 정보",
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n\n{'='*80}")
        print(f"테스트 {i}: {question}")
        print('='*80)
        
        try:
            # 1. 컨텍스트 준비 (FDA + DUR)
            print("\n[1단계] 컨텍스트 준비 중...")
            context_data = prepare_context(question)
            
            # 2. 결과 확인
            print(f"\n[2단계] 검색 결과:")
            print(f"  - 분류: {context_data['category']}")
            print(f"  - 키워드: {context_data['keyword']}")
            print(f"  - FDA 결과: {len(context_data['raw_results'])}건")
            print(f"  - 추출된 성분: {context_data['ingredients']}")
            
            # 3. DUR 정보 확인
            print(f"\n[3단계] DUR 정보:")
            if context_data['dur_context'] != "(병용금기 정보 없음)":
                print(context_data['dur_context'])
            else:
                print("  (DUR 정보 없음)")
            
            # 4. 답변 생성
            print(f"\n[4단계] 답변 생성 중...")
            answer = generate_answer(context_data)
            
            print(f"\n[최종 답변]")
            print("-" * 80)
            print(answer)
            print("-" * 80)
            
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n\n" + "=" * 80)
    print("테스트 완료")
    print("=" * 80)


if __name__ == "__main__":
    test_fda_dur_integration()
