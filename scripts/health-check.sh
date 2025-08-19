#!/bin/bash

# 시스템 헬스체크 스크립트
# 모든 서비스의 상태를 확인하고 보고서를 생성합니다.

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
OVERALL_STATUS="healthy"
REPORT_FILE="health-report-$(date +%Y%m%d_%H%M%S).txt"

# 보고서 헤더 작성
write_report_header() {
    cat > "$REPORT_FILE" << EOF
MyZone 시스템 헬스체크 보고서
생성 시간: $(date)
호스트: $(hostname)
사용자: $(whoami)

===========================================

EOF
}

# 보고서에 결과 추가
add_to_report() {
    echo "$1" >> "$REPORT_FILE"
}

# Docker 컨테이너 상태 확인
check_containers() {
    log_info "Docker 컨테이너 상태 확인 중..."
    add_to_report "## Docker 컨테이너 상태"
    add_to_report ""
    
    local containers=(
        "myzone_backend_prod"
        "myzone_frontend_prod"
        "myzone_db_prod"
        "myzone_redis_prod"
        "myzone_nginx_prod"
    )
    
    for container in "${containers[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "$container"; then
            local status=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null || echo "not found")
            local health=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "no healthcheck")
            
            if [[ "$status" == "running" ]]; then
                log_success "$container: 실행 중 (Health: $health)"
                add_to_report "✅ $container: 실행 중 (Health: $health)"
            else
                log_error "$container: $status"
                add_to_report "❌ $container: $status"
                OVERALL_STATUS="unhealthy"
            fi
        else
            log_error "$container: 컨테이너를 찾을 수 없음"
            add_to_report "❌ $container: 컨테이너를 찾을 수 없음"
            OVERALL_STATUS="unhealthy"
        fi
    done
    
    add_to_report ""
}

# HTTP 엔드포인트 상태 확인
check_endpoints() {
    log_info "HTTP 엔드포인트 상태 확인 중..."
    add_to_report "## HTTP 엔드포인트 상태"
    add_to_report ""
    
    local endpoints=(
        "http://localhost/health:Frontend Health"
        "http://localhost:8000/api/v1/health:Backend Health"
        "http://localhost:8000/docs:API Documentation"
    )
    
    for endpoint_info in "${endpoints[@]}"; do
        local endpoint=$(echo "$endpoint_info" | cut -d':' -f1)
        local name=$(echo "$endpoint_info" | cut -d':' -f2)
        
        local response=$(curl -s -o /dev/null -w "%{http_code}:%{time_total}" "$endpoint" 2>/dev/null || echo "000:0")
        local status_code=$(echo "$response" | cut -d':' -f1)
        local response_time=$(echo "$response" | cut -d':' -f2)
        
        if [[ "$status_code" == "200" ]]; then
            log_success "$name: OK (${response_time}s)"
            add_to_report "✅ $name: OK (응답시간: ${response_time}s)"
        else
            log_error "$name: HTTP $status_code"
            add_to_report "❌ $name: HTTP $status_code"
            OVERALL_STATUS="unhealthy"
        fi
    done
    
    add_to_report ""
}

