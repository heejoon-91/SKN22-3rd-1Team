import requests
import json

# OpenFDA API에서 boxed_warning이 있는 약품 1개 가져오기

url = "https://api.fda.gov/drug/label.json?search=_exists_:boxed_warning&limit=1"

try:
    response = requests.get(url, timeout=10)
    data = response.json()
    
    if 'results' in data and len(data['results']) > 0:
        result = data['results'][0]
        
        print("=" * 80)
        print("OpenFDA Boxed Warning 예시")
        print("=" * 80)
        
        # 기본 정보
        if 'openfda' in result:
            openfda = result['openfda']
            print(f"\n[약품 정보]")
            print(f"브랜드명: {openfda.get('brand_name', ['N/A'])[0]}")
            print(f"성분명: {openfda.get('generic_name', ['N/A'])[0]}")
            print(f"제조사: {openfda.get('manufacturer_name', ['N/A'])[0]}")
        
        # Boxed Warning
        if 'boxed_warning' in result:
            print(f"\n[⚠️ BOXED WARNING (블랙박스 경고)]")
            print("-" * 80)
            boxed_warning = result['boxed_warning'][0]
            # 처음 500자만 출력
            print(boxed_warning[:500] + "..." if len(boxed_warning) > 500 else boxed_warning)
        
        # 전체 JSON 저장
        with open('boxed_warning_example.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print("\n" + "=" * 80)
        print("전체 데이터는 'boxed_warning_example.json' 파일에 저장되었습니다.")
        print("=" * 80)
        
except Exception as e:
    print(f"오류 발생: {e}")
