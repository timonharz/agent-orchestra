#!/bin/bash

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "This script needs to be run as root to install Nginx and configure SSL"
  echo "Please run with: sudo ./deploy-with-nginx.sh your-domain.com"
  exit 1
fi

# Check if domain name is provided
if [ -z "$1" ]; then
  echo "Please provide your domain name as an argument"
  echo "Usage: sudo ./deploy-with-nginx.sh your-domain.com"
  exit 1
fi

DOMAIN=$1
APP_DIR=$(pwd)
API_PORT=8080

echo "Setting up Agent Orchestra API with Nginx for domain: $DOMAIN"

# Install dependencies
apt-get update
apt-get install -y nginx certbot python3-certbot-nginx

# Ensure Python dependencies are installed
pip install -r requirements.txt

# Create systemd service file for Agent Orchestra on a non-privileged port
cat > /etc/systemd/system/agent-orchestra.service << EOL
[Unit]
Description=Agent Orchestra API Server
After=network.target

[Service]
User=www-data
WorkingDirectory=$APP_DIR
ExecStart=$(which python3) $APP_DIR/server.py
Restart=always
RestartSec=10
Environment=PORT=$API_PORT

[Install]
WantedBy=multi-user.target
EOL

# Create Nginx configuration
cat > /etc/nginx/sites-available/agent-orchestra << EOL
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        return 301 https://\$host\$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name $DOMAIN;

    # SSL configuration will be added by Certbot

    location / {
        proxy_pass http://127.0.0.1:$API_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # WebSocket support if needed
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
        proxy_send_timeout 60s;
    }
}
EOL

# Enable the Nginx configuration
ln -sf /etc/nginx/sites-available/agent-orchestra /etc/nginx/sites-enabled/

# Test Nginx configuration
nginx -t

# Set correct permissions
chown -R www-data:www-data $APP_DIR
chmod -R 755 $APP_DIR

# Reload systemd, enable and start the service
systemctl daemon-reload
systemctl enable agent-orchestra
systemctl start agent-orchestra

# Restart Nginx
systemctl restart nginx

# Obtain SSL certificate with Certbot
certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

echo "Agent Orchestra has been deployed with Nginx HTTPS on $DOMAIN"
echo "You can check the API service status with: systemctl status agent-orchestra"
echo "You can check the Nginx status with: systemctl status nginx"
echo "View API logs with: journalctl -u agent-orchestra -f"
