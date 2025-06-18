import logging
from collections import defaultdict

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sqlalchemy import func
from sqlalchemy.orm import Session

from bookstar.config import settings
from bookstar.models.models import Book, Member, MemberBook, RecommenderModel
from bookstar.utils.decorators import log_database_operations, log_execution_time

# 전역 캐시 (메모리 누수 방지를 위해 클래스 외부에서 관리)
_user_books_cache: dict[int, tuple[list[str], list[str]]] = {}
_user_preferences_cache: dict[int, dict[str, dict[str, float]]] = {}
_similar_users_cache: dict[str, list[int]] = {}

class RecommendationService:
    """추천 서비스 클래스"""
    
    def __init__(self, db: Session):
        self.db = db
        
    @log_database_operations()
    @log_execution_time(threshold_ms=settings.logging['db_threshold_ms'])
    def get_user_books_data(self, user_id: int) -> tuple[list[str], list[str]]:
        """사용자의 읽은 책과 읽고 싶은 책 목록을 효율적으로 조회"""
        logger = logging.getLogger(__name__)
        
        if user_id in _user_books_cache:
            logger.debug(f"캐시에서 사용자 {user_id} 도서 데이터 반환")
            return _user_books_cache[user_id]
            
        logger.info(f"사용자 {user_id}의 도서 데이터를 DB에서 조회 중...")
        
        member_books = (
            self.db.query(MemberBook.book_id, MemberBook.reading_status)
            .filter(MemberBook.member_id == user_id)
            .all()
        )
        
        read_list = [
            str(book_id) for book_id, status in member_books 
            if status.value in ["READED", "READING"]
        ]
        want_list = [
            str(book_id) for book_id, status in member_books 
            if status.value == "WANT_TO_READ"
        ]
        
        result = (read_list, want_list)
        _user_books_cache[user_id] = result
        
        logger.info(
            f"사용자 {user_id} 도서 데이터 조회 완료: "
        f"읽은 책 {len(read_list)}권, 읽고 싶은 책 {len(want_list)}권",
            extra={
                'user_id': user_id,
                'read_books_count': len(read_list),
                'want_books_count': len(want_list)
            }
        )
        
        return result
    
    def get_user_preferences(self, user_id: int) -> dict[str, dict[str, float]]:
        """사용자 선호도를 효율적으로 계산"""
        if user_id in _user_preferences_cache:
            return _user_preferences_cache[user_id]
            
        read_list, want_list = self.get_user_books_data(user_id)
        
        if not read_list and not want_list:
            return {}
        
        # 단일 쿼리로 카테고리와 저자 정보 조회
        book_ids_int = [int(bid) for bid in read_list + want_list]
        book_data = (
            self.db.query(Book.alading_book_id, Book.book_category, Book.author)
            .filter(Book.alading_book_id.in_(book_ids_int))
            .all()
        )
        
        category_scores: dict[str, float] = defaultdict(float)
        author_scores: dict[str, float] = defaultdict(float)
        
        for book_id, category, author in book_data:
            read_weight = settings.recommendation['read_book_weight']
            unread_weight = settings.recommendation['unread_book_weight']
            weight = read_weight if str(book_id) in read_list else unread_weight
            
            if category:
                cat_weight = settings.recommendation['category_preference_weight']
                category_scores[category.value] += cat_weight * weight
            if author:
                auth_weight = settings.recommendation['author_preference_weight']
                author_scores[author] += auth_weight * weight
        
        result = {
            'categories': dict(category_scores),
            'authors': dict(author_scores)
        }
        _user_preferences_cache[user_id] = result
        return result
    
    @log_execution_time(threshold_ms=settings.logging['api_threshold_ms'])
    def get_content_based_recommendations(
        self, 
        user_id: int, 
        num_recommendations: int | None = None
    ) -> pd.DataFrame:
        """콘텐츠 기반 추천"""
        logger = logging.getLogger(__name__)
        if num_recommendations is None:
            num_recommendations = settings.recommendation[
                'default_recommendations_count'
            ]
        logger.info(
            f"콘텐츠 기반 추천 시작: 사용자 {user_id}, 추천 개수 {num_recommendations}"
        )
        
        preferences = self.get_user_preferences(user_id)
        
        if not preferences:
            # 랜덤 추천
            logger.info(f"사용자 {user_id}의 선호도 정보가 없어 랜덤 추천으로 전환")
            return self._get_random_books(num_recommendations)
        
        # 효율적인 책 데이터 조회 (필요한 컬럼만)
        books_query = (
            self.db.query(
                Book.alading_book_id,
                Book.title,
                Book.author,
                Book.book_category,
                Book.image_url
            )
        )
        
        # 이미 읽은 책 제외
        read_list, want_list = self.get_user_books_data(user_id)
        if read_list or want_list:
            books_query = books_query.filter(
                ~Book.alading_book_id.in_(read_list + want_list)
            )
        
        books_data = books_query.all()
        
        if not books_data:
            return pd.DataFrame()
        
        # DataFrame 생성
        df = pd.DataFrame([{
            "book_id": book.alading_book_id,
            "title": book.title,
            "author": book.author,
            "book_category": book.book_category,
            "image_url": book.image_url
        } for book in books_data])
        
        # 가중치 계산 (벡터화)
        category_weights: dict[str, float] = preferences.get('categories', {})
        author_weights: dict[str, float] = preferences.get('authors', {})
        
        df['category_weight'] = df['book_category'].map(
            lambda x: (
                category_weights.get(x.value if x else '', 0) 
                if pd.notna(x) else 0
            )
        )
        df['author_weight'] = df['author'].map(
            lambda x: author_weights.get(x if x else '', 0) if pd.notna(x) else 0
        )
        df['total_weight'] = df['category_weight'] + df['author_weight']
        
        # 상위 추천 반환
        return df.nlargest(num_recommendations, 'total_weight')
    
    def _get_random_books(self, num_recommendations: int) -> pd.DataFrame:
        """랜덤 책 추천"""
        books = (
            self.db.query(
                Book.alading_book_id,
                Book.title,
                Book.author,
                Book.book_category,
                Book.image_url
            )
            .order_by(func.random())
            .limit(num_recommendations)
            .all()
        )
        
        return pd.DataFrame([{
            "book_id": book.alading_book_id,
            "title": book.title,
            "author": book.author,
            "book_category": book.book_category,
            "image_url": book.image_url
        } for book in books])
    
    def get_similar_users(
        self, 
        user_id: int, 
        num_similar_users: int | None = None
    ) -> list[int]:
        """유사 사용자 찾기 (캐시 적용)"""
        if num_similar_users is None:
            num_similar_users = settings.recommendation['similar_users_count']
        
        cache_key = f"{user_id}_{num_similar_users}"
        if cache_key in _similar_users_cache:
            return _similar_users_cache[cache_key]
        
        user_data = self._build_user_books_data()
        if not user_data or user_id not in user_data:
            return []
        
        similar_users = self._find_similar_users_knn(
            user_data, user_id, num_similar_users
        )
        
        _similar_users_cache[cache_key] = similar_users
        return similar_users
    
    def _build_user_books_data(self) -> dict[int, set[str]]:
        """사용자-도서 데이터 구축"""
        user_books_data = (
            self.db.query(MemberBook.member_id, MemberBook.book_id)
            .join(Member, Member.id == MemberBook.member_id)
            .all()
        )
        
        if not user_books_data:
            return {}
        
        user_data = defaultdict(set)
        for uid, book_id in user_books_data:
            user_data[uid].add(book_id)
        
        return dict(user_data)
    
    def _find_similar_users_knn(
        self, 
        user_data: dict[int, set[str]], 
        user_id: int, 
        num_similar_users: int
    ) -> list[int]:
        """KNN을 사용하여 유사 사용자 찾기"""
        all_books = list(set(
            book_id 
            for books in user_data.values() 
            for book_id in books
        ))
        user_ids = list(user_data.keys())
        
        if len(user_ids) < 2:
            return []
        
        feature_matrix = self._build_feature_matrix(user_data, user_ids, all_books)
        return self._compute_similar_users(
            feature_matrix, user_ids, user_id, num_similar_users
        )
    
    def _build_feature_matrix(
        self, 
        user_data: dict[int, set[str]], 
        user_ids: list[int], 
        all_books: list[str]
    ) -> np.ndarray:
        """사용자-도서 특성 매트릭스 구축"""
        feature_matrix = np.zeros((len(user_ids), len(all_books)))
        for i, uid in enumerate(user_ids):
            for j, book_id in enumerate(all_books):
                if book_id in user_data[uid]:
                    feature_matrix[i, j] = 1
        return feature_matrix
    
    def _compute_similar_users(
        self, 
        feature_matrix: np.ndarray, 
        user_ids: list[int], 
        user_id: int, 
        num_similar_users: int
    ) -> list[int]:
        """KNN으로 유사 사용자 계산"""
        try:
            n_neighbors = min(num_similar_users + 1, len(user_ids))
            knn = NearestNeighbors(n_neighbors=n_neighbors)
            knn.fit(feature_matrix)
            
            current_user_index = user_ids.index(user_id)
            distances, indices = knn.kneighbors([feature_matrix[current_user_index]])
            
            similar_user_ids = [
                user_ids[idx] for idx in indices.flatten() 
                if idx != current_user_index
            ]
            
            return similar_user_ids[:num_similar_users]
        except Exception as e:
            logging.warning(f"유사 사용자 찾기 실패: {e}")
            return []
    
    def get_collaborative_recommendations(
        self, 
        user_id: int, 
        num_recommendations: int | None = None
    ) -> pd.DataFrame:
        """협업 필터링 기반 추천"""
        if num_recommendations is None:
            num_recommendations = settings.recommendation[
                'default_recommendations_count'
            ]
        similar_users = self.get_similar_users(user_id)
        
        if not similar_users:
            return pd.DataFrame()
        
        # 유사 사용자들이 읽은 책 조회
        similar_user_books = (
            self.db.query(MemberBook.book_id)
            .filter(MemberBook.member_id.in_(similar_users))
            .distinct()
            .all()
        )
        
        if not similar_user_books:
            return pd.DataFrame()
        
        book_ids = [book[0] for book in similar_user_books]
        
        # 현재 사용자가 이미 읽은 책 제외
        read_list, want_list = self.get_user_books_data(user_id)
        book_ids = [bid for bid in book_ids if bid not in read_list + want_list]
        
        if not book_ids:
            return pd.DataFrame()
        
        # 책 정보 조회
        books = (
            self.db.query(
                Book.alading_book_id,
                Book.title,
                Book.author,
                Book.book_category,
                Book.image_url
            )
            .filter(Book.alading_book_id.in_(book_ids))
            .limit(num_recommendations)
            .all()
        )
        
        return pd.DataFrame([{
            "book_id": book.alading_book_id,
            "title": book.title,
            "author": book.author,
            "book_category": book.book_category,
            "image_url": book.image_url
        } for book in books])

