#!/bin/bash

# MyZone 전체 테스트 실행 스크립트

set -e

echo "🚀 MyZone 전체 테스트 스위트 실행 시작"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 함수 정의
print_step() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 환경 변수 설정
export TESTING=1
export DATABASE_URL="sqlite:///./test.db"
export REDIS_URL="redis://localhost:6379"

# 1. 백엔드 단위 테스트
print_step "백엔드 단위 테스트 실행 중..."
cd backend

if python -m pytest tests/test_services/ tests/test_models/ -v --cov=app --cov-report=term-missing --cov-report=html:htmlcov; then
    print_success "백엔드 단위 테스트 완료"
else
    print_error "백엔드 단위 테스트 실패"
    exit 1
fi

# 2. 백엔드 API 테스트
print_step "백엔드 API 테스트 실행 중..."
if python -m pytest tests/test_api/ -v --cov=app --cov-report=term-missing --cov-append; then
    print_success "백엔드 API 테스트 완료"
else
    print_error "백엔드 API 테스트 실패"
    exit 1
fi

# 3. 백엔드 통합 테스트
print_step "백엔드 통합 테스트 실행 중..."
if python -m pytest tests/test_integration/ -v --cov=app --cov-report=term-missing --cov-append; then
    print_success "백엔드 통합 테스트 완료"
else
    print_error "백엔드 통합 테스트 실패"
    exit 1
fi

cd ..

# 4. 프론트엔드 테스트
print_step "프론트엔드 테스트 실행 중..."
cd frontend

if npm test -- --coverage --watchAll=false; then
    print_success "프론트엔드 테스트 완료"
else
    print_error "프론트엔드 테스트 실패"
    exit 1
fi

cd ..

# 5. E2E 테스트 (선택적)
if [ "$1" = "--e2e" ] || [ "$1" = "--all" ]; then
    print_step "E2E 테스트 실행 중..."
    
    # 백엔드 서버 시작 (백그라운드)
    cd backend
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    cd ..
    
    # 프론트엔드 서버 시작 (백그라운드)
    cd frontend
    npm start &
    FRONTEND_PID=$!
    cd ..
    
    # 서버 시작 대기
    print_step "서버 시작 대기 중..."
    sleep 30
    
    # E2E 테스트 실행
    if npx playwright test; then
        print_success "E2E 테스트 완료"
    else
        print_error "E2E 테스트 실패"
        # 서버 프로세스 종료
        kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
        exit 1
    fi
    
    # 서버 프로세스 종료
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
fi

# 6. 성능 테스트 (선택적)
if [ "$1" = "--performance" ] || [ "$1" = "--all" ]; then
    print_step "성능 테스트 실행 중..."
    
    # 백엔드 서버 시작 (백그라운드)
    cd backend
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    cd ..
    
    # 프론트엔드 서버 시작 (백그라운드)
    cd frontend
    npm start &
    FRONTEND_PID=$!
    cd ..
    
    # 서버 시작 대기
    print_step "서버 시작 대기 중..."
    sleep 30
    
    # 성능 테스트 실행
    if npx playwright test e2e/tests/performance.spec.ts; then
        print_success "성능 테스트 완료"
    else
        print_warning "성능 테스트에서 일부 이슈 발견 (계속 진행)"
    fi
    
    # 서버 프로세스 종료
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
fi

# 7. 코드 품질 검사 (선택적)
if [ "$1" = "--quality" ] || [ "$1" = "--all" ]; then
    print_step "코드 품질 검사 실행 중..."
    
    # Python 코드 품질 검사
    cd backend
    if command -v black &> /dev/null; then
        print_step "Python 코드 포맷팅 검사..."
        black --check . || print_warning "Python 코드 포맷팅 이슈 발견"
    fi
    
    if command -v flake8 &> /dev/null; then
        print_step "Python 린팅 검사..."
        flake8 . || print_warning "Python 린팅 이슈 발견"
    fi
    
    if command -v mypy &> /dev/null; then
        print_step "Python 타입 검사..."
        mypy app/ || print_warning "Python 타입 이슈 발견"
    fi
    cd ..
    
    # TypeScript 코드 품질 검사
    cd frontend
    print_step "TypeScript 린팅 검사..."
    npm run lint || print_warning "TypeScript 린팅 이슈 발견"
    
    print_step "TypeScript 타입 검사..."
    npx tsc --noEmit || print_warning "TypeScript 타입 이슈 발견"
    cd ..
fi

# 테스트 결과 요약
print_step "테스트 결과 요약"
echo "=================================="
print_success "백엔드 단위 테스트: 통과"
print_success "백엔드 API 테스트: 통과"
print_success "백엔드 통합 테스트: 통과"
print_success "프론트엔드 테스트: 통과"

if [ "$1" = "--e2e" ] || [ "$1" = "--all" ]; then
    print_success "E2E 테스트: 통과"
fi

if [ "$1" = "--performance" ] || [ "$1" = "--all" ]; then
    print_success "성능 테스트: 완료"
fi

if [ "$1" = "--quality" ] || [ "$1" = "--all" ]; then
    print_success "코드 품질 검사: 완료"
fi

echo "=================================="
print_success "🎉 모든 테스트가 성공적으로 완료되었습니다!"

# 커버리지 리포트 위치 안내
echo ""
print_step "📊 테스트 커버리지 리포트"
echo "백엔드 커버리지: backend/htmlcov/index.html"
echo "프론트엔드 커버리지: frontend/coverage/lcov-report/index.html"

if [ "$1" = "--e2e" ] || [ "$1" = "--all" ]; then
    echo "E2E 테스트 리포트: playwright-report/index.html"
fi

echo ""
print_success "테스트 스위트 실행 완료! 🚀"