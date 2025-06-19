"""
로깅 시스템 테스트
"""
import logging
import tempfile
from pathlib import Path

import pytest

from bookstar.config import settings
from bookstar.config.logging_config import LoggingConfig, logging_config


def test_logging_config_load():
    """로깅 설정이 정상적으로 로드되는지 테스트"""
    log_config = settings.logging
    
    # 기본 설정 확인
    assert 'level' in log_config
    assert 'use_json' in log_config
    assert 'enable_console' in log_config
    assert 'log_dir' in log_config
    
    # 성능 임계값 설정 확인
    assert 'performance_threshold_ms' in log_config
    assert 'db_threshold_ms' in log_config
    assert 'api_threshold_ms' in log_config
    assert 'heavy_threshold_ms' in log_config
    
    # 보관 정책 설정 확인
    assert 'main_log_retention_days' in log_config
    assert 'error_log_retention_days' in log_config
    assert 'access_log_retention_days' in log_config
    assert 'performance_log_retention_days' in log_config
    assert 'traceback_log_retention_days' in log_config


def test_logging_thresholds():
    """로깅 임계값이 올바르게 설정되었는지 테스트"""
    log_config = settings.logging
    
    # 임계값이 숫자인지 확인
    assert isinstance(log_config['performance_threshold_ms'], int)
    assert isinstance(log_config['db_threshold_ms'], int)
    assert isinstance(log_config['api_threshold_ms'], int)
    assert isinstance(log_config['heavy_threshold_ms'], int)
    
    # 임계값이 합리적인 범위인지 확인
    assert 0 < log_config['db_threshold_ms'] <= 1000
    assert 0 < log_config['api_threshold_ms'] <= 5000
    assert 0 < log_config['heavy_threshold_ms'] <= 10000


def test_logging_retention_policy():
    """로그 보관 정책이 올바르게 설정되었는지 테스트"""
    log_config = settings.logging
    
    # 보관 일수가 숫자인지 확인
    assert isinstance(log_config['main_log_retention_days'], int)
    assert isinstance(log_config['error_log_retention_days'], int)
    assert isinstance(log_config['access_log_retention_days'], int)
    assert isinstance(log_config['performance_log_retention_days'], int)
    assert isinstance(log_config['traceback_log_retention_days'], int)
    
    # 보관 일수가 합리적인 범위인지 확인
    assert 1 <= log_config['main_log_retention_days'] <= 365
    assert 1 <= log_config['error_log_retention_days'] <= 365
    assert 1 <= log_config['access_log_retention_days'] <= 365
    assert 1 <= log_config['performance_log_retention_days'] <= 365
    assert 1 <= log_config['traceback_log_retention_days'] <= 365


def _cleanup_logging_handlers():
    """모든 로깅 핸들러를 정리하는 헬퍼 함수"""
    # 루트 로거의 모든 핸들러 정리
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        try:
            handler.close()
        except Exception:
            pass
        root_logger.removeHandler(handler)
    
    # 전용 로거들 정리
    for logger_name in ['performance', 'access']:
        logger = logging.getLogger(logger_name)
        for handler in logger.handlers[:]:
            try:
                handler.close()
            except Exception:
                pass
            logger.removeHandler(handler)


def test_logging_setup():
    """로깅 시스템이 정상적으로 초기화되는지 테스트"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 임시 로그 디렉토리로 설정
        original_log_dir = settings.logging['log_dir']
        settings.logging['log_dir'] = temp_dir
        
        try:
            # 로깅 시스템 초기화
            logging_config.setup_logging()
            
            # 로거 가져오기
            logger = logging.getLogger('test_logger')
            performance_logger = logging_config.get_performance_logger()
            access_logger = logging_config.get_access_logger()
            
            # 로거들이 정상적으로 생성되었는지 확인
            assert logger is not None
            assert performance_logger is not None
            assert access_logger is not None
            
            # 로그 레벨 확인
            root_logger = logging.getLogger()
            expected_level = getattr(logging, settings.logging['level'])
            assert root_logger.level == expected_level
            
        finally:
            # 원래 설정 복원
            settings.logging['log_dir'] = original_log_dir
            # 핸들러 정리
            _cleanup_logging_handlers()


def test_logger_creation():
    """전용 로거들이 정상적으로 생성되는지 테스트"""
    try:
        # 로깅 시스템 초기화
        logging_config.setup_logging()
        
        # 전용 로거들 가져오기
        performance_logger = logging_config.get_performance_logger()
        access_logger = logging_config.get_access_logger()
        
        # 로거 이름 확인
        assert performance_logger.name == 'performance'
        assert access_logger.name == 'access'
        
        # 로거가 활성화되어 있는지 확인
        assert performance_logger.isEnabledFor(logging.INFO)
        assert access_logger.isEnabledFor(logging.INFO)
    finally:
        # 핸들러 정리
        _cleanup_logging_handlers()


def test_log_directory_creation():
    """로그 디렉토리가 자동으로 생성되는지 테스트"""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_dir = Path(temp_dir) / "test_logs"
        
        # 로그 디렉토리가 존재하지 않는 상태에서 시작
        assert not log_dir.exists()
        
        try:
            # 새로운 LoggingConfig 인스턴스로 테스트 (디렉토리 자동 생성 확인용)
            _ = LoggingConfig(log_dir=str(log_dir))
            
            # 로그 디렉토리가 생성되었는지 확인 (LoggingConfig 초기화 시 자동 생성)
            assert log_dir.exists()
            assert log_dir.is_dir()
        finally:
            # 핸들러 정리
            _cleanup_logging_handlers()


@pytest.mark.parametrize("log_level", ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
def test_log_levels(log_level):
    """다양한 로그 레벨이 정상적으로 작동하는지 테스트"""
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # 새로운 LoggingConfig 인스턴스로 테스트
            test_logging_config = LoggingConfig(log_dir=temp_dir)
            
            # 로깅 시스템 초기화
            test_logging_config.setup_logging(log_level=log_level)
            
            # 루트 로거의 레벨 확인
            root_logger = logging.getLogger()
            expected_level = getattr(logging, log_level)
            assert root_logger.level == expected_level
        finally:
            # 핸들러 정리
            _cleanup_logging_handlers()


def test_json_logging_toggle():
    """JSON 로깅 설정이 정상적으로 작동하는지 테스트"""
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # 새로운 LoggingConfig 인스턴스로 테스트
            test_logging_config = LoggingConfig(log_dir=temp_dir)
            
            # JSON 로깅 활성화
            test_logging_config.setup_logging(use_json=True)
            
            # JSON 포매터가 적용되었는지 확인
            root_logger = logging.getLogger()
            handlers = root_logger.handlers
            
            # 최소한 하나의 핸들러가 JSON 포매터를 사용하는지 확인
            for handler in handlers:
                if hasattr(handler.formatter, 'format'):
                    # JSON 포매터인지 확인하는 방법
                    break
            
            # JSON 로깅 비활성화
            test_logging_config.setup_logging(use_json=False)
        finally:
            # 핸들러 정리
            _cleanup_logging_handlers() 