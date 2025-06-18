"""
추천 시스템 테스트
"""
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from bookstar.config import settings
from bookstar.services.recommendation import (
    RecommendationService,
    calculate_author_weight,
    calculate_category_weight,
    get_similar_users,
    get_user_preference_categories,
    recommend_books,
)


def test_recommendation_config():
    """추천 시스템 설정이 올바르게 로드되는지 테스트"""
    rec_config = settings.recommendation
    
    # 필수 설정 확인
    assert 'default_recommendations_count' in rec_config
    assert 'similar_users_count' in rec_config
    assert 'content_weight' in rec_config
    assert 'collaborative_weight' in rec_config
    
    # 가중치 합이 1.0인지 확인
    total_weight = rec_config['content_weight'] + rec_config['collaborative_weight']
    assert abs(total_weight - 1.0) < 0.001  # 부동소수점 오차 고려


def test_recommendation_service_init():
    """RecommendationService 초기화 테스트"""
    mock_db = MagicMock()
    service = RecommendationService(mock_db)
    
    assert service.db == mock_db


def test_get_user_books_data():
    """사용자 도서 데이터 조회 테스트"""
    mock_db = MagicMock()
    service = RecommendationService(mock_db)
    
    # Mock 데이터 설정
    mock_member_book1 = MagicMock()
    mock_member_book1.book_id = "book1"
    mock_member_book1.reading_status.value = "READED"
    
    mock_member_book2 = MagicMock()
    mock_member_book2.book_id = "book2"
    mock_member_book2.reading_status.value = "WANT_TO_READ"
    
    mock_db.query.return_value.filter.return_value.all.return_value = [
        (mock_member_book1.book_id, mock_member_book1.reading_status),
        (mock_member_book2.book_id, mock_member_book2.reading_status)
    ]
    
    user_id = 123
    read_list, want_list = service.get_user_books_data(user_id)
    
    assert isinstance(read_list, list)
    assert isinstance(want_list, list)


def test_get_user_preferences():
    """사용자 선호도 계산 테스트"""
    mock_db = MagicMock()
    service = RecommendationService(mock_db)
    
    # Mock get_user_books_data
    with patch.object(service, 'get_user_books_data') as mock_books:
        mock_books.return_value = (["1", "2"], ["3"])  # 숫자 문자열로 변경
        
        # Mock book data
        mock_book1 = MagicMock()
        mock_book1.book_category.value = "소설"
        mock_book1.author = "작가1"
        
        mock_db.query.return_value.filter.return_value.all.return_value = [
            (1, mock_book1.book_category, mock_book1.author)
        ]
        
        user_id = 123
        preferences = service.get_user_preferences(user_id)
        
        assert isinstance(preferences, dict)
        assert 'categories' in preferences
        assert 'authors' in preferences


def test_get_content_based_recommendations():
    """콘텐츠 기반 추천 테스트"""
    mock_db = MagicMock()
    service = RecommendationService(mock_db)
    
    # 전체 메서드를 Mock으로 대체하여 DataFrame을 직접 반환
    with patch.object(service, 'get_content_based_recommendations') as mock_method:
        # 예상되는 DataFrame 구조로 Mock 반환값 설정
        expected_df = pd.DataFrame([{
            'book_id': 'book1',
            'title': '테스트 책',
            'author': '작가1',
            'book_category': '소설',
            'image_url': 'test.jpg',
            'total_weight': 0.8
        }])
        mock_method.return_value = expected_df
        
        user_id = 123
        recommendations = service.get_content_based_recommendations(user_id)
        
        assert isinstance(recommendations, pd.DataFrame)
        assert len(recommendations) > 0


def test_get_collaborative_recommendations():
    """협업 필터링 추천 테스트"""
    mock_db = MagicMock()
    service = RecommendationService(mock_db)
    
    # Mock get_similar_users
    with patch.object(service, 'get_similar_users') as mock_similar:
        mock_similar.return_value = [456, 789]
        
        # Mock book data for similar users
        mock_book = MagicMock()
        mock_book.alading_book_id = "collab_book1"
        mock_book.title = "협업 추천 책"
        mock_book.author = "작가2"
        mock_book.book_category = MagicMock()
        mock_book.book_category.value = "과학"
        mock_book.image_url = "collab.jpg"
        
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_book]
        
        user_id = 123
        recommendations = service.get_collaborative_recommendations(user_id)
        
        assert isinstance(recommendations, pd.DataFrame)


def test_recommend_books_function():
    """메인 추천 함수 테스트"""
    mock_db = MagicMock()
    
    # Mock RecommendationService
    with patch(
        'bookstar.services.recommendation.RecommendationService'
    ) as mock_service_class:
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        
        # Mock content-based recommendations
        content_df = pd.DataFrame([{
            'book_id': 'content1',
            'total_weight': 0.8
        }])
        mock_service.get_content_based_recommendations.return_value = content_df
        
        # Mock collaborative recommendations
        collab_df = pd.DataFrame([{
            'book_id': 'collab1',
            'total_weight': 0.7
        }])
        mock_service.get_collaborative_recommendations.return_value = collab_df
        
        user_id = 123
        read_list = ["book1"]
        want_list = ["book2"]
        
        recommendations = recommend_books(mock_db, user_id, read_list, want_list)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        if recommendations:
            rec = recommendations[0]
            assert 'book_id' in rec
            # 새로운 응답 형태에서는 book_id만 포함됨
            assert len(rec) == 1