def get_cached_model(db: Session, cache_key: str) -> RecommenderModel | None:
    """모델 캐시에서 모델 조회"""
    # 현재는 사용하지 않음
    return None

def cache_model(cache_key: str, model: RecommenderModel):
    """모델을 캐시에 저장"""
    # 현재는 사용하지 않음
    pass

@log_execution_time(threshold_ms=settings.logging['heavy_threshold_ms'])
def recommend_books(
    db: Session, 
    user_id: int, 
    read_list: list[str], 
    want_list: list[str], 
    num_recommendations: int | None = None
) -> list[dict]:
    """
    개선된 추천 시스템
    콘텐츠 기반 + 협업 필터링 하이브리드 방식
    """
    logger = logging.getLogger(__name__)
    if num_recommendations is None:
        num_recommendations = settings.recommendation['default_recommendations_count']
    logger.info(
        f"하이브리드 추천 시스템 시작: 사용자 {user_id}, 읽은 책 {len(read_list)}권, "
        f"읽고 싶은 책 {len(want_list)}권, 추천 개수 {num_recommendations}",
        extra={
            'user_id': user_id,
            'read_books_count': len(read_list),
            'want_books_count': len(want_list),
            'num_recommendations': num_recommendations
        }
    )
    
    try:
        service = RecommendationService(db)
        
        # 콘텐츠 기반 추천
        logger.info(f"콘텐츠 기반 추천 실행 중: 사용자 {user_id}")
        content_recommendations = service.get_content_based_recommendations(
            user_id, num_recommendations
        )
        
        # 협업 필터링 기반 추천
        logger.info(f"협업 필터링 추천 실행 중: 사용자 {user_id}")
        collaborative_recommendations = service.get_collaborative_recommendations(
            user_id, num_recommendations // 2
        )
        
        # 두 추천 결과 결합
        content_empty = content_recommendations.empty
        collaborative_empty = collaborative_recommendations.empty
        
        if not content_empty and not collaborative_empty:
            # 가중치 적용하여 결합
            content_recommendations['source'] = 'content'
            collaborative_recommendations['source'] = 'collaborative'
            
            combined_df = pd.concat([
                content_recommendations.head(num_recommendations // 2),
                collaborative_recommendations
            ]).drop_duplicates(subset=['book_id'])
            
        elif not content_empty:
            combined_df = content_recommendations
        elif not collaborative_empty:
            combined_df = collaborative_recommendations
        else:
            # 랜덤 추천
            combined_df = service._get_random_books(num_recommendations)
        
        # 최종 결과 반환
        final_recommendations = combined_df.head(num_recommendations)
        
        logger.info(
            f"추천 완료: 사용자 {user_id}에게 {len(final_recommendations)}권 추천",
            extra={
                'user_id': user_id,
                'final_recommendations_count': len(final_recommendations),
                'content_count': (
                    len(content_recommendations) if not content_empty else 0
                ),
                'collaborative_count': (
                    len(collaborative_recommendations) 
                    if not collaborative_empty else 0
                )
            }
        )
        
        return final_recommendations[
            ['book_id', 'title', 'author', 'book_category', 'image_url']
        ].to_dict(orient='records')
        
    except Exception as e:
        logger.error(
            f"추천 시스템 오류 발생: 사용자 {user_id}, 오류: {str(e)}",
            exc_info=True,
            extra={'user_id': user_id, 'error_type': type(e).__name__}
        )
        # 오류 발생 시 랜덤 추천
        logger.info(f"사용자 {user_id}에게 랜덤 추천으로 전환")
        service = RecommendationService(db)
        random_books = service._get_random_books(num_recommendations)
        return random_books[
            ['book_id', 'title', 'author', 'book_category', 'image_url']
        ].to_dict(orient='records')

# 하위 호환성을 위한 기존 함수들 (deprecated)
def create_user_item_matrix(db: Session, user_id: int):
    """Deprecated: 하위 호환성을 위해 유지"""
    logging.warning(
        "create_user_item_matrix는 deprecated됩니다. "
        "RecommendationService를 사용하세요."
    )
    return np.array([]), [], []

def train_model(user_item_matrix, num_epochs=None, learning_rate=None):
    """Deprecated: 하위 호환성을 위해 유지"""
    if num_epochs is None:
        num_epochs = settings.recommendation['num_epochs']
    if learning_rate is None:
        learning_rate = settings.recommendation['learning_rate']
    logging.warning(
        "train_model은 deprecated됩니다. "
        "RecommendationService를 사용하세요."
    )
    return None

def recommend_with_pytorch(model, user_id_index, all_books, top_n=5):
    """Deprecated: 하위 호환성을 위해 유지"""
    logging.warning(
        "recommend_with_pytorch는 deprecated됩니다. "
        "RecommendationService를 사용하세요."
    )
    return []

def calculate_author_weight(author, books, read_list, want_list):
    """Deprecated: 하위 호환성을 위해 유지"""
    logging.warning(
        "calculate_author_weight는 deprecated됩니다. "
        "RecommendationService를 사용하세요."
    )
    return 0

def calculate_category_weight(book_category: str, total_categories: dict) -> float:
    """Deprecated: 하위 호환성을 위해 유지"""
    logging.warning(
        "calculate_category_weight는 deprecated됩니다. "
        "RecommendationService를 사용하세요."
    )
    return 0

def get_user_preference_categories(db: Session, book_ids: list) -> dict:
    """Deprecated: 하위 호환성을 위해 유지"""
    logging.warning(
        "get_user_preference_categories는 deprecated됩니다. "
        "RecommendationService를 사용하세요."
    )
    return {}

def get_similar_users(
    db: Session, 
    read_list: list, 
    user_id: int, 
    num_similar_users=2
):
    """Deprecated: 하위 호환성을 위해 유지"""
    logging.warning(
        "get_similar_users는 deprecated됩니다. "
        "RecommendationService를 사용하세요."
    )
    return []
