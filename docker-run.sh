#!/bin/bash

# BookStar AI Docker 실행 스크립트
# 사용법: ./docker-run.sh [build|start|stop|restart|logs|status]

set -e

IMAGE_NAME="docker-ai-server"
CONTAINER_NAME="ai-server"

# config.toml에서 포트 읽기 (기본값: 8000)
if command -v python3 &> /dev/null && [ -f "config.toml" ]; then
    PORT=$(python3 -c "
import tomllib
try:
    with open('config.toml', 'rb') as f:
        config = tomllib.load(f)
    print(config.get('server', {}).get('port', 8000))
except:
    print(8000)
" 2>/dev/null || echo "8000")
else
    PORT="8000"
fi

# config.toml의 포트를 환경변수로 설정
export SERVER_PORT="$PORT"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 설정 정보 출력
log_info "config.toml에서 읽어온 포트: $PORT"
log_info "SERVER_PORT 환경변수 설정: $SERVER_PORT"

# Docker 이미지 빌드
build_image() {
    log_info "Docker 이미지 빌드 시작: $IMAGE_NAME"
    
    if docker build -t $IMAGE_NAME . ; then
        log_success "Docker 이미지 빌드 완료: $IMAGE_NAME"
    else
        log_error "Docker 이미지 빌드 실패"
        exit 1
    fi
}

# 컨테이너 시작
start_container() {
    # 기존 컨테이너가 실행 중인지 확인
    if docker ps -q -f name=$CONTAINER_NAME | grep -q . ; then
        log_warning "컨테이너 $CONTAINER_NAME 이미 실행 중입니다"
        return 0
    fi
    
    # 중지된 컨테이너가 있는지 확인하고 제거
    if docker ps -a -q -f name=$CONTAINER_NAME | grep -q . ; then
        log_info "기존 컨테이너 $CONTAINER_NAME 제거 중..."
        docker rm $CONTAINER_NAME
    fi
    
    log_info "컨테이너 시작: $CONTAINER_NAME"
    
    if docker run -d \
        --name $CONTAINER_NAME \
        -p $PORT:$PORT \
        --restart unless-stopped \
        -v $(pwd)/logs:/app/logs \
        $IMAGE_NAME ; then
        log_success "컨테이너 시작 완료: $CONTAINER_NAME"
        log_info "포트: http://localhost:$PORT"
        log_info "API 문서: http://localhost:$PORT/docs"
    else
        log_error "컨테이너 시작 실패"
        exit 1
    fi
}

# 컨테이너 중지
stop_container() {
    if docker ps -q -f name=$CONTAINER_NAME | grep -q . ; then
        log_info "컨테이너 중지: $CONTAINER_NAME"
        docker stop $CONTAINER_NAME
        log_success "컨테이너 중지 완료: $CONTAINER_NAME"
    else
        log_warning "실행 중인 컨테이너 $CONTAINER_NAME 없음"
    fi
}

# 컨테이너 재시작
restart_container() {
    log_info "컨테이너 재시작: $CONTAINER_NAME"
    stop_container
    sleep 2
    start_container
}

# 로그 확인
show_logs() {
    if docker ps -q -f name=$CONTAINER_NAME | grep -q . ; then
        log_info "컨테이너 로그 확인: $CONTAINER_NAME"
        docker logs -f $CONTAINER_NAME
    else
        log_error "실행 중인 컨테이너 $CONTAINER_NAME 없음"
        exit 1
    fi
}

# 상태 확인
show_status() {
    log_info "Docker 컨테이너 상태:"
    echo
    docker ps -a --filter name=$CONTAINER_NAME --format "table {{.ID}}\t{{.Image}}\t{{.Command}}\t{{.CreatedAt}}\t{{.Status}}\t{{.Ports}}\t{{.Names}}"
    echo
    
    if docker ps -q -f name=$CONTAINER_NAME | grep -q . ; then
        log_success "컨테이너 $CONTAINER_NAME 실행 중"
        log_info "헬스체크 상태 확인 중..."
        
        # 헬스체크 상태 확인
        health_status=$(docker inspect --format='{{.State.Health.Status}}' $CONTAINER_NAME 2>/dev/null || echo "unknown")
        case $health_status in
            "healthy")
                log_success "헬스체크: 정상 (healthy)"
                ;;
            "unhealthy")
                log_error "헬스체크: 비정상 (unhealthy)"
                ;;
            "starting")
                log_warning "헬스체크: 시작 중 (starting)"
                ;;
            *)
                log_warning "헬스체크: 알 수 없음 ($health_status)"
                ;;
        esac
        
        log_info "접속 URL: http://localhost:$PORT"
        log_info "API 문서: http://localhost:$PORT/docs"
    else
        log_warning "컨테이너 $CONTAINER_NAME 중지됨"
    fi
}

# 도움말
show_help() {
    echo "BookStar AI Docker 관리 스크립트"
    echo
    echo "사용법: $0 [명령어]"
    echo
    echo "명령어:"
    echo "  build     - Docker 이미지 빌드"
    echo "  start     - 컨테이너 시작"
    echo "  stop      - 컨테이너 중지"  
    echo "  restart   - 컨테이너 재시작"
    echo "  logs      - 컨테이너 로그 확인"
    echo "  status    - 컨테이너 상태 확인"
    echo "  help      - 도움말 표시"
    echo
    echo "예시:"
    echo "  $0 build && $0 start  # 빌드 후 시작"
    echo "  $0 status             # 상태 확인"
    echo "  $0 logs               # 실시간 로그 확인"
}

# 메인 로직
case "${1:-help}" in
    "build")
        build_image
        ;;
    "start")
        start_container
        ;;
    "stop")
        stop_container
        ;;
    "restart")
        restart_container
        ;;
    "logs")
        show_logs
        ;;
    "status")
        show_status
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    *)
        log_error "알 수 없는 명령어: $1"
        echo
        show_help
        exit 1
        ;;
esac 