# 데이터베이스 연결 확인
check_database() {
    log_info "데이터베이스 연결 확인 중..."
    add_to_report "## 데이터베이스 상태"
    add_to_report ""
    
    # PostgreSQL 연결 테스트
    if docker-compose -f docker-compose.prod.yml exec -T db pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then
        log_success "PostgreSQL: 연결 가능"
        add_to_report "✅ PostgreSQL: 연결 가능"
        
        # 연결 수 확인
        local connections=$(docker-compose -f docker-compose.prod.yml exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null | tr -d ' ')
        add_to_report "   활성 연결 수: $connections"
        
        # 데이터베이스 크기 확인
        local db_size=$(docker-compose -f docker-compose.prod.yml exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT pg_size_pretty(pg_database_size('$POSTGRES_DB'));" 2>/dev/null | tr -d ' ')
        add_to_report "   데이터베이스 크기: $db_size"
    else
        log_error "PostgreSQL: 연결 실패"
        add_to_report "❌ PostgreSQL: 연결 실패"
        OVERALL_STATUS="unhealthy"
    fi
    
    # Redis 연결 테스트
    if docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping >/dev/null 2>&1; then
        log_success "Redis: 연결 가능"
        add_to_report "✅ Redis: 연결 가능"
        
        # Redis 메모리 사용량 확인
        local redis_memory=$(docker-compose -f docker-compose.prod.yml exec -T redis redis-cli info memory | grep used_memory_human | cut -d':' -f2 | tr -d '\r')
        add_to_report "   메모리 사용량: $redis_memory"
    else
        log_error "Redis: 연결 실패"
        add_to_report "❌ Redis: 연결 실패"
        OVERALL_STATUS="unhealthy"
    fi
    
    add_to_report ""
}

# 시스템 리소스 확인
check_system_resources() {
    log_info "시스템 리소스 확인 중..."
    add_to_report "## 시스템 리소스"
    add_to_report ""
    
    # CPU 사용률
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    add_to_report "CPU 사용률: ${cpu_usage}%"
    
    if (( $(echo "$cpu_usage > 80" | bc -l) )); then
        log_warning "CPU 사용률이 높습니다: ${cpu_usage}%"
        OVERALL_STATUS="warning"
    else
        log_success "CPU 사용률: ${cpu_usage}%"
    fi
    
    # 메모리 사용률
    local memory_info=$(free | grep Mem)
    local total_mem=$(echo $memory_info | awk '{print $2}')
    local used_mem=$(echo $memory_info | awk '{print $3}')
    local memory_usage=$(echo "scale=1; $used_mem * 100 / $total_mem" | bc)
    
    add_to_report "메모리 사용률: ${memory_usage}%"
    
    if (( $(echo "$memory_usage > 85" | bc -l) )); then
        log_warning "메모리 사용률이 높습니다: ${memory_usage}%"
        OVERALL_STATUS="warning"
    else
        log_success "메모리 사용률: ${memory_usage}%"
    fi
    
    # 디스크 사용률
    local disk_usage=$(df -h / | awk 'NR==2 {print $5}' | cut -d'%' -f1)
    add_to_report "디스크 사용률: ${disk_usage}%"
    
    if (( disk_usage > 85 )); then
        log_warning "디스크 사용률이 높습니다: ${disk_usage}%"
        OVERALL_STATUS="warning"
    else
        log_success "디스크 사용률: ${disk_usage}%"
    fi
    
    # 로드 애버리지
    local load_avg=$(uptime | awk -F'load average:' '{print $2}')
    add_to_report "로드 애버리지:$load_avg"
    
    add_to_report ""
}

# SSL 인증서 확인
check_ssl_certificate() {
    log_info "SSL 인증서 확인 중..."
    add_to_report "## SSL 인증서 상태"
    add_to_report ""
    
    if [[ -f "/etc/nginx/ssl/cert.pem" ]]; then
        local expiry_date=$(openssl x509 -in /etc/nginx/ssl/cert.pem -noout -enddate | cut -d'=' -f2)
        local expiry_timestamp=$(date -d "$expiry_date" +%s)
        local current_timestamp=$(date +%s)
        local days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
        
        add_to_report "SSL 인증서 만료일: $expiry_date"
        add_to_report "만료까지 남은 일수: $days_until_expiry일"
        
        if (( days_until_expiry < 30 )); then
            log_warning "SSL 인증서가 30일 내에 만료됩니다: $days_until_expiry일"
            OVERALL_STATUS="warning"
        else
            log_success "SSL 인증서: 정상 ($days_until_expiry일 남음)"
        fi
    else
        log_warning "SSL 인증서 파일을 찾을 수 없습니다"
        add_to_report "⚠️ SSL 인증서 파일을 찾을 수 없습니다"
    fi
    
    add_to_report ""
}

# 로그 파일 확인
check_logs() {
    log_info "로그 파일 확인 중..."
    add_to_report "## 로그 파일 상태"
    add_to_report ""
    
    local log_dirs=("logs" "/var/log/nginx")
    
    for log_dir in "${log_dirs[@]}"; do
        if [[ -d "$log_dir" ]]; then
            local log_size=$(du -sh "$log_dir" 2>/dev/null | cut -f1)
            add_to_report "$log_dir 크기: $log_size"
            
            # 최근 오류 로그 확인
            local error_count=$(find "$log_dir" -name "*.log" -mtime -1 -exec grep -c "ERROR\|CRITICAL" {} + 2>/dev/null | awk '{sum+=$1} END {print sum+0}')
            add_to_report "$log_dir 최근 24시간 오류 수: $error_count"
            
            if (( error_count > 100 )); then
                log_warning "$log_dir에서 많은 오류가 발견되었습니다: $error_count"
                OVERALL_STATUS="warning"
            fi
        fi
    done
    
    add_to_report ""
}

# 백업 상태 확인
check_backups() {
    log_info "백업 상태 확인 중..."
    add_to_report "## 백업 상태"
    add_to_report ""
    
    if [[ -d "backups" ]]; then
        local latest_backup=$(ls -t backups/myzone_backup_*.sql.gz 2>/dev/null | head -1)
        if [[ -n "$latest_backup" ]]; then
            local backup_date=$(stat -c %y "$latest_backup" | cut -d' ' -f1)
            local backup_size=$(du -sh "$latest_backup" | cut -f1)
            
            add_to_report "최신 백업: $(basename $latest_backup)"
            add_to_report "백업 날짜: $backup_date"
            add_to_report "백업 크기: $backup_size"
            
            # 백업이 24시간 이내인지 확인
            local backup_timestamp=$(stat -c %Y "$latest_backup")
            local current_timestamp=$(date +%s)
            local hours_since_backup=$(( (current_timestamp - backup_timestamp) / 3600 ))
            
            if (( hours_since_backup > 24 )); then
                log_warning "백업이 24시간 이상 오래되었습니다: ${hours_since_backup}시간 전"
                OVERALL_STATUS="warning"
            else
                log_success "백업 상태: 정상 (${hours_since_backup}시간 전)"
            fi
        else
            log_error "백업 파일을 찾을 수 없습니다"
            add_to_report "❌ 백업 파일을 찾을 수 없습니다"
            OVERALL_STATUS="unhealthy"
        fi
    else
        log_warning "백업 디렉토리가 존재하지 않습니다"
        add_to_report "⚠️ 백업 디렉토리가 존재하지 않습니다"
    fi
    
    add_to_report ""
}

# 보고서 마무리
finalize_report() {
    add_to_report "===========================================")
    add_to_report ""
    add_to_report "전체 상태: $OVERALL_STATUS"
    add_to_report "보고서 생성 완료: $(date)"
    
    case $OVERALL_STATUS in
        "healthy")
            log_success "전체 시스템 상태: 정상"
            ;;
        "warning")
            log_warning "전체 시스템 상태: 주의 필요"
            ;;
        "unhealthy")
            log_error "전체 시스템 상태: 문제 발생"
            ;;
    esac
    
    log_info "상세 보고서: $REPORT_FILE"
}

