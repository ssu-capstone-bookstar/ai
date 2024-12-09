# 1. Python 이미지를 기반으로 사용합니다.
FROM python:3.11-slim

# 시스템 패키지 및 Java 설치
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-kor \
    openjdk-17-jdk \ 
    && rm -rf /var/lib/apt/lists/*

# JAVA_HOME 환경 변수 설정
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"
ENV BUCKET_NAME=savewordcloud

# 2. 작업 디렉토리를 /app으로 설정
WORKDIR /app

# 3. requirements.txt를 /app에 복사합니다.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 폰트 관련 디렉토리를 컨테이너로 복사
COPY ./fonts /usr/share/fonts/truetype/myfonts
# 6. 시스템에 설치된 폰트를 새로고침
RUN fc-cache -f -v

COPY .env /app/

# S3 관련 환경 변수 설정
ENV BUCKET_NAME=$BUCKET_NAME

# 7. src 디렉토리를 /app/src에 복사
COPY ./src /app/src

# PYTHONPATH 환경 변수 설정
ENV PYTHONPATH=/app/src:$PYTHONPATH

# 8. FastAPI 애플리케이션을 실행할 때 사용할 명령어 설정
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
