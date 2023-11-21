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

# Create the 'archive' folder if it does not exist
archive_dir = os.path.join(base_dir, 'archive')
if not os.path.exists(archive_dir):
    os.makedirs(archive_dir)

# Revised function to create timestamped subfolders
def create_timestamped_subfolders(base_dir, timestamp):
    directories = ['wavs/processed/loop', 'wavs/processed/oneshot', 
                   'wavs/raw', 'wavs/processed/combined']
    timestamped_dirs = {}
    for dir in directories:
        path = os.path.join(base_dir, dir, timestamp)
        os.makedirs(path, exist_ok=True)
        timestamped_dirs[dir] = path
    return timestamped_dirs

# Check if 'birdwater.txt' exists at the base directory, if not create it
word_list_file = os.path.join('/var/www/audio', 'birdwater.txt')

if not os.path.exists(word_list_file):
    nltk.download('words')
    from nltk.corpus import words
    word_list = random.sample(words.words(), 200)
    with open(word_list_file, 'w') as file:
        for word in word_list:
            file.write(word + '\n')

# Functions from the original notebook for audio processing
BATCH_SIZE         = 320
MAX_SEARCH_RESULTS = 10
DOWNLOAD_DIR       = 'wavs/raw'
LOOP_OUTPUT_DIR    = 'wavs/processed/loop'
ONESHOT_OUTPUT_DIR = 'wavs/processed/oneshot'
WORD_LIST          = 'birdwater.txt'

def read_lines(file):
    return open(file).read().splitlines()

class download_range_func:
    def __init__(self):
        pass
    def __call__(self, info_dict, ydl):
        timestamp = self.make_timestamp(info_dict)
        yield {
            'start_time': timestamp,
            'end_time': timestamp,
        }
    @staticmethod
    def make_timestamp(info):
        duration = info['duration']
        if duration is None:
            return 0
        return duration / 2

def make_random_search_phrase(word_list):
    words = random.sample(word_list, 2)
    phrase = ' '.join(words)
    print('Search phrase: "{}"'.format(phrase))
    return phrase

def make_download_options(phrase, download_dir):
    safe_phrase = ''.join(x for x in phrase if x.isalnum() or x in "._- ")
    return {
        'format': 'bestaudio/best',
        'paths': {'home': download_dir},
        'outtmpl': {'default': f'{safe_phrase}-%(id)s.%(ext)s'},
        'download_ranges': download_range_func(),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }]
    }

def process_file(filepath, phrase, oneshot_dir, loop_dir):
    try:
        safe_phrase = ''.join(x for x in phrase if x.isalnum() or x in "._- ")
        filename = os.path.basename(filepath)
        output_filepath_oneshot = os.path.join(oneshot_dir, f'oneshot_{safe_phrase}-{filename}')
        output_filepath_loop = os.path.join(loop_dir, f'loop_{safe_phrase}-{filename}')

        sound = AudioSegment.from_file(filepath, "wav")
        if len(sound) > 500:
            if not os.path.exists(output_filepath_oneshot):
                make_oneshot(sound, phrase, output_filepath_oneshot)
            if not os.path.exists(output_filepath_loop):
                make_loop(sound, phrase, output_filepath_loop)
            os.remove(filepath)
            return 1  # Return 1 for a successful processing of the video
    except Exception as err:
        print(f"Failed to process '{filepath}' ({err})")

    return 0

def make_oneshot(sound, phrase, output_filepath):
  final_length = min(2000, len(sound))
  quarter = int(final_length/4)
  sound   = sound[:final_length]
  sound   = sound.fade_out(duration=quarter)
  sound   = effects.normalize(sound)
  sound.export(output_filepath, format="wav")

def make_loop(sound, phrase, output_filepath):
    final_length = min(2000, len(sound))
    half         = int(final_length/2)
    fade_length  = int(final_length/4)
    beg   = sound[:half]
    end   = sound[half:]
    end   = end[:fade_length]
    beg   = beg.fade_in(duration=fade_length)
    end   = end.fade_out(duration=fade_length)
    sound = beg.overlay(end)
    sound = effects.normalize(sound)
    sound.export(output_filepath, format="wav")

def create_combined_loop(combined_dir):
    os.makedirs(combined_dir, exist_ok=True)  # Create the combined directory if it doesn't exist

    combined_loop = AudioSegment.silent(duration=100)  # A short silence to start
    loop_dir = os.path.join(combined_dir, '..', 'loop')  # Adjust path to loop directory
    for filepath in glob.glob(os.path.join(loop_dir, '*.wav')):
        sound = AudioSegment.from_file(filepath, format="wav")
        repeated_sound = sound * random.randint(3, 4)  # Repeat 3 or 4 times
        combined_loop += repeated_sound

    version = 1
    output_filename = "combined_loop_v{}.wav".format(version)
    output_filepath = os.path.join(combined_dir, output_filename)

    # Check if file already exists, and increment version number if it does
    while os.path.exists(output_filepath):
        version += 1
        output_filename = "combined_loop_v{}.wav".format(version)
        output_filepath = os.path.join(combined_dir, output_filename)

    combined_loop.export(output_filepath, format="wav")

