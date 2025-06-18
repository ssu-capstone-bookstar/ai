"""
데코레이터 테스트
"""
import asyncio
import time
from unittest.mock import MagicMock

import pytest

from bookstar.utils.decorators import (
    log_async_execution_time,
    log_database_operations,
    log_execution_time,
    retry_with_logging,
    validate_and_log,
)


def test_log_execution_time_decorator():
    """실행 시간 측정 데코레이터 테스트"""
    
    @log_execution_time(threshold_ms=100)
    def fast_function():
        time.sleep(0.01)  # 10ms
        return "fast"
    
    @log_execution_time(threshold_ms=10)
    def slow_function():
        time.sleep(0.05)  # 50ms
        return "slow"
    
    # 빠른 함수 실행 (임계값 미만)
    result = fast_function()
    assert result == "fast"
    
    # 느린 함수 실행 (임계값 초과)
    result = slow_function()
    assert result == "slow"


@pytest.mark.asyncio
async def test_log_async_execution_time_decorator():
    """비동기 실행 시간 측정 데코레이터 테스트"""
    
    @log_async_execution_time(threshold_ms=100)
    async def fast_async_function():
        await asyncio.sleep(0.01)  # 10ms
        return "async_fast"
    
    @log_async_execution_time(threshold_ms=10)
    async def slow_async_function():
        await asyncio.sleep(0.05)  # 50ms
        return "async_slow"
    
    # 빠른 비동기 함수 실행
    result = await fast_async_function()
    assert result == "async_fast"
    
    # 느린 비동기 함수 실행
    result = await slow_async_function()
    assert result == "async_slow"


def test_log_execution_time_with_args():
    """인자와 결과를 포함한 실행 시간 측정 테스트"""
    
    @log_execution_time(include_args=True, include_result=True, threshold_ms=0)
    def function_with_args(x, y, z=None):
        return {"sum": x + y, "z": z}
    
    result = function_with_args(1, 2, z="test")
    assert result == {"sum": 3, "z": "test"}


def test_log_database_operations_decorator():
    """데이터베이스 작업 로깅 데코레이터 테스트"""
    
    # Mock 데이터베이스 세션
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = [
        "result1", "result2"
    ]
    
    @log_database_operations(log_results=True)
    def get_data(db, user_id):
        return db.query().filter().all()
    
    result = get_data(mock_db, 123)
    assert result == ["result1", "result2"]


def test_retry_with_logging_success():
    """재시도 로깅 데코레이터 - 성공 케이스"""
    call_count = 0
    
    @retry_with_logging(max_attempts=3, delay=0.01)
    def sometimes_failing_function():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise Exception("Temporary failure")
        return "success"
    
    result = sometimes_failing_function()
    assert result == "success"
    assert call_count == 2  # 첫 번째 실패, 두 번째 성공


def test_retry_with_logging_failure():
    """재시도 로깅 데코레이터 - 실패 케이스"""
    call_count = 0
    
    @retry_with_logging(max_attempts=2, delay=0.01)
    def always_failing_function():
        nonlocal call_count
        call_count += 1
        raise Exception("Always fails")
    
    with pytest.raises(Exception, match="Always fails"):
        always_failing_function()
    
    assert call_count == 2  # 최대 시도 횟수만큼 호출


def test_validate_and_log_decorator():
    """입력/출력 검증 로깅 데코레이터 테스트"""
    
    def validate_positive_number(x):
        if x <= 0:
            raise ValueError("Number must be positive")
    
    @validate_and_log(input_validator=validate_positive_number)
    def process_number(x):
        return x * 2
    
    # 유효한 입력
    result = process_number(5)
    assert result == 10
    
    # 무효한 입력
    with pytest.raises(ValueError, match="Number must be positive"):
        process_number(-1)


def test_decorator_error_handling():
    """데코레이터 에러 처리 테스트"""
    
    @log_execution_time(threshold_ms=0)
    def error_function():
        raise RuntimeError("Test error")
    
    with pytest.raises(RuntimeError, match="Test error"):
        error_function()


@pytest.mark.parametrize("threshold_ms", [0, 50, 100, 500])
def test_different_thresholds(threshold_ms):
    """다양한 임계값 테스트"""
    
    @log_execution_time(threshold_ms=threshold_ms)
    def test_function():
        time.sleep(0.02)  # 20ms
        return "done"
    
    result = test_function()
    assert result == "done"


def test_decorator_with_exception():
    """예외 발생 시 데코레이터 동작 테스트"""
    
    @log_execution_time(threshold_ms=0)
    def exception_function():
        time.sleep(0.01)
        raise ValueError("Test exception")
    
    with pytest.raises(ValueError, match="Test exception"):
        exception_function()


@pytest.mark.asyncio
async def test_async_decorator_with_exception():
    """비동기 데코레이터 예외 처리 테스트"""
    
    @log_async_execution_time(threshold_ms=0)
    async def async_exception_function():
        await asyncio.sleep(0.01)
        raise ValueError("Async test exception")
    
    with pytest.raises(ValueError, match="Async test exception"):
        await async_exception_function()


def test_nested_decorators():
    """중첩된 데코레이터 테스트"""
    
    def simple_validator(x):
        if not isinstance(x, int):
            raise TypeError("Must be integer")
    
    @log_execution_time(threshold_ms=0)
    @validate_and_log(input_validator=simple_validator)
    def nested_decorated_function(x):
        time.sleep(0.01)
        return x * 3
    
    result = nested_decorated_function(4)
    assert result == 12
    
    with pytest.raises(TypeError, match="Must be integer"):
        nested_decorated_function("not_int")


def test_decorator_preserves_function_metadata():
    """데코레이터가 함수 메타데이터를 보존하는지 테스트"""
    
    @log_execution_time(threshold_ms=100)
    def original_function():
        """Original function docstring"""
        return "original"
    
    # 함수 이름과 docstring이 보존되는지 확인
    assert original_function.__name__ == "original_function"
    assert "Original function docstring" in original_function.__doc__


@pytest.mark.asyncio
async def test_async_decorator_preserves_metadata():
    """비동기 데코레이터가 함수 메타데이터를 보존하는지 테스트"""
    
    @log_async_execution_time(threshold_ms=100)
    async def original_async_function():
        """Original async function docstring"""
        return "async_original"
    
    # 함수 이름과 docstring이 보존되는지 확인
    assert original_async_function.__name__ == "original_async_function"
    assert "Original async function docstring" in original_async_function.__doc__ 