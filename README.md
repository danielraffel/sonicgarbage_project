# SonicGarbage README

## Introduction
SonicGarbage is a project focused on audio processing, utilizing a custom-generated word dictionary to create a set of distinct audio samples each time you access it by sampling YouTube. This project is inspired by the original work of [ColugoMusic](https://twitter.com/ColugoMusic/status/1726001266180956440?s=20).

### Demo
Currently running at [Polymetallic.co](https://Polymetallic.co)
There is an archive at [Polymetallic.co/archive](https://Polymetallic.co/archive)

## Getting Started

### Prerequisites
Ensure you have the following installed on your Ubuntu server:
- SSH access
- FFMPEG for media processing
- Python3 and pip for Python packages
- Nginx and Gunicorn for serving the web application
- Certbot for SSL certificate management

### Installation
1. **SSH into your server**  
   `ssh [your-server-address]`

2. **Update your system packages**  
   `sudo apt-get update`

3. **Install necessary software**  
   ```
   sudo apt-get install ffmpeg
   sudo apt-get install python3-pip
   sudo apt install nginx
   sudo apt install certbot python3-certbot-nginx
   ```

4. **Configure Nginx**  
   Edit your domain's Nginx configuration:  
   `sudo vi /etc/nginx/sites-available/yourdomain.com`  
   Replace the content with the provided configuration, updating `yourdomain.com` with your actual domain.
```
server {
    listen 80;
    server_name polymetallic.co www.polymetallic.co;
    return 301 https://$server_name$request_uri;
}

# HTTPS Server Block
server {
    listen 443 ssl http2;
    server_name polymetallic.co www.polymetallic.co;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/polymetallic.co/fullchain.pem; # SSL certificate path
    ssl_certificate_key /etc/letsencrypt/live/polymetallic.co/privkey.pem; # SSL key path

    # Serve static files from the 'wavs' directory
    location /wavs/ {
        alias /var/www/audio/wavs/;
        autoindex off;  # Turn this off in production for security
    }

    # Serve static files from the 'archive' directory
    location /archive/ {
        alias /var/www/audio/archive/;
        autoindex off;  # Turn this off in production for security
    }

    # Proxy requests to Flask application
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Additional SSL configurations, security headers, etc. can be added here
}
```

6. **Create project directories and clone the repository**  
   ```
   mkdir /var/www/audio
   cd /var/www/audio
   sudo chown -R $USER /var/www/audio
   sudo git clone https://github.com/danielraffel/sonicgarbage_project.git
   cd sonicgarbage_project
   ```

7. **Setup the project**  
   ```
   pip3 install -r requirements.txt && sudo python3 setup.py install
   ```

8. **Run Gunicorn server**
   You can run CTRL+Z to suspend after running
   ```
   cd /var/www/audio/sonicgarbage_project/sonicgarbage
   gunicorn -w 4 -b 0.0.0.0:8000 main:app
   ```

10. **Run the SonicGarbage script**  

   ```
   cd /var/www/audio
   sonicgarbage
   ```

   On completion, you should see output similar to the following:  
   ```
   Combined audio loop created in /var/www/audio/wavs/processed/combined/20231121034414/combined_loop_v1.wav
   Timestamped index.html created at /var/www/audio/archive/index.20231121034414.html
   Main index.html updated successfully at /var/www/audio/index.html
   Script execution completed. Total successful WAVs: 3
   ```

### Additional References
A Google Colab file was also created [GitHub repository](https://github.com/danielraffel/dodgylegally).

## What SonicGarbage Does
SonicGarbage streamlines the generation of unique audio samples from YouTube, enabling you to play and download them directly in your browser. Leveraging Python, it:

1. Generates random search terms from 'birdwater.txt' and finds corresponding audio samples from YouTube.
2. Processes the audio to produce single-shot and looped samples
3. Creates a playable web page where you can scroll over the YouTube IDs the samples were taken from and mix them.
4. Creates a combined looped audio file, repeating each sample 3-4 times

The core script performs the following:
- Manages audio file processing, including downloading, editing, and combining audio clips each time the page is loaded.
- Generates and updates web pages to display and archive the created audio files.

### Configuration tips
If you want to generate more or less audio files adjust `SUCCESSFUL_WAVS_REQUIRED = 12` in `main.py`

It's currently set artificially low to 3 because I am running this on a [Google e2-micro instance](https://cloud.google.com/free/docs/free-cloud-features?hl=en#compute) (eg Always Free Tier) and it seems to have hiccups if I generate and convert too many. I've generated up to 12 files without hiccups and will keep testing.

To control auto starting the gunicorn service use gunicorn.service and follow the instructions

## How to access the audio files
Right clicking should download the audio files.


