"""
파일 업로드 및 이미지 최적화 서비스
"""

import hashlib
import os
import time
import uuid
from io import BytesIO
from typing import List, Optional, Tuple

import boto3
import magic
from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile
from PIL import Image, ImageOps
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.services.file_security_service import file_security_service


class FileService:
    """파일 업로드 및 관리 서비스"""

    # 허용된 이미지 MIME 타입
    ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"}

    # 최대 파일 크기 (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024

    # 이미지 크기 설정
    IMAGE_SIZES = {"thumbnail": (150, 150), "small": (300, 300), "medium": (600, 600), "large": (1200, 1200)}

    def __init__(self):
        self.s3_client = None
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION,
            )

    async def validate_file(self, file: UploadFile) -> bool:
        """파일 유효성 및 보안 검사"""
        # 기본 파일 크기 검사
        if file.size and file.size > self.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, detail=f"파일 크기가 너무 큽니다. 최대 {self.MAX_FILE_SIZE // (1024*1024)}MB까지 허용됩니다."
            )

        # 파일 내용 읽기
        content = await file.read()
        await file.seek(0)  # 파일 포인터 리셋

        # 기본 MIME 타입 검사
        mime_type = magic.from_buffer(content, mime=True)
        if mime_type not in self.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400, detail=f"지원하지 않는 파일 형식입니다. 허용된 형식: {', '.join(self.ALLOWED_IMAGE_TYPES)}"
            )

        # 보안 검증 수행
        security_result = await file_security_service.validate_file_security(file)

        if not security_result["is_safe"]:
            # 위험한 파일을 격리
            await file_security_service.quarantine_file(content, file.filename, "; ".join(security_result["issues"]))

            raise HTTPException(status_code=400, detail=f"파일 보안 검사 실패: {'; '.join(security_result['issues'])}")

        return True

    def generate_filename(self, original_filename: str, prefix: str = "") -> str:
        """고유한 파일명 생성"""
        file_extension = os.path.splitext(original_filename)[1].lower()
        unique_id = str(uuid.uuid4())

        if prefix:
            return f"{prefix}_{unique_id}{file_extension}"
        return f"{unique_id}{file_extension}"

    def optimize_image(self, image_data: bytes, size: Tuple[int, int], quality: int = 85) -> bytes:
        """이미지 최적화 및 리사이징"""
        try:
            # PIL Image 객체 생성
            image = Image.open(BytesIO(image_data))

            # EXIF 정보 기반 회전 처리
            image = ImageOps.exif_transpose(image)

            # RGBA 모드를 RGB로 변환 (WebP 호환성)
            if image.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                background.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
                image = background

            # 이미지 리사이징 (비율 유지)
            image.thumbnail(size, Image.Resampling.LANCZOS)

            # WebP 형식으로 변환
            output = BytesIO()
            image.save(output, format="WebP", quality=quality, optimize=True)

            return output.getvalue()

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"이미지 처리 중 오류가 발생했습니다: {str(e)}")

    def create_image_variants(self, image_data: bytes) -> dict:
        """다양한 크기의 이미지 변형 생성"""
        variants = {}

        for size_name, dimensions in self.IMAGE_SIZES.items():
            try:
                optimized_data = self.optimize_image(image_data, dimensions)
                variants[size_name] = optimized_data
            except Exception as e:
                print(f"이미지 변형 생성 실패 ({size_name}): {str(e)}")
                continue

        return variants

    async def upload_to_s3(self, file_data: bytes, filename: str, content_type: str = "image/webp") -> str:
        """S3에 파일 업로드"""
        if not self.s3_client:
            raise HTTPException(status_code=500, detail="S3 설정이 올바르지 않습니다.")

        try:
            self.s3_client.put_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=filename,
                Body=file_data,
                ContentType=content_type,
                CacheControl="max-age=31536000",  # 1년 캐시
                Metadata={"uploaded_at": str(int(time.time())), "file_hash": hashlib.md5(file_data).hexdigest()},
            )

            # CDN URL 반환
            if settings.CLOUDFRONT_DOMAIN:
                return f"https://{settings.CLOUDFRONT_DOMAIN}/{filename}"
            else:
                return f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{filename}"

        except ClientError as e:
            raise HTTPException(status_code=500, detail=f"파일 업로드 실패: {str(e)}")

    async def save_local_file(self, file_data: bytes, filename: str) -> str:
        """로컬 파일 시스템에 저장"""
        upload_dir = os.path.join(settings.UPLOAD_DIR, "images")
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, filename)

        try:
            with open(file_path, "wb") as f:
                f.write(file_data)

            return f"/uploads/images/{filename}"

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"파일 저장 실패: {str(e)}")

    async def upload_device_image(self, file: UploadFile, device_id: int) -> dict:
        """단말기 이미지 업로드 및 최적화"""
        # 파일 유효성 검사
        await self.validate_file(file)

        # 파일 내용 읽기
        file_content = await file.read()

        # 이미지 변형 생성
        variants = self.create_image_variants(file_content)

        # 업로드된 이미지 URL 저장
        uploaded_urls = {}

        for size_name, image_data in variants.items():
            filename = self.generate_filename(file.filename, f"device_{device_id}_{size_name}")

            # S3 또는 로컬 저장소에 업로드
            if self.s3_client:
                url = await self.upload_to_s3(image_data, filename)
            else:
                url = await self.save_local_file(image_data, filename)

            uploaded_urls[size_name] = url

        return uploaded_urls

    async def delete_file(self, filename: str) -> bool:
        """파일 삭제"""
        try:
            if self.s3_client:
                # S3에서 삭제
                self.s3_client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=filename)
            else:
                # 로컬 파일 삭제
                file_path = os.path.join(settings.UPLOAD_DIR, "images", filename)
                if os.path.exists(file_path):
                    os.remove(file_path)

            return True

        except Exception as e:
            print(f"파일 삭제 실패: {str(e)}")
            return False

    def get_file_hash(self, file_data: bytes) -> str:
        """파일 해시 생성 (중복 검사용)"""
        return hashlib.md5(file_data).hexdigest()

    async def cleanup_temp_files(self) -> int:
        """임시 파일 정리"""
        cleaned_count = 0
        temp_dir = os.path.join(settings.UPLOAD_DIR, "temp")

        if not os.path.exists(temp_dir):
            return cleaned_count

        import time

        current_time = time.time()

        try:
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)

                # 1시간 이상 된 임시 파일 삭제
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getctime(file_path)
                    if file_age > 3600:  # 1시간
                        os.remove(file_path)
                        cleaned_count += 1

        except Exception as e:
            print(f"임시 파일 정리 중 오류: {str(e)}")

        return cleaned_count


# 전역 파일 서비스 인스턴스
file_service = FileService()
