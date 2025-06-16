"""
설정 관리 모듈
TOML 파일에서 설정을 읽어와 전역적으로 사용할 수 있도록 제공
"""
import os
from pathlib import Path
from typing import Any

import toml


class Settings:
    """설정 클래스"""
    
    def __init__(self):
        self._config = None
        self._secrets = None
        self._load_config()
        self._load_secrets()
    
    def _load_config(self):
        """TOML 설정 파일을 로드합니다."""
        # 프로젝트 루트 경로 찾기
        current_path = Path(__file__).parent
        project_root = current_path.parent.parent
        config_path = project_root / "config.toml"
        
        if not config_path.exists():
            raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")
        
        with open(config_path, encoding='utf-8') as f:
            self._config = toml.load(f)
    
    def _load_secrets(self):
        """민감한 정보가 담긴 .env.toml 파일을 로드합니다."""
        current_path = Path(__file__).parent
        project_root = current_path.parent.parent
        env_path = project_root / ".env.toml"
        
        self._secrets = {}
        
        if env_path.exists():
            with open(env_path, encoding='utf-8') as f:
                self._secrets = toml.load(f)
        
        # .env.toml 파일이 없어도 에러 없이 계속 진행 (환경변수 사용)
    
    @property
    def aws(self) -> dict[str, Any]:
        """AWS 설정"""
        aws_secrets = self._secrets.get('aws', {})
        return {
            'region': os.getenv(
                'AWS_REGION', 
                aws_secrets.get('region', 'ap-northeast-2')
            ),
            'bucket_name': os.getenv(
                'AWS_BUCKET_NAME', 
                aws_secrets.get('bucket_name')
            ),
            'access_key_id': os.getenv(
                'AWS_ACCESS_KEY_ID', 
                aws_secrets.get('access_key_id')
            ),
            'secret_access_key': os.getenv(
                'AWS_SECRET_ACCESS_KEY', 
                aws_secrets.get('secret_access_key')
            )
        }
    
    @property
    def database(self) -> dict[str, Any]:
        """데이터베이스 설정"""
        db_secrets = self._secrets.get('database', {})
        return {
            'user': os.getenv('DB_USER', db_secrets.get('user')),
            'password': os.getenv('DB_PASSWORD', db_secrets.get('password')),
            'host': os.getenv('DB_HOST', db_secrets.get('host', 'localhost')),
            'port': int(os.getenv('DB_PORT', str(db_secrets.get('port', 3306)))),
            'name': os.getenv('DB_NAME', db_secrets.get('name', 'bookstar'))
        }
    
    @property
    def database_url(self) -> str:
        """데이터베이스 연결 URL"""
        db = self.database
        return f"mysql+pymysql://{db['user']}:{db['password']}@{db['host']}:{db['port']}/{db['name']}"
    
    @property
    def app(self) -> dict[str, Any]:
        """애플리케이션 설정"""
        app_config = self._config.get('app', {})
        return {
            'cors_origins': app_config.get('cors_origins', ["*"]),
            'log_level': os.getenv('LOG_LEVEL', app_config.get('log_level', 'INFO'))
        }


# 전역 설정 인스턴스
settings = Settings() 