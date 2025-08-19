#!/usr/bin/env python3
"""
테스트 실행 스크립트
"""
import subprocess
import sys
import os


def run_tests():
    """테스트 실행"""
    # 환경 변수 설정
    os.environ["TESTING"] = "1"
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"
    
    # pytest 실행
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--cov=app",
        "--cov-report=term-missing"
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("✅ 모든 테스트가 성공적으로 완료되었습니다!")
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"❌ 테스트 실행 중 오류가 발생했습니다: {e}")
        return e.returncode


def run_unit_tests():
    """단위 테스트만 실행"""
    os.environ["TESTING"] = "1"
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_services/",
        "tests/test_models/",
        "-v",
        "-m", "unit"
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("✅ 단위 테스트가 성공적으로 완료되었습니다!")
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"❌ 단위 테스트 실행 중 오류가 발생했습니다: {e}")
        return e.returncode


def run_api_tests():
    """API 테스트만 실행"""
    os.environ["TESTING"] = "1"
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_api/",
        "-v",
        "-m", "api"
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("✅ API 테스트가 성공적으로 완료되었습니다!")
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"❌ API 테스트 실행 중 오류가 발생했습니다: {e}")
        return e.returncode


if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
        if test_type == "unit":
            sys.exit(run_unit_tests())
        elif test_type == "api":
            sys.exit(run_api_tests())
        else:
            print("사용법: python run_tests.py [unit|api]")
            sys.exit(1)
    else:
        sys.exit(run_tests())