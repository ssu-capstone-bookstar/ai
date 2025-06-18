# 📚 BookStar AI - 도서 추천 시스템

AI 기반 개인화 도서 추천 시스템입니다. 콘텐츠 기반 필터링과 협업 필터링을 결합한 하이브리드 추천 알고리즘을 사용합니다.

## 🚀 빠른 시작

### 1. **의존성 설치**

**방법 1: uv 사용 (권장)**
```bash
# uv 설치 (없는 경우)
pip install uv

# 방식 A
uv lock
uv sync
uv sync --dev  # 개발용 포함

# 방식 B
uv venv
uv pip sync requirements.txt
uv pip sync requirements-dev.txt  # 개발용 포함
```

**방법 2: requirements.txt 사용**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 개발용 포함
```

### 2. **환경 설정**
```bash
# 환경 설정 파일 생성
cp .env.toml.template .env.toml

# .env.toml 파일을 편집하여 실제 값 입력
```

### 3. **실행**
```bash
# 개발 모드
python main.py

# 설정 파일의 서버 정보로 실행됩니다:
# - 기본 호스트: 0.0.0.0
# - 기본 포트: 8000
```

---

## 🏗️ **프로젝트 구조**

```
bookstar-ai/
├── 📄 main.py                    # 메인 실행 파일
├── 📄 config.toml               # 앱 설정 (공개)
├── 📋 .env.toml.template        # 환경설정 템플릿
├── 🔒 .env.toml                 # 실제 환경설정 (Git 제외)
├── 📦 pyproject.toml            # 프로젝트 설정 및 의존성
├── 🐳 Dockerfile               # Docker 설정
├── 📂 bookstar/                # 메인 패키지
│   ├── 🎯 main.py              # FastAPI 애플리케이션
│   ├── ⚙️ config/              # 설정 관리
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── logging_config.py   # 로깅 시스템 설정
│   ├── 🗄️ models/              # 데이터베이스 모델
│   │   ├── __init__.py
│   │   └── models.py
│   ├── 📋 schemas/             # API 스키마
│   │   ├── __init__.py
│   │   └── schemas.py
│   ├── 🔗 database/            # 데이터베이스 연결
│   │   ├── __init__.py
│   │   └── connection.py
│   ├── 🤖 services/            # AI 추천 로직
│   │   ├── __init__.py
│   │   └── recommendation.py
│   └── 🛠️ utils/               # 유틸리티 (데코레이터 등)
│       ├── __init__.py
│       └── decorators.py
├── 📁 examples/                # 사용 예제
│   ├── logging_example.py      # 로깅 시스템 예제
│   └── logs/                   # 예제 실행 로그
├── 📁 logs/                    # 로그 파일들 (5종류)
│   ├── bookstar.log            # 전체 로그 (14일 보관)
│   ├── bookstar_error.log      # 에러 로그 (30일 보관)
│   ├── bookstar_access.log     # 액세스 로그 (7일 보관)
│   ├── bookstar_performance.log # 성능 로그 (10일 보관)
│   └── bookstar_traceback.log  # Traceback 로그 (60일 보관)
└── 🧪 tests/                  # 테스트 코드 (64개 테스트, 88% 커버리지)
    ├── __init__.py
    ├── conftest.py             # 테스트 설정 및 픽스처
    ├── test_main.py            # FastAPI 테스트 (2개)
    ├── test_config.py          # 설정 시스템 테스트 (15개)
    ├── test_logging.py         # 로깅 시스템 테스트 (12개)
    ├── test_decorators.py      # 데코레이터 테스트 (17개)
    └── test_recommendation.py  # 추천 시스템 테스트 (18개)
```

---

## ⚙️ **설정 관리**

### 📂 **설정 파일 구조**
- `config.toml`: 공개 설정 (Git ✅)
- `.env.toml`: 민감한 정보 (Git ❌)
- `.env.toml.template`: 설정 가이드 (Git ✅)

### 🔄 **우선순위**
1. **환경변수** 🥇 (최우선)
2. **.env.toml** 🥈 
3. **config.toml** 🥉

### 📄 **config.toml 구조 (최신)**
```toml
# 🚀 애플리케이션 기본 정보
[app]
title = "BookStar AI"
description = "AI 기반 도서 추천 시스템"
version = "1.0.0"
cors_origins = ["http://127.0.0.1:9101"]

# 🌐 서버 설정
[server]
host = "0.0.0.0"
port = 8000

# 🤖 AI 추천 시스템 설정
[recommendation]
default_recommendations_count = 10  # 기본 추천 도서 개수
similar_users_count = 3             # 협업 필터링 유사 사용자 수
content_weight = 0.7                # 콘텐츠 기반 가중치
collaborative_weight = 0.3          # 협업 필터링 가중치

