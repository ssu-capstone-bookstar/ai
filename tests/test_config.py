"""
설정 시스템 테스트
"""
from bookstar.config import settings


def test_settings_load():
    """설정이 정상적으로 로드되는지 테스트"""
    assert settings._config is not None
    assert 'app' in settings._config
    # aws와 database는 .env.toml에서 로드되므로 _secrets에서 확인
    assert settings._secrets is not None


def test_database_config():
    """데이터베이스 설정 테스트"""
    db_config = settings.database
    assert 'user' in db_config
    assert 'password' in db_config
    assert 'host' in db_config
    assert 'port' in db_config
    assert 'name' in db_config
    assert isinstance(db_config['port'], int)


def test_database_url():
    """데이터베이스 URL 생성 테스트"""
    url = settings.database_url
    assert url.startswith("mysql+pymysql://")
    assert "@" in url
    assert ":" in url


def test_aws_config():
    """AWS 설정 테스트"""
    aws_config = settings.aws
    assert 'region' in aws_config
    assert 'bucket_name' in aws_config
    assert 'access_key_id' in aws_config
    assert 'secret_access_key' in aws_config


def test_app_config():
    """앱 설정 테스트"""
    app_config = settings.app
    assert 'cors_origins' in app_config
    assert 'title' in app_config
    assert 'description' in app_config
    assert 'version' in app_config
    assert isinstance(app_config['cors_origins'], list)


def test_server_config():
    """서버 설정 테스트"""
    server_config = settings.server
    assert 'host' in server_config
    assert 'port' in server_config
    assert isinstance(server_config['port'], int)


def test_recommendation_config():
    """추천 시스템 설정 테스트"""
    rec_config = settings.recommendation
    assert 'default_recommendations_count' in rec_config
    assert 'similar_users_count' in rec_config
    assert 'content_weight' in rec_config
    assert 'collaborative_weight' in rec_config
    assert isinstance(rec_config['default_recommendations_count'], int)
    assert isinstance(rec_config['similar_users_count'], int)


def test_logging_config():
    """로깅 설정 테스트"""
    log_config = settings.logging
    
    # 기본 설정 확인
    assert 'level' in log_config
    assert 'use_json' in log_config
    assert 'enable_console' in log_config
    assert 'log_dir' in log_config
    
    # 로그 파일 관리 설정 확인
    assert 'max_file_size_mb' in log_config
    assert 'backup_count' in log_config
    
    # 로그 유형 활성화 설정 확인
    assert 'enable_access_log' in log_config
    assert 'enable_performance_log' in log_config
    assert 'enable_traceback_log' in log_config
    
    # 성능 임계값 설정 확인
    assert 'performance_threshold_ms' in log_config
    assert 'db_threshold_ms' in log_config
    assert 'api_threshold_ms' in log_config
    assert 'heavy_threshold_ms' in log_config
    
    # 로그 보관 정책 설정 확인
    assert 'main_log_retention_days' in log_config
    assert 'error_log_retention_days' in log_config
    assert 'access_log_retention_days' in log_config
    assert 'performance_log_retention_days' in log_config
    assert 'traceback_log_retention_days' in log_config


def test_all_config_sections():
    """모든 설정 섹션이 존재하는지 테스트"""
    # config.toml의 모든 섹션 확인
    assert hasattr(settings, 'app')
    assert hasattr(settings, 'server')
    assert hasattr(settings, 'recommendation')
    assert hasattr(settings, 'logging')
    
    # .env.toml의 모든 섹션 확인
    assert hasattr(settings, 'aws')
    assert hasattr(settings, 'database')


