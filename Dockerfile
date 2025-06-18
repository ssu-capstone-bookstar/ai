# Python 3.11 slim 이미지 사용
FROM python:3.11-slim

# 메타데이터 추가
LABEL maintainer="BookStar AI Team"
LABEL description="AI 기반 도서 추천 시스템"
LABEL version="1.0.0"

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 프로젝트 설정 파일 복사
COPY .env.toml .
COPY config.toml .

# 애플리케이션 코드 복사
COPY main.py .
COPY bookstar/ ./bookstar/

# 로그 디렉토리 생성
RUN mkdir -p logs

# 환경 변수 설정
ENV PYTHONPATH=/app:$PYTHONPATH
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 기본 포트 설정 (환경변수로 오버라이드 가능)
ENV SERVER_PORT=8000

# 포트 노출 (기본값, 실제로는 config.toml에서 읽어옴)
EXPOSE ${SERVER_PORT}

# 헬스체크 추가 (환경변수 사용)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${SERVER_PORT}/docs || exit 1

# 애플리케이션 실행 (main.py가 config.toml에서 포트를 읽어옴)
CMD ["python", "main.py"]
