"""
로그 설정 모듈
파이썬 표준 logging 모듈을 사용한 종합적인 로그 설정
"""
import json
import logging
import logging.handlers
import sys
import traceback
from datetime import datetime
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """JSON 형식으로 로그를 포맷팅하는 커스텀 포매터"""
    
    def format(self, record: logging.LogRecord) -> str:
        """로그 레코드를 JSON 형식으로 변환"""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": record.process,
            "thread_id": record.thread,
        }
        
        # 추가 속성들이 있으면 포함
        if hasattr(record, 'execution_time'):
            log_entry['execution_time_ms'] = record.execution_time
        
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
            
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        
        # 예외 정보가 있으면 포함
        if record.exc_info:
            exc_type, exc_value, exc_traceback = record.exc_info
            log_entry['exception'] = {
                'type': exc_type.__name__ if exc_type else 'Unknown',
                'message': str(exc_value) if exc_value else '',
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_entry, ensure_ascii=False)


class TracebackHandler(logging.handlers.TimedRotatingFileHandler):
    """Traceback을 별도 파일에 저장하는 핸들러 (시간 기반 로테이션)"""
    
    def __init__(self, filename: str, retention_days: int = 60):
        # 디렉토리가 없으면 생성
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        
        # TimedRotatingFileHandler 초기화
        super().__init__(
            filename=filename,
            when='midnight',
            interval=1,
            backupCount=retention_days,
            encoding='utf-8'
        )
    
    def emit(self, record: logging.LogRecord):
        """에러 레벨 로그의 traceback을 별도 파일에 저장"""
        if record.levelno >= logging.ERROR and record.exc_info:
            try:
                # 포맷팅된 traceback 메시지 생성
                original_msg = record.getMessage()
                
                # 상세한 traceback 정보 추가
                traceback_info = []
                traceback_info.append(f"\n{'='*80}")
                timestamp = datetime.fromtimestamp(record.created).isoformat()
                traceback_info.append(f"Timestamp: {timestamp}")
                traceback_info.append(f"Logger: {record.name}")
                traceback_info.append(f"Level: {record.levelname}")
                traceback_info.append(f"Message: {original_msg}")
                traceback_info.append(f"{'='*80}")
                
                # Traceback 추가
                if record.exc_info:
                    traceback_lines = traceback.format_exception(*record.exc_info)
                    traceback_info.extend(traceback_lines)
                
                traceback_info.append(f"{'='*80}\n")
                
                # 메시지 업데이트
                record.msg = '\n'.join(traceback_info)
                record.args = ()
                
                # 부모 클래스의 emit 호출 (로테이션 기능 포함)
                super().emit(record)
                
            except Exception:
                # 로그 핸들러에서 예외가 발생하면 무시 (무한 루프 방지)
                pass


