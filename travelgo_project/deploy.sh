#!/bin/bash

# TravelGo Deployment Script for AWS EC2
# =======================================
# This script automates the deployment of TravelGo on AWS EC2
# Run as: sudo bash deploy.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  TravelGo EC2 Deployment Script${NC}"
echo -e "${BLUE}============================================${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

# Variables
APP_DIR="/var/www/travelgo"
VENV_DIR="$APP_DIR/venv"
LOG_DIR="/var/log/travelgo"
SERVICE_NAME="travelgo"

echo -e "${YELLOW}Step 1: Updating system packages...${NC}"
apt-get update -y
apt-get upgrade -y

echo -e "${YELLOW}Step 2: Installing required packages...${NC}"
apt-get install -y python3 python3-pip python3-venv nginx git wget curl

echo -e "${YELLOW}Step 3: Creating application directory...${NC}"
mkdir -p $APP_DIR
mkdir -p $LOG_DIR
chown -R www-data:www-data $APP_DIR
chown -R www-data:www-data $LOG_DIR

echo -e "${YELLOW}Step 4: Creating Python virtual environment...${NC}"
cd $APP_DIR
python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate

echo -e "${YELLOW}Step 5: Copying application files...${NC}"
# Copy from current directory to app directory
cp -r . $APP_DIR/ 2>/dev/null || true

echo -e "${YELLOW}Step 6: Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r $APP_DIR/requirements.txt
pip install gunicorn

echo -e "${YELLOW}Step 7: Creating systemd service...${NC}"
cp $APP_DIR/travelgo.service /etc/systemd/system/
systemctl daemon-reload

echo -e "${YELLOW}Step 8: Configuring Nginx...${NC}"
cp $APP_DIR/nginx.conf /etc/nginx/sites-available/travelgo
ln -sf /etc/nginx/sites-available/travelgo /etc/nginx/sites-enabled/
nginx -t

echo -e "${YELLOW}Step 9: Setting up AWS credentials...${NC}"
# Create AWS credentials file
mkdir -p /root/.aws
cat > /root/.aws/credentials <<EOF
[default]
aws_access_key_id = ${AWS_ACCESS_KEY_ID}
aws_secret_access_key = ${AWS_SECRET_ACCESS_KEY}
EOF

cat > /root/.aws/config <<EOF
[default]
region = ap-south-1
output = json
EOF

chmod 600 /root/.aws/credentials

echo -e "${YELLOW}Step 10: Creating log rotation config...${NC}"
cat > /etc/logrotate.d/travelgo <<EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        [ -f /var/run/travelgo.pid ] && kill -USR1 \$(cat /var/run/travelgo.pid)
    endscript
}
EOF

echo -e "${YELLOW}Step 11: Enabling and starting services...${NC}"
systemctl enable $SERVICE_NAME
systemctl restart $SERVICE_NAME
systemctl reload nginx

echo -e "${YELLOW}Step 12: Checking service status...${NC}"
systemctl status $SERVICE_NAME --no-pager || true
nginx -t

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "Application URL: http://your-ec2-public-ip/"
echo -e "Health Check: http://your-ec2-public-ip/health"
echo ""
echo -e "Useful Commands:"
echo -e "  ${BLUE}sudo systemctl status travelgo${NC}   - Check app status"
echo -e "  ${BLUE}sudo systemctl restart travelgo${NC} - Restart app"
echo -e "  ${BLUE}sudo journalctl -u travelgo -f${NC}  - View logs"
echo -e "  ${BLUE}sudo nginx -t${NC}                    - Check Nginx config"
echo ""

