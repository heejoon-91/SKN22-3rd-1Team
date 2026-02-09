"""분류 → OpenFDA API 호출 → DUR 조회 → 답변 생성 RAG 체인"""
import json
from typing import Generator
from langchain_openai import ChatOpenAI

from .prompts import CLASSIFIER_PROMPT, ANSWER_PROMPT as GENERATOR_PROMPT
from ..api.openfda_client import (
    search_by_brand_name,
    search_by_generic_name,
    search_by_indication,
)
from ..api.formatter import format_label_results
from ..api.dur_client import search_dur_for_ingredients, format_dur_results
from ..config import CLASSIFIER_MODEL, LLM_MODEL, LLM_TEMPERATURE, OPENAI_API_KEY


def _get_classifier() -> ChatOpenAI:
    """분류용 LLM"""
    return ChatOpenAI(
        model=CLASSIFIER_MODEL,
        temperature=0.0,
        openai_api_key=OPENAI_API_KEY,
    )


def _get_generator(streaming: bool = False) -> ChatOpenAI:
    """답변 생성용 LLM"""
    return ChatOpenAI(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        openai_api_key=OPENAI_API_KEY,
        streaming=streaming,
    )


def classify(question: str) -> dict:
    """사용자 질문을 분류하여 category, keyword 반환"""
    llm = _get_classifier()
    prompt = CLASSIFIER_PROMPT.format_messages(question=question)
    result = llm.invoke(prompt)

    try:
        parsed = json.loads(result.content.strip())
    except json.JSONDecodeError:
        # 파싱 실패 시 기본값: 브랜드명 검색
        parsed = {"category": "brand_name", "keyword": question}

    return {
        "question": question,
        "category": parsed.get("category", "brand_name"),
        "keyword": parsed.get("keyword", question),
    }


def search_openfda(category: str, keyword: str) -> tuple[str, list[dict], list[str]]:
    """분류 결과에 따라 OpenFDA API 호출
    
    Returns:
        (context, raw_results, ingredients) 튜플
    """
    # invalid 카테고리 처리
    if category == "invalid":
        return "(invalid query)", [], []
    
    if category == "brand_name":
        results = search_by_brand_name(keyword)
    elif category == "generic_name":
        results = search_by_generic_name(keyword)
    elif category == "indication":
        results = search_by_indication(keyword)
    else:
        # 기본: 브랜드명 검색
        results = search_by_brand_name(keyword)

    # 포맷팅 및 성분 추출
    context, ingredients = format_label_results(results)
    return context, results, ingredients


def prepare_context(question: str) -> dict:
    """
    분류 + API 호출 + DUR 조회 + 컨텍스트 구성
    Streamlit에서 스트리밍 전에 호출
    """
    # 1단계: 분류
    classification = classify(question)

    # 2단계: FDA API 호출 및 성분 추출
    context, raw_results, ingredients = search_openfda(
        classification["category"],
        classification["keyword"]
    )

    # 3단계: DUR 정보 검색
    dur_context = "(병용금기 정보 없음)"
    if ingredients:
        try:
            print(f"[DUR 검색] 성분 {len(ingredients)}개: {ingredients}")
            dur_data = search_dur_for_ingredients(ingredients)
            if dur_data:
                dur_context = format_dur_results(dur_data)
                print(f"[DUR 검색] {len(dur_data)}개 성분의 DUR 정보 발견")
            else:
                print("[DUR 검색] DUR 정보 없음")
        except Exception as e:
            print(f"[DUR 검색 오류] {e}")
            dur_context = "(DUR 정보 조회 중 오류 발생)"

    return {
        "question": question,
        "category": classification["category"],
        "keyword": classification["keyword"],
        "context": context,
        "raw_results": raw_results,
        "ingredients": ingredients,  # 디버깅/로깅용
        "dur_context": dur_context,
    }


def stream_answer(context_data: dict) -> Generator[str, None, None]:
    """
    컨텍스트 데이터로 스트리밍 답변 생성
    Generator로 청크 단위 반환
    """
    llm = _get_generator(streaming=True)

    prompt_value = GENERATOR_PROMPT.format_messages(
        question=context_data["question"],
        category=context_data["category"],
        keyword=context_data["keyword"],
        context=context_data["context"],
        dur_context=context_data["dur_context"],
    )

    for chunk in llm.stream(prompt_value):
        if chunk.content:
            yield chunk.content


def generate_answer(context_data: dict) -> str:
    """
    컨텍스트 데이터로 전체 답변 생성 (비스트리밍)
    """
    llm = _get_generator(streaming=False)

    prompt_value = GENERATOR_PROMPT.format_messages(
        question=context_data["question"],
        category=context_data["category"],
        keyword=context_data["keyword"],
        context=context_data["context"],
        dur_context=context_data["dur_context"],
    )

    result = llm.invoke(prompt_value)
    return result.content


if __name__ == "__main__":
    # 테스트 코드
    print("=== RAG Chain 테스트 ===\n")
    
    test_question = "Tylenol의 효능과 병용금기는?"
    print(f"질문: {test_question}\n")
    
    # 컨텍스트 준비
    context_data = prepare_context(test_question)
    
    print(f"분류: {context_data['category']}")
    print(f"키워드: {context_data['keyword']}")
    print(f"성분: {context_data['ingredients']}")
    print(f"\nDUR 정보:\n{context_data['dur_context']}")
    
    # 답변 생성
    print("\n답변 생성 중...\n")
    answer = generate_answer(context_data)
    print(answer)
