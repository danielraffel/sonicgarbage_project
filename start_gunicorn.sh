#!/bin/bash
cd /var/www/audio/sonicgarbage_project/
gunicorn -w 4 -b 0.0.0.0:8000 main:app
