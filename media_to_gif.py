#!/usr/bin/env python3
"""
Script to generate GIFs with improved captions for every line of dialogue in subtitle files for multiple videos.

Usage:
    $ python3 media_to_gif.py
"""

import os
import sys
import re
import subprocess
import pysrt
import json
import logging
import multiprocessing
from slugify import slugify
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import time
import platform  # To detect the OS
from shutil import which

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration parameters
FPS = 15
WIDTH = 800
FONTSIZE = 24
OUTLINE = 2
MAX_WORKERS = os.cpu_count()

# Directories
INPUT_DIR = "input"
OUTPUT_DIR = "gifs"

# Skip Patterns Configuration
SKIP_ENABLED = True  # Enable skipping by default
SKIP_PATTERNS = [
    r".*[a-z]$",   # Ends with a lowercase letter
    r".*\,$",      # Ends with a comma
    r".*\:$",      # Ends with a colon
    r"^[a-z].*",   # Starts with a lowercase letter
    r"^\.\.\.",    # Starts with ellipsis
]

# Detect if running on Windows or Linux/MacOS
IS_WINDOWS = platform.system() == "Windows"

def check_ffmpeg_installed():
    """Check if FFmpeg is installed and available in the system's PATH."""
    if which("ffmpeg") is None:
        logging.error("FFmpeg is not installed or not available in your PATH. Please install it and ensure it's accessible.")
        sys.exit(1)

def striptags(text):
    """Strip HTML and special tags from subtitle text."""
    return re.sub(r'<.*?>|{.*?}', '', text).strip()

def no_skips(sub):
    """Filter out subtitles that match skip patterns, if enabled."""
    if not SKIP_ENABLED:
        return True  # Process all subtitles if skipping is disabled
    text = striptags(sub.text)
    return not any(re.search(pattern, text) for pattern in SKIP_PATTERNS)

def escape_for_ffmpeg(text):
    """Escape necessary characters for ffmpeg."""
    return text.replace('"', '\\"')

