# use this to control starting the gunicorn service
# sudo vi /etc/systemd/system/gunicorn.service
# To start: sudo systemctl start gunicorn
# To enable start on boot: sudo systemctl enable gunicorn
# Status: sudo systemctl status gunicorn
# Reload: sudo systemctl daemon-reload
# Restart: sudo systemctl restart gunicorn

[Unit]
Description=Gunicorn instance to serve sonicgarbage
After=network.target

[Service]
User=daniel_raffel
Group=www-data  # or another group you prefer
WorkingDirectory=/var/www/audio/sonicgarbage_project/sonicgarbage/
ExecStart=/home/daniel_raffel/.local/bin/gunicorn -w 4 -b 0.0.0.0:8000 main:app

[Install]
WantedBy=multi-user.target