# 사용자 선호도 계산 가중치
read_book_weight = 0.7              # 읽은 책의 가중치 (vs 읽고 싶은 책)
unread_book_weight = 1.0            # 읽지 않은 책의 가중치
category_preference_weight = 2.0    # 카테고리 선호도 가중치
author_preference_weight = 1.5      # 저자 선호도 가중치

# PyTorch 모델 훈련 설정 (deprecated 함수용)
num_epochs = 300                    # 훈련 에포크 수
learning_rate = 0.122               # 학습률

# 📊 로깅 시스템 설정
[logging]
level = "INFO"
use_json = false
enable_console = true
log_dir = "logs"

# 성능 임계값 설정 (ms)
performance_threshold_ms = 100
db_query_threshold_ms = 50
api_processing_threshold_ms = 200
heavy_computation_threshold_ms = 500

# 로그 보관 정책 (일 단위)
main_log_retention_days = 14
error_log_retention_days = 30
access_log_retention_days = 7
performance_log_retention_days = 10
traceback_log_retention_days = 60
```

### 🔒 **.env.toml 예시**
```toml
# ⚠️ 절대 Git에 올리지 마세요!

[aws]
region = "ap-northeast-2"
bucket_name = "your-bucket-name"
access_key_id = "실제_AWS_키"
secret_access_key = "실제_AWS_시크릿"

[database] 
user = "실제_DB_사용자"
password = "실제_DB_비밀번호"
host = "실제_DB_호스트"
port = 3306
name = "실제_DB_이름"
```

---

## 🤖 **AI 추천 시스템**

### 📊 **추천 알고리즘**
- **콘텐츠 기반 필터링**: 카테고리, 저자 선호도 분석
- **협업 필터링**: 유사 사용자 기반 추천
- **하이브리드 방식**: 두 방법을 결합하여 추천 품질 향상

### 🎯 **추천 설정 (config.toml)**
| 설정 | 기본값 | 설명 |
|------|--------|------|
| `default_recommendations_count` | 10 | 기본 추천 도서 개수 |
| `similar_users_count` | 3 | 협업 필터링에서 참고할 유사 사용자 수 |
| `content_weight` | 0.7 | 콘텐츠 기반 필터링 가중치 |
| `collaborative_weight` | 0.3 | 협업 필터링 가중치 |
| `read_book_weight` | 0.7 | 읽은 책의 선호도 가중치 |
| `unread_book_weight` | 1.0 | 읽지 않은 책의 선호도 가중치 |
| `category_preference_weight` | 2.0 | 카테고리 선호도 계산 가중치 |
| `author_preference_weight` | 1.5 | 저자 선호도 계산 가중치 |
| `num_epochs` | 300 | PyTorch 모델 훈련 에포크 수 |
| `learning_rate` | 0.122 | PyTorch 모델 학습률 |

### 🚀 **성능 최적화**
- **캐싱 시스템**: 사용자 데이터 및 선호도 캐싱
- **쿼리 최적화**: 단일 JOIN 쿼리로 데이터 조회
- **메모리 효율성**: 필요한 컬럼만 선택적 로드
- **완전한 설정 기반**: config.toml에서 모든 추천 파라미터 조정 가능 (하드코딩 완전 제거)
- **동적 Docker 설정**: docker-run.sh가 config.toml에서 포트를 자동으로 읽어옴

### 📈 **추천 과정**
1. **사용자 독서 이력 분석**: 읽은 책과 읽고 싶은 책 목록 조회
2. **선호도 가중치 계산**: 읽은 책(0.7) vs 읽고 싶은 책(1.0) 가중치 적용
3. **카테고리/저자 선호도 계산**: 카테고리(2.0배), 저자(1.5배) 가중치로 점수 산출
4. **유사 사용자 탐색**: KNN 알고리즘으로 설정 가능한 개수만큼 유사 사용자 발견
5. **하이브리드 추천**: 콘텐츠 기반(70%) + 협업 필터링(30%) 가중치로 결합
6. **최종 추천 목록 생성**: 설정된 개수만큼 개인화된 추천 결과 반환

---

## 📡 **API 사용법**

### 📚 **도서 추천 API**
```http
POST /recommend_books
Content-Type: application/json

