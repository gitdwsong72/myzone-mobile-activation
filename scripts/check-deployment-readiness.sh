#!/bin/bash

# 배포 준비 상태 확인 스크립트
# CI/CD 파이프라인이 정상적으로 작동할 수 있는지 확인합니다.

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

# 전역 변수
REPO="gitdwsong72/myzone-mobile-activation"
OVERALL_STATUS="ready"

# GitHub CLI 확인
check_gh_cli() {
    log_info "GitHub CLI 상태 확인 중..."
    
    if ! command -v gh &> /dev/null; then
        log_error "GitHub CLI가 설치되지 않았습니다."
        OVERALL_STATUS="not_ready"
        return 1
    fi
    
    if ! gh auth status &> /dev/null; then
        log_error "GitHub CLI에 로그인되지 않았습니다."
        OVERALL_STATUS="not_ready"
        return 1
    fi
    
    log_success "GitHub CLI 준비 완료"
}

# GitHub Secrets 확인
check_github_secrets() {
    log_info "GitHub Secrets 확인 중..."
    
    local required_secrets=(
        "STAGING_SSH_KEY"
        "STAGING_USER"
        "STAGING_HOST"
        "STAGING_URL"
        "PRODUCTION_SSH_KEY"
        "PRODUCTION_USER"
        "PRODUCTION_HOST"
        "PRODUCTION_URL"
        "DATABASE_URL"
        "REDIS_URL"
        "SECRET_KEY"
        "JWT_SECRET_KEY"
        "ENCRYPTION_KEY"
        "POSTGRES_DB"
        "POSTGRES_USER"
        "POSTGRES_PASSWORD"
    )
    
    local missing_secrets=()
    local secret_list=$(gh secret list -R "$REPO" --json name -q '.[].name')
    
    for secret in "${required_secrets[@]}"; do
        if echo "$secret_list" | grep -q "^$secret$"; then
            log_success "$secret 설정됨"
        else
            log_error "$secret 누락됨"
            missing_secrets+=("$secret")
            OVERALL_STATUS="not_ready"
        fi
    done
    
    if [[ ${#missing_secrets[@]} -eq 0 ]]; then
        log_success "모든 필수 Secrets 설정 완료"
    else
        log_error "누락된 Secrets: ${missing_secrets[*]}"
    fi
}

# 워크플로우 파일 확인
check_workflow_files() {
    log_info "GitHub Actions 워크플로우 파일 확인 중..."
    
    local workflow_files=(
        ".github/workflows/ci-cd.yml"
        ".github/workflows/test.yml"
        ".github/workflows/dependency-update.yml"
    )
    
    for workflow in "${workflow_files[@]}"; do
        if [[ -f "$workflow" ]]; then
            log_success "$(basename $workflow) 존재"
        else
            log_error "$(basename $workflow) 누락"
            OVERALL_STATUS="not_ready"
        fi
    done
}

# Docker 파일 확인
check_docker_files() {
    log_info "Docker 설정 파일 확인 중..."
    
    local docker_files=(
        "docker-compose.yml"
        "docker-compose.staging.yml"
        "docker-compose.prod.yml"
        "backend/Dockerfile.prod"
        "frontend/Dockerfile.prod"
    )
    
    for docker_file in "${docker_files[@]}"; do
        if [[ -f "$docker_file" ]]; then
            log_success "$(basename $docker_file) 존재"
        else
            log_warning "$(basename $docker_file) 누락 (선택사항)"
        fi
    done
}

# 환경 파일 확인
check_env_files() {
    log_info "환경 설정 파일 확인 중..."
    
    local env_files=(
        ".env.staging"
        ".env.production"
    )
    
    for env_file in "${env_files[@]}"; do
        if [[ -f "$env_file" ]]; then
            log_success "$env_file 존재"
        else
            log_warning "$env_file 누락"
        fi
    done
}

# 스크립트 파일 확인
check_scripts() {
    log_info "배포 스크립트 확인 중..."
    
    local scripts=(
        "scripts/deploy.sh"
        "scripts/backup.sh"
        "scripts/health-check.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [[ -f "$script" && -x "$script" ]]; then
            log_success "$(basename $script) 실행 가능"
        elif [[ -f "$script" ]]; then
            log_warning "$(basename $script) 존재하지만 실행 권한 없음"
            chmod +x "$script"
            log_success "$(basename $script) 실행 권한 부여됨"
        else
            log_error "$(basename $script) 누락"
            OVERALL_STATUS="not_ready"
        fi
    done
}

# GitHub Actions 활성화 확인
check_actions_enabled() {
    log_info "GitHub Actions 활성화 상태 확인 중..."
    
    if gh api repos/:owner/:repo/actions/permissions -R "$REPO" &>/dev/null; then
        log_success "GitHub Actions 활성화됨"
    else
        log_warning "GitHub Actions 상태 확인 불가"
    fi
}

# 브랜치 보호 규칙 확인
check_branch_protection() {
    log_info "브랜치 보호 규칙 확인 중..."
    
    local branches=("main" "develop")
    
    for branch in "${branches[@]}"; do
        if gh api repos/:owner/:repo/branches/$branch/protection -R "$REPO" &>/dev/null; then
            log_success "$branch 브랜치 보호 규칙 설정됨"
        else
            log_warning "$branch 브랜치 보호 규칙 미설정"
        fi
    done
}

# 배포 준비 상태 요약
print_summary() {
    echo ""
    echo "========================================"
    log_info "배포 준비 상태 요약"
    echo "========================================"
    
    case $OVERALL_STATUS in
        "ready")
            log_success "🚀 모든 준비 완료! 자동 배포 시작 가능"
            echo ""
            log_info "다음 단계:"
            echo "1. develop 브랜치에 코드 푸시 → 스테이징 자동 배포"
            echo "2. main 브랜치에 코드 푸시 → 프로덕션 자동 배포"
            echo "3. GitHub Actions 탭에서 워크플로우 진행 상황 모니터링"
            echo ""
            log_info "배포 명령어:"
            echo "git push origin develop  # 스테이징 배포"
            echo "git push origin main     # 프로덕션 배포"
            ;;
        "not_ready")
            log_error "❌ 배포 준비 미완료"
            echo ""
            log_info "위의 오류들을 수정한 후 다시 실행하세요."
            ;;
    esac
    
    echo ""
    log_info "저장소: https://github.com/$REPO"
    log_info "Actions: https://github.com/$REPO/actions"
    echo "========================================"
}

# 메인 실행
main() {
    log_info "MyZone 배포 준비 상태 확인 시작"
    echo ""
    
    check_gh_cli
    check_github_secrets
    check_workflow_files
    check_docker_files
    check_env_files
    check_scripts
    check_actions_enabled
    check_branch_protection
    
    print_summary
    
    # 종료 코드 설정
    case $OVERALL_STATUS in
        "ready")
            exit 0
            ;;
        "not_ready")
            exit 1
            ;;
    esac
}

# 스크립트 실행
main "$@"