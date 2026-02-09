import requests
import pandas as pd

# boxed_warning 또는 contraindications가 있는 경우만 추출

def fetch_all_grade_a_drugs(limit=100):
    """
    FDA API에서 boxed_warning 또는 contraindications가 있는 약물들을 추출합니다.
    """
    # 검색 쿼리: boxed_warning 필드나 contraindications 필드가 존재하는 약물만 검색
    search_query = '_exists_:boxed_warning OR _exists_:contraindications'
    url = f"https://api.fda.gov/drug/label.json?search={search_query}&limit={limit}"
    
    response = requests.get(url)
    if response.status_code != 200:
        print("API 호출 실패")
        return None

    results = response.json().get('results', [])
    extracted_list = []

    for drug in results:
        # 1. 주성분 추출 (generic_name 필드 활용) 
        ingredient = drug.get('openfda', {}).get('generic_name', ["N/A"])[0]
        
        # 2. 치명적 경고(Boxed Warning) 추출 
        boxed_warning = drug.get('boxed_warning', [""])[0]
        
        # 3. 절대 금기(Contraindications) 추출 
        contra_info = drug.get('contraindications', [""])[0]

        # 데이터가 있는 경우만 리스트에 추가
        if boxed_warning or contra_info:
            extracted_list.append({
                "주성분": ingredient,
                "절대금기_및_병용금기_사유": boxed_warning if boxed_warning else contra_info
            })

    return pd.DataFrame(extracted_list)

# 실행 및 CSV 저장
grade_a_df = fetch_all_grade_a_drugs(limit=50) # 예시로 50개 추출
if grade_a_df is not None:
    grade_a_df.to_csv("extracted_grade_a_drugs.csv", index=False, encoding='utf-8-sig')
    print(f"추출 완료: {len(grade_a_df)}개의 Grade A 약물을 찾았습니다.")