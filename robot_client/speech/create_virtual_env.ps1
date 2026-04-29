# Create virtual environment for the speech client on Windows
# Run this from PowerShell in the speech directory.
py -3 -m venv venv
if (Test-Path venv) {
    Write-Host "Virtual environment created. Activating..."
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    Write-Host "Virtual environment created and dependencies installed."
    Write-Host "Run '.\venv\Scripts\Activate.ps1' to activate again, then 'python pubsub.py' to start."
} else {
    Write-Error "Failed to create virtual environment. Ensure Python is installed and available as 'py'."
}
