#!/bin/bash

# GitHub Pages 배포 상태 확인 스크립트
# 사용법: ./scripts/check-deployment.sh [repository-name]

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 함수 정의
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_url() {
    local url=$1
    local name=$2
    local timeout=${3:-10}
    
    print_status "Checking $name: $url"
    
    if curl -s -f -m $timeout -o /dev/null "$url"; then
        print_success "$name is accessible"
        return 0
    else
        print_error "$name is not accessible"
        return 1
    fi
}

# 메인 로직
main() {
    local repo_name=${1:-"myzone-mobile-activation"}
    local github_user=${GITHUB_USER:-$(git config user.name 2>/dev/null || echo "unknown")}
    
    print_status "Starting deployment health check..."
    print_status "Repository: $repo_name"
    print_status "GitHub User: $github_user"
    
    # URL 구성
    local base_url="https://${github_user}.github.io/${repo_name}"
    local landing_url="$base_url"
    local app_url="$base_url/app"
    
    echo ""
    print_status "URLs to check:"
    echo "  Landing Page: $landing_url"
    echo "  React App: $app_url"
    echo ""
    
    # 상태 확인
    local landing_ok=false
    local app_ok=false
    
    if check_url "$landing_url" "Landing Page"; then
        landing_ok=true
    fi
    
    echo ""
    
    if check_url "$app_url" "React App"; then
        app_ok=true
    fi
    
    echo ""
    print_status "Health Check Summary:"
    echo "  Landing Page: $([ "$landing_ok" = true ] && echo -e "${GREEN}✅ OK${NC}" || echo -e "${RED}❌ FAIL${NC}")"
    echo "  React App: $([ "$app_ok" = true ] && echo -e "${GREEN}✅ OK${NC}" || echo -e "${RED}❌ FAIL${NC}")"
    
    if [ "$landing_ok" = true ] && [ "$app_ok" = true ]; then
        echo ""
        print_success "🎉 All services are healthy!"
        print_success "🚀 Deployment is successful and verified"
        return 0
    else
        echo ""
        print_warning "⚠️ Some services are not accessible"
        print_warning "🔄 GitHub Pages can take a few minutes to update after deployment"
        print_warning "💡 Try again in a few minutes if this is a recent deployment"
        return 1
    fi
}

# 도움말
show_help() {
    echo "GitHub Pages Deployment Health Check"
    echo ""
    echo "Usage: $0 [repository-name]"
    echo ""
    echo "Options:"
    echo "  -h, --help    Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  GITHUB_USER   GitHub username (default: git config user.name)"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Use default repository name"
    echo "  $0 my-awesome-project                 # Check specific repository"
    echo "  GITHUB_USER=myuser $0 my-project     # Override GitHub username"
}

# 인자 처리
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac