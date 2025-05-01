# Video Converter

A modern, user-friendly video converter with queue support, quality selection, and hardware acceleration (if available). Built with Python and Tkinter.

## Features
- Convert videos to MP4, AVI, MOV, MKV, WEBM
- Batch conversion (queue)
- Select output quality (Fast, Medium, High)
- Hardware acceleration (NVIDIA NVENC, Intel VAAPI) if available
- Progress bar and status for each file
- Modern dark UI
- **Subtitle selection and burn-in** (choose which subtitle to burn into the video)

## Requirements
- Python 3.8+
- FFmpeg (must be installed and available in your system PATH)

## Installation

### 1. Clone the repository
```bash
git clone <repo-url>
cd <repo-folder>
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Download and Install FFmpeg
- Go to: https://ffmpeg.org/download.html
- For Windows, you can use [gyan.dev FFmpeg builds](https://www.gyan.dev/ffmpeg/builds/)
- Download the latest **release full build** zip file
- Extract the zip (e.g., to `C:\ffmpeg`)

### 4. Add FFmpeg to your PATH (Windows)
1. Open the folder where you extracted FFmpeg (e.g., `C:\ffmpeg`)
2. Go to the `bin` folder (e.g., `C:\ffmpeg\bin`)
3. Copy the path to the `bin` folder
4. Press `Win + X` and select `System`
5. Click `Advanced system settings` > `Environment Variables`
6. Under `System variables`, find and select `Path`, then click `Edit`
7. Click `New` and paste the path to the `bin` folder
8. Click OK to close all dialogs
9. Open a new Command Prompt and run:
   ```
   ffmpeg -version
   ```
   You should see FFmpeg version info.

### 5. Run the Application
```bash
python conversor_video.py
```

## How to Use
1. Add your video files to the queue.
2. (Optional) **To select and burn a subtitle:** Double-click a video in the list. A window will appear showing all available subtitles in the file. Select the desired subtitle and click "Selecionar". The chosen subtitle will be burned into the video during conversion.
3. Choose output format, quality, and output folder.
4. Click "Iniciar Conversão" to start.

## Subtitles (Legendas)
- The app detects all embedded subtitles in your video files (MKV, MP4, etc).
- You can select which subtitle to burn into the video by double-clicking the video in the queue and choosing from the list.
- The selected subtitle will be permanently burned into the output video (burn-in), making it always visible and not removable.
- If you do not select a subtitle, the video will be converted without burning any subtitle.

## Troubleshooting
- If you get an error about FFmpeg not found, make sure it is installed and the `bin` folder is in your PATH.
- For hardware acceleration, ensure you have the latest drivers for your GPU and a compatible FFmpeg build.
- If output videos only play in VLC, make sure you are using the latest version of this app (it now enforces maximum compatibility for MP4).
- If you have issues with subtitles not appearing, make sure the video file actually contains embedded subtitles and that you selected the correct one.

---

Enjoy your fast and easy video conversions! 