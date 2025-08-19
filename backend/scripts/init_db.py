#!/usr/bin/env python3
"""
데이터베이스 초기화 스크립트
- 테이블 생성 (마이그레이션 실행)
- 시드 데이터 삽입
"""
import sys
import os
import subprocess

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.core.database import engine, Base
from app.db.seed_data import run_seed_data
from app.models import *  # 모든 모델 임포트


def create_tables():
    """테이블 생성"""
    print("📋 데이터베이스 테이블 생성 중...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ 테이블 생성 완료")
        return True
    except Exception as e:
        print(f"❌ 테이블 생성 실패: {e}")
        return False


def run_migrations():
    """Alembic 마이그레이션 실행"""
    print("🔄 Alembic 마이그레이션 실행 중...")
    try:
        # Alembic 마이그레이션 실행
        result = subprocess.run(
            ["python", "-m", "alembic", "upgrade", "head"],
            cwd=os.path.dirname(os.path.dirname(__file__)),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ 마이그레이션 완료")
            return True
        else:
            print(f"❌ 마이그레이션 실패: {result.stderr}")
            # 마이그레이션이 실패하면 직접 테이블 생성 시도
            return create_tables()
    except Exception as e:
        print(f"❌ 마이그레이션 실행 중 오류: {e}")
        # 마이그레이션이 실패하면 직접 테이블 생성 시도
        return create_tables()


def main():
    """메인 실행 함수"""
    print("🚀 MyZone 데이터베이스 초기화 시작")
    print("=" * 50)
    
    # 1. 마이그레이션 실행 또는 테이블 생성
    if not run_migrations():
        print("❌ 데이터베이스 초기화 실패")
        sys.exit(1)
    
    # 2. 시드 데이터 생성
    print("\n" + "=" * 50)
    run_seed_data()
    
    print("\n" + "=" * 50)
    print("🎉 MyZone 데이터베이스 초기화 완료!")
    print("\n📊 생성된 데이터:")
    print("- 요금제: 6개 (5G, LTE, 데이터중심, 통화중심)")
    print("- 단말기: 5개 (삼성, 애플, LG)")
    print("- 전화번호: 14개 (일반, 연속, 특별)")
    print("- 관리자: 3개 (super_admin 1개, operator 2개)")
    print("\n🔐 관리자 계정:")
    print("- Username: admin, Password: admin123!")
    print("- Username: operator1, Password: operator123!")
    print("- Username: operator2, Password: operator123!")


if __name__ == "__main__":
    main()