# Media to GIF Converter

A Python script to generate GIFs from video subtitles. For each subtitle line, the script creates a GIF with the respective caption displayed.

![Image](https://cdn.vzq.wtf/vzq.wtf/main.gif)

## Features
- Converts videos into GIFs based on subtitle files.
- Automatically escapes special characters for FFmpeg.
- Uses parallel processing to generate GIFs quickly.
- Supports multiple video formats like `.mp4`, `.mkv`, `.avi`, `.mov`.
- Configurable skip patterns for filtering unwanted subtitle lines.
- Control over CPU usage by adjusting the number of workers.
- **Two pairing modes** for matching videos and subtitles:
  - **Same-name matching** in the `input/` root directory.
  - **Subfolder matching** (different names allowed) for videos and subtitles in the same subfolder.

## Usage

> [!WARNING]  
> **This script is extremely resource heavy.**  
> Generating GIFs from videos can use up a lot of CPU and memory, especially for long videos or large subtitle files. Be cautious when running this script on systems with limited resources.

1. **Clone the repository**:
    ```bash
    git clone https://github.com/v-zq/media-to-gif.git
    cd media-to-gif
    ```

2. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Prepare directories**:
    - **For same-name matching**:
      - Place your video and subtitle files with matching names (except for the extensions) in the `input/` root directory.
    - **For subfolder matching**:
      - Place your video and subtitle files in subfolders inside the `input/` directory. Files in the same subfolder will be paired, even if they have different names.
    - Supported video formats: `.mp4`, `.mkv`, `.avi`, `.mov`.
    - Supported subtitle formats: `.srt`, `.sub`, `.ass`. (hehe)

4. **Run the script**:
    ```bash
    python3 media_to_gif.py
    ```

5. **View output**:
    - GIFs will be saved in the `gifs` directory, organized by video name.
    - Metadata about generated GIFs will also be stored in a `metadata.json` file in the respective folder.

## Configuration

- You can adjust the following settings in the script:
    - `FPS`: Frames per second for the output GIF (default: 15)
    - `WIDTH`: Width of the GIF in pixels (default: 800)
    - `FONTSIZE`: Size of the subtitle font in the GIF (default: 24)
    - `OUTLINE`: Outline thickness of the subtitle text (default: 2)

- Skip Patterns: By default, the script will skip subtitle lines based on patterns such as:
  - Subtitles starting with ellipses (...).
  - Subtitles ending with commas, colons, or lowercase letters.  
If you want to process all subtitles and disable skipping, set SKIP_ENABLED = False in the script configuration.

### Controlling Resource Usage

The script uses parallel processing to generate GIFs quickly, which can be very CPU-intensive. You can control how many CPU cores are used by adjusting the `MAX_WORKERS` setting in the script.

- By default, the script will use all available CPU cores (`os.cpu_count()`).
- To reduce CPU usage and make the script less resource-intensive, set `MAX_WORKERS` to a lower value (for example, `MAX_WORKERS = 4`).

Example: In the script, you can adjust the intensity by modifying this line:
```python
MAX_WORKERS = os.cpu_count()  # This uses all available CPU cores
```

## Requirements

- Python 3.x
- FFmpeg installed and available in your system's `PATH`.

## Notes
- **Same-name matching**: In the root `input/` directory, videos and subtitles should have matching filenames (except for the extensions) for proper pairing.
- **Subfolder matching**: Videos and subtitles placed in the same subfolder inside `input/` will be paired, even if they have different names.

## License

This project is licensed under The Unlicense - see the [The Unlicense](LICENSE) file for details.

## Acknowledgment

This project's code was initially based on work from [https://github.com/dunn/videos-to-gif/tree/trunk](https://github.com/dunn/videos-to-gif/tree/trunk).