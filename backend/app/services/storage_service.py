"""
스토리지 관리 서비스
"""
import os
import shutil
import logging
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime, timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """스토리지 관리 서비스"""
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.max_storage_size = getattr(settings, 'MAX_STORAGE_SIZE', 10 * 1024 * 1024 * 1024)  # 10GB 기본값
        
        # 디렉토리 구조 생성
        self.directories = {
            'images': self.upload_dir / 'images',
            'documents': self.upload_dir / 'documents',
            'temp': self.upload_dir / 'temp',
            'quarantine': self.upload_dir / 'quarantine',
            'backups': self.upload_dir / 'backups'
        }
        
        for directory in self.directories.values():
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_storage_usage(self) -> Dict[str, any]:
        """스토리지 사용량 조회"""
        usage_info = {
            'total_size_bytes': 0,
            'total_size_mb': 0,
            'directories': {},
            'file_counts': {},
            'oldest_file': None,
            'newest_file': None
        }
        
        oldest_time = float('inf')
        newest_time = 0
        
        for name, directory in self.directories.items():
            if not directory.exists():
                continue
            
            dir_size = 0
            file_count = 0
            
            try:
                for file_path in directory.rglob('*'):
                    if file_path.is_file():
                        file_size = file_path.stat().st_size
                        file_mtime = file_path.stat().st_mtime
                        
                        dir_size += file_size
                        file_count += 1
                        
                        if file_mtime < oldest_time:
                            oldest_time = file_mtime
                            usage_info['oldest_file'] = {
                                'path': str(file_path),
                                'modified': datetime.fromtimestamp(file_mtime).isoformat()
                            }
                        
                        if file_mtime > newest_time:
                            newest_time = file_mtime
                            usage_info['newest_file'] = {
                                'path': str(file_path),
                                'modified': datetime.fromtimestamp(file_mtime).isoformat()
                            }
                
                usage_info['directories'][name] = {
                    'size_bytes': dir_size,
                    'size_mb': round(dir_size / (1024 * 1024), 2),
                    'file_count': file_count
                }
                
                usage_info['total_size_bytes'] += dir_size
                usage_info['file_counts'][name] = file_count
                
            except Exception as e:
                logger.error(f"디렉토리 {name} 사용량 조회 중 오류: {str(e)}")
                usage_info['directories'][name] = {'error': str(e)}
        
        usage_info['total_size_mb'] = round(usage_info['total_size_bytes'] / (1024 * 1024), 2)
        usage_info['total_size_gb'] = round(usage_info['total_size_bytes'] / (1024 * 1024 * 1024), 2)
        usage_info['usage_percentage'] = round(
            (usage_info['total_size_bytes'] / self.max_storage_size) * 100, 2
        )
        
        return usage_info
    
    def cleanup_old_files(self, days_old: int = 30, directory_name: str = 'temp') -> int:
        """오래된 파일 정리"""
        if directory_name not in self.directories:
            raise ValueError(f"알 수 없는 디렉토리: {directory_name}")
        
        directory = self.directories[directory_name]
        if not directory.exists():
            return 0
        
        cutoff_time = datetime.now() - timedelta(days=days_old)
        cleaned_count = 0
        
        try:
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    if file_mtime < cutoff_time:
                        try:
                            file_path.unlink()
                            cleaned_count += 1
                            logger.info(f"오래된 파일 삭제: {file_path}")
                        except Exception as e:
                            logger.error(f"파일 삭제 실패 {file_path}: {str(e)}")
            
        except Exception as e:
            logger.error(f"파일 정리 중 오류: {str(e)}")
        
        return cleaned_count
    
    def cleanup_empty_directories(self) -> int:
        """빈 디렉토리 정리"""
        cleaned_count = 0
        
        try:
            for directory in self.directories.values():
                if not directory.exists():
                    continue
                
                for subdir in directory.rglob('*'):
                    if subdir.is_dir() and not any(subdir.iterdir()):
                        try:
                            subdir.rmdir()
                            cleaned_count += 1
                            logger.info(f"빈 디렉토리 삭제: {subdir}")
                        except Exception as e:
                            logger.error(f"디렉토리 삭제 실패 {subdir}: {str(e)}")
            
        except Exception as e:
            logger.error(f"빈 디렉토리 정리 중 오류: {str(e)}")
        
        return cleaned_count
    
    def find_duplicate_files(self, directory_name: str = 'images') -> List[Dict[str, any]]:
        """중복 파일 찾기 (해시 기반)"""
        if directory_name not in self.directories:
            raise ValueError(f"알 수 없는 디렉토리: {directory_name}")
        
        directory = self.directories[directory_name]
        if not directory.exists():
            return []
        
        import hashlib
        
        file_hashes = {}
        duplicates = []
        
        try:
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    try:
                        # 파일 해시 계산
                        with open(file_path, 'rb') as f:
                            file_hash = hashlib.md5(f.read()).hexdigest()
                        
                        if file_hash in file_hashes:
                            # 중복 파일 발견
                            duplicates.append({
                                'hash': file_hash,
                                'original_file': str(file_hashes[file_hash]),
                                'duplicate_file': str(file_path),
                                'size_bytes': file_path.stat().st_size
                            })
                        else:
                            file_hashes[file_hash] = file_path
                    
                    except Exception as e:
                        logger.error(f"파일 해시 계산 실패 {file_path}: {str(e)}")
            
        except Exception as e:
            logger.error(f"중복 파일 검색 중 오류: {str(e)}")
        
        return duplicates
    
    def create_backup(self, source_directory: str, backup_name: Optional[str] = None) -> str:
        """디렉토리 백업 생성"""
        if source_directory not in self.directories:
            raise ValueError(f"알 수 없는 디렉토리: {source_directory}")
        
        source_path = self.directories[source_directory]
        if not source_path.exists():
            raise FileNotFoundError(f"소스 디렉토리가 존재하지 않습니다: {source_path}")
        
        if not backup_name:
            backup_name = f"{source_directory}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = self.directories['backups'] / f"{backup_name}.tar.gz"
        
        try:
            import tarfile
            
            with tarfile.open(backup_path, 'w:gz') as tar:
                tar.add(source_path, arcname=source_directory)
            
            logger.info(f"백업 생성 완료: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"백업 생성 실패: {str(e)}")
            raise
    
    def restore_backup(self, backup_filename: str, target_directory: str) -> bool:
        """백업에서 복원"""
        if target_directory not in self.directories:
            raise ValueError(f"알 수 없는 디렉토리: {target_directory}")
        
        backup_path = self.directories['backups'] / backup_filename
        if not backup_path.exists():
            raise FileNotFoundError(f"백업 파일이 존재하지 않습니다: {backup_path}")
        
        target_path = self.directories[target_directory]
        
        try:
            import tarfile
            
            # 기존 디렉토리 백업
            if target_path.exists():
                temp_backup = self.create_backup(target_directory, f"{target_directory}_pre_restore")
                logger.info(f"기존 데이터 백업: {temp_backup}")
            
            # 복원 수행
            with tarfile.open(backup_path, 'r:gz') as tar:
                tar.extractall(self.upload_dir)
            
            logger.info(f"백업 복원 완료: {backup_path} -> {target_path}")
            return True
            
        except Exception as e:
            logger.error(f"백업 복원 실패: {str(e)}")
            return False
    
    def get_file_info(self, file_path: str) -> Dict[str, any]:
        """파일 상세 정보 조회"""
        full_path = Path(file_path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"파일이 존재하지 않습니다: {file_path}")
        
        stat = full_path.stat()
        
        file_info = {
            'path': str(full_path),
            'name': full_path.name,
            'size_bytes': stat.st_size,
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'accessed': datetime.fromtimestamp(stat.st_atime).isoformat(),
            'permissions': oct(stat.st_mode)[-3:],
            'is_readable': os.access(full_path, os.R_OK),
            'is_writable': os.access(full_path, os.W_OK),
            'is_executable': os.access(full_path, os.X_OK)
        }
        
        # MIME 타입 추가
        try:
            import magic
            file_info['mime_type'] = magic.from_file(str(full_path), mime=True)
        except Exception:
            file_info['mime_type'] = 'unknown'
        
        # 파일 해시 추가
        try:
            import hashlib
            with open(full_path, 'rb') as f:
                content = f.read()
                file_info['md5_hash'] = hashlib.md5(content).hexdigest()
                file_info['sha256_hash'] = hashlib.sha256(content).hexdigest()
        except Exception as e:
            file_info['hash_error'] = str(e)
        
        return file_info
    
    def optimize_storage(self) -> Dict[str, any]:
        """스토리지 최적화 수행"""
        optimization_result = {
            'actions_performed': [],
            'space_freed_bytes': 0,
            'files_removed': 0,
            'directories_removed': 0
        }
        
        # 1. 임시 파일 정리 (7일 이상)
        temp_cleaned = self.cleanup_old_files(7, 'temp')
        if temp_cleaned > 0:
            optimization_result['actions_performed'].append(f"임시 파일 {temp_cleaned}개 정리")
            optimization_result['files_removed'] += temp_cleaned
        
        # 2. 빈 디렉토리 정리
        empty_dirs_cleaned = self.cleanup_empty_directories()
        if empty_dirs_cleaned > 0:
            optimization_result['actions_performed'].append(f"빈 디렉토리 {empty_dirs_cleaned}개 정리")
            optimization_result['directories_removed'] += empty_dirs_cleaned
        
        # 3. 중복 파일 찾기 (정리는 수동으로)
        duplicates = self.find_duplicate_files('images')
        if duplicates:
            total_duplicate_size = sum(dup['size_bytes'] for dup in duplicates)
            optimization_result['actions_performed'].append(
                f"중복 파일 {len(duplicates)}개 발견 (총 {round(total_duplicate_size / (1024*1024), 2)}MB)"
            )
            optimization_result['duplicate_files'] = duplicates
        
        # 4. 오래된 백업 정리 (30일 이상)
        backup_cleaned = self.cleanup_old_files(30, 'backups')
        if backup_cleaned > 0:
            optimization_result['actions_performed'].append(f"오래된 백업 {backup_cleaned}개 정리")
            optimization_result['files_removed'] += backup_cleaned
        
        return optimization_result


# 전역 스토리지 서비스 인스턴스
storage_service = StorageService()