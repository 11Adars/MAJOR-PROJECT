@echo off
echo 🎬 Video Processing and Augmentation System
echo ================================================
echo.
echo This script will help you process your recorded videos:
echo - Generate 5 augmented versions per video
echo - Extract landmarks for training
echo - Save everything in CSV format
echo.

cd /d "%~dp0"

echo Starting video processor...
python process_videos.py

echo.
echo Processing complete! Check the output folders for results.
pause