def make_gif(args):
    """Generate a GIF for the given subtitle."""
    i, sub, video_path, subtitle_path, output_dir = args
    text = striptags(sub.text)

    gif_filename = f'{i:06}-{slugify(text)}.gif'
    gif_filepath = os.path.join(output_dir, gif_filename)

    if os.path.exists(gif_filepath) and os.path.getsize(gif_filepath) > 0:
        return {'text': sub.text, 'path': gif_filepath}

    start = sub.start
    end = sub.end
    start_str = str(start).replace(',', '.')
    duration_str = str(end - start).replace(',', '.')

    escaped_text = escape_for_ffmpeg(text)

    temp_sub_file = os.path.join(output_dir, f"temp_sub_{i}.srt")
    try:
        with open(temp_sub_file, 'w', encoding='utf-8') as f:
            f.write(f"1\n00:00:00,000 --> {duration_str}\n{escaped_text}\n")
    except IOError as e:
        logging.error(f"Error writing temporary subtitle file: {e}")
        return None

    # Use '/' for file paths in FFmpeg command, even on Windows (FFmpeg handles it better)
    if IS_WINDOWS:
        temp_sub_file_ffmpeg = temp_sub_file.replace('\\', '/')
        video_path_ffmpeg = video_path.replace('\\', '/')
    else:
        temp_sub_file_ffmpeg = temp_sub_file
        video_path_ffmpeg = video_path

    filter_string = (
        f"fps={FPS},scale={WIDTH}:-1:flags=lanczos,"
        f"subtitles='{temp_sub_file_ffmpeg}':force_style='FontName=Arial,FontSize={FONTSIZE},"
        f"PrimaryColour=&HFFFFFF,OutlineColour=&H000000,BorderStyle=1,Outline={OUTLINE},"
        f"Shadow=1,Alignment=2,MarginV=20'"
    )

    cmd = [
        'ffmpeg',
        '-v', 'error',
        '-ss', start_str,
        '-i', video_path_ffmpeg,
        '-t', duration_str,
        '-vf', filter_string,
        '-f', 'gif',
        gif_filepath
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        if os.path.exists(gif_filepath) and os.path.getsize(gif_filepath) > 0:
            os.remove(temp_sub_file)
            return {'text': sub.text, 'path': gif_filepath}
        else:
            logging.error(f"Error: Empty GIF generated for subtitle {i}")
            return None
    except subprocess.CalledProcessError as e:
        logging.error(f"Error generating GIF for subtitle {i}: {e.stderr}")
        return None
    finally:
        if os.path.exists(temp_sub_file):
            os.remove(temp_sub_file)

def process_video(video_file, subtitle_file):
    """Process a video by generating GIFs for each subtitle."""
    video_name = os.path.splitext(os.path.basename(video_file))[0]
    output_dir = os.path.join(OUTPUT_DIR, video_name)
    os.makedirs(output_dir, exist_ok=True)

    logging.info(f"Processing video: {video_name}")

    try:
        subs = pysrt.open(subtitle_file, encoding="utf-8")
    except IOError as e:
        logging.error(f"Error reading subtitle file {subtitle_file}: {e}")
        return

    filtered_subs = [sub for sub in subs if no_skips(sub)]

    logging.info(f"Total subtitles: {len(subs)}")
    logging.info(f"Filtered subtitles: {len(filtered_subs)}")

    tasks = [
        (i, sub, video_file, subtitle_file, output_dir)
        for i, sub in enumerate(filtered_subs)
    ]

    start_time = time.time()
    metadata_list = []

    # Parallel processing of subtitles
    with tqdm(total=len(filtered_subs), desc=f"Processing {video_name}", unit="gif") as pbar:
        with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_task = {executor.submit(make_gif, task): task for task in tasks}
            for future in as_completed(future_to_task):
                result = future.result()
                if result:
                    metadata_list.append(result)
                pbar.update(1)
                elapsed_time = time.time() - start_time
                pbar.set_postfix(elapsed=f"{elapsed_time:.2f}s")

    if metadata_list:
        metadata_list.sort(key=lambda x: int(os.path.basename(x['path']).split('-')[0]))
        metadata_path = os.path.join(output_dir, "metadata.json")
        try:
            with open(metadata_path, "w", encoding='utf-8') as f:
                json.dump(metadata_list, f, ensure_ascii=False, indent=4)
        except IOError as e:
            logging.error(f"Error writing metadata file: {e}")

    logging.info(f"Completed processing {video_name}.")

def find_video_pairs(input_dir):
    """Find matching video and subtitle file pairs in the input directory and subdirectories."""
    video_files = []
    subtitle_files = []

    # Walk through the input directory and its subdirectories
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in ['.mp4', '.mkv', '.avi', '.mov']:
                video_files.append(os.path.join(root, file))
            elif ext in ['.srt', '.sub', '.ass']:
                subtitle_files.append(os.path.join(root, file))

    # Pair based on same-name matching if in the root input folder
    # Pair any video file with any subtitle file in subfolders regardless of name
    video_pairs = []
    for video in video_files:
        video_name = os.path.splitext(os.path.basename(video))[0]
        video_dir = os.path.dirname(video)
        if video_dir == input_dir:
            # Same-name matching in root input folder
            matching_subtitle = next(
                (sub for sub in subtitle_files if os.path.splitext(os.path.basename(sub))[0] == video_name),
                None
            )
            if matching_subtitle:
                video_pairs.append((video, matching_subtitle))
        else:
            # Match any video with any subtitle in the same subfolder
            sub_in_same_folder = [sub for sub in subtitle_files if os.path.dirname(sub) == video_dir]
            for sub in sub_in_same_folder:
                video_pairs.append((video, sub))

    return video_pairs

def main():
    """Main entry point of the script."""
    check_ffmpeg_installed()

    # Create the input directory if it doesn't exist
    if not os.path.exists(INPUT_DIR):
        os.makedirs(INPUT_DIR)
        logging.info(f"Input directory '{INPUT_DIR}' created. Please add video and subtitle files to it.")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    video_pairs = find_video_pairs(INPUT_DIR)
    if not video_pairs:
        logging.error("No matching video and subtitle files found in the input directory.")
        sys.exit(1)

    for video_file, subtitle_file in video_pairs:
        process_video(video_file, subtitle_file)

    logging.info("All videos have been processed.")


if __name__ == '__main__':
    # Fix for multiprocessing on Windows
    if IS_WINDOWS:
        multiprocessing.set_start_method('spawn')

    try:
        main()
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        sys.exit(1)