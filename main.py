# Import necessary libraries
import os
import nltk
from pydub import AudioSegment, effects
from yt_dlp import YoutubeDL
import glob
import random
import datetime
from flask import Flask

# Initialize Flask app
app = Flask(__name__)

# Base directory on the server (modify this path as needed)
base_dir = '/var/www/audio'

# Check if base directory exists, if not, create it
if not os.path.exists(base_dir):
    os.makedirs(base_dir)

# Function to create a timestamped folder
def create_timestamped_folder():
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    path = os.path.join(base_dir, timestamp)
    os.makedirs(path, exist_ok=True)
    return path

# Use the timestamped folder for this run
current_run_dir = create_timestamped_folder()

# Paths for the folders within the timestamped folder
loop_dir = os.path.join(current_run_dir, 'wavs/processed/loop')
oneshot_dir = os.path.join(current_run_dir, 'wavs/processed/oneshot')
raw_dir = os.path.join(current_run_dir, 'wavs/raw')
combined_dir = os.path.join(current_run_dir, 'wavs/processed/combined')

# Create the required folders if they don't exist
os.makedirs(loop_dir, exist_ok=True)
os.makedirs(oneshot_dir, exist_ok=True)
os.makedirs(raw_dir, exist_ok=True)
os.makedirs(combined_dir, exist_ok=True)

# Check if 'birdwater.txt' exists at the base directory, if not create it
word_list_file = os.path.join(base_dir, 'birdwater.txt')
if not os.path.exists(word_list_file):
    nltk.download('words')
    from nltk.corpus import words
    word_list = random.sample(words.words(), 200)
    with open(word_list_file, 'w') as file:
        for word in word_list:
            file.write(word + '\n')

# Set BATCH_SIZE to 45
BATCH_SIZE = 45
MAX_SEARCH_RESULTS = 10
DOWNLOAD_DIR = raw_dir
LOOP_OUTPUT_DIR = loop_dir
ONESHOT_OUTPUT_DIR = oneshot_dir
WORD_LIST = word_list_file

# Function to generate HTML for audio files
def generate_html_for_audio_files(directory):
    html_content = ""
    files = sorted([f for f in os.listdir(directory) if f.endswith('.wav')])
    file_count = 0

    html_content += '<div class="row">'

    for file in files:
        file_name = file.split('-')[-1].split('.')[0]
        file_path = f"wavs/processed/loop/{file}"
        html_content += f'<div class="audio-file"><div>{file_name}</div><audio src="{file_path}"></audio></div>'
        
        file_count += 1
        if file_count % 3 != 0:
            html_content += ' '
        if file_count % 3 == 0 and file_count != len(files):
            html_content += '</div><div class="row">'

    html_content += '</div>'
    return f'<div class="container">{html_content}</div>'

# Function to update HTML file
def update_html_file(template_html_file_path, output_html_file_path, directory):
    html_to_insert = generate_html_for_audio_files(directory)
    with open(template_html_file_path, 'r') as template_file:
        template_html_content = template_file.read()
    modified_html_content = template_html_content.replace('<!-- Audio files will be added here -->', html_to_insert)
    with open(output_html_file_path, 'w') as output_file:
        output_file.write(modified_html_content)

# Function to update the archive.html file
def update_archive_html(archived_file_path):
    archive_html_path = os.path.join(base_dir, 'archive.html')
    link = f'<li><a href="{archived_file_path}">{archived_file_path.split("/")[-1]}</a></li>'

    if not os.path.exists(archive_html_path):
        with open(archive_html_path, 'w') as archive_file:
            archive_file.write('<html><head><title>Sonic Garbage Archive</title></head><body>')
            archive_file.write('<h1>Sonic Garbage Archive</h1><ul>')
            archive_file.write(link)
            archive_file.write('</ul></body></html>')
    else:
        with open(archive_html_path, 'r+') as archive_file:
            content = archive_file.read()
            position = content.find('</ul>')
            content = content[:position] + link + content[position:]
            archive_file.seek(0)
            archive_file.write(content)

# Function to archive existing index.html
def archive_existing_index(output_html_file_path):
    if os.path.exists(output_html_file_path):
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        archived_file_path = output_html_file_path.replace('index.html', f'index.{timestamp}.html')
        os.rename(output_html_file_path, archived_file_path)
        update_archive_html(archived_file_path)  # Update the archive.html

# Main function where audio processing happens
def main():
    # Your existing main function code for audio processing

    # Generate new index.html with updated audio files
    archive_existing_index('/var/www/audio/index.html')  # Replace with your path
    update_html_file('/var/www/audio/sonicgarbage/template_index.html', '/var/www/audio/index.html', loop_dir)

# Flask route to trigger the main function
@app.route('/run-script')
def run_script():
    main()
    return "Script executed"

# Flask route for the home page
@app.route('/')
def home():
    # Serve the updated index.html
    with open('/var/www/audio/index.html', 'r') as file:
        return file.read()

# Run the Flask app if this script is run directly
if __name__ == '__main__':
    app.run(debug=True)