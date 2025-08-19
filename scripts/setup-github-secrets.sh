#!/bin/bash

# GitHub Secrets 설정 도우미 스크립트
# GitHub CLI를 사용하여 Secrets를 자동으로 설정합니다.

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

# GitHub CLI 설치 확인
check_gh_cli() {
    if ! command -v gh &> /dev/null; then
        log_error "GitHub CLI가 설치되지 않았습니다."
        log_info "설치 방법:"
        log_info "  macOS: brew install gh"
        log_info "  Ubuntu: sudo apt install gh"
        log_info "  Windows: winget install GitHub.cli"
        exit 1
    fi
    
    # GitHub CLI 로그인 확인
    if ! gh auth status &> /dev/null; then
        log_error "GitHub CLI에 로그인되지 않았습니다."
        log_info "다음 명령어로 로그인하세요: gh auth login"
        exit 1
    fi
    
    log_success "GitHub CLI 준비 완료"
}

# SSH 키 생성
generate_ssh_keys() {
    log_info "SSH 키 생성 중..."
    
    mkdir -p ~/.ssh
    
    # 스테이징용 SSH 키
    if [[ ! -f ~/.ssh/myzone_staging ]]; then
        ssh-keygen -t rsa -b 4096 -C "staging@myzone.com" -f ~/.ssh/myzone_staging -N ""
        log_success "스테이징용 SSH 키 생성 완료"
    else
        log_warning "스테이징용 SSH 키가 이미 존재합니다"
    fi
    
    # 프로덕션용 SSH 키
    if [[ ! -f ~/.ssh/myzone_production ]]; then
        ssh-keygen -t rsa -b 4096 -C "production@myzone.com" -f ~/.ssh/myzone_production -N ""
        log_success "프로덕션용 SSH 키 생성 완료"
    else
        log_warning "프로덕션용 SSH 키가 이미 존재합니다"
    fi
    
    # 권한 설정
    chmod 600 ~/.ssh/myzone_staging ~/.ssh/myzone_production
    chmod 644 ~/.ssh/myzone_staging.pub ~/.ssh/myzone_production.pub
    
    log_info "생성된 공개키를 서버에 추가하세요:"
    echo ""
    echo "스테이징 서버:"
    echo "ssh-copy-id -i ~/.ssh/myzone_staging.pub user@staging.myzone.com"
    echo ""
    echo "프로덕션 서버:"
    echo "ssh-copy-id -i ~/.ssh/myzone_production.pub user@myzone.com"
    echo ""
}

# 사용자 입력 받기
get_user_input() {
    log_info "서버 정보를 입력해주세요:"
    
    # 스테이징 환경
    echo ""
    log_info "=== 스테이징 환경 ==="
    read -p "스테이징 서버 사용자명 (예: ubuntu): " STAGING_USER
    read -p "스테이징 서버 호스트 (예: staging.myzone.com): " STAGING_HOST
    read -p "스테이징 서버 URL (예: https://staging.myzone.com): " STAGING_URL
    
    # 프로덕션 환경
    echo ""
    log_info "=== 프로덕션 환경 ==="
    read -p "프로덕션 서버 사용자명 (예: myzone): " PRODUCTION_USER
    read -p "프로덕션 서버 호스트 (예: myzone.com): " PRODUCTION_HOST
    read -p "프로덕션 서버 URL (예: https://myzone.com): " PRODUCTION_URL
    
    # 선택사항
    echo ""
    log_info "=== 선택사항 ==="
    read -p "슬랙 웹훅 URL (선택사항, 엔터로 건너뛰기): " SLACK_WEBHOOK
    read -p "Codecov 토큰 (선택사항, 엔터로 건너뛰기): " CODECOV_TOKEN
}

# GitHub Secrets 설정
set_github_secrets() {
    log_info "GitHub Secrets 설정 중..."
    
    # SSH 키 읽기
    STAGING_SSH_KEY=$(cat ~/.ssh/myzone_staging)
    PRODUCTION_SSH_KEY=$(cat ~/.ssh/myzone_production)
    
    # 필수 Secrets 설정
    gh secret set STAGING_SSH_KEY --body "$STAGING_SSH_KEY"
    gh secret set STAGING_USER --body "$STAGING_USER"
    gh secret set STAGING_HOST --body "$STAGING_HOST"
    gh secret set STAGING_URL --body "$STAGING_URL"
    
    gh secret set PRODUCTION_SSH_KEY --body "$PRODUCTION_SSH_KEY"
    gh secret set PRODUCTION_USER --body "$PRODUCTION_USER"
    gh secret set PRODUCTION_HOST --body "$PRODUCTION_HOST"
    gh secret set PRODUCTION_URL --body "$PRODUCTION_URL"
    
    log_success "필수 Secrets 설정 완료"
    
    # 선택사항 Secrets 설정
    if [[ -n "$SLACK_WEBHOOK" ]]; then
        gh secret set SLACK_WEBHOOK --body "$SLACK_WEBHOOK"
        log_success "슬랙 웹훅 설정 완료"
    fi
    
    if [[ -n "$CODECOV_TOKEN" ]]; then
        gh secret set CODECOV_TOKEN --body "$CODECOV_TOKEN"
        log_success "Codecov 토큰 설정 완료"
    fi
}

# Secrets 목록 확인
list_secrets() {
    log_info "설정된 GitHub Secrets 목록:"
    gh secret list
}

# SSH 연결 테스트
test_ssh_connections() {
    log_info "SSH 연결 테스트 중..."
    
    # 스테이징 서버 테스트
    if ssh -i ~/.ssh/myzone_staging -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$STAGING_USER@$STAGING_HOST" "echo 'Staging connection successful'" 2>/dev/null; then
        log_success "스테이징 서버 연결 성공"
    else
        log_warning "스테이징 서버 연결 실패 - 공개키가 서버에 추가되었는지 확인하세요"
    fi
    
    # 프로덕션 서버 테스트
    if ssh -i ~/.ssh/myzone_production -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$PRODUCTION_USER@$PRODUCTION_HOST" "echo 'Production connection successful'" 2>/dev/null; then
        log_success "프로덕션 서버 연결 성공"
    else
        log_warning "프로덕션 서버 연결 실패 - 공개키가 서버에 추가되었는지 확인하세요"
    fi
}

# 설정 요약 출력
print_summary() {
    echo ""
    log_success "GitHub Secrets 설정 완료!"
    echo ""
    log_info "설정된 정보:"
    echo "  스테이징: $STAGING_USER@$STAGING_HOST ($STAGING_URL)"
    echo "  프로덕션: $PRODUCTION_USER@$PRODUCTION_HOST ($PRODUCTION_URL)"
    if [[ -n "$SLACK_WEBHOOK" ]]; then
        echo "  슬랙 알림: 설정됨"
    fi
    if [[ -n "$CODECOV_TOKEN" ]]; then
        echo "  Codecov: 설정됨"
    fi
    echo ""
    log_info "다음 단계:"
    echo "1. 공개키를 서버에 추가 (위에 표시된 명령어 사용)"
    echo "2. 코드를 develop 브랜치에 push하여 CI/CD 테스트"
    echo "3. GitHub Actions 탭에서 워크플로우 실행 확인"
    echo ""
}

# 메인 실행
main() {
    log_info "MyZone GitHub Secrets 설정 도우미"
    echo ""
    
    check_gh_cli
    generate_ssh_keys
    get_user_input
    set_github_secrets
    list_secrets
    test_ssh_connections
    print_summary
}

# 스크립트 실행
main "$@"