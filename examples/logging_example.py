"""
로깅 시스템 사용 예제
BookStar AI 프로젝트의 로깅 시스템 사용법을 보여주는 파일
"""
import logging
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bookstar.config import settings
from bookstar.config.logging_config import logging_config
from bookstar.utils.decorators import (
    log_database_operations,
    log_execution_time,
    retry_with_logging,
    validate_and_log,
)

# 로깅 시스템 초기화 (실제 앱에서는 main.py에서 수행)
logging_config.setup_logging(
    log_level="DEBUG",
    use_json=False,  # True로 하면 JSON 형식 로그
    enable_console=True
)

# 로거 인스턴스 가져오기
logger = logging.getLogger(__name__)
performance_logger = logging_config.get_performance_logger()
access_logger = logging_config.get_access_logger()

# 기본 로깅 예제
def basic_logging_example():
    """기본 로깅 사용 예제"""
    logger.debug("디버그 메시지 - 개발 중에만 표시")
    logger.info("정보 메시지 - 일반적인 애플리케이션 흐름")
    logger.warning("경고 메시지 - 잠재적 문제 상황")
    logger.error("에러 메시지 - 예외가 발생했지만 애플리케이션은 계속 실행")
    logger.critical("치명적 메시지 - 애플리케이션이 중단될 수 있는 심각한 문제")

# 구조화된 로깅 예제 (extra 필드 사용)
def structured_logging_example():
    """구조화된 로깅 사용 예제"""
    user_id = 12345
    action = "book_recommendation"
    
    logger.info(
        f"사용자 {user_id}가 도서 추천을 요청했습니다",
        extra={
            'user_id': user_id,
            'action': action,
            'timestamp': time.time(),
            'request_source': 'web_app'
        }
    )

# 실행시간 측정 데코레이터 예제
@log_execution_time(
    threshold_ms=settings.logging['performance_threshold_ms']
)  # 설정값 사용
def slow_function():
    """느린 함수 시뮬레이션"""
    logger.info("시간이 오래 걸리는 작업을 시작합니다...")
    time.sleep(0.2)  # 200ms 대기
    return "작업 완료"

@log_execution_time(include_args=True, include_result=True)
def function_with_args_logging(name: str, age: int, city: str = "Seoul"):
    """인자와 결과를 로깅하는 함수"""
    result = f"{name}님은 {age}세이고 {city}에 살고 있습니다"
    return result

# 데이터베이스 작업 시뮬레이션
@log_database_operations(log_results=True)
def simulate_db_query(table_name: str, limit: int = 10):
    """데이터베이스 쿼리 시뮬레이션"""
    logger.info(f"{table_name} 테이블에서 {limit}개 레코드 조회 중...")
    time.sleep(0.05)  # DB 쿼리 시뮬레이션
    return [{"id": i, "name": f"record_{i}"} for i in range(limit)]

# 재시도 로직 예제
@retry_with_logging(max_attempts=3, delay=0.1)
def unreliable_function(fail_count: int = 2):
    """실패할 수 있는 함수 시뮬레이션"""
    # 전역 변수로 호출 횟수 추적
    if not hasattr(unreliable_function, 'call_count'):
        unreliable_function.call_count = 0
    
    unreliable_function.call_count += 1
    
    if unreliable_function.call_count <= fail_count:
        raise ConnectionError(
            f"네트워크 오류 발생 (시도 {unreliable_function.call_count})"
        )
    
    return "성공!"

# 입력 검증 예제
def validate_user_input(user_id: int, name: str):
    """사용자 입력 검증"""
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("user_id는 양의 정수여야 합니다")
    if not isinstance(name, str) or len(name.strip()) == 0:
        raise ValueError("name은 빈 문자열이 아니어야 합니다")

def validate_output(result):
    """출력 검증"""
    if not isinstance(result, dict) or 'status' not in result:
        raise ValueError("결과는 'status' 키를 포함한 딕셔너리여야 합니다")

@validate_and_log(
    input_validator=lambda user_id, name: validate_user_input(user_id, name),
    output_validator=validate_output
)
def process_user_data(user_id: int, name: str):
    """사용자 데이터 처리 (검증 포함)"""
    logger.info(f"사용자 데이터 처리: ID={user_id}, Name={name}")
    
    # 비즈니스 로직
    processed_name = name.strip().title()
    
    return {
        'status': 'success',
        'user_id': user_id,
        'processed_name': processed_name,
        'message': f"안녕하세요, {processed_name}님!"
    }

