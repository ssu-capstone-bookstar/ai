"""
메인 API 테스트
"""
from fastapi.testclient import TestClient

from bookstar.main import app


def test_app_creation():
    """FastAPI 앱이 정상적으로 생성되는지 테스트"""
    assert app.title == "BookStar AI"
    assert app.description == "AI 기반 도서 추천 시스템"


def test_recommend_books_endpoint():
    """도서 추천 엔드포인트 테스트"""
    client = TestClient(app)
    
    # 임의의 사용자 ID로 추천 요청
    response = client.post(
        "/recommend_books",
        json={"user_id": 1}  # 테스트용 임의 ID
    )
    
    # 응답 검증
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    recommendations = data["recommendations"]
    assert isinstance(recommendations, list)
    
    if recommendations:  # 추천 결과가 있는 경우
        first_recommendation = recommendations[0]
        assert "book_id" in first_recommendation
        # 새로운 응답 형태에서는 book_id만 포함됨
        assert len(first_recommendation) == 1 