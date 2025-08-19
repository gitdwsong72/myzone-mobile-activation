#!/usr/bin/env python3
"""
데이터베이스 시드 데이터 생성 스크립트
사용법: python scripts/seed_db.py
"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.db.seed_data import run_seed_data

if __name__ == "__main__":
    run_seed_data()