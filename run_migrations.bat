@echo off
cd /d "%~dp0"
python manage.py makemigrations core requests_unified --no-input
python manage.py migrate --no-input
python populate.py
pause