{
  "user_id": 123
}
```

**응답 예시:**
```json
{
  "recommendations": [
    {
      "book_id": "book123",
      "title": "추천 도서 제목",
      "author": "저자명",
      "book_category": "카테고리",
      "image_url": "이미지_URL"
    }
  ]
}
```

---

## 📊 **로깅 시스템**

### 🗂️ **로그 파일 구조**
```
logs/
├── bookstar.log              # 전체 로그 (14일 보관)
├── bookstar_error.log        # 에러 전용 (30일 보관)
├── bookstar_access.log       # HTTP 요청 로그 (7일 보관)
├── bookstar_performance.log  # 성능 측정 로그 (10일 보관)
└── bookstar_traceback.log    # 상세 예외 정보 (60일 보관)
```

### ⚡ **성능 임계값 설정**
| 임계값 | 기본값 | 설명 |
|--------|--------|------|
| `performance_threshold_ms` | 100ms | 기본 성능 로그 임계값 |
| `db_query_threshold_ms` | 50ms | 데이터베이스 쿼리 임계값 |
| `api_processing_threshold_ms` | 200ms | API 처리 임계값 |
| `heavy_computation_threshold_ms` | 500ms | 무거운 연산 임계값 |

### 📅 **자동 로그 관리**
- **시간 기반 로테이션**: 모든 로그가 매일 자정에 로테이션
- **자동 삭제**: 설정된 보관 일수 후 자동 삭제
- **압축 저장**: 오래된 로그는 자동으로 압축

**📖 상세한 로깅 가이드**: [LOGGING_GUIDE.md](LOGGING_GUIDE.md)

---

## 🔐 **보안 가이드**

### ⚠️ **절대 Git 커밋 금지**
```bash
.env.toml  # 🚫 민감한 정보 포함
```

### 🏢 **환경별 권장사항**

| 환경 | 방법 | 예시 |
|------|------|------|
| **로컬 개발** | `.env.toml` | 파일에 실제 값 저장 |
| **CI/CD** | 환경변수 | GitHub Secrets, GitLab Variables |
| **프로덕션** | 외부 서비스 | AWS Secrets Manager, Vault |

### 🔍 **민감한 정보 체크리스트**
- ✅ 데이터베이스 비밀번호
- ✅ AWS 액세스 키
- ✅ API 토큰
- ✅ 서버 IP 주소
- ✅ 암호화 키

---

## 🧪 **테스트**

```bash
# 전체 테스트 실행
pytest

# 커버리지 포함 테스트
pytest --cov=bookstar --cov-report=term-missing

# 특정 테스트 실행
pytest tests/test_config.py      # 설정 시스템 테스트 (15개)
pytest tests/test_main.py        # FastAPI 엔드포인트 테스트 (2개)
pytest tests/test_logging.py     # 로깅 시스템 테스트 (12개)
pytest tests/test_decorators.py  # 데코레이터 테스트 (17개)
pytest tests/test_recommendation.py  # 추천 시스템 테스트 (18개)

# 설정 시스템 빠른 검증 (기본)
python -c "from bookstar.config import settings; settings.app; settings.server; settings.recommendation; settings.logging; settings.aws; settings.database; settings.database_url; print('✅ 모든 설정 로드 성공')"

# 설정 시스템 완전 검증 (pytest와 동일한 로직)
python -c "
from bookstar.config.config import settings
try:
    # 모든 설정 섹션 접근 및 검증
    app = settings.app
    server = settings.server  
    rec = settings.recommendation
    log = settings.logging
    aws = settings.aws
    db = settings.database
    db_url = settings.database_url
    
    # 필수 키 존재 확인
    assert 'title' in app and 'host' in server and 'level' in log
    assert 'default_recommendations_count' in rec
    assert 'region' in aws and 'user' in db
    
    # 데이터 타입 검증
    assert isinstance(server['port'], int)
    assert isinstance(log['performance_threshold_ms'], int)
    assert isinstance(rec['content_weight'], (int, float))
    
    # 값 범위 검증
    assert 1 <= server['port'] <= 65535
    assert abs(rec['content_weight'] + rec['collaborative_weight'] - 1.0) < 0.001
    
    print('✅ 모든 설정 검증 완료 (pytest 수준)')
except Exception as e:
    print(f'❌ 설정 검증 실패: {e}')
    exit(1)
"
```

---

## 🛠️ **개발도구**

```bash
# 코드 품질 검사
ruff check .

# 코드 자동 수정
ruff check . --fix

# 타입 체크
mypy bookstar/

# 전체 품질 검사
pytest && pytest --cov=bookstar && mypy bookstar/ && ruff check .

# 로깅 시스템 예제 실행
python examples/logging_example.py
```

---

## 🐳 **Docker 실행**

### 방법 1: Docker 관리 스크립트 사용 (권장)

```bash
# 스크립트에 실행 권한 부여 (최초 1회)
chmod +x docker-run.sh

# Docker 이미지 빌드
./docker-run.sh build

# 컨테이너 시작 (config.toml에서 포트 자동 읽기)
./docker-run.sh start

# 상태 확인
./docker-run.sh status

# 실시간 로그 확인
./docker-run.sh logs

# 컨테이너 중지
./docker-run.sh stop

# 컨테이너 재시작
./docker-run.sh restart
```

**🔧 동적 포트 설정**: `docker-run.sh`는 `config.toml`에서 포트를 자동으로 읽어와 사용합니다. 포트를 변경하려면 `config.toml`의 `server.port` 값만 수정하면 됩니다.

### 방법 2: Docker Compose 사용

```bash
# 백그라운드에서 빌드 및 시작 (mysql 서비스 필요)
docker-compose up -d --build

