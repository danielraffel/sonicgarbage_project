# Import necessary libraries
import os
import nltk
from pydub import AudioSegment, effects
from yt_dlp import YoutubeDL
import glob
import random
import datetime
import shutil
from flask import Flask

# Initialize Flask app
app = Flask(__name__, static_folder='/var/www/audio')

# Base directory on the server (modify this path as needed)
base_dir = '/var/www/audio'

# Directories for processed and raw WAVs
processed_dir = os.path.join(base_dir, 'wavs', 'processed')
raw_dir = os.path.join(base_dir, 'wavs', 'raw')
loop_dir = os.path.join(processed_dir, 'loop')
oneshot_dir = os.path.join(processed_dir, 'oneshot')
combined_dir = os.path.join(processed_dir, 'combined')

# Create necessary directories if they do not exist
for dir in [processed_dir, raw_dir, loop_dir, oneshot_dir, combined_dir]:
    os.makedirs(dir, exist_ok=True)

# Archive directory
archive_dir = os.path.join(base_dir, 'archive')
os.makedirs(archive_dir, exist_ok=True)


# # Create the 'archive' folder if it does not exist
# archive_dir = os.path.join(base_dir, 'archive')
# if not os.path.exists(archive_dir):
#     os.makedirs(archive_dir)

# Revised function to create timestamped subfolders
def create_timestamped_subfolders(timestamp):
    directories = {
        'processed_loop': loop_dir,
        'processed_oneshot': oneshot_dir,
        'raw': raw_dir,
        'processed_combined': combined_dir
    }
    timestamped_dirs = {}
    for key, dir in directories.items():
        path = os.path.join(dir, timestamp)
        os.makedirs(path, exist_ok=True)
        timestamped_dirs[key] = path
    return timestamped_dirs

# Check if 'birdwater.txt' exists at the base directory, if not create it
#word_list_file = os.path.join('/var/www/audio', 'birdwater.txt')
# word_list_file = '/var/www/audio/birdwater.txt'
word_list_file = os.path.join(base_dir, 'birdwater.txt')

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
# DOWNLOAD_DIR       = 'wavs/raw'
# LOOP_OUTPUT_DIR    = 'wavs/processed/loop'
# ONESHOT_OUTPUT_DIR = 'wavs/processed/oneshot'
# WORD_LIST          = 'birdwater.txt'
DOWNLOAD_DIR = raw_dir
LOOP_OUTPUT_DIR = loop_dir
ONESHOT_OUTPUT_DIR = oneshot_dir
WORD_LIST = word_list_file

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
        file_path = '/' + os.path.relpath(os.path.join(directory, file), base_dir)
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
    # timestamped_dirs = create_timestamped_subfolders(base_dir, timestamp)
    timestamped_dirs = create_timestamped_subfolders(timestamp)
    loop_dir = timestamped_dirs['processed_loop']
    oneshot_dir = timestamped_dirs['processed_oneshot']
    raw_dir = timestamped_dirs['raw']
    combined_dir = timestamped_dirs['processed_combined']

    # Adjusting paths in download options to the new raw_dir
    DOWNLOAD_DIR = raw_dir

    # Loop to download and process videos until the required number of WAV files is reached
    while total_success_count < SUCCESSFUL_WAVS_REQUIRED:
        phrase = make_random_search_phrase(word_list)
        video_url = f'ytsearch1:"{phrase}"'
        options = make_download_options(phrase, DOWNLOAD_DIR)
        downloaded = False

        # Attempt to download the video
        for _ in range(MAX_ATTEMPTS_PER_VIDEO):
            try:
                downloaded = YoutubeDL(options).download([video_url]) == 0
                if downloaded:
                    break
            except Exception as err:
                print(f"Error during download: {err}")

        # If download is successful, process the video file
        if downloaded:
            for filepath in glob.glob(os.path.join(DOWNLOAD_DIR, f'{phrase}-*.wav')):
                success = process_file(filepath, phrase, oneshot_dir, loop_dir)
                total_success_count += success
                if total_success_count >= SUCCESSFUL_WAVS_REQUIRED:
                    break

    # After achieving the target number of WAV files
    if total_success_count >= SUCCESSFUL_WAVS_REQUIRED:
        # Log and create a combined loop of processed audio files
        try:
            create_combined_loop(combined_dir)
            print(f"Combined audio loop created in {os.path.join(combined_dir, 'combined_loop_v1.wav')}")
        except Exception as e:
            print(f"Failed to create combined loop in {combined_dir}: {e}")

        # Create and archive the timestamped index.html in the archive directory
        timestamped_html_path = os.path.join(archive_dir, f'index.{timestamp}.html')
        try:
            update_html_file('/var/www/audio/sonicgarbage_project/template_index.html', timestamped_html_path, loop_dir)
            print(f"Timestamped index.html created at {timestamped_html_path}")
        except Exception as e:
            print(f"Error creating timestamped index.html: {e}")

        # Update /archive/index.html with a link to the new timestamped index.html
        try:
            update_archive_html(timestamped_html_path)
        except Exception as e:
            print(f"Error updating /archive/index.html: {e}")

        # Update the main index.html in /var/www/audio
        try:
            update_html_file('/var/www/audio/sonicgarbage_project/template_index.html', '/var/www/audio/index.html', loop_dir)
            print("Main index.html updated successfully at /var/www/audio/index.html")
        except Exception as e:
            print(f"Error updating main index.html: {e}")
    else:
        print("Failed to generate the required number of audio files.")

    # End of script summary
    print(f"Script execution completed. Total successful WAVs: {total_success_count}")


# Function to update the archive index.html file
def update_archive_html(archived_file_path):
    archive_index_path = os.path.join(archive_dir, 'index.html')
    
    # Extract the relative path from the archived file path
    relative_path = os.path.relpath(archived_file_path, base_dir)
    link = f'<li><a href="/{relative_path}">{os.path.basename(archived_file_path)}</a></li>'

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
        archived_file_name = f'index.{timestamp}.html'
        archived_file_path = os.path.join(archive_dir, archived_file_name)
        shutil.copy(output_html_file_path, archived_file_path)  # Copy instead of moving
        update_archive_html(archived_file_path)
        print(f"Archived index.html at {archived_file_path}")

# Flask route to trigger the main function
@app.route('/run-script')
def run_script():
    main()
    return "Script executed"

# Flask route for the home page
@app.route('/')
def home():
    main()
    return app.send_static_file('index.html')

# Run the Flask app if this script is run directly
if __name__ == '__main__':
    main()  # Automatically run main functionality
    app.run(debug=True)