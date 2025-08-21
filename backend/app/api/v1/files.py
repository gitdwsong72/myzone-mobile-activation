"""
파일 업로드 API 엔드포인트
"""

import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.core.file_permissions import require_file_delete_permission, require_file_write_permission
from app.models.admin import Admin
from app.services.file_security_service import file_security_service
from app.services.file_service import file_service

router = APIRouter()


@router.post("/upload/device-image/{device_id}")
async def upload_device_image(
    device_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
) -> Dict[str, Any]:
    """
    단말기 이미지 업로드

    - **device_id**: 단말기 ID
    - **file**: 업로드할 이미지 파일
    """
    try:
        # 단말기 존재 확인
        from app.services.device_service import device_service

        device = await device_service.get_device(db, device_id)
        if not device:
            raise HTTPException(status_code=404, detail="단말기를 찾을 수 없습니다.")

        # 이미지 업로드 및 최적화
        uploaded_urls = await file_service.upload_device_image(file, device_id)

        # 단말기 이미지 URL 업데이트
        await device_service.update_device_images(db, device_id, uploaded_urls)

        return {"message": "이미지가 성공적으로 업로드되었습니다.", "device_id": device_id, "images": uploaded_urls}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이미지 업로드 중 오류가 발생했습니다: {str(e)}")


