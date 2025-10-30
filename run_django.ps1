# Quick Django startup for ngrok
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Django Server Starting..." -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

# Set environment variables
$env:NGROK = "true"
$env:DEBUG = "True"
$env:ENABLE_HF_MODELS = "0"

Write-Host "Environment configured for ngrok" -ForegroundColor Green
Write-Host "Starting server on http://0.0.0.0:8000`n" -ForegroundColor Yellow

# Start Django
python manage.py runserver 0.0.0.0:8000
