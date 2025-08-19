#!/bin/bash

# SSL 인증서 설정 스크립트
# Let's Encrypt를 사용하여 프로덕션용 SSL 인증서를 설정합니다.

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
    echo "사용법: $0 [도메인] [이메일]"
    echo ""
    echo "예시:"
    echo "  $0 myzone.com admin@myzone.com"
    echo "  $0 api.myzone.com,www.myzone.com admin@myzone.com"
    echo ""
    exit 1
}

# 파라미터 확인
if [[ $# -lt 2 ]]; then
    log_error "도메인과 이메일을 지정해주세요."
    usage
fi

DOMAINS="$1"
EMAIL="$2"

log_info "SSL 인증서 설정 시작"
log_info "도메인: $DOMAINS"
log_info "이메일: $EMAIL"

# Certbot 설치 확인
if ! command -v certbot &> /dev/null; then
    log_info "Certbot 설치 중..."
    
    # Ubuntu/Debian
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y certbot python3-certbot-nginx
    # CentOS/RHEL
    elif command -v yum &> /dev/null; then
        sudo yum install -y epel-release
        sudo yum install -y certbot python3-certbot-nginx
    else
        log_error "지원되지 않는 운영체제입니다."
        exit 1
    fi
    
    log_success "Certbot 설치 완료"
fi

# SSL 디렉토리 생성
sudo mkdir -p /etc/nginx/ssl
sudo mkdir -p /var/www/certbot

# 임시 Nginx 설정 (인증서 발급용)
log_info "임시 Nginx 설정 생성 중..."
cat > /tmp/temp-nginx.conf << EOF
server {
    listen 80;
    server_name $DOMAINS;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}
EOF

# 기존 Nginx 설정 백업
if [[ -f /etc/nginx/sites-available/default ]]; then
    sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup
fi

# 임시 설정 적용
sudo cp /tmp/temp-nginx.conf /etc/nginx/sites-available/default
sudo nginx -t && sudo systemctl reload nginx

# Let's Encrypt 인증서 발급
log_info "Let's Encrypt 인증서 발급 중..."

# 도메인을 배열로 변환
IFS=',' read -ra DOMAIN_ARRAY <<< "$DOMAINS"
CERTBOT_DOMAINS=""
for domain in "${DOMAIN_ARRAY[@]}"; do
    CERTBOT_DOMAINS="$CERTBOT_DOMAINS -d $domain"
done

# 인증서 발급
sudo certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    $CERTBOT_DOMAINS

if [[ $? -eq 0 ]]; then
    log_success "SSL 인증서 발급 완료"
else
    log_error "SSL 인증서 발급 실패"
    exit 1
fi

# 첫 번째 도메인을 기본 도메인으로 사용
PRIMARY_DOMAIN="${DOMAIN_ARRAY[0]}"

# 인증서 파일을 Nginx SSL 디렉토리로 복사
sudo cp "/etc/letsencrypt/live/$PRIMARY_DOMAIN/fullchain.pem" /etc/nginx/ssl/cert.pem
sudo cp "/etc/letsencrypt/live/$PRIMARY_DOMAIN/privkey.pem" /etc/nginx/ssl/key.pem

# 파일 권한 설정
sudo chmod 644 /etc/nginx/ssl/cert.pem
sudo chmod 600 /etc/nginx/ssl/key.pem
sudo chown root:root /etc/nginx/ssl/*

log_success "SSL 인증서 파일 복사 완료"

# 자동 갱신 설정
log_info "자동 갱신 설정 중..."

# 갱신 스크립트 생성
cat > /tmp/renew-ssl.sh << 'EOF'
#!/bin/bash
certbot renew --quiet --post-hook "systemctl reload nginx"
EOF

sudo cp /tmp/renew-ssl.sh /usr/local/bin/renew-ssl.sh
sudo chmod +x /usr/local/bin/renew-ssl.sh

# Cron 작업 추가 (매월 1일 오전 3시)
(sudo crontab -l 2>/dev/null; echo "0 3 1 * * /usr/local/bin/renew-ssl.sh") | sudo crontab -

log_success "자동 갱신 설정 완료"

# DH 파라미터 생성 (보안 강화)
log_info "DH 파라미터 생성 중... (시간이 오래 걸릴 수 있습니다)"
sudo openssl dhparam -out /etc/nginx/ssl/dhparam.pem 2048

log_success "DH 파라미터 생성 완료"

# 최종 Nginx 설정 적용
log_info "프로덕션 Nginx 설정 적용 중..."
sudo cp nginx/prod.conf /etc/nginx/sites-available/default

# Nginx 설정 테스트
if sudo nginx -t; then
    sudo systemctl reload nginx
    log_success "Nginx 설정 적용 완료"
else
    log_error "Nginx 설정 오류"
    exit 1
fi

# SSL 테스트
log_info "SSL 설정 테스트 중..."
sleep 5

if curl -s -I "https://$PRIMARY_DOMAIN" | grep -q "HTTP/"; then
    log_success "SSL 설정 테스트 통과"
else
    log_warning "SSL 설정 테스트 실패 - 수동 확인이 필요합니다"
fi

# 보안 등급 확인 (선택사항)
log_info "SSL Labs 테스트 URL: https://www.ssllabs.com/ssltest/analyze.html?d=$PRIMARY_DOMAIN"

log_success "SSL 설정 완료!"
echo ""
log_info "설정 정보:"
echo "  도메인: $DOMAINS"
echo "  인증서 위치: /etc/nginx/ssl/"
echo "  자동 갱신: 매월 1일 오전 3시"
echo "  DH 파라미터: /etc/nginx/ssl/dhparam.pem"

# 정리
rm -f /tmp/temp-nginx.conf /tmp/renew-ssl.sh