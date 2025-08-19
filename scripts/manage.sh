#!/bin/bash

# MyZone 통합 관리 스크립트
# 모든 운영 작업을 하나의 인터페이스로 관리합니다.

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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

log_header() {
    echo -e "${CYAN}🚀 $1${NC}"
}

# 사용법 출력
usage() {
    log_header "MyZone 통합 관리 도구"
    echo ""
    echo "사용법: $0 [명령] [옵션]"
    echo ""
    echo "명령:"
    echo "  setup              초기 설정 (시크릿 생성, SSL 설정)"
    echo "  deploy [env]       배포 (staging/production)"
    echo "  backup             데이터베이스 백업"
    echo "  restore            재해 복구"
    echo "  health             헬스체크"
    echo "  logs [service]     로그 확인"
    echo "  monitor            모니터링 시스템 시작/중지"
    echo "  ssl [domain]       SSL 인증서 설정"
    echo "  status             전체 시스템 상태"
    echo "  update             의존성 업데이트"
    echo "  clean              정리 작업"
    echo "  secrets            GitHub Secrets 관리"
    echo ""
    echo "예시:"
    echo "  $0 setup"
    echo "  $0 deploy production"
    echo "  $0 health"
    echo "  $0 logs backend"
    echo "  $0 secrets setup"
    echo "  $0 secrets validate"
    echo "  $0 ssl myzone.com admin@myzone.com"
    echo ""
    exit 1
}