def generate_html_for_audio_files(directory):
    html_content = ""
    file_count = 0

    # List files in the specified directory
    files = sorted([f for f in os.listdir(directory) if f.endswith('.wav')])

    html_content += '<div class="row">'

    for file in files:
        file_name = file.split('-')[-1].split('.')[0]
        file_path = os.path.relpath(os.path.join(directory, file), base_dir)  # Adjust path relative to base_dir
        # Add the audio file div without playback controls
        html_content += f'<div class="audio-file"><div>{file_name}</div><audio src="{file_path}"></audio></div>'
        
        file_count += 1
        if file_count % 3 != 0:
            html_content += ' '
        if file_count % 3 == 0 and file_count != len(files):
            html_content += '</div><div class="row">'

    html_content += '</div>'
    return f'<div class="container">{html_content}</div>'

def update_html_file(template_html_file_path, output_html_file_path, directory):
    html_to_insert = generate_html_for_audio_files(directory)

    with open(template_html_file_path, 'r') as template_file:
        template_html_content = template_file.read()

    modified_html_content = template_html_content.replace('<!-- Audio files will be added here -->', html_to_insert)

    with open(output_html_file_path, 'w') as output_file:
        output_file.write(modified_html_content)

def setup():
    if not os.path.exists(LOOP_OUTPUT_DIR):
        os.makedirs(LOOP_OUTPUT_DIR)
    if not os.path.exists(ONESHOT_OUTPUT_DIR):
        os.makedirs(ONESHOT_OUTPUT_DIR)

# Main function where audio processing happens
MAX_ATTEMPTS_PER_VIDEO = 3  # Maximum number of attempts to download a video for each phrase

# Number of successful WAV audio files required to end the script
SUCCESSFUL_WAVS_REQUIRED = 3

def main():
    # Generate a unique timestamp for this run
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    # Setup and read word list
    setup()
    word_list = read_lines(WORD_LIST)
    total_success_count = 0

    # Create timestamped subdirectories for this run
    timestamped_dirs = create_timestamped_subfolders(base_dir, timestamp)
    loop_dir = timestamped_dirs['wavs/processed/loop']
    oneshot_dir = timestamped_dirs['wavs/processed/oneshot']
    raw_dir = timestamped_dirs['wavs/raw']
    combined_dir = timestamped_dirs['wavs/processed/combined']

    # Adjusting paths in download options to the new raw_dir
    DOWNLOAD_DIR = raw_dir

        while total_success_count < SUCCESSFUL_WAVS_REQUIRED:
        phrase = make_random_search_phrase(word_list)
        video_url = f'ytsearch1:"{phrase}"'
        options = make_download_options(phrase, DOWNLOAD_DIR)
        downloaded = False

        for _ in range(MAX_ATTEMPTS_PER_VIDEO):
            try:
                downloaded = YoutubeDL(options).download([video_url]) == 0
                if downloaded:
                    break
            except Exception as err:
                print(f"Error during download: {err}")

        if downloaded:
            for filepath in glob.glob(os.path.join(DOWNLOAD_DIR, f'{phrase}-*.wav')):
                success = process_file(filepath, phrase, oneshot_dir, loop_dir)
                total_success_count += success
                if total_success_count >= SUCCESSFUL_WAVS_REQUIRED:
                    break

    # Create combined loop
    create_combined_loop(combined_dir)  # Ensure this function is adjusted for the new directory

    # Generate new index.html with updated audio files
    update_html_file('/var/www/audio/sonicgarbage_project/template_index.html', '/var/www/audio/index.html', loop_dir)

    # Archive existing index.html with the timestamp
    archive_existing_index('/var/www/audio/index.html', timestamp)

# Function to update the archive index.html file
def update_archive_html(archived_file_path):
    archive_index_path = os.path.join(archive_dir, 'index.html')
    link = f'<li><a href="{archived_file_path}">{os.path.basename(archived_file_path)}</a></li>'

    if not os.path.exists(archive_index_path):
        with open(archive_index_path, 'w') as archive_file:
            archive_file.write('<html><head><title>Sonic Garbage Archive</title></head><body>')
            archive_file.write('<h1>Sonic Garbage Archive</h1><ul>')
            archive_file.write(link)
            archive_file.write('</ul></body></html>')
    else:
        with open(archive_index_path, 'r+') as archive_file:
            content = archive_file.read()
            position = content.find('</ul>')
            content = content[:position] + link + content[position:]
            archive_file.seek(0)
            archive_file.write(content)

# Function to archive existing index.html
def archive_existing_index(output_html_file_path, timestamp):
    if os.path.exists(output_html_file_path):
        # Ensure the archived file is placed in the 'archive' directory
        archived_file_name = f'index.{timestamp}.html'
        archived_file_path = os.path.join(archive_dir, archived_file_name)
        os.rename(output_html_file_path, archived_file_path)
        # Update the archive index.html within the 'archive' directory
        update_archive_html(archived_file_path)

# Flask route to trigger the main function
@app.route('/run-script')
def run_script():
    main()
    return "Script executed"

# Flask route for the home page
@app.route('/')
def home():
    # Call main function each time the home page is loaded
    main()

    # Serve the updated index.html
    with open('/var/www/audio/index.html', 'r') as file:
        return file.read()

# Run the Flask app if this script is run directly
if __name__ == '__main__':
    main()  # Automatically run main functionality
    app.run(debug=True)