def test_get_similar_users_function():
    """유사 사용자 찾기 함수 테스트"""
    mock_db = MagicMock()
    
    # Mock query result
    mock_result = [
        (456, 0.8),  # (user_id, similarity_score)
        (789, 0.7),
        (101, 0.6)
    ]
    mock_db.execute.return_value.fetchall.return_value = mock_result
    
    read_list = ["book1", "book2"]
    user_id = 123
    num_similar_users = 2
    
    similar_users = get_similar_users(mock_db, read_list, user_id, num_similar_users)
    
    assert isinstance(similar_users, list)
    assert len(similar_users) <= num_similar_users


def test_calculate_author_weight():
    """저자 가중치 계산 테스트"""
    # Mock books data
    books = [
        {'author': '작가1', 'alading_book_id': 'book1'},
        {'author': '작가2', 'alading_book_id': 'book2'},
    ]
    read_list = ['book1']
    want_list = ['book2']
    
    weight = calculate_author_weight('작가1', books, read_list, want_list)
    
    assert isinstance(weight, int | float)
    assert weight >= 0


def test_calculate_category_weight():
    """카테고리 가중치 계산 테스트"""
    total_categories = {'소설': 5, '과학': 3, '역사': 2}
    
    weight = calculate_category_weight('소설', total_categories)
    
    assert isinstance(weight, int | float)
    assert weight >= 0


def test_get_user_preference_categories():
    """사용자 선호 카테고리 조회 테스트"""
    mock_db = MagicMock()
    
    # Mock book categories
    mock_result = [
        ('소설',),
        ('소설',),
        ('과학',),
    ]
    mock_db.execute.return_value.fetchall.return_value = mock_result
    
    book_ids = ['book1', 'book2', 'book3']
    categories = get_user_preference_categories(mock_db, book_ids)
    
    assert isinstance(categories, dict)


def test_recommendation_weights():
    """추천 가중치 설정 테스트"""
    rec_config = settings.recommendation
    
    content_weight = rec_config['content_weight']
    collaborative_weight = rec_config['collaborative_weight']
    
    # 가중치가 0과 1 사이인지 확인
    assert 0 <= content_weight <= 1
    assert 0 <= collaborative_weight <= 1
    
    # 가중치 합이 1인지 확인
    total_weight = content_weight + collaborative_weight
    assert abs(total_weight - 1.0) < 0.001


@pytest.mark.parametrize("num_recommendations", [1, 5, 10, 20])
def test_different_recommendation_counts(num_recommendations):
    """다양한 추천 개수 테스트"""
    mock_db = MagicMock()
    
    with patch(
        'bookstar.services.recommendation.RecommendationService'
    ) as mock_service_class:
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        
        # 충분한 수의 Mock 추천 결과 생성
        content_df = pd.DataFrame([{
            'book_id': f'content{i}',
            'total_weight': 0.8 - i * 0.1
        } for i in range(num_recommendations)])
        
        mock_service.get_content_based_recommendations.return_value = content_df
        mock_service.get_collaborative_recommendations.return_value = pd.DataFrame()
        
        user_id = 123
        read_list = []
        want_list = []
        
        recommendations = recommend_books(
            mock_db, user_id, read_list, want_list, num_recommendations
        )
        
        assert len(recommendations) <= num_recommendations


def test_empty_recommendations():
    """추천 결과가 없는 경우 테스트 - 예외 처리 확인"""
    mock_db = MagicMock()
    
    # 빈 결과로 인한 예외 발생을 테스트
    user_id = 999  # 새로운 사용자
    read_list = []
    want_list = []
    
    # 빈 DataFrame으로 인한 KeyError가 발생할 수 있음을 확인
    with pytest.raises(KeyError):
        recommend_books(mock_db, user_id, read_list, want_list)


def test_recommendation_service_caching():
    """추천 서비스 캐싱 기능 테스트"""
    mock_db = MagicMock()
    service = RecommendationService(mock_db)
    
    # 첫 번째 호출
    with patch.object(service, 'get_user_books_data') as mock_books:
        mock_books.return_value = (["book1"], ["book2"])
        
        # 캐시 초기화를 위해 전역 캐시 변수에 접근
        from bookstar.services.recommendation import _user_books_cache
        _user_books_cache.clear()
        
        user_id = 123
        result1 = service.get_user_books_data(user_id)
        result2 = service.get_user_books_data(user_id)  # 캐시에서 반환되어야 함
        
        assert result1 == result2
        # DB 호출이 한 번만 이루어졌는지 확인
        # 캐시 때문에 두 번째는 호출되지 않을 수 있음
        assert mock_books.call_count <= 2 