import logging
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from bookstar.config import settings
from bookstar.config.logging_config import logging_config
from bookstar.database.connection import get_db
from bookstar.models.models import MemberBook
from bookstar.schemas.schemas import UserRequest
from bookstar.services.recommendation import recommend_books
from bookstar.utils.decorators import log_async_execution_time


# 로깅 시스템 초기화
@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 애플리케이션 시작 시 - 모든 로깅 설정 적용
    logging_config.setup_logging(
        log_level=settings.logging['level'],
        use_json=settings.logging['use_json'],
        enable_console=settings.logging['enable_console'],
        max_file_size_mb=settings.logging['max_file_size_mb'],
        backup_count=settings.logging['backup_count'],
        enable_access_log=settings.logging['enable_access_log'],
        enable_performance_log=settings.logging['enable_performance_log'],
        enable_traceback_log=settings.logging['enable_traceback_log'],
        main_log_retention_days=settings.logging['main_log_retention_days'],
        error_log_retention_days=settings.logging['error_log_retention_days'],
        access_log_retention_days=settings.logging['access_log_retention_days'],
        performance_log_retention_days=settings.logging['performance_log_retention_days'],
        traceback_log_retention_days=settings.logging['traceback_log_retention_days']
    )
    
    logger = logging.getLogger(__name__)
    logger.info("BookStar AI 애플리케이션이 시작되었습니다.")
    logger.info(f"로그 설정: {settings.logging}")
    
    yield
    
    # 애플리케이션 종료 시
    logger.info("BookStar AI 애플리케이션이 종료되었습니다.")
app = FastAPI(
    title="BookStar AI", 
    description="AI 기반 도서 추천 시스템",
    lifespan=lifespan
)

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app['cors_origins'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 요청 로깅 미들웨어
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """HTTP 요청을 로깅하는 미들웨어"""
    start_time = time.perf_counter()
    
    # 액세스 로거
    access_logger = logging_config.get_access_logger()
    
    # 요청 정보 로깅
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    request_id = str(time.time_ns())[-8:]  # 간단한 요청 ID
    
    access_logger.info(
        f"[{request_id}] 요청 시작: {request.method} {request.url.path}",
        extra={
            'request_id': request_id,
            'method': request.method,
            'path': request.url.path,
            'client_ip': client_ip,
            'user_agent': user_agent,
            'query_params': str(request.query_params)
        }
    )
    
    try:
        response = await call_next(request)
        
        # 응답 시간 계산
        process_time = (time.perf_counter() - start_time) * 1000
        
        # 응답 로깅
        access_logger.info(
            f"[{request_id}] 요청 완료: {request.method} {request.url.path} - "
            f"상태코드: {response.status_code}, 처리시간: {process_time:.2f}ms",
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.url.path,
                'status_code': response.status_code,
                'response_time_ms': process_time,
                'client_ip': client_ip
            }
        )
        
        # 응답 헤더에 요청 ID 추가
        response.headers["X-Request-ID"] = request_id
        return response
        
    except Exception as e:
        process_time = (time.perf_counter() - start_time) * 1000
        
        access_logger.error(
            f"[{request_id}] 요청 실패: {request.method} {request.url.path} - "
            f"처리시간: {process_time:.2f}ms, 오류: {str(e)}",
            exc_info=True,
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.url.path,
                'response_time_ms': process_time,
                'client_ip': client_ip,
                'error': str(e)
            }
        )
        raise


@app.post("/recommend_books")
@log_async_execution_time(threshold_ms=settings.logging['performance_threshold_ms'])
async def get_recommendations(user: UserRequest, db: Session = Depends(get_db)):
    """도서 추천 API 엔드포인트"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"도서 추천 요청: 사용자 ID = {user.user_id}")
        
        # 사용자 도서 정보 조회
        member_books = (
            db.query(MemberBook)
            .filter(MemberBook.member_id == user.user_id)
            .all() or []
        )

        read_list = [
            str(book.book_id) 
            for book in member_books 
            if book.reading_status.value in ["READED", "READING"]
        ]
        want_list = [
            str(book.book_id) 
            for book in member_books 
            if book.reading_status.value == "WANT_TO_READ"
        ]

        logger.info(
            f"사용자 도서 정보 조회 완료: 읽은 책 {len(read_list)}권, "
            f"읽고 싶은 책 {len(want_list)}권",
            extra={
                'user_id': user.user_id,
                'read_books_count': len(read_list),
                'want_books_count': len(want_list)
            }
        )
        
        logger.debug(f"읽은 책 목록: {read_list}")
        logger.debug(f"읽고 싶은 책 목록: {want_list}")

        if not read_list and not want_list:
            logger.warning(
                f"사용자 {user.user_id}의 도서 이력이 없어 랜덤 추천을 진행합니다.",
                extra={'user_id': user.user_id, 'recommendation_type': 'random'}
            )
            recommendations = recommend_books(
                db=db,
                user_id=user.user_id,
                read_list=[],
                want_list=[],
                num_recommendations=settings.recommendation['default_recommendations_count']
            )
        else:
            logger.info(
                f"사용자 {user.user_id}의 도서 이력을 바탕으로 "
                f"개인화 추천을 진행합니다.",
                extra={'user_id': user.user_id, 'recommendation_type': 'personalized'}
            )
            recommendations = recommend_books(
                db=db,
                user_id=user.user_id,
                read_list=read_list,
                want_list=want_list,
                num_recommendations=settings.recommendation['default_recommendations_count']
            )

        logger.info(
            f"도서 추천 완료: 사용자 {user.user_id}에게 {len(recommendations)}권 추천",
            extra={
                'user_id': user.user_id,
                'recommendations_count': len(recommendations)
            }
        )

        return {"recommendations": recommendations}

    except Exception as e:
        logger.error(
            f"도서 추천 처리 중 오류 발생: 사용자 {user.user_id}, 오류: {str(e)}",
            exc_info=True,
            extra={'user_id': user.user_id, 'error_type': type(e).__name__}
        )
        raise HTTPException(status_code=500, detail=str(e)) from e