#!/bin/bash

# GitHub Secrets 검증 스크립트
# 설정된 Secrets가 올바른지 확인합니다.

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

# GitHub CLI 확인
check_gh_cli() {
    if ! command -v gh &> /dev/null; then
        log_error "GitHub CLI가 설치되지 않았습니다."
        exit 1
    fi
    
    if ! gh auth status &> /dev/null; then
        log_error "GitHub CLI에 로그인되지 않았습니다."
        exit 1
    fi
}

# 필수 Secrets 확인
check_required_secrets() {
    log_info "필수 GitHub Secrets 확인 중..."
    
    local required_secrets=(
        "STAGING_SSH_KEY"
        "STAGING_USER"
        "STAGING_HOST"
        "STAGING_URL"
        "PRODUCTION_SSH_KEY"
        "PRODUCTION_USER"
        "PRODUCTION_HOST"
        "PRODUCTION_URL"
    )
    
    local missing_secrets=()
    
    for secret in "${required_secrets[@]}"; do
        if gh secret list | grep -q "^$secret"; then
            log_success "$secret 설정됨"
        else
            log_error "$secret 누락됨"
            missing_secrets+=("$secret")
        fi
    done
    
    if [[ ${#missing_secrets[@]} -gt 0 ]]; then
        log_error "누락된 필수 Secrets: ${missing_secrets[*]}"
        return 1
    fi
    
    log_success "모든 필수 Secrets 설정 완료"
    return 0
}

# 선택사항 Secrets 확인
check_optional_secrets() {
    log_info "선택사항 GitHub Secrets 확인 중..."
    
    local optional_secrets=(
        "SLACK_WEBHOOK"
        "CODECOV_TOKEN"
        "SONAR_TOKEN"
    )
    
    for secret in "${optional_secrets[@]}"; do
        if gh secret list | grep -q "^$secret"; then
            log_success "$secret 설정됨"
        else
            log_warning "$secret 설정되지 않음 (선택사항)"
        fi
    done
}

# SSH 키 형식 검증
validate_ssh_key_format() {
    local key_name="$1"
    local key_content
    
    # GitHub API를 통해 Secret 값을 직접 가져올 수는 없으므로
    # 로컬 SSH 키 파일이 있는지 확인
    local key_file=""
    case "$key_name" in
        "STAGING_SSH_KEY")
            key_file="$HOME/.ssh/myzone_staging"
            ;;
        "PRODUCTION_SSH_KEY")
            key_file="$HOME/.ssh/myzone_production"
            ;;
    esac
    
    if [[ -f "$key_file" ]]; then
        if ssh-keygen -l -f "$key_file" &>/dev/null; then
            log_success "$key_name 형식 유효"
        else
            log_error "$key_name 형식 무효"
            return 1
        fi
    else
        log_warning "$key_name 로컬 키 파일 없음 ($key_file)"
    fi
}

# URL 형식 검증
validate_url_format() {
    local url_name="$1"
    local url_pattern="^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$"
    
    # 실제 URL 값을 가져올 수 없으므로 패턴만 확인
    log_info "$url_name URL 형식은 수동으로 확인해주세요"
    log_info "올바른 형식: https://domain.com 또는 http://ip-address"
}

# 네트워크 연결 테스트
test_network_connectivity() {
    log_info "네트워크 연결 테스트 중..."
    
    # 일반적인 연결 테스트
    if ping -c 1 google.com &>/dev/null; then
        log_success "인터넷 연결 정상"
    else
        log_error "인터넷 연결 실패"
        return 1
    fi
    
    # GitHub 연결 테스트
    if curl -s https://api.github.com/zen &>/dev/null; then
        log_success "GitHub API 연결 정상"
    else
        log_error "GitHub API 연결 실패"
        return 1
    fi
}

# GitHub Actions 권한 확인
check_actions_permissions() {
    log_info "GitHub Actions 권한 확인 중..."
    
    # 저장소 정보 가져오기
    local repo_info
    if repo_info=$(gh repo view --json permissions 2>/dev/null); then
        log_success "저장소 접근 권한 확인됨"
    else
        log_error "저장소 접근 권한 없음"
        return 1
    fi
    
    # Actions 활성화 확인
    if gh api repos/:owner/:repo/actions/permissions &>/dev/null; then
        log_success "GitHub Actions 활성화됨"
    else
        log_warning "GitHub Actions 상태 확인 불가"
    fi
}

# 워크플로우 파일 검증
validate_workflow_files() {
    log_info "워크플로우 파일 검증 중..."
    
    local workflow_files=(
        ".github/workflows/ci-cd.yml"
        ".github/workflows/test.yml"
        ".github/workflows/dependency-update.yml"
    )
    
    for workflow in "${workflow_files[@]}"; do
        if [[ -f "$workflow" ]]; then
            # YAML 문법 검사 (yq가 설치된 경우)
            if command -v yq &>/dev/null; then
                if yq eval . "$workflow" &>/dev/null; then
                    log_success "$workflow 문법 유효"
                else
                    log_error "$workflow 문법 오류"
                fi
            else
                log_success "$workflow 파일 존재"
            fi
        else
            log_error "$workflow 파일 없음"
        fi
    done
}

# 환경별 설정 검증
validate_environment_config() {
    log_info "환경별 설정 검증 중..."
    
    # Docker Compose 파일 확인
    local compose_files=(
        "docker-compose.yml"
        "docker-compose.staging.yml"
        "docker-compose.prod.yml"
        "docker-compose.monitoring.yml"
    )
    
    for compose_file in "${compose_files[@]}"; do
        if [[ -f "$compose_file" ]]; then
            if docker-compose -f "$compose_file" config &>/dev/null; then
                log_success "$compose_file 설정 유효"
            else
                log_error "$compose_file 설정 오류"
            fi
        else
            log_warning "$compose_file 파일 없음"
        fi
    done
}

# 보안 검사
security_check() {
    log_info "보안 검사 중..."
    
    # .gitignore 확인
    if [[ -f ".gitignore" ]]; then
        local sensitive_patterns=(
            "secrets/"
            "*.pem"
            "*.key"
            ".env.production"
            ".env.staging"
        )
        
        for pattern in "${sensitive_patterns[@]}"; do
            if grep -q "$pattern" .gitignore; then
                log_success ".gitignore에 $pattern 포함됨"
            else
                log_warning ".gitignore에 $pattern 누락됨"
            fi
        done
    else
        log_error ".gitignore 파일 없음"
    fi
    
    # 민감한 파일이 Git에 포함되지 않았는지 확인
    if git ls-files | grep -E "\.(pem|key)$|secrets/|\.env\.production" &>/dev/null; then
        log_error "민감한 파일이 Git에 포함되어 있습니다!"
        git ls-files | grep -E "\.(pem|key)$|secrets/|\.env\.production"
    else
        log_success "민감한 파일이 Git에서 제외됨"
    fi
}

# 종합 보고서 생성
generate_report() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local report_file="secrets-validation-report-$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "MyZone GitHub Secrets 검증 보고서"
        echo "생성 시간: $timestamp"
        echo "========================================"
        echo ""
        
        echo "GitHub Secrets 목록:"
        gh secret list
        echo ""
        
        echo "워크플로우 파일:"
        find .github/workflows -name "*.yml" -o -name "*.yaml" 2>/dev/null || echo "워크플로우 파일 없음"
        echo ""
        
        echo "Docker Compose 파일:"
        find . -maxdepth 1 -name "docker-compose*.yml" 2>/dev/null || echo "Docker Compose 파일 없음"
        echo ""
        
        echo "SSH 키 파일:"
        ls -la ~/.ssh/myzone_* 2>/dev/null || echo "SSH 키 파일 없음"
        echo ""
        
    } > "$report_file"
    
    log_success "검증 보고서 생성: $report_file"
}

# 메인 실행
main() {
    log_info "MyZone GitHub Secrets 검증 시작"
    echo ""
    
    local exit_code=0
    
    check_gh_cli || exit_code=1
    check_required_secrets || exit_code=1
    check_optional_secrets
    
    validate_ssh_key_format "STAGING_SSH_KEY"
    validate_ssh_key_format "PRODUCTION_SSH_KEY"
    
    validate_url_format "STAGING_URL"
    validate_url_format "PRODUCTION_URL"
    
    test_network_connectivity || exit_code=1
    check_actions_permissions || exit_code=1
    validate_workflow_files || exit_code=1
    validate_environment_config
    security_check
    
    generate_report
    
    echo ""
    if [[ $exit_code -eq 0 ]]; then
        log_success "모든 검증 통과! CI/CD 파이프라인 사용 준비 완료"
    else
        log_error "일부 검증 실패. 위의 오류를 수정한 후 다시 실행하세요"
    fi
    
    exit $exit_code
}

# 스크립트 실행
main "$@"