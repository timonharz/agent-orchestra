#!/bin/bash

# Check if script is run as root (required for port 80)
if [ "$EUID" -ne 0 ]; then
  echo "This script needs to be run as root to bind to port 80"
  echo "Please run with: sudo ./deploy.sh"
  exit 1
fi

# Ensure Python dependencies are installed
pip install -r requirements.txt

# Create systemd service file for Agent Orchestra
cat > /etc/systemd/system/agent-orchestra.service << EOL
[Unit]
Description=Agent Orchestra API Server
After=network.target

[Service]
User=root
WorkingDirectory=$(pwd)
ExecStart=$(which python3) $(pwd)/server.py
Restart=always
RestartSec=10
Environment=PORT=80

[Install]
WantedBy=multi-user.target
EOL

# Reload systemd, enable and start the service
systemctl daemon-reload
systemctl enable agent-orchestra
systemctl start agent-orchestra

echo "Agent Orchestra has been deployed and is running on port 80"
echo "You can check the status with: systemctl status agent-orchestra"
echo "View logs with: journalctl -u agent-orchestra -f"
