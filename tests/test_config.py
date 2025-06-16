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
    assert 'log_level' in app_config
    assert isinstance(app_config['cors_origins'], list) 