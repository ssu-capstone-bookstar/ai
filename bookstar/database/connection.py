import logging
import time

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

from bookstar.config import settings

# 데이터베이스 로거 설정
db_logger = logging.getLogger('database')

# SQLAlchemy 쿼리 로깅을 위한 이벤트 리스너
@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """쿼리 실행 전 로깅"""
    conn.info.setdefault('query_start_time', []).append(time.perf_counter())
    db_logger.debug(
        f"쿼리 실행 시작: {statement[:200]}...",
        extra={'query_type': 'start', 'parameters': str(parameters)[:500]}
    )

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """쿼리 실행 후 로깅"""
    total = time.perf_counter() - conn.info['query_start_time'].pop(-1)
    total_ms = total * 1000
    
    if total_ms > settings.logging['db_threshold_ms']:  # config.toml 설정 사용
        db_logger.warning(
            f"느린 쿼리 감지: {total_ms:.2f}ms - {statement[:200]}...",
            extra={
                'query_type': 'slow',
                'execution_time_ms': total_ms,
                'parameters': str(parameters)[:500]
            }
        )
    else:
        db_logger.debug(
            f"쿼리 실행 완료: {total_ms:.2f}ms",
            extra={
                'query_type': 'complete',
                'execution_time_ms': total_ms
            }
        )

# SQLAlchemy 엔진 생성
# 비밀번호를 제외한 DB URL 로깅
db_url_safe = settings.database_url.split('@')[-1]
db_logger.info(f"데이터베이스 엔진 생성 중: {db_url_safe}")
engine = create_engine(settings.database_url, echo=False)  # echo=False로 중복 로그 방지
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """데이터베이스 세션을 제공하는 의존성 함수"""
    db = SessionLocal()
    session_id = str(id(db))[-6:]  # 세션 ID
    
    db_logger.debug(f"[{session_id}] 데이터베이스 세션 생성")
    
    try:
        yield db
    except Exception as e:
        db_logger.error(
            f"[{session_id}] 데이터베이스 세션 오류: {str(e)}",
            exc_info=True,
            extra={'session_id': session_id, 'error_type': type(e).__name__}
        )
        db.rollback()
        raise
    finally:
        db_logger.debug(f"[{session_id}] 데이터베이스 세션 종료")
        db.close()
