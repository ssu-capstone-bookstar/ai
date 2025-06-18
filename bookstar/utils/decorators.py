"""
데코레이터 유틸리티 모듈
함수 실행시간 측정, 로깅, 재시도 등의 데코레이터 제공
"""
import functools
import logging
import time
import uuid
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar

# 타입 힌트를 위한 제네릭 타입
P = ParamSpec('P')
T = TypeVar('T')


def log_execution_time(
    logger: logging.Logger | None = None,
    log_level: int = logging.INFO,
    include_args: bool = False,
    include_result: bool = False,
    threshold_ms: float | None = None
):
    """
    함수 실행시간을 측정하고 로그에 기록하는 데코레이터
    
    Args:
        logger: 사용할 로거 (없으면 기본 로거 사용)
        log_level: 로그 레벨
        include_args: 함수 인자를 로그에 포함할지 여부
        include_result: 함수 결과를 로그에 포함할지 여부  
        threshold_ms: 이 시간(ms) 이상 걸린 경우만 로그 기록
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start_time = time.perf_counter()
            request_id = str(uuid.uuid4())[:8]
            
            func_logger = logger or logging.getLogger(func.__module__)
            performance_logger = logging.getLogger('performance')
            
            # 함수 시작 로그
            func_logger.debug(
                f"[{request_id}] 함수 실행 시작: {func.__name__}",
                extra={'request_id': request_id}
            )
            
            try:
                # 함수 실행
                if include_args:
                    func_logger.debug(
                        f"[{request_id}] 함수 인자: args={args}, kwargs={kwargs}",
                        extra={'request_id': request_id}
                    )
                
                result = func(*args, **kwargs)
                
                # 실행시간 계산
                end_time = time.perf_counter()
                execution_time_ms = (end_time - start_time) * 1000
                
                # threshold 체크
                if threshold_ms is None or execution_time_ms >= threshold_ms:
                    # 일반 로그
                    func_logger.log(
                        log_level,
                        f"[{request_id}] {func.__name__} 실행 완료 - "
                        f"{execution_time_ms:.2f}ms",
                        extra={
                            'request_id': request_id,
                            'execution_time': execution_time_ms
                        }
                    )
                    
                    # 성능 로그 (별도 파일)
                    performance_logger.info(
                        f"{func.__module__}.{func.__name__}",
                        extra={
                            'request_id': request_id,
                            'execution_time': execution_time_ms,
                            'function_name': func.__name__,
                            'module_name': func.__module__,
                            'args_count': len(args),
                            'kwargs_count': len(kwargs)
                        }
                    )
                
                if include_result:
                    func_logger.debug(
                        f"[{request_id}] 함수 결과: {result}",
                        extra={'request_id': request_id}
                    )
                
                return result
                
            except Exception as e:
                end_time = time.perf_counter()
                execution_time_ms = (end_time - start_time) * 1000
                
                func_logger.error(
                    f"[{request_id}] {func.__name__} 실행 실패 - "
                    f"{execution_time_ms:.2f}ms: {str(e)}",
                    exc_info=True,
                    extra={
                        'request_id': request_id,
                        'execution_time': execution_time_ms
                    }
                )
                raise
        
        return wrapper
    return decorator


def log_async_execution_time(
    logger: logging.Logger | None = None,
    log_level: int = logging.INFO,
    include_args: bool = False,
    include_result: bool = False,
    threshold_ms: float | None = None
):
    """
    비동기 함수 실행시간을 측정하고 로그에 기록하는 데코레이터
    """
    def decorator(func: Callable[P, Any]) -> Callable[P, Any]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            start_time = time.perf_counter()
            request_id = str(uuid.uuid4())[:8]
            
            func_logger = logger or logging.getLogger(func.__module__)
            performance_logger = logging.getLogger('performance')
            
            # 함수 시작 로그
            func_logger.debug(
                f"[{request_id}] 비동기 함수 실행 시작: {func.__name__}",
                extra={'request_id': request_id}
            )
            
            try:
                if include_args:
                    func_logger.debug(
                        f"[{request_id}] 함수 인자: args={args}, kwargs={kwargs}",
                        extra={'request_id': request_id}
                    )
                
                result = await func(*args, **kwargs)
                
                end_time = time.perf_counter()
                execution_time_ms = (end_time - start_time) * 1000
                
                if threshold_ms is None or execution_time_ms >= threshold_ms:
                    func_logger.log(
                        log_level,
                        f"[{request_id}] {func.__name__} 비동기 실행 완료 - "
                        f"{execution_time_ms:.2f}ms",
                        extra={
                            'request_id': request_id,
                            'execution_time': execution_time_ms
                        }
                    )
                    
                    performance_logger.info(
                        f"{func.__module__}.{func.__name__} (async)",
                        extra={
                            'request_id': request_id,
                            'execution_time': execution_time_ms,
                            'function_name': func.__name__,
                            'module_name': func.__module__,
                            'is_async': True
                        }
                    )
                
                if include_result:
                    func_logger.debug(
                        f"[{request_id}] 함수 결과: {result}",
                        extra={'request_id': request_id}
                    )
                
                return result
                
            except Exception as e:
                end_time = time.perf_counter()
                execution_time_ms = (end_time - start_time) * 1000
                
                func_logger.error(
                    f"[{request_id}] {func.__name__} 비동기 실행 실패 - "
                    f"{execution_time_ms:.2f}ms: {str(e)}",
                    exc_info=True,
                    extra={
                        'request_id': request_id,
                        'execution_time': execution_time_ms
                    }
                )
                raise
        
        return wrapper
    return decorator


def retry_with_logging(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    logger: logging.Logger | None = None
):
    """
    실패시 재시도하는 데코레이터 (로깅 포함)
    
    Args:
        max_attempts: 최대 시도 횟수
        delay: 재시도 간격 (초)
        backoff_factor: 재시도 간격 증가 배수
        exceptions: 재시도할 예외 타입들
        logger: 사용할 로거
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            func_logger = logger or logging.getLogger(func.__module__)
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        func_logger.error(
                            f"{func.__name__} 최종 실패 - "
                            f"{max_attempts}회 시도 후 포기: {str(e)}",
                            exc_info=True
                        )
                        raise
                    
                    func_logger.warning(
                        f"{func.__name__} 시도 {attempt + 1}/{max_attempts} "
                        f"실패: {str(e)} - {current_delay:.1f}초 후 재시도"
                    )
                    
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
                except Exception as e:
                    # 재시도하지 않을 예외는 바로 로그 후 재발생
                    func_logger.error(
                        f"{func.__name__} 실행 실패 (재시도하지 않음): {str(e)}",
                        exc_info=True
                    )
                    raise
            
            # 이 코드는 실행되지 않음 (mypy를 위한 unreachable 코드)
            raise RuntimeError("Unexpected code path")
        
        return wrapper
    return decorator


