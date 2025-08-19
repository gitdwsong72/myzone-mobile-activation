#!/bin/bash

# 재해 복구 스크립트
# 백업에서 시스템을 복구합니다.

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
    echo "사용법: $0 [옵션]"
    echo ""
    echo "옵션:"
    echo "  --backup-file FILE    복구할 백업 파일 지정"
    echo "  --backup-date DATE    복구할 백업 날짜 지정 (YYYY-MM-DD)"
    echo "  --list-backups        사용 가능한 백업 목록 표시"
    echo "  --dry-run            실제 복구 없이 시뮬레이션만 실행"
    echo "  --force              확인 없이 강제 복구"
    echo ""
    echo "예시:"
    echo "  $0 --backup-date 2024-01-15"
    echo "  $0 --backup-file /backups/myzone_backup_20240115_030000.sql.gz"
    echo "  $0 --list-backups"
    echo ""
    exit 1
}

# 백업 목록 표시
list_backups() {
    log_info "사용 가능한 백업 파일:"
    echo ""
    
    # 로컬 백업
    if [[ -d "backups" ]]; then
        echo "로컬 백업:"
        ls -la backups/myzone_backup_*.sql.gz 2>/dev/null | while read -r line; do
            echo "  $line"
        done
        echo ""
    fi
    
    # S3 백업 (AWS CLI가 설치된 경우)
    if command -v aws &> /dev/null && [[ ! -z "${BACKUP_S3_BUCKET}" ]]; then
        echo "S3 백업:"
        aws s3 ls s3://${BACKUP_S3_BUCKET}/database-backups/ | while read -r line; do
            echo "  $line"
        done
    fi
}

# 백업 파일 다운로드 (S3에서)
download_backup() {
    local backup_file="$1"
    local local_file="backups/$(basename $backup_file)"
    
    if command -v aws &> /dev/null && [[ ! -z "${BACKUP_S3_BUCKET}" ]]; then
        log_info "S3에서 백업 파일 다운로드 중..."
        aws s3 cp "s3://${BACKUP_S3_BUCKET}/database-backups/$backup_file" "$local_file"
        echo "$local_file"
    else
        log_error "AWS CLI가 설치되지 않았거나 S3 버킷이 설정되지 않았습니다."
        exit 1
    fi
}

# 데이터베이스 복구
restore_database() {
    local backup_file="$1"
    
    log_info "데이터베이스 복구 시작..."
    log_info "백업 파일: $backup_file"
    
    # 백업 파일 존재 확인
    if [[ ! -f "$backup_file" ]]; then
        log_error "백업 파일을 찾을 수 없습니다: $backup_file"
        exit 1
    fi
    
    # 현재 데이터베이스 백업 (안전장치)
    log_info "현재 데이터베이스 백업 중..."
    CURRENT_BACKUP="backups/pre-restore-$(date +%Y%m%d_%H%M%S).sql"
    docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" > "$CURRENT_BACKUP"
    log_success "현재 데이터베이스 백업 완료: $CURRENT_BACKUP"
    
    # 애플리케이션 중지
    log_info "애플리케이션 중지 중..."
    docker-compose -f docker-compose.prod.yml stop backend frontend
    
    # 데이터베이스 연결 종료
    log_info "데이터베이스 연결 종료 중..."
    docker-compose -f docker-compose.prod.yml exec -T db psql -U "$POSTGRES_USER" -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$POSTGRES_DB' AND pid <> pg_backend_pid();"
    
    # 기존 데이터베이스 삭제 및 재생성
    log_info "데이터베이스 재생성 중..."
    docker-compose -f docker-compose.prod.yml exec -T db psql -U "$POSTGRES_USER" -d postgres -c "DROP DATABASE IF EXISTS $POSTGRES_DB;"
    docker-compose -f docker-compose.prod.yml exec -T db psql -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE $POSTGRES_DB;"
    
    # 백업 복원
    log_info "백업 복원 중..."
    if [[ "$backup_file" == *.gz ]]; then
        gunzip -c "$backup_file" | docker-compose -f docker-compose.prod.yml exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
    else
        docker-compose -f docker-compose.prod.yml exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$backup_file"
    fi
    
    # 데이터베이스 마이그레이션 실행
    log_info "데이터베이스 마이그레이션 실행 중..."
    docker-compose -f docker-compose.prod.yml exec -T backend alembic upgrade head
    
    # 애플리케이션 재시작
    log_info "애플리케이션 재시작 중..."
    docker-compose -f docker-compose.prod.yml start backend frontend
    
    # 헬스체크
    log_info "헬스체크 수행 중..."
    sleep 30
    
    BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health || echo "000")
    FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/health || echo "000")
    
    if [[ "$BACKEND_HEALTH" == "200" && "$FRONTEND_HEALTH" == "200" ]]; then
        log_success "복구 완료 및 헬스체크 통과"
    else
        log_error "복구 후 헬스체크 실패 (Backend: $BACKEND_HEALTH, Frontend: $FRONTEND_HEALTH)"
        log_warning "이전 백업으로 롤백을 고려하세요: $CURRENT_BACKUP"
        exit 1
    fi
}

