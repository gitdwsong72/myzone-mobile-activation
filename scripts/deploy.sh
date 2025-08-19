#!/bin/bash

# 배포 스크립트
# 환경별로 MyZone 애플리케이션을 배포합니다.

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 함수 정의
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 사용법 출력
usage() {
    echo "사용법: $0 [환경] [옵션]"
    echo ""
    echo "환경:"
    echo "  staging     스테이징 환경에 배포"
    echo "  production  프로덕션 환경에 배포"
    echo ""
    echo "옵션:"
    echo "  --no-build  이미지 빌드 건너뛰기"
    echo "  --no-backup 배포 전 백업 건너뛰기"
    echo "  --force     확인 없이 강제 배포"
    echo ""
    exit 1
}

# 파라미터 파싱
ENVIRONMENT=""
NO_BUILD=false
NO_BACKUP=false
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        staging|production)
            ENVIRONMENT="$1"
            shift
            ;;
        --no-build)
            NO_BUILD=true
            shift
            ;;
        --no-backup)
            NO_BACKUP=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            log_error "알 수 없는 옵션: $1"
            usage
            ;;
    esac
done

# 환경 검증
if [[ -z "$ENVIRONMENT" ]]; then
    log_error "환경을 지정해주세요."
    usage
fi

# 환경별 설정
case $ENVIRONMENT in
    staging)
        COMPOSE_FILE="docker-compose.staging.yml"
        ENV_FILE=".env.staging"
        ;;
    production)
        COMPOSE_FILE="docker-compose.prod.yml"
        ENV_FILE=".env.production"
        ;;
esac

log_info "MyZone $ENVIRONMENT 환경 배포 시작"

# 환경 파일 확인
if [[ ! -f "$ENV_FILE" ]]; then
    log_error "환경 파일을 찾을 수 없습니다: $ENV_FILE"
    exit 1
fi

# 시크릿 파일 확인 (프로덕션만)
if [[ "$ENVIRONMENT" == "production" && ! -f "secrets/.env.secrets" ]]; then
    log_warning "시크릿 파일이 없습니다. 생성하시겠습니까? (y/n)"
    if [[ "$FORCE" == "true" ]] || read -r -p "" response && [[ "$response" =~ ^[Yy]$ ]]; then
        ./scripts/generate-secrets.sh
    else
        log_error "시크릿 파일이 필요합니다."
        exit 1
    fi
fi

# 배포 확인
if [[ "$FORCE" != "true" ]]; then
    log_warning "$ENVIRONMENT 환경에 배포하시겠습니까? (y/n)"
    read -r -p "" response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        log_info "배포가 취소되었습니다."
        exit 0
    fi
fi

# 환경 변수 로드
log_info "환경 변수 로드 중..."
set -a
source "$ENV_FILE"
if [[ -f "secrets/.env.secrets" ]]; then
    source "secrets/.env.secrets"
fi
set +a

# 백업 (프로덕션만)
if [[ "$ENVIRONMENT" == "production" && "$NO_BACKUP" != "true" ]]; then
    log_info "배포 전 백업 수행 중..."
    if docker-compose -f "$COMPOSE_FILE" exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" > "backups/pre-deploy-$(date +%Y%m%d_%H%M%S).sql"; then
        log_success "백업 완료"
    else
        log_warning "백업 실패 - 계속 진행하시겠습니까? (y/n)"
        if [[ "$FORCE" != "true" ]]; then
            read -r -p "" response
            if [[ ! "$response" =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi
fi

# 이미지 빌드
if [[ "$NO_BUILD" != "true" ]]; then
    log_info "Docker 이미지 빌드 중..."
    docker-compose -f "$COMPOSE_FILE" build --no-cache
    log_success "이미지 빌드 완료"
fi

# 기존 컨테이너 중지
log_info "기존 컨테이너 중지 중..."
docker-compose -f "$COMPOSE_FILE" down

# 새 컨테이너 시작
log_info "새 컨테이너 시작 중..."
docker-compose -f "$COMPOSE_FILE" up -d

# 헬스체크 대기
log_info "서비스 헬스체크 대기 중..."
sleep 30

# 헬스체크 수행
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health || echo "000")
FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/health || echo "000")

if [[ "$BACKEND_HEALTH" == "200" && "$FRONTEND_HEALTH" == "200" ]]; then
    log_success "헬스체크 통과"
else
    log_error "헬스체크 실패 (Backend: $BACKEND_HEALTH, Frontend: $FRONTEND_HEALTH)"
    log_info "로그 확인:"
    docker-compose -f "$COMPOSE_FILE" logs --tail=50
    exit 1
fi

# 데이터베이스 마이그레이션 (필요한 경우)
log_info "데이터베이스 마이그레이션 확인 중..."
docker-compose -f "$COMPOSE_FILE" exec -T backend alembic upgrade head

# 배포 완료
log_success "$ENVIRONMENT 환경 배포 완료!"

# 서비스 상태 출력
log_info "서비스 상태:"
docker-compose -f "$COMPOSE_FILE" ps

# 배포 정보 출력
echo ""
log_info "배포 정보:"
echo "  환경: $ENVIRONMENT"
echo "  시간: $(date)"
echo "  커밋: $(git rev-parse --short HEAD 2>/dev/null || echo 'N/A')"
echo "  브랜치: $(git branch --show-current 2>/dev/null || echo 'N/A')"

# 슬랙 알림 (웹훅 URL이 설정된 경우)
if [[ ! -z "${SLACK_WEBHOOK_URL}" ]]; then
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"🚀 MyZone $ENVIRONMENT 배포 완료\\n📅 시간: $(date)\\n🔗 커밋: $(git rev-parse --short HEAD 2>/dev/null || echo 'N/A')\"}" \
        "${SLACK_WEBHOOK_URL}" || true
fi

log_success "배포 프로세스 완료!"