# PowerShell setup script for Visa Developer AI Agent Chat (Windows)

Write-Host "Setting up Visa Developer AI Agent Chat (for Windows)..."

# 1. Create and activate virtual environment
python -m venv venv
if (!(Test-Path "venv")) {
    Write-Host "❌ ERROR: Failed to create virtual environment."
    exit 1
}

# Activate the virtual environment
# Note: Activation only affects the current script, not the parent shell
. .\venv\Scripts\Activate.ps1

# 2. Install backend requirements
python -m pip install --upgrade pip
pip install -r requirements.txt

# 3. Check for .env
if (!(Test-Path ".env")) {
    Write-Host "❌ ERROR: Missing .env file. Please create one in the root directory."
    exit 1
}

# 4. Start backend
Write-Host "Starting FastAPI backend..."
Start-Process -NoNewWindow -FilePath "python" -ArgumentList "-m uvicorn backend.app:app --reload" -PassThru | Set-Variable BACKEND_PROC

# 5. Start frontend
Write-Host "Installing frontend and starting React app..."
Push-Location frontend
npm install
Start-Process -NoNewWindow -FilePath "npm" -ArgumentList "run dev" -PassThru | Set-Variable FRONTEND_PROC
Pop-Location

Write-Host ""
Write-Host "✅ App is running!"
Write-Host "Frontend → http://localhost:5173"
Write-Host "Backend  → http://localhost:8000"
Write-Host "Please open your browser to the frontend URL to interact with the app."
Write-Host ""
Write-Host "To stop: Stop-Process -Id $($BACKEND_PROC.Id) $($FRONTEND_PROC.Id)"