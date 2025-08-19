"""
구조화된 로깅 시스템 설정
"""
import os
import sys
import json
import logging
import logging.config
from datetime import datetime
from typing import Any, Dict, Optional
from pythonjsonlogger import jsonlogger
from app.core.config import settings

class StructuredFormatter(jsonlogger.JsonFormatter):
    """구조화된 JSON 로그 포매터"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        super().add_fields(log_record, record, message_dict)
        
        # 기본 필드 추가
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # 환경 정보 추가
        log_record['environment'] = settings.ENVIRONMENT
        log_record['service'] = 'myzone-api'
        log_record['version'] = '1.0.0'
        
        # 프로세스 정보 추가
        log_record['process_id'] = os.getpid()
        log_record['thread_id'] = record.thread
        
        # 추가 컨텍스트 정보가 있으면 포함
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        if hasattr(record, 'ip_address'):
            log_record['ip_address'] = record.ip_address
        if hasattr(record, 'endpoint'):
            log_record['endpoint'] = record.endpoint
        if hasattr(record, 'method'):
            log_record['method'] = record.method
        if hasattr(record, 'status_code'):
            log_record['status_code'] = record.status_code
        if hasattr(record, 'response_time'):
            log_record['response_time'] = record.response_time
        if hasattr(record, 'error_code'):
            log_record['error_code'] = record.error_code

class SecurityLogFilter(logging.Filter):
    """보안 관련 로그 필터"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        # 민감한 정보 마스킹
        if hasattr(record, 'args') and record.args:
            record.args = self._mask_sensitive_data(record.args)
        
        # 메시지에서 민감한 정보 마스킹
        if record.getMessage():
            record.msg = self._mask_sensitive_message(record.msg)
        
        return True
    
    def _mask_sensitive_data(self, args: tuple) -> tuple:
        """민감한 데이터 마스킹"""
        masked_args = []
        for arg in args:
            if isinstance(arg, str):
                masked_args.append(self._mask_sensitive_message(arg))
            else:
                masked_args.append(arg)
        return tuple(masked_args)
    
    def _mask_sensitive_message(self, message: str) -> str:
        """민감한 메시지 마스킹"""
        import re
        
        # 비밀번호 마스킹
        message = re.sub(r'(password["\']?\s*[:=]\s*["\']?)([^"\'}\s,]+)', r'\1****', message, flags=re.IGNORECASE)
        
        # 토큰 마스킹
        message = re.sub(r'(token["\']?\s*[:=]\s*["\']?)([^"\'}\s,]+)', r'\1****', message, flags=re.IGNORECASE)
        
        # 카드번호 마스킹
        message = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '****-****-****-****', message)
        
        # 주민번호 마스킹
        message = re.sub(r'\b\d{6}[-]?\d{7}\b', '******-*******', message)
        
        # 전화번호 부분 마스킹
        message = re.sub(r'\b01[0-9][-]?\d{3,4}[-]?\d{4}\b', lambda m: m.group()[:3] + '****' + m.group()[-4:], message)
        
        return message

