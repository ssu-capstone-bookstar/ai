"""
BookStar AI 서비스의 메인 애플리케이션
"""
import logging

import uvicorn

from bookstar.config import settings
from bookstar.main import app

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, settings.logging['level']),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """
    FastAPI 서버를 시작합니다.
    """
    uvicorn.run(
        app,
        host=settings.server['host'],
        port=settings.server['port'],
        log_level=settings.logging['level'].lower()
    )

if __name__ == "__main__":
    main() 