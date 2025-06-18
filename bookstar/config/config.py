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
            'title': app_config.get('title', 'BookStar AI'),
            'description': app_config.get('description', 'AI 기반 도서 추천 시스템'),
            'version': app_config.get('version', '1.0.0')
        }
        
    @property
    def server(self) -> dict[str, Any]:
        """서버 설정"""
        server_config = self._config.get('server', {})
        return {
            'host': os.getenv('SERVER_HOST', server_config.get('host', '0.0.0.0')),
            'port': int(os.getenv('SERVER_PORT', str(server_config.get('port', 8000))))
        }
        
    @property
    def recommendation(self) -> dict[str, Any]:
        """추천 시스템 설정"""
        rec_config = self._config.get('recommendation', {})
        return {
            'default_recommendations_count': rec_config.get(
                'default_recommendations_count', 10
            ),
            'similar_users_count': rec_config.get('similar_users_count', 3),
            'content_weight': rec_config.get('content_weight', 0.7),
            'collaborative_weight': rec_config.get('collaborative_weight', 0.3),
            # 사용자 선호도 계산 가중치
            'read_book_weight': rec_config.get('read_book_weight', 0.7),
            'unread_book_weight': rec_config.get('unread_book_weight', 1.0),
            'category_preference_weight': rec_config.get(
                'category_preference_weight', 2.0
            ),
            'author_preference_weight': rec_config.get(
                'author_preference_weight', 1.5
            ),
            # PyTorch 모델 훈련 설정
            'num_epochs': rec_config.get('num_epochs', 300),
            'learning_rate': rec_config.get('learning_rate', 0.122)
        }
    
    @property
    def logging(self) -> dict:
        """로깅 관련 설정"""
        logging_config = self._config.get('logging', {})
        
        return {
            'level': os.getenv('LOG_LEVEL', logging_config.get('level', 'INFO')),
            'use_json': logging_config.get('use_json', False),
            'enable_console': logging_config.get('enable_console', True),
            'log_dir': logging_config.get('log_dir', 'logs'),
            'performance_threshold_ms': logging_config.get(
                'performance_threshold_ms', 100
            ),
            'max_file_size_mb': logging_config.get('max_file_size_mb', 10),
            'backup_count': logging_config.get('backup_count', 5),
            'enable_access_log': logging_config.get('enable_access_log', True),
            'enable_performance_log': logging_config.get(
                'enable_performance_log', True
            ),
            'enable_traceback_log': logging_config.get(
                'enable_traceback_log', True
            ),
            # 직관적인 임계값 설정
            'db_threshold_ms': logging_config.get('db_query_threshold_ms', 50),
            'api_threshold_ms': logging_config.get(
                'api_processing_threshold_ms', 200
            ),
            'heavy_threshold_ms': logging_config.get(
                'heavy_computation_threshold_ms', 500
            ),
            # 로그 파일 로테이션 설정 (모든 로그에 일관된 보관 정책)
            'main_log_retention_days': logging_config.get(
                'main_log_retention_days', 14
            ),
            'error_log_retention_days': logging_config.get(
                'error_log_retention_days', 30
            ),
            'access_log_retention_days': logging_config.get(
                'access_log_retention_days', 7
            ),
            'performance_log_retention_days': logging_config.get(
                'performance_log_retention_days', 10
            ),
            'traceback_log_retention_days': logging_config.get(
                'traceback_log_retention_days', 60
            )
        }


# 전역 설정 인스턴스
settings = Settings() 