# 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f ai-server

# 중지 및 제거
docker-compose down
```

**📝 Docker Compose 구조**:
- **포트**: 8000 고정 (호스트:컨테이너 모두 8000)
- **의존성**: mysql 서비스가 먼저 시작된 후 ai-server 시작
- **볼륨**: 로그 디렉토리만 호스트와 공유
- **네트워크**: 기본 네트워크 사용 (간소화)

### 방법 3: 직접 Docker 명령어 사용

```bash
# Docker 이미지 빌드
docker build -t docker-ai-server .

# Docker 컨테이너 실행
docker run -d \
  --name ai-server \
  -p 8000:8000 \
  --restart unless-stopped \
  -v $(pwd)/logs:/app/logs \
  docker-ai-server

# 컨테이너 상태 확인
docker ps
```

### 🔍 **예상 결과**

성공적으로 실행되면 다음과 같은 컨테이너 상태를 확인할 수 있습니다:

```
CONTAINER ID   IMAGE                COMMAND           CREATED        STATUS                  PORTS                    NAMES
07417843388d   docker-ai-server     "python main.py"  17 hours ago   Up 17 hours (healthy)   0.0.0.0:8000->8000/tcp   ai-server
```

### 🌐 **접속 정보**

- **API 서버**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs  
- **헬스체크**: 30초마다 자동 확인

---

## 🔧 **환경변수로 설정 오버라이드**

```bash
# 서버 설정 변경
export SERVER_HOST=127.0.0.1
export SERVER_PORT=9000

# 로그 레벨 변경
export LOG_LEVEL=DEBUG

# 추천 개수 변경 (현재는 config.toml에서만 지원)
```

---

## 📈 **모니터링**

### 🔍 **로그 모니터링**
```bash
# 실시간 로그 모니터링
tail -f logs/bookstar.log

# 에러 로그만 확인
tail -f logs/bookstar_error.log

# 성능 로그 확인
tail -f logs/bookstar_performance.log
```

### 📊 **성능 분석**
```bash
# 느린 쿼리 확인
grep "느린 쿼리" logs/bookstar.log

# 성능 임계값 초과 함수 확인
grep "실행 완료" logs/bookstar_performance.log
```

---

## ✅ **프로젝트 완료 상태**

### 🎯 **핵심 달성 사항**
- ✅ **완전한 하드코딩 제거**: 모든 설정값이 `config.toml`에서 관리됨
- ✅ **동적 설정 시스템**: Docker 스크립트까지 설정 파일 기반으로 작동
- ✅ **포괄적 테스트**: 64개 테스트, 88% 코드 커버리지 달성
- ✅ **코드 품질**: MyPy, Ruff 모든 검사 통과
- ✅ **로깅 시스템**: 5종류 로그 파일, 자동 로테이션 및 보관 정책
- ✅ **AI 추천 시스템**: 하이브리드 알고리즘, 완전한 설정 기반
- ✅ **Docker 최적화**: 중복 설정 제거, mysql 의존성 추가, 간소화된 구조

### �� **설정 가능한 모든 항목 (총 40개)**
| 카테고리 | 설정 항목 수 | 주요 설정 |
|----------|-------------|-----------|
| **앱 정보** | 4개 | 제목, 설명, 버전, CORS |
| **서버** | 2개 | 호스트, 포트 |
| **추천 시스템** | 10개 | 추천 개수, 가중치, 임계값 등 |
| **로깅** | 15개 | 로그 레벨, 임계값, 보관 정책 등 |
| **데이터베이스** | 5개 | 연결 정보 |
| **AWS** | 4개 | 인증 정보 |

### 📊 **최종 검증 결과**
```bash
# 모든 품질 검사 통과
✅ pytest: 64개 테스트 모두 통과
✅ 커버리지: 88% (773개 구문 중 92개 누락)
✅ mypy: 15개 소스 파일에서 타입 체크 문제 없음
✅ ruff: 모든 코드 스타일 및 품질 검사 통과
✅ 설정 검증: 모든 설정 섹션 로드 성공
✅ Docker: 중복 제거, 의존성 관리, 8000 포트 고정
```

### 🚀 **사용 준비 완료**
이제 `config.toml` 파일 하나만 수정하면 전체 시스템의 동작을 완전히 제어할 수 있습니다. 하드코딩된 값은 더 이상 존재하지 않으며, 모든 설정이 중앙화되어 관리됩니다.

**Docker 배포 방식**:
- **개발/테스트**: `docker-run.sh` 사용 (동적 포트)
- **프로덕션**: `docker-compose` 사용 (mysql 의존성, 8000 포트 고정)