def log_database_operations(
    logger: logging.Logger | None = None,
    log_queries: bool = True,
    log_results: bool = False
):
    """
    데이터베이스 작업을 로깅하는 데코레이터
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            func_logger = logger or logging.getLogger('database')
            request_id = str(uuid.uuid4())[:8]
            start_time = time.perf_counter()
            
            try:
                if log_queries:
                    func_logger.info(
                        f"[{request_id}] DB 작업 시작: {func.__name__}",
                        extra={'request_id': request_id, 'operation': func.__name__}
                    )
                
                result = func(*args, **kwargs)
                
                end_time = time.perf_counter()
                execution_time_ms = (end_time - start_time) * 1000
                
                func_logger.info(
                    f"[{request_id}] DB 작업 완료: {func.__name__} - "
                    f"{execution_time_ms:.2f}ms",
                    extra={
                        'request_id': request_id,
                        'operation': func.__name__,
                        'execution_time': execution_time_ms
                    }
                )
                
                if log_results and result is not None:
                    if hasattr(result, '__len__'):
                        func_logger.debug(
                            f"[{request_id}] DB 결과: {len(result)}개 레코드",
                            extra={
                                'request_id': request_id, 
                                'record_count': len(result)
                            }
                        )
                    else:
                        func_logger.debug(
                            f"[{request_id}] DB 결과: {type(result).__name__}",
                            extra={'request_id': request_id}
                        )
                
                return result
                
            except Exception as e:
                end_time = time.perf_counter()
                execution_time_ms = (end_time - start_time) * 1000
                
                func_logger.error(
                    f"[{request_id}] DB 작업 실패: {func.__name__} - "
                    f"{execution_time_ms:.2f}ms: {str(e)}",
                    exc_info=True,
                    extra={
                        'request_id': request_id,
                        'operation': func.__name__,
                        'execution_time': execution_time_ms
                    }
                )
                raise
        
        return wrapper
    return decorator


def validate_and_log(
    input_validator: Callable | None = None,
    output_validator: Callable | None = None,
    logger: logging.Logger | None = None
):
    """
    입력/출력 검증과 로깅을 수행하는 데코레이터
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            func_logger = logger or logging.getLogger(func.__module__)
            request_id = str(uuid.uuid4())[:8]
            
            try:
                # 입력 검증
                if input_validator:
                    input_validator(*args, **kwargs)
                    func_logger.debug(
                        f"[{request_id}] {func.__name__} 입력 검증 통과",
                        extra={'request_id': request_id}
                    )
                
                result = func(*args, **kwargs)
                
                # 출력 검증
                if output_validator:
                    output_validator(result)
                    func_logger.debug(
                        f"[{request_id}] {func.__name__} 출력 검증 통과",
                        extra={'request_id': request_id}
                    )
                
                return result
                
            except Exception as e:
                func_logger.error(
                    f"[{request_id}] {func.__name__} 검증 또는 실행 실패: {str(e)}",
                    exc_info=True,
                    extra={'request_id': request_id}
                )
                raise
        
        return wrapper
    return decorator 