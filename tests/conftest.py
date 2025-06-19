"""
pytest 설정 파일
테스트 환경에서 사용할 설정들을 정의
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bookstar.config import settings
from bookstar.database import Base


@pytest.fixture(scope="session")
def engine():
    """데이터베이스 엔진"""
    engine = create_engine(settings.database_url, echo=True)
    
    # 테스트 데이터베이스에 테이블 생성
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # 테스트 종료 후 모든 테이블 삭제
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(engine):
    """실제 데이터베이스 세션"""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        yield session
    finally:
        session.rollback()  # 테스트 중 변경사항 롤백
        session.close() 