# 슬랙 알림 전송
send_slack_notification() {
    if [[ ! -z "${SLACK_WEBHOOK_URL}" ]]; then
        local emoji=""
        local color=""
        
        case $OVERALL_STATUS in
            "healthy")
                emoji="✅"
                color="good"
                ;;
            "warning")
                emoji="⚠️"
                color="warning"
                ;;
            "unhealthy")
                emoji="❌"
                color="danger"
                ;;
        esac
        
        curl -X POST -H 'Content-type: application/json' \
            --data "{
                \"attachments\": [{
                    \"color\": \"$color\",
                    \"title\": \"$emoji MyZone 헬스체크 결과\",
                    \"text\": \"전체 상태: $OVERALL_STATUS\\n시간: $(date)\\n호스트: $(hostname)\",
                    \"footer\": \"MyZone Monitoring\"
                }]
            }" \
            "${SLACK_WEBHOOK_URL}" || true
    fi
}

# 메인 실행
main() {
    log_info "MyZone 시스템 헬스체크 시작"
    
    # 환경 변수 로드
    if [[ -f ".env.production" ]]; then
        set -a
        source .env.production
        if [[ -f "secrets/.env.secrets" ]]; then
            source secrets/.env.secrets
        fi
        set +a
    fi
    
    write_report_header
    
    check_containers
    check_endpoints
    check_database
    check_system_resources
    check_ssl_certificate
    check_logs
    check_backups
    
    finalize_report
    send_slack_notification
    
    # 종료 코드 설정
    case $OVERALL_STATUS in
        "healthy")
            exit 0
            ;;
        "warning")
            exit 1
            ;;
        "unhealthy")
            exit 2
            ;;
    esac
}

# 스크립트 실행
main "$@"