# 예외 처리와 traceback 로깅 예제
def exception_logging_example():
    """예외 처리와 traceback 로깅 예제"""
    try:
        # 의도적으로 예외 발생
        _ = 10 / 0
    except ZeroDivisionError:
        logger.error(
            "0으로 나누기 오류가 발생했습니다",
            exc_info=True,  # traceback 정보 포함
            extra={
                'error_type': 'ZeroDivisionError',
                'operation': 'division',
                'operands': [10, 0]
            }
        )
    
    try:
        # 파일 접근 오류
        with open('nonexistent_file.txt') as f:
            _ = f.read()
    except FileNotFoundError:
        logger.error(
            "파일을 찾을 수 없습니다",
            exc_info=True,
            extra={
                'error_type': 'FileNotFoundError',
                'target_file': 'nonexistent_file.txt',
                'operation': 'file_read'
            }
        )

# 성능 로깅 예제
def performance_logging_example():
    """성능 로깅 전용 예제"""
    # 성능 로그는 별도 파일에 저장됨
    performance_logger.info(
        "사용자 추천 알고리즘 성능 측정",
        extra={
            'algorithm': 'hybrid_recommendation',
            'execution_time': 250.5,
            'user_count': 1000,
            'recommendation_count': 10,
            'cache_hit_rate': 0.85
        }
    )

# 액세스 로깅 예제  
def access_logging_example():
    """액세스 로깅 전용 예제"""
    # 액세스 로그는 별도 파일에 저장됨
    access_logger.info(
        "API 엔드포인트 접근",
        extra={
            'method': 'POST',
            'endpoint': '/recommend_books',
            'user_id': 12345,
            'ip_address': '192.168.1.100',
            'user_agent': 'BookStar Mobile App v1.0',
            'response_time_ms': 180.2,
            'status_code': 200
        }
    )

def main():
    """모든 로깅 예제를 실행하는 메인 함수"""
    logger.info("=== BookStar AI 로깅 시스템 예제 ===")
    
    logger.info("1. 기본 로깅 예제")
    basic_logging_example()
    
    logger.info("2. 구조화된 로깅 예제")
    structured_logging_example()
    
    logger.info("3. 실행시간 측정 데코레이터 예제")
    result = slow_function()
    logger.info(f"결과: {result}")
    
    logger.info("4. 인자/결과 로깅 데코레이터 예제")
    result = function_with_args_logging("김철수", 30, "부산")
    logger.info(f"결과: {result}")
    
    logger.info("5. 데이터베이스 작업 로깅 예제")
    db_result = simulate_db_query("users", 5)
    logger.info(f"DB 결과: {len(db_result)}개 레코드")
    
    logger.info("6. 재시도 로직 예제")
    try:
        # 호출 횟수 초기화
        if hasattr(unreliable_function, 'call_count'):
            delattr(unreliable_function, 'call_count')
        
        retry_result = unreliable_function(fail_count=2)
        logger.info(f"재시도 결과: {retry_result}")
    except Exception as e:
        logger.info(f"재시도 최종 실패: {e}")
    
    logger.info("7. 입력/출력 검증 예제")
    try:
        validation_result = process_user_data(12345, "  김영희  ")
        logger.info(f"검증 결과: {validation_result}")
    except Exception as e:
        logger.info(f"검증 실패: {e}")
    
    logger.info("8. 예외 처리와 traceback 로깅 예제")
    exception_logging_example()
    
    logger.info("9. 성능 로깅 예제")
    performance_logging_example()
    
    logger.info("10. 액세스 로깅 예제")
    access_logging_example()
    
    logger.info("=== 로깅 시스템 예제 완료 ===")
    logger.info("로그 파일들은 'logs/' 디렉토리에 저장되었습니다:")
    logger.info("- bookstar.log (전체 로그)")
    logger.info("- bookstar_error.log (에러 로그)")
    logger.info("- bookstar_access.log (액세스 로그)")
    logger.info("- bookstar_performance.log (성능 로그)")
    logger.info("- bookstar_traceback.log (traceback 로그)")

if __name__ == "__main__":
    main()