"""
개선된 FDA DUR 데이터 수집 스크립트
- 에러 처리 강화
- URL 인코딩 추가
- 프로젝트 구조와 일관성 유지
"""
import requests
import pandas as pd
from urllib.parse import quote
from typing import List, Dict, Optional
import time

# boxed_warning 또는 contraindications가 있는 경우만 추출

def fetch_drugs_with_warnings(limit: int = 100, include_contraindications: bool = True) -> Optional[pd.DataFrame]:
    """
    FDA API에서 boxed_warning 또는 contraindications가 있는 약물들을 추출합니다.
    
    Args:
        limit: 가져올 최대 약물 수 (기본값: 100)
        include_contraindications: contraindications도 포함할지 여부
    
    Returns:
        DataFrame 또는 None (실패 시)
    """
    # 검색 쿼리 구성
    if include_contraindications:
        search_query = '_exists_:boxed_warning OR _exists_:contraindications'
    else:
        search_query = '_exists_:boxed_warning'
    
    # URL 인코딩 적용
    encoded_query = quote(search_query)
    url = f"https://api.fda.gov/drug/label.json?search={encoded_query}&limit={limit}"
    
    print(f"🔍 FDA API 호출 중... (최대 {limit}개)")
    print(f"📡 URL: {url[:100]}...")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        results = data.get('results', [])
        
        if not results:
            print("❌ 검색 결과가 없습니다.")
            return None
        
        print(f"✅ {len(results)}개의 약물 데이터를 받았습니다.")
        
        # 데이터 추출
        extracted_list = []
        
        for idx, drug in enumerate(results, 1):
            try:
                # 주성분 추출
                openfda = drug.get('openfda', {})
                generic_names = openfda.get('generic_name', ["N/A"])
                ingredient = generic_names[0] if generic_names else "N/A"
                
                # 브랜드명 추출
                brand_names = openfda.get('brand_name', [])
                brand_name = brand_names[0] if brand_names else "N/A"
                
                # Boxed Warning 추출
                boxed_warnings = drug.get('boxed_warning', [])
                boxed_warning_text = boxed_warnings[0][:500] if boxed_warnings else ""
                
                # Contraindications 추출
                contraindications = drug.get('contraindications', [])
                contraindication_text = contraindications[0][:500] if contraindications else ""
                
                # 경고 유형 결정
                if boxed_warning_text:
                    warning_type = "BOXED_WARNING"
                    warning_severity = "CRITICAL"
                    warning_content = boxed_warning_text
                elif contraindication_text:
                    warning_type = "CONTRAINDICATION"
                    warning_severity = "HIGH"
                    warning_content = contraindication_text
                else:
                    continue  # 경고가 없으면 스킵
                
                extracted_list.append({
                    "순번": idx,
                    "주성분": ingredient,
                    "브랜드명": brand_name,
                    "경고_유형": warning_type,
                    "심각도": warning_severity,
                    "경고_내용": warning_content,
                    "Boxed_Warning_존재": "YES" if boxed_warning_text else "NO",
                    "Contraindication_존재": "YES" if contraindication_text else "NO"
                })
                
                # 진행 상황 표시
                if idx % 10 == 0:
                    print(f"  처리 중... {idx}/{len(results)}")
                    
            except Exception as e:
                print(f"  ⚠️  약물 #{idx} 처리 중 오류: {e}")
                continue
        
        if not extracted_list:
            print("❌ 추출된 데이터가 없습니다.")
            return None
        
        df = pd.DataFrame(extracted_list)
        print(f"\n✅ 총 {len(df)}개의 약물 정보를 추출했습니다.")
        
        # 통계 출력
        print("\n📊 통계:")
        print(f"  - Boxed Warning: {df['Boxed_Warning_존재'].value_counts().get('YES', 0)}개")
        print(f"  - Contraindication: {df['Contraindication_존재'].value_counts().get('YES', 0)}개")
        
        return df
        
    except requests.exceptions.Timeout:
        print("❌ API 요청 시간 초과 (30초)")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP 오류: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ API 호출 실패: {e}")
        return None
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return None


def save_to_csv(df: pd.DataFrame, filename: str = "fda_drug_warnings.csv"):
    """DataFrame을 CSV 파일로 저장"""
    try:
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\n💾 파일 저장 완료: {filename}")
        return True
    except Exception as e:
        print(f"❌ 파일 저장 실패: {e}")
        return False


def analyze_warnings(df: pd.DataFrame):
    """경고 데이터 분석 및 요약"""
    print("\n" + "=" * 80)
    print("📈 FDA 약물 경고 데이터 분석")
    print("=" * 80)
    
    print(f"\n총 약물 수: {len(df)}")
    
    print("\n경고 유형별 분포:")
    print(df['경고_유형'].value_counts())
    
    print("\n심각도별 분포:")
    print(df['심각도'].value_counts())
    
    # 상위 10개 약물 표시
    print("\n상위 10개 약물:")
    print(df[['순번', '주성분', '브랜드명', '경고_유형']].head(10).to_string(index=False))
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    print("=" * 80)
    print("FDA 약물 경고 데이터 수집 시작")
    print("=" * 80)
    
    # 데이터 수집 (50개로 제한 - 테스트용)
    df = fetch_drugs_with_warnings(limit=50, include_contraindications=True)
    
    if df is not None:
        # 분석
        analyze_warnings(df)
        
        # CSV 저장
        save_to_csv(df, "fda_drug_warnings.csv")
        
        print("\n✅ 모든 작업 완료!")
    else:
        print("\n❌ 데이터 수집 실패")
