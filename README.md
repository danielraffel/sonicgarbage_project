# SonicGarbage README

## Introduction
SonicGarbage is an audio processing project that creates unique soundscapes by combining elements from various audio sources. This project is inspired by the original work of [ColugoMusic](https://twitter.com/ColugoMusic/status/1726001266180956440?s=20) and further extends the concept using the power of Python and Flask.

### Demo
Currently running at [Polymetallic.co](https://Polymetallic.co)
There is an archive at [Polymetallic.co/archive](https://Polymetallic.co/archive)

## Getting Started

### Prerequisites
Ensure you have the following installed on your Ubuntu server:
- SSH access
- FFMPEG for media processing
- Python3 and pip for Python packages
- Nginx for serving the web application
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
   # Redirect HTTP traffic to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS Server Block
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem; # SSL certificate path
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem; # SSL key path

    # Root directory for static files
    root /var/www/audio;

    # Default index file
    index index.html;

    # Serve static files directly
    location / {
        try_files $uri $uri/ =404;
    }

    # Proxy requests to Flask application
    # Adjust if Flask app is running elsewhere or on a different port
    location /app {
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
This is based on work that is described in this Google Colab file at [GitHub repository](https://github.com/danielraffel/dodgylegally).

## What SonicGarbage Does
SonicGarbage automates the process of creating unique samples from YouTube and lets you play (and download) them in your browser. It uses Python to:
1. Generates random search phrases in birdwater.txt and downloads corresponding audio from YouTube.
2. Processes the audio to create one-shotdodgylegally/wavs/oneshot/ and loop dodgylegally/wavs/loop/ samples
3. Combines looped samples into a single audio file that repeats each sample 3-4 times, incrementing the version number to avoid overwriting. You can find it in dodgylegally/wavs/processed/combined/

The core script performs the following:
- Manages audio file processing, including downloading, editing, and combining audio clips.
- Generates and updates web pages to display and archive the created audio files.

Notes: if you want to generate more or less audio files adjust `SUCCESSFUL_WAVS_REQUIRED = 12` in `main.py`
It's currently set artificially low to 3 because I am running this on a [Google e2-micro instance](https://cloud.google.com/free/docs/free-cloud-features?hl=en#compute) (eg Always Free Tier) and it seems to have hiccups if I generate and convert too many. I've generated up to 12 files without hiccups and will keep testing.

## How to access the audio files
Right clicking should download the audio files.

## ToDo
Get index.html to trigger flask/gunicorn to auto run. This script should be very close to enabling that but I've not quite landed it yet.

I think I need to:
1) Run Flask on Port 80 or 8080: By default, I am running Gunicorn on port 8000. So I probably need to edit the last part of `main.py`
```
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```
2) Set Up Flask to Serve `index.html` on Home Route: Modify the Flask route to serve `index.html` and ensure the `main()` function is called each time this route is accessed.
```
@app.route('/')
def home():
    main()  # This will execute your main function
    with open('/var/www/audio/index.html', 'r') as file:
        return file.read()
```