# 파일 시스템 복구
restore_files() {
    local backup_date="$1"
    
    log_info "파일 시스템 복구 시작..."
    
    # 업로드 파일 백업
    if [[ -d "backend_uploads_prod" ]]; then
        log_info "현재 업로드 파일 백업 중..."
        tar -czf "backups/uploads-backup-$(date +%Y%m%d_%H%M%S).tar.gz" backend_uploads_prod/
    fi
    
    # S3에서 파일 복구 (설정된 경우)
    if command -v aws &> /dev/null && [[ ! -z "${BACKUP_S3_BUCKET}" ]]; then
        log_info "S3에서 파일 복구 중..."
        aws s3 sync "s3://${BACKUP_S3_BUCKET}/file-backups/$backup_date/" backend_uploads_prod/
        log_success "파일 복구 완료"
    else
        log_warning "S3 설정이 없어 파일 복구를 건너뜁니다."
    fi
}

# 설정 파일 복구
restore_configs() {
    log_info "설정 파일 복구 시작..."
    
    # 현재 설정 백업
    tar -czf "backups/config-backup-$(date +%Y%m%d_%H%M%S).tar.gz" \
        .env.production \
        secrets/ \
        nginx/ \
        2>/dev/null || true
    
    # Git에서 최신 설정 가져오기
    log_info "Git에서 최신 설정 가져오기..."
    git stash
    git pull origin main
    
    log_success "설정 파일 복구 완료"
}

# 메인 로직
main() {
    local BACKUP_FILE=""
    local BACKUP_DATE=""
    local LIST_BACKUPS=false
    local DRY_RUN=false
    local FORCE=false
    
    # 파라미터 파싱
    while [[ $# -gt 0 ]]; do
        case $1 in
            --backup-file)
                BACKUP_FILE="$2"
                shift 2
                ;;
            --backup-date)
                BACKUP_DATE="$2"
                shift 2
                ;;
            --list-backups)
                LIST_BACKUPS=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
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
    
    # 백업 목록 표시
    if [[ "$LIST_BACKUPS" == "true" ]]; then
        list_backups
        exit 0
    fi
    
    # 백업 파일 또는 날짜 확인
    if [[ -z "$BACKUP_FILE" && -z "$BACKUP_DATE" ]]; then
        log_error "백업 파일 또는 날짜를 지정해주세요."
        usage
    fi
    
    # 환경 변수 로드
    if [[ -f ".env.production" ]]; then
        set -a
        source .env.production
        if [[ -f "secrets/.env.secrets" ]]; then
            source secrets/.env.secrets
        fi
        set +a
    fi
    
    # 백업 날짜로 파일 찾기
    if [[ -n "$BACKUP_DATE" && -z "$BACKUP_FILE" ]]; then
        BACKUP_DATE_FORMATTED=$(echo "$BACKUP_DATE" | tr -d '-')
        BACKUP_FILE=$(find backups/ -name "myzone_backup_${BACKUP_DATE_FORMATTED}_*.sql.gz" | head -1)
        
        if [[ -z "$BACKUP_FILE" ]]; then
            log_warning "로컬에서 백업 파일을 찾을 수 없습니다. S3에서 검색 중..."
            BACKUP_FILE=$(download_backup "myzone_backup_${BACKUP_DATE_FORMATTED}_030000.sql.gz")
        fi
    fi
    
    log_info "MyZone 재해 복구 시작"
    log_info "백업 파일: $BACKUP_FILE"
    
    # Dry run
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN 모드 - 실제 복구는 수행하지 않습니다."
        log_info "복구할 백업 파일: $BACKUP_FILE"
        log_info "복구 단계:"
        echo "  1. 현재 데이터베이스 백업"
        echo "  2. 애플리케이션 중지"
        echo "  3. 데이터베이스 복원"
        echo "  4. 파일 시스템 복구"
        echo "  5. 설정 파일 복구"
        echo "  6. 애플리케이션 재시작"
        echo "  7. 헬스체크"
        exit 0
    fi
    
    # 복구 확인
    if [[ "$FORCE" != "true" ]]; then
        log_warning "정말로 시스템을 복구하시겠습니까? 현재 데이터가 손실될 수 있습니다. (y/n)"
        read -r -p "" response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log_info "복구가 취소되었습니다."
            exit 0
        fi
    fi
    
    # 복구 실행
    restore_database "$BACKUP_FILE"
    
    if [[ -n "$BACKUP_DATE" ]]; then
        restore_files "$BACKUP_DATE"
    fi
    
    restore_configs
    
    log_success "재해 복구 완료!"
    
    # 슬랙 알림
    if [[ ! -z "${SLACK_WEBHOOK_URL}" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"🔄 MyZone 재해 복구 완료\\n📁 백업 파일: $(basename $BACKUP_FILE)\\n📅 시간: $(date)\"}" \
            "${SLACK_WEBHOOK_URL}" || true
    fi
}

# 스크립트 실행
main "$@"