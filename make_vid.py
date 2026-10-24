import subprocess
import json
from pathlib import Path

# Load run data
runs = json.loads(Path("submission/video/run.json").read_text())
total_duration = int(runs[-1]["end"]) + 2

# Create a simple black video with title using ffmpeg
ffmpeg_cmd = [
    "ffmpeg", "-y",
    "-f", "lavfi",
    "-i", f"color=c=black:s=1280x720:d={total_duration}",
    "-vf", "drawtext=text='Laptop AI Assistant: Safe File & App Management':fontsize=40:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-preset", "ultrafast",
    "submission/video/demo.mp4"
]

result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, cwd="./bothinath-decider-hackathon-kit")
if result.returncode == 0:
    print("Video created")
else:
    print(f"Error: {result.stderr[:200]}")