def get_logging_config() -> Dict[str, Any]:
    """로깅 설정 반환"""
    
    # 로그 디렉토리 생성
    log_dir = os.path.join(os.getcwd(), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'structured': {
                '()': StructuredFormatter,
                'format': '%(timestamp)s %(level)s %(name)s %(message)s'
            },
            'simple': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        },
        'filters': {
            'security_filter': {
                '()': SecurityLogFilter,
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'structured' if settings.ENVIRONMENT == 'production' else 'simple',
                'stream': sys.stdout,
                'filters': ['security_filter']
            },
            'file_info': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'INFO',
                'formatter': 'structured',
                'filename': os.path.join(log_dir, 'app.log'),
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'filters': ['security_filter']
            },
            'file_error': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'structured',
                'filename': os.path.join(log_dir, 'error.log'),
                'maxBytes': 10485760,  # 10MB
                'backupCount': 10,
                'filters': ['security_filter']
            },
            'file_security': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'WARNING',
                'formatter': 'structured',
                'filename': os.path.join(log_dir, 'security.log'),
                'maxBytes': 10485760,  # 10MB
                'backupCount': 10,
                'filters': ['security_filter']
            },
            'file_access': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'INFO',
                'formatter': 'structured',
                'filename': os.path.join(log_dir, 'access.log'),
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'filters': ['security_filter']
            }
        },
        'loggers': {
            # 루트 로거
            '': {
                'level': 'INFO',
                'handlers': ['console', 'file_info', 'file_error'],
                'propagate': False
            },
            # 애플리케이션 로거
            'app': {
                'level': 'DEBUG' if settings.ENVIRONMENT == 'development' else 'INFO',
                'handlers': ['console', 'file_info', 'file_error'],
                'propagate': False
            },
            # 보안 로거
            'security': {
                'level': 'WARNING',
                'handlers': ['console', 'file_security'],
                'propagate': False
            },
            # 액세스 로거
            'access': {
                'level': 'INFO',
                'handlers': ['file_access'],
                'propagate': False
            },
            # 외부 라이브러리 로거 레벨 조정
            'uvicorn': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False
            },
            'uvicorn.access': {
                'level': 'INFO',
                'handlers': ['file_access'],
                'propagate': False
            },
            'sqlalchemy': {
                'level': 'WARNING',
                'handlers': ['console', 'file_error'],
                'propagate': False
            },
            'alembic': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False
            }
        }
    }
    
    return config

def setup_logging():
    """로깅 설정 초기화"""
    config = get_logging_config()
    logging.config.dictConfig(config)
    
    # 로깅 설정 완료 로그
    logger = logging.getLogger('app')
    logger.info("Logging system initialized", extra={
        'environment': settings.ENVIRONMENT,
        'log_level': logger.level
    })

class LogContext:
    """로그 컨텍스트 관리 클래스"""
    
    def __init__(self):
        self._context = {}
    
    def set(self, key: str, value: Any):
        """컨텍스트 값 설정"""
        self._context[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """컨텍스트 값 조회"""
        return self._context.get(key, default)
    
    def clear(self):
        """컨텍스트 초기화"""
        self._context.clear()
    
    def get_all(self) -> Dict[str, Any]:
        """모든 컨텍스트 반환"""
        return self._context.copy()

# 전역 로그 컨텍스트
log_context = LogContext()

def get_logger(name: str) -> logging.Logger:
    """컨텍스트가 포함된 로거 반환"""
    logger = logging.getLogger(name)
    
    # 기존 로거를 래핑하여 컨텍스트 정보 자동 추가
    class ContextLogger:
        def __init__(self, logger: logging.Logger):
            self._logger = logger
        
        def _log_with_context(self, level: int, msg: str, *args, **kwargs):
            # 컨텍스트 정보를 extra에 추가
            extra = kwargs.get('extra', {})
            extra.update(log_context.get_all())
            kwargs['extra'] = extra
            
            self._logger.log(level, msg, *args, **kwargs)
        
        def debug(self, msg: str, *args, **kwargs):
            self._log_with_context(logging.DEBUG, msg, *args, **kwargs)
        
        def info(self, msg: str, *args, **kwargs):
            self._log_with_context(logging.INFO, msg, *args, **kwargs)
        
        def warning(self, msg: str, *args, **kwargs):
            self._log_with_context(logging.WARNING, msg, *args, **kwargs)
        
        def error(self, msg: str, *args, **kwargs):
            self._log_with_context(logging.ERROR, msg, *args, **kwargs)
        
        def critical(self, msg: str, *args, **kwargs):
            self._log_with_context(logging.CRITICAL, msg, *args, **kwargs)
        
        def exception(self, msg: str, *args, **kwargs):
            kwargs['exc_info'] = True
            self.error(msg, *args, **kwargs)
    
    return ContextLogger(logger)