def test_config_data_types():
    """설정 값들의 데이터 타입이 올바른지 테스트"""
    # 서버 설정 타입 확인
    assert isinstance(settings.server['host'], str)
    assert isinstance(settings.server['port'], int)
    
    # 추천 시스템 설정 타입 확인
    assert isinstance(settings.recommendation['default_recommendations_count'], int)
    assert isinstance(settings.recommendation['similar_users_count'], int)
    assert isinstance(settings.recommendation['content_weight'], int | float)
    assert isinstance(settings.recommendation['collaborative_weight'], int | float)
    
    # 로깅 설정 타입 확인
    assert isinstance(settings.logging['level'], str)
    assert isinstance(settings.logging['use_json'], bool)
    assert isinstance(settings.logging['enable_console'], bool)
    assert isinstance(settings.logging['log_dir'], str)
    
    # 성능 임계값 타입 확인
    assert isinstance(settings.logging['performance_threshold_ms'], int)
    assert isinstance(settings.logging['db_threshold_ms'], int)
    assert isinstance(settings.logging['api_threshold_ms'], int)
    assert isinstance(settings.logging['heavy_threshold_ms'], int)
    
    # 보관 정책 타입 확인
    assert isinstance(settings.logging['main_log_retention_days'], int)
    assert isinstance(settings.logging['error_log_retention_days'], int)
    assert isinstance(settings.logging['access_log_retention_days'], int)
    assert isinstance(settings.logging['performance_log_retention_days'], int)
    assert isinstance(settings.logging['traceback_log_retention_days'], int)


def test_config_value_ranges():
    """설정 값들이 합리적인 범위에 있는지 테스트"""
    # 서버 포트 범위 확인
    assert 1 <= settings.server['port'] <= 65535
    
    # 추천 개수 범위 확인
    assert 1 <= settings.recommendation['default_recommendations_count'] <= 100
    assert 1 <= settings.recommendation['similar_users_count'] <= 50
    
    # 추천 가중치 범위 확인
    assert 0 <= settings.recommendation['content_weight'] <= 1
    assert 0 <= settings.recommendation['collaborative_weight'] <= 1
    
    # 성능 임계값 범위 확인
    assert 0 < settings.logging['performance_threshold_ms'] <= 10000
    assert 0 < settings.logging['db_threshold_ms'] <= 5000
    assert 0 < settings.logging['api_threshold_ms'] <= 10000
    assert 0 < settings.logging['heavy_threshold_ms'] <= 30000
    
    # 보관 일수 범위 확인
    assert 1 <= settings.logging['main_log_retention_days'] <= 365
    assert 1 <= settings.logging['error_log_retention_days'] <= 365
    assert 1 <= settings.logging['access_log_retention_days'] <= 365
    assert 1 <= settings.logging['performance_log_retention_days'] <= 365
    assert 1 <= settings.logging['traceback_log_retention_days'] <= 365


def test_recommendation_weights_sum():
    """추천 가중치의 합이 1.0인지 테스트"""
    content_weight = settings.recommendation['content_weight']
    collaborative_weight = settings.recommendation['collaborative_weight']
    total_weight = content_weight + collaborative_weight
    
    # 부동소수점 오차를 고려하여 검증
    assert abs(total_weight - 1.0) < 0.001


def test_logging_level_validity():
    """로깅 레벨이 유효한 값인지 테스트"""
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    assert settings.logging['level'] in valid_levels


def test_cors_origins_format():
    """CORS origins 설정이 올바른 형식인지 테스트"""
    cors_origins = settings.app['cors_origins']
    assert isinstance(cors_origins, list)
    
    for origin in cors_origins:
        assert isinstance(origin, str)
        # URL 형식 기본 검증
        assert origin.startswith('http://') or origin.startswith('https://')


def test_complete_settings_integration():
    """전체 설정 시스템 통합 테스트 - 모든 설정 로드 성공"""
    try:
        # 모든 설정 섹션 접근
        app_config = settings.app
        server_config = settings.server
        rec_config = settings.recommendation
        log_config = settings.logging
        aws_config = settings.aws
        db_config = settings.database
        
        # 데이터베이스 URL 생성
        db_url = settings.database_url
        
        # 모든 설정이 성공적으로 로드되었는지 확인
        assert app_config is not None
        assert server_config is not None
        assert rec_config is not None
        assert log_config is not None
        assert aws_config is not None
        assert db_config is not None
        assert db_url is not None
        
        # 이것이 README.md의 검증 명령어와 동일한 역할
        # print('✅ 모든 설정 로드 성공')  # ruff 오류 방지를 위해 주석 처리
        
    except Exception as e:
        msg = f"설정 로드 실패: {str(e)}"
        raise AssertionError(msg) from e 