# 초기 설정
setup() {
    log_header "MyZone 초기 설정"
    
    log_info "1. 시크릿 생성"
    ./scripts/generate-secrets.sh
    
    log_info "2. 디렉토리 생성"
    mkdir -p logs/{nginx,backend} backups monitoring/{grafana,prometheus}
    
    log_info "3. 권한 설정"
    chmod 755 scripts/*.sh
    
    log_success "초기 설정 완료"
}

# 배포
deploy() {
    local environment="$1"
    
    if [[ -z "$environment" ]]; then
        log_error "환경을 지정해주세요 (staging/production)"
        exit 1
    fi
    
    log_header "MyZone $environment 배포"
    ./scripts/deploy.sh "$environment" "${@:2}"
}

# 백업
backup() {
    log_header "데이터베이스 백업"
    
    if docker-compose -f docker-compose.prod.yml ps | grep -q "myzone_db_prod"; then
        ./scripts/backup.sh
    else
        log_error "프로덕션 데이터베이스가 실행 중이지 않습니다"
        exit 1
    fi
}

# 복구
restore() {
    log_header "재해 복구"
    ./scripts/disaster-recovery.sh "$@"
}

# 헬스체크
health() {
    log_header "시스템 헬스체크"
    ./scripts/health-check.sh
}

# 로그 확인
logs() {
    local service="$1"
    
    log_header "로그 확인"
    
    if [[ -z "$service" ]]; then
        log_info "사용 가능한 서비스: backend, frontend, db, redis, nginx"
        docker-compose -f docker-compose.prod.yml logs --tail=100
    else
        case "$service" in
            backend|frontend|db|redis|nginx)
                docker-compose -f docker-compose.prod.yml logs --tail=100 -f "$service"
                ;;
            *)
                log_error "알 수 없는 서비스: $service"
                log_info "사용 가능한 서비스: backend, frontend, db, redis, nginx"
                exit 1
                ;;
        esac
    fi
}

# 모니터링 시스템
monitor() {
    local action="$1"
    
    log_header "모니터링 시스템"
    
    case "$action" in
        start)
            log_info "모니터링 시스템 시작"
            docker-compose -f docker-compose.monitoring.yml up -d
            log_success "모니터링 시스템이 시작되었습니다"
            log_info "Grafana: http://localhost:3001"
            log_info "Prometheus: http://localhost:9090"
            log_info "Kibana: http://localhost:5601"
            ;;
        stop)
            log_info "모니터링 시스템 중지"
            docker-compose -f docker-compose.monitoring.yml down
            log_success "모니터링 시스템이 중지되었습니다"
            ;;
        restart)
            log_info "모니터링 시스템 재시작"
            docker-compose -f docker-compose.monitoring.yml restart
            log_success "모니터링 시스템이 재시작되었습니다"
            ;;
        status)
            docker-compose -f docker-compose.monitoring.yml ps
            ;;
        *)
            log_error "사용법: $0 monitor [start|stop|restart|status]"
            exit 1
            ;;
    esac
}

# SSL 설정
ssl() {
    local domain="$1"
    local email="$2"
    
    if [[ -z "$domain" || -z "$email" ]]; then
        log_error "도메인과 이메일을 지정해주세요"
        log_info "사용법: $0 ssl domain.com admin@domain.com"
        exit 1
    fi
    
    log_header "SSL 인증서 설정"
    ./scripts/ssl-setup.sh "$domain" "$email"
}

# 시스템 상태
status() {
    log_header "MyZone 시스템 상태"
    
    echo ""
    log_info "Docker 컨테이너 상태:"
    docker-compose -f docker-compose.prod.yml ps
    
    echo ""
    log_info "시스템 리소스:"
    echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')"
    echo "메모리: $(free -h | grep Mem | awk '{print $3"/"$2}')"
    echo "디스크: $(df -h / | awk 'NR==2 {print $3"/"$2" ("$5" 사용)"}')"
    
    echo ""
    log_info "네트워크 상태:"
    if curl -s -o /dev/null -w "%{http_code}" http://localhost/health | grep -q "200"; then
        log_success "Frontend: 정상"
    else
        log_error "Frontend: 오류"
    fi
    
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health | grep -q "200"; then
        log_success "Backend: 정상"
    else
        log_error "Backend: 오류"
    fi
}

# 의존성 업데이트
update() {
    log_header "의존성 업데이트"
    
    log_info "1. Git 저장소 업데이트"
    git pull origin main
    
    log_info "2. Docker 이미지 업데이트"
    docker-compose -f docker-compose.prod.yml pull
    
    log_info "3. 컨테이너 재시작"
    docker-compose -f docker-compose.prod.yml up -d
    
    log_success "업데이트 완료"
}

# 정리 작업
clean() {
    log_header "시스템 정리"
    
    log_info "1. 사용하지 않는 Docker 이미지 정리"
    docker image prune -f
    
    log_info "2. 사용하지 않는 Docker 볼륨 정리"
    docker volume prune -f
    
    log_info "3. 오래된 로그 파일 정리"
    find logs/ -name "*.log" -mtime +30 -delete 2>/dev/null || true
    
    log_info "4. 오래된 백업 파일 정리"
    find backups/ -name "*.sql.gz" -mtime +30 -delete 2>/dev/null || true
    
    log_success "정리 완료"
}

# GitHub Secrets 관리
secrets() {
    local action="$1"
    
    log_header "GitHub Secrets 관리"
    
    case "$action" in
        setup)
            log_info "GitHub Secrets 자동 설정"
            ./scripts/setup-github-secrets.sh
            ;;
        validate)
            log_info "GitHub Secrets 검증"
            ./scripts/validate-secrets.sh
            ;;
        list)
            log_info "GitHub Secrets 목록"
            if command -v gh &> /dev/null; then
                gh secret list
            else
                log_error "GitHub CLI가 설치되지 않았습니다"
                exit 1
            fi
            ;;
        template)
            log_info "Secrets 템플릿 표시"
            if [[ -f ".github/secrets-template.env" ]]; then
                cat .github/secrets-template.env
            else
                log_error "템플릿 파일을 찾을 수 없습니다"
                exit 1
            fi
            ;;
        help)
            echo "GitHub Secrets 관리 명령어:"
            echo "  setup      - SSH 키 생성 및 Secrets 자동 설정"
            echo "  validate   - 설정된 Secrets 검증"
            echo "  list       - 현재 설정된 Secrets 목록"
            echo "  template   - Secrets 템플릿 표시"
            echo "  help       - 이 도움말 표시"
            ;;
        *)
            log_error "사용법: $0 secrets [setup|validate|list|template|help]"
            exit 1
            ;;
    esac
}

# 메인 로직
main() {
    if [[ $# -eq 0 ]]; then
        usage
    fi
    
    local command="$1"
    shift
    
    case "$command" in
        setup)
            setup "$@"
            ;;
        deploy)
            deploy "$@"
            ;;
        backup)
            backup "$@"
            ;;
        restore)
            restore "$@"
            ;;
        health)
            health "$@"
            ;;
        logs)
            logs "$@"
            ;;
        monitor)
            monitor "$@"
            ;;
        ssl)
            ssl "$@"
            ;;
        status)
            status "$@"
            ;;
        update)
            update "$@"
            ;;
        clean)
            clean "$@"
            ;;
        secrets)
            secrets "$@"
            ;;
        -h|--help|help)
            usage
            ;;
        *)
            log_error "알 수 없는 명령: $command"
            usage
            ;;
    esac
}

# 스크립트 실행
main "$@"