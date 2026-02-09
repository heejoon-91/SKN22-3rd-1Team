# HeeJoon/4rd - FDA-DUR 통합 시스템

FDA API 검색 결과에서 성분을 추출하여 한국 DUR 데이터베이스의 병용금기 정보를 함께 제공하는 시스템입니다.

## 디렉토리 구조

```
HeeJoon/4rd/
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── openfda_client.py    # FDA API 클라이언트
│   │   ├── formatter.py          # 성분 추출 + 포맷팅
│   │   └── dur_client.py         # DUR 검색 클라이언트
│   ├── chain/
│   │   ├── __init__.py
│   │   ├── prompts.py            # LLM 프롬프트
│   │   └── rag_chain.py          # FDA-DUR 통합 RAG Chain
│   └── config.py                 # 환경 설정
├── test_fda_dur.py               # 테스트 스크립트
└── README.md                     # 이 파일
```

## 주요 기능

1. **FDA API 검색**: 브랜드명, 성분명, 증상으로 약물 검색
2. **성분 자동 추출**: FDA 결과에서 `generic_name` 추출
3. **DUR 조회**: 추출된 성분으로 Supabase `dur` 테이블 검색
4. **통합 답변**: FDA 정보 + 한국 DUR 병용금기 정보 제공

## 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

필요한 패키지:
- `langchain-openai`
- `supabase`
- `requests`
- `python-dotenv`

### 2. 환경 변수 설정

프로젝트 루트의 `.env` 파일에 다음 변수가 설정되어 있어야 합니다:

```
OPENAI_API_KEY=your_openai_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### 3. 테스트 실행

```bash
cd c:\codes\SKN22-3rd-1Team\HeeJoon\4rd
python test_fda_dur.py
```

## 사용 예시

```python
from chain.rag_chain import prepare_context, generate_answer

# 질문 입력
question = "Tylenol의 효능과 병용금기는?"

# 컨텍스트 준비 (FDA + DUR)
context_data = prepare_context(question)

# 답변 생성
answer = generate_answer(context_data)
print(answer)
```

**출력 예시**:
```
### 💊 관련 성분 및 효능
- **아세트아미노펜(acetaminophen)**: 발열 및 통증 완화

---

### ⚠️ 주의사항

#### 🔴 병용금기 (Drug Interactions)
- **아세트아미노펜(acetaminophen)**: 
  - [FDA] 와파린과 병용 시 출혈 위험 증가
  - [한국 DUR] 이부프로펜과 병용 시 간 독성 위험
```

## 주요 모듈 설명

### `api/dur_client.py`
- `search_dur_by_ingredient(ingredient)`: 단일 성분 DUR 검색
- `search_dur_for_ingredients(ingredients)`: 여러 성분 일괄 검색
- `format_dur_results(dur_data)`: DUR 결과 포맷팅

### `api/formatter.py`
- `extract_ingredients(fda_results)`: FDA 결과에서 성분 추출
- `format_label_results(results)`: FDA 결과 포맷팅 + 성분 리스트 반환

### `chain/rag_chain.py`
- `prepare_context(question)`: 질문 분류 → FDA 검색 → DUR 조회
- `stream_answer(context_data)`: 스트리밍 답변 생성
- `generate_answer(context_data)`: 전체 답변 생성

## 문제 해결

### ImportError 발생 시
```bash
# Python path 확인
cd c:\codes\SKN22-3rd-1Team\HeeJoon\4rd
python -c "import sys; print(sys.path)"
```

### Supabase 연결 오류
- `.env` 파일의 `SUPABASE_URL`과 `SUPABASE_KEY` 확인
- Supabase 프로젝트에 `dur` 테이블이 존재하는지 확인

### DUR 정보가 표시되지 않음
- 성분명이 영문인지 확인 (예: "acetaminophen")
- DUR 테이블에 해당 성분 데이터가 있는지 확인

## 다음 단계

- [ ] Streamlit 앱 통합
- [ ] 단위 테스트 작성
- [ ] 성분명 매핑 테이블 추가
- [ ] DUR 결과 캐싱