@router.post("/upload/multiple")
async def upload_multiple_files(
    files: List[UploadFile] = File(...), current_admin: Admin = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    여러 파일 동시 업로드

    - **files**: 업로드할 파일 목록
    """
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="한 번에 최대 10개의 파일만 업로드할 수 있습니다.")

    uploaded_files = []
    failed_files = []

    for file in files:
        try:
            # 파일 유효성 검사
            await file_service.validate_file(file)

            # 파일 내용 읽기
            file_content = await file.read()
            await file.seek(0)

            # 이미지 최적화
            variants = file_service.create_image_variants(file_content)

            # 업로드
            file_urls = {}
            for size_name, image_data in variants.items():
                filename = file_service.generate_filename(file.filename, size_name)

                if file_service.s3_client:
                    url = await file_service.upload_to_s3(image_data, filename)
                else:
                    url = await file_service.save_local_file(image_data, filename)

                file_urls[size_name] = url

            uploaded_files.append({"filename": file.filename, "urls": file_urls})

        except Exception as e:
            failed_files.append({"filename": file.filename, "error": str(e)})

    return {
        "message": f"{len(uploaded_files)}개 파일이 성공적으로 업로드되었습니다.",
        "uploaded": uploaded_files,
        "failed": failed_files,
    }


@router.delete("/delete/{filename}")
async def delete_file(
    filename: str, current_admin: Admin = Depends(get_current_admin), _: bool = Depends(lambda: require_file_delete_permission)
) -> Dict[str, str]:
    """
    파일 삭제

    - **filename**: 삭제할 파일명
    """
    try:
        success = await file_service.delete_file(filename)

        if success:
            return {"message": "파일이 성공적으로 삭제되었습니다."}
        else:
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 삭제 중 오류가 발생했습니다: {str(e)}")


@router.post("/cleanup")
async def cleanup_temp_files(
    background_tasks: BackgroundTasks, current_admin: Admin = Depends(get_current_admin)
) -> Dict[str, str]:
    """
    임시 파일 정리 (백그라운드 작업)
    """
    background_tasks.add_task(file_service.cleanup_temp_files)

    return {"message": "임시 파일 정리 작업이 시작되었습니다."}


@router.get("/storage-info")
async def get_storage_info(current_admin: Admin = Depends(get_current_admin)) -> Dict[str, Any]:
    """
    스토리지 정보 조회
    """
    import os

    from app.core.config import settings

    storage_info = {
        "storage_type": "S3" if file_service.s3_client else "Local",
        "upload_dir": settings.UPLOAD_DIR,
        "max_file_size": settings.MAX_FILE_SIZE,
        "allowed_types": list(file_service.ALLOWED_IMAGE_TYPES),
        "image_sizes": file_service.IMAGE_SIZES,
    }

    # 로컬 스토리지인 경우 디스크 사용량 정보 추가
    if not file_service.s3_client:
        try:
            upload_path = os.path.join(settings.UPLOAD_DIR, "images")
            if os.path.exists(upload_path):
                total_size = 0
                file_count = 0

                for root, dirs, files in os.walk(upload_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        total_size += os.path.getsize(file_path)
                        file_count += 1

                storage_info.update(
                    {
                        "local_storage": {
                            "total_size_bytes": total_size,
                            "total_size_mb": round(total_size / (1024 * 1024), 2),
                            "file_count": file_count,
                        }
                    }
                )
        except Exception as e:
            storage_info["local_storage_error"] = str(e)

    return storage_info


@router.get("/quarantine")
async def list_quarantine_files(current_admin: Admin = Depends(get_current_admin)) -> Dict[str, Any]:
    """격리된 파일 목록 조회 (관리자 전용)"""
    if current_admin.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="격리 파일 접근 권한이 없습니다.")

    import os

    from app.core.config import settings

    quarantine_dir = os.path.join(settings.UPLOAD_DIR, "quarantine")
    quarantine_files = []

    if os.path.exists(quarantine_dir):
        # 격리 로그 읽기
        log_path = os.path.join(quarantine_dir, "quarantine.log")
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as log_file:
                for line in log_file:
                    parts = line.strip().split(",")
                    if len(parts) >= 4:
                        quarantine_files.append(
                            {
                                "timestamp": int(parts[0]),
                                "quarantine_filename": parts[1],
                                "original_filename": parts[2],
                                "reason": parts[3],
                            }
                        )

    return {
        "quarantine_files": sorted(quarantine_files, key=lambda x: x["timestamp"], reverse=True),
        "total_count": len(quarantine_files),
    }


@router.delete("/quarantine/{quarantine_filename}")
async def delete_quarantine_file(
    quarantine_filename: str, current_admin: Admin = Depends(get_current_admin)
) -> Dict[str, str]:
    """격리된 파일 삭제 (관리자 전용)"""
    if current_admin.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="격리 파일 삭제 권한이 없습니다.")

    import os

    from app.core.config import settings

    quarantine_dir = os.path.join(settings.UPLOAD_DIR, "quarantine")
    file_path = os.path.join(quarantine_dir, quarantine_filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="격리된 파일을 찾을 수 없습니다.")

    try:
        os.remove(file_path)
        return {"message": "격리된 파일이 삭제되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 삭제 중 오류: {str(e)}")


@router.post("/quarantine/cleanup")
async def cleanup_quarantine_files(
    background_tasks: BackgroundTasks, days_old: int = 30, current_admin: Admin = Depends(get_current_admin)
) -> Dict[str, str]:
    """오래된 격리 파일 정리 (관리자 전용)"""
    if current_admin.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="격리 파일 정리 권한이 없습니다.")

    background_tasks.add_task(file_security_service.cleanup_quarantine_files, days_old)

    return {"message": f"{days_old}일 이상 된 격리 파일 정리 작업이 시작되었습니다."}


@router.get("/security-scan/{filename}")
async def rescan_file_security(filename: str, current_admin: Admin = Depends(get_current_admin)) -> Dict[str, Any]:
    """파일 보안 재검사 (관리자 전용)"""
    import os

    from app.core.config import settings

    file_path = os.path.join(settings.UPLOAD_DIR, "images", filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")

    try:
        # 파일 내용 읽기
        with open(file_path, "rb") as f:
            content = f.read()

        # 가짜 UploadFile 객체 생성
        class FakeUploadFile:
            def __init__(self, filename: str, content: bytes):
                self.filename = filename
                self.content_type = None
                self._content = content
                self._position = 0

            async def read(self):
                return self._content

            async def seek(self, position: int):
                self._position = position

        fake_file = FakeUploadFile(filename, content)

        # 보안 검사 수행
        scan_result = await file_security_service.validate_file_security(fake_file)

        return {"filename": filename, "scan_timestamp": int(time.time()), "scan_result": scan_result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 스캔 중 오류: {str(e)}")


@router.get("/permissions/{file_path:path}")
async def check_file_permissions(file_path: str, current_admin: Admin = Depends(get_current_admin)) -> Dict[str, Any]:
    """파일 접근 권한 확인 (관리자 전용)"""
    from app.core.file_permissions import file_permission_manager

    # 다양한 역할에 대한 권한 확인
    roles = ["user", "manager", "admin"]
    permissions_by_role = {}

    for role in roles:
        file_category = file_permission_manager.get_file_category(f"/{file_path}")
        if file_category:
            permissions = file_security_service.get_file_permissions(role, file_category)
            permissions_by_role[role] = permissions

    return {"file_path": file_path, "file_category": file_category, "permissions_by_role": permissions_by_role}


@router.get("/storage/usage")
async def get_storage_usage(current_admin: Admin = Depends(get_current_admin)) -> Dict[str, Any]:
    """스토리지 사용량 조회 (관리자 전용)"""
    from app.services.storage_service import storage_service

    return storage_service.get_storage_usage()


@router.post("/storage/optimize")
async def optimize_storage(
    background_tasks: BackgroundTasks, current_admin: Admin = Depends(get_current_admin)
) -> Dict[str, str]:
    """스토리지 최적화 수행 (관리자 전용)"""
    if current_admin.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="스토리지 최적화 권한이 없습니다.")

    from app.services.storage_service import storage_service

    background_tasks.add_task(storage_service.optimize_storage)

    return {"message": "스토리지 최적화 작업이 시작되었습니다."}


@router.get("/storage/duplicates/{directory}")
async def find_duplicate_files(directory: str, current_admin: Admin = Depends(get_current_admin)) -> Dict[str, Any]:
    """중복 파일 찾기 (관리자 전용)"""
    from app.services.storage_service import storage_service

    try:
        duplicates = storage_service.find_duplicate_files(directory)
        return {"directory": directory, "duplicate_count": len(duplicates), "duplicates": duplicates}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/storage/backup/{directory}")
async def create_backup(
    directory: str, backup_name: Optional[str] = None, current_admin: Admin = Depends(get_current_admin)
) -> Dict[str, str]:
    """디렉토리 백업 생성 (관리자 전용)"""
    if current_admin.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="백업 생성 권한이 없습니다.")

    from app.services.storage_service import storage_service

    try:
        backup_path = storage_service.create_backup(directory, backup_name)
        return {"message": "백업이 성공적으로 생성되었습니다.", "backup_path": backup_path}
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"백업 생성 중 오류: {str(e)}")


@router.get("/info/{file_path:path}")
async def get_file_info(file_path: str, current_admin: Admin = Depends(get_current_admin)) -> Dict[str, Any]:
    """파일 상세 정보 조회 (관리자 전용)"""
    from app.services.storage_service import storage_service

    try:
        return storage_service.get_file_info(file_path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 정보 조회 중 오류: {str(e)}")
