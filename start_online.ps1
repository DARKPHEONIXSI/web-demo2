# start_online.ps1
# This script downloads Cloudflared (if missing) and starts a quick tunnel to expose localhost:5000

$ErrorActionPreference = "Stop"
$CloudflaredUrl = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
$CloudflaredExe = "$PSScriptRoot\cloudflared.exe"
$Port = 5000

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  On Ice - Exposing Website to the Internet  " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $CloudflaredExe)) {
    Write-Host "Cloudflared not found locally. Downloading from Cloudflare..." -ForegroundColor Yellow
    try {
        Invoke-WebRequest -Uri $CloudflaredUrl -OutFile $CloudflaredExe
        Write-Host "Download complete!" -ForegroundColor Green
    } catch {
        Write-Host "Error downloading Cloudflared: $_" -ForegroundColor Red
        Write-Host "Please download it manually from: $CloudflaredUrl" -ForegroundColor Red
        Write-Host "Save it as cloudflared.exe in this directory and run this script again." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Cloudflared is already installed." -ForegroundColor Green
}

Write-Host ""
Write-Host "Starting tunnel to localhost:$Port..." -ForegroundColor Yellow
Write-Host "Make sure your Flask server is running in another terminal window!" -ForegroundColor Yellow
Write-Host "Look for the URL ending in '.trycloudflare.com' below." -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the tunnel when you're done." -ForegroundColor Gray
Write-Host "---------------------------------------------" -ForegroundColor Gray

# Run cloudflared quick tunnel
& $CloudflaredExe tunnel --url http://localhost:$Port
