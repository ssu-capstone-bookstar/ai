# BookStar AI 로깅 시스템 가이드

BookStar AI 프로젝트의 종합적인 로깅 시스템 사용법을 안내합니다.

## 📋 목차

1. [로깅 시스템 개요](#로깅-시스템-개요)
2. [로그 파일 구조](#로그-파일-구조)
3. [설정 방법](#설정-방법)
4. [기본 사용법](#기본-사용법)
5. [데코레이터 사용법](#데코레이터-사용법)
6. [구조화된 로깅](#구조화된-로깅)
7. [성능 모니터링](#성능-모니터링)
8. [예외 처리와 Traceback](#예외-처리와-traceback)
9. [로그 파일 관리](#로그-파일-관리)
10. [모범 사례](#모범-사례)

## 🚀 로깅 시스템 개요

BookStar AI는 파이썬의 표준 `logging` 모듈을 기반으로 한 종합적인 로깅 시스템을 제공합니다.

### 주요 기능
- ✅ **다양한 로그 레벨**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- ✅ **파일별 로그 분리**: 전체, 에러, 액세스, 성능, traceback
- ✅ **통합 로그 로테이션**: 모든 로그 파일이 시간 기반으로 자동 관리
- ✅ **자동 보관 정책**: 로그 유형별 최적화된 보관 기간
- ✅ **JSON 포맷 지원**: 구조화된 로그 출력
- ✅ **실행시간 측정**: 함수별 성능 모니터링
- ✅ **자동 Traceback 저장**: 예외 발생시 상세한 오류 정보 저장
- ✅ **데이터베이스 쿼리 로깅**: 느린 쿼리 자동 감지
- ✅ **HTTP 요청 로깅**: 모든 API 요청/응답 로깅

## 📁 로그 파일 구조

```
logs/
├── bookstar.log              # 📄 전체 로그 (일일 로테이션, 14일 보관)
├── bookstar_error.log        # ❌ 에러 전용 (일일 로테이션, 30일 보관)
├── bookstar_access.log       # 🌐 HTTP 요청 로그 (일일 로테이션, 7일 보관)
├── bookstar_performance.log  # ⚡ 성능 측정 로그 (일일 로테이션, 10일 보관)
└── bookstar_traceback.log    # 🔍 상세 예외 정보 (일일 로테이션, 60일 보관)
```

### 🕒 **통합 로테이션 시스템**
- **로테이션 방식**: 모든 로그 파일이 **매일 자정**에 로테이션
- **자동 압축**: 오래된 로그 파일은 자동으로 gzip 압축
- **자동 정리**: 설정된 보관 기간 후 자동 삭제
- **일관된 관리**: 모든 로그 파일이 동일한 시간 기반 정책 적용

### 📊 **로그 보관 정책**
| 로그 파일 | 보관 기간 | 용도 | 비고 |
|-----------|-----------|------|------|
| `bookstar.log` | 14일 | 일반 디버깅 | 전체 로그 통합 |
| `bookstar_error.log` | 30일 | 문제 해결 | 에러 분석 중요 |
| `bookstar_access.log` | 7일 | 트래픽 분석 | 단기 모니터링 |
| `bookstar_performance.log` | 10일 | 성능 최적화 | 성능 트렌드 분석 |
| `bookstar_traceback.log` | 60일 | 상세 디버깅 | 가장 오래 보관 |

## ⚙️ 설정 방법

### config.toml 설정 (최신)

```toml
[logging]
# === 기본 로그 설정 ===
level = "INFO"                      # 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
use_json = false                    # JSON 형식 로그 출력 여부
enable_console = true               # 콘솔 출력 여부
log_dir = "logs"                    # 로그 파일 저장 디렉토리

# === 로그 파일 관리 ===
max_file_size_mb = 10               # 로그 파일 최대 크기 (MB)
backup_count = 5                    # 로그 파일 백업 개수

# === 로그 유형 활성화 ===
enable_access_log = true            # HTTP 요청/응답 로그
enable_performance_log = true       # 성능 측정 로그
enable_traceback_log = true         # 상세 예외 정보 로그

# === 성능 임계값 설정 (ms) ===
performance_threshold_ms = 100      # 기본 성능 로그 임계값
db_query_threshold_ms = 50          # 데이터베이스 쿼리 임계값
api_processing_threshold_ms = 200   # API 처리 임계값
heavy_computation_threshold_ms = 500 # 무거운 연산 임계값

# === 로그 보관 정책 (일 단위) ===
# 모든 로그 파일이 시간 기반 로테이션으로 자동 관리됩니다
main_log_retention_days = 14        # 전체 로그 (일반적인 디버깅)
error_log_retention_days = 30       # 에러 로그 (문제 해결용)
access_log_retention_days = 7       # 액세스 로그 (트래픽 분석)
performance_log_retention_days = 10 # 성능 로그 (최적화 분석)
traceback_log_retention_days = 60   # Traceback 로그 (상세 디버깅, 가장 오래 보관)
```

### 환경변수 설정

```bash
export LOG_LEVEL=DEBUG  # 개발 환경
export LOG_LEVEL=INFO   # 운영 환경
```

## 📝 기본 사용법

### 로거 인스턴스 가져오기

```python
import logging
from bookstar.config.logging_config import logging_config

# 기본 로거
logger = logging.getLogger(__name__)

# 전용 로거들
performance_logger = logging_config.get_performance_logger()
access_logger = logging_config.get_access_logger()
```

### 기본 로깅

```python
def process_user_request(user_id: int):
    logger.debug(f"사용자 {user_id} 요청 처리 시작")
    logger.info(f"사용자 {user_id}의 데이터를 조회합니다")
    logger.warning(f"사용자 {user_id}의 캐시가 만료되었습니다")
    logger.error(f"사용자 {user_id} 데이터 조회 실패", exc_info=True)
    logger.critical(f"데이터베이스 연결 실패")
```

## 🎯 데코레이터 사용법

### 실행시간 측정

```python
from bookstar.utils.decorators import log_execution_time, log_async_execution_time

# 동기 함수용
@log_execution_time(threshold_ms=100)  # 100ms 이상만 로그
def slow_operation():
    time.sleep(0.2)
    return "완료"

# 비동기 함수용
@log_async_execution_time(threshold_ms=200)
async def async_operation():
    await asyncio.sleep(0.3)
    return "비동기 완료"

@log_execution_time(include_args=True, include_result=True)
def process_data(data: dict, options: dict = None):
    # 함수 인자와 결과를 모두 로깅
    return {"processed": True}
```

### 데이터베이스 작업 로깅

```python
from bookstar.utils.decorators import log_database_operations

@log_database_operations(log_results=True)
def get_user_books(db: Session, user_id: int):
    return db.query(Book).filter(Book.user_id == user_id).all()
```

### 재시도 로직

```python
from bookstar.utils.decorators import retry_with_logging

@retry_with_logging(max_attempts=3, delay=1.0, backoff_factor=2.0)
def call_external_api():
    # 외부 API 호출 (실패시 자동 재시도)
    response = requests.get("https://api.example.com/data")
    return response.json()
```

### 입력/출력 검증

```python
from bookstar.utils.decorators import validate_and_log

def validate_user_input(user_id: int, name: str):
    if user_id <= 0:
        raise ValueError("user_id는 양수여야 합니다")

@validate_and_log(input_validator=validate_user_input)
def create_user(user_id: int, name: str):
    return {"id": user_id, "name": name}
```

## 📊 구조화된 로깅

### Extra 필드 사용

```python
logger.info(
    f"사용자 {user_id}가 도서 추천을 요청했습니다",
    extra={
        'user_id': user_id,
        'action': 'book_recommendation',
        'request_source': 'mobile_app',
        'timestamp': time.time(),
        'books_count': len(read_books)
    }
)
```

### JSON 형식 로깅

```python
# config.toml에서 use_json = true 설정시
# 출력 예시:
{
    "timestamp": "2024-01-15T10:30:45.123456",
    "level": "INFO",
    "logger": "bookstar.services.recommendation",
    "message": "사용자 12345가 도서 추천을 요청했습니다",
    "module": "recommendation",
    "function": "recommend_books",
    "line": 45,
    "user_id": 12345,
    "action": "book_recommendation",
    "execution_time_ms": 250.5
}
```

## ⚡ 성능 모니터링

### 자동 성능 측정

```python
@log_execution_time(threshold_ms=100)
def expensive_computation():
    # 100ms 이상 걸리면 자동으로 성능 로그에 기록
    pass
```

### 성능 로그 직접 기록

```python
performance_logger.info(
    "추천 알고리즘 성능 측정",
    extra={
        'algorithm': 'hybrid_recommendation',
        'execution_time_ms': 250.5,
        'user_count': 1000,
        'cache_hit_rate': 0.85,
        'memory_usage_mb': 45.2
    }
)
```

### 성능 임계값 활용

```python
from bookstar.config import settings

# 설정에서 임계값 가져오기
db_threshold = settings.logging['db_query_threshold_ms']
api_threshold = settings.logging['api_processing_threshold_ms']

@log_execution_time(threshold_ms=db_threshold)
def database_query():
    # 50ms 이상 걸리면 로그 (db_query_threshold_ms)
    pass

@log_execution_time(threshold_ms=api_threshold)
def api_processing():
    # 200ms 이상 걸리면 로그 (api_processing_threshold_ms)
    pass
```

## 🔥 예외 처리와 Traceback

### 기본 예외 로깅

```python
try:
    risky_operation()
except Exception as e:
    logger.error(
        f"작업 실패: {str(e)}",
        exc_info=True,  # traceback 정보 포함
        extra={
            'error_type': type(e).__name__,
            'operation': 'risky_operation',
            'user_id': user_id
        }
    )
```

### Traceback 별도 저장

에러 레벨 로그에 `exc_info=True`를 포함하면 자동으로 `bookstar_traceback.log`에 상세한 예외 정보가 저장됩니다.

```
================================================================================
Timestamp: 2024-01-15T10:30:45.123456
Logger: bookstar.services.recommendation
Level: ERROR
Message: 추천 시스템 오류 발생
================================================================================
Traceback (most recent call last):
  File "/app/bookstar/services/recommendation.py", line 123, in recommend_books
    result = complex_calculation()
  File "/app/bookstar/services/recommendation.py", line 456, in complex_calculation
    return 10 / 0
ZeroDivisionError: division by zero
================================================================================
```

## 🗂️ **로그 파일 관리 (최신)**

### 📅 **통합 시간 기반 로테이션**

모든 로그 파일이 동일한 시간 기반 정책을 사용합니다:

```python
# 모든 로그 파일의 로테이션 설정
TimedRotatingFileHandler(
    filename="logs/bookstar.log",
    when="midnight",        # 매일 자정에 로테이션
    interval=1,             # 1일 간격
    backupCount=14,         # 14일치 보관
    encoding="utf-8"
)
```

### 🗄️ **로그 파일 명명 규칙**

로테이션된 파일들은 다음과 같이 명명됩니다:

```
logs/
├── bookstar.log              # 현재 로그
├── bookstar.log.2024-01-14   # 어제 로그
├── bookstar.log.2024-01-13   # 2일 전 로그
├── bookstar.log.2024-01-12   # 3일 전 로그
└── ...                       # 보관 기간까지
```

### 📊 **디스크 사용량 예측**

| 로그 파일 | 일일 예상 크기 | 보관 기간 | 최대 디스크 사용량 |
|-----------|----------------|-----------|-------------------|
| `bookstar.log` | ~50MB | 14일 | ~700MB |
| `bookstar_error.log` | ~5MB | 30일 | ~150MB |
| `bookstar_access.log` | ~20MB | 7일 | ~140MB |
| `bookstar_performance.log` | ~10MB | 10일 | ~100MB |
| `bookstar_traceback.log` | ~2MB | 60일 | ~120MB |
| **전체** | **~87MB** | **혼합** | **~1.2GB** |

### 🧹 **자동 정리 시스템**

- **자동 삭제**: 보관 기간 초과 시 자동 삭제
- **압축 저장**: 로테이션된 파일은 gzip 압축 (약 90% 용량 절약)
- **실시간 모니터링**: 디스크 사용량 자동 추적

## 📋 모범 사례

### 1. 적절한 로그 레벨 사용

```python
# ✅ 좋은 예
logger.debug("캐시 키 생성: cache_key_12345")      # 개발 정보
logger.info("사용자 인증 성공: user_id=12345")        # 일반 정보
logger.warning("API 응답 시간 초과: 3.2초")            # 주의 사항
logger.error("데이터베이스 연결 실패", exc_info=True)   # 오류
logger.critical("시스템 메모리 부족")                   # 치명적 오류

# ❌ 나쁜 예
logger.error("사용자 로그인")  # 에러가 아닌데 ERROR 레벨 사용
logger.debug("치명적 시스템 오류")  # 심각한 문제인데 DEBUG 레벨 사용
```

### 2. 구조화된 로깅 활용

```python
# ✅ 좋은 예 - 검색 가능한 구조화된 정보
logger.info(
    "도서 추천 완료",
    extra={
        'user_id': user_id,
        'recommendations_count': len(recommendations),
        'algorithm': 'hybrid',
        'execution_time_ms': 250.5
    }
)

# ❌ 나쁜 예 - 파싱하기 어려운 문자열
logger.info(f"사용자 {user_id}에게 {len(recommendations)}개 추천 완료 (250.5ms)")
```

### 3. 민감한 정보 보호

```python
# ✅ 좋은 예
logger.info(f"사용자 인증 성공: user_id={user_id}")

# ❌ 나쁜 예 - 비밀번호나 토큰 로깅 금지
logger.info(f"로그인: password={password}, token={auth_token}")
```

### 4. 성능 고려

```python
# ✅ 좋은 예 - 조건부 로깅
if logger.isEnabledFor(logging.DEBUG):
    expensive_debug_info = generate_expensive_debug_info()
    logger.debug(f"상세 정보: {expensive_debug_info}")

# ✅ 좋은 예 - 설정 기반 임계값
from bookstar.config import settings

@log_execution_time(threshold_ms=settings.logging['db_query_threshold_ms'])
def database_operation():
    pass
```

### 5. 로그 보관 최적화

```python
# 로그 유형별 적절한 보관 기간 설정
[logging]
main_log_retention_days = 14        # 일반 디버깅: 2주
error_log_retention_days = 30       # 에러 분석: 1개월  
access_log_retention_days = 7       # 트래픽 분석: 1주
performance_log_retention_days = 10 # 성능 분석: 10일
traceback_log_retention_days = 60   # 상세 디버깅: 2개월
```

## 🔧 트러블슈팅

### 로그가 파일에 저장되지 않는 경우

1. 로그 디렉토리 권한 확인
```bash
mkdir -p logs
chmod 755 logs
```

2. 로깅 시스템 초기화 확인
```python
from bookstar.config.logging_config import logging_config
logging_config.setup_logging()
```

### 로그 파일이 너무 큰 경우

**📅 시간 기반 로테이션으로 해결됨**
- 모든 로그 파일이 매일 자정에 자동 로테이션
- 보관 기간 초과 시 자동 삭제
- 더 짧은 보관 기간 설정 가능:

```toml
[logging]
main_log_retention_days = 7     # 2주 → 1주로 단축
error_log_retention_days = 15   # 30일 → 15일로 단축
```

### 로그 로테이션이 작동하지 않는 경우

1. 로그 파일 권한 확인
```bash
ls -la logs/
```

2. 시스템 시간 확인
```bash
date
```

3. 로테이션 테스트
```python
import logging
from bookstar.config.logging_config import logging_config

# 로깅 시스템 초기화
logging_config.setup_logging()

# 테스트 로그 생성
logger = logging.getLogger(__name__)
logger.info("로테이션 테스트 로그")
```

### JSON 로그 파싱 오류

JSON 로그 사용시 특수 문자 이스케이프 확인:
```python
import json

# JSON 안전한 로깅
logger.info(
    "사용자 입력 처리",
    extra={'user_input': json.dumps(user_input)}  # 안전한 JSON 직렬화
)
```

## 📊 로그 분석 도구

### 1. **실시간 모니터링**

```bash
# 전체 로그 실시간 보기
tail -f logs/bookstar.log

# 에러만 실시간 모니터링
tail -f logs/bookstar_error.log

# 성능 문제 실시간 추적
tail -f logs/bookstar_performance.log | grep "임계값 초과"
```

### 2. **로그 검색 및 분석**

```bash
# 특정 사용자의 모든 활동 추적
grep "user_id=12345" logs/bookstar.log

# 성능 문제 분석
grep "느린 쿼리" logs/bookstar.log
grep "실행 시간" logs/bookstar_performance.log

# 에러 빈도 분석
grep -c "ERROR" logs/bookstar_error.log.*

# 일별 로그 분석
ls -la logs/bookstar.log.2024-01-*
```

### 3. **로그 통계**

```bash
# 로그 레벨별 통계
awk '{print $3}' logs/bookstar.log | sort | uniq -c

# 에러 유형별 통계
grep "ERROR" logs/bookstar_error.log | awk '{print $NF}' | sort | uniq -c

# 성능 문제 상위 함수
grep "실행 완료" logs/bookstar_performance.log | sort -k5 -nr | head -10
```

## 📚 예제 실행

로깅 시스템 예제를 실행해보세요:

```bash
cd bookstar-ai
python examples/logging_example.py
```

실행 후 `logs/` 디렉토리에서 생성된 로그 파일들을 확인할 수 있습니다:

```bash
ls -la logs/
# bookstar.log
# bookstar_error.log  
# bookstar_access.log
# bookstar_performance.log
# bookstar_traceback.log
```

## 🔄 로그 보관 정책 커스터마이징

환경에 따라 보관 정책을 조정할 수 있습니다:

### 개발 환경 (짧은 보관)
```toml
[logging]
main_log_retention_days = 3
error_log_retention_days = 7
access_log_retention_days = 1
performance_log_retention_days = 3
traceback_log_retention_days = 14
```

### 운영 환경 (긴 보관)
```toml
[logging]
main_log_retention_days = 30
error_log_retention_days = 90
access_log_retention_days = 14
performance_log_retention_days = 30
traceback_log_retention_days = 180
```

---

**💡 팁**: 로깅은 디버깅과 모니터링의 핵심입니다. 적절한 로그 레벨과 구조화된 정보를 활용하여 애플리케이션의 상태를 효과적으로 추적하세요! 새로운 통합 로그 관리 시스템으로 더욱 체계적인 로그 관리가 가능해졌습니다. 🚀 