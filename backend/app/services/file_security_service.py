"""
파일 보안 및 검증 서비스
"""
import os
import hashlib
import mimetypes
import subprocess
import tempfile
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import magic
from fastapi import UploadFile, HTTPException
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class FileSecurityService:
    """파일 보안 및 검증 서비스"""
    
    # 허용된 파일 확장자
    ALLOWED_EXTENSIONS = {
        'images': {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'},
        'documents': {'.pdf', '.doc', '.docx', '.txt'},
        'archives': {'.zip', '.rar', '.7z'}
    }
    
    # 위험한 파일 확장자 (업로드 금지)
    DANGEROUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', 
        '.jar', '.php', '.asp', '.aspx', '.jsp', '.sh', '.ps1'
    }
    
    # 허용된 MIME 타입
    ALLOWED_MIME_TYPES = {
        'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'image/bmp',
        'application/pdf', 'text/plain',
        'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed'
    }
    
    # 악성 파일 시그니처 (간단한 패턴)
    MALICIOUS_SIGNATURES = [
        b'MZ',  # PE 실행 파일
        b'\x7fELF',  # ELF 실행 파일
        b'<script',  # JavaScript
        b'<?php',  # PHP 코드
        b'<%',  # ASP 코드
    ]
    
    def __init__(self):
        self.max_file_size = settings.MAX_FILE_SIZE
        self.quarantine_dir = os.path.join(settings.UPLOAD_DIR, 'quarantine')
        os.makedirs(self.quarantine_dir, exist_ok=True)
    
    async def validate_file_security(self, file: UploadFile) -> Dict[str, any]:
        """파일 보안 검증"""
        validation_result = {
            'is_safe': True,
            'issues': [],
            'file_info': {},
            'scan_results': {}
        }
        
        try:
            # 파일 내용 읽기
            content = await file.read()
            await file.seek(0)  # 파일 포인터 리셋
            
            # 기본 파일 정보 수집
            validation_result['file_info'] = {
                'filename': file.filename,
                'size': len(content),
                'content_type': file.content_type,
                'md5_hash': hashlib.md5(content).hexdigest(),
                'sha256_hash': hashlib.sha256(content).hexdigest()
            }
            
            # 1. 파일 크기 검증
            if not self._validate_file_size(len(content)):
                validation_result['is_safe'] = False
                validation_result['issues'].append('파일 크기가 허용 한도를 초과했습니다.')
            
            # 2. 파일 확장자 검증
            if not self._validate_file_extension(file.filename):
                validation_result['is_safe'] = False
                validation_result['issues'].append('허용되지 않는 파일 확장자입니다.')
            
            # 3. MIME 타입 검증
            real_mime_type = magic.from_buffer(content, mime=True)
            validation_result['file_info']['real_mime_type'] = real_mime_type
            
            if not self._validate_mime_type(real_mime_type):
                validation_result['is_safe'] = False
                validation_result['issues'].append('허용되지 않는 파일 형식입니다.')
            
            # 4. 파일 헤더 검증 (확장자와 실제 내용 일치 여부)
            if not self._validate_file_header(file.filename, content):
                validation_result['is_safe'] = False
                validation_result['issues'].append('파일 확장자와 실제 내용이 일치하지 않습니다.')
            
            # 5. 악성 코드 시그니처 검사
            malicious_patterns = self._scan_malicious_patterns(content)
            if malicious_patterns:
                validation_result['is_safe'] = False
                validation_result['issues'].append(f'악성 패턴이 발견되었습니다: {malicious_patterns}')
                validation_result['scan_results']['malicious_patterns'] = malicious_patterns
            
            # 6. 이미지 파일 추가 검증
            if real_mime_type.startswith('image/'):
                image_validation = self._validate_image_file(content)
                validation_result['scan_results']['image_validation'] = image_validation
                if not image_validation['is_valid']:
                    validation_result['is_safe'] = False
                    validation_result['issues'].extend(image_validation['issues'])
            
            # 7. 바이러스 스캔 (ClamAV가 설치된 경우)
            virus_scan_result = await self._scan_virus(content)
            validation_result['scan_results']['virus_scan'] = virus_scan_result
            if not virus_scan_result['is_clean']:
                validation_result['is_safe'] = False
                validation_result['issues'].append('바이러스가 발견되었습니다.')
            
        except Exception as e:
            logger.error(f"파일 보안 검증 중 오류: {str(e)}")
            validation_result['is_safe'] = False
            validation_result['issues'].append(f'파일 검증 중 오류가 발생했습니다: {str(e)}')
        
        return validation_result
    
    def _validate_file_size(self, size: int) -> bool:
        """파일 크기 검증"""
        return size <= self.max_file_size
    
    def _validate_file_extension(self, filename: str) -> bool:
        """파일 확장자 검증"""
        if not filename:
            return False
        
        extension = Path(filename).suffix.lower()
        
        # 위험한 확장자 차단
        if extension in self.DANGEROUS_EXTENSIONS:
            return False
        
        # 허용된 확장자 확인
        for category, extensions in self.ALLOWED_EXTENSIONS.items():
            if extension in extensions:
                return True
        
        return False
    
    def _validate_mime_type(self, mime_type: str) -> bool:
        """MIME 타입 검증"""
        return mime_type in self.ALLOWED_MIME_TYPES
    
    def _validate_file_header(self, filename: str, content: bytes) -> bool:
        """파일 헤더 검증 (매직 넘버 확인)"""
        if not content:
            return False
        
        extension = Path(filename).suffix.lower()
        
        # 이미지 파일 헤더 검증
        image_headers = {
            '.jpg': [b'\xff\xd8\xff'],
            '.jpeg': [b'\xff\xd8\xff'],
            '.png': [b'\x89PNG\r\n\x1a\n'],
            '.gif': [b'GIF87a', b'GIF89a'],
            '.webp': [b'RIFF'],
            '.bmp': [b'BM']
        }
        
        if extension in image_headers:
            for header in image_headers[extension]:
                if content.startswith(header):
                    return True
            return False
        
        # PDF 파일 헤더 검증
        if extension == '.pdf':
            return content.startswith(b'%PDF-')
        
        # ZIP 파일 헤더 검증
        if extension == '.zip':
            return content.startswith(b'PK\x03\x04') or content.startswith(b'PK\x05\x06')
        
        # 기타 파일은 통과
        return True
    
    def _scan_malicious_patterns(self, content: bytes) -> List[str]:
        """악성 패턴 스캔"""
        found_patterns = []
        
        for signature in self.MALICIOUS_SIGNATURES:
            if signature in content:
                found_patterns.append(signature.decode('utf-8', errors='ignore'))
        
        # 스크립트 태그 검사
        dangerous_patterns = [
            b'<script', b'</script>', b'javascript:', b'vbscript:',
            b'onload=', b'onerror=', b'onclick=', b'eval(',
            b'document.write', b'innerHTML'
        ]
        
        for pattern in dangerous_patterns:
            if pattern in content.lower():
                found_patterns.append(pattern.decode('utf-8', errors='ignore'))
        
        return found_patterns
    
    def _validate_image_file(self, content: bytes) -> Dict[str, any]:
        """이미지 파일 추가 검증"""
        result = {
            'is_valid': True,
            'issues': [],
            'metadata': {}
        }
        
        try:
            from PIL import Image
            from io import BytesIO
            
            # PIL로 이미지 열기 시도
            image = Image.open(BytesIO(content))
            
            # 이미지 메타데이터 수집
            result['metadata'] = {
                'format': image.format,
                'mode': image.mode,
                'size': image.size,
                'has_transparency': image.mode in ('RGBA', 'LA') or 'transparency' in image.info
            }
            
            # 이미지 크기 제한 (예: 최대 4K 해상도)
            max_dimension = 4096
            if image.size[0] > max_dimension or image.size[1] > max_dimension:
                result['is_valid'] = False
                result['issues'].append(f'이미지 크기가 너무 큽니다. 최대 {max_dimension}x{max_dimension}까지 허용됩니다.')
            
            # EXIF 데이터 검사 (개인정보 포함 가능성)
            if hasattr(image, '_getexif') and image._getexif():
                result['metadata']['has_exif'] = True
                # 실제 서비스에서는 EXIF 데이터를 제거하는 것이 좋습니다
            
        except Exception as e:
            result['is_valid'] = False
            result['issues'].append(f'이미지 파일이 손상되었거나 올바르지 않습니다: {str(e)}')
        
        return result
    
    async def _scan_virus(self, content: bytes) -> Dict[str, any]:
        """바이러스 스캔 (ClamAV 사용)"""
        result = {
            'is_clean': True,
            'scanner': 'none',
            'scan_result': 'not_scanned'
        }
        
        try:
            # ClamAV가 설치되어 있는지 확인
            clamscan_path = self._find_clamscan()
            if not clamscan_path:
                result['scan_result'] = 'scanner_not_available'
                return result
            
            # 임시 파일에 내용 저장
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                # ClamAV로 스캔 실행
                cmd = [clamscan_path, '--no-summary', '--infected', temp_file_path]
                process = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=30
                )
                
                result['scanner'] = 'clamav'
                
                if process.returncode == 0:
                    result['is_clean'] = True
                    result['scan_result'] = 'clean'
                elif process.returncode == 1:
                    result['is_clean'] = False
                    result['scan_result'] = 'infected'
                    result['details'] = process.stdout.strip()
                else:
                    result['scan_result'] = 'scan_error'
                    result['error'] = process.stderr.strip()
                
            finally:
                # 임시 파일 삭제
                os.unlink(temp_file_path)
                
        except subprocess.TimeoutExpired:
            result['scan_result'] = 'scan_timeout'
        except Exception as e:
            logger.error(f"바이러스 스캔 중 오류: {str(e)}")
            result['scan_result'] = 'scan_error'
            result['error'] = str(e)
        
        return result
    
    def _find_clamscan(self) -> Optional[str]:
        """ClamAV clamscan 실행 파일 찾기"""
        possible_paths = [
            '/usr/bin/clamscan',
            '/usr/local/bin/clamscan',
            '/opt/homebrew/bin/clamscan',  # macOS Homebrew
            'clamscan'  # PATH에서 찾기
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run([path, '--version'], capture_output=True, timeout=5)
                if result.returncode == 0:
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        return None
    
    async def quarantine_file(self, file_content: bytes, filename: str, reason: str) -> str:
        """위험한 파일을 격리 디렉토리로 이동"""
        try:
            # 격리 파일명 생성 (타임스탬프 + 해시)
            import time
            timestamp = int(time.time())
            file_hash = hashlib.md5(file_content).hexdigest()[:8]
            quarantine_filename = f"{timestamp}_{file_hash}_{filename}"
            
            quarantine_path = os.path.join(self.quarantine_dir, quarantine_filename)
            
            # 파일 저장
            with open(quarantine_path, 'wb') as f:
                f.write(file_content)
            
            # 격리 로그 기록
            log_path = os.path.join(self.quarantine_dir, 'quarantine.log')
            with open(log_path, 'a', encoding='utf-8') as log_file:
                log_file.write(f"{timestamp},{quarantine_filename},{filename},{reason}\n")
            
            logger.warning(f"파일이 격리되었습니다: {filename} -> {quarantine_filename}, 사유: {reason}")
            
            return quarantine_path
            
        except Exception as e:
            logger.error(f"파일 격리 중 오류: {str(e)}")
            raise HTTPException(status_code=500, detail="파일 격리 중 오류가 발생했습니다.")
    
    def get_file_permissions(self, user_role: str, file_type: str) -> Dict[str, bool]:
        """사용자 역할에 따른 파일 접근 권한 반환"""
        permissions = {
            'can_upload': False,
            'can_download': False,
            'can_delete': False,
            'can_view_metadata': False
        }
        
        if user_role == 'admin':
            permissions.update({
                'can_upload': True,
                'can_download': True,
                'can_delete': True,
                'can_view_metadata': True
            })
        elif user_role == 'manager':
            permissions.update({
                'can_upload': True,
                'can_download': True,
                'can_delete': False,
                'can_view_metadata': True
            })
        elif user_role == 'user':
            if file_type in ['image', 'document']:
                permissions.update({
                    'can_upload': True,
                    'can_download': True,
                    'can_delete': False,
                    'can_view_metadata': False
                })
        
        return permissions
    
    async def cleanup_quarantine_files(self, days_old: int = 30) -> int:
        """오래된 격리 파일 정리"""
        cleaned_count = 0
        
        try:
            import time
            current_time = time.time()
            cutoff_time = current_time - (days_old * 24 * 3600)
            
            for filename in os.listdir(self.quarantine_dir):
                if filename == 'quarantine.log':
                    continue
                
                file_path = os.path.join(self.quarantine_dir, filename)
                
                if os.path.isfile(file_path):
                    file_mtime = os.path.getmtime(file_path)
                    
                    if file_mtime < cutoff_time:
                        os.remove(file_path)
                        cleaned_count += 1
                        logger.info(f"오래된 격리 파일 삭제: {filename}")
            
        except Exception as e:
            logger.error(f"격리 파일 정리 중 오류: {str(e)}")
        
        return cleaned_count


# 전역 파일 보안 서비스 인스턴스
file_security_service = FileSecurityService()