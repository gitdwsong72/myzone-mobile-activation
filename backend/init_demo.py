#!/usr/bin/env python3
"""
데모 환경 초기화 스크립트
SQLite 데이터베이스 생성 및 시드 데이터 삽입
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 환경 변수 설정
os.environ["DATABASE_URL"] = "sqlite:///./demo.db"
os.environ["ENVIRONMENT"] = "demo"
os.environ["SECRET_KEY"] = "demo-secret-key-for-initialization"

from app.core.database import engine
from app.models.base import Base
from app.models import *  # 모든 모델 import
from app.db.seed_data import create_demo_data

def init_demo_database():
    """데모 데이터베이스 초기화"""
    print("🚀 데모 데이터베이스 초기화 시작...")
    
    try:
        # 테이블 생성
        print("📋 테이블 생성 중...")
        Base.metadata.create_all(bind=engine)
        print("✅ 테이블 생성 완료")
        
        # 시드 데이터 생성
        print("🌱 시드 데이터 생성 중...")
        create_demo_data()
        print("✅ 시드 데이터 생성 완료")
        
        print("🎉 데모 데이터베이스 초기화 완료!")
        print("📍 데이터베이스 파일: demo.db")
        
    except Exception as e:
        print(f"❌ 초기화 실패: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_demo_database()