class LoggingConfig:
    """로깅 설정 관리 클래스"""
    
    def __init__(self, log_dir: str = "logs", app_name: str = "bookstar"):
        self.log_dir = Path(log_dir)
        self.app_name = app_name
        self.log_dir.mkdir(exist_ok=True)
        
        # 로그 파일 경로들
        self.log_files = {
            'all': self.log_dir / f"{app_name}.log",
            'error': self.log_dir / f"{app_name}_error.log",
            'access': self.log_dir / f"{app_name}_access.log",
            'performance': self.log_dir / f"{app_name}_performance.log",
            'traceback': self.log_dir / f"{app_name}_traceback.log",
        }
    
    def setup_logging(self, 
                     log_level: str = "INFO", 
                     use_json: bool = False,
                     enable_console: bool = True,
                     max_file_size_mb: int = 10,
                     backup_count: int = 5,
                     enable_access_log: bool = True,
                     enable_performance_log: bool = True,
                     enable_traceback_log: bool = True,
                     main_log_retention_days: int = 14,
                     error_log_retention_days: int = 30,
                     access_log_retention_days: int = 7,
                     performance_log_retention_days: int = 10,
                     traceback_log_retention_days: int = 60) -> None:
        """로깅 설정을 초기화합니다."""
        
        # 기존 핸들러 제거 (중복 로그 방지)
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 로그 레벨 설정
        level = getattr(logging, log_level.upper())
        root_logger.setLevel(level)
        
        # 포매터 선택
        if use_json:
            formatter: logging.Formatter = JSONFormatter()
            console_formatter: logging.Formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - '
                '%(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                datefmt='%H:%M:%S'
            )
        
        # 1. 콘솔 핸들러 (옵션)
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
        
        # 2. 전체 로그 파일 핸들러 (시간 기반 로테이션으로 변경)
        all_handler = logging.handlers.TimedRotatingFileHandler(
            self.log_files['all'],
            when='midnight',
            interval=1,
            backupCount=main_log_retention_days,
            encoding='utf-8'
        )
        all_handler.setLevel(logging.DEBUG)
        all_handler.setFormatter(formatter)
        root_logger.addHandler(all_handler)
        
        # 3. 에러 전용 파일 핸들러 (시간 기반 로테이션)
        error_handler = logging.handlers.TimedRotatingFileHandler(
            self.log_files['error'],
            when='midnight',
            interval=1,
            backupCount=error_log_retention_days,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)
        
        # 4. 성능 로그 핸들러 (조건부 생성, 시간 기반 로테이션으로 변경)
        if enable_performance_log:
            performance_handler = logging.handlers.TimedRotatingFileHandler(
                self.log_files['performance'],
                when='midnight',
                interval=1,
                backupCount=performance_log_retention_days,
                encoding='utf-8'
            )
            performance_handler.setLevel(logging.INFO)
            performance_handler.setFormatter(formatter)
            
            # 성능 로거 생성
            performance_logger = logging.getLogger('performance')
            performance_logger.addHandler(performance_handler)
            performance_logger.setLevel(logging.INFO)
            performance_logger.propagate = False  # 중복 로그 방지
        
        # 5. 액세스 로그 핸들러 (조건부 생성)
        if enable_access_log:
            access_handler = logging.handlers.TimedRotatingFileHandler(
                self.log_files['access'],
                when='midnight',
                interval=1,
                backupCount=access_log_retention_days,
                encoding='utf-8'
            )
            access_handler.setLevel(logging.INFO)
            access_handler.setFormatter(formatter)
            
            # 액세스 로거 생성
            access_logger = logging.getLogger('access')
            access_logger.addHandler(access_handler)
            access_logger.setLevel(logging.INFO)
            access_logger.propagate = False
        
        # 6. Traceback 전용 핸들러 (조건부 생성, 시간 기반 로테이션)
        if enable_traceback_log:
            traceback_handler = TracebackHandler(
                str(self.log_files['traceback']),
                retention_days=traceback_log_retention_days
            )
            traceback_handler.setLevel(logging.ERROR)
            root_logger.addHandler(traceback_handler)
        
        # 로깅 설정 완료 로그
        logging.info(f"로깅 시스템이 초기화되었습니다. 로그 디렉토리: {self.log_dir}")
        logging.info(f"로그 레벨: {log_level}, JSON 포맷: {use_json}")
        logging.info("모든 로그 파일이 시간 기반 로테이션으로 설정되었습니다.")
        logging.info(
            f"보관 정책 - 전체: {main_log_retention_days}일, "
            f"에러: {error_log_retention_days}일, "
            f"액세스: {access_log_retention_days}일"
        )
        logging.info(
            f"보관 정책 - 성능: {performance_log_retention_days}일, "
            f"Traceback: {traceback_log_retention_days}일"
        )
        logging.info(
            f"활성화된 로그 - 액세스: {enable_access_log}, "
            f"성능: {enable_performance_log}, "
            f"Traceback: {enable_traceback_log}"
        )
    
    def get_logger(self, name: str) -> logging.Logger:
        """특정 이름의 로거를 반환합니다."""
        return logging.getLogger(name)
    
    def get_performance_logger(self) -> logging.Logger:
        """성능 측정 전용 로거를 반환합니다."""
        return logging.getLogger('performance')
    
    def get_access_logger(self) -> logging.Logger:
        """액세스 로그 전용 로거를 반환합니다."""
        return logging.getLogger('access')


# 전역 로깅 설정 인스턴스
logging_config = LoggingConfig() 